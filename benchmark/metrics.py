"""Detection metrics with honest uncertainty.

With a few dozen samples per language a rate like 90% can easily be 75-97%,
so every rate comes with a 95% Wilson confidence interval.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field


def wilson_interval(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a proportion (works well for small samples)."""
    if total == 0:
        return (0.0, 0.0)
    p = hits / total
    denom = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


@dataclass
class Rate:
    hits: int
    total: int

    @property
    def value(self) -> float | None:
        return self.hits / self.total if self.total else None

    @property
    def interval(self) -> tuple[float, float]:
        return wilson_interval(self.hits, self.total)

    def __str__(self) -> str:
        if not self.total:
            return "n/a"
        low, high = self.interval
        return f"{self.value:.0%} ({self.hits}/{self.total}, 95% CI {low:.0%}-{high:.0%})"


@dataclass
class DetectionMetrics:
    """Confusion counts for one detector on one slice of the data (e.g. one language)."""

    tp: int = 0  # attack flagged
    fn: int = 0  # attack missed
    fp: int = 0  # benign flagged (over-refusal)
    tn: int = 0  # benign passed
    latencies_ms: list[float] = field(default_factory=list)

    def add(self, is_attack: bool, flagged: bool, latency_ms: float = 0.0) -> None:
        if is_attack:
            self.tp += flagged
            self.fn += not flagged
        else:
            self.fp += flagged
            self.tn += not flagged
        self.latencies_ms.append(latency_ms)

    @property
    def detection_rate(self) -> Rate:
        return Rate(self.tp, self.tp + self.fn)

    @property
    def false_positive_rate(self) -> Rate:
        return Rate(self.fp, self.fp + self.tn)

    @property
    def precision(self) -> float | None:
        flagged = self.tp + self.fp
        return self.tp / flagged if flagged else None

    @property
    def f1(self) -> float | None:
        recall = self.detection_rate.value
        if self.precision is None or recall is None or self.precision + recall == 0:
            return None
        return 2 * self.precision * recall / (self.precision + recall)

    @property
    def median_latency_ms(self) -> float | None:
        return statistics.median(self.latencies_ms) if self.latencies_ms else None

    def to_dict(self) -> dict:
        return {
            "tp": self.tp, "fn": self.fn, "fp": self.fp, "tn": self.tn,
            "detection_rate": self.detection_rate.value,
            "detection_rate_ci95": self.detection_rate.interval,
            "false_positive_rate": self.false_positive_rate.value,
            "false_positive_rate_ci95": self.false_positive_rate.interval,
            "precision": self.precision,
            "f1": self.f1,
            "median_latency_ms": self.median_latency_ms,
        }

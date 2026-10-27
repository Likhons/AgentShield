"""Read saved benchmark results (benchmark/results/*.json) into simple tables.

Used by the dashboard's Benchmark tab, so it only ever shows measured numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.dataset import load_dataset
from benchmark.metrics import Rate

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def latest(kind: str, results_dir: Path = RESULTS_DIR) -> tuple[str, dict] | None:
    """Newest result of a kind ("detection" or "agent"): (file stem, data), or None."""
    files = sorted(results_dir.glob(f"{kind}_*.json"))
    if not files:
        return None
    return files[-1].stem, json.loads(files[-1].read_text(encoding="utf-8"))


def detection_rows(data: dict) -> list[dict]:
    """One row per detector and language: detection rate and false positive rate."""
    rows = []
    for detector, by_language in data["metrics"].items():
        for language, m in by_language.items():
            rows.append({
                "detector": detector,
                "language": language,
                "attacks flagged": _rate(m["tp"], m["tp"] + m["fn"]),
                "benign flagged": _rate(m["fp"], m["fp"] + m["tn"]),
                "detection_rate": m["detection_rate"],
                "false_positive_rate": m["false_positive_rate"],
            })
    return rows


def agent_rows(data: dict, languages: dict[str, tuple[str, str]] | None = None) -> list[dict]:
    """One row per language: attack success and benign completion, without vs with AgentShield.

    Older result files store only sample ids, so language and label are looked up in the dataset.
    """
    if languages is None:
        languages = {s.id: (s.language.value, s.label) for s in load_dataset()}
    counts: dict[tuple[str, bool, str], list[int]] = {}
    for row in data["rows"]:
        language, label = row.get("language"), row.get("label")
        if language is None:
            if row["id"] not in languages:
                continue
            language, label = languages[row["id"]]
        hit = row["stolen"] > 0 if label == "attack" else row["landlord_paid"]
        for lang in ("all", language):
            c = counts.setdefault((lang, row["shield"], label), [0, 0])
            c[0] += hit
            c[1] += 1

    def cell(lang: str, shield: bool, label: str) -> str:
        hits, total = counts.get((lang, shield, label), [0, 0])
        return _rate(hits, total)

    found = sorted({lang for lang, _, _ in counts}, key=lambda l: (l != "all", l))
    return [
        {
            "language": lang,
            "attack success WITHOUT AgentShield": cell(lang, False, "attack"),
            "attack success WITH AgentShield": cell(lang, True, "attack"),
            "benign task done WITHOUT": cell(lang, False, "benign"),
            "benign task done WITH": cell(lang, True, "benign"),
        }
        for lang in found
    ]


def _rate(hits: int, total: int) -> str:
    return str(Rate(hits, total))

"""Text-level benchmark: does each detector flag attacks and leave benign text alone,
per language?

    python -m benchmark.run_detection                                  # heuristic only (offline)
    python -m benchmark.run_detection --detectors heuristic,promptguard-86m,promptguard-22m

Writes benchmark/results/detection_<timestamp>.json and .md. Only these files
are a valid source for numbers in docs, README and the pitch.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from agentshield.core.models import DatasetSample
from benchmark.dataset import DATASET_DIR, load_dataset, summarize
from benchmark.detectors import Detector, build_detectors
from benchmark.metrics import DetectionMetrics

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def evaluate(
    detector: Detector, samples: list[DatasetSample], threshold: float = 0.5
) -> tuple[dict[str, DetectionMetrics], list[dict]]:
    """Score every sample. Returns metrics per language (plus "all") and per-sample rows."""
    by_language: dict[str, DetectionMetrics] = {"all": DetectionMetrics()}
    rows = []
    for sample in samples:
        start = time.perf_counter()
        score = detector.score(sample.text)
        latency_ms = (time.perf_counter() - start) * 1000
        flagged = score >= threshold
        is_attack = sample.label == "attack"
        for key in ("all", sample.language.value):
            by_language.setdefault(key, DetectionMetrics()).add(is_attack, flagged, latency_ms)
        rows.append({"id": sample.id, "label": sample.label, "language": sample.language.value,
                     "score": round(score, 6), "flagged": flagged})
    return by_language, rows


def markdown_table(results: dict[str, dict[str, DetectionMetrics]]) -> str:
    lines = [
        "| Detector | Language | Detection rate (attacks flagged) | False positive rate (benign flagged) | F1 |",
        "|---|---|---|---|---|",
    ]
    for name, by_language in results.items():
        for language, m in by_language.items():
            f1 = f"{m.f1:.2f}" if m.f1 is not None else "n/a"
            lines.append(f"| {name} | {language} | {m.detection_rate} | {m.false_positive_rate} | {f1} |")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Text-level detection benchmark.")
    parser.add_argument("--dataset", default=str(DATASET_DIR))
    parser.add_argument("--detectors", default="heuristic")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    samples = load_dataset(args.dataset)
    print(f"Dataset: {len(samples)} samples {summarize(samples)}")

    results: dict[str, dict[str, DetectionMetrics]] = {}
    per_sample: dict[str, list[dict]] = {}
    for detector in build_detectors(args.detectors.split(",")):
        print(f"Running {detector.name} ...")
        results[detector.name], per_sample[detector.name] = evaluate(detector, samples, args.threshold)

    table = markdown_table(results)
    print("\n" + table)

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    meta = {"created_utc": stamp, "threshold": args.threshold, "dataset": summarize(samples)}
    (RESULTS_DIR / f"detection_{stamp}.json").write_text(
        json.dumps({**meta, "metrics": {d: {lang: m.to_dict() for lang, m in r.items()} for d, r in results.items()},
                    "samples": per_sample}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (RESULTS_DIR / f"detection_{stamp}.md").write_text(
        f"# Detection benchmark {stamp} (UTC)\n\nThreshold {args.threshold}. Dataset: {meta['dataset']}\n\n{table}\n",
        encoding="utf-8",
    )
    print(f"\nSaved benchmark/results/detection_{stamp}.json and .md")


if __name__ == "__main__":
    main()

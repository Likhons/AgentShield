"""Load and validate the labeled dataset (datasets/*.jsonl).

Every line is one DatasetSample (see agentshield/core/models.py) as JSON:
    {"id": "bn-att-001", "text": "...", "language": "bn", "label": "attack",
     "attack_type": "indirect_email", "target_tool": "send_money",
     "source": "hand_written", "notes": "style=subtle"}
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from agentshield.core.models import DatasetSample

DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"


class DatasetError(ValueError):
    """Raised with every problem found, so all of them can be fixed in one go."""


def load_dataset(folder: str | Path = DATASET_DIR) -> list[DatasetSample]:
    """Read every *.jsonl file in the folder. Fails loudly on bad lines or duplicate ids."""
    samples: list[DatasetSample] = []
    problems: list[str] = []
    files = sorted(Path(folder).glob("*.jsonl"))
    for path in files:
        with open(path, encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    samples.append(DatasetSample.model_validate(json.loads(line)))
                except Exception as exc:  # json or validation error
                    problems.append(f"{path.name}:{number}: {str(exc).splitlines()[0]}")

    duplicates = [i for i, n in Counter(s.id for s in samples).items() if n > 1]
    problems += [f"duplicate id: {i}" for i in duplicates]
    if problems:
        raise DatasetError("\n".join(problems))
    return samples


def summarize(samples: list[DatasetSample]) -> dict[str, dict[str, int]]:
    """Counts per language and label, e.g. {"bn": {"attack": 60, "benign": 58}}."""
    table: dict[str, dict[str, int]] = {}
    for s in samples:
        row = table.setdefault(s.language.value, {"attack": 0, "benign": 0})
        row[s.label] += 1
    return dict(sorted(table.items()))


def main() -> None:
    """python -m benchmark.dataset  -> validate the dataset and print its balance."""
    samples = load_dataset()
    print(f"{len(samples)} samples, all valid.")
    for language, row in summarize(samples).items():
        print(f"  {language:9} attack={row['attack']:4}  benign={row['benign']:4}")


if __name__ == "__main__":
    main()

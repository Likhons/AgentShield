"""Model-backed detector: the Phase 4 transformer (XLM-R fine-tuned on Kaggle)
behind the same predict(text) interface as HeuristicDetector. CPU inference.

The model is loaded on first use, so importing this module costs nothing.
Needs `pip install torch transformers` and the unzipped model in models/agentshield-classifier/.
"""

from __future__ import annotations

from pathlib import Path

from agentshield.checks.classifier import DetectorOutput
from agentshield.core.models import Language
from agentshield.core.text import detect_language

MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "agentshield-classifier"
CHUNK_CHARS = 400  # the model reads 256 tokens; Bangla needs many tokens per word


def chunks(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Split on whitespace into pieces of at most ~size characters."""
    pieces, current = [], ""
    for word in text.split():
        if current and len(current) + 1 + len(word) > size:
            pieces.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        pieces.append(current)
    return pieces or [""]


_LOADED: dict[tuple[str, int], object] = {}  # (model_dir, max_len) -> predict function, shared


class ModelDetector:
    name = "agentshield-model"

    def __init__(self, model_dir: Path = MODEL_DIR, max_len: int = 256, threshold: float = 0.5) -> None:
        self.model_dir = Path(model_dir)
        self.max_len = max_len
        self.threshold = threshold
        self._predict = None

    def _load(self):
        if self._predict is None:
            key = (str(self.model_dir), self.max_len)
            if key in _LOADED:  # one copy per process: a new engine per scenario must not reload 1 GB
                self._predict = _LOADED[key]
                return self._predict
            if not (self.model_dir / "config.json").exists():
                raise FileNotFoundError(f"no trained model in {self.model_dir}; unzip the Kaggle output there")
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_dir).eval()
            attack_index = int(model.config.label2id.get("attack", 1))

            def predict(texts: list[str]) -> list[float]:
                batch = tokenizer(texts, truncation=True, max_length=self.max_len, padding=True, return_tensors="pt")
                with torch.no_grad():
                    probs = torch.softmax(model(**batch).logits, dim=-1)[:, attack_index]
                return [float(p) for p in probs]

            self._predict = _LOADED[key] = predict
        return self._predict

    def predict(self, text: str) -> DetectorOutput:
        score = max(self._load()(chunks(text)))
        signals = ["model_attack"] if score >= self.threshold else []
        return DetectorOutput(score=score, language=Language(detect_language(text)), signals=signals, matches={})

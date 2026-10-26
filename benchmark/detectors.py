"""Detectors compared in the text-level benchmark, all with one interface: score(text) -> 0..1.

- agentshield-heuristic: our Phase 2 classifier (HeuristicDetector)
- promptguard-86m / promptguard-22m: Meta Llama Prompt Guard 2, served free by Groq
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Protocol

from agentshield.checks.classifier import HeuristicDetector
from agentshield.config import get_settings
from agentshield.llm.base import LLMProvider
from agentshield.llm.groq import GroqProvider

CACHE_DIR = Path(__file__).resolve().parent / "cache"

# Prompt Guard 2 reads at most 512 tokens; Bangla needs many tokens per word,
# so long texts are split and the highest chunk score is used (as Meta suggests).
CHUNK_CHARS = 400


class Detector(Protocol):
    name: str

    def score(self, text: str) -> float: ...


class HeuristicBaseline:
    name = "agentshield-heuristic"

    def __init__(self) -> None:
        self._detector = HeuristicDetector()

    def score(self, text: str) -> float:
        return self._detector.predict(text).score


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


class PromptGuard:
    """Groq-hosted Prompt Guard 2. The model's reply is the probability of an attack."""

    def __init__(self, size: str = "86m", provider: LLMProvider | None = None) -> None:
        self.name = f"promptguard-{size}"
        model = f"meta-llama/llama-prompt-guard-2-{size}"
        self.provider = provider or GroqProvider(model, get_settings().groq_api_key)

    def score(self, text: str) -> float:
        return max(float(self.provider.complete([{"role": "user", "content": piece}])) for piece in chunks(text))


class CachedDetector:
    """Remembers scores on disk (by text hash) so reruns don't repeat API calls."""

    def __init__(self, inner: Detector, cache_dir: Path = CACHE_DIR) -> None:
        self.inner = inner
        self.name = inner.name
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.path = cache_dir / f"{inner.name}.jsonl"
        self._scores: dict[str, float] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self._scores[row["sha1"]] = row["score"]

    def score(self, text: str) -> float:
        key = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if key not in self._scores:
            self._scores[key] = self.inner.score(text)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sha1": key, "score": self._scores[key]}) + "\n")
        return self._scores[key]


def build_detectors(names: list[str]) -> list[Detector]:
    available = {
        "heuristic": lambda: HeuristicBaseline(),
        "promptguard-86m": lambda: CachedDetector(PromptGuard("86m")),
        "promptguard-22m": lambda: CachedDetector(PromptGuard("22m")),
    }
    unknown = [n for n in names if n not in available]
    if unknown:
        raise ValueError(f"unknown detector(s) {unknown}; choose from {sorted(available)}")
    return [available[n]() for n in names]

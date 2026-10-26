"""Classifier check: does untrusted content try to give the AI instructions?

Two layers, so the detector can be swapped later:
  Detector         predict(text) -> DetectorOutput      (heuristic now, trained model in Phase 4)
  ClassifierCheck  check(request) -> CheckResult        (scans only untrusted context items)

Heuristic signals were derived from the demo data: what the attacks (e10-e12, w2,
notes.txt) contain that the normal texts (e1-e3, w1, budget.txt) do not.
Money words alone ("taka", "send", "বিল", "পাঠা") are NOT a signal: normal Bangla
text is full of them. The attack signal is *talking to the AI*.

Signals combine as 1 - (1-w1)(1-w2)...: several weak signals add up, but one weak
signal alone never reaches the 0.5 flag line.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Protocol

from agentshield.core.models import CheckName, CheckResult, ContextItem, GuardRequest, Language
from agentshield.core.text import detect_language, normalize

FLAG_THRESHOLD = 0.5
_CACHE_LIMIT = 2000


@dataclass(frozen=True)
class DetectorOutput:
    score: float  # 0..1, how likely this text is a prompt injection
    language: Language
    signals: list[str] = field(default_factory=list)  # signal categories found
    matches: dict[str, str] = field(default_factory=dict)  # category -> matched snippet


class Detector(Protocol):
    name: str

    def predict(self, text: str) -> DetectorOutput: ...


# ---------------------------------------------------------------------------
# Heuristic detector
# ---------------------------------------------------------------------------

_PHONE = r"(?<!\d)(?:\+?88)?01\d{9}(?!\d)"

# category -> (weight, patterns). Patterns cover English, Bangla and Banglish spellings.
_SIGNALS: dict[str, tuple[float, list[str]]] = {
    # "Ignore all previous instructions" - the core of an injection.
    "override": (0.7, [
        r"\b(ignore|disregard|forget|override)\s+(all\s+|any\s+)?(the\s+|your\s+)?(previous|prior|above|earlier|original)\s+(instructions?|rules?|prompts?|messages?)",
        r"(আগের|পূর্ববর্তী|পূর্বের)\s*(সব|সকল|সমস্ত)?\s*(নির্দেশ\S*|কথা\S*)\s*(ভুলে\s*(যাও|যান|যা)|উপেক্ষা\s*\S*|বাদ\s*(দাও|দিন))",
        r"\b(ag(e|er|ey|her)|purber|previous)\s+(sob|shob|sab|shokol|all)?\s*(instructions?|instrakshon|nirdesh\w*|kotha|rules?)\s+(bhul|vul|ignore)\w*",
    ]),
    # Text that speaks to the AI instead of to the human reader.
    "ai_address": (0.4, [
        r"\b(note|message|instructions?|notice|attention)s?\s+(for|to)\s+(the\s+|all\s+)?(ai|assistant|llm|agent|bot)s?\b",
        r"\b(ai|llm)\s+(assistant|agent|model)s?\b",
        r"\b(ai|assistant|sohokari|shohokari)\s*(er|r)\s+(jonno|jnno|jonne)\b",
        r"(এআই|ai)\s*(সহকারী|সহায়ক|অ্যাসিস্ট্যান্ট)\S*",
        r"(সহকারী|সহায়ক)\S*\s*(জন্য|প্রতি|উদ্দেশ্যে)",
    ]),
    # Hide the action from the user.
    "secrecy": (0.45, [
        r"\b(do\s+not|don'?t|never)\s+(tell|inform|notify|mention\s+(this\s+)?to|alert)\s+(the\s+)?user\b",
        r"\bwithout\s+(telling|informing|notifying)\s+(the\s+)?user\b",
        r"\buser\s*(ke|k)?\s*(kichu|kisu|kicchu)?\s*(bol|jana)(ba|be|ben|bo|o)?\s*(na|nah)\b",
        r"\buser\s*(ke|k)?\s*(bolar|janano|janabar)\s*(dorkar|dorkaar)\s*(nai|nei|nay)\b",
        r"(ব্যবহারকারী|গ্রাহক|ইউজার)\S*\s*(কিছু\S*\s*)?(বলবে|বলবেন|বলো|জানাবে|জানাবেন|জানিও|জানানোর\s*দরকার)\s*না",
    ]),
    # "The user already approved this" - claimed permission.
    "fake_authority": (0.45, [
        r"\buser\s+(has\s+)?(already\s+)?(approved|authori[sz]ed|consented|given\s+(permission|consent))",
        r"\buser\s*(age|agei|already)?\s*(permission|onumoti)\s*(diyeche|diyechen|dise|disen|dichhe)",
        r"(ব্যবহারকারী|গ্রাহক|ইউজার)\S*\s*(আগেই|ইতিমধ্যে|ইতোমধ্যে)?\s*(অনুমতি|সম্মতি)\s*দি\S*",
    ]),
    # Text hidden from humans or dressed up as a system message.
    "hidden_block": (0.25, [
        r"<!--",
        r"\[\s*(system|সিস্টেম)",
        r"\bsystem\s+(notice|message|prompt|override)\b",
    ]),
    # An order to move money to a specific number (weak alone: real bills say this too).
    "action_with_number": (0.3, []),  # handled in code: imperative verb + phone number
    "urgency": (0.15, [
        r"\b(immediately|urgent(ly)?|right\s+now|asap)\b",
        r"\b(ekhoni|ekhuni|jaldi|taratari)\b",
        r"(এখনই|জরুরি|তাড়াতাড়ি|অবিলম্বে)",
    ]),
}

_ACTION_VERBS = [
    r"\b(send|transfer|pay|wire|deposit)\b",
    r"\b(pathao|pathan|pathiye\s+dao|pathay\s+dao|transfer\s+(koro|koren|kor))\b",
    r"(পাঠাও|পাঠান|পাঠিয়ে\s*দাও|পাঠিয়ে\s*দিন|ট্রান্সফার\s*কর\S*|পরিশোধ\s*কর\S*)",
]


def _compile(patterns: list[str]) -> list[re.Pattern[str]]:
    # Patterns go through the same normalize() as the text, so "য়" written as one
    # code point or as "য" + "়" matches either way.
    return [re.compile(normalize(p), re.IGNORECASE) for p in patterns]


_COMPILED = {name: _compile(patterns) for name, (_, patterns) in _SIGNALS.items()}
_WEIGHTS = {name: weight for name, (weight, _) in _SIGNALS.items()}
_ACTION_RE = _compile(_ACTION_VERBS)
_PHONE_RE = re.compile(_PHONE)


def _to_language(text: str) -> Language:
    try:
        return Language(detect_language(text))
    except ValueError:
        return Language.UNKNOWN


class HeuristicDetector:
    """Rule-based baseline. Phase 4's trained model replaces it with the same predict()."""

    name = "heuristic-v1"

    def predict(self, text: str) -> DetectorOutput:
        clean = normalize(text)
        matches: dict[str, str] = {}
        for category, patterns in _COMPILED.items():
            for pattern in patterns:
                found = pattern.search(clean)
                if found:
                    matches[category] = found.group()[:80]
                    break

        verb = next((m for p in _ACTION_RE if (m := p.search(clean))), None)
        phone = _PHONE_RE.search(clean)
        if verb and phone:
            matches["action_with_number"] = f"{verb.group()} ... {phone.group()}"

        remaining = 1.0
        for category in matches:
            remaining *= 1.0 - _WEIGHTS[category]
        return DetectorOutput(
            score=round(1.0 - remaining, 4),
            language=_to_language(clean),
            signals=list(matches),
            matches=matches,
        )


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------

_LABELS = {
    "override": ("overrides earlier instructions", "আগের নির্দেশ বাতিল করতে বলে"),
    "ai_address": ("speaks directly to the AI", "সরাসরি AI-কে উদ্দেশ্য করে লেখা"),
    "secrecy": ("tells the AI to hide it from the user", "ব্যবহারকারীর কাছে গোপন রাখতে বলে"),
    "fake_authority": ("claims the user already approved", "দাবি করে ব্যবহারকারী আগেই অনুমতি দিয়েছেন"),
    "hidden_block": ("hidden or fake system text", "লুকানো বা নকল system লেখা"),
    "action_with_number": ("orders a payment to a number", "একটা নম্বরে টাকা পাঠানোর আদেশ"),
    "urgency": ("creates urgency", "তাড়াহুড়ো করতে বলে"),
}


class ClassifierCheck:
    """Runs the detector on every untrusted context item and reports the worst one."""

    def __init__(self, detector: Detector | None = None, threshold: float = FLAG_THRESHOLD) -> None:
        self.detector = detector or HeuristicDetector()
        self.threshold = threshold
        self._cache: dict[tuple[str, str], DetectorOutput] = {}

    def _predict(self, item: ContextItem) -> DetectorOutput:
        # The whole context is re-checked on every tool call, so cache by item.
        key = (item.id, item.content)
        if key not in self._cache:
            if len(self._cache) >= _CACHE_LIMIT:
                self._cache.clear()
            self._cache[key] = self.detector.predict(item.content)
        return self._cache[key]

    def check(self, request: GuardRequest) -> CheckResult:
        start = time.perf_counter()
        items = request.untrusted_context()  # never the user's own words
        scanned = [(item, self._predict(item)) for item in items]

        def describe(item: ContextItem, out: DetectorOutput) -> dict:
            return {
                "item_id": item.id,
                "source": item.source.value,
                "origin": item.origin,
                "language": out.language.value,
                "score": out.score,
                "signals": out.signals,
                "matches": out.matches,
            }

        details: dict = {"detector": getattr(self.detector, "name", type(self.detector).__name__), "items_scanned": len(scanned)}
        if not scanned:
            return CheckResult(
                check=CheckName.CLASSIFIER,
                risk_score=0.0,
                reason_en="No untrusted content to scan.",
                reason_bn="স্ক্যান করার মতো কোনো অবিশ্বস্ত কনটেন্ট নেই।",
                details=details,
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        top_item, top = max(scanned, key=lambda pair: pair[1].score)
        flagged = top.score >= self.threshold
        details["top_item"] = describe(top_item, top)
        details["flagged_items"] = [describe(i, o) for i, o in scanned if o.score >= self.threshold]

        if flagged:
            where = top_item.source.value + (f" ({top_item.origin})" if top_item.origin else "")
            en = ", ".join(_LABELS.get(s, (s, s))[0] for s in top.signals)
            bn = ", ".join(_LABELS.get(s, (s, s))[1] for s in top.signals)
            reason_en = f"Possible prompt injection in {where}: {en}."
            reason_bn = f"{where}-এ AI-কে নির্দেশ দেওয়ার চেষ্টা পাওয়া গেছে: {bn}।"
        else:
            reason_en = "No injection signs in untrusted content."
            reason_bn = "অবিশ্বস্ত কনটেন্টে injection-এর কোনো লক্ষণ পাওয়া যায়নি।"

        return CheckResult(
            check=CheckName.CLASSIFIER,
            risk_score=top.score,
            flagged=flagged,
            reason_en=reason_en,
            reason_bn=reason_bn,
            details=details,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

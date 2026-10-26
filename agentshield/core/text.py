"""Text helpers shared by the checks (Bangla-aware normalization)."""

import re
import unicodedata

BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
DIGIT_COMMA_RE = re.compile(r"(?<=\d),(?=\d)")


def normalize(text: str) -> str:
    """NFC-normalize, turn Bangla digits into ASCII digits and drop thousands
    separators, so "৪,৫০০" and "4500" compare equal."""
    text = unicodedata.normalize("NFC", text).translate(BANGLA_DIGITS)
    return DIGIT_COMMA_RE.sub("", text)


def bangla_ratio(text: str) -> float:
    """Share of letters that are in the Bangla Unicode block."""
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    return sum("ঀ" <= ch <= "৿" for ch in letters) / len(letters)


BANGLISH_MARKERS = {
    "ami", "tumi", "apni", "koro", "koren", "jao", "bhai", "apu", "taka", "er", "ei",
    "ache", "hobe", "kichu", "na", "diben", "din", "pathao", "sob", "kal", "jonno", "nai",
}


def detect_language(text: str) -> str:
    """Rough language label: "bn" (Bangla script), "banglish" or "en"."""
    if bangla_ratio(text) > 0.3:
        return "bn"
    words = re.findall(r"[a-z]+", text.lower())
    hits = sum(word in BANGLISH_MARKERS for word in words)
    return "banglish" if hits >= 2 else "en"

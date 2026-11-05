"""Taint check: where did each tool-call argument come from?

For every argument value we look for it:
  1. in what the user (or system) wrote          -> "user"      (safe)
  2. in tool output (email, web, file, bank ...), newest first
                                                  -> "tool_data" (tainted, item remembered)
  3. nowhere                                      -> "unknown"   (the LLM made it up)

The details also list every tool item that holds an argument value, not only the
newest one, and say whether every value could be traced. The engine uses them to
score only the content a tool call really depends on.

Tool output never counts as user-provided, not even trusted tool:bank output:
an attacker's number that once landed in a transaction record must not look
like something the user typed.
"""

from __future__ import annotations

import re
import time
from fnmatch import fnmatch
from typing import Any, Iterable, Literal

from agentshield.checks.policy import normalize_id
from agentshield.core.models import CheckName, CheckResult, ContextItem, GuardRequest, SourceType

DEFAULT_SENSITIVE_TOOLS: frozenset[str] = frozenset(
    {"send_money", "send_email", "pay_bill", "transfer_*", "delete_*"}
)
MIN_VALUE_LENGTH = 3  # shorter values ("5", "ok") would match almost anywhere

_USER_SOURCES = {SourceType.USER, SourceType.SYSTEM}
_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
# A run of digits that may contain separators: "01799-999999", "৫,০০০", "+880 1711 111111".
# Runs are maximal, so "500" is never found inside "5000".
_NUMBER_RUN = re.compile(r"\+?\d(?:[\d,.\-]|\s(?=\d))*")
_NUMERIC = re.compile(r"\d+(?:\.\d+)?")

# Risk by (argument status, is the tool sensitive?)
_RISK = {
    ("tool_data", True): 0.9,
    ("unknown", True): 0.5,
    ("tool_data", False): 0.2,
    ("unknown", False): 0.1,
}

Status = Literal["user", "tool_data", "unknown", "ignored"]


def _normalize_value(value: Any) -> str:
    return normalize_id(value).replace(",", "").rstrip(".")


def _number_candidates(text: str) -> set[str]:
    """Every number in the text, as a whole run and as its separate parts."""
    found: set[str] = set()
    for match in _NUMBER_RUN.finditer(text.translate(_BN_DIGITS)):
        run = match.group()
        found.add(_normalize_value(run))
        found.update(_normalize_value(part) for part in re.split(r"[\s\-,]+", run) if part)
    return found


def _numbers_equal(a: str, b: str) -> bool:
    if a == b:
        return True
    # "5000" == "5000.00" for amounts; leading-zero IDs (phone numbers) must match exactly.
    if a.startswith("0") or b.startswith("0"):
        return False
    return float(a) == float(b)


def _appears_in(needle: str, numeric: bool, text: str) -> bool:
    if numeric:
        return any(
            _NUMERIC.fullmatch(c) and _numbers_equal(needle, c) for c in _number_candidates(text)
        )
    return needle.casefold() in text.casefold()


def _scalar_values(value: Any) -> Iterable[Any]:
    """Flatten lists/dicts so nested argument values are checked too."""
    if isinstance(value, dict):
        for v in value.values():
            yield from _scalar_values(v)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            yield from _scalar_values(v)
    elif value is not None and not isinstance(value, bool):
        yield value


class TaintChecker:
    """Traces each argument of a tool call back to its source."""

    def __init__(self, sensitive_tools: Iterable[str] = DEFAULT_SENSITIVE_TOOLS) -> None:
        self.sensitive_tools = frozenset(sensitive_tools)

    def is_sensitive(self, tool_name: str) -> bool:
        return any(fnmatch(tool_name, pattern) for pattern in self.sensitive_tools)

    def check(self, request: GuardRequest) -> CheckResult:
        start = time.perf_counter()
        sensitive = self.is_sensitive(request.tool_call.tool_name)

        user_texts = [request.user_request] + [
            item.content for item in request.context if item.source in _USER_SOURCES
        ]
        tool_items = [item for item in reversed(request.context) if item.source not in _USER_SOURCES]

        traced: dict[str, dict[str, Any]] = {}
        for name, raw in request.tool_call.arguments.items():
            traced[name] = self._trace(raw, user_texts, tool_items)

        risk = max(
            (_RISK.get((t["status"], sensitive), 0.0) for t in traced.values()), default=0.0
        )
        reason_en, reason_bn = self._reasons(traced)
        linked = dict.fromkeys(i for t in traced.values() for i in t.get("item_ids", []))
        return CheckResult(
            check=CheckName.TAINT,
            risk_score=risk,
            flagged=risk >= 0.5,
            reason_en=reason_en,
            reason_bn=reason_bn,
            details={
                "sensitive_tool": sensitive,
                "arguments": traced,
                "linked_item_ids": list(linked),
                "all_traced": all(t["fully_traced"] for t in traced.values()),
            },
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    # -- tracing ------------------------------------------------------------

    def _trace(self, raw: Any, user_texts: list[str], tool_items: list[ContextItem]) -> dict[str, Any]:
        """Trace one argument. With nested values, the worst status wins."""
        worst: dict[str, Any] = {"value": str(raw), "status": "ignored"}
        order = {"ignored": 0, "user": 1, "unknown": 2, "tool_data": 3}
        item_ids: dict[str, None] = {}
        fully_traced = True
        for value in _scalar_values(raw):
            result = self._trace_scalar(value, user_texts, tool_items)
            item_ids.update(dict.fromkeys(result.get("item_ids", [])))
            fully_traced = fully_traced and result["status"] in ("user", "tool_data")
            if order[result["status"]] > order[worst["status"]]:
                worst = {**result, "value": str(raw)}
        return {**worst, "item_ids": list(item_ids), "fully_traced": fully_traced}

    @staticmethod
    def _trace_scalar(value: Any, user_texts: list[str], tool_items: list[ContextItem]) -> dict[str, Any]:
        needle = _normalize_value(value)
        numeric = bool(_NUMERIC.fullmatch(needle))
        if not numeric:
            needle = str(value).strip()
        if len(needle) < MIN_VALUE_LENGTH:
            return {"status": "ignored"}

        if any(_appears_in(needle, numeric, text) for text in user_texts):
            return {"status": "user"}
        matches = [item for item in tool_items if _appears_in(needle, numeric, item.content)]
        if matches:
            newest = matches[0]  # tool_items is newest first
            return {
                "status": "tool_data",
                "item_id": newest.id,
                "item_ids": [item.id for item in matches],
                "source": newest.source.value,
                "origin": newest.origin,
            }
        return {"status": "unknown"}

    # -- reasons ------------------------------------------------------------

    @staticmethod
    def _reasons(traced: dict[str, dict[str, Any]]) -> tuple[str, str]:
        en: list[str] = []
        bn: list[str] = []
        for name, t in traced.items():
            arg = f"{name}={t['value']}"
            if t["status"] == "tool_data":
                where = t["source"] + (f" ({t['origin']})" if t.get("origin") else "")
                en.append(f"{arg} came from {where}, not from your request.")
                bn.append(f"{arg} এসেছে {where} থেকে, আপনার অনুরোধ থেকে না।")
            elif t["status"] == "unknown":
                en.append(f"{arg} is not in your request or in any data; the AI produced it itself.")
                bn.append(f"{arg} আপনার অনুরোধ বা কোনো ডাটায় নেই; AI নিজে মানটি বানিয়েছে।")
        if not en:
            return (
                "All arguments come from your request.",
                "সব argument আপনার অনুরোধ থেকে এসেছে।",
            )
        return " ".join(en), " ".join(bn)

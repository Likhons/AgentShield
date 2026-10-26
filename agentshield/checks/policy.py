"""Policy check: deterministic rules loaded from YAML.

"AI where judgment is needed, rules where certainty is needed."
This check never calls an LLM. When a rule matches it sets `forced_decision`,
so the engine must respect it no matter what the other checks say.
"""

from __future__ import annotations

import re
import time
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agentshield.core.models import CheckName, CheckResult, Decision, GuardRequest

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "policies" / "default.yaml"

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_SEVERITY = {Decision.ALLOW: 0, Decision.ASK_HUMAN: 1, Decision.BLOCK: 2}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_id(value: Any) -> str:
    """Normalize a phone number / account ID so different spellings compare equal.

    "+880 1711-111111", "01711111111" and "০১৭১১১১১১১১" all become "01711111111".
    """
    text = str(value).translate(_BN_DIGITS)
    text = re.sub(r"[\s\-().]", "", text).lower()
    if text.startswith("+88"):
        text = text[3:]
    elif text.startswith("88") and len(text) == 13:
        text = text[2:]
    return text


# A run of digits that may contain spaces/dashes between digits: "01799 999999", "+880 1711-111111".
_NUMBER_RUN = re.compile(r"\+?\d(?:[\d\-]|\s(?=\d))*")


def _numbers_in(text: str) -> set[str]:
    """Every whole number in the text: each run as one number, and each of its parts.

    Parts matter because spaces are allowed inside a run: in "to 01711111111 500"
    the run is "01711111111 500", and both "01711111111" and "500" must be found.
    """
    found: set[str] = set()
    for match in _NUMBER_RUN.finditer(str(text).translate(_BN_DIGITS)):
        run = match.group()
        found.add(normalize_id(run))
        found.update(normalize_id(part) for part in re.split(r"[\s\-]+", run) if part)
    return found


def mentioned_in(value: Any, text: str) -> bool:
    """True if `value` appears in `text`. Numbers must match whole: 01000000666 is not in 010000006661."""
    needle = normalize_id(value)
    if not needle:
        return False
    if needle.isdigit():
        return needle in _numbers_in(text)
    return needle in normalize_id(text)


def parse_amount(value: Any) -> float | None:
    """Read an amount like 5000, "5,000", "৫০০০ টাকা" or "Tk 5000". None if unreadable."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).translate(_BN_DIGITS).replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def _format_amount(value: float | None) -> str:
    if value is None:
        return "?"
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "?"


# ---------------------------------------------------------------------------
# YAML schema (validated, so a typo in the YAML fails loudly at startup)
# ---------------------------------------------------------------------------


class ArgumentRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    argument: str


class ArgumentThreshold(ArgumentRef):
    value: float


class Conditions(BaseModel):
    """All conditions that are set must be true for the rule to match."""

    model_config = ConfigDict(extra="forbid")

    tainted: bool | None = None
    argument_gt: ArgumentThreshold | None = None
    recipient_unknown: ArgumentRef | None = None
    not_mentioned_by_user: ArgumentRef | None = None


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str = ""
    tools: list[str] = Field(min_length=1, description="Tool names; glob patterns like 'delete_*' allowed.")
    when: Conditions = Field(default_factory=Conditions)
    decision: Decision
    risk: float = Field(ge=0.0, le=1.0)
    reason_en: str
    reason_bn: str

    @field_validator("decision")
    @classmethod
    def _no_allow_rules(cls, value: Decision) -> Decision:
        # A forced ALLOW would silently override the other checks. Not supported on purpose.
        if value == Decision.ALLOW:
            raise ValueError("policy rules may only ask_human or block")
        return value


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    currency: str = "BDT"
    rules: list[PolicyRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> PolicyConfig:
        ids = [rule.id for rule in self.rules]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"duplicate rule ids: {sorted(duplicates)}")
        return self


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class PolicyEngine:
    """Matches a GuardRequest against the policy rules and returns a CheckResult."""

    def __init__(self, config: PolicyConfig) -> None:
        self.config = config

    @classmethod
    def from_yaml(cls, path: str | Path = DEFAULT_POLICY_PATH) -> PolicyEngine:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(PolicyConfig.model_validate(data))

    def check(self, request: GuardRequest) -> CheckResult:
        start = time.perf_counter()
        matched = [rule for rule in self.config.rules if self._matches(rule, request)]
        latency_ms = (time.perf_counter() - start) * 1000

        if not matched:
            return CheckResult(
                check=CheckName.POLICY,
                risk_score=0.0,
                reason_en="No policy rule matched.",
                reason_bn="কোনো নীতিমালার নিয়ম মেলেনি।",
                details={"matched_rules": []},
                latency_ms=latency_ms,
            )

        top = max(matched, key=lambda r: (_SEVERITY[r.decision], r.risk))
        values = self._template_values(top, request)
        return CheckResult(
            check=CheckName.POLICY,
            risk_score=max(rule.risk for rule in matched),
            flagged=True,
            forced_decision=top.decision,
            reason_en=top.reason_en.format_map(values),
            reason_bn=top.reason_bn.format_map(values),
            details={"matched_rules": [rule.id for rule in matched], "top_rule": top.id},
            latency_ms=latency_ms,
        )

    # -- matching -----------------------------------------------------------

    def _matches(self, rule: PolicyRule, request: GuardRequest) -> bool:
        tool = request.tool_call.tool_name
        if not any(fnmatch(tool, pattern) for pattern in rule.tools):
            return False

        when = rule.when
        args = request.tool_call.arguments

        if when.tainted is not None and request.is_tainted != when.tainted:
            return False

        if when.argument_gt is not None:
            amount = parse_amount(args.get(when.argument_gt.argument, ""))
            # Fail-safe: an amount we cannot read counts as over the limit.
            if amount is not None and amount <= when.argument_gt.value:
                return False

        if when.recipient_unknown is not None:
            recipient = args.get(when.recipient_unknown.argument)
            known = {normalize_id(r) for r in request.known_recipients}
            if recipient is not None and normalize_id(recipient) in known:
                return False

        if when.not_mentioned_by_user is not None:
            value = args.get(when.not_mentioned_by_user.argument)
            if value is not None and mentioned_in(value, request.user_request):
                return False

        return True

    @staticmethod
    def _template_values(rule: PolicyRule, request: GuardRequest) -> _SafeDict:
        args = request.tool_call.arguments
        when = rule.when
        # Argument names come from the rule itself, so a tool with e.g. "recipient"/"value" still reads well.
        amount_arg = when.argument_gt.argument if when.argument_gt else "amount"
        recipient_ref = when.recipient_unknown or when.not_mentioned_by_user
        recipient_arg = recipient_ref.argument if recipient_ref else "to"

        values = _SafeDict(tool=request.tool_call.tool_name)
        if amount_arg in args:
            values["amount"] = _format_amount(parse_amount(args[amount_arg]))
        if recipient_arg in args:
            values["recipient"] = str(args[recipient_arg])
        if when.argument_gt is not None:
            values["limit"] = _format_amount(when.argument_gt.value)
        return values

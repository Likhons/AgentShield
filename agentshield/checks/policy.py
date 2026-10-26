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
            needle = normalize_id(value) if value is not None else ""
            if needle and needle in normalize_id(request.user_request):
                return False

        return True

    @staticmethod
    def _template_values(rule: PolicyRule, request: GuardRequest) -> _SafeDict:
        args = request.tool_call.arguments
        limit = rule.when.argument_gt.value if rule.when.argument_gt else None
        values = _SafeDict(tool=request.tool_call.tool_name)
        if "amount" in args:
            values["amount"] = _format_amount(parse_amount(args["amount"]))
        if "to" in args:
            values["recipient"] = str(args["to"])
        if limit is not None:
            values["limit"] = _format_amount(limit)
        return values

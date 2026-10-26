"""Core data models shared by every part of AgentShield.

Flow:
    GuardRequest (user request + proposed ToolCall + ContextItems)
        -> each check returns a CheckResult
        -> the engine combines them into a Verdict (ALLOW / ASK_HUMAN / BLOCK)
        -> the Verdict is stored as an AuditRecord

DatasetSample is used by the benchmark and the classifier training data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def _new_id() -> str:
    return uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    """Where a piece of text in the agent's context came from."""

    USER = "user"
    SYSTEM = "system"
    TOOL_EMAIL = "tool:email"
    TOOL_WEB = "tool:web"
    TOOL_FILE = "tool:file"
    TOOL_BANK = "tool:bank"  # structured data from our own banking backend
    TOOL_OTHER = "tool:other"


# Only text from these sources may give the agent instructions.
# TOOL_BANK is trusted because it is our own structured data (balance, limits).
# Free text inside it that a third party can write (e.g. a transfer memo)
# must be added as a separate TOOL_OTHER item instead.
TRUSTED_SOURCES: frozenset[SourceType] = frozenset(
    {SourceType.USER, SourceType.SYSTEM, SourceType.TOOL_BANK}
)


class Language(str, Enum):
    EN = "en"
    BN = "bn"  # Bangla script
    BANGLISH = "banglish"  # Bangla written in Latin script
    MIXED = "mixed"  # code-mixed Bangla + English
    UNKNOWN = "unknown"


class Decision(str, Enum):
    ALLOW = "allow"
    ASK_HUMAN = "ask_human"
    BLOCK = "block"


class CheckName(str, Enum):
    TAINT = "taint"
    CLASSIFIER = "classifier"
    INTENT = "intent"
    POLICY = "policy"


class AttackType(str, Enum):
    DIRECT = "direct"  # attacker types into the chat
    INDIRECT_EMAIL = "indirect_email"  # hidden inside an email the agent reads
    INDIRECT_WEB = "indirect_web"  # hidden inside a web page
    INDIRECT_FILE = "indirect_file"  # hidden inside a document


# ---------------------------------------------------------------------------
# Request side
# ---------------------------------------------------------------------------


class ContextItem(BaseModel):
    """One piece of text the agent has seen, labeled with its source (taint label)."""

    id: str = Field(default_factory=_new_id)
    content: str
    source: SourceType
    origin: str | None = None  # e.g. "email:42" or a URL
    language: Language = Language.UNKNOWN

    @property
    def is_trusted(self) -> bool:
        return self.source in TRUSTED_SOURCES


class ToolCall(BaseModel):
    """A tool call the agent wants to make. Nothing runs until AgentShield allows it."""

    id: str = Field(default_factory=_new_id)
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    derived_from: list[str] = Field(
        default_factory=list,
        description="IDs of ContextItems that led the agent to make this call.",
    )


class GuardRequest(BaseModel):
    """Everything AgentShield needs to judge one tool call."""

    id: str = Field(default_factory=_new_id)
    session_id: str = "default"
    user_request: str
    tool_call: ToolCall
    context: list[ContextItem] = Field(default_factory=list)
    known_recipients: list[str] = Field(
        default_factory=list,
        description="This user's saved contacts (phone numbers / account IDs). Used by the policy check.",
    )

    def untrusted_context(self) -> list[ContextItem]:
        return [item for item in self.context if not item.is_trusted]

    def sources_of_call(self) -> list[ContextItem]:
        """The context items this tool call was derived from."""
        wanted = set(self.tool_call.derived_from)
        return [item for item in self.context if item.id in wanted]

    @property
    def is_tainted(self) -> bool:
        """True if the call may have been influenced by untrusted data.

        Fail-safe: when we cannot tell where the call came from (no
        `derived_from`, or IDs we don't recognize), any untrusted item in the
        context counts. Precise tracing (e.g. matching argument values against
        email text) lives in checks/taint.py.
        """
        wanted = set(self.tool_call.derived_from)
        sources = self.sources_of_call()
        if not wanted or len(sources) < len(wanted):
            return bool(self.untrusted_context())
        return any(not item.is_trusted for item in sources)

    def is_known_recipient(self, recipient: str) -> bool:
        return recipient.strip() in {r.strip() for r in self.known_recipients}


# ---------------------------------------------------------------------------
# Result side
# ---------------------------------------------------------------------------


class CheckResult(BaseModel):
    """Output of a single check (taint, classifier, intent or policy)."""

    check: CheckName
    risk_score: float = Field(ge=0.0, le=1.0)
    flagged: bool = False
    skipped: bool = Field(
        default=False,
        description="True if the check did not run (e.g. intent check skipped to save LLM calls).",
    )
    reason_en: str = ""
    reason_bn: str = ""
    forced_decision: Decision | None = Field(
        default=None,
        description="Set by deterministic checks (e.g. policy) to override the score.",
    )
    details: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = Field(default=0.0, ge=0.0)


class DecisionThresholds(BaseModel):
    """Maps a combined risk score to a decision."""

    ask_human_at: float = Field(default=0.4, ge=0.0, le=1.0)
    block_at: float = Field(default=0.75, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_order(self) -> DecisionThresholds:
        if self.ask_human_at > self.block_at:
            raise ValueError("ask_human_at must be <= block_at")
        return self

    def decide(self, risk_score: float) -> Decision:
        if risk_score >= self.block_at:
            return Decision.BLOCK
        if risk_score >= self.ask_human_at:
            return Decision.ASK_HUMAN
        return Decision.ALLOW


class Verdict(BaseModel):
    """AgentShield's final answer for one GuardRequest."""

    request_id: str
    decision: Decision
    risk_score: float = Field(ge=0.0, le=1.0)
    reason_en: str
    reason_bn: str
    checks: list[CheckResult] = Field(default_factory=list)
    total_latency_ms: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=_now)

    @property
    def allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    def flagged_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if c.flagged]

    @property
    def llm_called(self) -> bool:
        """True if the intent check actually ran (KPI: how often we call the LLM)."""
        return any(c.check == CheckName.INTENT and not c.skipped for c in self.checks)


class AuditRecord(BaseModel):
    """Flat row written to the SQLite audit log and shown on the dashboard."""

    id: str = Field(default_factory=_new_id)
    timestamp: datetime = Field(default_factory=_now)
    session_id: str
    request_id: str
    user_request: str
    tool_name: str
    arguments: dict[str, Any]
    tainted: bool
    decision: Decision
    risk_score: float
    reason_en: str
    reason_bn: str
    checks: list[CheckResult]
    total_latency_ms: float

    @classmethod
    def from_verdict(cls, request: GuardRequest, verdict: Verdict) -> AuditRecord:
        return cls(
            session_id=request.session_id,
            request_id=request.id,
            user_request=request.user_request,
            tool_name=request.tool_call.tool_name,
            arguments=request.tool_call.arguments,
            tainted=request.is_tainted,
            decision=verdict.decision,
            risk_score=verdict.risk_score,
            reason_en=verdict.reason_en,
            reason_bn=verdict.reason_bn,
            checks=verdict.checks,
            total_latency_ms=verdict.total_latency_ms,
        )


# ---------------------------------------------------------------------------
# Dataset / benchmark
# ---------------------------------------------------------------------------


class DatasetSample(BaseModel):
    """One labeled example for the benchmark and classifier training."""

    id: str = Field(default_factory=_new_id)
    text: str
    language: Language
    label: Literal["attack", "benign"]
    attack_type: AttackType | None = None
    target_tool: str | None = None  # e.g. "send_money"
    source: Literal["hand_written", "llm_generated", "external"] = "hand_written"
    notes: str = ""

    @model_validator(mode="after")
    def _attack_needs_type(self) -> DatasetSample:
        if self.label == "attack" and self.attack_type is None:
            raise ValueError("attack samples need an attack_type")
        if self.label == "benign" and self.attack_type is not None:
            raise ValueError("benign samples must not have an attack_type")
        return self

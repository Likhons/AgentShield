"""SDK: protect any agent's tools with AgentShield in two lines.

    session = ShieldSession(engine, user_request=task, known_recipients=contacts)
    protected = session.wrap("send_money", send_money, source="tool:bank")

Every wrapped call is checked by the engine before it runs, and every tool
output is remembered with its source label, which is what the taint check needs.
Framework-agnostic: wrap() takes a plain function and returns a plain function.
"""

from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, Iterable
from uuid import uuid4

from agentshield.core.models import ContextItem, Decision, GuardRequest, SourceType, ToolCall, Verdict

logger = logging.getLogger(__name__)

Approver = Callable[[ToolCall, Verdict], bool]
ToolFunc = Callable[..., Any]

# Tool output can never be labeled as if the user or system wrote it.
_NOT_FOR_TOOLS = {SourceType.USER, SourceType.SYSTEM}


def to_source(source: str | SourceType) -> SourceType:
    """Map a label like "tool:email" to SourceType. Unknown labels become TOOL_OTHER (untrusted)."""
    if isinstance(source, SourceType):
        return source
    try:
        return SourceType(source)
    except ValueError:
        logger.warning("unknown source label %r, treating it as untrusted tool:other", source)
        return SourceType.TOOL_OTHER


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)


class ShieldSession:
    """One user task: keeps the context, checks every tool call, records every tool output."""

    def __init__(
        self,
        engine: Any,
        user_request: str,
        known_recipients: Iterable[str] = (),
        approver: Approver | None = None,
        session_id: str | None = None,
    ) -> None:
        self.engine = engine
        self.user_request = user_request
        self.known_recipients = list(known_recipients)
        self.approver = approver  # None = nobody to ask, so ASK_HUMAN means "no"
        self.session_id = session_id or uuid4().hex[:12]
        self.context: list[ContextItem] = [ContextItem(content=user_request, source=SourceType.USER)]
        self.history: list[tuple[ToolCall, Verdict]] = []

    def record(self, content: Any, source: str | SourceType, origin: str | None = None) -> ContextItem:
        """Add something the agent has seen to the context, with its source label."""
        item = ContextItem(content=_as_text(content), source=to_source(source), origin=origin)
        self.context.append(item)
        return item

    def guard(self, tool_name: str, arguments: dict[str, Any]) -> Verdict:
        """Ask the engine about one tool call and remember the answer."""
        call = ToolCall(tool_name=tool_name, arguments=dict(arguments))
        request = GuardRequest(
            session_id=self.session_id,
            user_request=self.user_request,
            tool_call=call,
            context=list(self.context),
            known_recipients=self.known_recipients,
        )
        verdict = self.engine.check(request)
        self.history.append((call, verdict))
        return verdict

    def wrap(self, name: str, func: ToolFunc, source: str | SourceType) -> ToolFunc:
        """Return a protected version of `func` that only runs when AgentShield allows it."""
        label = to_source(source)
        if label in _NOT_FOR_TOOLS:
            raise ValueError(f"tool '{name}' cannot use source '{label.value}': tool output is never user/system text")

        @functools.wraps(func)
        def protected(**kwargs: Any) -> Any:
            call_verdict = self.guard(name, kwargs)
            call = self.history[-1][0]

            if call_verdict.decision == Decision.BLOCK:
                return f"[AgentShield] {call_verdict.reason_en}"
            if call_verdict.decision == Decision.ASK_HUMAN and not self._approved(call, call_verdict):
                return f"[AgentShield] Not approved by the user. {call_verdict.reason_en}"

            result = func(**kwargs)
            self.record(result, label, origin=name)
            return result

        return protected

    def wrap_all(self, tools: dict[str, tuple[ToolFunc, str | SourceType]]) -> dict[str, ToolFunc]:
        """Wrap many tools at once: {"send_money": (send_money, "tool:bank"), ...}."""
        return {name: self.wrap(name, func, source) for name, (func, source) in tools.items()}

    def _approved(self, call: ToolCall, verdict: Verdict) -> bool:
        if self.approver is None:
            return False
        try:
            return self.approver(call, verdict) is True  # only an explicit True approves
        except Exception:
            logger.exception("approver failed; treating as not approved")
            return False

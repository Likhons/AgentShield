"""Decision engine: runs the four checks and turns their reports into one Verdict.

Order:  taint (always, cheap) -> classifier -> intent (LLM, only when needed) -> policy
Score:  taint * 0.3 + classifier * 0.3 + intent * 0.4   (skipped checks count as 0)
Final:  the stricter of (score decision, policy forced decision, check-error floor)

The weights are fixed and NOT re-normalized when a check is skipped. Otherwise
taint alone would reach 0.9 and a legitimate bill payment would be blocked.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Protocol

from pydantic import BaseModel, Field

from agentshield.checks.intent import RISK_UNVERIFIED, IntentChecker
from agentshield.checks.policy import DEFAULT_POLICY_PATH, PolicyEngine
from agentshield.checks.taint import TaintChecker
from agentshield.core.models import (
    AuditRecord,
    CheckName,
    CheckResult,
    Decision,
    DecisionThresholds,
    GuardRequest,
    Verdict,
)

logger = logging.getLogger(__name__)

_SEVERITY = {Decision.ALLOW: 0, Decision.ASK_HUMAN: 1, Decision.BLOCK: 2}
_HEADERS = {
    Decision.ALLOW: ("Allowed.", "অনুমতি দেওয়া হয়েছে।"),
    Decision.ASK_HUMAN: ("Needs your approval.", "আপনার অনুমতি প্রয়োজন।"),
    Decision.BLOCK: ("Blocked.", "আটকানো হয়েছে।"),
}


class Checker(Protocol):
    def check(self, request: GuardRequest) -> CheckResult: ...


class AuditSink(Protocol):
    def write(self, record: AuditRecord) -> Any: ...


class CheckWeights(BaseModel):
    taint: float = Field(default=0.3, ge=0.0)
    classifier: float = Field(default=0.3, ge=0.0)
    intent: float = Field(default=0.4, ge=0.0)


def _stricter(a: Decision, b: Decision | None) -> Decision:
    if b is None:
        return a
    return a if _SEVERITY[a] >= _SEVERITY[b] else b


class Engine:
    """Combines taint, classifier, intent and policy into a single Verdict."""

    def __init__(
        self,
        policy: PolicyEngine,
        taint: TaintChecker,
        intent: IntentChecker | None = None,
        classifier: Checker | None = None,
        thresholds: DecisionThresholds | None = None,
        weights: CheckWeights | None = None,
        audit: AuditSink | None = None,
    ) -> None:
        self.policy = policy
        self.taint = taint
        self.intent = intent
        self.classifier = classifier
        self.thresholds = thresholds or DecisionThresholds()
        self.weights = weights or CheckWeights()
        self.audit = audit

    def check(self, request: GuardRequest) -> Verdict:
        start = time.perf_counter()

        taint = self._safe_run(CheckName.TAINT, self.taint.check, request)
        classifier = self._run_classifier(request)
        intent = self._run_intent(request, taint, classifier)
        policy = self._safe_run(CheckName.POLICY, self.policy.check, request)
        checks = [taint, classifier, intent, policy]

        weighted = self._weighted_score(taint, classifier, intent)
        decision = self.thresholds.decide(weighted)
        for result in checks:
            decision = _stricter(decision, result.forced_decision)

        reason_en, reason_bn = self._reasons(decision, checks, policy)
        verdict = Verdict(
            request_id=request.id,
            decision=decision,
            risk_score=round(min(1.0, max(weighted, policy.risk_score)), 4),
            reason_en=reason_en,
            reason_bn=reason_bn,
            checks=checks,
            total_latency_ms=(time.perf_counter() - start) * 1000,
        )
        self._write_audit(request, verdict)
        return verdict

    # -- running checks ----------------------------------------------------

    @staticmethod
    def _safe_run(name: CheckName, fn: Callable[[GuardRequest], CheckResult], request: GuardRequest) -> CheckResult:
        """Run a check; a crash becomes a flagged medium-risk result that can never allow."""
        try:
            return fn(request)
        except Exception as exc:
            logger.exception("%s check crashed", name.value)
            return CheckResult(
                check=name,
                risk_score=RISK_UNVERIFIED,
                flagged=True,
                forced_decision=Decision.ASK_HUMAN,
                reason_en=f"The {name.value} check failed; treated as medium risk.",
                reason_bn=f"{name.value} check-এ সমস্যা হয়েছে; মাঝারি ঝুঁকি ধরা হয়েছে।",
                details={"error": f"{type(exc).__name__}: {exc}"[:300]},
            )

    def _run_classifier(self, request: GuardRequest) -> CheckResult:
        if self.classifier is None:
            return CheckResult(
                check=CheckName.CLASSIFIER,
                risk_score=0.0,
                skipped=True,
                reason_en="Classifier not configured.",
                reason_bn="Classifier এখনো যুক্ত করা হয়নি।",
                details={"skip_reason": "not configured"},
            )
        return self._safe_run(CheckName.CLASSIFIER, self.classifier.check, request)

    def _run_intent(self, request: GuardRequest, taint: CheckResult, classifier: CheckResult) -> CheckResult:
        try:
            sensitive = self.taint.is_sensitive(request.tool_call.tool_name)
        except Exception:
            sensitive = True  # fail-safe
        if not sensitive:
            return IntentChecker.skipped("tool is not sensitive")
        if not (taint.flagged or classifier.flagged):
            return IntentChecker.skipped("cheaper checks found no risk")
        if self.intent is None:
            # Judgment was needed but no LLM is available: same as an LLM outage.
            return CheckResult(
                check=CheckName.INTENT,
                risk_score=RISK_UNVERIFIED,
                flagged=True,
                reason_en="Could not verify intent (no LLM configured); treated as medium risk.",
                reason_bn="উদ্দেশ্য যাচাই করা যায়নি (কোনো LLM যুক্ত নেই); মাঝারি ঝুঁকি ধরা হয়েছে।",
                details={"error": "no LLM provider configured"},
            )
        return self._safe_run(CheckName.INTENT, self.intent.check, request)

    def _weighted_score(self, taint: CheckResult, classifier: CheckResult, intent: CheckResult) -> float:
        def value(result: CheckResult) -> float:
            return 0.0 if result.skipped else result.risk_score

        w = self.weights
        return w.taint * value(taint) + w.classifier * value(classifier) + w.intent * value(intent)

    # -- output ------------------------------------------------------------

    @staticmethod
    def _reasons(decision: Decision, checks: list[CheckResult], policy: CheckResult) -> tuple[str, str]:
        header_en, header_bn = _HEADERS[decision]
        flagged = [c for c in checks if c.flagged and not c.skipped]
        # A policy rule that decided the outcome explains it best, so it goes first.
        if policy in flagged and policy.forced_decision is not None:
            flagged.remove(policy)
            flagged.insert(0, policy)
        if not flagged:
            return f"{header_en} No risk found.", f"{header_bn} কোনো ঝুঁকি পাওয়া যায়নি।"
        en = " ".join([header_en] + [c.reason_en for c in flagged if c.reason_en])
        bn = " ".join([header_bn] + [c.reason_bn for c in flagged if c.reason_bn])
        return en, bn

    def _write_audit(self, request: GuardRequest, verdict: Verdict) -> None:
        if self.audit is None:
            return
        try:
            self.audit.write(AuditRecord.from_verdict(request, verdict))
        except Exception:
            logger.exception("could not write audit record")  # never break the agent over logging


def build_default_engine(policy_path: str | Path = DEFAULT_POLICY_PATH, audit: AuditSink | None = None) -> Engine:
    """Wire up the default engine. Without a working LLM provider, intent is None (fail-safe)."""
    intent: IntentChecker | None = None
    try:
        from agentshield.llm import get_provider

        intent = IntentChecker(get_provider())
    except Exception:
        logger.warning("no LLM provider available; intent check will report 'unverified'", exc_info=True)
    return Engine(
        policy=PolicyEngine.from_yaml(policy_path),
        taint=TaintChecker(),
        intent=intent,
        audit=audit,
    )

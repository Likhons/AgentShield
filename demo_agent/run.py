"""Run demo scenarios against the banking agent, with or without AgentShield.

Examples (PowerShell, venv active):
    python -m demo_agent.run                          # Bangla attack, unprotected
    python -m demo_agent.run --shield                 # same attack, protected by AgentShield
    python -m demo_agent.run --compare --all          # every scenario, side by side
    python -m demo_agent.run --scenario attack_bill_bn --shield --provider groq
    python -m demo_agent.run --list
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, replace

from agentshield.audit.log import AuditLog
from agentshield.checks.classifier import ClassifierCheck
from agentshield.checks.intent import IntentChecker
from agentshield.checks.policy import PolicyEngine
from agentshield.checks.taint import TaintChecker
from agentshield.config import get_settings
from agentshield.core.engine import Engine
from agentshield.core.models import ToolCall, Verdict
from agentshield.llm import get_provider
from agentshield.sdk.session import ShieldSession
from demo_agent.agent import AgentRun, BankingAgent, Step
from demo_agent.scenarios import Outcome, build_world, judge_outcome, load_scenarios

ICONS = {"allow": "ALLOW", "ask_human": "ASK_HUMAN", "block": "BLOCK"}


@dataclass
class ScenarioResult:
    """Everything one scenario run produced."""

    name: str
    run: AgentRun
    outcome: Outcome
    start_balance: int
    end_balance: int
    shielded: bool
    history: list[tuple[ToolCall, Verdict]] = field(default_factory=list)
    step_verdicts: list[Verdict | None] = field(default_factory=list)  # one per step, None if unchecked


def match_verdicts(steps: list[Step], history: list[tuple[ToolCall, Verdict]]) -> list[Verdict | None]:
    """Pair each agent step with its AgentShield verdict. Both happen in the same order;
    a step for an unknown tool never reached AgentShield and gets None."""
    queue = list(history)
    matched: list[Verdict | None] = []
    for step in steps:
        if queue and queue[0][0].tool_name == step.tool:
            matched.append(queue.pop(0)[1])
        else:
            matched.append(None)
    return matched


def build_engine(provider: str | None = None, model: str | None = None, audit: AuditLog | None = None) -> Engine:
    """AgentShield engine whose intent judge uses the same LLM provider as the agent."""
    return Engine(
        policy=PolicyEngine.from_yaml(),
        taint=TaintChecker(),
        intent=IntentChecker(get_provider(provider, model)),
        classifier=ClassifierCheck(),
        audit=audit,
    )


def run_scenario(
    name: str,
    provider: str | None = None,
    model: str | None = None,
    shield: bool = False,
    audit: AuditLog | None = None,
    approve: bool = False,
) -> ScenarioResult:
    """Run one scenario. With shield=True every tool call goes through AgentShield first."""
    scenario = load_scenarios()[name]
    world = build_world(scenario)
    start = world.balance
    tools = world.tool_specs()
    session = None

    if shield:
        session = ShieldSession(
            build_engine(provider, model, audit),
            user_request=scenario["user_task"],
            known_recipients=world.contacts.values(),
            approver=(lambda call, verdict: True) if approve else None,
        )
        tools = {n: replace(s, func=session.wrap(n, s.func, s.source)) for n, s in tools.items()}

    run = BankingAgent(get_provider(provider, model), tools).run(scenario["user_task"])
    history = session.history if session else []
    return ScenarioResult(
        name=name,
        run=run,
        outcome=judge_outcome(world, scenario),
        start_balance=start,
        end_balance=world.balance,
        shielded=shield,
        history=history,
        step_verdicts=match_verdicts(run.steps, history) if shield else [None] * len(run.steps),
    )


def shorten(text: str, limit: int = 160) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


def summary(result: ScenarioResult) -> str:
    if result.outcome.stolen:
        return f"STOLEN {result.outcome.stolen} BDT"
    blocked = sum(1 for _, v in result.history if v.decision.value != "allow")
    return f"safe ({blocked} stopped)" if blocked else "safe"


def print_run(result: ScenarioResult) -> None:
    label = "WITH AgentShield" if result.shielded else "without AgentShield"
    print(f"\n=== Scenario: {result.name} ({label}) ===")
    print(f"User: {result.run.task}")
    for step, verdict in zip(result.run.steps, result.step_verdicts):
        print(f"[step {step.number}] {step.tool} {json.dumps(step.args, ensure_ascii=False)}")
        if verdict and (verdict.decision.value != "allow" or step.tool == "send_money"):
            print(f"    AgentShield: {ICONS[verdict.decision.value]} (risk {verdict.risk_score:.2f}, {verdict.total_latency_ms:.0f} ms)")
            print(f"    reason: {shorten(verdict.reason_en, 220)}")
            print(f"    কারণ:   {shorten(verdict.reason_bn, 220)}")
        print(f"    -> {shorten(step.result)}")
    print(f"Agent final answer: {shorten(result.run.final_answer, 200)}")
    print(f"Balance: {result.start_balance} -> {result.end_balance} BDT")
    if result.outcome.stolen:
        targets = ", ".join(t.to for t in result.outcome.unauthorized)
        print(f"RESULT: MONEY STOLEN! {result.outcome.stolen} BDT sent to {targets}, which the user never asked for.")
    else:
        print("RESULT: safe, no unauthorized transfers.")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # so Bangla text prints correctly
    parser = argparse.ArgumentParser(description="Run the demo banking agent.")
    parser.add_argument("--scenario", default="attack_email_bn")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--list", action="store_true", help="list scenarios")
    parser.add_argument("--shield", action="store_true", help="protect the agent with AgentShield")
    parser.add_argument("--compare", action="store_true", help="run without and with AgentShield")
    parser.add_argument("--approve", action="store_true", help="simulate a human who approves every ASK_HUMAN")
    parser.add_argument("--provider", help="override LLM_PROVIDER (mock / gemini / groq)")
    parser.add_argument("--model", help="override LLM_MODEL")
    args = parser.parse_args()

    scenarios = load_scenarios()
    if args.list:
        for name, s in scenarios.items():
            print(f"{name:24} {s['description']}")
        return

    names = list(scenarios) if args.all else [args.scenario]
    modes = [False, True] if args.compare else [args.shield]
    audit = AuditLog(get_settings().audit_db_path) if True in modes else None

    rows = []
    for name in names:
        results = [run_scenario(name, args.provider, args.model, shield, audit, args.approve) for shield in modes]
        for result in results:
            print_run(result)
        rows.append((name, results))

    if len(names) > 1 or args.compare:
        print("\n=== Summary ===")
        header = "without AgentShield".ljust(22) + "with AgentShield" if args.compare else ("with" if args.shield else "without") + " AgentShield"
        print(f"{'scenario':24} {header}")
        for name, results in rows:
            print(f"{name:24} " + "".join(summary(r).ljust(22) for r in results))
    if audit:
        print(f"\nAudit log: {get_settings().audit_db_path}  {audit.stats()}")
        audit.close()


if __name__ == "__main__":
    main()

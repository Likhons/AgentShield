"""Run demo scenarios against the UNPROTECTED banking agent.

Examples (PowerShell, venv active):
    python -m demo_agent.run                          # Bangla attack scenario
    python -m demo_agent.run --scenario attack_email_en
    python -m demo_agent.run --all                    # every scenario + summary
    python -m demo_agent.run --list
"""

import argparse
import json
import sys

from agentshield.llm import get_provider
from demo_agent.agent import AgentRun, BankingAgent
from demo_agent.scenarios import Outcome, build_world, judge_outcome, load_scenarios


def run_scenario(
    name: str, provider: str | None = None, model: str | None = None
) -> tuple[AgentRun, Outcome, int, int]:
    """Run one scenario. Returns the agent run, outcome, start and end balance."""
    scenario = load_scenarios()[name]
    world = build_world(scenario)
    start = world.balance
    agent = BankingAgent(get_provider(provider, model), world.tool_specs())
    run = agent.run(scenario["user_task"])
    return run, judge_outcome(world, scenario["user_task"]), start, world.balance


def shorten(text: str, limit: int = 160) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


def print_run(name: str, run: AgentRun, outcome: Outcome, start: int, end: int) -> None:
    print(f"\n=== Scenario: {name} ===")
    print(f"User: {run.task}")
    for step in run.steps:
        print(f"[step {step.number}] {step.tool} {json.dumps(step.args, ensure_ascii=False)}")
        print(f"    -> {shorten(step.result)}")
    print(f"Agent final answer: {shorten(run.final_answer, 200)}")
    print(f"Balance: {start} -> {end} BDT")
    if outcome.stolen:
        targets = ", ".join(t.to for t in outcome.unauthorized)
        print(f"RESULT: MONEY STOLEN! {outcome.stolen} BDT sent to {targets}, which the user never asked for.")
    else:
        print("RESULT: safe, no unauthorized transfers.")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # so Bangla text prints correctly
    parser = argparse.ArgumentParser(description="Run the vulnerable demo agent (no AgentShield).")
    parser.add_argument("--scenario", default="attack_email_bn")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--list", action="store_true", help="list scenarios")
    parser.add_argument("--provider", help="override LLM_PROVIDER (mock / gemini / groq)")
    parser.add_argument("--model", help="override LLM_MODEL")
    args = parser.parse_args()

    scenarios = load_scenarios()
    if args.list:
        for name, s in scenarios.items():
            print(f"{name:24} {s['description']}")
        return

    names = list(scenarios) if args.all else [args.scenario]
    summary = []
    for name in names:
        run, outcome, start, end = run_scenario(name, args.provider, args.model)
        print_run(name, run, outcome, start, end)
        summary.append((name, outcome.stolen))

    if args.all:
        print("\n=== Summary (without AgentShield) ===")
        for name, stolen in summary:
            print(f"{name:24} {'STOLEN ' + str(stolen) + ' BDT' if stolen else 'safe'}")


if __name__ == "__main__":
    main()

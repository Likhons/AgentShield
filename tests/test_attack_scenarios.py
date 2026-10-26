"""End-to-end: the UNPROTECTED agent is tricked by every attack, benign tasks stay safe.

When AgentShield is added (Phase 2), a second test file will show the same
attacks being blocked.
"""

import pytest

from demo_agent.agent import parse_action
from demo_agent.run import run_scenario
from demo_agent.scenarios import load_scenarios

ATTACKS = [name for name in load_scenarios() if name.startswith("attack_")]
BENIGN = [name for name in load_scenarios() if name.startswith("benign_")]


@pytest.mark.parametrize("name", ATTACKS)
def test_attack_steals_money_without_agentshield(name: str) -> None:
    _, outcome, start, end = run_scenario(name, provider="mock")
    assert outcome.stolen > 0
    assert end == start - outcome.stolen


@pytest.mark.parametrize("name", BENIGN)
def test_benign_scenario_is_safe(name: str) -> None:
    run, outcome, _, _ = run_scenario(name, provider="mock")
    assert outcome.stolen == 0
    assert run.final_answer


def test_benign_send_really_sends() -> None:
    run, _, start, end = run_scenario("benign_send", provider="mock")
    assert run.steps[0].tool == "send_money"
    assert end == start - 500


def test_parse_action_handles_code_fences_and_plain_text() -> None:
    assert parse_action('```json\n{"action": "final", "answer": "hi"}\n```') == {
        "action": "final",
        "answer": "hi",
    }
    assert parse_action("I am just text") is None

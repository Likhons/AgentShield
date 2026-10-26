"""End-to-end: every attack steals money from the UNPROTECTED agent and is
stopped once the same agent's tools are wrapped with AgentShield; benign tasks
keep working in both modes. All runs use the offline mock LLM.
"""

import pytest

from agentshield.audit.log import AuditLog
from demo_agent.agent import parse_action
from demo_agent.run import run_scenario
from demo_agent.scenarios import load_scenarios

ATTACKS = [name for name in load_scenarios() if name.startswith("attack_")]
BENIGN = [name for name in load_scenarios() if name.startswith("benign_")]


# ---- without AgentShield ---------------------------------------------------


@pytest.mark.parametrize("name", ATTACKS)
def test_attack_steals_money_without_agentshield(name: str) -> None:
    result = run_scenario(name, provider="mock")
    assert result.outcome.stolen > 0
    assert result.start_balance - result.end_balance >= result.outcome.stolen


@pytest.mark.parametrize("name", BENIGN)
def test_benign_scenario_is_safe_without_agentshield(name: str) -> None:
    result = run_scenario(name, provider="mock")
    assert result.outcome.stolen == 0
    assert result.run.final_answer


def test_benign_send_really_sends() -> None:
    result = run_scenario("benign_send", provider="mock")
    assert result.run.steps[0].tool == "send_money"
    assert result.end_balance == result.start_balance - 500


# ---- with AgentShield ------------------------------------------------------


@pytest.mark.parametrize("name", ATTACKS)
def test_attack_is_stopped_with_agentshield(name: str) -> None:
    result = run_scenario(name, provider="mock", shield=True)
    assert result.outcome.stolen == 0
    stopped = [v for c, v in result.history if c.tool_name == "send_money" and v.decision.value != "allow"]
    assert stopped, "the malicious send_money must be stopped"
    assert all(v.reason_bn for v in stopped)


@pytest.mark.parametrize("name", BENIGN)
def test_benign_scenario_still_works_with_agentshield(name: str) -> None:
    without = run_scenario(name, provider="mock")
    with_shield = run_scenario(name, provider="mock", shield=True)
    assert with_shield.outcome.stolen == 0
    assert with_shield.end_balance == without.end_balance  # same legitimate payments happen


@pytest.mark.parametrize("name", ["attack_bill_bn", "attack_bill_en", "attack_bill_banglish"])
def test_fake_bill_blocked_but_landlord_paid(name: str) -> None:
    result = run_scenario(name, provider="mock", shield=True)
    paid = {t["to"] for t in [s.args for s in result.run.steps if s.tool == "send_money" and s.result.startswith("Sent")]}
    assert paid == {"01000000102"}
    assert result.end_balance == result.start_balance - 8000


def test_judge_can_use_its_own_model(monkeypatch) -> None:
    import demo_agent.run as run_module
    from agentshield.llm.mock import MockProvider

    asked: list[tuple] = []

    def fake_get_provider(provider=None, model=None):
        asked.append((provider, model))
        return MockProvider()

    monkeypatch.setattr(run_module, "get_provider", fake_get_provider)
    run_module.build_engine("groq", "agent-model", judge_model="judge-model")
    assert asked == [("groq", "judge-model")]


def test_every_step_is_matched_to_a_verdict() -> None:
    result = run_scenario("attack_email_bn", provider="mock", shield=True)
    assert len(result.step_verdicts) == len(result.run.steps)
    assert all(v is not None for v in result.step_verdicts)


def test_protected_run_writes_audit_log() -> None:
    with AuditLog() as audit:
        result = run_scenario("attack_email_bn", provider="mock", shield=True, audit=audit)
        assert audit.stats()["total"] == len(result.history)
        assert audit.stats()["block"] == 1


def test_parse_action_handles_code_fences_and_plain_text() -> None:
    assert parse_action('```json\n{"action": "final", "answer": "hi"}\n```') == {
        "action": "final",
        "answer": "hi",
    }
    assert parse_action("I am just text") is None

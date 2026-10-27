"""Agent-level benchmark on the offline mock agent, using the demo's own texts as items."""

import pytest

from agentshield.core.models import DatasetSample
from benchmark.run_agent import (
    TASK_FILE, TASK_PAY_BILLS, TASK_SUMMARY, TASK_WEB, build_case, evaluate, outcome_table, run_case,
)
from demo_agent.scenarios import load_json

EMAILS = {e["id"]: e["body"] for e in load_json("emails.json")}
PAGES = {p["id"]: p["content"] for p in load_json("web_pages.json")}
FILES = load_json("files.json")


def attack(sample_id, text, language, attack_type, style="blunt", target_tool="send_money"):
    return DatasetSample(id=sample_id, text=text, language=language, label="attack",
                         attack_type=attack_type, target_tool=target_tool, notes=f"style={style}")


ATTACKS = [
    attack("bn-email", EMAILS["e11"], "bn", "indirect_email"),
    attack("bn-bill", EMAILS["e21"], "bn", "indirect_email", style="subtle"),
    attack("banglish-web", PAGES["w2"], "banglish", "indirect_web"),
    attack("bn-file", FILES["notes.txt"], "bn", "indirect_file"),
]
BENIGN = DatasetSample(id="bn-benign", text=EMAILS["e2"], language="bn", label="benign")


@pytest.mark.parametrize(
    "sample, task",
    [(ATTACKS[0], TASK_SUMMARY), (ATTACKS[1], TASK_PAY_BILLS), (ATTACKS[2], TASK_WEB),
     (ATTACKS[3], TASK_FILE), (BENIGN, TASK_PAY_BILLS)],
)
def test_items_are_placed_in_the_right_task(sample, task):
    _, scenario = build_case(sample)
    assert scenario["user_task"] == task


def test_out_of_scope_items_are_skipped():
    assert build_case(attack("d", "x", "en", "direct")) is None
    assert build_case(attack("nv", "x", "en", "indirect_file", target_tool="send_referral")) is None


@pytest.mark.parametrize("sample", ATTACKS, ids=lambda s: s.id)
def test_mock_attack_succeeds_without_and_fails_with_agentshield(sample):
    assert run_case(sample, "mock", shield=False)["stolen"] > 0
    assert run_case(sample, "mock", shield=True)["stolen"] == 0


def test_benign_item_keeps_the_rent_payment():
    assert run_case(BENIGN, "mock", shield=False)["landlord_paid"]
    assert run_case(BENIGN, "mock", shield=True)["landlord_paid"]


def test_outcomes_name_how_money_was_stopped():
    assert run_case(ATTACKS[0], "mock", shield=False)["outcome"] == "attacker paid"
    assert run_case(ATTACKS[0], "mock", shield=True)["outcome"] == "blocked"
    assert run_case(BENIGN, "mock", shield=True)["outcome"] == "paid"


def test_outcome_table_counts_only_protected_runs():
    _, rows = evaluate([ATTACKS[0], BENIGN], "mock", runs=1)
    table = outcome_table(rows)
    assert "| bn | attack | blocked 1 |" in table
    assert "| bn | benign | paid 1 |" in table


def test_evaluate_counts_per_language():
    tallies, rows = evaluate(ATTACKS + [BENIGN], "mock", runs=1)
    assert len(rows) == 10  # 5 items x 2 modes
    assert tallies[("all", False)].attacks.hits == 4
    assert tallies[("all", True)].attacks.hits == 0
    assert tallies[("bn", True)].benign.value == 1.0

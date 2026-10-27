"""Mixed inbox: real rent bill + an injection email. Shows the classifier-scope effect."""

from benchmark.run_mixed import LANDLORD, build_mixed
from demo_agent.run import run_world
from demo_agent.scenarios import load_json

INJECTION_EMAIL = next(e["body"] for e in load_json("emails.json") if e["id"] == "e11")


def rent_paid(order: str, classifier: bool) -> bool:
    world, scenario = build_mixed(INJECTION_EMAIL, order)
    result = run_world("mixed", world, scenario, provider="mock", shield=True, classifier=classifier)
    assert result.outcome.stolen == 0  # the attacker is never paid with AgentShield
    return any(t.to == LANDLORD for t in world.transactions)


def test_order_of_emails():
    world, _ = build_mixed("x", "attack_first")
    assert [e["id"] for e in world.emails] == ["e91", "e20"]
    world, _ = build_mixed("x", "rent_first")
    assert [e["id"] for e in world.emails] == ["e20", "e91"]


def test_classifier_scanning_all_context_holds_the_rent_when_attack_comes_first():
    assert rent_paid("attack_first", classifier=True) is False  # held for approval (current design)
    assert rent_paid("attack_first", classifier=False) is True
    assert rent_paid("rent_first", classifier=True) is True

"""Tests for the fake MockPay tools."""

from demo_agent.scenarios import build_world, load_scenarios


def make_world():
    return build_world(load_scenarios()["attack_email_bn"])


def test_get_balance() -> None:
    assert "25000 BDT" in make_world().get_balance()


def test_send_money_reduces_balance_and_records_transaction() -> None:
    world = make_world()
    result = world.send_money("01000000101", 500)
    assert "Sent 500 BDT" in result
    assert world.balance == 24500
    assert world.transactions[0].to == "01000000101"


def test_send_money_rejects_bad_input() -> None:
    world = make_world()
    assert world.send_money("12345", 100).startswith("Error")
    assert world.send_money("01000000101", -5).startswith("Error")
    assert world.send_money("01000000101", 999999).startswith("Error")
    assert world.transactions == []


def test_read_inbox_and_email() -> None:
    world = make_world()
    assert "e11 |" in world.read_inbox()
    assert "৫০০০ টাকা" in world.read_email("e11")
    assert world.read_email("nope").startswith("Error")


def test_search_web_and_read_file() -> None:
    world = build_world(load_scenarios()["attack_web_banglish"])
    assert "Cashback" in world.search_web("mockpay cashback offer")
    assert world.read_file("missing.txt").startswith("Error")


def test_every_tool_has_a_source_label() -> None:
    for spec in make_world().tool_specs().values():
        assert spec.source.startswith("tool:")

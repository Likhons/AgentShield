"""Network view (benchmark/network.py): simulated wallet + cross-user graph check."""

from __future__ import annotations

import json

import pytest

from benchmark import network


@pytest.fixture(scope="module")
def report() -> dict:
    return network.report()


def test_report_is_deterministic_and_json(report):
    again = network.report()
    assert json.dumps(report, sort_keys=True) == json.dumps(again, sort_keys=True)
    assert report["simulated"] is True


def test_world_has_only_fake_numbers():
    world = network.build_world()
    assert all(n.startswith("010") and len(n) == 11 for n in world.accounts)


def test_per_call_verdicts_come_from_the_policy():
    world = network.build_world()
    network.apply_policy(world)
    untrusted_scams = [a for a in world.attempts if a.scam and a.source in network.UNTRUSTED]
    assert untrusted_scams and all(a.per_call == "block" for a in untrusted_scams)
    assert all(a.per_call_rule == "tainted_transfer_to_stranger" for a in untrusted_scams)
    # a user paying a saved contact is never stopped by the policy (unless above the amount limit)
    small_known = [a for a in world.attempts if not a.scam and a.recipient in a.contacts and a.amount <= 10000]
    assert all(a.per_call == "allow" for a in small_known)


def test_network_never_increases_money_to_scammers(report):
    assert report["with_network"]["scam_moved"] <= report["per_call"]["scam_moved"]
    assert report["with_network"]["scam_stopped_network"] > 0
    assert report["per_call"]["scam_stopped_network"] == 0


def test_no_legit_account_is_flagged(report):
    assert report["evaluation"]["legit_flagged"] == 0
    assert report["with_network"]["legit_blocked_network"] == 0
    for a in report["accounts"]:
        if a["truth"] == "legit":
            assert a["tier"] in ("watch", "clear")


def test_linked_numbers_are_caught_faster(report):
    """In the phone-scam ring every later number is caught after fewer people than the first."""
    ring = next(r for r in report["rings"] if any(m["tier"] == "cashout" for m in r["members"]))
    caught = sorted((m for m in ring["members"] if m["flagged_after"] is not None), key=lambda m: m["flagged_at"])
    assert len(caught) >= 2
    assert all(m["flagged_after"] < caught[0]["flagged_after"] for m in caught[1:])


def test_flagged_payments_are_blocked_after_the_flag(report):
    for ring in report["rings"]:
        for m in ring["members"]:
            if not m["flagged_at"]:
                continue
            after = [p for p in m["attempts"] if p["t"] > m["flagged_at"]]
            assert all(p["outcome"] != "moved" for p in after)


def test_api_endpoint(tmp_path):
    from fastapi.testclient import TestClient

    from agentshield.audit.log import AuditLog
    from webapi.app import build_app

    client = TestClient(build_app(audit=AuditLog(tmp_path / "audit.db")))
    r = client.get("/api/network")
    assert r.status_code == 200
    body = r.json()
    assert body["simulated"] is True and body["rings"] and body["accounts"]

"""benchmark/report.py turns saved result files into dashboard tables."""

import json

from benchmark.report import agent_rows, detection_rows, latest


def test_latest_picks_newest_file(tmp_path):
    for stamp in ["20261027-100000", "20261027-120000"]:
        (tmp_path / f"agent_{stamp}.json").write_text(json.dumps({"stamp": stamp}), encoding="utf-8")
    name, data = latest("agent", tmp_path)
    assert name == "agent_20261027-120000"
    assert latest("detection", tmp_path) is None


def test_detection_rows():
    data = {"metrics": {"guard": {"bn": {"tp": 1, "fn": 3, "fp": 0, "tn": 10,
                                         "detection_rate": 0.25, "false_positive_rate": 0.0}}}}
    [row] = detection_rows(data)
    assert row["detector"] == "guard" and row["language"] == "bn"
    assert row["attacks flagged"].startswith("25% (1/4")
    assert row["benign flagged"].startswith("0% (0/10")


def test_agent_rows_with_and_without_language_in_rows():
    rows = [
        {"id": "a1", "shield": False, "stolen": 500, "landlord_paid": False},
        {"id": "a1", "shield": True, "stolen": 0, "landlord_paid": False},
        {"id": "b1", "language": "bn", "label": "benign", "shield": False, "stolen": 0, "landlord_paid": True},
        {"id": "b1", "language": "bn", "label": "benign", "shield": True, "stolen": 0, "landlord_paid": True},
    ]
    table = agent_rows({"rows": rows}, languages={"a1": ("bn", "attack")})
    bn = next(r for r in table if r["language"] == "bn")
    assert bn["attack success WITHOUT AgentShield"].startswith("100% (1/1")
    assert bn["attack success WITH AgentShield"].startswith("0% (0/1")
    assert bn["benign task done WITH"].startswith("100% (1/1")
    assert table[0]["language"] == "all"

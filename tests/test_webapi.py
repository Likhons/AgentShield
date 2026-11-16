"""Dashboard API (webapi/): same numbers and wording as the Streamlit dashboard, offline (mock + recordings)."""

import csv
import io

import pytest
from fastapi.testclient import TestClient

from agentshield.audit.log import AuditLog
from benchmark.dataset import load_dataset, summarize
from dashboard import ui
from webapi.app import build_app, rate_cell, summary_banner


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("GROQ_API_KEY", "")  # live mode must be off in tests
    return TestClient(build_app(audit=AuditLog()))


def run(client, name="attack_email_bn", mode="mock", approve=False):
    r = client.post(f"/api/scenarios/{name}/run", json={"mode": mode, "approve": approve})
    assert r.status_code == 200, r.text
    return r.json()


def test_rate_cell_parses_numbers_and_keeps_text():
    assert rate_cell("20% (4/20, 95% CI 8%-42%)") == {
        "text": "20% (4/20, 95% CI 8%-42%)", "hits": 4, "total": 20, "pct": 20, "ci": [8, 42]}
    assert rate_cell("n/a")["hits"] is None


@pytest.mark.parametrize("name,without,with_", [
    ("attack_email_bn", 5000, 0), ("attack_email_bn", 0, 0), ("benign_send", 0, 0), ("attack_x", 3000, 3000)])
def test_banner_wording_matches_streamlit(name, without, with_):
    api = summary_banner(name, without, with_)
    st = ui.summary_banner(name, without, with_)
    assert (api is None) == (st is None)
    if api:
        assert api["text"] == st[1]


def test_overview_counts_come_from_the_real_sources(client):
    body = client.get("/api/overview").json()
    attacks = {lang: c.get("attack", 0) for lang, c in summarize(load_dataset()).items()}
    assert body["attack_samples"]["total"] == sum(attacks.values())
    assert len(body["checks"]) == 4
    assert body["policy_rules"] == 3
    assert body["live_mode_available"] is False
    if body["real_llm"]:
        assert body["real_llm"]["with"]["total"] == body["real_llm"]["without"]["total"]


def test_scenarios_list_attacks_first_with_recording_flags(client):
    items = client.get("/api/scenarios").json()
    kinds = [s["kind"] for s in items]
    assert kinds == sorted(kinds)  # "attack" < "benign"
    by_name = {s["name"]: s for s in items}
    assert by_name["attack_bill_bn"]["has_recording"] is True
    assert by_name["attack_email_bn"]["user_task"]


def test_mock_run_without_vs_with_shield(client):
    body = run(client)
    assert body["without"]["stolen"] == 5000
    assert body["with"]["stolen"] == 0 and body["with"]["stopped"] == 1
    assert body["banner"]["tone"] == "saved"
    blocked = [s for s in body["with"]["steps"] if s["verdict"] and s["verdict"]["decision"] == "block"]
    assert len(blocked) == 1 and blocked[0]["tool"] == "send_money"
    assert blocked[0]["verdict"]["reason_bn"] and len(blocked[0]["verdict"]["checks"]) == 4
    assert all(s["verdict"] is None for s in body["without"]["steps"])


def test_recorded_run_replays_the_real_groq_numbers(client):
    body = run(client, "attack_bill_bn", mode="recorded")
    assert body["recorded_utc"]
    assert body["without"]["stolen"] == 4500 and body["with"]["stolen"] == 0


def test_live_mode_off_without_key_and_unknown_scenario(client):
    r = client.post("/api/scenarios/attack_email_bn/run", json={"mode": "groq"})
    assert r.status_code == 400 and "Live mode is off" in r.json()["detail"]
    assert client.post("/api/scenarios/nope/run", json={"mode": "mock"}).status_code == 404


def test_audit_filters_detail_and_csv(client):
    run(client)
    body = client.get("/api/audit", params={"limit": 50}).json()
    assert body["total"] >= 5 and body["counts"]["block"] >= 1
    blocks = client.get("/api/audit", params={"decision": "block"}).json()["records"]
    assert blocks and all(r["decision"] == "block" for r in blocks)

    one = client.get(f"/api/audit/{blocks[0]['id']}").json()
    assert one["tool_name"] == "send_money" and one["reason_bn"]
    assert client.get("/api/audit/does-not-exist").status_code == 404

    assert body["newest"] and body["counts"]["total"] == body["total"]
    only_blocks = client.get("/api/audit.csv", params={"decision": "block", "tool": "send_money"}).content
    assert len(list(csv.reader(io.StringIO(only_blocks.decode("utf-8-sig"))))) - 1 == len(blocks)

    raw = client.get("/api/audit.csv").content
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM keeps Bangla in Excel
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    assert rows[0][:6] == ["id", "timestamp_utc", "session_id", "request_id", "tool", "decision"]
    assert len(rows) - 1 == body["total"]


def test_benchmarks_sections_have_parsed_numbers(client):
    sections = client.get("/api/benchmarks").json()["sections"]
    kinds = [s["kind"] for s in sections]
    assert "agent" in kinds and "detection" in kinds
    agent = next(s for s in sections if s["kind"] == "agent")
    all_row = next(r for r in agent["rows"] if r["language"] == "all")
    assert all_row["label"] == "All"
    assert all_row["attack success WITH AgentShield"]["total"] is not None
    detection = next(s for s in sections if s["kind"] == "detection")
    assert "{" not in detection["dataset"]  # readable label, not a raw dict


def test_policies_and_datasets(client):
    pol = client.get("/api/policies").json()
    assert pol["file"] == "default.yaml" and len(pol["rules"]) == 3

    ds = client.get("/api/datasets").json()
    assert {l["label"] for l in ds["languages"]} == {"BN", "EN", "Banglish"}
    files = {f["file"]: f for f in ds["files"]}
    assert files["benign.jsonl"]["items"] == 135

    prev = client.get("/api/datasets/benign.jsonl", params={"limit": 2}).json()
    assert prev["total"] == 135 and len(prev["records"]) == 2
    assert client.get("/api/datasets/missing.jsonl").status_code == 404
    assert client.get("/api/datasets/bad name.jsonl").status_code == 400


def test_policy_yaml_and_validation(client):
    pol = client.get("/api/policies").json()
    assert set(pol["yaml"]) == {r["id"] for r in pol["rules"]}
    good = {"id": "x", "tools": ["send_money"], "when": {"argument_gt": {"argument": "amount", "value": 5000}},
            "decision": "ask_human", "risk": 0.7, "reason_en": "e", "reason_bn": "বা"}
    ok = client.post("/api/policies/validate", json=good).json()
    assert ok["valid"] and "argument_gt" in ok["yaml"] and "বা" in ok["yaml"]
    bad = client.post("/api/policies/validate", json={**good, "decision": "allow"}).json()
    assert not bad["valid"] and "decision" in bad["error"]


def test_docs_preview_breakdown_and_download(client):
    doc = client.get("/api/docs/results").json()
    assert doc["file"] == "docs/results.md" and doc["markdown"].strip()
    assert client.get("/api/docs/secrets").status_code == 422  # only the listed documents

    prev = client.get("/api/datasets/benign.jsonl").json()
    assert len(prev["records"]) == 15
    assert sum(r["benign"] for r in prev["by_language"]) == 135

    raw = client.get("/api/datasets/benign.jsonl/download")
    assert raw.status_code == 200 and len(raw.content.decode("utf-8").strip().splitlines()) == 135


def test_attack_texts_hidden_unless_enabled(client, monkeypatch):
    monkeypatch.delenv("SHOW_ATTACK_TEXTS", raising=False)
    files = {f["file"]: f for f in client.get("/api/datasets").json()["files"]}
    assert files["attacks.jsonl"]["texts_public"] is False and files["attacks.jsonl"]["items"] > 0
    assert files["benign.jsonl"]["texts_public"] is True

    prev = client.get("/api/datasets/attacks.jsonl").json()
    assert prev["texts_public"] is False and prev["note"]
    assert prev["records"] and all(r["text"] is None for r in prev["records"])
    assert sum(r["attack"] for r in prev["by_language"]) == prev["total"]  # counts stay
    assert client.get("/api/datasets/attacks.jsonl/download").status_code == 403

    monkeypatch.setenv("SHOW_ATTACK_TEXTS", "1")
    shown = client.get("/api/datasets/attacks.jsonl", params={"limit": 2}).json()
    assert shown["texts_public"] and all(r["text"] for r in shown["records"])
    assert client.get("/api/datasets/attacks.jsonl/download").status_code == 200


def _live_client(monkeypatch, key="test-key", model="test-model", per_hour=None):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("GROQ_API_KEY", key)
    monkeypatch.setenv("LLM_MODEL", model)  # set even when empty, so a local .env cannot fill it in
    if per_hour is not None:
        monkeypatch.setenv("LIVE_RUNS_PER_HOUR", str(per_hour))
    return TestClient(build_app(audit=AuditLog()))


def test_live_mode_needs_key_and_model(monkeypatch):
    no_model = _live_client(monkeypatch, model="")
    assert no_model.get("/api/overview").json()["live_mode_available"] is False
    assert no_model.post("/api/scenarios/attack_email_bn/run", json={"mode": "groq"}).status_code == 400
    assert _live_client(monkeypatch, per_hour=0).get("/api/overview").json()["live_mode_available"] is False
    assert _live_client(monkeypatch, per_hour=20).get("/api/overview").json()["live_mode_available"] is True


def test_live_runs_are_capped_per_hour(monkeypatch):
    """Protects the free Groq quota on a public server; no real Groq call is made here."""
    import webapi.app as webapi_app
    from agentshield.llm import LLMError

    real_run = webapi_app.run_scenario

    def fake_run(name, provider=None, **kwargs):
        if provider == "groq":
            raise LLMError("no network in tests")
        return real_run(name, provider=provider, **kwargs)

    monkeypatch.setattr(webapi_app, "run_scenario", fake_run)
    client = _live_client(monkeypatch, per_hour=2)
    codes = [client.post("/api/scenarios/benign_balance/run", json={"mode": "groq"}).status_code for _ in range(3)]
    assert codes == [502, 502, 429]
    assert "Recorded Run" in client.post("/api/scenarios/benign_balance/run", json={"mode": "groq"}).json()["detail"]
    assert client.post("/api/scenarios/benign_balance/run", json={"mode": "mock"}).status_code == 200  # offline unaffected


def test_gateway_endpoints_still_mounted(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "total" in client.get("/v1/stats").json()

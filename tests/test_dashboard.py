"""The dashboard renders and the live demo runs on the offline mock LLM."""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "dashboard" / "app.py")


@pytest.fixture(autouse=True)
def temporary_audit_db(tmp_path, monkeypatch):
    """Never write test decisions into the real audit log."""
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def test_dashboard_loads_without_errors() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    assert any("Hidden Instructions" in m.value for m in app.markdown)


def test_recorded_mode_without_recordings_explains_how_to_record(monkeypatch, tmp_path) -> None:
    import demo_agent.recording as recording

    monkeypatch.setattr(recording, "RECORDINGS_DIR", tmp_path)
    monkeypatch.setattr(recording.recording_path, "__defaults__", (tmp_path,))
    monkeypatch.setattr(recording.load_result, "__defaults__", (tmp_path,))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="agent_mode").set_value("recorded (groq)")
    app.button(key="run").click().run()
    assert not app.exception
    assert any("--record" in i.value for i in app.info)


def test_approval_checkbox_lets_the_large_transfer_through() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.selectbox(key="scenario").set_value("benign_send_large")
    app.radio(key="agent_mode").set_value("mock")
    app.checkbox(key="approve").check()
    app.button(key="run").click().run()
    assert not app.exception
    assert any("approved" in e.label and "not approved" not in e.label for e in app.expander)


def test_live_demo_side_by_side_on_mock() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="agent_mode").set_value("mock")
    app.button(key="run").click().run()
    assert not app.exception
    assert any("MONEY STOLEN" in e.value for e in app.error)  # left column
    assert any("AgentShield stopped" in s.value for s in app.success)  # right column


@pytest.mark.parametrize("page", ["Benchmarks", "Audit Log", "Policies", "Datasets"])
def test_every_page_renders(page) -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="nav_page").set_value(page).run()
    assert not app.exception




def test_summary_banner_is_honest() -> None:
    from dashboard.ui import summary_banner

    assert "saved ৳ 4,500" in summary_banner("attack_bill_bn", 4500, 0)[1]
    css, text = summary_banner("attack_email_bn", 0, 0)
    assert css == "summary-neutral" and "ignored this attack" in text and "Normal task" not in text
    assert "Normal task" in summary_banner("benign_inbox", 0, 0)[1]
    assert summary_banner("attack_bill_bn", 4500, 4500) is None
    # a payment held for the user's approval did not run: never "let it run"
    css, text = summary_banner("benign_send_large", 0, 0, held=15000)
    assert css == "summary-held" and "Held for your approval" in text and "৳ 15,000" in text and "let it run" not in text
    assert "saved ৳ 4,500" in summary_banner("attack_bill_bn", 4500, 0, held=15000)[1]  # money saved comes first


def test_audit_log_console_filters_pagination_drawer_and_csv(tmp_path, monkeypatch) -> None:
    from datetime import datetime, timedelta, timezone
    from agentshield.audit.log import AuditLog
    from agentshield.core.models import AuditRecord, CheckName, CheckResult, Decision
    from dashboard.app import build_audit_csv

    db_file = tmp_path / "audit.db"
    monkeypatch.setenv("AUDIT_DB_PATH", str(db_file))
    st.cache_resource.clear()

    base = datetime(2026, 11, 15, 18, 0, tzinfo=timezone.utc)
    with AuditLog(db_file) as log:
        for i in range(10):
            dec = Decision.BLOCK if i == 9 else (Decision.ASK_HUMAN if i == 8 else Decision.ALLOW)
            log.write(
                AuditRecord(
                    id=f"rec{i:02d}",
                    timestamp=base + timedelta(seconds=i),
                    session_id="s1",
                    request_id=f"req{i:02d}",
                    user_request="Please summarize my inbox.",
                    tool_name="send_money" if i >= 8 else "read_email",
                    arguments={"to": "01000000666", "amount": 5000 + i},
                    tainted=(i >= 8),
                    decision=dec,
                    risk_score=0.95 if i == 9 else (0.6 if i == 8 else 0.06),
                    reason_en="Blocked untrusted transfer." if i == 9 else "Allowed.",
                    reason_bn="আটকানো হয়েছে। অবিশ্বস্ত কনটেন্ট থেকে টাকা পাঠানোর নির্দেশ এসেছে।" if i == 9 else "অনুমতি দেওয়া হয়েছে।",
                    checks=[CheckResult(check=CheckName.INTENT, risk_score=0.1, skipped=(i % 2 == 0))],
                    total_latency_ms=10.0 + i,
                )
            )
        csv_text = build_audit_csv(log.recent(10)).decode("utf-8-sig")
        assert "আটকানো হয়েছে" in csv_text
        assert "01000000666" in csv_text

    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="nav_page").set_value("Audit Log").run()
    assert not app.exception

    joined_md = "\n".join(m.value for m in app.markdown)
    # KPIs, Bangla reason in details drawer, and pagination indicator
    assert "Checked Calls" in joined_md and "10" in joined_md
    assert "Showing 1–8 of 10" in joined_md
    assert "আটকানো হয়েছে। অবিশ্বস্ত কনটেন্ট থেকে টাকা পাঠানোর নির্দেশ এসেছে।" in joined_md
    # args are HTML-escaped in the drawer (the browser shows plain quotes)
    assert '"to": "01000000666"' in joined_md or "&quot;to&quot;: &quot;01000000666&quot;" in joined_md

    # Copy actions in drawer
    app.button(key="audit_copy_args").click().run()
    assert not app.exception
    assert any("01000000666" in c.value for c in app.code)

    app.button(key="audit_copy_id").click().run()
    assert not app.exception
    assert any("rec09" in c.value for c in app.code)

    # Pagination: Next page shows records 9–10 of 10
    app.button(key="audit_next_page").click().run()
    assert not app.exception
    assert any("Showing 9–10 of 10" in m.value for m in app.markdown)

    # Filter by Decision = block
    app.radio(key="audit_decision_filter").set_value("block").run()
    assert not app.exception
    assert any("Showing 1–1 of 1" in m.value for m in app.markdown)

    # Search + Clear filters
    app.text_input(key="audit_search").set_value("5009").run()
    assert not app.exception
    assert any("Showing 1–1 of 1" in m.value for m in app.markdown)
    app.button(key="audit_clear_filters").click().run()
    assert not app.exception
    assert any("Showing 1–8 of 10" in m.value for m in app.markdown)


def test_policies_page_renders_kpis_filters_and_search() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="nav_page").set_value("Policies").run()
    assert not app.exception

    md = "\n".join(m.value for m in app.markdown)
    assert "Total Policies" in md and "Block Policies" in md and "Ask Policies" in md
    assert "tainted_transfer_to_stranger" in md
    assert "unknown_recipient_not_from_user" in md
    assert "large_transfer" in md

    # Filter to Block policies only
    app.radio(key="policy_decision_filter").set_value("block").run()
    assert not app.exception
    md_block = "\n".join(m.value for m in app.markdown)
    assert "tainted_transfer_to_stranger" in md_block
    assert "large_transfer" not in md_block

    # Reset to all and search for "10000"
    app.radio(key="policy_decision_filter").set_value("all").run()
    app.text_input(key="policy_search").set_value("10000").run()
    assert not app.exception
    md_search = "\n".join(m.value for m in app.markdown)
    assert "large_transfer" in md_search
    assert "tainted_transfer_to_stranger" not in md_search


def test_datasets_page_renders_distribution_donut_and_file_filters() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="nav_page").set_value("Datasets").run()
    assert not app.exception

    md = "\n".join(m.value for m in app.markdown)
    assert "Language Distribution" in md
    assert "Total Samples" in md and "334" in md
    for fname in ("attacks.jsonl", "benign.jsonl", "benign_own.jsonl", "benign_payreq.jsonl", "external.jsonl"):
        assert fname in md
    assert "64 / 64" in md and "135 / 135" in md and "35 / 35" in md and "0 / 60" in md and "0 / 40" in md

    # Filter by source = external
    app.selectbox(key="dataset_source_filter").set_value("external").run()
    assert not app.exception
    md_ext = "\n".join(m.value for m in app.markdown)
    # check the file list only (the README expander mentions every file by name)
    assert "<span>external.jsonl</span>" in md_ext
    assert "<span>benign_own.jsonl</span>" not in md_ext

    # Reset source filter and search for "attacks"
    app.selectbox(key="dataset_source_filter").set_value("All Sources").run()
    app.text_input(key="dataset_search").set_value("attacks").run()
    assert not app.exception
    md_att = "\n".join(m.value for m in app.markdown)
    assert "<span>attacks.jsonl</span>" in md_att
    assert "<span>external.jsonl</span>" not in md_att


def _open_dataset_file(file_name: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.query_params["dfile"] = file_name
    app.query_params["daction"] = "open"
    app.run()
    app.radio(key="nav_page").set_value("Datasets").run()
    assert not app.exception
    return app


def test_attack_texts_stay_private_unless_enabled(monkeypatch) -> None:
    """docs/ethics_impact.md: attack texts are shared on request, so the public dashboard shows counts only."""
    monkeypatch.delenv("SHOW_ATTACK_TEXTS", raising=False)
    app = _open_dataset_file("attacks.jsonl")
    assert not app.get("download_button")  # the file's bytes never reach the page
    assert any("not published" in i.value for i in app.info)
    sample = app.dataframe[-1].value
    assert len(sample) == 15 and set(sample["text"]) == {"hidden"}
    assert set(sample["label"]) == {"attack"}  # metadata stays visible

    benign = _open_dataset_file("benign.jsonl")  # other files are unchanged
    assert benign.get("download_button")
    assert "hidden" not in set(benign.dataframe[-1].value["text"])

    monkeypatch.setenv("SHOW_ATTACK_TEXTS", "1")
    shown = _open_dataset_file("attacks.jsonl")
    assert shown.get("download_button")
    assert "hidden" not in set(shown.dataframe[-1].value["text"])


def test_benchmarks_page_renders_real_and_simulated_runs_with_outcomes() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="nav_page").set_value("Benchmarks").run()
    assert not app.exception

    md = "\n".join(m.value for m in app.markdown)
    assert "Agent level, real LLM (Groq): is the money safe?" in md
    assert "Agent level, simulated agent" in md
    assert "Attack Success" in md and "Benign Success" in md
    assert "How each case ended with AgentShield" in md
    assert "docs/results.md" in md

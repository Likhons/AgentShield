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

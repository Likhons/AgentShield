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
    assert app.title[0].value == "🛡️ AgentShield"


def test_live_demo_side_by_side_on_mock() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value("mock")
    app.button[0].click().run()
    assert not app.exception
    assert any("MONEY STOLEN" in e.value for e in app.error)  # left column
    assert any("AgentShield stopped" in s.value for s in app.success)  # right column

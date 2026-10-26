"""The dashboard renders and the live demo runs on the offline mock LLM."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "dashboard" / "app.py")


def test_dashboard_loads_without_errors() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "🛡️ AgentShield"


def test_live_demo_shows_stolen_money_on_mock() -> None:
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value("mock")
    app.button[0].click().run()
    assert not app.exception
    assert any("MONEY STOLEN" in e.value for e in app.error)

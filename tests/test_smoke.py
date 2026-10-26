"""Smoke test: proves pytest runs and the package can be imported."""

import agentshield


def test_package_imports() -> None:
    assert agentshield.__version__ == "0.0.1"

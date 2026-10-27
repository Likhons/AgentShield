"""Record a run, load it back, and get the same story."""

from demo_agent.recording import available, load_result, save_result
from demo_agent.run import run_scenario


def test_round_trip(tmp_path):
    original = run_scenario("attack_bill_bn", provider="mock", shield=True)
    save_result(original, "mock", folder=tmp_path)
    loaded, recorded_utc = load_result("attack_bill_bn", True, "mock", folder=tmp_path)

    assert recorded_utc
    assert loaded.run.task == original.run.task
    assert [s.tool for s in loaded.run.steps] == [s.tool for s in original.run.steps]
    assert loaded.end_balance == original.end_balance
    assert loaded.outcome.stolen == original.outcome.stolen
    assert [v.decision if v else None for v in loaded.step_verdicts] == \
           [v.decision if v else None for v in original.step_verdicts]
    assert len(loaded.history) == len(original.history)


def test_missing_and_available(tmp_path):
    assert load_result("nope", True, "mock", folder=tmp_path) is None
    for shield in (False, True):
        save_result(run_scenario("benign_send", provider="mock", shield=shield), "mock", folder=tmp_path)
    save_result(run_scenario("benign_balance", provider="mock", shield=True), "mock", folder=tmp_path)
    assert available("mock", folder=tmp_path) == {"benign_send"}  # needs both columns

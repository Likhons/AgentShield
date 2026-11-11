"""Phase 4 plumbing: the trained-model detector entry and test-split filtering.
No model files and no torch are needed here; the real model is evaluated manually."""

import json

import pytest

from benchmark.dataset import load_dataset
from benchmark.detectors import TrainedModel, build_detectors
from benchmark.run_detection import filter_split
from tests.test_benchmark import demo_rows, write_dataset


@pytest.fixture
def samples(tmp_path):
    write_dataset(tmp_path, demo_rows())
    return load_dataset(tmp_path)


def write_split(path, **splits):
    path.write_text(json.dumps(splits), encoding="utf-8")
    return path


def test_filter_split_keeps_only_the_named_ids(samples, tmp_path):
    split_file = write_split(tmp_path / "split_ids.json", train=["e1", "e2"], val=["e3"], test=["e10", "e11"])
    test_items = filter_split(samples, "test", split_file)
    assert sorted(s.id for s in test_items) == ["e10", "e11"]
    assert [s.id for s in filter_split(samples, "val", split_file)] == ["e3"]


def test_filter_split_fails_when_split_is_stale(samples, tmp_path):
    split_file = write_split(tmp_path / "split_ids.json", train=["e1"], val=["e2"], test=["e3", "gone-001"])
    with pytest.raises(ValueError, match="stale"):
        filter_split(samples, "test", split_file)


def test_filter_split_fails_without_file_or_unknown_split(samples, tmp_path):
    with pytest.raises(FileNotFoundError):
        filter_split(samples, "test", tmp_path / "missing.json")
    split_file = write_split(tmp_path / "split_ids.json", train=["e1"], test=["e2"])
    with pytest.raises(ValueError, match="split 'val'"):
        filter_split(samples, "val", split_file)


def test_model_detector_is_registered_and_lazy(tmp_path):
    (detector,) = build_detectors(["model"])
    assert detector.name == "agentshield-model"
    # Building it must not need torch or model files; scoring without a model fails clearly.
    missing = TrainedModel(model_dir=tmp_path / "no-model")
    with pytest.raises(FileNotFoundError, match="Kaggle"):
        missing.score("hello")


# ---- runtime adapter (agentshield/checks/model_detector.py) ------------------


def test_model_detector_predict_uses_worst_chunk_and_signals(monkeypatch):
    from agentshield.checks.model_detector import ModelDetector
    from agentshield.core.models import Language

    detector = ModelDetector(model_dir="nowhere")
    seen = []

    def fake_predict(texts):
        seen.extend(texts)
        return [0.1 if "attack" not in t else 0.9 for t in texts]

    monkeypatch.setattr(detector, "_load", lambda: fake_predict)
    calm = detector.predict("Apnar bidyut bill 1250 taka, 15 November er moddhe pay korun.")
    assert calm.score == pytest.approx(0.1) and calm.signals == [] and calm.language == Language.BANGLISH
    loud = detector.predict(("normal words " * 60) + "attack")
    assert loud.score == pytest.approx(0.9) and loud.signals == ["model_attack"]
    assert len(seen) > 2  # the long text was split into chunks


def test_make_detector_reads_the_env(monkeypatch):
    from agentshield.checks.classifier import HeuristicDetector
    from agentshield.checks.model_detector import ModelDetector
    from demo_agent.run import make_detector

    monkeypatch.delenv("AGENTSHIELD_DETECTOR", raising=False)
    assert isinstance(make_detector(), HeuristicDetector)
    monkeypatch.setenv("AGENTSHIELD_DETECTOR", "model")
    assert isinstance(make_detector(), ModelDetector)  # lazy: no torch needed yet
    with pytest.raises(ValueError):
        make_detector("gpt")

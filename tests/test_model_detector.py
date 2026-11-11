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

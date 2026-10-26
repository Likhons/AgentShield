"""Benchmark plumbing: dataset validation, metrics, detectors and the runner.
Uses the existing demo emails as a tiny dataset; no API calls."""

import json

import pytest

from benchmark.dataset import DatasetError, load_dataset, summarize
from benchmark.detectors import CachedDetector, PromptGuard, chunks
from benchmark.metrics import DetectionMetrics, wilson_interval
from benchmark.run_detection import evaluate, markdown_table
from demo_agent.scenarios import load_json

EMAILS = {e["id"]: e for e in load_json("emails.json")}


def write_dataset(folder, rows):
    with open(folder / "data.jsonl", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def demo_rows():
    rows = []
    for email_id in ["e1", "e2", "e3", "e10", "e11", "e12"]:
        e = EMAILS[email_id]
        attack = e["kind"] == "attack"
        rows.append({
            "id": email_id, "text": e["body"], "language": e["language"],
            "label": "attack" if attack else "benign",
            "attack_type": "indirect_email" if attack else None,
        })
    return rows


@pytest.fixture
def dataset(tmp_path):
    write_dataset(tmp_path, demo_rows())
    return load_dataset(tmp_path)


# ---- dataset ---------------------------------------------------------------


def test_load_and_summarize(dataset):
    assert len(dataset) == 6
    assert summarize(dataset)["bn"] == {"attack": 1, "benign": 1}


def test_bad_rows_are_all_reported(tmp_path):
    rows = demo_rows()
    rows[0]["label"] = "maybe"  # invalid label
    rows[1]["id"] = rows[2]["id"]  # duplicate id
    del rows[3]["attack_type"]  # attack without a type
    write_dataset(tmp_path, rows)
    with pytest.raises(DatasetError) as err:
        load_dataset(tmp_path)
    message = str(err.value)
    assert "data.jsonl:1" in message and "data.jsonl:4" in message and "duplicate id" in message


def test_real_dataset_folder_is_valid():
    load_dataset()  # whatever is in datasets/ right now must always load


# ---- metrics ---------------------------------------------------------------


def test_metrics_counts_and_rates():
    m = DetectionMetrics()
    for is_attack, flagged in [(True, True), (True, True), (True, False), (False, False), (False, True)]:
        m.add(is_attack, flagged)
    assert (m.tp, m.fn, m.fp, m.tn) == (2, 1, 1, 1)
    assert m.detection_rate.value == pytest.approx(2 / 3)
    assert m.false_positive_rate.value == pytest.approx(0.5)
    assert m.f1 == pytest.approx(2 / 3)


def test_wilson_interval_is_wide_for_small_samples():
    low, high = wilson_interval(9, 10)
    assert low < 0.6 and high > 0.98
    assert wilson_interval(0, 0) == (0.0, 0.0)


# ---- detectors and runner --------------------------------------------------


class KeywordDetector:
    """Fake detector: flags texts from the demo attack emails by id-specific words."""

    name = "fake"

    def score(self, text):
        return 0.9 if "01000000666" in text.translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")) else 0.1


def test_evaluate_per_language(dataset):
    by_language, rows = evaluate(KeywordDetector(), dataset)
    assert by_language["all"].detection_rate.value == 1.0
    assert by_language["all"].false_positive_rate.value == 0.0
    assert set(by_language) == {"all", "en", "bn", "banglish"}
    assert len(rows) == 6
    assert "| fake | bn |" in markdown_table({"fake": by_language})


class FakeGuardProvider:
    def __init__(self):
        self.calls = []

    def complete(self, messages):
        text = messages[0]["content"]
        self.calls.append(text)
        return "0.97" if "attack" in text else "0.0004"


def test_promptguard_scores_long_text_by_worst_chunk():
    provider = FakeGuardProvider()
    guard = PromptGuard("86m", provider=provider)
    long_text = ("normal words " * 60) + "attack"
    assert guard.score(long_text) == pytest.approx(0.97)
    assert len(provider.calls) > 1
    assert all(len(c) <= 400 for c in provider.calls)


def test_chunks_keep_all_words():
    text = "শব্দ " * 300
    assert " ".join(chunks(text)).split() == text.split()


def test_cache_avoids_repeat_calls(tmp_path):
    provider = FakeGuardProvider()
    first = CachedDetector(PromptGuard("86m", provider=provider), cache_dir=tmp_path)
    first.score("hello")
    first.score("hello")
    second = CachedDetector(PromptGuard("86m", provider=provider), cache_dir=tmp_path)
    assert second.score("hello") == pytest.approx(0.0004)
    assert len(provider.calls) == 1

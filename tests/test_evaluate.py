"""Testovi za scripts/evaluate.py — tačnost + Brier (d1.2 proper scoring)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from evaluate import minimal_score  # noqa: E402


def test_accuracy_plain():
    ref = [{"id": "a", "decision": "o1"}, {"id": "b", "decision": "o2"}]
    pred = [{"id": "a", "decision": "o1"}, {"id": "b", "decision": "o3"}]
    r = minimal_score(ref, pred)
    assert r == {"total": 2, "hit": 1, "accuracy": 0.5}


def test_accuracy_dict_reference():
    ref = [{"id": "a", "reference": {"decision": "o1"}}]
    pred = [{"id": "a", "decision": "o1"}]
    assert minimal_score(ref, pred)["accuracy"] == 1.0


def test_brier_rewards_calibration():
    ref = [{"id": "a", "decision": "o1"}, {"id": "b", "decision": "o1"}]
    confident = [{"id": "a", "decision": "o1", "probs": {"o1": 0.9, "o2": 0.1}},
                 {"id": "b", "decision": "o2", "probs": {"o1": 0.1, "o2": 0.9}}]
    humble = [{"id": "a", "decision": "o1", "probs": {"o1": 0.6, "o2": 0.4}},
              {"id": "b", "decision": "o2", "probs": {"o1": 0.4, "o2": 0.6}}]
    assert minimal_score(ref, confident)["brier"] > minimal_score(ref, humble)["brier"]
    assert minimal_score(ref, confident)["brier_n"] == 2


def test_no_probs_no_brier():
    r = minimal_score([{"id": "a", "decision": "o1"}], [{"id": "a", "decision": "o1"}])
    assert "brier" not in r

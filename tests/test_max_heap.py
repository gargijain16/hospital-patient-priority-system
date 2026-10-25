import random

import pytest

from algorithms.max_heap import MaxHeap, patient_heap
from utils.sample_data import generate_patients


def test_extract_order_and_heap_property_throughout():
    rng = random.Random(5)
    h = MaxHeap()
    scores = [rng.random() * 100 for _ in range(200)]
    for i, s in enumerate(scores):
        h.insert(f"I{i:03d}", s)
        assert h.is_valid()
    out = []
    while not h.is_empty():
        out.append(h.extract().score)
        assert h.is_valid()
    assert out == sorted(scores, reverse=True)   # sorted() only as oracle


def test_peek_does_not_remove_and_empty_errors():
    h = MaxHeap()
    with pytest.raises(IndexError):
        h.peek()
    with pytest.raises(IndexError):
        h.extract()
    h.insert("a", 1.0)
    h.insert("b", 2.0)
    assert h.peek().item_id == "b" and len(h) == 2


def test_duplicate_and_invalid_scores_rejected():
    h = MaxHeap()
    h.insert("a", 1.0)
    with pytest.raises(ValueError):
        h.insert("a", 2.0)
    with pytest.raises(ValueError):
        h.insert("b", float("nan"))
    with pytest.raises(KeyError):
        h.update_priority("zzz", 1.0)


def test_update_priority_up_and_down():
    h = MaxHeap()
    for i in range(20):
        h.insert(f"I{i:02d}", float(i))
    h.update_priority("I00", 100.0)
    assert h.peek().item_id == "I00" and h.is_valid()
    h.update_priority("I00", -5.0)
    assert h.peek().item_id == "I19" and h.is_valid()
    order = []
    while not h.is_empty():
        order.append(h.extract().item_id)
    assert order[-1] == "I00" and len(order) == 20


def test_patient_heap_uses_tie_breaks():
    ps = generate_patients(60, seed=9)
    h = patient_heap()
    for p in ps:
        h.insert(p.patient_id, 50.0, p)       # force identical scores
    first = h.extract().payload
    best = ps[0]
    for p in ps:
        if (p.severity_score, -p.arrival_time) > (best.severity_score, -best.arrival_time):
            best = p
    assert first.severity_score == best.severity_score and first.arrival_time == best.arrival_time


def test_record_history_and_tree_text():
    h = MaxHeap(record=True)
    for i in range(5):
        h.insert(f"N{i}", float(i))
    h.extract()
    assert [x["op"] for x in h.history] == ["insert"] * 5 + ["extract"]
    assert "N3" in h.to_tree_text() and h.history[-1]["size"] == 4

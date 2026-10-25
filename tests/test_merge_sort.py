import random

from algorithms.merge_sort import merge_sort, sort_patients
from algorithms.models import Patient
from utils.sample_data import generate_patients

lt = lambda a, b: a < b


def test_matches_reference_on_random_lists():
    rng = random.Random(1)
    for _ in range(50):
        data = [rng.randint(-50, 50) for _ in range(rng.randint(0, 80))]
        assert merge_sort(data, lt) == sorted(data)   # sorted() is only the test oracle


def test_empty_single_and_input_untouched():
    assert merge_sort([], lt) == []
    assert merge_sort([5], lt) == [5]
    data = [3, 1, 2]
    merge_sort(data, lt)
    assert data == [3, 1, 2]


def test_already_sorted_and_reversed():
    assert merge_sort(list(range(20)), lt) == list(range(20))
    assert merge_sort(list(range(20, 0, -1)), lt) == list(range(1, 21))


def test_stability():
    items = [(1, "a"), (0, "b"), (1, "c"), (0, "d"), (1, "e")]
    out = merge_sort(items, lambda x, y: x[0] < y[0])
    assert out == [(0, "b"), (0, "d"), (1, "a"), (1, "c"), (1, "e")]


def test_comparison_count_is_n_log_n_bounded():
    import math
    n = 256
    stats = {}
    merge_sort(list(range(n, 0, -1)), lt, stats)
    assert stats["comparisons"] <= n * math.ceil(math.log2(n))


def test_trace_last_merge_is_final_result():
    steps = []
    out = merge_sort([5, 2, 9, 1, 7], lt, steps=steps, label=str)
    merges = [s for s in steps if s["type"] == "merge"]
    assert merges[-1]["merged"] == [str(x) for x in out]
    assert merges[-1]["depth"] == 0
    assert len(merges) == 4   # n-1 merges


def test_patient_criteria_and_ties():
    ps = generate_patients(40, seed=3)
    by_sev = sort_patients(ps, "severity", now=200)
    assert all(by_sev[i].severity_score >= by_sev[i + 1].severity_score for i in range(39))
    by_arr = sort_patients(ps, "arrival")
    assert all(by_arr[i].arrival_time <= by_arr[i + 1].arrival_time for i in range(39))
    by_wait = sort_patients(ps, "waiting", now=500)
    assert all(by_wait[i].waiting_time(500) >= by_wait[i + 1].waiting_time(500) for i in range(39))
    by_tr = sort_patients(ps, "treatment")
    assert all(by_tr[i].treatment_time <= by_tr[i + 1].treatment_time for i in range(39))
    twins = [Patient("B", "x", 30, "Low", 1, 0, 10), Patient("A", "x", 30, "Low", 1, 0, 10)]
    assert [p.patient_id for p in sort_patients(twins, "priority")] == ["A", "B"]


def test_unknown_criterion():
    import pytest
    with pytest.raises(ValueError):
        sort_patients([], "nonsense")

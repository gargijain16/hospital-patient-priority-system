import pytest

from algorithms.metrics import (compute_metrics, count_severity_inversions, jain_index, mean, median,
                                severity_distribution)
from algorithms.models import Patient


def done(pid, sev, arr, start, tr):
    p = Patient(pid, "x", 30, sev, 3, arr, tr)
    p.start_time, p.finish_time = start, start + tr
    return p


def test_hand_computed_metrics():
    ds = [done("A", "Low", 0, 0, 10), done("B", "Critical", 2, 10, 20), done("C", "Low", 4, 30, 10)]
    m = compute_metrics(ds, start_clock=0, horizon=30, starvation_threshold=20)
    assert m["n_scheduled"] == 3
    assert m["avg_wait"] == pytest.approx((0 + 8 + 26) / 3)
    assert m["max_wait"] == 26
    assert m["avg_turnaround"] == pytest.approx((10 + 28 + 36) / 3)
    assert m["avg_treatment"] == pytest.approx(40 / 3) and m["total_treatment"] == 40
    assert m["completed_in_horizon"] == 2 and m["throughput_per_hour"] == pytest.approx(4.0)
    assert m["starvation_count"] == 1
    assert m["critical_avg_wait"] == 8 and m["high_avg_wait"] is None
    assert m["makespan"] == 40


def test_empty_metrics_do_not_crash():
    m = compute_metrics([])
    assert m["n_scheduled"] == 0 and m["avg_wait"] == 0.0 and m["max_wait"] == 0 and m["jain_index"] == 1.0


def test_jain_index_bounds():
    assert jain_index([5, 5, 5]) == pytest.approx(1.0)
    assert jain_index([0, 0]) == 1.0
    assert jain_index([10, 0, 0, 0]) == pytest.approx(0.25)


def test_inversions():
    a = done("A", "Low", 0, 0, 10)
    b = done("B", "Critical", 1, 10, 10)    # arrived at 1 <= a.start? 1 <= 0 is False -> no inversion
    assert count_severity_inversions([a, b]) == 0
    c = done("C", "Low", 0, 5, 10)
    d = done("D", "Critical", 1, 15, 10)    # arrived 1 <= 5 and more severe, served later
    assert count_severity_inversions([c, d]) == 1


def test_mean_median_distribution():
    assert mean([]) == 0.0 and mean([1, 2, 3]) == 2.0
    assert median([5, 1, 3]) == 3 and median([4, 1, 3, 2]) == 2.5
    with pytest.raises(ValueError):
        median([])
    ds = [done("A", "Low", 0, 0, 1), done("B", "Low", 0, 1, 1), done("C", "High", 0, 2, 1)]
    assert severity_distribution(ds) == {"Critical": 0, "High": 1, "Moderate": 0, "Low": 2}

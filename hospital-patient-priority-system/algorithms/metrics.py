"""Performance metrics for a completed schedule (all in simulated minutes).

Definitions (n = patients scheduled; w_i, t_i, T_i = waiting, treatment, turnaround):
  waiting      w_i = start_i - arrival_i
  turnaround   T_i = finish_i - arrival_i = w_i + t_i
  average wait = (sum w_i) / n            maximum wait = max w_i
  throughput   = patients finished by (start_clock + horizon) / (horizon / 60)   [patients/hour]
  starvation   = number of patients with w_i > threshold (default 60 min)
  Jain index   = (sum w_i)^2 / (n * sum w_i^2), 1 = identical waits, ~1/n = very unequal.
                 It measures *equality of waiting*, not clinical fairness.
  severity inversions = pairs (a, b) where a started first, b had already arrived and is
                 strictly more severe than a.  Counts how often urgency was overridden.

Limitations: results depend on the simulated arrival pattern, a single treatment bay,
non-preemptive service and exact treatment-time knowledge. These are execution-independent
quantities; they are NOT the algorithm run time measured on the benchmark page.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from .models import Patient, SEVERITY_ORDER
from .merge_sort import merge_sort

INVERSION_CAP = 3000   # O(n^2) metric; skipped above this size


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    total = 0.0
    for v in values:
        total += v
    return total / len(values)


def median(values: Sequence[float]) -> float:
    """Median using our own merge sort (no ``statistics`` / ``sorted``)."""
    if not values:
        raise ValueError("median of an empty sequence")
    ordered = merge_sort(list(values), lambda a, b: a < b)
    n = len(ordered)
    mid = n // 2
    return float(ordered[mid]) if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


def jain_index(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return 1.0
    s = sq = 0.0
    for v in values:
        s += v
        sq += v * v
    return 1.0 if sq == 0 else (s * s) / (n * sq)


def severity_distribution(patients: Sequence[Patient]) -> Dict[str, int]:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for p in patients:
        counts[p.severity] += 1
    return counts


def wait_by_severity(done: Sequence[Patient]) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    for sev in SEVERITY_ORDER:
        waits = [p.start_time - p.arrival_time for p in done if p.severity == sev]
        out[sev] = mean(waits) if waits else None
    return out


def count_severity_inversions(done: Sequence[Patient]) -> Optional[int]:
    """done must be in service order. Returns None when too large to evaluate."""
    n = len(done)
    if n > INVERSION_CAP:
        return None
    total = 0
    for i in range(n):
        a = done[i]
        for j in range(i + 1, n):
            b = done[j]
            if b.severity_score > a.severity_score and b.arrival_time <= a.start_time:
                total += 1
    return total


def compute_metrics(done: Sequence[Patient], start_clock: int = 0, horizon: int = 240,
                    starvation_threshold: int = 60) -> Dict[str, object]:
    """Metrics for patients that have start_time / finish_time set (in service order)."""
    n = len(done)
    waits = [p.start_time - p.arrival_time for p in done]
    turns = [p.finish_time - p.arrival_time for p in done]
    treats = [p.treatment_time for p in done]
    max_wait = 0
    for w in waits:
        if w > max_wait:
            max_wait = w
    horizon_end = start_clock + horizon
    finished_in_h = 0
    makespan_end = start_clock
    for p in done:
        if p.finish_time <= horizon_end:
            finished_in_h += 1
        if p.finish_time > makespan_end:
            makespan_end = p.finish_time
    starving = 0
    for w in waits:
        if w > starvation_threshold:
            starving += 1
    total_treat = 0
    for t in treats:
        total_treat += t
    by_sev = wait_by_severity(done)
    return {
        "n_scheduled": n,
        "avg_wait": mean(waits),
        "max_wait": max_wait,
        "avg_turnaround": mean(turns),
        "avg_treatment": mean(treats),
        "total_treatment": total_treat,
        "throughput_per_hour": finished_in_h / (horizon / 60.0) if horizon > 0 else 0.0,
        "completed_in_horizon": finished_in_h,
        "horizon_end": horizon_end,
        "starvation_count": starving,
        "starvation_threshold": starvation_threshold,
        "jain_index": jain_index(waits),
        "critical_avg_wait": by_sev["Critical"],
        "high_avg_wait": by_sev["High"],
        "severity_inversions": count_severity_inversions(done),
        "makespan": makespan_end - start_clock,
    }


def metrics_for_result(result, horizon: int = 240, starvation_threshold: int = 60) -> Dict[str, object]:
    return compute_metrics(result.patients(), result.start_clock, horizon, starvation_threshold)

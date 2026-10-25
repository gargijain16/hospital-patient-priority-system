"""Merge sort written from scratch, with an optional step-by-step trace.

``before(a, b)`` must return True when ``a`` should appear strictly before ``b``.
When neither element precedes the other, the element from the LEFT half is taken first,
so the sort is stable.

Complexity: best / average / worst O(n log n) comparisons, O(n) auxiliary space
(the merge buffers), O(log n) recursion depth.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .models import Patient, ScoreConfig
from .greedy_scheduler import priority_score


def _merge(left: List[Any], right: List[Any], before: Callable[[Any, Any], bool]) -> Tuple[List[Any], int]:
    """Merge two sorted lists. Returns (merged list, number of comparisons)."""
    out: List[Any] = []
    i = j = comps = 0
    nl, nr = len(left), len(right)
    while i < nl and j < nr:
        comps += 1
        if before(right[j], left[i]):   # right strictly first only when it must precede
            out.append(right[j]); j += 1
        else:                            # ties keep left first -> stable
            out.append(left[i]); i += 1
    while i < nl:
        out.append(left[i]); i += 1
    while j < nr:
        out.append(right[j]); j += 1
    return out, comps


def merge_sort(items: Sequence[Any], before: Callable[[Any, Any], bool],
               stats: Optional[Dict[str, int]] = None,
               steps: Optional[List[dict]] = None,
               label: Optional[Callable[[Any], str]] = None,
               _offset: int = 0, _depth: int = 0) -> List[Any]:
    """Return a new sorted list. ``stats`` collects comparisons/merges; ``steps`` collects a trace."""
    n = len(items)
    if n <= 1:
        return list(items)
    lab = label or str
    mid = n // 2
    if steps is not None:
        steps.append({"type": "split", "depth": _depth, "offset": _offset,
                      "left": [lab(x) for x in items[:mid]], "right": [lab(x) for x in items[mid:]]})
    left = merge_sort(items[:mid], before, stats, steps, label, _offset, _depth + 1)
    right = merge_sort(items[mid:], before, stats, steps, label, _offset + mid, _depth + 1)
    merged, comps = _merge(left, right, before)
    if stats is not None:
        stats["comparisons"] = stats.get("comparisons", 0) + comps
        stats["merges"] = stats.get("merges", 0) + 1
    if steps is not None:
        steps.append({"type": "merge", "depth": _depth, "offset": _offset,
                      "left": [lab(x) for x in left], "right": [lab(x) for x in right],
                      "merged": [lab(x) for x in merged], "comparisons": comps})
    return merged


# --------------------------------------------------------------------------- patient sorting
CRITERIA = {
    "priority": "Priority score (high to low)",
    "severity": "Emergency severity (high to low)",
    "waiting": "Waiting time (long to short)",
    "arrival": "Arrival order (earliest first)",
    "treatment": "Treatment time (short to long)",
}


def _before_factory(descending: bool, severity_tiebreak: bool) -> Callable[[Any, Any], bool]:
    """Comparator on (key, patient) pairs; ties fall back to severity (optional), arrival, ID."""
    def before(a, b):
        if a[0] != b[0]:
            return a[0] > b[0] if descending else a[0] < b[0]
        pa, pb = a[1], b[1]
        if severity_tiebreak and pa.severity_score != pb.severity_score:
            return pa.severity_score > pb.severity_score
        if pa.arrival_time != pb.arrival_time:
            return pa.arrival_time < pb.arrival_time
        return pa.patient_id < pb.patient_id
    return before


def sort_patients(patients: Sequence[Patient], criterion: str = "priority", now: int = 0,
                  cfg: Optional[ScoreConfig] = None, stats: Optional[Dict[str, int]] = None,
                  steps: Optional[List[dict]] = None) -> List[Patient]:
    """Sort patients with merge sort by one of ``CRITERIA``. Input is not modified."""
    cfg = cfg or ScoreConfig()
    if criterion == "priority":
        wrapped = [(priority_score(p, now, cfg), p) for p in patients]
        before = _before_factory(True, True)
    elif criterion == "severity":
        wrapped = [(p.severity_score, p) for p in patients]
        before = _before_factory(True, True)
    elif criterion == "waiting":
        wrapped = [(p.waiting_time(now), p) for p in patients]
        before = _before_factory(True, True)
    elif criterion == "arrival":
        wrapped = [(p.arrival_time, p) for p in patients]
        before = _before_factory(False, False)
    elif criterion == "treatment":
        wrapped = [(p.treatment_time, p) for p in patients]
        before = _before_factory(False, False)
    else:
        raise ValueError(f"Unknown sort criterion: {criterion!r}")

    def label(w):
        v = w[0]
        return f"{w[1].patient_id} [{v:.1f}]" if isinstance(v, float) else f"{w[1].patient_id} [{v}]"

    result = merge_sort(wrapped, before, stats, steps, label)
    return [w[1] for w in result]

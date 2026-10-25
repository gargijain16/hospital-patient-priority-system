"""Real execution-time benchmark (never hard-coded).

* datasets are generated BEFORE any timer starts;
* only the ordering function call is timed (time.perf_counter); no UI, CSV or chart work;
* every algorithm sees the identical dataset and the same scoring/tie-break rules;
* outputs are verified before timings are reported;
* the median of ``repeats`` runs is reported (our own merge-sort based median).
"""
from __future__ import annotations

import os
import platform
import time
from typing import Callable, Dict, List, Optional, Sequence

from algorithms.models import Patient, ScoreConfig
from algorithms.greedy_scheduler import priority_score
from algorithms.metrics import median
from algorithms.scheduling_strategies import (order_by_greedy_selection, order_by_heap, order_by_merge_sort,
                                              order_fcfs, order_stf)
from .sample_data import generate_patients

ALGORITHMS = [
    ("greedy_selection", "Greedy repeated selection", "O(n^2)", "O(n)"),
    ("merge_sort", "Merge sort by priority score", "O(n log n)", "O(n)"),
    ("heap", "Binary max-heap (n inserts + n extracts)", "O(n log n)", "O(n)"),
    ("fcfs", "FCFS (merge sort by arrival)", "O(n log n)", "O(n)"),
    ("stf", "Shortest treatment first (merge sort)", "O(n log n)", "O(n)"),
]
MAX_SIZE = 50_000


def environment_info() -> Dict[str, str]:
    info = time.get_clock_info("perf_counter")
    return {"python": platform.python_version(), "platform": platform.platform(),
            "cpu_count": str(os.cpu_count()), "timer_resolution_s": f"{info.resolution:.1e}",
            "timer_implementation": info.implementation}


def _ids(ps: Sequence[Patient]) -> List[str]:
    return [p.patient_id for p in ps]


def verify_outputs(patients: Sequence[Patient], now: int, cfg: ScoreConfig,
                   outputs: Dict[str, List[Patient]]) -> List[Dict]:
    """Untimed correctness checks that must pass before any timing is trusted."""
    checks: List[Dict] = []
    expected = set(_ids(patients))
    for key, out in outputs.items():
        ids = _ids(out)
        ok = len(ids) == len(patients) and set(ids) == expected
        checks.append({"algorithm": key, "check": "no patient lost or duplicated", "passed": ok})
    ref = _ids(outputs["merge_sort"])
    for key in ("heap", "greedy_selection"):
        if key in outputs:
            checks.append({"algorithm": key, "check": "same order as merge sort (identical score + tie-break)",
                           "passed": _ids(outputs[key]) == ref})
    fc = outputs["fcfs"]
    checks.append({"algorithm": "fcfs", "check": "arrival times non-decreasing",
                   "passed": all(fc[i].arrival_time <= fc[i + 1].arrival_time for i in range(len(fc) - 1))})
    st = outputs["stf"]
    checks.append({"algorithm": "stf", "check": "treatment times non-decreasing",
                   "passed": all(st[i].treatment_time <= st[i + 1].treatment_time for i in range(len(st) - 1))})
    ms = outputs["merge_sort"]
    scores = [priority_score(p, now, cfg) for p in ms]
    checks.append({"algorithm": "merge_sort", "check": "scores non-increasing",
                   "passed": all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))})
    return checks


def run_benchmark(sizes: Sequence[int], repeats: int = 5, seed: int = 42, quadratic_cap: int = 2000,
                  cfg: Optional[ScoreConfig] = None,
                  progress: Optional[Callable[[float, str], None]] = None) -> Dict:
    cfg = cfg or ScoreConfig()
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    for n in sizes:
        if n < 1 or n > MAX_SIZE:
            raise ValueError(f"Each size must be between 1 and {MAX_SIZE}.")
    rows: List[Dict] = []
    verification: List[Dict] = []
    total_steps = len(sizes) * len(ALGORITHMS)
    step = 0
    for n in sizes:
        patients = generate_patients(n, seed=seed)                 # BEFORE timing
        now = 0
        for p in patients:
            if p.arrival_time > now:
                now = p.arrival_time
        funcs: Dict[str, Callable[[], List[Patient]]] = {
            "greedy_selection": lambda: order_by_greedy_selection(patients, now, cfg),
            "merge_sort": lambda: order_by_merge_sort(patients, now, cfg),
            "heap": lambda: order_by_heap(patients, now, cfg),
            "fcfs": lambda: order_fcfs(patients),
            "stf": lambda: order_stf(patients),
        }
        skip_quadratic = n > quadratic_cap
        outputs = {k: f() for k, f in funcs.items() if not (k == "greedy_selection" and skip_quadratic)}
        checks = verify_outputs(patients, now, cfg, outputs)
        all_ok = all(c["passed"] for c in checks)
        for c in checks:
            verification.append({"n": n, **c})
        for key, label, tcx, scx in ALGORITHMS:
            step += 1
            if progress:
                progress(step / total_steps, f"n = {n}: {label}")
            base = {"n": n, "key": key, "algorithm": label, "time_complexity": tcx, "space_complexity": scx}
            if key == "greedy_selection" and skip_quadratic:
                rows.append({**base, "status": f"skipped (n > {quadratic_cap}, O(n^2) cap)", "median_ms": None,
                             "min_ms": None, "max_ms": None, "runs": 0})
                continue
            if not all_ok:
                rows.append({**base, "status": "verification failed", "median_ms": None, "min_ms": None,
                             "max_ms": None, "runs": 0})
                continue
            times: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                funcs[key]()
                t1 = time.perf_counter()
                times.append((t1 - t0) * 1000.0)
            lo = hi = times[0]
            for t in times:
                lo = t if t < lo else lo
                hi = t if t > hi else hi
            rows.append({**base, "status": "ok", "median_ms": median(times), "min_ms": lo, "max_ms": hi,
                         "runs": repeats})
    return {"rows": rows, "verification": verification, "environment": environment_info(),
            "params": {"sizes": list(sizes), "repeats": repeats, "seed": seed, "quadratic_cap": quadratic_cap}}

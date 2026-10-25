"""Scheduling strategies (single treatment bay, non-preemptive) and snapshot orderings.

Simulation model (``simulate``): one treatment bay. Whenever the bay is free, the strategy
picks one patient from those who have already arrived; treatment then runs to completion
(no pre-emption) and the clock moves to the finish time. If nobody is waiting the clock
jumps to the next arrival (idle time).

Strategies and implementation notes (r = patients currently waiting, n = all patients):

* greedy - re-scores every waiting patient at each decision (waiting time changes the
           score) with a linear scan.  One decision O(r); all n patients O(n^2) worst case.
* heap   - binary max-heap keyed by the score computed when the patient is admitted
           (keys go stale as waiting grows).  insert/extract O(log n); total O(n log n).
           With ``refresh_heap=True`` every key is refreshed before each extraction, which
           reproduces the greedy order exactly at O(r log r) per decision.
* fcfs   - arrival order (merge sort by arrival, then a pointer).  O(n log n) total.
* stf    - shortest treatment time among waiting patients, linear scan.  O(r) per decision.

Snapshot orderings (``order_by_*``) rank a fixed set of patients at one instant; they are
used by the live queue and by the benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .models import Patient, ScoreConfig, STATUS_COMPLETED
from .greedy_scheduler import greedy_select, explain_choice, priority_score, precedes
from .merge_sort import sort_patients
from .max_heap import patient_heap

STRATEGY_LABELS = {
    "greedy": "Greedy weighted priority",
    "heap": "Priority heap (binary max-heap)",
    "fcfs": "First-Come, First-Served",
    "stf": "Shortest treatment first",
}
STRATEGY_ORDER = ("greedy", "heap", "fcfs", "stf")


@dataclass
class ScheduleEntry:
    patient: Patient
    position: int
    start: int
    finish: int
    wait: int
    turnaround: int
    treatment: int
    score_at_start: float


@dataclass
class ScheduleResult:
    strategy: str
    entries: List[ScheduleEntry]
    trace: List[dict]
    start_clock: int
    end_clock: int
    idle_time: int

    def patients(self) -> List[Patient]:
        return [e.patient for e in self.entries]

    def entry_for(self, patient_id: str) -> Optional[ScheduleEntry]:
        for e in self.entries:
            if e.patient.patient_id == patient_id:
                return e
        return None


def _stf_before(a: Patient, b: Patient) -> bool:
    if a.treatment_time != b.treatment_time:
        return a.treatment_time < b.treatment_time
    if a.arrival_time != b.arrival_time:
        return a.arrival_time < b.arrival_time
    return a.patient_id < b.patient_id


def simulate(patients: Sequence[Patient], strategy: str, cfg: Optional[ScoreConfig] = None,
             start_clock: Optional[int] = None, refresh_heap: bool = False,
             record_trace: bool = True) -> ScheduleResult:
    """Replay ``patients`` from scratch under ``strategy``. Input objects are not modified."""
    if strategy not in STRATEGY_LABELS:
        raise ValueError(f"Unknown strategy: {strategy!r}")
    cfg = cfg or ScoreConfig()
    work = [p.copy() for p in patients]
    pending = sort_patients(work, "arrival")
    n = len(pending)
    if n == 0:
        return ScheduleResult(strategy, [], [], start_clock or 0, start_clock or 0, 0)

    clock = start_clock if start_clock is not None else pending[0].arrival_time
    first_clock = clock
    ptr = done = idle = head = 0
    ready: List[Patient] = []
    heap = patient_heap() if strategy == "heap" else None
    entries: List[ScheduleEntry] = []
    trace: List[dict] = []

    while done < n:
        while ptr < n and pending[ptr].arrival_time <= clock:       # admit arrivals
            p = pending[ptr]
            ptr += 1
            if heap is not None:
                heap.insert(p.patient_id, priority_score(p, clock, cfg), p)
            else:
                ready.append(p)
        if heap is not None:
            count = len(heap)
        elif strategy == "fcfs":
            count = len(ready) - head
        else:
            count = len(ready)
        if count == 0:                                               # idle until next arrival
            nxt = pending[ptr].arrival_time
            idle += nxt - clock
            clock = nxt
            continue

        comps = None
        heap_key = None
        if strategy == "greedy":
            choice = greedy_select(ready, clock, cfg)
            chosen, score, comps = choice.patient, choice.score, choice.components
            reason = explain_choice(choice)
            ready[choice.index] = ready[-1]
            ready.pop()
        elif strategy == "fcfs":
            chosen = ready[head]
            head += 1
            score = priority_score(chosen, clock, cfg)
            reason = f"Earliest arrival (minute {chosen.arrival_time}) among {count} waiting patient(s)."
        elif strategy == "stf":
            best_i = 0
            for i in range(1, len(ready)):
                if _stf_before(ready[i], ready[best_i]):
                    best_i = i
            chosen = ready[best_i]
            ready[best_i] = ready[-1]
            ready.pop()
            score = priority_score(chosen, clock, cfg)
            reason = f"Shortest treatment ({chosen.treatment_time} min) among {count} waiting patient(s)."
        else:  # heap
            if refresh_heap:
                for it in heap.items():
                    heap.update_priority(it.item_id, priority_score(it.payload, clock, cfg))
            item = heap.extract()
            chosen = item.payload
            heap_key = item.score
            score = priority_score(chosen, clock, cfg)
            reason = (f"Extracted heap root with key {item.score:.2f} from {count} item(s)"
                      f"{' after refreshing all keys' if refresh_heap else ' (key frozen at admission)'}.")

        chosen.start_time = clock
        chosen.finish_time = clock + chosen.treatment_time
        chosen.status = STATUS_COMPLETED
        chosen.queue_position = done + 1
        wait = clock - chosen.arrival_time
        entries.append(ScheduleEntry(chosen, done + 1, clock, chosen.finish_time, wait,
                                     chosen.finish_time - chosen.arrival_time,
                                     chosen.treatment_time, score))
        if record_trace:
            trace.append({"step": done + 1, "clock": clock, "patient_id": chosen.patient_id,
                          "severity": chosen.severity, "score": score, "heap_key": heap_key,
                          "candidates": count, "reason": reason, "components": comps})
        clock = chosen.finish_time
        done += 1

    return ScheduleResult(strategy, entries, trace, first_clock, clock, idle)


def run_all(patients: Sequence[Patient], cfg: Optional[ScoreConfig] = None,
            start_clock: Optional[int] = None, refresh_heap: bool = False,
            strategies: Sequence[str] = STRATEGY_ORDER) -> Dict[str, ScheduleResult]:
    """Run the identical dataset through several strategies."""
    return {s: simulate(patients, s, cfg, start_clock, refresh_heap) for s in strategies}


# ----------------------------------------------------------------------- snapshot orderings
def order_by_merge_sort(patients: Sequence[Patient], now: int, cfg: Optional[ScoreConfig] = None) -> List[Patient]:
    """Priority order via merge sort. O(n log n), O(n) auxiliary space."""
    return sort_patients(patients, "priority", now, cfg)


def order_by_heap(patients: Sequence[Patient], now: int, cfg: Optional[ScoreConfig] = None) -> List[Patient]:
    """Priority order via n heap inserts followed by n extractions. O(n log n)."""
    cfg = cfg or ScoreConfig()
    heap = patient_heap()
    for p in patients:
        heap.insert(p.patient_id, priority_score(p, now, cfg), p)
    out: List[Patient] = []
    while not heap.is_empty():
        out.append(heap.extract().payload)
    return out


def order_by_greedy_selection(patients: Sequence[Patient], now: int, cfg: Optional[ScoreConfig] = None) -> List[Patient]:
    """Repeated greedy selection of the best remaining patient (selection sort). O(n^2)."""
    cfg = cfg or ScoreConfig()
    remaining = [(priority_score(p, now, cfg), p) for p in patients]
    out: List[Patient] = []
    while remaining:
        best_i = 0
        for i in range(1, len(remaining)):
            if precedes(remaining[i][0], remaining[i][1], remaining[best_i][0], remaining[best_i][1]):
                best_i = i
        out.append(remaining[best_i][1])
        remaining[best_i] = remaining[-1]
        remaining.pop()
    return out


def order_fcfs(patients: Sequence[Patient]) -> List[Patient]:
    return sort_patients(patients, "arrival")


def order_stf(patients: Sequence[Patient]) -> List[Patient]:
    return sort_patients(patients, "treatment")


def snapshot_order(strategy: str, patients: Sequence[Patient], now: int,
                   cfg: Optional[ScoreConfig] = None, selection_cap: int = 300) -> List[Patient]:
    """Who would be served next, in order, if everyone listed were waiting at ``now``."""
    if strategy == "greedy":
        if len(patients) <= selection_cap:
            return order_by_greedy_selection(patients, now, cfg)
        return order_by_merge_sort(patients, now, cfg)   # identical order, faster for big queues
    if strategy == "heap":
        return order_by_heap(patients, now, cfg)
    if strategy == "fcfs":
        return order_fcfs(patients)
    if strategy == "stf":
        return order_stf(patients)
    raise ValueError(f"Unknown strategy: {strategy!r}")

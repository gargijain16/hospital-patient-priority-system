"""Scenario runner behind the Test Lab page. Every check is executed live (nothing is pre-recorded)."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from algorithms.models import Patient, ScoreConfig
from algorithms.greedy_scheduler import priority_score, score_components
from algorithms.max_heap import patient_heap
from algorithms.metrics import compute_metrics, severity_distribution
from algorithms.scheduling_strategies import (STRATEGY_ORDER, order_by_greedy_selection, order_by_heap,
                                              order_by_merge_sort, simulate)
from . import scenarios as sc
from .sample_data import generate_patients
from .validation import parse_csv, validate_record

QUAD_CAP = 1500
SIM_CAP = 400   # full simulations of the O(n^2) strategies only below this size


def _c(scenario: str, check: str, passed: bool, detail: str = "") -> Dict:
    return {"scenario": scenario, "check": check, "passed": bool(passed), "detail": detail}


def _ids(ps) -> List[str]:
    return [p.patient_id for p in ps]


def schedule_problems(result, patients) -> str:
    """Return '' if the schedule is sound, otherwise a description of the first problem."""
    ids = _ids(result.patients())
    if len(ids) != len(patients) or set(ids) != set(_ids(patients)):
        return "patients lost or duplicated"
    prev_finish = None
    for e in result.entries:
        if e.start < e.patient.arrival_time:
            return f"{e.patient.patient_id} started before arriving"
        if e.wait < 0 or e.finish - e.start != e.treatment:
            return f"{e.patient.patient_id} has an inconsistent time"
        if prev_finish is not None and e.start < prev_finish:
            return f"treatments overlap at {e.patient.patient_id}"
        prev_finish = e.finish
    return ""


def generic_checks(name: str, patients: List[Patient], now: int, cfg: Optional[ScoreConfig] = None) -> List[Dict]:
    cfg = cfg or ScoreConfig()
    out: List[Dict] = []
    n = len(patients)
    merged = order_by_merge_sort(patients, now, cfg)
    out.append(_c(name, "Merge sort keeps every patient exactly once",
                  len(merged) == n and set(_ids(merged)) == set(_ids(patients)), f"n = {n}"))
    scores = [priority_score(p, now, cfg) for p in merged]
    out.append(_c(name, "Scores are non-increasing in merge-sort order",
                  all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))))
    heap_order = order_by_heap(patients, now, cfg)
    out.append(_c(name, "Heap extraction order equals merge-sort order", _ids(heap_order) == _ids(merged)))
    if n <= QUAD_CAP:
        out.append(_c(name, "Greedy repeated selection equals merge-sort order",
                      _ids(order_by_greedy_selection(patients, now, cfg)) == _ids(merged)))
    else:
        out.append(_c(name, "Greedy repeated selection (skipped: O(n^2) cap)", True, f"n = {n} > {QUAD_CAP}"))
    h = patient_heap()
    for p in patients:
        h.insert(p.patient_id, priority_score(p, now, cfg), p)
    ok = h.is_valid()
    if n <= 300:
        while ok and not h.is_empty():
            h.extract()
            ok = h.is_valid()
    out.append(_c(name, "Heap property holds after inserts" + (" and every extraction" if n <= 300 else ""), ok))
    for s in STRATEGY_ORDER:
        if n > SIM_CAP and s in ("greedy", "stf"):
            out.append(_c(name, f"{s}: simulation skipped (O(n^2) on large queue)", True, f"n = {n} > {SIM_CAP}"))
            continue
        res = simulate(patients, s, cfg)
        problem = schedule_problems(res, patients)
        out.append(_c(name, f"{s}: valid schedule (no loss, no overlap, start >= arrival)", problem == "", problem))
    if n <= SIM_CAP:
        g = simulate(patients, "greedy", cfg)
        r = simulate(patients, "heap", cfg, refresh_heap=True)
        out.append(_c(name, "Heap with refreshed keys reproduces the greedy schedule", _ids(g.patients()) == _ids(r.patients())))
    return out


def _position(result, pid: str) -> int:
    e = result.entry_for(pid)
    return e.position if e else -1


# ------------------------------------------------------------------------- scenario checks
def _normal_mixed() -> List[Dict]:
    d = sc.mixed_queue_10()
    return generic_checks("Mixed queue of 10", d["patients"], d["now"])


def _normal_distinct() -> List[Dict]:
    d = sc.distinct_scores()
    name = "Distinct priority scores"
    order = _ids(order_by_merge_sort(d["patients"], d["now"]))
    return generic_checks(name, d["patients"], d["now"]) + [_c(name, "Order is D1, D2, D3, D4, D5", order == ["D1", "D2", "D3", "D4", "D5"], str(order))]


def _normal_equal_sev() -> List[Dict]:
    d = sc.equal_severity_different_waits()
    name = "Equal severity, different waits"
    order = _ids(order_by_merge_sort(d["patients"], d["now"]))
    return generic_checks(name, d["patients"], d["now"]) + [_c(name, "Longest waiter first (E0, E1, E2, E3)", order == ["E0", "E1", "E2", "E3"], str(order))]


def _boundary_empty() -> List[Dict]:
    name = "Empty queue"
    res = [simulate([], s) for s in STRATEGY_ORDER]
    m = compute_metrics([], 0, 240, 60)
    return [_c(name, "All strategies return an empty schedule", all(len(r.entries) == 0 for r in res)),
            _c(name, "Snapshot orderings return empty lists", order_by_merge_sort([], 0) == [] and order_by_heap([], 0) == []),
            _c(name, "Metrics do not divide by zero", m["n_scheduled"] == 0 and m["avg_wait"] == 0.0),
            _c(name, "Extracting from an empty heap raises IndexError", _raises(lambda: patient_heap().extract(), IndexError))]


def _raises(fn: Callable, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


def _boundary_single() -> List[Dict]:
    p = [sc._p("ONLY", 40, "High", 4, 0, 25)]
    return generic_checks("Single patient", p, 0) + [
        _c("Single patient", "Waits 0 minutes under every strategy",
           all(simulate(p, s).entries[0].wait == 0 for s in STRATEGY_ORDER))]


def _boundary_equal() -> List[Dict]:
    d = sc.all_equal_scores()
    name = "All scores equal"
    order = _ids(order_by_merge_sort(d["patients"], d["now"]))
    again = _ids(order_by_merge_sort(list(reversed(d["patients"])), d["now"]))
    return generic_checks(name, d["patients"], d["now"]) + [
        _c(name, "Ties resolved by patient ID (Q00..Q11)", order == [f"Q{i:02d}" for i in range(12)]),
        _c(name, "Order independent of input order (deterministic)", order == again)]


def _boundary_ages_priorities() -> List[Dict]:
    name = "Min/max age and priority"
    base = {"patient_id": "X1", "age": 0, "severity": "Low", "medical_priority": 1, "arrival_time": 0, "treatment_time": 10}
    checks = []
    for field, good, bad in (("age", (0, 120), (-1, 121)), ("medical_priority", (1, 5), (0, 6))):
        for v in good:
            p, e = validate_record({**base, field: v})
            checks.append(_c(name, f"{field} = {v} accepted", p is not None, "; ".join(e)))
        for v in bad:
            p, e = validate_record({**base, field: v})
            checks.append(_c(name, f"{field} = {v} rejected", p is None, "; ".join(e)))
    lo = sc._p("MIN", 0, "Low", 1, 0, 10)
    hi = sc._p("MAX", 120, "Critical", 5, 0, 10)
    checks.append(_c(name, "Scores stay within 0-100 at the extremes",
                     0 <= priority_score(lo, 0) <= 100 and 0 <= priority_score(hi, 500) <= 100))
    return checks


def _boundary_zero_wait() -> List[Dict]:
    d = sc.zero_wait()
    p = d["patients"][0]
    comp = score_components(p, d["now"])
    return [_c("Zero waiting time", "Waiting time is 0 and waiting points are 0", p.waiting_time(d["now"]) == 0 and comp["waiting_pts"] == 0),
            _c("Zero waiting time", "Waiting time never goes negative before arrival", p.waiting_time(0) == 0)]


def _boundary_bad_treatment() -> List[Dict]:
    name = "Invalid treatment duration"
    base = {"patient_id": "T1", "age": 30, "severity": "Low", "medical_priority": 1, "arrival_time": 0}
    out = []
    for v in (0, -5, "abc", "", 1.5):
        p, e = validate_record({**base, "treatment_time": v})
        out.append(_c(name, f"treatment_time = {v!r} rejected", p is None, "; ".join(e)))
    p, e = validate_record({**base, "treatment_time": 1})
    out.append(_c(name, "treatment_time = 1 accepted", p is not None))
    return out


def _boundary_csv_missing() -> List[Dict]:
    name = "Missing CSV fields"
    pats, errs = parse_csv("patient_id,age,severity,medical_priority,arrival_time\nA1,30,Low,1,0\n")
    pats2, errs2 = parse_csv("age,severity,medical_priority,arrival_time,treatment_time\n30,Low,,0,10\n")
    return [_c(name, "Missing column treatment_time is reported", pats == [] and any("treatment_time" in e for e in errs), "; ".join(errs)),
            _c(name, "Blank medical_priority is reported with its row number", pats2 == [] and any("Row 2" in e for e in errs2), "; ".join(errs2))]


def _boundary_dup_ids() -> List[Dict]:
    name = "Duplicate patient IDs"
    text = "patient_id,age,severity,medical_priority,arrival_time,treatment_time\nA1,30,Low,1,0,10\nA1,31,Low,1,1,10\n"
    pats, errs = parse_csv(text)
    p, e = validate_record({"patient_id": "A1", "age": 3, "severity": "Low", "medical_priority": 1, "arrival_time": 0, "treatment_time": 5}, existing_ids={"A1"})
    return [_c(name, "Duplicate inside a CSV is reported", any("Duplicate" in x for x in errs), "; ".join(errs)),
            _c(name, "Duplicate against existing patients is rejected", p is None and any("Duplicate" in x for x in e))]


def _large(n: int) -> Callable[[], List[Dict]]:
    def run() -> List[Dict]:
        ps = generate_patients(n, seed=11)
        now = 0
        for p in ps:
            now = p.arrival_time if p.arrival_time > now else now
        return generic_checks(f"{n:,} patients", ps, now) + [
            _c(f"{n:,} patients", "Severity distribution sums to n", sum(severity_distribution(ps).values()) == n)]
    return run


def _adv_critical_last() -> List[Dict]:
    d = sc.critical_arrives_last()
    name = "Critical patient arrives last"
    greedy, fcfs = simulate(d["patients"], "greedy"), simulate(d["patients"], "fcfs")
    return generic_checks(name, d["patients"], d["now"]) + [
        _c(name, "FCFS serves the Critical patient last", _position(fcfs, "CRIT") == len(d["patients"])),
        _c(name, "Greedy serves the Critical patient earlier than FCFS", _position(greedy, "CRIT") < _position(fcfs, "CRIT"),
           f"greedy position {_position(greedy, 'CRIT')}, FCFS position {_position(fcfs, 'CRIT')}")]


def _adv_identical() -> List[Dict]:
    return _boundary_equal()


def _adv_stf_long() -> List[Dict]:
    d = sc.long_treatment_stf()
    name = "Long patient bypassed under STF"
    stf, fcfs = simulate(d["patients"], "stf"), simulate(d["patients"], "fcfs")
    return generic_checks(name, d["patients"], d["now"]) + [
        _c(name, "LONG is served last under STF", _position(stf, "LONG") == len(d["patients"])),
        _c(name, "LONG waits longer under STF than under FCFS", stf.entry_for("LONG").wait > fcfs.entry_for("LONG").wait,
           f"STF wait {stf.entry_for('LONG').wait} min, FCFS wait {fcfs.entry_for('LONG').wait} min")]


def _adv_long_wait() -> List[Dict]:
    d = sc.very_long_wait()
    name = "Very long waiting time"
    old, new = d["patients"]
    cap = ScoreConfig().wait_cap
    return generic_checks(name, d["patients"], d["now"]) + [
        _c(name, "Waiting contribution is capped at 100 normalised points", score_components(old, d["now"])["waiting_norm"] == 100.0),
        _c(name, "Score with 5000 min equals score at the cap", priority_score(old, d["now"]) == priority_score(old, old.arrival_time + cap)),
        _c(name, "Longer-waiting patient is served first", _ids(order_by_merge_sort(d["patients"], d["now"]))[0] == "OLD")]


def _adv_weights() -> List[Dict]:
    d = sc.weights_change_order()
    name = "Weight change alters order"
    orders = {k: tuple(_ids(order_by_merge_sort(d["patients"], d["now"], c))) for k, c in sc.WEIGHT_SETS.items()}
    return [_c(name, "Three weight sets give at least two distinct orderings", len(set(orders.values())) >= 2,
               " | ".join(f"{k}: {','.join(v)}" for k, v in orders.items())),
            _c(name, "Each ordering keeps every patient exactly once", all(len(set(v)) == 6 for v in orders.values()))]


SCENARIOS = [
    ("normal_mixed", "A. Normal", "Mixed queue of 10 patients", _normal_mixed),
    ("normal_distinct", "A. Normal", "Patients with distinct priority scores", _normal_distinct),
    ("normal_equal_sev", "A. Normal", "Equal severity, different waiting times", _normal_equal_sev),
    ("b_empty", "B. Boundary", "Empty queue", _boundary_empty),
    ("b_single", "B. Boundary", "Single patient", _boundary_single),
    ("b_equal", "B. Boundary", "All patients with equal scores", _boundary_equal),
    ("b_ranges", "B. Boundary", "Minimum / maximum age and medical priority", _boundary_ages_priorities),
    ("b_zero_wait", "B. Boundary", "Zero waiting time", _boundary_zero_wait),
    ("b_bad_treat", "B. Boundary", "Invalid or negative treatment duration", _boundary_bad_treatment),
    ("b_csv_missing", "B. Boundary", "Missing CSV fields", _boundary_csv_missing),
    ("b_dup", "B. Boundary", "Duplicate patient IDs", _boundary_dup_ids),
    ("c_1000", "C. Large", "1,000 patients", _large(1000)),
    ("c_5000", "C. Large", "5,000 patients", _large(5000)),
    ("c_10000", "C. Large", "10,000 patients", _large(10000)),
    ("d_crit_last", "D. Adversarial", "A critical patient arriving last", _adv_critical_last),
    ("d_identical", "D. Adversarial", "Many patients with identical priorities", _adv_identical),
    ("d_stf_long", "D. Adversarial", "Long-treatment patient bypassed under STF", _adv_stf_long),
    ("d_long_wait", "D. Adversarial", "A patient with a very long waiting time", _adv_long_wait),
    ("d_weights", "D. Adversarial", "Changing the weights changes the ordering", _adv_weights),
]


def groups() -> List[str]:
    seen: List[str] = []
    for _, g, _, _ in SCENARIOS:
        if g not in seen:
            seen.append(g)
    return seen


def run_scenarios(group: Optional[str] = None) -> List[Dict]:
    out: List[Dict] = []
    for sid, g, title, fn in SCENARIOS:
        if group is None or g == group:
            try:
                for row in fn():
                    out.append({"group": g, **row, "scenario": title})
            except Exception as exc:  # a crash is itself a failed check
                out.append({"group": g, "scenario": title, "check": "scenario ran without exception",
                            "passed": False, "detail": f"{type(exc).__name__}: {exc}"})
    return out


def run_custom(n: int, seed: int, critical_share: float) -> List[Dict]:
    ps = generate_patients(n, seed=seed, critical_share=critical_share)
    now = 0
    for p in ps:
        now = p.arrival_time if p.arrival_time > now else now
    rows = generic_checks(f"Custom: n={n}, seed={seed}", ps, now)
    again = generate_patients(n, seed=seed, critical_share=critical_share)
    rows.append(_c(rows[0]["scenario"], "Same seed reproduces the identical dataset", ps == again))
    return rows

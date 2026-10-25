import pytest

from algorithms.greedy_scheduler import (age_score, greedy_select, precedes, priority_score, score_components,
                                         waiting_norm)
from algorithms.models import Patient, ScoreConfig
from algorithms.scheduling_strategies import (STRATEGY_ORDER, order_by_greedy_selection, order_by_heap,
                                              order_by_merge_sort, run_all, simulate, snapshot_order)
from utils.sample_data import demo_patients, generate_patients
from utils.testlab import schedule_problems


def mk(pid, sev="Moderate", med=3, arr=0, tr=20, age=30):
    return Patient(pid, "x", age, sev, med, arr, tr)


def test_score_formula_by_hand():
    p = mk("A", "Critical", 5, 0, 20, age=30)   # severity 100, medical 100, wait 60/120=50, age 25
    c = score_components(p, 60)
    assert c["severity_pts"] == pytest.approx(40.0)
    assert c["medical_pts"] == pytest.approx(25.0)
    assert c["waiting_pts"] == pytest.approx(10.0)
    assert c["age_pts"] == pytest.approx(3.75)
    assert c["total"] == pytest.approx(78.75) and priority_score(p, 60) == c["total"]


def test_weights_cap_and_age_config():
    p = mk("A", "Low", 1)
    assert waiting_norm(10_000, ScoreConfig()) == 100.0
    assert waiting_norm(-4, ScoreConfig()) == 0.0
    assert priority_score(p, 120) == priority_score(p, 9999)
    assert age_score(0, ScoreConfig()) == 100.0 and age_score(120, ScoreConfig()) == 90.0
    heavy = ScoreConfig(w_severity=100, w_medical=0, w_waiting=0, w_age=0)
    assert priority_score(mk("B", "Critical", 1), 0, heavy) == 100.0
    with pytest.raises(ValueError):
        ScoreConfig(0, 0, 0, 0).weights()
    assert ScoreConfig(wait_cap=0).validate()


def test_tie_break_chain():
    a, b = mk("A", "High", arr=5), mk("B", "Low", arr=0)
    assert precedes(50, a, 50, b)            # higher severity first
    c, d = mk("C", arr=1), mk("D", arr=2)
    assert precedes(50, c, 50, d)            # earlier arrival
    e, f = mk("E"), mk("F")
    assert precedes(50, e, 50, f) and not precedes(50, f, 50, e)   # patient id


def test_greedy_select_and_empty():
    assert greedy_select([], 0) is None
    ps = [mk("L", "Low", 1), mk("C", "Critical", 5), mk("M")]
    ch = greedy_select(ps, 10)
    assert ch.patient.patient_id == "C" and ch.index == 1 and ch.n_candidates == 3


def test_fcfs_preserves_arrival_order():
    ps = generate_patients(60, seed=2)
    res = simulate(ps, "fcfs")
    arr = [e.patient.arrival_time for e in res.entries]
    assert all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))


def test_stf_picks_shortest_available():
    ps = [mk("A", arr=0, tr=30), mk("B", arr=1, tr=50), mk("C", arr=2, tr=5), mk("D", arr=3, tr=15)]
    assert [e.patient.patient_id for e in simulate(ps, "stf").entries] == ["A", "C", "D", "B"]


def test_greedy_takes_critical_when_free():
    ps = [mk("A", "Low", 1, 0, 20), mk("B", "Low", 1, 1, 20), mk("CR", "Critical", 5, 2, 20)]
    assert [e.patient.patient_id for e in simulate(ps, "greedy").entries] == ["A", "CR", "B"]


def test_all_strategies_valid_no_loss_no_duplicates():
    for seed in range(5):
        ps = generate_patients(80, seed=seed, mean_gap=6)
        for s, res in run_all(ps).items():
            assert schedule_problems(res, ps) == "", (s, seed)


def test_idle_time_when_gaps():
    ps = [mk("A", arr=0, tr=10), mk("B", arr=100, tr=10)]
    res = simulate(ps, "greedy")
    assert res.entries[1].start == 100 and res.idle_time == 90 and res.entries[1].wait == 0


def test_heap_with_refresh_equals_greedy():
    for seed in range(6):
        ps = generate_patients(70, seed=seed, mean_gap=5)
        g = [e.patient.patient_id for e in simulate(ps, "greedy").entries]
        h = [e.patient.patient_id for e in simulate(ps, "heap", refresh_heap=True).entries]
        assert g == h


def test_snapshot_orderings_agree():
    ps = generate_patients(150, seed=4)
    a = [p.patient_id for p in order_by_merge_sort(ps, 500)]
    assert a == [p.patient_id for p in order_by_heap(ps, 500)]
    assert a == [p.patient_id for p in order_by_greedy_selection(ps, 500)]
    assert a == [p.patient_id for p in snapshot_order("greedy", ps, 500)]


def test_inputs_not_mutated_and_empty_and_unknown():
    ps = demo_patients()
    simulate(ps, "greedy")
    assert all(p.start_time is None and p.status == "Waiting" for p in ps)
    for s in STRATEGY_ORDER:
        assert simulate([], s).entries == []
    with pytest.raises(ValueError):
        simulate(ps, "bogus")


def test_seeded_generation_reproducible():
    assert generate_patients(50, seed=8) == generate_patients(50, seed=8)
    assert generate_patients(50, seed=8) != generate_patients(50, seed=9)


def test_waiting_time_grows_with_clock_and_is_not_treatment():
    p = mk("A", arr=10, tr=45)
    assert p.waiting_time(10) == 0 and p.waiting_time(40) == 30 and p.waiting_time(70) == 60
    assert p.waiting_time(70) != p.treatment_time

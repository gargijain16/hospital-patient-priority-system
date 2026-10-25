from __future__ import annotations

import streamlit as st

from algorithms.metrics import metrics_for_result
from algorithms.greedy_scheduler import priority_score
from algorithms.merge_sort import sort_patients
from algorithms.scheduling_strategies import STRATEGY_LABELS, STRATEGY_ORDER, run_all
from algorithms.models import ScoreConfig
from utils import charts, scenarios as sc
from . import state
from .components import callout, disclaimer, empty_state, plot, section_header, table
from .content import ASSUMPTIONS, COMPLEXITY_BASIC, COMPLEXITY_STRATEGIES

REPLAY_CAP = 1500


def _metric_rows(metrics):
    rows = []
    for s in STRATEGY_ORDER:
        m = metrics[s]
        rows.append({"Strategy": STRATEGY_LABELS[s], "Avg wait (min)": round(m["avg_wait"], 2), "Max wait (min)": m["max_wait"],
                     "Avg turnaround (min)": round(m["avg_turnaround"], 2), "Avg treatment (min)": round(m["avg_treatment"], 2),
                     "Patients": m["n_scheduled"], "Total treatment (min)": m["total_treatment"],
                     "Throughput (/h)": round(m["throughput_per_hour"], 2),
                     "Waits > threshold": m["starvation_count"], "Jain index": round(m["jain_index"], 3),
                     "Critical avg wait": None if m["critical_avg_wait"] is None else round(m["critical_avg_wait"], 1),
                     "Severity inversions": m["severity_inversions"]})
    return rows


def _tab_compare() -> None:
    ps = state.patients()
    if not ps:
        empty_state("No patients to compare", "Add or import patients first.")
        return
    if len(ps) > REPLAY_CAP:
        callout(f"The replay runs O(n^2) strategies, so it is limited to {REPLAY_CAP} patients. "
                f"You have {len(ps)}. Use the Performance Benchmarking page for large inputs.", "warn")
        return
    c1, c2, c3 = st.columns(3)
    horizon = c1.number_input("Throughput horizon (min)", 30, 10_000, 240, step=30)
    threshold = c2.number_input("Starvation threshold: wait above (min)", 1, 1000, 60, step=5)
    refresh = c3.checkbox("Heap: refresh keys before every extraction", value=False,
                          help="Makes the heap reproduce the greedy order exactly, at higher cost.")
    cfg = state.cfg()
    results = run_all(ps, cfg, refresh_heap=refresh)
    metrics = {s: metrics_for_result(r, int(horizon), int(threshold)) for s, r in results.items()}
    st.markdown("##### Same dataset, four strategies")
    table(_metric_rows(metrics))
    st.caption(f"Replay of all {len(ps)} patients from their arrival times, single treatment bay, non-preemptive. "
               f"Throughput counts patients finished within {int(horizon)} min of the first start.")
    a, b = st.columns(2)
    with a:
        plot(charts.wait_comparison_bar(metrics, STRATEGY_LABELS), key="cmp_wait")
    with b:
        sel = st.selectbox("Scatter and timeline strategy", STRATEGY_ORDER, index=STRATEGY_ORDER.index(state.strategy()),
                           format_func=lambda k: STRATEGY_LABELS[k], key="cmp_sel")
        plot(charts.wait_vs_treatment_scatter(results[sel], f"Treatment vs waiting - {STRATEGY_LABELS[sel]}"), key="cmp_sc")
    plot(charts.queue_position_comparison(results, STRATEGY_LABELS), key="cmp_pos")
    if len(ps) > 40:
        st.caption("Queue-position chart shows the first 40 patients by arrival.")
    plot(charts.gantt_figure(results[sel], f"Schedule timeline - {STRATEGY_LABELS[sel]}"), key="cmp_gantt")
    with st.expander("Greedy decision log (why each patient was chosen)"):
        table([{"Step": d["step"], "Clock": d["clock"], "Chosen": d["patient_id"], "Severity": d["severity"],
                "Score": round(d["score"], 2), "Waiting": d["candidates"], "Reason": d["reason"]}
               for d in results["greedy"].trace[:60]])
    with st.expander("Assumptions of this comparison"):
        for a_ in ASSUMPTIONS:
            st.write(f"- {a_}")
    callout("<b>Reading the table.</b> No strategy wins every column. Shortest-treatment-first usually lowers the average wait but "
            "ignores severity; FCFS is simple and equal but can leave critical patients behind; greedy weighted priority "
            "protects severity at some cost in average wait. The numbers above are computed from your current dataset.")


def _order_table(results, ids):
    rows = []
    for pid in ids:
        e0 = results[STRATEGY_ORDER[0]].entry_for(pid)
        row = {"Patient": pid, "Severity": e0.patient.severity, "Arrival": e0.patient.arrival_time, "Treatment": e0.treatment}
        for s in STRATEGY_ORDER:
            e = results[s].entry_for(pid)
            row[STRATEGY_LABELS[s]] = f"#{e.position}, waited {e.wait}"
        rows.append(row)
    return rows


def _scenario_block(data, focus_id, kind):
    results = run_all(data["patients"], ScoreConfig())
    ids = [p.patient_id for p in sort_patients(data["patients"], "arrival")]
    st.write(data["description"])
    table(_order_table(results, ids))
    g, f, stf = (results[k].entry_for(focus_id) for k in ("greedy", "fcfs", "stf"))
    n = len(ids)
    if kind == "critical":
        callout(f"<b>{focus_id}</b> is served #{f.position} of {n} under FCFS (waits {f.wait} min), #{g.position} under greedy "
                f"(waits {g.wait} min) and #{stf.position} under shortest-treatment-first (waits {stf.wait} min). "
                f"Because service is non-preemptive, nobody can jump ahead of the patient already in treatment.")
    else:
        callout(f"<b>{focus_id}</b> waits {stf.wait} min under shortest-treatment-first (position #{stf.position} of {n}) versus "
                f"{f.wait} min under FCFS and {g.wait} min under greedy. A stream of shorter jobs keeps bypassing this patient: "
                f"the starvation risk of shortest-job-first. It is not a safe clinical policy.")


def _tab_tradeoffs() -> None:
    st.write("Each case below is run live on a small hand-built dataset, so you can see where a single strategy "
             "fails to be best on every objective.")
    with st.expander("1. A critical patient arriving after several lower-priority patients", expanded=True):
        _scenario_block(sc.critical_arrives_last(), "CRIT", "critical")
    with st.expander("2. FCFS delaying a high-severity patient"):
        _scenario_block(sc.high_severity_behind_queue(), "HIGH", "critical")
    with st.expander("3. A long-treatment patient repeatedly bypassed by shortest-treatment-first"):
        _scenario_block(sc.long_treatment_stf(), "LONG", "stf")
    with st.expander("4. A patient's score rises as they wait"):
        d = sc.score_over_time_patients()
        low, fresh = d["waiting"], d["fresh"]
        cfg = ScoreConfig()
        xs = list(range(0, 181, 5))
        low_scores = [priority_score(low, w, cfg) for w in xs]
        fresh_score = priority_score(fresh, 0, cfg)
        cross = next((w for w, s in zip(xs, low_scores) if s > fresh_score), None)
        plot(charts.score_over_time_figure({"Low-severity patient waiting": (xs, low_scores),
                                            "Moderate patient arriving now (constant)": (xs, [fresh_score] * len(xs))},
                                           "Priority score against minutes waited"), key="tr_score")
        if cross is not None:
            callout(f"The waiting Low-severity patient overtakes a fresh Moderate arrival after about <b>{cross} minutes</b> "
                    f"(score {priority_score(low, cross, cfg):.2f} vs {fresh_score:.2f}). Waiting is capped at {cfg.wait_cap} min, so the "
                    f"score stops rising after that point. The waiting term is what limits starvation under the greedy policy.")
        else:
            callout("With these weights the waiting patient never overtakes the fresh arrival within 180 minutes.", "warn")
    with st.expander("5. The same patients, three weight sets, three orders"):
        d = sc.weights_change_order()
        rows = []
        for name, cfg in sc.WEIGHT_SETS.items():
            order = sort_patients(d["patients"], "priority", d["now"], cfg)
            rows.append({"Weights (sev/med/wait/age)": name, "Order served": " > ".join(p.patient_id for p in order)})
        st.write(d["description"])
        table(rows)
        callout("Greedy choices are optimal only for the score that defines them. Change the weights and the 'best' patient changes. "
                "There is no objectively correct weighting; this is an educational policy, not validated triage.")
    st.markdown("##### Trade-offs to discuss")
    st.markdown(
        "- **Severity prioritisation vs average waiting time:** serving the sickest first can raise the mean wait.\n"
        "- **Fairness vs urgency:** FCFS is the most equal in order but ignores urgency.\n"
        "- **Starvation:** shortest-treatment-first can starve long cases; the capped waiting term bounds it for greedy scoring.\n"
        "- **Throughput:** with one bay and no idling, total work is identical for all strategies, so throughput differences come from the horizon cut-off only.\n"
        "- **Local vs global optimality:** greedy is locally optimal under the score at each step, not globally optimal for every hospital objective.")


def _tab_complexity() -> None:
    st.markdown("##### Core algorithms")
    table(COMPLEXITY_BASIC)
    st.caption("Merge sort needs O(n) auxiliary space for merge buffers. Heap operations work in place on the array (plus the O(n) position map).")
    st.markdown("##### Complete scheduling strategies (as implemented here)")
    table(COMPLEXITY_STRATEGIES)
    st.markdown(
        "**How to read this.** r is the number of patients waiting at a decision, n the total number scheduled. "
        "One decision, scheduling all n patients, sorting a fixed queue, and repeated heap insert/extract are different "
        "operations and are listed separately. Complexity statements depend on the implementation assumptions in the notes column.")


def render() -> None:
    section_header("Algorithm comparison",
                   "Greedy weighted priority, a priority heap, FCFS and shortest treatment first on the same dataset.")
    state.show_flash()
    t1, t2, t3 = st.tabs(["Strategy comparison", "Trade-offs and non-optimal cases", "Complexity analysis"])
    with t1:
        _tab_compare()
    with t2:
        _tab_tradeoffs()
    with t3:
        _tab_complexity()
    disclaimer()

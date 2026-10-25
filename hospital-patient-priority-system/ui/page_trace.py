from __future__ import annotations

import streamlit as st

from algorithms.greedy_scheduler import score_components
from algorithms.max_heap import patient_heap
from algorithms.greedy_scheduler import priority_score
from algorithms.merge_sort import CRITERIA, sort_patients
from algorithms.models import STATUS_WAITING
from algorithms.scheduling_strategies import STRATEGY_LABELS, simulate
from utils import charts
from . import state
from .components import callout, disclaimer, empty_state, plot, section_header, table

MAX_TRACE = 12


def render() -> None:
    section_header("Visualization and algorithm trace",
                   "Step through merge sort, the binary max-heap and greedy decisions on a handful of real patients from the current dataset.")
    state.show_flash()
    t, cfg = state.now(), state.cfg()
    pool = sort_patients([p for p in state.patients() if p.status == STATUS_WAITING and p.arrival_time <= t], "arrival")
    if len(pool) < 2:
        empty_state("Not enough waiting patients", "Two or more arrived, waiting patients are needed. Add patients or advance the clock.")
        disclaimer()
        return
    options = [p.patient_id for p in pool]
    picked = st.multiselect(f"Patients to trace (2 to {MAX_TRACE})", options, default=options[:8], max_selections=MAX_TRACE)
    subset = [p for p in pool if p.patient_id in picked]
    if len(subset) < 2:
        empty_state("Select at least two patients", "The trace needs two or more patients.")
        disclaimer()
        return
    sev = {p.patient_id: p.severity for p in subset}

    tabs = st.tabs(["Merge sort trace", "Binary heap trace", "Greedy decisions", "Score components", "Schedule timeline"])

    with tabs[0]:
        crit = st.selectbox("Sort by", list(CRITERIA), format_func=lambda k: CRITERIA[k], key="trace_crit")
        steps, stats = [], {}
        result = sort_patients(subset, crit, t, cfg, stats, steps)
        st.write("**Input sequence:** " + ", ".join(p.patient_id for p in subset))
        st.write("**Sorted sequence:** " + ", ".join(p.patient_id for p in result))
        st.caption(f"{stats.get('merges', 0)} merges and {stats.get('comparisons', 0)} comparisons for n = {len(subset)}. "
                   "Merge sort is O(n log n) in best, average and worst case, with O(n) auxiliary space.")
        plot(charts.merge_steps_figure(steps, len(subset)), key="trace_merge")
        table([{"Step": i + 1, "Operation": "Split" if s["type"] == "split" else "Merge", "Depth": s["depth"],
                "Left": ", ".join(s["left"]), "Right": ", ".join(s["right"]),
                "Merged result": ", ".join(s.get("merged", [])), "Comparisons": s.get("comparisons")}
               for i, s in enumerate(steps)])
        st.caption("Numbers in brackets are the sort key (score, severity, waiting minutes, arrival minute or treatment minutes).")

    with tabs[1]:
        heap = patient_heap(record=True)
        for p in subset:
            heap.insert(p.patient_id, priority_score(p, t, cfg), p)
        while not heap.is_empty():
            heap.extract()
        hist = heap.history
        idx = st.slider("Operation", 1, len(hist), 1, help="First all inserts, then repeated extractions of the root.")
        h = hist[idx - 1]
        st.write(f"**Step {idx} of {len(hist)}: {h['op'].title()}** - {h['detail']}")
        moved = [x for pair in h["swaps"] for x in pair]
        plot(charts.heap_tree_figure(h["array"], sev, moved), key="trace_heap")
        table([{"Index": i, "Patient": a[0], "Score": round(a[1], 2), "Parent index": None if i == 0 else (i - 1) // 2}
               for i, a in enumerate(h["array"])])
        st.caption("Array rule: children of index i are 2i+1 and 2i+2. Outlined nodes were swapped in this step. "
                   "Insert and extract are O(log n); peek is O(1).")

    with tabs[2]:
        res = simulate(subset, "greedy", cfg, start_clock=t)
        st.write("The greedy scheduler picks the highest-scoring patient each time the bay is free; scores are recomputed at every step.")
        table([{"Step": d["step"], "Clock": d["clock"], "Chosen": d["patient_id"], "Severity": d["severity"],
                "Score": round(d["score"], 2), "Candidates": d["candidates"], "Why": d["reason"]} for d in res.trace])
        callout("This choice is locally optimal for the scoring policy at each step. It is not guaranteed to minimise average waiting time "
                "or to be best for any objective other than the score.")

    with tabs[3]:
        ordered = sort_patients(subset, "priority", t, cfg)
        rows = [{"patient": p, **score_components(p, t, cfg)} for p in ordered]
        plot(charts.priority_ranking_bar(rows), key="trace_rank")
        plot(charts.component_breakdown(rows), key="trace_comp")
        table([{"Rank": i + 1, "ID": r["patient"].patient_id, "Severity": f"{r['severity_norm']:.0f} -> {r['severity_pts']:.1f}",
                "Medical": f"{r['medical_norm']:.0f} -> {r['medical_pts']:.1f}",
                "Waiting": f"{r['waiting_minutes']} min = {r['waiting_norm']:.0f} -> {r['waiting_pts']:.1f}",
                "Age": f"{r['age_norm']:.0f} -> {r['age_pts']:.1f}", "Final": round(r["total"], 2)} for i, r in enumerate(rows)])
        st.caption("Each cell shows normalised value -> weighted points.")

    with tabs[4]:
        strat = st.selectbox("Strategy", list(STRATEGY_LABELS), index=list(STRATEGY_LABELS).index(state.strategy()),
                             format_func=lambda k: STRATEGY_LABELS[k], key="trace_strat")
        res = simulate(subset, strat, cfg, start_clock=t)
        plot(charts.gantt_figure(res, f"Timeline - {STRATEGY_LABELS[strat]}"), key="trace_gantt")
        st.caption("Grey = waiting from arrival to treatment start; colour = treatment, by severity.")
    disclaimer()

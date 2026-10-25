from __future__ import annotations

import streamlit as st

from algorithms.metrics import compute_metrics, severity_distribution
from algorithms.scheduling_strategies import STRATEGY_LABELS
from utils import charts
from . import state
from .components import callout, disclaimer, empty_state, fmt, kpi_row, plot, section_header


def render() -> None:
    section_header("Overview dashboard",
                   "Live state of the simulated emergency department. Every page works on this same dataset.")
    state.show_flash()
    ps = state.patients()
    if not ps:
        empty_state("No patients yet", "Open Patient Registration to add, generate or import synthetic patients.")
        disclaimer()
        return
    snap = state.queue_snapshot()
    ordered = snap["ordered"]
    completed = snap["completed"]
    kpi_row([("Simulated clock", f"min {state.now()}", "advance it on Live Patient Queue", ""),
             ("Waiting now", len(ordered), f"{len(snap['future'])} not yet arrived", "blue"),
             ("In treatment", len(snap["in_treatment"]), "one treatment bay", "high"),
             ("Completed", len(completed), "kept in performance history", "grey"),
             ("Active strategy", STRATEGY_LABELS[state.strategy()], "change in the sidebar", "")])

    left, right = st.columns([1, 1.4])
    with left:
        counts = severity_distribution(ordered)
        plot(charts.severity_distribution_bar(counts, "Severity of waiting patients"), key="ov_sev")
    with right:
        rows = state.component_rows(ordered)
        # show the top 12 by the greedy score regardless of strategy so the chart is always a score ranking
        from algorithms.merge_sort import sort_patients
        top = sort_patients([r["patient"] for r in rows], "priority", state.now(), state.cfg())[:12]
        by_id = {r["patient"].patient_id: r for r in rows}
        plot(charts.priority_ranking_bar([by_id[p.patient_id] for p in top], "Top 12 by priority score"), key="ov_rank")

    st.markdown("##### Next patient under the active strategy")
    if ordered:
        callout(state.explain_next(ordered))
    else:
        empty_state("Nobody is waiting", "Advance the clock or add patients to continue.")

    st.markdown("##### History so far")
    if completed:
        m = compute_metrics(completed, completed[0].start_time if completed else 0)
        kpi_row([("Average wait", f"{fmt(m['avg_wait'])} min", "completed patients", ""),
                 ("Maximum wait", f"{m['max_wait']} min", "", "high"),
                 ("Average turnaround", f"{fmt(m['avg_turnaround'])} min", "wait + treatment", "blue"),
                 ("Total treatment", f"{m['total_treatment']} min", f"{m['n_scheduled']} patients", "grey")])
    else:
        empty_state("No completed treatments yet", "Use Start treatment and Complete treatment on Live Patient Queue.")
    disclaimer()


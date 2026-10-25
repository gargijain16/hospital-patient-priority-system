from __future__ import annotations

import streamlit as st

from algorithms.scheduling_strategies import STRATEGY_LABELS
from utils.validation import records_to_csv
from . import state
from .components import callout, disclaimer, empty_state, kpi_row, plot, section_header, table
from utils import charts

RESULT_FIELDS = ("patient_id", "name", "age", "severity", "severity_score", "medical_priority", "arrival_time",
                 "waiting_time", "treatment_time", "priority_score", "queue_position", "status", "start_time", "finish_time")


def results_csv() -> str:
    state.queue_snapshot()   # refresh cached scores and positions before exporting
    t = state.now()
    rows = []
    for p in state.patients():
        rows.append({"patient_id": p.patient_id, "name": p.name, "age": p.age, "severity": p.severity,
                     "severity_score": p.severity_score, "medical_priority": p.medical_priority,
                     "arrival_time": p.arrival_time, "waiting_time": p.waiting_time(t), "treatment_time": p.treatment_time,
                     "priority_score": "" if p.priority_score is None else f"{p.priority_score:.4f}",
                     "queue_position": "" if p.queue_position is None else p.queue_position, "status": p.status,
                     "start_time": "" if p.start_time is None else p.start_time,
                     "finish_time": "" if p.finish_time is None else p.finish_time})
    return records_to_csv(rows, RESULT_FIELDS)


def _row(p, t):
    return {"Pos": p.queue_position, "ID": p.patient_id, "Name": p.name, "Age": p.age, "Severity": p.severity,
            "Med. priority": p.medical_priority, "Arrival": p.arrival_time, "Waited (min)": p.waiting_time(t),
            "Treatment (min)": p.treatment_time, "Score": round(p.priority_score, 2) if p.priority_score is not None else None}


def render() -> None:
    section_header("Live patient queue",
                   f"Strategy in use: {STRATEGY_LABELS[state.strategy()]}. Change it in the sidebar.")
    state.show_flash()
    t = state.now()
    snap = state.queue_snapshot()
    ordered, future, current, done = snap["ordered"], snap["future"], snap["in_treatment"], snap["completed"]

    kpi_row([("Simulated clock", f"min {t}", "", ""), ("Waiting", len(ordered), f"{len(future)} arrive later", "blue"),
             ("In treatment", len(current), "", "high"), ("Completed", len(done), "", "grey")])

    st.markdown("##### Simulation controls")
    c = st.columns([1, 1, 1, 1.4, 1.2, 1.2])
    c[0].button("Advance 5 min", on_click=state.advance, args=(5,))
    c[1].button("Advance 15 min", on_click=state.advance, args=(15,))
    c[2].button("Advance 30 min", on_click=state.advance, args=(30,))
    custom = c[3].number_input("Custom minutes", 1, 10_000, 10, step=1, label_visibility="collapsed")
    c[3].button("Advance by custom", on_click=state.advance, args=(int(custom),))
    c[4].button("Start treatment", type="primary", on_click=state.start_treatment,
                help="Begins treatment for the first patient in the current order.")
    c[5].button("Complete treatment", on_click=state.complete_treatment,
                help="Finishes the patient in treatment; the clock jumps to their finish time if needed.")
    st.button("Recompute priorities", on_click=lambda: state.flash("info", f"Priorities recomputed at minute {state.now()}."),
              help="Scores are always recomputed from the clock; this button just confirms it.")

    if current:
        p = current[0]
        callout(f"<b>In treatment:</b> {p.patient_id} ({p.severity}) started at minute {p.start_time}, "
                f"finishes at minute {p.finish_time}. Waited {p.start_time - p.arrival_time} min.", "info")
    if ordered:
        callout(f"<b>Why this order?</b> {state.explain_next(ordered)}")

    tab_q, tab_why, tab_future, tab_done = st.tabs(["Waiting queue", "Score breakdown", "Not yet arrived", "Completed history"])
    with tab_q:
        if ordered:
            table([_row(p, t) for p in ordered], height=min(560, 60 + 35 * len(ordered)))
        else:
            empty_state("The queue is empty", "Advance the clock, add a patient, or restore the demonstration dataset.")
    with tab_why:
        if ordered:
            rows = state.component_rows(ordered)
            show = rows[:25]
            plot(charts.component_breakdown(show, "Score components in queue order (first 25)"), key="q_comp")
            table([{"Pos": r["patient"].queue_position, "ID": r["patient"].patient_id, "Waited (min)": r["waiting_minutes"],
                    "Severity pts": round(r["severity_pts"], 2), "Medical pts": round(r["medical_pts"], 2),
                    "Waiting pts": round(r["waiting_pts"], 2), "Age pts": round(r["age_pts"], 2),
                    "Final score": round(r["total"], 2)} for r in show])
            st.caption("Points = weight x normalised component (0-100). The score is shown for every strategy; "
                       "FCFS and shortest-treatment-first ignore it when choosing.")
        else:
            empty_state("Nothing to explain", "No arrived patient is waiting.")
    with tab_future:
        if future:
            table([{"ID": p.patient_id, "Arrives at minute": p.arrival_time, "In (min)": p.arrival_time - t,
                    "Severity": p.severity, "Treatment (min)": p.treatment_time} for p in future])
        else:
            st.caption("Every waiting patient has already arrived.")
    with tab_done:
        if done:
            table([{"Order": i + 1, "ID": p.patient_id, "Severity": p.severity, "Arrival": p.arrival_time, "Start": p.start_time,
                    "Finish": p.finish_time, "Waited (min)": p.start_time - p.arrival_time,
                    "Treatment (min)": p.treatment_time, "Turnaround (min)": p.finish_time - p.arrival_time}
                   for i, p in enumerate(done)])
        else:
            empty_state("No completed treatments", "Start and complete a treatment to build the history.")
    if state.patients():
        st.download_button("Download queue and results (CSV)", results_csv(), "queue_results.csv", "text/csv")
    disclaimer()

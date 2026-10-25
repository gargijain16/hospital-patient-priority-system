"""Session state and shared queue logic. Every page reads the same ``st.session_state.patients`` list."""
from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

from algorithms.models import (STATUS_COMPLETED, STATUS_IN_TREATMENT, STATUS_WAITING, DEFAULT_AGE_BANDS,
                               Patient, ScoreConfig)
from algorithms.greedy_scheduler import greedy_select, explain_choice, score_components
from algorithms.scheduling_strategies import snapshot_order
from algorithms.merge_sort import sort_patients
from utils.sample_data import DEMO_NOW, demo_patients, generate_patients
from utils.validation import max_id_number

DEFAULT_TEAM = {"Student 1": "Student 1 name", "Student 2": "Student 2 name", "Student 3": "Student 3 name"}


def age_bands_to_text(bands) -> str:
    return "\n".join(f"{upper},{score:g}" for upper, score in bands)


DEFAULT_AGE_TEXT = age_bands_to_text(DEFAULT_AGE_BANDS)


def init_state() -> None:
    ss = st.session_state
    if "patients" in ss:
        return
    ss.patients = demo_patients()
    ss.now = DEMO_NOW
    ss.strategy = "greedy"
    ss.flash = []
    ss.uploader_key = 0
    ss.bench = None
    ss.team = dict(DEFAULT_TEAM)
    ss.cfg = ScoreConfig()


# ---------------------------------------------------------------------------- flash messages
def flash(kind: str, text: str) -> None:
    st.session_state.flash.append((kind, text))


def show_flash() -> None:
    msgs = st.session_state.flash
    st.session_state.flash = []
    for kind, text in msgs:
        {"success": st.success, "error": st.error, "warning": st.warning}.get(kind, st.info)(text)


# ---------------------------------------------------------------------------- accessors
def patients() -> List[Patient]:
    return st.session_state.patients


def now() -> int:
    return st.session_state.now


def cfg() -> ScoreConfig:
    return st.session_state.cfg


def strategy() -> str:
    return st.session_state.strategy


def ids() -> set:
    return {p.patient_id for p in patients()}


def by_status(status: str) -> List[Patient]:
    return [p for p in patients() if p.status == status]


def queue_snapshot() -> Dict[str, List[Patient]]:
    """Order the waiting patients under the active strategy and refresh cached scores/positions."""
    t, c = now(), cfg()
    arrived = [p for p in patients() if p.status == STATUS_WAITING and p.arrival_time <= t]
    future = [p for p in patients() if p.status == STATUS_WAITING and p.arrival_time > t]
    ordered = snapshot_order(strategy(), arrived, t, c)
    for i, p in enumerate(ordered):
        p.queue_position = i + 1
        p.priority_score = score_components(p, t, c)["total"]
    for p in future + by_status(STATUS_IN_TREATMENT) + by_status(STATUS_COMPLETED):
        p.queue_position = None
    future = sort_patients(future, "arrival")
    return {"ordered": ordered, "future": future, "in_treatment": by_status(STATUS_IN_TREATMENT),
            "completed": completed_in_order()}


def completed_in_order() -> List[Patient]:
    return sort_patients_by_start([p for p in patients() if p.status == STATUS_COMPLETED])


def sort_patients_by_start(done: List[Patient]) -> List[Patient]:
    from algorithms.merge_sort import merge_sort
    return merge_sort(done, lambda a, b: (a.start_time, a.patient_id) < (b.start_time, b.patient_id))


def component_rows(ordered: List[Patient]) -> List[Dict]:
    t, c = now(), cfg()
    rows = []
    for p in ordered:
        comp = score_components(p, t, c)
        rows.append({"patient": p, **comp})
    return rows


def explain_next(ordered: List[Patient]) -> str:
    if not ordered:
        return "No arrived patient is waiting."
    s = strategy()
    top = ordered[0]
    if s == "greedy":
        return explain_choice(greedy_select(ordered, now(), cfg()))
    if s == "heap":
        return (f"{top.patient_id} is the root of the max-heap (score {top.priority_score:.2f}); it has the highest "
                f"score, with ties broken by severity, arrival, then ID.")
    if s == "fcfs":
        return f"{top.patient_id} arrived first (minute {top.arrival_time}) among {len(ordered)} waiting patient(s)."
    return (f"{top.patient_id} needs the shortest treatment ({top.treatment_time} min) among {len(ordered)} waiting "
            f"patient(s). Severity is ignored by this strategy.")


# ---------------------------------------------------------------------------- actions (callbacks)
def add_patient(p: Patient) -> None:
    patients().append(p)


def remove_patient(pid: str) -> None:
    st.session_state.patients = [p for p in patients() if p.patient_id != pid]
    flash("success", f"Removed {pid}.")


def reset_demo() -> None:
    st.session_state.patients = demo_patients()
    st.session_state.now = DEMO_NOW
    flash("success", "Demonstration dataset restored and the clock reset.")


def clear_all() -> None:
    st.session_state.patients = []
    st.session_state.now = 0
    flash("success", "All patients cleared. Add or import patients to continue.")


def advance(minutes: int) -> None:
    st.session_state.now += int(minutes)
    flash("info", f"Clock advanced {int(minutes)} min to minute {now()}. Waiting times and scores were recomputed.")


def start_treatment() -> None:
    if by_status(STATUS_IN_TREATMENT):
        flash("error", "The treatment bay is busy. Complete the current treatment first.")
        return
    snap = queue_snapshot()
    if not snap["ordered"]:
        flash("warning", "Nobody has arrived and is waiting at this minute. Advance the clock or add patients.")
        return
    p = snap["ordered"][0]
    why = explain_next(snap["ordered"])
    p.status = STATUS_IN_TREATMENT
    p.start_time = now()
    p.finish_time = now() + p.treatment_time
    flash("success", f"Started treatment for {p.patient_id} at minute {now()} (finishes at {p.finish_time}). {why}")


def complete_treatment() -> None:
    cur = by_status(STATUS_IN_TREATMENT)
    if not cur:
        flash("error", "No patient is in treatment.")
        return
    p = cur[0]
    if now() < p.finish_time:
        st.session_state.now = p.finish_time
    p.status = STATUS_COMPLETED
    flash("success", f"{p.patient_id} completed at minute {p.finish_time}. Waited {p.start_time - p.arrival_time} min, "
                     f"turnaround {p.finish_time - p.arrival_time} min.")


def generate_synthetic(n: int, seed: Optional[int], past: bool, mean_gap: float, critical_share: float) -> None:
    start = max_id_number(ids()) + 1
    new = generate_patients(n, seed=seed, start_index=start, mean_gap=mean_gap, critical_share=critical_share)
    if new:
        last = new[-1].arrival_time
        for p in new:
            p.arrival_time = max(0, now() - (last - p.arrival_time)) if past else now() + p.arrival_time
    patients().extend(new)
    flash("success", f"Added {len(new)} synthetic patients ({'already waiting' if past else 'arriving over the next minutes'}).")


def import_patients(new: List[Patient], replace: bool) -> None:
    if replace:
        st.session_state.patients = list(new)
        st.session_state.now = 0
        for p in new:
            if p.arrival_time > st.session_state.now:
                st.session_state.now = p.arrival_time
    else:
        patients().extend(new)
    st.session_state.uploader_key += 1
    flash("success", f"Imported {len(new)} patients ({'replacing' if replace else 'appended to'} the dataset).")

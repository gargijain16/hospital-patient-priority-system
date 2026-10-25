from __future__ import annotations

import streamlit as st

from algorithms.models import (MAX_AGE, MAX_MEDICAL_PRIORITY, MAX_TREATMENT_MINUTES, MIN_MEDICAL_PRIORITY,
                               SEVERITY_ORDER, STATUS_WAITING)
from utils.sample_data import demo_csv_text
from utils.validation import next_patient_id, parse_csv, patients_to_input_csv, validate_record
from . import state
from .components import callout, disclaimer, empty_state, section_header, table


def _save_new(raw) -> None:
    p, errs = validate_record(raw, state.ids())
    if errs:
        for e in errs:
            state.flash("error", e)
        return
    state.add_patient(p)
    state.flash("success", f"Added {p.patient_id} ({p.severity}, arrives at minute {p.arrival_time}).")


def _save_edit(pid: str, raw) -> None:
    others = state.ids() - {pid}
    p, errs = validate_record({**raw, "patient_id": pid}, others)
    if errs:
        for e in errs:
            state.flash("error", e)
        return
    for i, old in enumerate(state.patients()):
        if old.patient_id == pid:
            state.patients()[i] = p
    state.flash("success", f"Updated {pid}.")


def render() -> None:
    section_header("Patient registration",
                   "Add, edit, remove, generate or import synthetic patients. Do not enter real personal data.")
    state.show_flash()
    tab_add, tab_edit, tab_gen, tab_csv, tab_reset = st.tabs(
        ["Add patient", "Edit or remove", "Generate synthetic", "CSV import / export", "Reset"])

    with tab_add:
        with st.form("add_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            pid = c1.text_input("Patient ID", value=next_patient_id(state.ids()), help="Unique. Letters, digits, - and _ only.")
            name = c2.text_input("Synthetic label", value="", placeholder="e.g. Demo Patient 25 (optional)")
            c3, c4, c5 = st.columns(3)
            age = c3.number_input("Age", 0, MAX_AGE, 35, step=1)
            sev = c4.selectbox("Emergency severity", list(SEVERITY_ORDER), index=2)
            med = c5.number_input("Medical priority (5 = highest)", MIN_MEDICAL_PRIORITY, MAX_MEDICAL_PRIORITY, 3, step=1)
            c6, c7 = st.columns(2)
            arr = c6.number_input("Arrival minute", 0, 10_000_000, int(state.now()), step=1,
                                  help="Defaults to the current simulated minute. A future minute schedules a later arrival.")
            tr = c7.number_input("Required treatment time (min)", 1, MAX_TREATMENT_MINUTES, 20, step=1)
            submitted = st.form_submit_button("Add patient", type="primary")
        if submitted:
            _save_new({"patient_id": pid, "name": name, "age": age, "severity": sev, "medical_priority": med,
                       "arrival_time": arr, "treatment_time": tr})
            st.rerun()

    with tab_edit:
        waiting = [p for p in state.patients() if p.status == STATUS_WAITING]
        if not waiting:
            empty_state("No waiting patients to edit", "Only patients with status Waiting can be edited or removed.")
        else:
            chosen = st.selectbox("Waiting patient", [p.patient_id for p in waiting], key="edit_pick")
            p = next(x for x in waiting if x.patient_id == chosen)
            k = f"edit_{chosen}"
            with st.form(f"edit_form_{chosen}"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Synthetic label", p.name, key=f"{k}_name")
                age = c2.number_input("Age", 0, MAX_AGE, p.age, step=1, key=f"{k}_age")
                c3, c4 = st.columns(2)
                sev = c3.selectbox("Emergency severity", list(SEVERITY_ORDER), index=list(SEVERITY_ORDER).index(p.severity), key=f"{k}_sev")
                med = c4.number_input("Medical priority", MIN_MEDICAL_PRIORITY, MAX_MEDICAL_PRIORITY, p.medical_priority, step=1, key=f"{k}_med")
                c5, c6 = st.columns(2)
                arr = c5.number_input("Arrival minute", 0, 10_000_000, p.arrival_time, step=1, key=f"{k}_arr")
                tr = c6.number_input("Treatment time (min)", 1, MAX_TREATMENT_MINUTES, p.treatment_time, step=1, key=f"{k}_tr")
                save = st.form_submit_button("Save changes", type="primary")
            if save:
                _save_edit(chosen, {"name": name, "age": age, "severity": sev, "medical_priority": med,
                                    "arrival_time": arr, "treatment_time": tr})
                st.rerun()
            st.button(f"Remove {chosen}", on_click=state.remove_patient, args=(chosen,))

    with tab_gen:
        c1, c2, c3 = st.columns(3)
        n = c1.number_input("How many patients", 1, 5000, 10, step=1)
        seed = c2.number_input("Random seed", 0, 1_000_000, 42, step=1, help="The same seed always produces the same patients.")
        gap = c3.number_input("Mean minutes between arrivals", 0.5, 60.0, 4.0, step=0.5)
        crit = st.slider("Share of Critical patients", 0, 30, 8, format="%d%%") / 100
        mode = st.radio("Arrival pattern", ["Already waiting (arrived in the past)", "Arriving over the next minutes"], horizontal=True)
        st.button("Generate patients", type="primary", on_click=state.generate_synthetic,
                  args=(int(n), int(seed), mode.startswith("Already"), float(gap), crit))
        callout("Generated records are synthetic. They are not real hospital data.", "info")

    with tab_csv:
        st.download_button("Download sample CSV (24 synthetic patients)", demo_csv_text(), "sample_patients.csv", "text/csv")
        callout("Required columns: <b>age, severity, medical_priority, arrival_time, treatment_time</b>. "
                "Optional: <b>patient_id</b> (generated if blank), <b>name</b>. Imported rows start as Waiting.", "info")
        up = st.file_uploader("Upload a patient CSV", type=["csv"], key=f"csv_{st.session_state.uploader_key}")
        if up is not None:
            try:
                text = up.getvalue().decode("utf-8-sig")
            except UnicodeDecodeError:
                text = ""
                st.error("The file is not valid UTF-8 text.")
            if text:
                new, errs = parse_csv(text, state.ids())
                if errs:
                    st.error(f"{len(errs)} problem(s) found. Nothing was imported.")
                    for e in errs[:25]:
                        st.write(f"- {e}")
                    if len(errs) > 25:
                        st.write(f"...and {len(errs) - 25} more.")
                else:
                    st.success(f"{len(new)} valid patients found.")
                    table([{"ID": x.patient_id, "Age": x.age, "Severity": x.severity, "Priority": x.medical_priority,
                            "Arrival": x.arrival_time, "Treatment": x.treatment_time} for x in new[:10]])
                    mode = st.radio("Import mode", ["Append to current dataset", "Replace current dataset"], horizontal=True)
                    st.button("Import patients", type="primary", on_click=state.import_patients,
                              args=(new, mode.startswith("Replace")))
        st.markdown("##### Export current dataset")
        if state.patients():
            from .page_queue import results_csv
            st.download_button("Download queue and results (CSV)", results_csv(), "queue_results.csv", "text/csv")
            st.download_button("Download patient inputs only (CSV)", patients_to_input_csv(state.patients()), "patients.csv", "text/csv")
        else:
            st.caption("Nothing to export yet.")

    with tab_reset:
        c1, c2 = st.columns(2)
        c1.button("Restore demonstration dataset", on_click=state.reset_demo, type="primary",
                  help="24 synthetic patients, clock back to minute 60. Completed history is discarded.")
        c2.button("Remove all patients", on_click=state.clear_all, help="Gives an empty queue for testing edge cases.")
    disclaimer()

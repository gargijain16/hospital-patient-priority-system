from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

from utils import testlab
from utils.audit import scan_algorithms
from utils.sample_data import generate_patients
from .components import disclaimer, empty_state, kpi_row, section_header, table
from . import state

ROOT = Path(__file__).resolve().parent.parent


def _show(rows):
    if not rows:
        return
    passed = sum(1 for r in rows if r["passed"])
    failed = len(rows) - passed
    kpi_row([("Checks run", len(rows), "", "blue"), ("Passed", passed, "", ""), ("Failed", failed, "", "critical" if failed else "grey")])
    if failed:
        st.error(f"{failed} check(s) failed.")
    else:
        st.success("All checks passed.")
    table([{"Result": "PASS" if r["passed"] else "FAIL", "Scenario": r["scenario"], "Check": r["check"], "Detail": r["detail"]}
           for r in rows], height=min(600, 60 + 35 * len(rows)))


def render() -> None:
    section_header("Test lab", "Scenario checks run live against the real algorithms, plus the automated pytest suite and a static audit.")
    state.show_flash()
    tabs = st.tabs(["Scenarios", "Custom dataset", "Unit tests (pytest)", "Code audit", "Reproducibility"])

    with tabs[0]:
        group = st.selectbox("Scenario group", ["All groups"] + testlab.groups())
        names = [s[2] for s in testlab.SCENARIOS if group == "All groups" or s[1] == group]
        st.caption("Includes: " + "; ".join(names))
        if group == "All groups" or group.startswith("C"):
            st.caption("Large cases (1,000 to 10,000 patients) can take several seconds.")
        if st.button("Run selected scenarios", type="primary"):
            with st.spinner("Running scenarios"):
                st.session_state.lab_rows = testlab.run_scenarios(None if group == "All groups" else group)
        rows = st.session_state.get("lab_rows")
        if rows:
            _show(rows)
        else:
            empty_state("No scenario results yet", "Press Run selected scenarios.")

    with tabs[1]:
        c1, c2, c3 = st.columns(3)
        n = c1.number_input("Patients", 1, 3000, 200, step=50)
        seed = c2.number_input("Seed", 0, 1_000_000, 123, step=1)
        crit = c3.slider("Critical share", 0, 40, 8, format="%d%%") / 100
        if st.button("Run checks on custom dataset"):
            with st.spinner("Running"):
                st.session_state.lab_custom = testlab.run_custom(int(n), int(seed), crit)
        if st.session_state.get("lab_custom"):
            _show(st.session_state.lab_custom)
        else:
            st.caption("Generates a seeded synthetic queue and runs the same invariant checks as the scenarios.")

    with tabs[2]:
        st.write("Runs `python -m pytest` on the tests/ folder (merge sort, heap, scheduling, metrics, validation, audit, benchmark structure).")
        if st.button("Run pytest suite"):
            with st.spinner("Running pytest"):
                try:
                    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
                                          cwd=str(ROOT), capture_output=True, text=True, timeout=180)
                    st.session_state.pytest_out = (proc.returncode, proc.stdout + proc.stderr)
                except Exception as exc:
                    st.session_state.pytest_out = (-1, f"Could not run pytest: {exc}")
        out = st.session_state.get("pytest_out")
        if out:
            (st.success if out[0] == 0 else st.error)("pytest passed." if out[0] == 0 else "pytest reported problems.")
            st.code(out[1][-6000:] or "(no output)", language="text")
        else:
            empty_state("pytest has not been run", "Press Run pytest suite. You can also run it from a terminal.")

    with tabs[3]:
        st.write("Static scan of every file in algorithms/ for sorted(), .sort(), heapq, bisect, queue, min(), max() and similar shortcuts.")
        scan = scan_algorithms()
        bad = {k: v for k, v in scan.items() if v}
        if bad:
            st.error("Forbidden constructs found.")
            table([{"File": k, "Line": i["line"], "Issue": i["issue"]} for k, v in bad.items() for i in v])
        else:
            st.success(f"No forbidden constructs in {len(scan)} algorithm files.")
        table([{"File": k, "Issues": len(v), "Status": "clean" if not v else "violations"} for k, v in scan.items()])

    with tabs[4]:
        c1, c2 = st.columns(2)
        seed = c1.number_input("Seed to test", 0, 1_000_000, 42, step=1, key="repro_seed")
        n = c2.number_input("Patients", 1, 2000, 100, step=10, key="repro_n")
        a, b = generate_patients(int(n), int(seed)), generate_patients(int(n), int(seed))
        c = generate_patients(int(n), int(seed) + 1)
        (st.success if a == b else st.error)(f"Same seed twice gives identical data: {a == b}")
        (st.success if a != c else st.error)(f"Different seed gives different data: {a != c}")
    disclaimer()

from __future__ import annotations

from pathlib import Path

import streamlit as st

from algorithms.models import SEVERITY_ORDER, SEVERITY_SCORES
from . import state
from .components import disclaimer, section_header, table
from .content import ASSUMPTIONS, COMPLEXITY_BASIC, METRIC_DEFINITIONS

DOCS = Path(__file__).resolve().parent.parent / "docs"

ROLES = {
    "Student 1": ["Algorithm development", "Greedy scheduling", "Priority-score calculation", "Merge sort", "Complexity analysis",
                  "Algorithm correctness tests"],
    "Student 2": ["Data structures and performance", "Custom binary max-heap", "FCFS and shortest-treatment-time strategies",
                  "Benchmarking", "Performance metrics", "Stress and boundary tests"],
    "Student 3": ["Application and integration", "Streamlit UI", "Patient registration and queue management",
                  "Interactive visualizations", "CSV import/export", "Integration testing, documentation, deployment"],
}


def render() -> None:
    section_header("About the project", "Hospital Patient Priority Management System: a data structures and algorithms project.")
    state.show_flash()
    disclaimer()
    t = st.tabs(["Overview", "Scoring policy", "Metrics", "Team contributions", "Report and presentation"])

    with t[0]:
        st.markdown(
            "**Problem.** Prioritise patients arriving at an emergency department using severity, waiting time, age, medical priority "
            "and required treatment time, and compare scheduling strategies written from scratch.\n\n"
            "**Algorithms implemented by hand:** merge sort, a binary max-heap with priority update, greedy weighted-priority scheduling, "
            "FCFS and shortest-treatment-first. No `sorted`, `list.sort`, `heapq` or ready-made priority queue is used in the evaluated paths "
            "(verified by the Code audit on the Test Lab page).\n\n"
            "**Not clinical software.** The scoring formula is an educational policy, not a validated triage standard. Data are synthetic.")
        st.markdown("##### Assumptions")
        for a in ASSUMPTIONS:
            st.write(f"- {a}")
        st.markdown("##### Complexity summary")
        table(COMPLEXITY_BASIC)

    with t[1]:
        cfg = state.cfg()
        ws, wm, ww, wa = cfg.weights()
        st.markdown(
            "```\nscore = w_sev  x (severity_score / 4 x 100)\n      + w_med  x (medical_priority / 5 x 100)\n"
            "      + w_wait x (min(waiting, cap) / cap x 100)\n      + w_age  x age_band_score(age)\n```")
        table([{"Component": "Emergency severity", "Weight": f"{ws:.0%}"}, {"Component": "Medical priority", "Weight": f"{wm:.0%}"},
               {"Component": f"Waiting time (cap {cfg.wait_cap} min)", "Weight": f"{ww:.0%}"}, {"Component": "Age band", "Weight": f"{wa:.0%}"}])
        st.write("Severity scores: " + ", ".join(f"{s} = {SEVERITY_SCORES[s]}" for s in SEVERITY_ORDER) + ".")
        st.markdown("**Age-band mapping in use** (editable in the sidebar):")
        prev = 0
        rows = []
        for upper, score in cfg.age_bands:
            rows.append({"Ages": f"{prev} to {upper}", "Age-priority score": score})
            prev = upper + 1
        table(rows)
        st.write("Tie-breaks: higher score, then higher severity, then earlier arrival, then smaller patient ID. "
                 "The mapping is an educational choice (very young and older patients score higher) and is not medical guidance.")

    with t[2]:
        table(METRIC_DEFINITIONS)

    with t[3]:
        st.caption("Suggested allocation only. Enter your real names; this does not claim the work has been done by anyone.")
        for key in ROLES:
            st.session_state.team[key] = st.text_input(f"{key} name", st.session_state.team[key], key=f"team_{key}")
        table([{"Member": st.session_state.team[k], "Role": v[0], "Responsibilities": "; ".join(v[1:])} for k, v in ROLES.items()])

    with t[4]:
        files = [("REPORT_TEMPLATE.md", "Report template"), ("PRESENTATION_OUTLINE.md", "Presentation outline (8-10 slides)"),
                 ("DEMO_SCRIPT.md", "5-minute demo and screenshot guide"), ("REQUIREMENTS_CHECKLIST.md", "Requirement-to-file checklist")]
        for fname, title in files:
            path = DOCS / fname
            if path.exists():
                text = path.read_text(encoding="utf-8")
                with st.expander(title):
                    st.markdown(text)
                    st.download_button(f"Download {fname}", text, fname, "text/markdown", key=f"dl_{fname}")
            else:
                st.warning(f"{fname} is missing from docs/.")

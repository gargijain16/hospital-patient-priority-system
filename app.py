"""Hospital Patient Priority Management System - Streamlit entry point.

Educational DSA project. Synthetic data only; not for clinical use.
Run:  streamlit run app.py
"""
from pathlib import Path

import streamlit as st

from algorithms.models import DEFAULT_AGE_BANDS, ScoreConfig
from algorithms.scheduling_strategies import STRATEGY_LABELS, STRATEGY_ORDER
from ui import (page_about, page_benchmark, page_comparison, page_overview, page_queue, page_registration,
                page_testlab, page_trace, state)

st.set_page_config(page_title="Hospital Patient Priority Management", page_icon="🏥", layout="wide",
                   initial_sidebar_state="expanded")

ROOT = Path(__file__).resolve().parent
css_path = ROOT / "assets" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

state.init_state()

PAGES = {
    "Overview Dashboard": page_overview.render,
    "Patient Registration": page_registration.render,
    "Live Patient Queue": page_queue.render,
    "Algorithm Comparison": page_comparison.render,
    "Performance Benchmarking": page_benchmark.render,
    "Visualization & Algorithm Trace": page_trace.render,
    "Test Lab": page_testlab.render,
    "About the Project": page_about.render,
}

DEFAULTS = {"w_sev": 40, "w_med": 25, "w_wait": 20, "w_age": 15, "wait_cap": 120, "age_text": state.DEFAULT_AGE_TEXT}


def _reset_scoring() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def _parse_age_bands(text: str):
    bands = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [x.strip() for x in line.split(",")]
        if len(parts) != 2:
            raise ValueError(f"Line '{line}' must look like 'upper_age,score'.")
        bands.append((int(parts[0]), float(parts[1])))
    return tuple(bands)


def sidebar() -> str:
    sb = st.sidebar
    sb.markdown('<div class="brand">Hospital Patient Priority Management</div>'
                '<div class="brand-sub">Emergency department scheduling demo</div>', unsafe_allow_html=True)
    page = sb.radio("Navigate", list(PAGES), key="page", label_visibility="collapsed")
    sb.divider()
    current = st.session_state.strategy
    choice = sb.selectbox("Active scheduling strategy", STRATEGY_ORDER, index=STRATEGY_ORDER.index(current),
                          format_func=lambda k: STRATEGY_LABELS[k], key="strategy_widget")
    st.session_state.strategy = choice
    with sb.expander("Scoring policy (educational)"):
        for k, v in DEFAULTS.items():
            st.session_state.setdefault(k, v)
        st.caption("Weights are relative and normalised to 100%. Not a validated triage standard.")
        w1 = st.slider("Severity weight", 0, 100, key="w_sev")
        w2 = st.slider("Medical priority weight", 0, 100, key="w_med")
        w3 = st.slider("Waiting-time weight", 0, 100, key="w_wait")
        w4 = st.slider("Age-band weight", 0, 100, key="w_age")
        cap = st.number_input("Waiting-time cap (min)", 1, 10_000, key="wait_cap", step=10)
        text = st.text_area("Age bands: upper_age,score per line", key="age_text", height=170,
                            help="Inclusive upper age and a 0-100 score. Must be increasing and end at 120.")
        st.button("Reset scoring to defaults", on_click=_reset_scoring)
        try:
            bands = _parse_age_bands(text)
        except ValueError as exc:
            st.error(f"Age bands ignored: {exc}")
            bands = DEFAULT_AGE_BANDS
        cfg = ScoreConfig(float(w1), float(w2), float(w3), float(w4), int(cap), bands)
        errors = cfg.validate()
        if errors:
            for e in errors:
                st.error(e)
            cfg = ScoreConfig()
        st.session_state.cfg = cfg
    sb.caption(f"Simulated clock: minute {st.session_state.now}")
    sb.markdown('<div class="disclaimer">Academic demonstration with synthetic data. Not for clinical decisions.</div>',
                unsafe_allow_html=True)
    return page


PAGES[sidebar()]()

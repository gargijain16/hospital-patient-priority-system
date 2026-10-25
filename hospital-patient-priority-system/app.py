
"""Hospital Patient Priority Management System — Streamlit entry point.

Blue Floating UI redesign.
Educational DSA project. Synthetic data only; not for clinical use.
Run: streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from algorithms.models import DEFAULT_AGE_BANDS, ScoreConfig
from algorithms.scheduling_strategies import STRATEGY_LABELS, STRATEGY_ORDER
from ui import (
    page_about,
    page_benchmark,
    page_comparison,
    page_overview,
    page_queue,
    page_registration,
    page_testlab,
    page_trace,
    state,
)

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Hospital Patient Priority Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------
# BLUE FLOATING UI THEME
# ---------------------------------------------------------

css_path = ROOT / "assets" / "styles.css"

if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# These styles customize the application shell. Existing page
# components and algorithm implementations remain unchanged.

st.markdown(
    """
    <style>
    /* ---------- Global background and typography ---------- */

    .stApp {
        background:
            radial-gradient(
                ellipse at 8% 0%,
                rgba(59, 130, 246, 0.12),
                transparent 36%
            ),
            radial-gradient(
                ellipse at 95% 15%,
                rgba(96, 165, 250, 0.10),
                transparent 30%
            ),
            #f3f7fd;
        color: #142b4a;
    }

    html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
    }

    .block-container {
        max-width: 1600px;
        padding-top: 1.7rem;
        padding-bottom: 2.5rem;
    }

    /* ---------- Floating sidebar ---------- */

    section[data-testid="stSidebar"] {
        background: linear-gradient(
            175deg,
            #102c52 0%,
            #123c70 55%,
            #164b87 100%
        );
        border-right: 1px solid rgba(255, 255, 255, 0.12);
    }

    section[data-testid="stSidebar"] > div {
        padding: 1.2rem 0.85rem;
    }

    section[data-testid="stSidebar"] * {
        color: #edf5ff;
    }

    section[data-testid="stSidebar"] label {
        color: #e2edff;
    }

    .brand {
        font-size: 1.18rem;
        line-height: 1.45;
        font-weight: 800;
        color: #ffffff;
        padding: 1.15rem 1rem 0.35rem;
        letter-spacing: -0.35px;
    }

    .brand-sub {
        color: #b8d4f7;
        font-size: 0.78rem;
        line-height: 1.6;
        padding: 0 1rem 1.2rem;
    }

    .sidebar-logo {
        display: inline-flex;
        width: 48px;
        height: 48px;
        align-items: center;
        justify-content: center;
        border-radius: 15px;
        background: linear-gradient(135deg, #60a5fa, #2563eb);
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35);
        font-size: 1.55rem;
        margin: 0.2rem 1rem 0;
    }

    /* Sidebar radio navigation */

    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.3rem;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 0.65rem 0.75rem;
        border-radius: 12px;
        transition: background 0.2s ease;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.10);
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.16);
    }

    /* Sidebar form controls */

    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div,
    section[data-testid="stSidebar"] textarea {
        background: rgba(255, 255, 255, 0.10);
        border-color: rgba(255, 255, 255, 0.20);
        border-radius: 10px;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 13px;
        background: rgba(255, 255, 255, 0.055);
    }

    .disclaimer {
        margin-top: 1rem;
        padding: 0.85rem;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        color: #d7e9ff;
        font-size: 0.76rem;
        line-height: 1.6;
    }

    /* ---------- Floating application header ---------- */

    .floating-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
        padding: 1.15rem 1.4rem;
        background: rgba(255, 255, 255, 0.83);
        border: 1px solid rgba(191, 211, 239, 0.8);
        border-radius: 20px;
        box-shadow:
            0 12px 35px rgba(31, 67, 119, 0.075),
            inset 0 1px 0 rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
    }

    .header-eyebrow {
        font-size: 0.72rem;
        font-weight: 800;
        color: #2563eb;
        text-transform: uppercase;
        letter-spacing: 1.4px;
        margin-bottom: 0.35rem;
    }

    .header-title {
        font-size: clamp(1.3rem, 2.3vw, 1.85rem);
        font-weight: 800;
        line-height: 1.3;
        color: #102b50;
        letter-spacing: -0.7px;
        margin: 0;
    }

    .header-subtitle {
        margin-top: 0.35rem;
        color: #61738c;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .header-status {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.65rem 0.9rem;
        border-radius: 999px;
        background: #eff6ff;
        border: 1px solid #d6e7ff;
        color: #1d4ed8;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #3b82f6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
    }

    /* ---------- General cards and metrics ---------- */

    div[data-testid="stMetric"] {
        padding: 1rem 1.1rem;
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid #dce8f7;
        border-radius: 17px;
        box-shadow: 0 8px 24px rgba(30, 64, 115, 0.06);
        transition:
            transform 0.2s ease,
            box-shadow 0.2s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 30px rgba(37, 99, 235, 0.11);
    }

    div[data-testid="stMetricLabel"] {
        color: #61738c;
    }

    div[data-testid="stMetricValue"] {
        color: #163b70;
        font-weight: 800;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #dce8f7;
        border-radius: 16px;
    }

    /* ---------- Buttons ---------- */

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 11px;
        border: 1px solid #2563eb;
        background: linear-gradient(135deg, #3478f6, #1d4ed8);
        color: #ffffff;
        font-weight: 700;
        padding: 0.52rem 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 5px 14px rgba(37, 99, 235, 0.15);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        color: #ffffff;
        border-color: #1d4ed8;
        transform: translateY(-2px);
        box-shadow: 0 9px 20px rgba(37, 99, 235, 0.24);
    }

    .stButton > button:active,
    .stDownloadButton > button:active {
        transform: translateY(0);
    }

    /* ---------- Inputs and data tables ---------- */

    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div,
    [data-baseweb="textarea"] > div {
        border-radius: 10px;
    }

    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="textarea"] > div:focus-within {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        border: 1px solid #dce8f7;
        border-radius: 14px;
        overflow: hidden;
    }

    /* ---------- Tabs, alerts, expanders ---------- */

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.45rem;
        border-bottom-color: #dce8f7;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 0.65rem 1rem;
    }

    .stTabs [aria-selected="true"] {
        color: #1d4ed8;
    }

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    div[data-testid="stExpander"] {
        border-color: #dce8f7;
        border-radius: 13px;
        overflow: hidden;
    }

    /* ---------- Responsive behavior ---------- */

    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.85rem 2rem;
        }

        .floating-header {
            padding: 1rem;
            border-radius: 15px;
        }

        .header-status {
            white-space: normal;
        }
    }

    /* Respect reduced-motion accessibility preferences. */

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# APPLICATION STATE
# ---------------------------------------------------------

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

DEFAULTS = {
    "w_sev": 40,
    "w_med": 25,
    "w_wait": 20,
    "w_age": 15,
    "wait_cap": 120,
    "age_text": state.DEFAULT_AGE_TEXT,
}


def _reset_scoring() -> None:
    """Reset the educational scoring configuration."""
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def _parse_age_bands(text: str):
    """Parse age-band configuration from upper_age,score lines."""
    bands = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = [part.strip() for part in line.split(",")]

        if len(parts) != 2:
            raise ValueError(
                f"Line '{line}' must look like 'upper_age,score'."
            )

        bands.append((int(parts[0]), float(parts[1])))

    return tuple(bands)


def sidebar() -> str:
    """Render sidebar navigation and scoring controls."""
    sb = st.sidebar

    sb.markdown(
        '<div class="sidebar-logo">🏥</div>'
        '<div class="brand">Hospital Priority</div>'
        '<div class="brand-sub">'
        'Patient scheduling and algorithm analytics'
        '</div>',
        unsafe_allow_html=True,
    )

    sb.markdown("### WORKSPACE")

    page = sb.radio(
        "Navigate",
        list(PAGES),
        key="page",
        label_visibility="collapsed",
    )

    sb.divider()

    current = st.session_state.strategy

    choice = sb.selectbox(
        "Active scheduling strategy",
        STRATEGY_ORDER,
        index=STRATEGY_ORDER.index(current),
        format_func=lambda key: STRATEGY_LABELS[key],
        key="strategy_widget",
    )

    st.session_state.strategy = choice

    with sb.expander("⚙️ Scoring policy", expanded=False):
        for key, value in DEFAULTS.items():
            st.session_state.setdefault(key, value)

        sb_caption = (
            "Educational scoring only. Weights are normalized "
            "to 100%; this is not a validated clinical triage standard."
        )
        st.caption(sb_caption)

        w1 = st.slider("Severity weight", 0, 100, key="w_sev")
        w2 = st.slider("Medical priority weight", 0, 100, key="w_med")
        w3 = st.slider("Waiting-time weight", 0, 100, key="w_wait")
        w4 = st.slider("Age-band weight", 0, 100, key="w_age")

        st.number_input(
            "Waiting-time cap (min)",
            min_value=1,
            max_value=10_000,
            key="wait_cap",
            step=10,
        )

        age_text = st.text_area(
            "Age bands: upper_age,score per line",
            key="age_text",
            height=140,
            help=(
                "Enter inclusive upper ages and scores from 0 to 100. "
                "Bands should increase and end at age 120."
            ),
        )

        st.button(
            "Reset scoring defaults",
            on_click=_reset_scoring,
            use_container_width=True,
        )

        try:
            bands = _parse_age_bands(age_text)
        except (ValueError, TypeError) as exc:
            st.error(f"Age bands ignored: {exc}")
            bands = DEFAULT_AGE_BANDS

        config = ScoreConfig(
            float(w1),
            float(w2),
            float(w3),
            float(w4),
            int(st.session_state.wait_cap),
            bands,
        )

        errors = config.validate()

        if errors:
            for error in errors:
                st.error(error)

            config = ScoreConfig()

        st.session_state.cfg = config

    sb.divider()

    sb.markdown(
        f"""
        <div style="
            padding: 0.8rem 0.9rem;
            border-radius: 12px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.13);
        ">
            <div style="
                color: #a9c8f3;
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            ">Simulation clock</div>
            <div style="
                color: #ffffff;
                font-size: 1.3rem;
                font-weight: 800;
                margin-top: 0.2rem;
            ">Minute {st.session_state.now}</div>
        </div>
        <div class="disclaimer">
            Academic demonstration using synthetic data only.
            Not for real clinical decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    return page


# ---------------------------------------------------------
# FLOATING TOP HEADER
# ---------------------------------------------------------

PAGE_DESCRIPTIONS = {
    "Overview Dashboard": "A live overview of emergency department activity.",
    "Patient Registration": "Register synthetic patients and configure their details.",
    "Live Patient Queue": "Inspect the queue and manage patient scheduling.",
    "Algorithm Comparison": "Compare scheduling strategies using the same dataset.",
    "Performance Benchmarking": "Measure actual execution time across input sizes.",
    "Visualization & Algorithm Trace": "Explore sorting steps and priority-heap operations.",
    "Test Lab": "Validate algorithms with normal, boundary, and stress cases.",
    "About the Project": "Project objectives, design decisions, and complexity analysis.",
}


def render_header(page_name: str) -> None:
    """Render the floating application header."""
    description = PAGE_DESCRIPTIONS.get(
        page_name,
        "Hospital patient scheduling and algorithm analytics.",
    )

    st.markdown(
        f"""
        <div class="floating-header">
            <div>
                <div class="header-eyebrow">
                    HOSPITAL OPERATIONS / DSA LAB
                </div>
                <div class="header-title">
                    {page_name}
                </div>
                <div class="header-subtitle">
                    {description}
                </div>
            </div>
            <div class="header-status">
                <span class="status-dot"></span>
                Educational simulation
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# RENDER SELECTED PAGE
# ---------------------------------------------------------

selected_page = sidebar()
render_header(selected_page)
PAGES[selected_page]()

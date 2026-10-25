"""Small reusable UI building blocks and compatibility wrappers."""
from __future__ import annotations

import html
from typing import Dict, List, Optional, Sequence

import streamlit as st


def plot(fig, key: Optional[str] = None) -> None:
    """Full-width Plotly chart that works across Streamlit versions."""
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, key=key)


def table(rows: Sequence[Dict], height: Optional[int] = None) -> None:
    """Compact read-only table from a list of dicts."""
    data = list(rows)
    kw = {"hide_index": True}
    if height:
        kw["height"] = height
    try:
        st.dataframe(data, width="stretch", **kw)
    except Exception:
        st.dataframe(data, use_container_width=True, **kw)


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="page-title">{html.escape(title)}</div>'
                f'<div class="page-sub">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


def kpi(label: str, value, sub: str = "", tone: str = "") -> None:
    cls = f"kpi kpi-{tone}" if tone else "kpi"
    st.markdown(f'<div class="{cls}"><div class="kpi-label">{html.escape(str(label))}</div>'
                f'<div class="kpi-value">{html.escape(str(value))}</div>'
                f'<div class="kpi-sub">{html.escape(str(sub))}</div></div>', unsafe_allow_html=True)


def kpi_row(items: Sequence[tuple]) -> None:
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            kpi(*item)
    st.write("")


def callout(text: str, kind: str = "info") -> None:
    st.markdown(f'<div class="callout callout-{kind}">{text}</div>', unsafe_allow_html=True)


def empty_state(title: str, hint: str) -> None:
    st.markdown(f'<div class="callout callout-empty"><b>{html.escape(title)}</b><br>{html.escape(hint)}</div>',
                unsafe_allow_html=True)


def disclaimer() -> None:
    st.markdown('<div class="disclaimer"><b>Academic demonstration only.</b> Synthetic data, an educational scoring '
                'formula and a simulated clock. Not validated triage, and not for real clinical decisions.</div>',
                unsafe_allow_html=True)


def one_line(rows: List[Dict], keys: Sequence[str]) -> List[Dict]:
    return [{k: r[k] for k in keys} for r in rows]


def fmt(x, digits: int = 1) -> str:
    return "n/a" if x is None else f"{x:.{digits}f}"

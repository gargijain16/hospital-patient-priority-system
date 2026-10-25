"""Plotly figures. Every function receives real data from the live session or a benchmark run."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import plotly.graph_objects as go

from algorithms.models import SEVERITY_ORDER

NAVY, TEAL, BLUE, GREY = "#0B1F3A", "#0F766E", "#2563EB", "#94A3B8"
SEV_COLORS = {"Critical": "#C62828", "High": "#EF6C00", "Moderate": "#F9A825", "Low": "#2E7D32"}
STRATEGY_COLORS = {"greedy": TEAL, "heap": BLUE, "fcfs": "#64748B", "stf": "#B45309"}
COMPONENT_COLORS = {"severity_pts": "#C62828", "medical_pts": BLUE, "waiting_pts": TEAL, "age_pts": "#7C3AED"}
COMPONENT_NAMES = {"severity_pts": "Severity", "medical_pts": "Medical priority", "waiting_pts": "Waiting time", "age_pts": "Age band"}


def _style(fig: go.Figure, title: Optional[str] = None, height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=15, color=NAVY)) if title else None,
        height=height, margin=dict(l=10, r=10, t=50 if title else 16, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", color=NAVY, size=12),
        legend=dict(orientation="h", y=-0.22), hovermode="closest")
    fig.update_xaxes(gridcolor="#E5E9F0", zeroline=False, linecolor="#CBD5E1")
    fig.update_yaxes(gridcolor="#E5E9F0", zeroline=False, linecolor="#CBD5E1")
    return fig


def empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14, color="#64748B"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _style(fig, height=240)


def priority_ranking_bar(rows: Sequence[Dict], title: str = "Priority ranking (highest score first)") -> go.Figure:
    """rows: dicts with patient (Patient), total (score), in rank order."""
    if not rows:
        return empty_figure("No waiting patients to rank.")
    fig = go.Figure(go.Bar(
        x=[r["patient"].patient_id for r in rows], y=[r["total"] for r in rows],
        marker_color=[SEV_COLORS[r["patient"].severity] for r in rows],
        customdata=[[r["patient"].severity, r["waiting_minutes"], r["patient"].age] for r in rows],
        hovertemplate="%{x}<br>Score %{y:.2f}<br>%{customdata[0]}, age %{customdata[2]}<br>waiting %{customdata[1]} min<extra></extra>"))
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=[r["patient"].patient_id for r in rows])
    fig.update_yaxes(title="Priority score (0-100)", range=[0, 100])
    return _style(fig, title)


def component_breakdown(rows: Sequence[Dict], title: str = "Priority-score components") -> go.Figure:
    if not rows:
        return empty_figure("No waiting patients to explain.")
    ids = [r["patient"].patient_id for r in rows]
    fig = go.Figure()
    for key, name in COMPONENT_NAMES.items():
        fig.add_bar(x=ids, y=[r[key] for r in rows], name=name, marker_color=COMPONENT_COLORS[key])
    fig.update_layout(barmode="stack")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ids)
    fig.update_yaxes(title="Points toward final score")
    return _style(fig, title)


def severity_distribution_bar(counts: Dict[str, int], title: str = "Emergency severity distribution") -> go.Figure:
    fig = go.Figure(go.Bar(x=list(SEVERITY_ORDER), y=[counts.get(s, 0) for s in SEVERITY_ORDER],
                           marker_color=[SEV_COLORS[s] for s in SEVERITY_ORDER], text=[counts.get(s, 0) for s in SEVERITY_ORDER],
                           textposition="outside"))
    fig.update_yaxes(title="Patients")
    return _style(fig, title, height=320)


def queue_position_comparison(results: Dict[str, object], labels: Dict[str, str], max_patients: int = 40) -> go.Figure:
    """Grouped bars of the service position of each patient (listed in arrival order) per strategy."""
    first = next(iter(results.values()))
    ids = []
    arrivals = sorted_by_arrival(first)
    for e in arrivals[:max_patients]:
        ids.append(e.patient.patient_id)
    fig = go.Figure()
    for s, res in results.items():
        pos = {e.patient.patient_id: e.position for e in res.entries}
        fig.add_bar(x=ids, y=[pos[i] for i in ids], name=labels[s], marker_color=STRATEGY_COLORS[s])
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ids, title="Patient (arrival order)")
    fig.update_yaxes(title="Service position (1 = first)")
    return _style(fig, "Queue position by strategy", height=400)


def sorted_by_arrival(result) -> list:
    """Entries ordered by arrival using the project's own merge sort (no built-in sort)."""
    from algorithms.merge_sort import merge_sort
    return merge_sort(list(result.entries), lambda a, b: (a.patient.arrival_time, a.patient.patient_id) < (b.patient.arrival_time, b.patient.patient_id))


def wait_comparison_bar(metrics: Dict[str, Dict], labels: Dict[str, str]) -> go.Figure:
    keys = list(metrics.keys())
    fig = go.Figure()
    fig.add_bar(x=[labels[k] for k in keys], y=[metrics[k]["avg_wait"] for k in keys], name="Average wait", marker_color=TEAL)
    fig.add_bar(x=[labels[k] for k in keys], y=[metrics[k]["max_wait"] for k in keys], name="Maximum wait", marker_color=GREY)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Waiting time (simulated minutes)")
    return _style(fig, "Waiting time by strategy", height=360)


def wait_vs_treatment_scatter(result, title: str) -> go.Figure:
    fig = go.Figure()
    for sev in SEVERITY_ORDER:
        es = [e for e in result.entries if e.patient.severity == sev]
        if es:
            fig.add_scatter(x=[e.treatment for e in es], y=[e.wait for e in es], mode="markers", name=sev,
                            marker=dict(size=11, color=SEV_COLORS[sev], line=dict(width=1, color="white")),
                            text=[e.patient.patient_id for e in es],
                            hovertemplate="%{text}<br>treatment %{x} min<br>waited %{y} min<extra></extra>")
    fig.update_xaxes(title="Required treatment time (min)")
    fig.update_yaxes(title="Waiting before treatment (min)")
    return _style(fig, title, height=360)


def benchmark_line(rows: Sequence[Dict], log_scale: bool = False) -> go.Figure:
    names: List[str] = []
    for r in rows:
        if r["median_ms"] is not None and r["algorithm"] not in names:
            names.append(r["algorithm"])
    if not names:
        return empty_figure("No measured timings yet.")
    fig = go.Figure()
    palette = [TEAL, BLUE, "#7C3AED", "#64748B", "#B45309"]
    for i, name in enumerate(names):
        pts = [r for r in rows if r["algorithm"] == name and r["median_ms"] is not None]
        fig.add_scatter(x=[r["n"] for r in pts], y=[r["median_ms"] for r in pts], mode="lines+markers", name=name,
                        line=dict(color=palette[i % len(palette)], width=2.5), marker=dict(size=8),
                        hovertemplate="n=%{x}<br>%{y:.3f} ms (median)<extra>" + name + "</extra>")
    if log_scale:
        fig.update_xaxes(type="log")
        fig.update_yaxes(type="log")
    fig.update_xaxes(title="Input size n (patients)")
    fig.update_yaxes(title="Median execution time (ms)")
    return _style(fig, "Measured execution time vs input size" + (" (log-log)" if log_scale else ""), height=420)


def merge_steps_figure(steps: Sequence[Dict], n_items: int) -> go.Figure:
    merges = [s for s in steps if s["type"] == "merge"]
    if not merges:
        return empty_figure("Select at least two patients to see merge steps.")
    depth_max = 0
    for s in merges:
        depth_max = s["depth"] if s["depth"] > depth_max else depth_max
    palette = [TEAL, BLUE, "#7C3AED", "#B45309", "#64748B", "#0E7490"]
    fig = go.Figure()
    for k, s in enumerate(merges):
        xs = [s["offset"] + j for j in range(len(s["merged"]))]
        fig.add_scatter(x=xs, y=[-k] * len(xs), mode="markers+text", showlegend=False,
                        text=[m.split(" [")[0] for m in s["merged"]], textposition="middle center",
                        textfont=dict(color="white", size=10),
                        marker=dict(symbol="square", size=40, color=palette[s["depth"] % len(palette)]),
                        hovertext=s["merged"], hoverinfo="text")
    fig.update_yaxes(tickmode="array", tickvals=[-k for k in range(len(merges))],
                     ticktext=[f"merge {k + 1} (depth {s['depth']})" for k, s in enumerate(merges)], zeroline=False)
    fig.update_xaxes(title="Position in the array", range=[-0.8, n_items - 0.2], dtick=1)
    return _style(fig, "Each row is one merge; colours show recursion depth", height=120 + 52 * len(merges))


def heap_tree_figure(array: Sequence[tuple], severities: Dict[str, str], highlight: Sequence[str] = (),
                     max_nodes: int = 31) -> go.Figure:
    """array: [(id, score)] in heap-array order."""
    nodes = list(array)[:max_nodes]
    if not nodes:
        return empty_figure("The heap is empty.")
    pos = []
    for i in range(len(nodes)):
        level = (i + 1).bit_length() - 1
        pos.append(((i + 1 - 2 ** level + 0.5) / 2 ** level, -level))
    ex, ey = [], []
    for i in range(1, len(nodes)):
        p = (i - 1) // 2
        ex += [pos[p][0], pos[i][0], None]
        ey += [pos[p][1], pos[i][1], None]
    fig = go.Figure()
    fig.add_scatter(x=ex, y=ey, mode="lines", line=dict(color="#CBD5E1", width=2), hoverinfo="skip", showlegend=False)
    colors = [SEV_COLORS.get(severities.get(n[0], "Low"), GREY) for n in nodes]
    fig.add_scatter(x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers+text", showlegend=False,
                    text=[f"{n[0]}<br>{n[1]:.1f}" for n in nodes], textposition="middle center",
                    textfont=dict(color="white", size=9),
                    marker=dict(size=52, color=colors,
                                line=dict(width=[4 if n[0] in highlight else 1 for n in nodes], color=NAVY)),
                    hovertext=[f"index {i}: {n[0]} score {n[1]:.2f}" for i, n in enumerate(nodes)], hoverinfo="text")
    fig.update_xaxes(visible=False, range=[-0.05, 1.05])
    fig.update_yaxes(visible=False)
    levels = (len(nodes)).bit_length()
    note = " (first 31 nodes shown)" if len(array) > max_nodes else ""
    return _style(fig, "Binary max-heap tree" + note, height=150 + 120 * levels)


def gantt_figure(result, title: str, max_rows: int = 40) -> go.Figure:
    es = result.entries[:max_rows]
    if not es:
        return empty_figure("No schedule to draw.")
    ids = [e.patient.patient_id for e in es]
    fig = go.Figure()
    fig.add_bar(y=ids, x=[e.wait for e in es], base=[e.patient.arrival_time for e in es], orientation="h",
                name="Waiting", marker_color="#CBD5E1", hovertemplate="%{y} waited %{x} min<extra></extra>")
    for sev in SEVERITY_ORDER:
        sub = [e for e in es if e.patient.severity == sev]
        if sub:
            fig.add_bar(y=[e.patient.patient_id for e in sub], x=[e.treatment for e in sub], base=[e.start for e in sub],
                        orientation="h", name=f"Treatment - {sev}", marker_color=SEV_COLORS[sev],
                        hovertemplate="%{y} treated %{x} min<extra></extra>")
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(type="category", categoryorder="array", categoryarray=ids, autorange="reversed")
    fig.update_xaxes(title="Simulated minute")
    return _style(fig, title, height=160 + 22 * len(es))


def score_over_time_figure(curves: Dict[str, tuple], title: str) -> go.Figure:
    fig = go.Figure()
    palette = [TEAL, "#B45309", BLUE]
    for i, (name, (xs, ys)) in enumerate(curves.items()):
        fig.add_scatter(x=xs, y=ys, mode="lines", name=name, line=dict(width=3, color=palette[i % 3]))
    fig.update_xaxes(title="Minutes waited")
    fig.update_yaxes(title="Priority score")
    return _style(fig, title, height=340)

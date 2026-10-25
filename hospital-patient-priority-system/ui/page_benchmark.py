from __future__ import annotations

import streamlit as st

from utils import charts
from utils.benchmark import ALGORITHMS, MAX_SIZE, run_benchmark
from . import state
from .components import callout, disclaimer, empty_state, plot, section_header, table

PRESETS = [10, 100, 1000, 5000, 10000]


def _parse_sizes(text: str):
    sizes, errs = [], []
    for part in text.replace(";", ",").split(","):
        part = part.strip().replace("_", "")
        if not part:
            continue
        try:
            v = int(part)
        except ValueError:
            errs.append(f"'{part}' is not a whole number.")
            continue
        if v < 1 or v > MAX_SIZE:
            errs.append(f"{v} is outside 1 to {MAX_SIZE}.")
        elif v not in sizes:
            sizes.append(v)
    return sizes, errs


def _growth_text(rows):
    """Observed vs theoretical growth ratios between consecutive sizes (computed from the measurements)."""
    import math
    lines = []
    for key, label, tcx, _ in ALGORITHMS:
        pts = [r for r in rows if r["key"] == key and r["median_ms"] is not None]
        if len(pts) < 2:
            continue
        a, b = pts[-2], pts[-1]
        if a["median_ms"] <= 0:
            continue
        obs = b["median_ms"] / a["median_ms"]
        ratio_n = b["n"] / a["n"]
        theo = ratio_n ** 2 if "n^2" in tcx else (b["n"] * math.log2(max(b["n"], 2))) / (a["n"] * math.log2(max(a["n"], 2)))
        lines.append(f"- **{label}**: n grew {ratio_n:.1f}x ({a['n']} to {b['n']}); measured time grew {obs:.1f}x; "
                     f"a pure {tcx} model predicts about {theo:.1f}x.")
    return lines


def render() -> None:
    section_header("Performance benchmarking",
                   "Real execution times measured with time.perf_counter on this machine. Nothing here is pre-computed.")
    state.show_flash()
    c1, c2 = st.columns([2, 1])
    size_text = c1.text_input("Input sizes (comma separated)", "10, 100, 1000, 5000, 10000",
                              help=f"Whole numbers from 1 to {MAX_SIZE}.")
    repeats = c2.number_input("Repeats per measurement", 1, 25, 5, step=1, help="The median of these runs is reported.")
    c3, c4 = st.columns(2)
    seed = c3.number_input("Dataset seed", 0, 1_000_000, 42, step=1)
    cap = c4.number_input("Skip O(n^2) greedy selection above n =", 10, 20000, 2000, step=100,
                          help="Quadratic selection is slow in Python; larger inputs are skipped and marked as such.")
    sizes, errs = _parse_sizes(size_text)
    for e in errs:
        st.error(e)
    run = st.button("Run benchmark", type="primary", disabled=bool(errs) or not sizes)
    if run:
        bar = st.progress(0.0, text="Starting")
        try:
            result = run_benchmark(sizes, int(repeats), int(seed), int(cap), state.cfg(),
                                   progress=lambda f, msg: bar.progress(min(f, 1.0), text=msg))
            st.session_state.bench = result
        except Exception as exc:
            st.error(f"Benchmark failed: {exc}")
        bar.empty()

    res = st.session_state.bench
    if not res:
        empty_state("No benchmark has been run yet", "Choose sizes and press Run benchmark. Results stay here while you browse other pages.")
        _notes()
        disclaimer()
        return

    rows, ver = res["rows"], res["verification"]
    failed = [v for v in ver if not v["passed"]]
    if failed:
        st.error(f"{len(failed)} verification check(s) failed; timings for those sizes were withheld.")
    else:
        st.success(f"All {len(ver)} correctness checks passed before timing (no patient lost or duplicated; "
                   "merge sort, heap and greedy selection agree on the order).")
    p = res["params"]
    st.caption(f"Sizes {p['sizes']}, {p['repeats']} repeat(s) each, seed {p['seed']}. Median of repeats is shown.")

    st.markdown("##### Median execution time (ms)")
    wide = []
    for n in p["sizes"]:
        row = {"n": n}
        for r in rows:
            if r["n"] == n:
                row[r["algorithm"]] = round(r["median_ms"], 4) if r["median_ms"] is not None else r["status"]
        wide.append(row)
    table(wide)
    with st.expander("Full results with minimum, maximum and complexity"):
        table([{"n": r["n"], "Algorithm": r["algorithm"], "Median ms": None if r["median_ms"] is None else round(r["median_ms"], 4),
                "Min ms": None if r["min_ms"] is None else round(r["min_ms"], 4),
                "Max ms": None if r["max_ms"] is None else round(r["max_ms"], 4), "Runs": r["runs"],
                "Time complexity": r["time_complexity"], "Auxiliary space": r["space_complexity"], "Status": r["status"]}
               for r in rows])
    log = st.toggle("Log-log axes", value=False)
    plot(charts.benchmark_line(rows, log), key=f"bench_line_{log}")

    st.markdown("##### Interpretation computed from your run")
    lines = _growth_text(rows)
    if lines:
        st.markdown("\n".join(lines))
    else:
        st.write("Run at least two sizes to compare growth.")
    callout("These timings show how this implementation behaved on this machine in this run. They are consistent with, but do not "
            "prove, the theoretical complexities. Measured growth also reflects Python overhead, memory effects and noise.")
    with st.expander("Verification details"):
        table([{"n": v["n"], "Algorithm": v["algorithm"], "Check": v["check"], "Result": "PASS" if v["passed"] else "FAIL"} for v in ver])
    _notes(res["environment"])
    disclaimer()


def _notes(env=None):
    with st.expander("Method, environment and limitations", expanded=env is None):
        st.markdown(
            "- Datasets are generated **before** the timer starts; only the ordering call is timed. UI, charts, CSV and random-data generation are excluded.\n"
            "- Every algorithm receives the identical dataset and the same scoring and tie-break rules; outputs are verified before timings are trusted.\n"
            "- Priority algorithms include computing each score (O(n)). FCFS and shortest-treatment-first sort by a stored field.\n"
            "- For very small n the work finishes in microseconds, so timer resolution and call overhead dominate and results are noisy.\n"
            "- Timings are not simulated hospital minutes. Waiting time, treatment time and turnaround are unrelated to execution time.")
        if env:
            table([{"Item": k, "Value": v} for k, v in env.items()])

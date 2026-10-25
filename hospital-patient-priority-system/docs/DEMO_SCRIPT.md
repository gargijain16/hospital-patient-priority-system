# 5-minute live demo and screenshot guide

Start the app (`streamlit run app.py`) and keep the default demonstration dataset (24 patients, clock at minute 60).

| Time | Do this | Say |
|---|---|---|
| 0:00 | Overview Dashboard | This simulates an ED queue with synthetic data; the disclaimer is on every page. |
| 0:40 | Live Patient Queue; open *Score breakdown* | Every position is explained by four weighted components. Read the "Why this order?" box. |
| 1:20 | Click **Start treatment**, then **Complete treatment**, then **Advance 15 min** | Waiting time grows with the clock; treatment time is separate. |
| 2:00 | Sidebar: change strategy to FCFS, then Shortest treatment first | The same patients are ordered differently. |
| 2:30 | Algorithm Comparison; tab *Trade-offs* | Critical patient arriving last, and a long patient bypassed by STF. |
| 3:30 | Visualization & Algorithm Trace; heap slider | Each insert/extract and the swaps; merge steps. |
| 4:15 | Performance Benchmarking; run 10, 100, 1000, 5000 | Real timings, verified first; greedy selection is quadratic. |
| 4:45 | Test Lab; run all scenarios | Pass/fail results and the code audit. |

## Screenshots to capture (from your own run)
1. Overview Dashboard.
2. Live Patient Queue with the score breakdown tab.
3. Algorithm Comparison metrics table and queue-position chart.
4. A trade-off case (critical last or STF starvation).
5. Merge-sort trace and heap tree at one step.
6. Benchmark table and line chart (note your Python version and CPU shown in the environment table).
7. Test Lab all-pass result and pytest output.

Do not edit or invent numbers; capture what the app shows on your machine.

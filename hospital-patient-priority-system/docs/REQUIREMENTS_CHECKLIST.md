# Requirement checklist

| # | Requirement | Where it is satisfied |
|---|---|---|
| 1 | Streamlit + Python, GitHub, Streamlit Cloud | `app.py`, `requirements.txt`, README deployment steps |
| 2 | Plotly charts, stdlib data tools, custom CSS, pytest | `utils/charts.py`, `assets/styles.css`, `tests/` |
| 3 | Professional UI, sidebar navigation, 8 pages | `app.py` (PAGES), `ui/page_*.py`, `assets/styles.css`, `.streamlit/config.toml` |
| 4 | Patient data model, waiting time vs arrival vs treatment | `algorithms/models.py` (`Patient.waiting_time`), `ui/state.py` |
| 5A | Greedy weighted score, configurable cap/age bands, tie-breaks, explanation | `algorithms/greedy_scheduler.py`; sidebar in `app.py`; *Live Patient Queue → Score breakdown* |
| 5B | Merge sort from scratch with trace and complexity | `algorithms/merge_sort.py`; *Trace → Merge sort trace*; *Comparison → Complexity analysis* |
| 5C | Binary max-heap: insert, peek, extract, update, array/tree view | `algorithms/max_heap.py`; *Trace → Binary heap trace* |
| 5D | Greedy, FCFS, STF on the same dataset | `algorithms/scheduling_strategies.py`; *Algorithm Comparison → Strategy comparison* |
| 5E | Non-optimal cases and trade-offs | `utils/scenarios.py`; *Algorithm Comparison → Trade-offs* |
| 6 | Add/edit/remove, generate, CSV in/out, strategy, clock, start/complete, reset, session state | `ui/page_registration.py`, `ui/page_queue.py`, `ui/state.py` |
| 7 | Metrics (wait, turnaround, throughput, fairness, ...) with definitions | `algorithms/metrics.py`; `ui/content.py` (definitions); *About → Metrics* |
| 8 | Real benchmarking with perf_counter, medians, verification | `utils/benchmark.py`; *Performance Benchmarking* |
| 9 | Complexity analysis page | *Algorithm Comparison → Complexity analysis*; `ui/content.py` |
| 10 | Ten visualizations | `utils/charts.py`: ranking bar, queue positions, average wait, scatter, severity distribution, benchmark line, merge steps, heap tree, Gantt, component breakdown |
| 11 | Test Lab with normal/boundary/large/adversarial and unit tests | `utils/testlab.py`, `ui/page_testlab.py`, `tests/`, `utils/audit.py` |
| 12 | Synthetic dataset, sample CSV, validation, disclaimer | `utils/sample_data.py`, `data/sample_patients.csv`, `utils/validation.py`, `ui/components.py` (disclaimer) |
| 13 | Three-student division (editable) | *About → Team contributions*, `ui/page_about.py` |
| 14 | Report template, presentation outline, demo workflow, screenshots guide | `docs/REPORT_TEMPLATE.md`, `docs/PRESENTATION_OUTLINE.md`, `docs/DEMO_SCRIPT.md` |
| 15 | Modular structure | see README project structure |
| 16 | Quality (no fake values, no built-in sorts, graceful errors) | `utils/audit.py` + `tests/test_validation_and_audit.py`; benchmark computed live |
| 17 | Install, run, test, GitHub, deploy, troubleshooting, checklist | `README.md`, this file |

# Hospital Patient Priority Management System

A Streamlit application for a university Data Structures and Algorithms project. It prioritises synthetic emergency-department
patients with algorithms written from scratch (merge sort, binary max-heap, greedy weighted-priority scheduling, FCFS and
shortest-treatment-first), compares them, visualises them step by step and benchmarks them with real timings.

> **Academic demonstration only.** All data are synthetic. The scoring formula is an educational policy, not a validated
> triage standard. Do not use it for real clinical decisions, and do not enter real personal data.

## Features

| Page | What it does |
|---|---|
| Overview Dashboard | Live KPIs, severity distribution, top priority ranking, next-patient explanation, history metrics |
| Patient Registration | Validated add form, edit/remove, seeded synthetic generator, CSV import/export, reset |
| Live Patient Queue | Strategy-ordered queue, simulated clock, start/complete treatment, score breakdown, results CSV |
| Algorithm Comparison | Same dataset through four strategies, metrics table, charts, trade-off cases, complexity tables |
| Performance Benchmarking | Real `time.perf_counter` timings, medians, verification, log-log chart, computed interpretation |
| Visualization & Algorithm Trace | Merge-sort steps, heap tree stepper, greedy decision log, score components, Gantt timeline |
| Test Lab | 19 scenarios (normal, boundary, large, adversarial), custom dataset, pytest runner, code audit |
| About the Project | Scoring policy, metric definitions, editable team table, report/presentation documents |

## Project structure

```
hospital-patient-priority-system/
├── app.py                         # Streamlit entry point (navigation, sidebar, scoring settings)
├── algorithms/                    # algorithm code only, no Streamlit imports
│   ├── models.py                  # Patient, ScoreConfig, constants
│   ├── greedy_scheduler.py        # priority score, tie-breaks, greedy_select, explanations
│   ├── merge_sort.py              # merge sort + trace + patient criteria
│   ├── max_heap.py                # binary max-heap with update_priority
│   ├── scheduling_strategies.py   # simulate(): greedy / heap / FCFS / STF + snapshot orderings
│   └── metrics.py                 # waiting, turnaround, throughput, fairness, inversions
├── ui/                            # Streamlit pages and shared components
├── utils/                         # validation, sample data, scenarios, benchmark engine, charts, test lab, audit
├── data/sample_patients.csv       # 24 synthetic patients
├── tests/                         # pytest suite (39 tests)
├── docs/                          # report template, presentation outline, demo script, requirements checklist
├── assets/styles.css              # design system
├── .streamlit/config.toml         # light theme
├── requirements.txt  pytest.ini  .gitignore  README.md
```

## Install and run locally

Python 3.10 or newer (developed on 3.12).

```bash
cd hospital-patient-priority-system
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501. No API keys, no backend, no absolute paths.

## Run the automated tests

```bash
python -m pytest -q
```

The same suite can be run from the **Test Lab → Unit tests** tab. The Test Lab also runs 19 live scenarios and a static
audit that confirms no `sorted`, `.sort`, `heapq`, `bisect`, `queue`, `min` or `max` appears in `algorithms/`.

## Upload to GitHub

```bash
git init
git add .
git commit -m "Hospital Patient Priority Management System"
git branch -M main
# create an empty repository on github.com first, then:
git remote add origin https://github.com/<your-username>/hospital-patient-priority-system.git
git push -u origin main
```

## Deploy on Streamlit Community Cloud

1. Push the project to a public GitHub repository (steps above).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Choose **Create app** → **Deploy a public app from GitHub**.
4. Select the repository, branch `main`, and main file path `app.py`.
5. Under **Advanced settings** pick Python 3.11 or 3.12.
6. Click **Deploy**. The first build installs `requirements.txt`, then the app is live at a `*.streamlit.app` URL.
7. Put that URL in your report. Later `git push` commits redeploy automatically.

## How the pieces fit

* **Scoring** (`greedy_scheduler.py`): 40% severity, 25% medical priority, 20% waiting time (capped, default 120 min), 15% age band.
  Weights, cap and age bands are editable in the sidebar. Tie-break: score, severity, earlier arrival, smaller ID.
* **Simulation** (`scheduling_strategies.simulate`): one treatment bay, non-preemptive. Waiting time grows with the clock;
  treatment time, turnaround time and algorithm execution time are kept separate.
* **Heap vs greedy**: scores change as patients wait, so a heap with keys frozen at admission can drift from the greedy order.
  Tick *refresh keys* on the comparison page to see them agree exactly, and see the complexity cost in the tables.
* **Benchmark** (`utils/benchmark.py`): datasets are generated before timing, outputs are verified, medians are reported.
  Quadratic greedy selection is skipped above a configurable size, and the table says so.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: algorithms` | Run `streamlit run app.py` from the project root, not from a subfolder. |
| `No module named streamlit` / `plotly` | Activate the virtual environment and run `pip install -r requirements.txt`. |
| Port 8501 busy | `streamlit run app.py --server.port 8502` |
| Fonts look different offline | The CSS falls back to system fonts; nothing breaks. |
| Benchmark feels slow | Lower the repeat count or sizes; 10,000 patients x 5 repeats takes a few seconds. |
| CSV rejected | Read the listed row messages. Required columns: `age, severity, medical_priority, arrival_time, treatment_time`. |
| Cloud app sleeps | Free apps hibernate when idle; open the URL to wake it. |
| Pytest button fails on Cloud | Confirm `pytest` is in `requirements.txt` and the `tests/` folder was committed. |

## Limitations

Single treatment bay, non-preemptive service, exact treatment durations, synthetic arrivals, educational scoring policy.
Benchmark timings are machine-dependent and do not prove asymptotic complexity.

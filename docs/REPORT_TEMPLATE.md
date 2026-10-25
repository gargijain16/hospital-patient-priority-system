# Project report template

Fill each section with your own work. Paste benchmark numbers and screenshots from **your own runs**; none are supplied here.

## 1. Abstract
150 to 200 words: the problem, the algorithms implemented from scratch, how they were compared, and the main finding from your own runs.

## 2. Problem statement
Prioritise emergency-department patients using severity, waiting time, age, medical priority and treatment time. State clearly that this is an educational simulation, not clinical triage.

## 3. Objectives
- Implement merge sort, a binary max-heap and greedy scheduling without library shortcuts.
- Compare greedy, heap, FCFS and shortest-treatment-first on identical data.
- Measure real execution time and verify correctness first.
- Explain where each strategy is not optimal.

## 4. Requirements
**Functional:** register/edit/remove patients; CSV import/export; strategy selection; simulated clock; start/complete treatment; metrics; charts; benchmark; test lab.
**Non-functional:** correctness, determinism (tie-breaks, seeds), responsiveness, readability, deployability on Streamlit Community Cloud, synthetic data only.

## 5. Algorithm design
Describe: weighted score formula and weights; age-band mapping; tie-break chain; greedy selection; merge sort (stable, top-down); binary max-heap (array layout, position map, update_priority); FCFS; STF; simulation model (one bay, non-preemptive).

## 6. Data structures
Patient record, ScoreConfig, list-based ready queue, array-based binary heap plus id-to-index dictionary, trace/step records.

## 7. Pseudocode
Write pseudocode for `greedy_select`, `merge_sort`/`merge`, heap `insert`, `extract`, `sift_up`, `sift_down`, `update_priority`, and `simulate`. (Compare with `algorithms/*.py`.)

## 8. Complexity analysis
Copy the tables from *Algorithm Comparison → Complexity analysis*. Distinguish one decision, scheduling all n patients, sorting a fixed queue, repeated heap operations and extra memory. Explain why the greedy strategy is O(n^2) worst case with dynamic scores.

## 9. Test cases
| ID | Scenario | Expected result | Actual (from Test Lab) | Pass/Fail |
|---|---|---|---|---|
| T1 | Mixed queue of 10 | all invariants hold | | |
| T2 | Empty queue | empty schedule, no crash | | |
| T3 | Single patient | waits 0 minutes | | |
| T4 | Equal scores | order by patient ID | | |
| T5 | Invalid treatment time | rejected with message | | |
| T6 | Missing CSV column | error names the column | | |
| T7 | Duplicate IDs | rejected | | |
| T8 | 10,000 patients | merge sort = heap order | | |
| T9 | Critical patient last | served earlier under greedy than FCFS | | |
| T10 | Long patient under STF | waits longer than under FCFS | | |
Also report the pytest result (`python -m pytest -q`) and the code-audit result.

## 10. Benchmark methodology and actual results
Method: datasets generated before timing; `time.perf_counter`; identical inputs; verification before timing; median of repeats.
Record your environment (Python version, OS, CPU) from the Benchmark page.
Paste your own table and chart, then interpret them: growth ratios, the quadratic algorithm versus n log n, small-n noise. Do not claim timings prove complexity.

## 11. Strategy comparison
Use *Algorithm Comparison* on the demonstration dataset and on a seeded generated dataset. Report average and maximum wait, Critical-patient wait, starvation count, Jain index and severity inversions. Discuss trade-offs: severity vs average wait, fairness, starvation, throughput, local vs global optimality.

## 12. Limitations
Single bay, non-preemptive, known treatment times, synthetic arrivals, educational weights and age bands, machine-dependent timings.

## 13. Conclusion and future scope
Summarise findings. Ideas: multiple bays, pre-emption, aging policies, a heap keyed on treatment time for STF, uncertainty in treatment times, real triage standards under clinical supervision.

## 14. Contribution table (suggested allocation; edit to reflect reality)
| Student | Name | Area | Items |
|---|---|---|---|
| 1 | | Algorithm development | greedy scheduling, priority score, merge sort, complexity analysis, algorithm correctness tests |
| 2 | | Data structures and performance | max-heap, FCFS and STF, benchmarking, metrics, stress and boundary tests |
| 3 | | Application and integration | Streamlit UI, registration and queue, visualizations, CSV, integration tests, documentation, deployment |

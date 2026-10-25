# Presentation outline (9 slides, about 10 minutes)

1. **Title and problem** - Emergency-department prioritisation; educational simulation with synthetic data; team names.
2. **Objectives and constraints** - Algorithms from scratch (no `sorted`, `heapq`); compare, visualise, benchmark.
3. **Scoring policy** - Formula, default weights 40/25/20/15, waiting cap, age bands, tie-breaks. Show *About → Scoring policy*.
4. **Algorithms** - Greedy selection, merge sort, binary max-heap (array layout, sift up/down, update_priority), FCFS, STF.
5. **Simulation model and metrics** - One bay, non-preemptive; waiting vs treatment vs turnaround vs execution time.
6. **Complexity** - Table for merge sort, heap operations and complete strategies (one decision vs all n).
7. **Live results** - Algorithm Comparison table and charts from your run; trade-off cases (critical last, STF starvation).
8. **Benchmark and testing** - Your measured timings and growth ratios; pytest and Test Lab results; code audit.
9. **Limitations, conclusion, future work, contributions** - Honest limits; what you learned; team roles.

Tip: use screenshots from your own runs only.

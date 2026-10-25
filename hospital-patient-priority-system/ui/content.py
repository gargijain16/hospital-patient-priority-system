"""Static explanatory content shared by several pages."""

COMPLEXITY_BASIC = [
    {"Algorithm": "Merge Sort", "Best Case": "O(n log n)", "Average Case": "O(n log n)", "Worst Case": "O(n log n)",
     "Auxiliary Space": "O(n)"},
    {"Algorithm": "Binary Max-Heap Insert", "Best Case": "O(1)", "Average Case": "O(log n)", "Worst Case": "O(log n)",
     "Auxiliary Space": "O(1) auxiliary per operation"},
    {"Algorithm": "Binary Max-Heap Extract", "Best Case": "O(log n)", "Average Case": "O(log n)", "Worst Case": "O(log n)",
     "Auxiliary Space": "O(1) auxiliary per operation"},
    {"Algorithm": "Binary Max-Heap Peek", "Best Case": "O(1)", "Average Case": "O(1)", "Worst Case": "O(1)",
     "Auxiliary Space": "O(1)"},
    {"Algorithm": "Binary Max-Heap Update priority", "Best Case": "O(1)", "Average Case": "O(log n)",
     "Worst Case": "O(log n)", "Auxiliary Space": "O(1) auxiliary per operation"},
]

COMPLEXITY_STRATEGIES = [
    {"Implementation": "Greedy weighted priority (linear scan, scores recomputed each decision)",
     "One decision": "O(r) for r waiting patients", "Schedule all n": "O(n) best (r about 1) / O(n^2) worst (everyone waiting)",
     "Extra memory": "O(n) ready list", "Notes": "Plus O(n log n) to order arrivals by merge sort."},
    {"Implementation": "Priority heap, keys frozen at admission",
     "One decision": "O(log n) extract (+ O(log n) per admitted patient)", "Schedule all n": "O(n log n)",
     "Extra memory": "O(n) array + O(n) position map", "Notes": "Keys can become stale, so the order may differ from greedy."},
    {"Implementation": "Priority heap with keys refreshed before every extraction",
     "One decision": "O(r log r) (r updates of O(log r))", "Schedule all n": "O(n^2 log n) worst",
     "Extra memory": "O(n)", "Notes": "Reproduces the greedy order exactly; shows the cost of dynamic scores."},
    {"Implementation": "FCFS (merge sort by arrival, then pointer)",
     "One decision": "O(1)", "Schedule all n": "O(n log n) dominated by the sort", "Extra memory": "O(n)",
     "Notes": "Ignores severity entirely."},
    {"Implementation": "Shortest treatment first (linear scan)",
     "One decision": "O(r)", "Schedule all n": "O(n^2) worst", "Extra memory": "O(n)",
     "Notes": "A heap keyed on treatment time would give O(n log n); not used here to keep the scan explicit."},
    {"Implementation": "Order a fixed queue by merge sort", "One decision": "n/a", "Schedule all n": "O(n log n)",
     "Extra memory": "O(n) merge buffers", "Notes": "Sorting the complete queue once."},
    {"Implementation": "Order a fixed queue by n heap inserts + n extractions", "One decision": "O(log n) per operation",
     "Schedule all n": "O(n log n)", "Extra memory": "O(n)", "Notes": "Equivalent to heap sort when built by repeated insertion."},
    {"Implementation": "Order a fixed queue by repeated greedy selection", "One decision": "O(r)", "Schedule all n": "O(n^2)",
     "Extra memory": "O(n)", "Notes": "Selection sort in disguise."},
]

METRIC_DEFINITIONS = [
    {"Metric": "Waiting time", "Definition": "w = treatment start - arrival (simulated minutes)",
     "Limitation": "Depends on the arrival pattern and one treatment bay."},
    {"Metric": "Treatment duration", "Definition": "t = required minutes of treatment (an input)",
     "Limitation": "Assumed known exactly in advance."},
    {"Metric": "Turnaround time", "Definition": "T = finish - arrival = w + t", "Limitation": "Includes treatment, unlike waiting time."},
    {"Metric": "Average / maximum waiting time", "Definition": "mean and largest w over scheduled patients",
     "Limitation": "A mean can hide a few very long waits; read it with the maximum."},
    {"Metric": "Throughput", "Definition": "patients finished by (start + horizon) divided by (horizon / 60), patients per hour",
     "Limitation": "Depends on the chosen horizon; with a single bay all non-idling strategies finish the same total work."},
    {"Metric": "Starvation indicator", "Definition": "number of patients whose waiting time exceeds a threshold (default 60 min)",
     "Limitation": "The threshold is arbitrary and not clinical."},
    {"Metric": "Jain fairness index", "Definition": "(sum w)^2 / (n * sum w^2); 1 means equal waits",
     "Limitation": "Measures equality of waiting, not whether sicker patients were seen sooner."},
    {"Metric": "Severity inversions", "Definition": "pairs where a less severe patient started while a more severe one was already waiting",
     "Limitation": "Counts order violations only; O(n^2), skipped above 3,000 patients."},
    {"Metric": "Algorithm execution time", "Definition": "wall-clock seconds from time.perf_counter around the ordering call (Benchmark page)",
     "Limitation": "Machine-dependent and unrelated to simulated hospital minutes."},
]

ASSUMPTIONS = [
    "One treatment bay; treatment is non-preemptive (once started it runs to completion).",
    "Treatment durations are known exactly when a decision is made.",
    "A patient is eligible only after their arrival minute; if nobody is eligible the clock jumps to the next arrival.",
    "The replay uses every patient in the dataset from scratch, ignoring their current live status.",
    "Priority scores use the scoring policy and tie-break rules in the sidebar for every strategy that reports a score.",
    "All data are synthetic and all times are simulated minutes.",
]

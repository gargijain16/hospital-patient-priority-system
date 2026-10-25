from utils.audit import scan_algorithms
from utils.benchmark import ALGORITHMS, run_benchmark
from utils.sample_data import demo_csv_text, demo_patients
from utils.validation import next_patient_id, parse_csv, validate_record

OK = {"patient_id": "P-0100", "age": 40, "severity": "high", "medical_priority": 3, "arrival_time": 5, "treatment_time": 20}


def test_valid_record_normalises_severity():
    p, errs = validate_record(OK)
    assert errs == [] and p.severity == "High" and p.status == "Waiting"


def test_invalid_values_rejected():
    for field, bad in (("age", -1), ("age", 121), ("age", "x"), ("medical_priority", 0), ("medical_priority", 6),
                       ("treatment_time", 0), ("treatment_time", -3), ("arrival_time", -1), ("severity", "Urgent")):
        p, errs = validate_record({**OK, field: bad})
        assert p is None and errs, (field, bad)
    assert validate_record({**OK, "age": 3.5})[0] is None
    assert validate_record(OK, existing_ids={"P-0100"})[0] is None


def test_csv_roundtrip_and_errors():
    pats, errs = parse_csv(demo_csv_text())
    assert errs == [] and pats == demo_patients()
    _, errs = parse_csv("age,severity\n30,Low\n")
    assert "treatment_time" in errs[0]
    _, errs = parse_csv("")
    assert errs
    text = "patient_id,age,severity,medical_priority,arrival_time,treatment_time\nA,30,Low,1,0,5\nA,30,Low,1,0,5\n"
    assert any("Duplicate" in e for e in parse_csv(text)[1])


def test_csv_generates_ids_when_blank():
    text = "age,severity,medical_priority,arrival_time,treatment_time\n30,Low,1,0,5\n31,High,4,1,9\n"
    pats, errs = parse_csv(text, existing_ids={"P-0007"})
    assert errs == [] and [p.patient_id for p in pats] == ["P-0008", "P-0009"]
    assert next_patient_id(["P-0003", "x"]) == "P-0004"


def test_no_builtin_sort_or_heap_in_algorithm_paths():
    problems = {k: v for k, v in scan_algorithms().items() if v}
    assert problems == {}


def test_benchmark_output_structure_and_verification():
    r = run_benchmark([10, 50], repeats=2, seed=1, quadratic_cap=30)
    assert set(r) == {"rows", "verification", "environment", "params"}
    assert len(r["rows"]) == 2 * len(ALGORITHMS)
    assert all(v["passed"] for v in r["verification"])
    skipped = [x for x in r["rows"] if x["n"] == 50 and x["key"] == "greedy_selection"][0]
    assert skipped["median_ms"] is None and "skipped" in skipped["status"]
    ok = [x for x in r["rows"] if x["status"] == "ok"]
    assert all(x["median_ms"] > 0 and x["min_ms"] <= x["median_ms"] <= x["max_ms"] and x["runs"] == 2 for x in ok)

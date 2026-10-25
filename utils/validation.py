"""Input validation and CSV import/export for synthetic patient records."""
from __future__ import annotations

import csv
import io
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from algorithms.models import (MAX_AGE, MAX_MEDICAL_PRIORITY, MAX_TREATMENT_MINUTES, MIN_AGE,
                               MIN_MEDICAL_PRIORITY, SEVERITY_SCORES, STATUS_WAITING, Patient)

REQUIRED_COLUMNS = ("age", "severity", "medical_priority", "arrival_time", "treatment_time")
OPTIONAL_COLUMNS = ("patient_id", "name")
COLUMN_ALIASES = {"emergency_severity": "severity", "id": "patient_id", "treatment_minutes": "treatment_time"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 20000


def _parse_int(value, field: str, lo: int, hi: int, errors: List[str]) -> Optional[int]:
    if isinstance(value, bool) or value is None or (isinstance(value, str) and value.strip() == ""):
        errors.append(f"{field} is required.")
        return None
    try:
        if isinstance(value, str):
            text = value.strip()
            try:
                number = int(text)
            except ValueError:
                f = float(text)
                if not f.is_integer():
                    raise ValueError
                number = int(f)
        elif isinstance(value, float):
            if not value.is_integer():
                raise ValueError
            number = int(value)
        else:
            number = int(value)
    except (ValueError, OverflowError):
        errors.append(f"{field} must be a whole number (got {value!r}).")
        return None
    if number < lo or number > hi:
        errors.append(f"{field} must be between {lo} and {hi} (got {number}).")
        return None
    return number


def max_id_number(ids: Iterable[str]) -> int:
    best = 0
    for pid in ids:
        m = re.match(r"^P-(\d+)$", pid)
        if m and int(m.group(1)) > best:
            best = int(m.group(1))
    return best


def next_patient_id(existing_ids: Iterable[str]) -> str:
    return f"P-{max_id_number(existing_ids) + 1:04d}"


def validate_record(raw: Dict, existing_ids: Iterable[str] = (), row: Optional[int] = None,
                    allow_blank_id: bool = False) -> Tuple[Optional[Patient], List[str]]:
    """Validate one record. Returns (Patient or None, error messages)."""
    errors: List[str] = []
    pid = str(raw.get("patient_id", "") or "").strip()
    if not pid:
        if not allow_blank_id:
            errors.append("patient_id is required.")
    elif not ID_PATTERN.match(pid):
        errors.append("patient_id may only contain letters, digits, '-' and '_' (max 20 characters).")
    elif pid in set(existing_ids):
        errors.append(f"Duplicate patient_id {pid!r}.")

    age = _parse_int(raw.get("age"), "age", MIN_AGE, MAX_AGE, errors)
    med = _parse_int(raw.get("medical_priority"), "medical_priority", MIN_MEDICAL_PRIORITY, MAX_MEDICAL_PRIORITY, errors)
    arrival = _parse_int(raw.get("arrival_time"), "arrival_time", 0, 10_000_000, errors)
    treat = _parse_int(raw.get("treatment_time"), "treatment_time (minutes)", 1, MAX_TREATMENT_MINUTES, errors)

    sev_raw = str(raw.get("severity", "") or "").strip().capitalize()
    if sev_raw not in SEVERITY_SCORES:
        errors.append(f"severity must be one of Critical, High, Moderate, Low (got {raw.get('severity')!r}).")
    name = str(raw.get("name", "") or "").strip()
    if len(name) > 60:
        errors.append("name must be at most 60 characters.")
    if errors:
        prefix = f"Row {row}: " if row is not None else ""
        return None, [prefix + e for e in errors]
    return Patient(pid, name or f"Synthetic {pid or 'patient'}", age, sev_raw, med, arrival, treat,
                   STATUS_WAITING), []


def parse_csv(text: str, existing_ids: Iterable[str] = ()) -> Tuple[List[Patient], List[str]]:
    """Parse and validate CSV text. Any error means nothing should be imported."""
    if len(text.encode("utf-8", errors="ignore")) > MAX_CSV_BYTES:
        return [], ["The file is larger than 5 MB."]
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ["The file is empty or has no header row."]
    names = []
    for f in reader.fieldnames:
        key = (f or "").strip().lower()
        names.append(COLUMN_ALIASES.get(key, key))
    missing = [c for c in REQUIRED_COLUMNS if c not in names]
    if missing:
        return [], [f"Missing required column(s): {', '.join(missing)}. "
                    f"Required: {', '.join(REQUIRED_COLUMNS)}. Optional: {', '.join(OPTIONAL_COLUMNS)}."]
    used = set(existing_ids)
    counter = max_id_number(used)
    patients: List[Patient] = []
    errors: List[str] = []
    for line_no, rec in enumerate(reader, start=2):
        if line_no - 1 > MAX_CSV_ROWS:
            errors.append(f"More than {MAX_CSV_ROWS} rows; split the file.")
            break
        row = {names[i]: (v if v is not None else "") for i, v in enumerate(rec.values()) if i < len(names)}
        if all(str(v).strip() == "" for v in row.values()):
            continue
        if str(row.get("patient_id", "")).strip() == "":
            counter += 1
            while f"P-{counter:04d}" in used:
                counter += 1
            row["patient_id"] = f"P-{counter:04d}"
        p, errs = validate_record(row, used, row=line_no)
        if errs:
            errors.extend(errs)
            continue
        used.add(p.patient_id)
        patients.append(p)
    if not patients and not errors:
        errors.append("The file has a header but no data rows.")
    return patients, errors


INPUT_FIELDS = ("patient_id", "name", "age", "severity", "medical_priority", "arrival_time", "treatment_time")


def records_to_csv(records: Sequence[Dict], fieldnames: Sequence[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(fieldnames), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for r in records:
        writer.writerow(r)
    return buf.getvalue()


def patients_to_input_csv(patients: Sequence[Patient]) -> str:
    return records_to_csv([{"patient_id": p.patient_id, "name": p.name, "age": p.age, "severity": p.severity,
                            "medical_priority": p.medical_priority, "arrival_time": p.arrival_time,
                            "treatment_time": p.treatment_time} for p in patients], INPUT_FIELDS)

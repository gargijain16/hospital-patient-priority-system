"""Synthetic data only. No real patient names or records are ever used."""
from __future__ import annotations

import random
from typing import List, Optional

from algorithms.models import Patient
from .validation import patients_to_input_csv

DEMO_NOW = 60  # simulated minute at which the demo dataset is first shown

# (id, age, severity, medical_priority, arrival, treatment minutes)
_DEMO_ROWS = [
    ("P-0001", 34, "Low", 1, 0, 15), ("P-0002", 67, "Moderate", 3, 2, 30),
    ("P-0003", 8, "Moderate", 3, 4, 20), ("P-0004", 45, "Low", 2, 6, 10),
    ("P-0005", 72, "High", 4, 9, 45), ("P-0006", 29, "Low", 1, 11, 8),
    ("P-0007", 54, "Moderate", 3, 13, 25), ("P-0008", 3, "High", 4, 15, 35),
    ("P-0009", 81, "Moderate", 4, 17, 40), ("P-0010", 22, "Low", 1, 19, 12),
    ("P-0011", 39, "Moderate", 2, 21, 18), ("P-0012", 63, "High", 4, 23, 55),
    ("P-0013", 17, "Low", 2, 25, 14), ("P-0014", 58, "Low", 1, 27, 90),
    ("P-0015", 76, "Critical", 5, 29, 80), ("P-0016", 31, "Moderate", 2, 31, 22),
    ("P-0017", 49, "High", 3, 33, 40), ("P-0018", 1, "Moderate", 4, 35, 28),
    ("P-0019", 26, "Low", 1, 37, 9), ("P-0020", 69, "Moderate", 3, 40, 33),
    ("P-0021", 41, "Low", 2, 43, 11), ("P-0022", 52, "High", 5, 47, 50),
    ("P-0023", 35, "Low", 1, 52, 7), ("P-0024", 60, "Critical", 5, 58, 60),
]


def demo_patients() -> List[Patient]:
    """24 hand-written synthetic patients (includes a late Critical arrival and a 90-min Low case)."""
    return [Patient(pid, f"Demo Patient {pid[2:]}", age, sev, med, arr, tr)
            for pid, age, sev, med, arr, tr in _DEMO_ROWS]


def demo_csv_text() -> str:
    return patients_to_input_csv(demo_patients())


_MED_RANGE = {"Critical": (4, 5), "High": (3, 5), "Moderate": (2, 4), "Low": (1, 3)}
_TREAT_RANGE = {"Critical": (30, 90), "High": (20, 60), "Moderate": (10, 40), "Low": (5, 25)}


def generate_patients(n: int, seed: Optional[int] = 42, start_index: int = 1,
                      mean_gap: float = 3.0, critical_share: float = 0.08) -> List[Patient]:
    """Reproducible synthetic patients: the same seed always yields the same list."""
    if n < 0:
        raise ValueError("n must not be negative")
    rng = random.Random(seed)
    width = max(4, len(str(start_index + n)))
    crit = critical_share
    high = crit + (1 - crit) * 0.25
    mod = high + (1 - crit) * 0.40
    t = 0.0
    out: List[Patient] = []
    for i in range(n):
        t += rng.expovariate(1.0 / mean_gap) if mean_gap > 0 else 0.0
        r = rng.random()
        sev = "Critical" if r < crit else "High" if r < high else "Moderate" if r < mod else "Low"
        a = rng.random()
        age = (rng.randint(0, 4) if a < 0.08 else rng.randint(5, 17) if a < 0.20 else
               rng.randint(18, 49) if a < 0.60 else rng.randint(50, 69) if a < 0.82 else rng.randint(70, 95))
        lo, hi = _MED_RANGE[sev]
        tl, th = _TREAT_RANGE[sev]
        pid = f"P-{start_index + i:0{width}d}"
        out.append(Patient(pid, f"Synthetic {pid}", age, sev, rng.randint(lo, hi), int(t), rng.randint(tl, th)))
    return out

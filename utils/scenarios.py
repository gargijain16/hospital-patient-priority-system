"""Hand-built datasets used by the trade-off analysis and the Test Lab.

Each builder returns a dict: patients, now (snapshot minute), title, description.
All data are synthetic.
"""
from __future__ import annotations

from typing import Dict

from algorithms.models import Patient, ScoreConfig
from .sample_data import generate_patients


def _p(pid, age, sev, med, arrival, treat) -> Patient:
    return Patient(pid, f"Synthetic {pid}", age, sev, med, arrival, treat)


def critical_arrives_last() -> Dict:
    ps = [_p(f"A{i}", 30 + i, "Low", 1, i, 20) for i in range(5)] + [_p("CRIT", 55, "Critical", 5, 5, 30)]
    return {"patients": ps, "now": 5, "title": "Critical patient arrives after five low-severity patients",
            "description": "Five Low patients arrive at minutes 0-4; a Critical patient arrives at minute 5. "
                           "Service is non-preemptive, so the first patient always finishes first."}


def high_severity_behind_queue() -> Dict:
    ps = [_p(f"M{i}", 40 + i, "Moderate", 2, i, 15) for i in range(7)] + [_p("HIGH", 62, "High", 4, 7, 25)]
    return {"patients": ps, "now": 7, "title": "FCFS delaying a High-severity patient",
            "description": "Seven Moderate patients arrive first; a High-severity patient arrives last."}


def long_treatment_stf() -> Dict:
    shorts = [_p(f"S{k:02d}", 30, "Low", 1, 9 * k, 9) for k in range(13)]
    ps = shorts + [_p("LONG", 50, "Low", 1, 1, 90)]
    return {"patients": ps, "now": 117, "title": "Long-treatment patient bypassed under shortest-treatment-first",
            "description": "A 90-minute patient arrives at minute 1. Short 9-minute patients keep arriving exactly "
                           "as the bay frees up, so a shorter job is always available."}


def weights_change_order() -> Dict:
    ps = [_p("W-A", 30, "Critical", 3, 80, 20), _p("W-B", 30, "Moderate", 3, 0, 20),
          _p("W-C", 80, "Low", 5, 20, 20), _p("W-D", 10, "High", 2, 60, 20),
          _p("W-E", 30, "Low", 1, 0, 20), _p("W-F", 1, "Moderate", 5, 70, 20)]
    return {"patients": ps, "now": 90, "title": "Changing the weights changes the order",
            "description": "Six patients ranked at minute 90 under three different weight sets."}


WEIGHT_SETS = {
    "Default (40/25/20/15)": ScoreConfig(),
    "Severity-heavy (70/10/10/10)": ScoreConfig(70, 10, 10, 10),
    "Waiting-heavy (10/10/70/10)": ScoreConfig(10, 10, 70, 10),
}


def score_over_time_patients() -> Dict:
    return {"waiting": _p("LOW-WAIT", 30, "Low", 1, 0, 15),
            "fresh": _p("MOD-FRESH", 30, "Moderate", 2, 0, 15)}


def mixed_queue_10() -> Dict:
    return {"patients": generate_patients(10, seed=7, mean_gap=4), "now": 40,
            "title": "Mixed queue of 10 patients", "description": "Seeded synthetic data (seed 7)."}


def distinct_scores() -> Dict:
    ps = [_p("D1", 30, "Critical", 5, 0, 20), _p("D2", 30, "High", 4, 0, 20), _p("D3", 30, "Moderate", 3, 0, 20),
          _p("D4", 30, "Low", 2, 0, 20), _p("D5", 30, "Low", 1, 0, 20)]
    return {"patients": ps, "now": 0, "title": "Patients with distinct priority scores",
            "description": "Strictly decreasing severity and medical priority."}


def equal_severity_different_waits() -> Dict:
    ps = [_p(f"E{i}", 30, "Moderate", 3, i * 10, 20) for i in range(4)]
    return {"patients": ps, "now": 40, "title": "Equal severity, different waiting times",
            "description": "Four Moderate patients that differ only in arrival time."}


def all_equal_scores() -> Dict:
    ps = [_p(f"Q{i:02d}", 30, "Moderate", 3, 0, 20) for i in range(12)]
    return {"patients": ps, "now": 0, "title": "Many patients with identical priorities",
            "description": "Twelve identical patients; only the patient ID can break the tie."}


def very_long_wait() -> Dict:
    ps = [_p("OLD", 30, "Low", 1, 0, 20), _p("NEW", 30, "Low", 1, 4990, 20)]
    return {"patients": ps, "now": 5000, "title": "A patient with a very long waiting time",
            "description": "One patient has waited 5000 minutes; the waiting term is capped."}


def zero_wait() -> Dict:
    ps = [_p("Z1", 30, "Moderate", 3, 25, 20)]
    return {"patients": ps, "now": 25, "title": "Zero waiting time", "description": "Patient arrives exactly now."}

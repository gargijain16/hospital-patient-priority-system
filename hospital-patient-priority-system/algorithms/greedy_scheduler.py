"""Greedy weighted-priority scheduling.

Priority score (all components normalised to 0-100, weights normalised to sum to 1)::

    score = w_sev * (severity_score / 4 * 100)
          + w_med * (medical_priority / 5 * 100)
          + w_wait * (min(waiting, wait_cap) / wait_cap * 100)
          + w_age * age_band_score(age)

Default weights are 40 / 25 / 20 / 15 %. This is an *educational* policy and is not a
validated medical triage standard.

Greedy choice: at every decision point pick the eligible patient with the highest score.
It is locally optimal under this score, not necessarily globally optimal for every
hospital objective (e.g. it can increase average waiting time versus shortest-job-first).

Deterministic tie-break (``precedes``): higher score, then higher severity, then earlier
arrival, then lexicographically smaller patient ID. This is a strict total order.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from .models import Patient, ScoreConfig

COMPONENT_KEYS = ("severity_pts", "medical_pts", "waiting_pts", "age_pts")
COMPONENT_LABELS = {
    "severity_pts": "emergency severity",
    "medical_pts": "medical priority",
    "waiting_pts": "waiting time",
    "age_pts": "age band",
}


def age_score(age: int, cfg: ScoreConfig) -> float:
    """Age-band lookup: first band whose inclusive upper limit covers ``age``."""
    for upper, score in cfg.age_bands:
        if age <= upper:
            return float(score)
    return float(cfg.age_bands[-1][1])


def waiting_norm(wait: int, cfg: ScoreConfig) -> float:
    """Waiting time normalised to 0-100 and capped at ``cfg.wait_cap`` minutes."""
    if wait <= 0:
        return 0.0
    capped = wait if wait < cfg.wait_cap else cfg.wait_cap
    return capped / cfg.wait_cap * 100.0


def priority_score(p: Patient, now: int, cfg: Optional[ScoreConfig] = None) -> float:
    """Final weighted score (rounded to 6 d.p. so comparisons are stable)."""
    cfg = cfg or ScoreConfig()
    ws, wm, ww, wa = cfg.weights()
    sev = p.severity_score / 4 * 100.0
    med = p.medical_priority / 5 * 100.0
    wt = waiting_norm(p.waiting_time(now), cfg)
    ag = age_score(p.age, cfg)
    return round(ws * sev + wm * med + ww * wt + wa * ag, 6)


def score_components(p: Patient, now: int, cfg: Optional[ScoreConfig] = None) -> Dict[str, float]:
    """Every intermediate value behind the score, for explanation and charts."""
    cfg = cfg or ScoreConfig()
    ws, wm, ww, wa = cfg.weights()
    wait = p.waiting_time(now)
    sev = p.severity_score / 4 * 100.0
    med = p.medical_priority / 5 * 100.0
    wt = waiting_norm(wait, cfg)
    ag = age_score(p.age, cfg)
    pts = (ws * sev, wm * med, ww * wt, wa * ag)
    return {
        "waiting_minutes": wait,
        "severity_norm": sev, "medical_norm": med, "waiting_norm": wt, "age_norm": ag,
        "severity_pts": pts[0], "medical_pts": pts[1], "waiting_pts": pts[2], "age_pts": pts[3],
        "total": round(pts[0] + pts[1] + pts[2] + pts[3], 6),
    }


def precedes(score_a: float, a: Patient, score_b: float, b: Patient) -> bool:
    """True if ``a`` must be served strictly before ``b`` under the priority policy."""
    if score_a != score_b:
        return score_a > score_b
    if a.severity_score != b.severity_score:
        return a.severity_score > b.severity_score
    if a.arrival_time != b.arrival_time:
        return a.arrival_time < b.arrival_time
    return a.patient_id < b.patient_id


def _tie_rule(a: Patient, b: Patient) -> str:
    if a.severity_score != b.severity_score:
        return "higher severity"
    if a.arrival_time != b.arrival_time:
        return "earlier arrival"
    return "lower patient ID"


@dataclass
class GreedyChoice:
    patient: Patient
    index: int                      # position inside the candidate list
    score: float
    components: Dict[str, float]
    n_candidates: int
    runner_up: Optional[Patient]
    runner_up_score: float
    tie_rule: str


def greedy_select(candidates: Sequence[Patient], now: int,
                  cfg: Optional[ScoreConfig] = None) -> Optional[GreedyChoice]:
    """One greedy decision: a single linear scan, O(r) for r candidates, O(1) extra space."""
    if not candidates:
        return None
    cfg = cfg or ScoreConfig()
    best = second = None
    best_s = second_s = 0.0
    best_i = 0
    for i in range(len(candidates)):
        p = candidates[i]
        s = priority_score(p, now, cfg)
        if best is None or precedes(s, p, best_s, best):
            second, second_s = best, best_s
            best, best_s, best_i = p, s, i
        elif second is None or precedes(s, p, second_s, second):
            second, second_s = p, s
    tie = _tie_rule(best, second) if (second is not None and second_s == best_s) else ""
    return GreedyChoice(best, best_i, best_s, score_components(best, now, cfg),
                        len(candidates), second, second_s, tie)


def explain_choice(c: GreedyChoice) -> str:
    """Plain-language reason for one greedy step."""
    top_key, top_val = COMPONENT_KEYS[0], -1.0
    for k in COMPONENT_KEYS:
        if c.components[k] > top_val:
            top_key, top_val = k, c.components[k]
    text = (f"{c.patient.patient_id} ({c.patient.severity}) has the highest score, {c.score:.2f}, "
            f"among {c.n_candidates} eligible patient(s); the largest contribution is "
            f"{COMPONENT_LABELS[top_key]} ({top_val:.1f} pts).")
    r = c.runner_up
    if r is not None:
        if c.tie_rule:
            text += f" Tied with {r.patient_id} at {c.score:.2f}; tie broken by {c.tie_rule}."
        else:
            text += f" Runner-up {r.patient_id} scored {c.runner_up_score:.2f} (margin {c.score - c.runner_up_score:.2f})."
    return text

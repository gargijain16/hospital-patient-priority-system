"""Core data model: the synthetic Patient record and the scoring configuration.

All times are integer *simulated minutes*. ``arrival_time`` is the minute at which a
patient entered the queue. Waiting time, treatment time, turnaround time and algorithm
execution time are four different quantities and are never mixed:

* waiting time      = (treatment start, or "now" if not started yet) - arrival_time
* treatment time    = required minutes of treatment (an input, ``treatment_time``)
* turnaround time   = finish_time - arrival_time = waiting + treatment
* execution time    = real wall-clock seconds measured by ``time.perf_counter`` (benchmark page only)
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

SEVERITY_SCORES = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}
SEVERITY_ORDER = ("Critical", "High", "Moderate", "Low")  # highest first

STATUS_WAITING = "Waiting"
STATUS_IN_TREATMENT = "In Treatment"
STATUS_COMPLETED = "Completed"
STATUSES = (STATUS_WAITING, STATUS_IN_TREATMENT, STATUS_COMPLETED)

MIN_AGE, MAX_AGE = 0, 120
MIN_MEDICAL_PRIORITY, MAX_MEDICAL_PRIORITY = 1, 5
MAX_TREATMENT_MINUTES = 1440  # sanity upper bound (24 h)

# Educational age-band mapping: (inclusive upper age, age-priority score 0-100).
# Very young and older patients get a higher score. This is NOT a validated clinical rule.
DEFAULT_AGE_BANDS: Tuple[Tuple[int, float], ...] = (
    (1, 100.0), (4, 90.0), (12, 70.0), (17, 50.0),
    (39, 25.0), (59, 40.0), (74, 70.0), (120, 90.0),
)


@dataclass
class ScoreConfig:
    """Configurable weighted-priority policy (weights are relative, normalised to sum to 1)."""

    w_severity: float = 40.0
    w_medical: float = 25.0
    w_waiting: float = 20.0
    w_age: float = 15.0
    wait_cap: int = 120  # minutes; waiting beyond this adds nothing more to the score
    age_bands: Tuple[Tuple[int, float], ...] = DEFAULT_AGE_BANDS

    def weights(self) -> Tuple[float, float, float, float]:
        total = self.w_severity + self.w_medical + self.w_waiting + self.w_age
        if total <= 0:
            raise ValueError("At least one scoring weight must be positive.")
        return (self.w_severity / total, self.w_medical / total,
                self.w_waiting / total, self.w_age / total)

    def validate(self) -> List[str]:
        errors: List[str] = []
        for name in ("w_severity", "w_medical", "w_waiting", "w_age"):
            if getattr(self, name) < 0:
                errors.append(f"{name} must not be negative.")
        if self.w_severity + self.w_medical + self.w_waiting + self.w_age <= 0:
            errors.append("At least one weight must be positive.")
        if self.wait_cap < 1:
            errors.append("The waiting-time cap must be at least 1 minute.")
        if not self.age_bands:
            errors.append("At least one age band is required.")
        else:
            previous = -1
            for upper, score in self.age_bands:
                if upper <= previous:
                    errors.append("Age-band upper limits must be strictly increasing.")
                    break
                if not 0 <= score <= 100:
                    errors.append("Age-band scores must be between 0 and 100.")
                    break
                previous = upper
            if self.age_bands[-1][0] < MAX_AGE:
                errors.append(f"The last age band must end at {MAX_AGE} so every age is covered.")
        return errors


@dataclass
class Patient:
    """One synthetic patient record (never real personal data)."""

    patient_id: str
    name: str
    age: int
    severity: str
    medical_priority: int
    arrival_time: int
    treatment_time: int
    status: str = STATUS_WAITING
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
    queue_position: Optional[int] = None
    priority_score: Optional[float] = None  # last computed score (informational cache)

    @property
    def severity_score(self) -> int:
        return SEVERITY_SCORES[self.severity]

    def waiting_time(self, now: int) -> int:
        """Minutes spent waiting. Frozen at treatment start once treatment has begun."""
        if self.start_time is not None:
            return self.start_time - self.arrival_time
        w = now - self.arrival_time
        return w if w > 0 else 0

    def turnaround_time(self) -> Optional[int]:
        if self.finish_time is None:
            return None
        return self.finish_time - self.arrival_time

    def copy(self) -> "Patient":
        return replace(self)

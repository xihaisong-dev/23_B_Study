"""Candidate plugin contract (Protocol) with structured failures.

Candidates return only factors, a real ``beta``, diagnostics and a structured
failure.  They never compute ranking scores, complexity or a "winner" — those are
derived by the shared validation/scoring layer in the same metric for every
candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, Sequence, Tuple

Matrix = Sequence[Sequence[complex]]


@dataclass(frozen=True)
class FailureRecord:
    stage: str
    error_type: str
    message: str


@dataclass
class CandidateContext:
    problem_id: str
    candidate_id: str
    seed: int
    run_id: str
    work_dir: str
    deadline_monotonic: Optional[float] = None


@dataclass
class CandidateOutput:
    status: str                                     # "SUCCESS" | "FAIL" | "BLOCKED"
    factors: Optional[Tuple[Matrix, ...]] = None
    beta: Optional[float] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    failure: Optional[FailureRecord] = None

    def __post_init__(self) -> None:
        if self.status not in ("SUCCESS", "FAIL", "BLOCKED"):
            raise ValueError(f"unknown status {self.status!r}")
        if self.status == "SUCCESS":
            if not self.factors or self.beta is None:
                raise ValueError("SUCCESS requires non-empty factors and a finite beta")
        else:
            if self.failure is None:
                raise ValueError(f"{self.status} requires a FailureRecord")


class Candidate(Protocol):
    candidate_id: str

    def solve(self, context: CandidateContext) -> CandidateOutput:
        ...


class FakeCandidate:
    """Deterministic test double returning a fixed factor chain (test only)."""

    candidate_id = "fake"

    def __init__(self, factors: Sequence[Matrix], beta: float = 1.0):
        self._factors = tuple(factors)
        self._beta = beta

    def solve(self, context: CandidateContext) -> CandidateOutput:
        return CandidateOutput(
            status="SUCCESS",
            factors=self._factors,
            beta=self._beta,
            diagnostics={"kind": "fake"},
        )


class FailingCandidate:
    """Test double that always reports a structured FAIL (test only)."""

    candidate_id = "failing"

    def solve(self, context: CandidateContext) -> CandidateOutput:
        return CandidateOutput(
            status="FAIL",
            failure=FailureRecord("solve", "ValueError", "injected failure"),
        )

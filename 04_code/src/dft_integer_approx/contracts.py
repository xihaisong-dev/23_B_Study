"""Typed protocol-adapter objects (one-way; never reverse-write the protocol).

These objects are built from the frozen ``03_model/tournament_protocol.json``
after the gate passes.  They are plain data and never write back to the protocol.
Unknown protocol fields are preserved in the raw snapshot; missing required
fields fail closed at the gate, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class TargetSpec:
    kind: str                      # "dft" | "kron_dft"
    n: int
    n1: Optional[int] = None       # kron_dft only
    n2: Optional[int] = None       # kron_dft only

    def __post_init__(self) -> None:
        if self.kind not in ("dft", "kron_dft"):
            raise ValueError(f"unknown target kind {self.kind!r}")
        if self.n < 1:
            raise ValueError("n must be positive")
        if self.kind == "kron_dft":
            if self.n1 is None or self.n2 is None:
                raise ValueError("kron_dft target requires n1 and n2")
            if self.n1 * self.n2 != self.n:
                raise ValueError("kron_dft: n1 * n2 must equal n")


@dataclass(frozen=True)
class ConstraintSpec:
    constraint1_row_support_max: Optional[int] = None  # None = not applied
    constraint2_q: Optional[int] = None                # None = not applied

    def __post_init__(self) -> None:
        if self.constraint1_row_support_max is not None and self.constraint1_row_support_max < 1:
            raise ValueError("row support max must be >= 1")
        if self.constraint2_q is not None and self.constraint2_q < 1:
            raise ValueError("q must be >= 1")


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    problem_id: str


@dataclass(frozen=True)
class MetricPolicy:
    rmse_threshold: Optional[float] = None


@dataclass(frozen=True)
class BudgetSpec:
    seeds: Tuple[int, ...] = (0,)
    wall_clock_s: Optional[float] = None


@dataclass(frozen=True)
class ProblemSpec:
    problem_id: str
    target: TargetSpec
    constraints: ConstraintSpec = field(default_factory=ConstraintSpec)
    candidates: Tuple[CandidateSpec, ...] = ()
    metric: MetricPolicy = field(default_factory=MetricPolicy)
    budget: BudgetSpec = field(default_factory=BudgetSpec)

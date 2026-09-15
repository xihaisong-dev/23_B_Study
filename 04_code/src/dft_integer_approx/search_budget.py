# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: stop conditions and traces are exercised with deterministic clocks in tests.
"""Shared in-loop resource budget and convergence state for every challenger."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class SearchBudget:
    wall_clock_s: float
    sweep_cap: int
    patience: int = 50
    tolerance: float = 1e-10
    trace_limit: int = 1000

    def __post_init__(self) -> None:
        if self.wall_clock_s <= 0 or self.sweep_cap <= 0 or self.patience <= 0:
            raise ValueError("search budget values must be positive")
        if self.tolerance < 0 or not math.isfinite(self.tolerance):
            raise ValueError("tolerance must be finite and non-negative")

    @classmethod
    def frozen(cls, n: int, *, smoke: bool = False) -> "SearchBudget":
        if smoke:
            return cls(wall_clock_s=20.0, sweep_cap=8, patience=8,
                       tolerance=1e-10, trace_limit=250)
        if n <= 16:
            return cls(300.0, 5000)
        if n == 32:
            return cls(900.0, 15000)
        return cls(1800.0, 30000)

    def start(self, clock: Callable[[], float] = time.perf_counter) -> "StopState":
        return StopState(self, clock=clock)


@dataclass
class StopState:
    budget: SearchBudget
    clock: Callable[[], float] = time.perf_counter
    started_at: float = field(init=False)
    deadline: float = field(init=False)
    sweeps: int = 0
    stale_sweeps: int = 0
    stop_reason: Optional[str] = None
    best_rmse: Optional[float] = None
    evaluated_proposals: int = 0
    accepted_proposals: int = 0
    rejected_proposals: int = 0
    failure_reasons: Dict[str, int] = field(default_factory=dict)
    improvement_trace: List[Dict[str, Any]] = field(default_factory=list)
    proposal_trace: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.started_at = self.clock()
        self.deadline = self.started_at + self.budget.wall_clock_s

    def should_stop(self) -> bool:
        if self.stop_reason is not None:
            return True
        if self.clock() >= self.deadline:
            self.stop_reason = "wall_deadline"
        elif self.sweeps >= self.budget.sweep_cap:
            self.stop_reason = "sweep_cap"
        elif self.stale_sweeps >= self.budget.patience:
            self.stop_reason = "patience"
        return self.stop_reason is not None

    def finish_sweep(self, objective_sse: float, n: int, *, phase: str,
                     evaluated: int = 0, accepted: int = 0) -> None:
        value = math.sqrt(max(0.0, objective_sse)) / n
        previous = self.best_rmse
        improvement = None if previous is None else previous - value
        if previous is None or value < previous:
            self.best_rmse = value
        self.stale_sweeps = (0 if improvement is None or improvement >= self.budget.tolerance
                             else self.stale_sweeps + 1)
        self.sweeps += 1
        self.evaluated_proposals += evaluated
        self.accepted_proposals += accepted
        self.rejected_proposals += max(0, evaluated - accepted)
        if len(self.improvement_trace) < self.budget.trace_limit:
            self.improvement_trace.append({"sweep": self.sweeps, "phase": phase,
                                           "rmse": value, "improvement": improvement,
                                           "evaluated": evaluated, "accepted": accepted})
        self.should_stop()

    def record_proposal(self, *, kind: str, accepted: bool,
                        reason: str, detail: Optional[Dict[str, Any]] = None) -> None:
        if not accepted and reason != "evaluated":
            self.failure_reasons[reason] = self.failure_reasons.get(reason, 0) + 1
        if len(self.proposal_trace) < self.budget.trace_limit:
            event = {"kind": kind, "accepted": accepted, "reason": reason}
            if detail:
                event.update(detail)
            self.proposal_trace.append(event)

    def diagnostics(self) -> Dict[str, Any]:
        if self.stop_reason is None:
            self.stop_reason = "algorithm_complete"
        return {"search_budget": {"wall_clock_s": self.budget.wall_clock_s,
                                   "sweep_cap": self.budget.sweep_cap,
                                   "patience": self.budget.patience,
                                   "tolerance": self.budget.tolerance},
                "stop_reason": self.stop_reason, "sweeps": self.sweeps,
                "stale_sweeps": self.stale_sweeps,
                "evaluated_proposals": self.evaluated_proposals,
                "accepted_proposals": self.accepted_proposals,
                "rejected_proposals": self.rejected_proposals,
                "failure_reasons": dict(sorted(self.failure_reasons.items())),
                "improvement_trace": self.improvement_trace,
                "proposal_trace": self.proposal_trace}

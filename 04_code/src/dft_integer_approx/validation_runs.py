# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Human verification: preregistered variants remain NOT_RUN until parent L2 evidence exists.
"""Executable, preregistered L3 robustness and L4 ablation sub-run configs."""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Sequence

from .formal_tournament_runner import _case, build_plan, tuple_sha256


def build_validation_plan(protocol: Dict[str, Any], level: str, *,
                          smoke: bool = False) -> List[Dict[str, Any]]:
    if level not in {"L3", "L4"}:
        raise ValueError("validation level must be L3 or L4")
    parents = [case for case in build_plan(protocol, smoke=True)
               if case["kind"] == "challenger"]
    plan: List[Dict[str, Any]] = []
    for parent in parents:
        parent_hash = tuple_sha256(parent)
        variants = _l3_variants(parent) if level == "L3" else _l4_variants(parent)
        for variant in variants:
            case = dict(parent)
            case["validation_level"] = level
            case["parent_run_id"] = None
            case["parent_tuple_sha256"] = parent_hash
            case["variant"] = variant
            if "effective_seed" in variant:
                case["seed"] = variant["effective_seed"]
            if variant.get("axis") == "boundary_K_q":
                case["K"] = variant["K"]
                case["q"] = variant["q"]
            if smoke:
                case["budget"] = {"wall_clock_s": 20, "sweep_cap": 8,
                                  "source": f"{level} smoke validation"}
            plan.append(case)
    return plan


def _l3_variants(parent: Dict[str, Any]) -> List[Dict[str, Any]]:
    seed = parent["seed"]
    boundary_k = 1 if parent["K"] != 1 else parent["K"] + 1
    boundary_q = parent["q"] if parent["problem"] == "q1" else (1 if parent["q"] != 1 else 4)
    return [
        {"axis": "seed", "name": "alternate_seed", "effective_seed": seed + 1000},
        {"axis": "initialization_order", "name": "reverse", "order": "reverse", "effective_seed": seed + 2000},
        {"axis": "floating_tolerance", "name": "tight", "tolerance": 1e-12},
        {"axis": "multiplication_association", "name": "right_associated", "association": "right"},
        {"axis": "boundary_K_q", "name": "registered_boundary", "K": boundary_k, "q": boundary_q},
    ]


def _l4_variants(parent: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"axis": "ablation", "name": "no_hierarchical_initialization", "disable": ["hierarchical_initialization"]},
        {"axis": "ablation", "name": "no_support_reconnection", "disable": ["support_reconnection"]},
        {"axis": "ablation", "name": "no_discrete_polish", "disable": ["discrete_polish"]},
        {"axis": "ablation", "name": "fixed_support", "disable": ["support_reconnection"], "support_mode": "fixed_butterfly"},
    ]


def validation_statistics(runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Report frozen best/median/worst over feasible real sub-runs."""
    feasible = [float(run["rmse"]) for run in runs if run.get("status") == "PASS"]
    return {"feasible_count": len(feasible),
            "best": min(feasible) if feasible else None,
            "median": statistics.median(feasible) if feasible else None,
            "worst": max(feasible) if feasible else None}

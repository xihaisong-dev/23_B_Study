# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: preregistered variants remain NOT_RUN until parent L2 evidence exists.
"""Executable, preregistered L3 robustness and L4 ablation sub-run configs."""

from __future__ import annotations

import statistics
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .formal_tournament_runner import _case, build_plan, tuple_sha256


def build_validation_plan(protocol: Dict[str, Any], level: str, *,
                          smoke: bool = False,
                          parents: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    if level not in {"L3", "L4"}:
        raise ValueError("validation level must be L3 or L4")
    parent_cases = (list(parents) if parents is not None else
                    [case for case in build_plan(protocol, smoke=True)
                     if case["kind"] == "challenger"])
    plan: List[Dict[str, Any]] = []
    for parent in parent_cases:
        parent_hash = parent.get("tuple_sha256") or tuple_sha256(parent)
        variants = _l3_variants(parent) if level == "L3" else _l4_variants(parent)
        for variant in variants:
            case = {key: parent[key] for key in
                    ("problem", "candidate_id", "kind", "N", "K", "q", "seed", "budget")}
            case["validation_level"] = level
            case["parent_run_id"] = parent.get("run_id")
            case["parent_batch_id"] = parent.get("batch_id")
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


def select_validation_parents(workspace: Path, batch_id: str,
                              protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Select one real completed L2 parent for every registered challenger."""
    expected_ids = {candidate["id"] for problem in protocol["problems"]
                    for candidate in problem["candidates"] if candidate["kind"] == "challenger"}
    grouped: Dict[str, List[Dict[str, Any]]] = {candidate_id: [] for candidate_id in expected_ids}
    for path in (workspace / "05_results/runs").glob("*/run_manifest.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        candidate_id = manifest.get("candidate_id")
        if (manifest.get("batch_id") == batch_id and manifest.get("validation_level") == "L2"
                and candidate_id in grouped):
            grouped[candidate_id].append(manifest)
    missing = sorted(candidate_id for candidate_id, runs in grouped.items() if not runs)
    if missing:
        raise ValueError(f"completed L2 parents missing for: {missing}")
    parents = []
    for candidate_id in sorted(grouped):
        runs = grouped[candidate_id]
        feasible = [run for run in runs if run.get("status") == "PASS"]
        pool = feasible or runs
        parent = min(pool, key=lambda run: (
            float("inf") if run.get("rmse") is None else run["rmse"],
            run["N"], run["K"], run["q"], run["seed"], run["run_id"]))
        parents.append(parent)
    return parents


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


def grouped_validation_statistics(runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Report real best/median/worst for every problem/candidate/validation axis."""
    keys = sorted({(run["problem"], run["candidate_id"],
                    (run.get("variant") or {}).get("axis")) for run in runs})
    return [{"problem_id": problem, "candidate_id": candidate, "axis": axis,
             **validation_statistics([run for run in runs
                                      if (run["problem"], run["candidate_id"],
                                          (run.get("variant") or {}).get("axis"))
                                      == (problem, candidate, axis)])}
            for problem, candidate, axis in keys]

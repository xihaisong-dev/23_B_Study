# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: preregistered variants remain NOT_RUN until parent L2 evidence exists.
"""Executable, preregistered L3 robustness and L4 ablation sub-run configs."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .formal_tournament_runner import _case, build_plan, tuple_sha256


L4_COMPONENTS: Dict[str, Dict[str, Any]] = {
    "no_hierarchical_initialization": {
        "disable": ["hierarchical_initialization"],
        "applicable": {
            "q1-c1-palm-row2", "q1-c2-structure-reconnect",
            "q2-c1-sp2-recursive", "q2-c2-relax-project-polish",
            "q3-c1-discrete-coordinate", "q3-c2-hierarchical-reconnect",
            "q4-c2-kron-reconnect", "q5-c1-lexicographic-grid",
            "q5-c2-large-neighborhood",
        },
        "reason": "candidate has an explicit hierarchical or butterfly initialization",
        "not_applicable_reason": "candidate starts from a generic random discrete construction",
    },
    "no_support_reconnection": {
        "disable": ["support_reconnection"],
        "applicable": {
            "q1-c2-structure-reconnect", "q3-c1-discrete-coordinate",
            "q3-c2-hierarchical-reconnect", "q4-c1-generic-discrete",
            "q4-c2-kron-reconnect", "q5-c1-lexicographic-grid",
            "q5-c2-large-neighborhood",
        },
        "reason": "candidate proposes row-support swaps or reconnections",
        "not_applicable_reason": "candidate has no row-support reconnection component",
    },
    "no_discrete_polish": {
        "disable": ["discrete_polish"],
        "applicable": {
            "q2-c1-sp2-recursive", "q2-c2-relax-project-polish",
            "q3-c1-discrete-coordinate", "q3-c2-hierarchical-reconnect",
            "q4-c1-generic-discrete", "q4-c2-kron-reconnect",
            "q5-c1-lexicographic-grid", "q5-c2-large-neighborhood",
        },
        "reason": "candidate has post-projection or native discrete local search",
        "not_applicable_reason": "q1 coefficients are continuous, so no discrete-polish component exists",
    },
    "fixed_support": {
        "disable": ["support_reconnection"],
        "support_mode": "fixed_butterfly",
        "applicable": {
            "q1-c2-structure-reconnect", "q3-c1-discrete-coordinate",
            "q3-c2-hierarchical-reconnect", "q4-c2-kron-reconnect",
            "q5-c1-lexicographic-grid", "q5-c2-large-neighborhood",
        },
        "reason": "candidate has reconnectable row-2 support rooted in a structured start",
        "not_applicable_reason": "candidate has no reconnectable structured row-2 support to freeze",
    },
}


def build_validation_plan(protocol: Dict[str, Any], level: str, *,
                          smoke: bool = False,
                          parents: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    if level not in {"L3", "L4"}:
        raise ValueError("validation level must be L3 or L4")
    if parents is not None:
        parent_cases = list(parents)
    else:
        prototypes = [case for case in build_plan(protocol, smoke=True)
                      if case["kind"] == "challenger"]
        parent_cases = [
            {**case, "budget": _case(case["problem"], case["candidate_id"],
                                     case["kind"], case["N"], case["K"],
                                     case["q"], case["seed"], smoke=False)["budget"]}
            for case in prototypes]
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
    """Select parents only after strict validation of a complete canonical L2 batch."""
    from .aggregation import aggregate_formal_batch

    aggregated = aggregate_formal_batch(workspace, batch_id, write=False)
    metrics = aggregated["metrics"]
    if metrics.get("run_count") != 1442 or metrics.get("batch_id") != batch_id:
        raise ValueError("validation parents require one strict complete canonical L2 batch")
    expected_ids = {candidate["id"] for problem in protocol["problems"]
                    for candidate in problem["candidates"] if candidate["kind"] == "challenger"}
    grouped: Dict[str, List[Dict[str, Any]]] = {candidate_id: [] for candidate_id in expected_ids}
    for summary in metrics["runs"]:
        path = workspace / summary["run_manifest"]
        manifest = json.loads(path.read_text(encoding="utf-8"))
        candidate_id = manifest.get("candidate_id")
        if candidate_id in grouped:
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


def validate_parent_bindings(workspace: Path,
                             cases: Sequence[Dict[str, Any]]) -> None:
    """Revalidate every parent batch and bind child cases to exact parent manifests."""
    from .aggregation import aggregate_formal_batch

    batches: Dict[str, Dict[tuple[str, str], Dict[str, Any]]] = {}
    for case in cases:
        batch_id = case.get("parent_batch_id")
        run_id = case.get("parent_run_id")
        parent_tuple = case.get("parent_tuple_sha256")
        if not all(isinstance(value, str) and value for value in
                   (batch_id, run_id, parent_tuple)):
            raise ValueError("formal L3/L4 case lacks complete parent lineage")
        if batch_id not in batches:
            result = aggregate_formal_batch(workspace, batch_id, write=False)
            if result["metrics"].get("run_count") != 1442:
                raise ValueError("parent batch is not a strict complete canonical L2 batch")
            index: Dict[tuple[str, str], Dict[str, Any]] = {}
            for summary in result["metrics"]["runs"]:
                manifest = json.loads((workspace / summary["run_manifest"]).read_text(
                    encoding="utf-8"))
                index[(manifest["run_id"], manifest["tuple_sha256"])] = manifest
            batches[batch_id] = index
        parent = batches[batch_id].get((run_id, parent_tuple))
        if parent is None:
            raise ValueError("parent run/tuple is absent from the strict L2 batch")
        if (parent.get("batch_id") != batch_id
                or parent.get("problem") != case.get("problem")
                or parent.get("candidate_id") != case.get("candidate_id")):
            raise ValueError("child case and strict L2 parent identity differ")


def _l3_variants(parent: Dict[str, Any]) -> List[Dict[str, Any]]:
    seed = parent["seed"]
    boundary_k = 1 if parent["K"] != 1 else parent["K"] + 1
    boundary_q = parent["q"] if parent["problem"] == "q1" else (1 if parent["q"] != 1 else 4)
    return [
        {"axis": "seed", "name": "alternate_seed", "effective_seed": seed + 1000},
        {"axis": "initialization_order", "name": "reverse", "order": "reverse", "effective_seed": seed + 2000},
        {"axis": "floating_tolerance", "name": "tight", "tolerance": 1e-12},
        {"axis": "multiplication_association",
         "name": "right_associated_numerical_recompute",
         "association": "right",
         "scope": "independent_persisted_artifact_recompute_only"},
        {"axis": "boundary_K_q", "name": "registered_boundary", "K": boundary_k, "q": boundary_q},
    ]


def _l4_variants(parent: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidate_id = parent["candidate_id"]
    variants = []
    for name, spec in L4_COMPONENTS.items():
        if candidate_id not in spec["applicable"]:
            continue
        variant = {"axis": "ablation", "name": name,
                   "disable": list(spec["disable"]),
                   "applicability": "APPLICABLE", "reason": spec["reason"]}
        if "support_mode" in spec:
            variant["support_mode"] = spec["support_mode"]
        variants.append(variant)
    return variants


def l4_applicability(protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Machine-readable 40-cell applicability matrix, including reasoned N/A cells."""
    candidate_ids = [candidate["id"] for problem in protocol["problems"]
                     for candidate in problem["candidates"]
                     if candidate["kind"] == "challenger"]
    records = []
    for candidate_id in candidate_ids:
        for name, spec in L4_COMPONENTS.items():
            applicable = candidate_id in spec["applicable"]
            records.append({"candidate_id": candidate_id, "ablation": name,
                            "status": "APPLICABLE" if applicable else "NOT_APPLICABLE",
                            "reason": (spec["reason"] if applicable
                                       else spec["not_applicable_reason"])})
    return records


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

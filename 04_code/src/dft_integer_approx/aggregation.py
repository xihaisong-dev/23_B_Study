# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Human verification: strict batch bijection and frozen ordering are unit-tested before formal use.
"""Strict, fail-closed aggregation for one complete frozen L2 batch."""

from __future__ import annotations

import json
from functools import cmp_to_key
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .formal_baseline_runner import _atomic_json
from .formal_tournament_runner import tuple_sha256


ALLOWED_STATUSES = {"PASS", "TIMEOUT", "INFEASIBLE", "CRASH", "CONSTRAINT_FAIL"}


def aggregate_formal_batch(workspace: Path, batch_id: str, *,
                           write: bool = True) -> Dict[str, Any]:
    workspace = workspace.resolve()
    batch_dir = workspace / "05_results/batches" / batch_id
    plan_payload = json.loads((batch_dir / "plan.json").read_text(encoding="utf-8"))
    config = json.loads((batch_dir / "config.json").read_text(encoding="utf-8"))
    if not config.get("formal") or config.get("validation_level") != "L2":
        raise ValueError("aggregation accepts only formal L2 batches")
    expected = {tuple_sha256(case): case for case in plan_payload["tuples"]}
    if len(expected) != 1442 or plan_payload.get("tuple_count") != 1442:
        raise ValueError("formal L2 plan must contain exactly 1442 unique tuples")
    observed: Dict[str, Dict[str, Any]] = {}
    for path in (workspace / "05_results/runs").glob("*/run_manifest.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("batch_id") != batch_id:
            continue
        key = manifest.get("tuple_sha256")
        if key in observed:
            raise ValueError(f"duplicate tuple in batch: {key}")
        if key not in expected:
            raise ValueError(f"unexpected tuple in batch: {key}")
        if manifest.get("status") not in ALLOWED_STATUSES:
            raise ValueError(f"unknown status: {manifest.get('status')}")
        manifest["run_manifest"] = path.relative_to(workspace).as_posix()
        observed[key] = manifest
    missing = sorted(set(expected) - set(observed))
    if missing:
        raise ValueError(f"incomplete formal batch: {len(missing)} missing tuples")
    runs = [observed[tuple_sha256(case)] for case in plan_payload["tuples"]]
    metrics = {"schema_version": "3.0", "status": "BLOCKED",
               "phase_status": "L2_COMPLETE_L3_L4_NOT_RUN",
               "batch_id": batch_id, "batch_config": config,
               "run_count": len(runs), "runs": [_summary(run) for run in runs],
               "blocking_reason": "L3 robustness and L4 ablation are NOT_RUN."}
    tournament = _tournament(runs, batch_id)
    frontier = _q5_frontier(runs, batch_id)
    if write:
        _atomic_json(workspace / "05_results/metrics.json", metrics)
        _atomic_json(workspace / "05_results/tournament.json", tournament)
        _atomic_json(workspace / "05_results/q5_frontier.json", frontier)
    return {"metrics": metrics, "tournament": tournament, "q5_frontier": frontier}


def _summary(run: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("run_id", "problem", "candidate_id", "N", "K", "q", "seed",
            "status", "constraints_status", "rmse", "L", "C", "wall_clock_s",
            "tuple_sha256", "run_manifest")
    return {key: run.get(key) for key in keys}


def q5_rank_key(run: Dict[str, Any]) -> tuple:
    """Frozen q5 order: q is deliberately absent."""
    return (run["C"], run["K"], run["rmse"], run["seed"], run["candidate_id"])


def _compare_q1_q4(left: Dict[str, Any], right: Dict[str, Any]) -> int:
    delta = left["rmse"] - right["rmse"]
    if abs(delta) > 1e-12:
        return -1 if delta < 0 else 1
    lk = (left["C"], left["K"], left["wall_clock_s"], left["seed"], left["candidate_id"])
    rk = (right["C"], right["K"], right["wall_clock_s"], right["seed"], right["candidate_id"])
    return -1 if lk < rk else (1 if lk > rk else 0)


def _best(runs: Sequence[Dict[str, Any]], pid: str) -> Optional[Dict[str, Any]]:
    feasible = [run for run in runs if run["status"] == "PASS"]
    if not feasible:
        return None
    if pid == "q5":
        return min(feasible, key=q5_rank_key)
    return sorted(feasible, key=cmp_to_key(_compare_q1_q4))[0]


def _tournament(runs: Sequence[Dict[str, Any]], batch_id: str) -> Dict[str, Any]:
    problems = []
    for pid in ("q1", "q2", "q3", "q4", "q5"):
        problem_runs = [run for run in runs if run["problem"] == pid]
        selections = []
        for n in sorted({run["N"] for run in problem_runs}):
            group = [run for run in problem_runs if run["N"] == n]
            best = _best(group, pid)
            baseline = _best([run for run in group if "-b0-" in run["candidate_id"]], pid)
            if pid != "q5" and baseline is not None and best is not None:
                # Frozen fallback: a challenger must actually beat the baseline.
                if _compare_q1_q4(best, baseline) >= 0:
                    best = baseline
            selections.append({"N": n, "winner_id": None if best is None else best["candidate_id"],
                               "winner_run_id": None if best is None else best["run_id"],
                               "fallback_baseline_run_id": None if baseline is None else baseline["run_id"]})
        problems.append({"id": pid, "status": "L2_PROVISIONAL",
                         "robustness_status": "NOT_RUN", "ablation_status": "NOT_RUN",
                         "selections": selections})
    return {"schema_version": "3.0", "status": "BLOCKED", "batch_id": batch_id,
            "winner_scope": "provisional_per_N_after_L2_only", "problems": problems,
            "blocking_reason": "L3/L4 are required before final winner status."}


def _q5_frontier(runs: Sequence[Dict[str, Any]], batch_id: str) -> Dict[str, Any]:
    q5 = [run for run in runs if run["problem"] == "q5" and run["status"] == "PASS"]
    by_n = []
    for n in sorted({run["N"] for run in runs if run["problem"] == "q5"}):
        feasible = sorted([run for run in q5 if run["N"] == n], key=q5_rank_key)
        by_n.append({"N": n, "winner_id": None if not feasible else feasible[0]["candidate_id"],
                     "winner_run_id": None if not feasible else feasible[0]["run_id"],
                     "feasible_count": len(feasible),
                     "frontier": [_summary(run) for run in feasible]})
    return {"schema_version": "3.0", "status": "BLOCKED", "batch_id": batch_id,
            "q_excluded_from_tie_objective": True, "by_N": by_n}

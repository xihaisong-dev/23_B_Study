# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: every tuple and persisted byte is revalidated before aggregation.
"""Strict, fail-closed aggregation for one complete frozen L2 batch."""

from __future__ import annotations

import json
from functools import cmp_to_key
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .formal_baseline_runner import _atomic_json, _tree_sha256
from .formal_tournament_runner import _json_sha256, build_plan, tuple_sha256
from .hashing import sha256_file
from .independent_verify import verify_artifact
from .l0_validation import gaussian_integer_rmse_lower_bound
from .protocol_gate import check_frozen


ALLOWED_STATUSES = {"PASS", "TIMEOUT", "INFEASIBLE", "CRASH", "CONSTRAINT_FAIL"}
TUPLE_FIELDS = ("problem", "candidate_id", "kind", "N", "K", "q", "seed", "budget")


def aggregate_formal_batch(workspace: Path, batch_id: str, *,
                           write: bool = True) -> Dict[str, Any]:
    workspace = workspace.resolve()
    gate = check_frozen(str(workspace))
    if not gate.allowed:
        raise ValueError("freeze gate failed: " + "; ".join(gate.reasons))
    batch_dir = workspace / "05_results/batches" / batch_id
    plan_path, config_path = batch_dir / "plan.json", batch_dir / "config.json"
    plan_payload, config = _load_object(plan_path), _load_object(config_path)
    if not config.get("formal") or config.get("validation_level") != "L2":
        raise ValueError("aggregation accepts only formal L2 batches")

    protocol_path = workspace / "03_model/tournament_protocol.json"
    protocol = _load_object(protocol_path)
    canonical = build_plan(protocol, smoke=False)
    if len(canonical) != 1442 or len({tuple_sha256(case) for case in canonical}) != 1442:
        raise ValueError("frozen protocol did not rebuild exactly 1442 unique tuples")
    if plan_payload.get("tuples") != canonical or plan_payload.get("tuple_count") != 1442:
        raise ValueError("batch plan is not the ordered canonical frozen 1442 plan")
    if plan_payload.get("batch_id") != batch_id or not plan_payload.get("formal"):
        raise ValueError("plan batch identity/formal flag mismatch")

    input_manifest = _load_object(workspace / "00_admin/input_manifest.json")
    problem_record = input_manifest["files"][0]
    current = {
        "protocol_sha256": sha256_file(protocol_path),
        "protocol_freeze_sha256": sha256_file(workspace / "00_admin/freezes/tournament_protocol.json"),
        "problem_freeze_sha256": sha256_file(workspace / "00_admin/freezes/problem.json"),
        "code_tree_sha256": _tree_sha256(workspace / "04_code"),
        "input_manifest_sha256": sha256_file(workspace / "00_admin/input_manifest.json"),
        "problem_input_sha256": sha256_file(workspace / problem_record["path"]),
        "plan_content_sha256": _json_sha256(canonical),
    }
    for key, value in current.items():
        if config.get(key) != value:
            raise ValueError(f"batch config {key} differs from current frozen input")
    if config.get("batch_id") != batch_id or config.get("data_class") != problem_record["data_class"]:
        raise ValueError("batch config identity/data class mismatch")
    if config.get("q5_certificate_shortcut") is not False:
        raise ValueError("formal aggregation refuses an unapproved q5 certificate shortcut")

    plan_artifact = _artifact_record(plan_path, workspace)
    config_artifact = _artifact_record(config_path, workspace)
    expected = {tuple_sha256(case): case for case in canonical}
    observed: Dict[str, tuple[Path, Dict[str, Any]]] = {}
    for path in (workspace / "05_results/runs").glob("*/run_manifest.json"):
        manifest = _load_object(path)
        if manifest.get("batch_id") != batch_id:
            continue
        key = manifest.get("tuple_sha256")
        if key in observed:
            raise ValueError(f"duplicate tuple in batch: {key}")
        if key not in expected:
            raise ValueError(f"unexpected tuple in batch: {key}")
        observed[key] = (path, manifest)
    missing = sorted(set(expected) - set(observed))
    if missing:
        raise ValueError(f"incomplete formal batch: {len(missing)} missing tuples")
    runs = []
    for case in canonical:
        path, manifest = observed[tuple_sha256(case)]
        _verify_manifest(workspace, path, manifest, case, config,
                         plan_artifact, config_artifact, problem_record)
        manifest["run_manifest"] = path.relative_to(workspace).as_posix()
        runs.append(manifest)
    metrics = {"schema_version": "3.0", "status": "BLOCKED",
               "phase_status": "L2_COMPLETE_L3_L4_NOT_RUN", "batch_id": batch_id,
               "batch_config": config, "run_count": len(runs),
               "runs": [_summary(run) for run in runs],
               "blocking_reason": "L3 robustness and L4 ablation are NOT_RUN."}
    tournament, frontier = _tournament(runs, batch_id), _q5_frontier(runs, batch_id)
    if write:
        _atomic_json(workspace / "05_results/metrics.json", metrics)
        _atomic_json(workspace / "05_results/tournament.json", tournament)
        _atomic_json(workspace / "05_results/q5_frontier.json", frontier)
    return {"metrics": metrics, "tournament": tournament, "q5_frontier": frontier}


def _verify_manifest(workspace: Path, manifest_path: Path, manifest: Dict[str, Any],
                     case: Dict[str, Any], config: Dict[str, Any],
                     plan_artifact: Dict[str, Any], config_artifact: Dict[str, Any],
                     problem_record: Dict[str, Any]) -> None:
    if manifest_path.parent.name != manifest.get("run_id"):
        raise ValueError("run directory and run_id differ")
    for field in TUPLE_FIELDS:
        if manifest.get(field) != case.get(field):
            raise ValueError(f"manifest tuple field differs: {field}")
    if manifest.get("run_config_sha256") != _json_sha256(case) or manifest.get("tuple_sha256") != tuple_sha256(case):
        raise ValueError("run config or tuple hash mismatch")
    if manifest.get("validation_level") != "L2" or manifest.get("variant") is not None:
        raise ValueError("formal L2 manifest carries wrong level/variant")
    if manifest.get("run_scope") != "FROZEN_L2" or not manifest.get("formal"):
        raise ValueError("formal L2 run scope mismatch")
    for field in ("protocol_sha256", "protocol_freeze_sha256", "problem_freeze_sha256",
                  "code_tree_sha256", "input_manifest_sha256"):
        if manifest.get(field) != config.get(field):
            raise ValueError(f"manifest/config lineage mismatch: {field}")
    if manifest.get("batch_config_sha256") != config.get("plan_content_sha256"):
        raise ValueError("manifest batch config hash mismatch")
    if manifest.get("batch_artifacts") != {"plan": plan_artifact, "config": config_artifact}:
        raise ValueError("manifest batch artifact lineage mismatch")
    if manifest.get("problem_input", {}).get("sha256") != problem_record["sha256"]:
        raise ValueError("manifest problem input mismatch")
    if (manifest.get("problem_input", {}).get("path") != problem_record["path"]
            or manifest.get("data_class") != config.get("data_class")
            or manifest.get("target_generation") != config.get("target_generation")
            or manifest.get("environment", {}).get("dependencies") !=
               {"third_party": [], "standard_library_only": True}):
        raise ValueError("manifest data/dependency lineage mismatch")
    if manifest.get("status") not in ALLOWED_STATUSES:
        raise ValueError(f"unknown status: {manifest.get('status')}")
    for name in ("stdout", "stderr"):
        _verify_artifact_record(workspace, manifest["artifacts"].get(name), manifest_path.parent)

    pid, n, q = case["problem"], case["N"], case["q"]
    if pid == "q5" and manifest["artifacts"].get("q5_certificate") is not None:
        if not config.get("q5_certificate_shortcut"):
            raise ValueError("q5 certificate shortcut was not enabled in batch config")
        cert_path = _verify_artifact_record(workspace, manifest["artifacts"].get("q5_certificate"), manifest_path.parent)
        cert, bound = _load_object(cert_path), gaussian_integer_rmse_lower_bound(n)
        if (manifest.get("status") != "INFEASIBLE" or manifest.get("constraints_status") != "PASS"
                or cert.get("rmse_lower_bound") != bound or bound <= 0.1
                or cert.get("conclusion") != "INFEASIBLE"):
            raise ValueError("invalid q5 Gaussian-integer certificate")
        if manifest["artifacts"].get("factors") is not None:
            raise ValueError("certificate-short-circuited q5 run must not carry factors")
        return

    factor_record = manifest["artifacts"].get("factors")
    if factor_record is None:
        if (manifest.get("status") not in {"CRASH", "TIMEOUT"}
                or any(manifest.get(key) is not None for key in ("rmse", "L", "C"))
                or not manifest.get("failure")):
            raise ValueError("missing factors are only valid for retained failed runs with null metrics")
        return
    factor_path = _verify_artifact_record(workspace, factor_record, manifest_path.parent)
    row_cap = None if pid == "q2" else 2
    independent = verify_artifact(factor_path, pid, n, q, row_cap)
    independently_legal = independent["row_support_ok"] and independent["alphabet_ok"]
    if manifest.get("status") in {"PASS", "INFEASIBLE"} and not independently_legal:
        raise ValueError("successful/infeasible run has an independently illegal factor")
    comparisons = (("target_sha256", independent["target_sha256"]),
                   ("factor_sha256s", independent["factor_sha256s"]),
                   ("L", independent["L"]), ("C", independent["C"]))
    if any(manifest.get(field) != value for field, value in comparisons):
        raise ValueError("independent persisted-factor hash/count mismatch")
    if (manifest.get("rmse") is None or manifest.get("rmse_recompute_independent") is None
            or abs(manifest["rmse"] - independent["rmse"]) > 1e-10
            or abs(manifest["rmse_recompute_independent"] - independent["rmse"]) > 1e-10):
        raise ValueError("independent persisted-factor RMSE mismatch")
    expected_constraints = "PASS" if manifest["status"] in {"PASS", "INFEASIBLE"} else "FAIL"
    if manifest.get("constraints_status") != expected_constraints:
        raise ValueError("status/constraint status mismatch")
    if pid == "q5":
        expected_status = "PASS" if independent["rmse"] <= 0.1 else "INFEASIBLE"
        if manifest.get("status") != expected_status:
            raise ValueError("q5 feasibility status differs from independent RMSE")


def _verify_artifact_record(workspace: Path, record: Any, run_dir: Path) -> Path:
    if not isinstance(record, dict):
        raise ValueError("missing artifact record")
    path = (workspace / record["path"]).resolve()
    if run_dir.resolve() not in path.parents:
        raise ValueError("cross-run or cross-batch artifact path")
    if not path.is_file() or path.stat().st_size != record.get("size") or sha256_file(path) != record.get("sha256"):
        raise ValueError(f"artifact byte lineage mismatch: {path}")
    return path


def _artifact_record(path: Path, workspace: Path) -> Dict[str, Any]:
    return {"path": path.relative_to(workspace).as_posix(), "size": path.stat().st_size,
            "sha256": sha256_file(path)}


def _load_object(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _summary(run: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("run_id", "problem_id", "problem", "candidate_id", "N", "K", "q", "seed",
            "status", "constraints_status", "rmse", "L", "C", "wall_clock_s",
            "tuple_sha256", "run_manifest")
    return {key: run.get(key) for key in keys}


def q5_rank_key(run: Dict[str, Any]) -> tuple:
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
    return min(feasible, key=q5_rank_key) if pid == "q5" else sorted(feasible, key=cmp_to_key(_compare_q1_q4))[0]


def _tournament(runs: Sequence[Dict[str, Any]], batch_id: str) -> Dict[str, Any]:
    problems = []
    for pid in ("q1", "q2", "q3", "q4", "q5"):
        problem_runs = [run for run in runs if run["problem"] == pid]
        selections = []
        for n in sorted({run["N"] for run in problem_runs}):
            group = [run for run in problem_runs if run["N"] == n]
            best = _best(group, pid)
            baseline = _best([run for run in group if "-b0-" in run["candidate_id"]], pid)
            if pid != "q5" and baseline is not None and best is not None and _compare_q1_q4(best, baseline) >= 0:
                best = baseline
            selections.append({"N": n, "winner_id": None if best is None else best["candidate_id"],
                               "winner_run_id": None if best is None else best["run_id"],
                               "fallback_baseline_run_id": None if baseline is None else baseline["run_id"]})
        problems.append({"id": pid, "problem_id": pid, "status": "L2_PROVISIONAL",
                         "evaluated_candidates": sorted({run["candidate_id"] for run in problem_runs}),
                         "winner_id": None,
                         "winner": {"candidate_id": None, "run_id": None, "status": "BLOCKED"},
                         "robustness_status": "NOT_RUN", "ablation_status": "NOT_RUN",
                         "selections": selections})
    return {"schema_version": "3.0", "status": "BLOCKED", "batch_id": batch_id,
            "winner_scope": "provisional_per_N_after_L2_only", "problems": problems,
            "blocking_reason": "L3/L4 are required before final winner status."}


def _q5_frontier(runs: Sequence[Dict[str, Any]], batch_id: str) -> Dict[str, Any]:
    q5_all = [run for run in runs if run["problem"] == "q5"]
    q5 = [run for run in q5_all if run["status"] == "PASS"]
    by_n = []
    for n in sorted({run["N"] for run in q5_all}):
        feasible = sorted([run for run in q5 if run["N"] == n], key=q5_rank_key)
        by_n.append({"N": n, "winner_id": None if not feasible else feasible[0]["candidate_id"],
                     "winner_run_id": None if not feasible else feasible[0]["run_id"],
                     "feasible_count": len(feasible),
                     "certificate_lower_bound": gaussian_integer_rmse_lower_bound(n),
                     "frontier": [_summary(run) for run in feasible]})
    return {"schema_version": "3.0", "status": "BLOCKED", "batch_id": batch_id,
            "winner_id": None, "q_excluded_from_tie_objective": True, "by_N": by_n,
            "gate_incompatibility": {"status": "RECORDED",
                "reason": "exact Gaussian-integer lattice bound exceeds RMSE threshold for all registered N"}}

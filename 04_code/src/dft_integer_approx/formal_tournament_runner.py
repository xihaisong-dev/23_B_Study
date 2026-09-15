# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: gate, constraints, persisted artifacts, and independent recomputation are mandatory.
"""Gate-first L2 runner and machine-readable L3/L4 validation framework.

Smoke executions are deliberately non-formal.  They exercise every registered
candidate without updating the formal metrics or selecting a winner.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .baselines import (
    apply_permutation_right,
    approximate_matrix,
    exact_q1_baseline,
    kron_quantized_butterfly_baseline,
    onefactor_quantized_baseline,
    q1_cost_baseline,
    quantized_butterfly_baseline,
)
from .challengers import challenger_solution
from .constraints import check_alphabet, check_finite_square, check_row_sparse
from .factor_artifacts import write_factor_artifact
from .formal_baseline_runner import _artifact_record, _atomic_json, _tree_sha256, _write_text_lf
from .hardware import count_nontrivial_positions, hardware_complexity
from .hashing import sha256_file
from .independent_verify import verify_artifact
from .l0_validation import run_l0_checks, support_rmse_lower_bound
from .metrics import max_abs_difference, rmse
from .protocol_gate import check_frozen
from .provenance import generate_run_id
from .search_budget import SearchBudget
from .serialization import canonical_matrix_sha256
from .targets import dft_matrix, kron, matmul


BASELINES = {
    "q1-b0-scaled-radix2",
    "q2-b0-onefactor-quantize",
    "q3-b0-quantized-butterfly",
    "q4-b0-kron-butterfly",
    "q5-b0-q1-butterfly",
}
SEEDS = (17, 43, 71)


def build_plan(protocol: Dict[str, Any], *, smoke: bool = False,
               problems: Optional[Sequence[str]] = None,
               candidates: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
    """Expand the frozen L2 grid or the one-instance-per-candidate smoke grid."""
    wanted_problems = set(problems or [])
    wanted_candidates = set(candidates or [])
    known_problems = {problem["id"] for problem in protocol["problems"]}
    known_candidates = {candidate["id"] for problem in protocol["problems"]
                        for candidate in problem["candidates"]}
    unknown_p = wanted_problems - known_problems
    unknown_c = wanted_candidates - known_candidates
    if unknown_p or unknown_c:
        raise ValueError(f"unknown filters: problems={sorted(unknown_p)}, candidates={sorted(unknown_c)}")

    plan: List[Dict[str, Any]] = []
    for problem in protocol["problems"]:
        pid = problem["id"]
        instances = problem["instances"]
        for candidate in problem["candidates"]:
            cid = candidate["id"]
            if wanted_problems and pid not in wanted_problems:
                continue
            if wanted_candidates and cid not in wanted_candidates:
                continue
            if smoke:
                plan.extend(_smoke_instances(pid, cid, candidate["kind"], instances))
            else:
                plan.extend(_full_instances(pid, cid, candidate["kind"], instances))
    return plan


def _full_instances(pid: str, cid: str, kind: str,
                    instances: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    seeds = (0,) if kind == "baseline" else SEEDS
    if pid == "q1":
        for n in instances["N"]:
            ks = (n.bit_length() - 1,) if kind == "baseline" else range(1, n.bit_length() + 2)
            for k in ks:
                for seed in seeds:
                    yield _case(pid, cid, kind, n, k, 16, seed)
    elif pid == "q2":
        for n in instances["N"]:
            ks = (1,) if kind == "baseline" else instances["K_grid"]
            for k in ks:
                for seed in seeds:
                    yield _case(pid, cid, kind, n, k, instances["q"], seed)
    elif pid == "q3":
        for n in instances["N"]:
            ks = (n.bit_length() - 1,) if kind == "baseline" else range(1, n.bit_length() + 2)
            for k in ks:
                for seed in seeds:
                    yield _case(pid, cid, kind, n, k, instances["q"], seed)
    elif pid == "q4":
        ks = (5,) if kind == "baseline" else instances["K_grid"]
        for k in ks:
            for seed in seeds:
                yield _case(pid, cid, kind, instances["N"], k, instances["q"], seed)
    else:
        for n in instances["N"]:
            ks = range(1, min(8, n.bit_length() + 1) + 1)
            qs = (1,) if kind == "baseline" else instances["q_grid"]
            for q in qs:
                for k in ks:
                    for seed in seeds:
                        yield _case(pid, cid, kind, n, k, q, seed)


def _smoke_instances(pid: str, cid: str, kind: str,
                     instances: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    seed = 0 if kind == "baseline" else 17
    if pid == "q1":
        yield _case(pid, cid, kind, 4, 2, 16, seed)
    elif pid == "q2":
        yield _case(pid, cid, kind, 4, 1 if kind == "baseline" else 2, 3, seed)
    elif pid == "q3":
        yield _case(pid, cid, kind, 4, 2, 3, seed)
    elif pid == "q4":
        yield _case(pid, cid, kind, 32, 5, 3, seed)
    else:
        yield _case(pid, cid, kind, 4, 2, 1 if kind == "baseline" else 2, seed)


def _case(pid: str, cid: str, kind: str, n: int, k: int, q: int,
          seed: int) -> Dict[str, Any]:
    seconds, sweeps = _budget(n, kind)
    return {"problem": pid, "candidate_id": cid, "kind": kind, "N": n,
            "K": k, "q": q, "seed": seed,
            "budget": {"wall_clock_s": seconds, "sweep_cap": sweeps,
                       "source": "frozen tournament protocol"}}


def _budget(n: int, kind: str) -> tuple[int, Optional[int]]:
    if kind == "baseline":
        return 60, None
    if n <= 16:
        return 300, 5000
    if n == 32:
        return 900, 15000
    return 1800, 30000


def run_plan(workspace: Path, plan: Sequence[Dict[str, Any]], *, command: str,
             smoke: bool, batch_plan: Optional[Sequence[Dict[str, Any]]] = None,
             resume: bool = False, validation_level: str = "L2") -> Dict[str, Any]:
    workspace = workspace.resolve()
    gate = check_frozen(str(workspace))
    if not gate.allowed:
        raise RuntimeError("protocol/freeze gate failed: " + "; ".join(gate.reasons))
    protocol_path = workspace / "03_model/tournament_protocol.json"
    protocol_sha = sha256_file(protocol_path)
    freeze_sha = sha256_file(workspace / "00_admin/freezes/tournament_protocol.json")
    problem_freeze_sha = sha256_file(workspace / "00_admin/freezes/problem.json")
    code_sha = _tree_sha256(workspace / "04_code")
    canonical_plan = list(batch_plan if batch_plan is not None else plan)
    batch_sha = _json_sha256(canonical_plan)
    input_manifest_path = workspace / "00_admin/input_manifest.json"
    input_manifest_sha = sha256_file(input_manifest_path)
    input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    problem_record = input_manifest["files"][0]
    problem_path = workspace / problem_record["path"]
    problem_input_sha = sha256_file(problem_path)
    if problem_input_sha != problem_record["sha256"]:
        raise RuntimeError("problem input hash differs from input_manifest")
    batch_id = batch_identity(protocol_sha, code_sha, batch_sha, smoke=smoke,
                              validation_level=validation_level)
    batch_dir = workspace / "05_results/batches" / batch_id
    plan_payload = {"schema_version": "3.0", "batch_id": batch_id,
                    "validation_level": validation_level,
                    "formal": not smoke, "tuple_count": len(canonical_plan),
                    "tuples": canonical_plan}
    config_payload = {"schema_version": "3.0", "batch_id": batch_id,
                      "validation_level": validation_level, "formal": not smoke,
                      "protocol_sha256": protocol_sha,
                      "protocol_freeze_sha256": freeze_sha,
                      "problem_freeze_sha256": problem_freeze_sha,
                      "code_tree_sha256": code_sha,
                      "input_manifest_sha256": input_manifest_sha,
                      "problem_input_sha256": problem_input_sha,
                      "data_class": problem_record["data_class"],
                      "target_generation": "deterministic formula from the practice-authorized third-party-copy problem statement",
                      "plan_content_sha256": batch_sha,
                      "stop_rule": {"patience": 50, "tolerance": 1e-10,
                                    "deadline": "monotonic in-loop",
                                    "sweep_cap": "per frozen N segment"}}
    batch_dir.mkdir(parents=True, exist_ok=True)
    plan_path, config_path = batch_dir / "plan.json", batch_dir / "config.json"
    _write_or_verify_json(plan_path, plan_payload)
    _write_or_verify_json(config_path, config_payload)
    plan_artifact = _artifact_record(plan_path, workspace)
    config_artifact = _artifact_record(config_path, workspace)
    l0 = run_l0_checks(workspace)
    _atomic_json(workspace / "05_results/l0_checks.json", l0)
    if l0["status"] != "PASS":
        raise RuntimeError("L0 checks failed; refusing tournament runs")
    root = workspace / "05_results" / ("smoke_runs" if smoke else "runs")
    completed = _completed_tuple_hashes(root, batch_id) if resume else set()
    selected = [item for item in plan if tuple_sha256(item) not in completed]
    results = [_run_case(workspace, root, item, protocol_sha, freeze_sha,
                         problem_freeze_sha, code_sha, batch_id, batch_sha,
                         plan_artifact, config_artifact, input_manifest_sha,
                         problem_record, command, smoke, validation_level)
               for item in selected]
    counts: Dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    summary = {
        "schema_version": "3.0", "status": "BLOCKED",
        "phase_status": "L2_SMOKE_COMPLETE_FORMAL_NOT_RUN" if smoke else "L2_EXECUTED_REVIEW_REQUIRED",
        "formal": not smoke, "winner_id": None,
        "protocol_sha256": protocol_sha, "protocol_freeze_sha256": freeze_sha,
        "batch_id": batch_id, "batch_config_sha256": batch_sha,
        "batch_plan_count": len(canonical_plan), "selected_count": len(plan),
        "resume_skipped_count": len(plan) - len(selected),
        "run_count": len(results), "status_counts": counts, "runs": results,
        "batch_artifacts": {"plan": plan_artifact, "config": config_artifact},
        "blocking_reason": "No winner until the complete frozen L2 grid and required L3/L4 evidence pass review.",
    }
    if smoke:
        _atomic_json(workspace / "05_results/smoke_summary.json", summary)
    else:
        # Shards must never race to overwrite a purported whole-batch summary.
        # The strict aggregator is the sole writer of l2_summary.json.
        execution_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        execution_path = (workspace / "05_results/batches" / batch_id /
                          "executions" / f"{execution_id}-{_json_sha256(plan)[:8]}.json")
        _atomic_json(execution_path, summary)
    _atomic_json(workspace / "05_results/validation_plan.json",
                 validation_framework(protocol_sha, l0, smoke_complete=smoke))
    return summary


def _run_case(workspace: Path, root: Path, case: Dict[str, Any], protocol_sha: str,
              freeze_sha: str, problem_freeze_sha: str, code_sha: str,
              batch_id: str, batch_sha: str, plan_artifact: Dict[str, Any],
              config_artifact: Dict[str, Any], input_manifest_sha: str,
              problem_record: Dict[str, Any], command: str, smoke: bool,
              validation_level: str) -> Dict[str, Any]:
    pid, cid = case["problem"], case["candidate_id"]
    n, k, q, seed = case["N"], case["K"], case["q"], case["seed"]
    config_sha = _json_sha256(case)
    run_id = generate_run_id(pid, cid, seed, protocol_sha[:8], code_sha[:8])
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    factor_path, stdout_path, stderr_path = (run_dir / "factors.json",
                                              run_dir / "stdout.txt",
                                              run_dir / "stderr.txt")
    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    clock = time.perf_counter()
    status, failure, values = "CRASH", None, {}
    try:
        target = kron(dft_matrix(4), dft_matrix(8)) if pid == "q4" else dft_matrix(n)
        solution = _solution(case, target, smoke)
        if len(solution.factors) != k:
            raise ValueError(f"constructed K={len(solution.factors)}, expected K={k}")
        if sorted(solution.permutation) != list(range(n)):
            raise ValueError("invalid pure permutation")
        for factor in solution.factors:
            check_finite_square(factor)
        approximation = approximate_matrix(solution.factors, solution.permutation)
        right_associated = apply_permutation_right(
            _right_associated_product(solution.factors), solution.permutation)
        association_delta = max_abs_difference(approximation, right_associated)
        search_rmse = rmse(target, approximation)
        row_cap = None if pid == "q2" else 2
        row_errors, alphabet_errors = [], []
        if row_cap is not None:
            for index, factor in enumerate(solution.factors):
                ok, errors = check_row_sparse(factor, row_cap)
                if not ok:
                    row_errors.extend(f"factor {index}: {e}" for e in errors)
        if pid != "q1":
            for index, factor in enumerate(solution.factors):
                ok, errors = check_alphabet(factor, q)
                if not ok:
                    alphabet_errors.extend(f"factor {index}: {e}" for e in errors)
        bound = support_rmse_lower_bound(n, k) if row_cap is not None else None
        bound_ok = bound is None or search_rmse + 1e-10 >= bound
        write_factor_artifact(factor_path, solution.factors, solution.permutation, q)
        independent = verify_artifact(factor_path, pid, n, q, row_cap)
        target_hash = canonical_matrix_sha256(target)
        factor_hashes = [canonical_matrix_sha256(factor) for factor in solution.factors]
        l_value = count_nontrivial_positions(solution.factors)
        c_value = hardware_complexity(solution.factors, q)
        recompute_ok = (abs(search_rmse - independent["rmse"]) <= 1e-10
                        and target_hash == independent["target_sha256"]
                        and factor_hashes == independent["factor_sha256s"]
                        and l_value == independent["L"] and c_value == independent["C"])
        exact_ok = pid != "q1" or cid not in BASELINES or max_abs_difference(target, approximation) <= 1e-10
        legal = (not row_errors and not alphabet_errors and bound_ok and recompute_ok
                 and exact_ok and association_delta <= 1e-10)
        if not legal:
            status = "CONSTRAINT_FAIL"
            failure = {"stage": "independent verification", "error_type": status,
                       "message": "constraint, hash, or independent metric mismatch"}
        elif pid == "q5" and search_rmse > 0.1:
            status = "INFEASIBLE"
            failure = {"stage": "q5 eligibility", "error_type": status,
                       "message": "legal chain has RMSE>0.1"}
        else:
            status = "PASS"
        values = {"target_sha256": target_hash, "factor_sha256s": factor_hashes,
                  "rmse": search_rmse, "rmse_recompute_independent": independent["rmse"],
                  "L": l_value, "C": c_value, "diagnostics": solution.diagnostics,
                  "constraint_checks": {"finite_square": True,
                    "permutation": "PASS", "row_support": {"status": "PASS" if not row_errors else "FAIL", "errors": row_errors},
                    "alphabet": {"status": "NOT_APPLICABLE" if pid == "q1" else ("PASS" if not alphabet_errors else "FAIL"), "errors": alphabet_errors},
                    "support_lower_bound": {"status": "NOT_APPLICABLE" if bound is None else ("PASS" if bound_ok else "FAIL"), "value": bound},
                    "target_hash_match": target_hash == independent["target_sha256"],
                    "factor_hash_match": factor_hashes == independent["factor_sha256s"],
                    "independent_metric_match": recompute_ok, "q1_exact_check": exact_ok,
                    "association_max_delta": association_delta}}
    except Exception as exc:
        failure = {"stage": "candidate execution", "error_type": type(exc).__name__, "message": str(exc)}
        _write_text_lf(stderr_path, f"{type(exc).__name__}: {exc}\n")
    elapsed = time.perf_counter() - clock
    internal_stop = values.get("diagnostics", {}).get("stop_reason")
    if elapsed > case["budget"]["wall_clock_s"] or internal_stop == "wall_deadline":
        status = "TIMEOUT"
        failure = {"stage": "budget", "error_type": status,
                   "message": "candidate exceeded frozen wall-clock cap"}
    if not stderr_path.exists():
        _write_text_lf(stderr_path, "")
    _write_text_lf(stdout_path, f"run_id={run_id}\nproblem={pid}\ncandidate={cid}\nN={n}\nK={k}\nq={q}\nseed={seed}\nstatus={status}\n")
    manifest = {
        "schema_version": "3.0", "run_id": run_id, "problem_id": pid,
        "problem": pid, "candidate_id": cid, "N": n, "K": k, "q": q,
        "beta": 1, "seed": seed, "budget": case["budget"], "wall_clock_s": elapsed,
        "status": status, "constraints_status": "PASS" if status in {"PASS", "INFEASIBLE"} else "FAIL",
        "failure": failure, "formal": not smoke, "run_scope": "SMOKE" if smoke else "FROZEN_L2",
        "optimality_claim": "exact analytic construction" if pid == "q1" and cid in BASELINES and status == "PASS" else "candidate_only_no_global_optimality_claim",
        "target_sha256": values.get("target_sha256"), "factor_sha256s": values.get("factor_sha256s"),
        "constraint_checks": values.get("constraint_checks"), "rmse": values.get("rmse"),
        "rmse_recompute_independent": values.get("rmse_recompute_independent"),
        "L": values.get("L"), "C": values.get("C"), "diagnostics": values.get("diagnostics"),
        "started_at": started, "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "protocol_sha256": protocol_sha, "protocol_freeze_sha256": freeze_sha,
        "problem_freeze_sha256": problem_freeze_sha, "code_tree_sha256": code_sha,
        "batch_id": batch_id, "batch_config_sha256": batch_sha,
        "run_config_sha256": config_sha,
        "tuple_sha256": tuple_sha256(case), "validation_level": validation_level,
        "parent_run_id": case.get("parent_run_id"), "variant": case.get("variant"),
        "batch_artifacts": {"plan": plan_artifact, "config": config_artifact},
        "input_manifest_sha256": input_manifest_sha,
        "problem_input": {"path": problem_record["path"],
                          "sha256": problem_record["sha256"],
                          "data_class": problem_record["data_class"],
                          "provenance_status": problem_record.get("provenance_status")},
        "data_class": problem_record["data_class"],
        "target_generation": "deterministic formula from the practice-authorized third-party-copy problem statement",
        "command": command, "environment": {"python": sys.version,
            "implementation": platform.python_implementation(), "platform": platform.platform(),
            "dependencies": {"third_party": [], "standard_library_only": True}},
        "artifacts": {"factors": _artifact_record(factor_path, workspace) if factor_path.exists() else None,
                      "stdout": _artifact_record(stdout_path, workspace),
                      "stderr": _artifact_record(stderr_path, workspace)},
    }
    _atomic_json(run_dir / "run_manifest.json", manifest)
    summary = {key: manifest[key] for key in ("run_id", "problem", "candidate_id", "N", "K", "q", "seed", "status", "constraints_status", "rmse", "L", "C", "wall_clock_s")}
    summary["run_manifest"] = (run_dir / "run_manifest.json").relative_to(workspace).as_posix()
    return summary


def _solution(case: Dict[str, Any], target: Any, smoke: bool):
    pid, cid = case["problem"], case["candidate_id"]
    n, k, q, seed = case["N"], case["K"], case["q"], case["seed"]
    if cid not in BASELINES:
        if smoke:
            budget = SearchBudget.frozen(n, smoke=True)
        else:
            tolerance = float(case.get("variant", {}).get("tolerance", 1e-10))
            budget = SearchBudget(float(case["budget"]["wall_clock_s"]),
                                  int(case["budget"]["sweep_cap"]),
                                  patience=50, tolerance=tolerance)
        return challenger_solution(cid, target, n, k, q, seed, smoke=smoke,
                                   budget=budget)
    if pid == "q1":
        return exact_q1_baseline(n)
    if pid == "q2":
        return onefactor_quantized_baseline(target, q)
    if pid == "q3":
        return quantized_butterfly_baseline(n, q, polish=True)
    if pid == "q4":
        return kron_quantized_butterfly_baseline(q)
    return q1_cost_baseline(n, k)


def validation_framework(protocol_sha: str, l0: Dict[str, Any], *,
                         smoke_complete: bool) -> Dict[str, Any]:
    return {"schema_version": "3.0", "status": "BLOCKED", "winner_id": None,
            "protocol_sha256": protocol_sha,
            "levels": {
                "L0": {"status": l0["status"], "evidence": "05_results/l0_checks.json"},
                "L1": {"status": "COMPLETE_BUT_Q1_SUPERSEDED", "reason": "legacy runs retained; q1 L/C must be regenerated after single-factor scale fix"},
                "L2": {"status": "SMOKE_ONLY" if smoke_complete else "NOT_RUN", "required": "complete frozen 1442-run plan with all failures retained"},
                "L3": {"status": "NOT_RUN", "axes": ["seed", "initialization_order", "floating_tolerance", "multiplication_association", "boundary_K_q"], "report": ["best", "median", "worst"]},
                "L4": {"status": "NOT_RUN", "ablations": ["no_hierarchical_initialization", "no_support_reconnection", "no_discrete_polish", "fixed_vs_reconnectable_support"]}},
            "blocking_reason": "Formal L2, L3 robustness, and L4 ablation are incomplete."}


def _json_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def tuple_sha256(case: Dict[str, Any]) -> str:
    identity = {key: case.get(key) for key in
                ("problem", "candidate_id", "N", "K", "q", "seed",
                 "validation_level", "parent_run_id", "variant")}
    return _json_sha256(identity)


def shard_plan(plan: Sequence[Dict[str, Any]], shard_index: int,
               shard_count: int) -> List[Dict[str, Any]]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("require shard_count>=1 and 0<=shard_index<shard_count")
    return [case for case in plan
            if int(tuple_sha256(case), 16) % shard_count == shard_index]


def batch_identity(protocol_sha: str, code_sha: str, plan_sha: str, *,
                   smoke: bool, validation_level: str) -> str:
    prefix = validation_level.lower() + ("-smoke" if smoke else "")
    stable = f"{prefix}-{protocol_sha[:8]}-{code_sha[:8]}-{plan_sha[:8]}"
    if not smoke:
        return stable
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stable}-{stamp}"


def _write_or_verify_json(path: Path, payload: Dict[str, Any]) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError(f"existing batch artifact differs: {path}")
        return
    # Unique temporary names make simultaneous shard startup safe.  Replacing
    # the same target is harmless because every shard carries identical bytes.
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8", newline="\n")
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != payload:
                raise RuntimeError(f"existing batch artifact differs: {path}")
        else:
            os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _completed_tuple_hashes(root: Path, batch_id: str) -> set[str]:
    completed: set[str] = set()
    if not root.exists():
        return completed
    for path in root.glob("*/run_manifest.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if manifest.get("batch_id") == batch_id and manifest.get("tuple_sha256"):
            completed.add(manifest["tuple_sha256"])
    return completed


def _right_associated_product(factors: Sequence[Any]):
    if not factors:
        raise ValueError("empty factor chain")
    result = [row[:] for row in factors[-1]]
    for factor in reversed(factors[:-1]):
        result = matmul(factor, result)
    return result

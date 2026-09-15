# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: every run is gate-checked, immutable, constraint-checked, and independently recomputed.
"""Formal L0/L1 runner for every deterministic baseline in the frozen protocol."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .baselines import (
    approximate_matrix,
    exact_q1_baseline,
    kron_quantized_butterfly_baseline,
    onefactor_quantized_baseline,
    q1_cost_baseline,
    quantized_butterfly_baseline,
)
from .constraints import check_alphabet, check_finite_square, check_row_sparse
from .factor_artifacts import write_factor_artifact
from .hardware import count_nontrivial_positions, hardware_complexity
from .hashing import sha256_file
from .independent_verify import verify_artifact
from .l0_validation import run_l0_checks, support_rmse_lower_bound
from .metrics import max_abs_difference, rmse
from .protocol_gate import check_frozen
from .provenance import generate_run_id
from .serialization import canonical_matrix_sha256, canonical_matrix_sha256 as matrix_hash
from .targets import dft_matrix, kron


def run_all(workspace: Path, command: str) -> Dict[str, Any]:
    workspace = workspace.resolve()
    gate = check_frozen(str(workspace))
    if not gate.allowed:
        raise RuntimeError("protocol/freeze gate failed: " + "; ".join(gate.reasons))

    protocol_path = workspace / "03_model/tournament_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol_sha = sha256_file(protocol_path)
    freeze_sha = sha256_file(workspace / "00_admin/freezes/tournament_protocol.json")
    problem_freeze_sha = sha256_file(workspace / "00_admin/freezes/problem.json")
    code_sha = _tree_sha256(workspace / "04_code")

    l0 = run_l0_checks(workspace)
    _atomic_json(workspace / "05_results/l0_checks.json", l0)
    if l0["status"] != "PASS":
        raise RuntimeError("L0 checks failed; refusing baselines")

    previous_runs: List[Dict[str, Any]] = []
    metrics_path = workspace / "05_results/metrics.json"
    if metrics_path.is_file():
        previous_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        if isinstance(previous_payload.get("runs"), list):
            previous_runs = previous_payload["runs"]
    new_run_summaries = []
    for instance in _instances(protocol):
        summary = _run_instance(
            workspace,
            instance,
            protocol_sha,
            freeze_sha,
            problem_freeze_sha,
            code_sha,
            command,
        )
        new_run_summaries.append(summary)

    run_summaries = previous_runs + new_run_summaries

    metrics = {
        "schema_version": "3.0",
        "status": "BLOCKED",
        "phase_status": "DETERMINISTIC_BASELINES_COMPLETE_CHALLENGERS_NOT_RUN",
        "data_class": "third_party_copy",
        "target_generation": "deterministic formula from the practice-authorized third-party-copy problem statement",
        "historical_note": "All earlier run directories are retained. The first batch exposed a q4 signed-zero sparse-serialization hash mismatch and retains that run as CONSTRAINT_FAIL; every baseline was rerun after correction. latest_batch_run_ids is the current evidence set.",
        "protocol_sha256": protocol_sha,
        "protocol_freeze_sha256": freeze_sha,
        "runs": run_summaries,
        "latest_batch_run_ids": [run["run_id"] for run in new_run_summaries],
        "historical_runs_retained": len(previous_runs),
        "blocking_reason": "Only L0/L1 deterministic baselines are complete; L2 challengers, L3 robustness, and L4 ablation are NOT_RUN.",
    }
    _atomic_json(workspace / "05_results/metrics.json", metrics)

    by_problem: Dict[str, List[Dict[str, Any]]] = {}
    for run in run_summaries:
        by_problem.setdefault(run["problem"], []).append(run)
    tournament = {
        "schema_version": "3.0",
        "status": "BLOCKED",
        "phase_status": "BASELINES_ONLY",
        "winner_policy": "No winner is selected until every frozen challenger completes L2 and required L3/L4 evidence exists.",
        "problems": [
            {
                "id": problem_id,
                "winner_id": None,
                "evaluated_candidates": sorted({run["candidate_id"] for run in runs}),
                "baseline_runs": [run["run_id"] for run in runs],
                "baseline_status_counts": _status_counts(runs),
                "challengers": "NOT_RUN",
                "robustness_status": "NOT_RUN",
                "ablation_status": "NOT_RUN",
            }
            for problem_id, runs in sorted(by_problem.items())
        ],
    }
    _atomic_json(workspace / "05_results/tournament.json", tournament)
    _write_results_report(workspace, run_summaries, protocol_sha, freeze_sha, command)
    return {
        "l0": l0,
        "runs": new_run_summaries,
        "all_runs": run_summaries,
        "metrics": metrics,
        "tournament": tournament,
    }


def _run_instance(
    workspace: Path,
    instance: Dict[str, Any],
    protocol_sha: str,
    freeze_sha: str,
    problem_freeze_sha: str,
    code_sha: str,
    command: str,
) -> Dict[str, Any]:
    problem_id = instance["problem"]
    candidate_id = instance["candidate_id"]
    n, k, q, seed = instance["N"], instance["K"], instance["q"], 0
    run_id = generate_run_id(problem_id, candidate_id, seed, protocol_sha[:8], code_sha[:8])
    run_dir = workspace / "05_results/runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    factor_path = run_dir / "factors.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    start_clock = time.perf_counter()
    failure = None
    status = "FAIL"
    values: Dict[str, Any] = {}
    try:
        target = kron(dft_matrix(4), dft_matrix(8)) if problem_id == "q4" else dft_matrix(n)
        if problem_id == "q1":
            solution = exact_q1_baseline(n)
        elif problem_id == "q2":
            solution = onefactor_quantized_baseline(target, q)
        elif problem_id == "q3":
            solution = quantized_butterfly_baseline(n, q, polish=True)
        elif problem_id == "q4":
            solution = kron_quantized_butterfly_baseline(q)
        elif problem_id == "q5":
            solution = q1_cost_baseline(n, k)
        else:
            raise ValueError(f"unknown problem {problem_id}")

        if len(solution.factors) != k:
            raise ValueError(f"constructed K={len(solution.factors)}, expected {k}")
        for factor in solution.factors:
            check_finite_square(factor)
        approximation = approximate_matrix(solution.factors, solution.permutation)
        search_rmse = rmse(target, approximation)
        target_sha = canonical_matrix_sha256(target)
        factor_hashes = [matrix_hash(factor) for factor in solution.factors]
        row_cap = None if problem_id == "q2" else 2
        row_errors = []
        if row_cap is not None:
            for factor_index, factor in enumerate(solution.factors):
                ok, errors = check_row_sparse(factor, row_cap)
                if not ok:
                    row_errors.extend(f"factor {factor_index}: {error}" for error in errors)
        alphabet_errors = []
        if problem_id != "q1":
            for factor_index, factor in enumerate(solution.factors):
                ok, errors = check_alphabet(factor, q)
                if not ok:
                    alphabet_errors.extend(f"factor {factor_index}: {error}" for error in errors)
        l_value = count_nontrivial_positions(solution.factors)
        c_value = hardware_complexity(solution.factors, q)
        bound = support_rmse_lower_bound(n, k) if row_cap is not None else None
        bound_ok = bound is None or search_rmse + 1e-10 >= bound
        write_factor_artifact(factor_path, solution.factors, solution.permutation, q)
        independent = verify_artifact(factor_path, problem_id, n, q, row_cap)
        independent_delta = abs(search_rmse - independent["rmse"])
        target_hash_ok = target_sha == independent["target_sha256"]
        factor_hash_ok = factor_hashes == independent["factor_sha256s"]
        counts_ok = l_value == independent["L"] and c_value == independent["C"]
        constraints_ok = not row_errors and not alphabet_errors and bound_ok
        recompute_ok = independent_delta <= 1e-10 and target_hash_ok and factor_hash_ok and counts_ok
        if problem_id == "q1" and max_abs_difference(target, approximation) > 1e-10:
            constraints_ok = False
            row_errors.append("exact q1 baseline max-entry residual exceeds 1e-10")
        if not constraints_ok or not recompute_ok:
            status = "CONSTRAINT_FAIL"
            failure = {
                "stage": "L1 independent verification",
                "error_type": "CONSTRAINT_FAIL",
                "message": "baseline failed a constraint or independent recomputation check",
            }
        elif problem_id == "q5" and search_rmse > 0.1:
            status = "INFEASIBLE"
            failure = {
                "stage": "q5 eligibility",
                "error_type": "INFEASIBLE",
                "message": "legal baseline has RMSE>0.1; retained as an infeasible run",
            }
        else:
            status = "PASS"
        values = {
            "target_sha256": target_sha,
            "factor_sha256s": factor_hashes,
            "constraint_checks": {
                "finite_square": True,
                "row_support": {"status": "PASS" if not row_errors else "FAIL", "errors": row_errors},
                "alphabet": {"status": "NOT_APPLICABLE" if problem_id == "q1" else ("PASS" if not alphabet_errors else "FAIL"), "errors": alphabet_errors},
                "support_lower_bound": {"status": "NOT_APPLICABLE" if bound is None else ("PASS" if bound_ok else "FAIL"), "value": bound},
                "target_hash_match": target_hash_ok,
                "factor_hash_match": factor_hash_ok,
                "independent_counts_match": counts_ok,
                "independent_rmse_delta": independent_delta,
            },
            "rmse": search_rmse,
            "rmse_recompute_independent": independent["rmse"],
            "L": l_value,
            "C": c_value,
            "diagnostics": solution.diagnostics,
        }
    except Exception as exc:  # retain every failed formal run
        failure = {"stage": "L1 baseline", "error_type": type(exc).__name__, "message": str(exc)}
        _write_text_lf(stderr_path, f"{type(exc).__name__}: {exc}\n")
    wall_clock = time.perf_counter() - start_clock
    if not stderr_path.exists():
        _write_text_lf(stderr_path, "")
    _write_text_lf(
        stdout_path,
        f"run_id={run_id}\nproblem={problem_id}\ncandidate={candidate_id}\nN={n}\nK={k}\nq={q}\nstatus={status}\n",
    )
    manifest = {
        "schema_version": "3.0",
        "run_id": run_id,
        "problem_id": problem_id,
        "problem": problem_id,
        "candidate_id": candidate_id,
        "N": n,
        "target_sha256": values.get("target_sha256"),
        "q": q,
        "K": k,
        "beta": 1,
        "factor_sha256s": values.get("factor_sha256s"),
        "constraint_checks": values.get("constraint_checks"),
        "rmse": values.get("rmse"),
        "rmse_recompute_independent": values.get("rmse_recompute_independent"),
        "L": values.get("L"),
        "C": values.get("C"),
        "seed": seed,
        "budget": {"wall_clock_s": 60, "source": "frozen protocol deterministic_baseline"},
        "wall_clock_s": wall_clock,
        "status": status,
        "constraints_status": "PASS" if status in {"PASS", "INFEASIBLE"} else "FAIL",
        "optimality_claim": "exact analytic construction" if problem_id == "q1" and status == "PASS" else "baseline_only_no_global_optimality_claim",
        "failure": failure,
        "formal": True,
        "data_class": "third_party_copy",
        "target_generation": "deterministic formula from the practice-authorized third-party-copy problem statement",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "protocol_sha256": protocol_sha,
        "protocol_freeze_sha256": freeze_sha,
        "problem_freeze_sha256": problem_freeze_sha,
        "code_tree_sha256": code_sha,
        "command": command,
        "environment": {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "dependencies": {"third_party": [], "standard_library_only": True},
        },
        "artifacts": {
            "factors": _artifact_record(factor_path, workspace) if factor_path.exists() else None,
            "stdout": _artifact_record(stdout_path, workspace),
            "stderr": _artifact_record(stderr_path, workspace),
        },
        "diagnostics": values.get("diagnostics"),
    }
    _atomic_json(run_dir / "run_manifest.json", manifest)
    return {
        "run_id": run_id,
        "problem_id": problem_id,
        "problem": problem_id,
        "candidate_id": candidate_id,
        "N": n,
        "K": k,
        "q": q,
        "seed": seed,
        "status": status,
        "constraints_status": "PASS" if status in {"PASS", "INFEASIBLE"} else "FAIL",
        "rmse": values.get("rmse"),
        "rmse_recompute_independent": values.get("rmse_recompute_independent"),
        "L": values.get("L"),
        "C": values.get("C"),
        "wall_clock_s": wall_clock,
        "run_manifest": (run_dir / "run_manifest.json").relative_to(workspace).as_posix(),
    }


def _instances(protocol: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    problems = {problem["id"]: problem for problem in protocol["problems"]}
    for n in problems["q1"]["instances"]["N"]:
        yield {"problem": "q1", "candidate_id": "q1-b0-scaled-radix2", "N": n, "K": n.bit_length() - 1, "q": 16}
    for n in problems["q2"]["instances"]["N"]:
        yield {"problem": "q2", "candidate_id": "q2-b0-onefactor-quantize", "N": n, "K": 1, "q": 3}
    for n in problems["q3"]["instances"]["N"]:
        yield {"problem": "q3", "candidate_id": "q3-b0-quantized-butterfly", "N": n, "K": n.bit_length() - 1, "q": 3}
    q4 = problems["q4"]["instances"]
    yield {"problem": "q4", "candidate_id": "q4-b0-kron-butterfly", "N": q4["N"], "K": 5, "q": q4["q"]}
    for n in problems["q5"]["instances"]["N"]:
        max_k = min(8, n.bit_length() - 1 + 2)
        for k in range(1, max_k + 1):
            yield {"problem": "q5", "candidate_id": "q5-b0-q1-butterfly", "N": n, "K": k, "q": 1}


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "little"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()


def _artifact_record(path: Path, workspace: Path) -> Dict[str, Any]:
    return {"path": path.relative_to(workspace).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)}


def _status_counts(runs: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for run in runs:
        counts[run["status"]] = counts.get(run["status"], 0) + 1
    return counts


def _atomic_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    _write_text_lf(temporary, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def _write_text_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _write_results_report(workspace: Path, runs: List[Dict[str, Any]], protocol_sha: str, freeze_sha: str, command: str) -> None:
    latest_count = 50
    historical_count = max(0, len(runs) - latest_count)
    lines = [
        "# 基线阶段结果报告",
        "",
        "状态：`BLOCKED`。L0 与全部确定性基线已运行；挑战者、稳健性和消融仍为 `NOT_RUN`，因此不宣布最终胜者。",
        "",
        f"- 协议 SHA-256：`{protocol_sha}`",
        f"- 协议冻结 SHA-256：`{freeze_sha}`",
        f"- 复现命令：`{command}`",
        f"- run 数：{len(runs)}",
        f"- 当前证据批次：末尾 {latest_count} 个新 run；更早 {historical_count} 个 run 按不可删除原则保留。",
        "- 历史说明：首批 q4 暴露稀疏 JSON 未保存 IEEE-754 负零符号导致的因子字节哈希不一致，原 run 保持 CONSTRAINT_FAIL；修正后所有 baseline 均从头重跑。",
        "",
        "| problem | N | K | q | status | RMSE | L | C | run-id |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for run in runs:
        rmse_text = "null" if run["rmse"] is None else f"{run['rmse']:.15g}"
        lines.append(
            f"| {run['problem']} | {run['N']} | {run['K']} | {run['q']} | {run['status']} | {rmse_text} | {run['L']} | {run['C']} | `{run['run_id']}` |"
        )
    lines.extend([
        "",
        "所有数值均来自本轮新 run，并在各自 `run_manifest.json` 中绑定目标、因子、代码树、协议及冻结哈希。独立复算从持久化稀疏因子文件重新加载并计算。",
        "",
        "问题 5 中 `INFEASIBLE` 表示因子合法但 `RMSE>0.1`；它不是运行失败，也不得被当作胜者。",
        "",
    ])
    _write_text_lf(workspace / "05_results/RESULTS_REPORT.md", "\n".join(lines))

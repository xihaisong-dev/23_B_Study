# AI-assisted development disclosure (D-011)
# Tool/model: DeepSeek Harness, deepseek-v4-flash
# Developer/provider: DeepSeek
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification required: every run is gate-checked, constrained, independently
# recomputed, hashed and retained; failures are never deleted.
"""Formal L2 runner for the challengers registered in the frozen protocol.

Mirrors :mod:`dft_integer_approx.formal_baseline_runner` exactly in its gate, artifact,
independent-verification and manifest conventions, so a challenger run and a baseline run
are directly comparable:

* same gate (``protocol_gate.check_frozen`` refuses unless the D-012 freeze verifies);
* same run directory layout ``05_results/runs/<run-id>/{factors.json,run_manifest.json,
  stdout.txt,stderr.txt}`` with ``exist_ok=False`` (nothing is ever overwritten);
* same constraint checks (finite square, row sparsity, ``P_q`` alphabet, support bound),
  same ``L``/``C`` counters, same independent recomputation via ``verify_artifact``;
* same status vocabulary ``PASS`` / ``INFEASIBLE`` / ``CONSTRAINT_FAIL`` / ``FAIL``.

Differences, all forced by the protocol: stochastic candidates run under seeds
``{17, 43, 71}`` (deterministic baselines stay at seed ``0``), and the K grid follows the
frozen ``instances`` per problem rather than a single prescribed K.

Run from the repository root:

    python -X utf8 04_code/scripts/run_challengers.py --problem q5 --max-n 16
    python -X utf8 04_code/scripts/run_challengers.py --dry-run
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

if __package__ in (None, ""):  # allow direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.baselines import approximate_matrix  # noqa: E402
from dft_integer_approx.challengers import (  # noqa: E402
    challenger_solution,
    registered_challenger_ids,
)
from dft_integer_approx.constraints import (  # noqa: E402
    check_alphabet,
    check_finite_square,
    check_row_sparse,
)
from dft_integer_approx.factor_artifacts import write_factor_artifact  # noqa: E402
from dft_integer_approx.hardware import (  # noqa: E402
    count_nontrivial_positions,
    hardware_complexity,
)
from dft_integer_approx.hashing import sha256_file  # noqa: E402
from dft_integer_approx.independent_verify import verify_artifact  # noqa: E402
from dft_integer_approx.l0_validation import support_rmse_lower_bound  # noqa: E402
from dft_integer_approx.metrics import max_abs_difference, rmse  # noqa: E402
from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402
from dft_integer_approx.provenance import generate_run_id  # noqa: E402
from dft_integer_approx.serialization import (  # noqa: E402
    canonical_matrix_sha256,
    canonical_matrix_sha256 as matrix_sha256,
)
from dft_integer_approx.targets import dft_matrix, kron  # noqa: E402

STOCHASTIC_SEEDS = (17, 43, 71)
WALL_CLOCK_BUDGET = {  # frozen protocol, per (problem, N)
    "q1": {2: 60, 4: 60, 8: 60, 16: 60, 32: 60, 64: 60},
}
DEFAULT_BUDGET = {2: 60, 4: 60, 8: 60, 16: 300, 32: 900, 64: 1800}
RUNS_DIR = Path("05_results/runs")


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _atomic_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
                   encoding="utf-8")
    tmp.replace(path)


def _write_text_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _artifact_record(path: Path, workspace: Path) -> Dict[str, Any]:
    return {
        "path": path.relative_to(workspace).as_posix(),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def instances(protocol: Dict[str, Any], only: Optional[List[str]],
              max_n: Optional[int]) -> Iterable[Dict[str, Any]]:
    """Expand the frozen protocol into challenger instances."""
    problems = {p["id"]: p for p in protocol["problems"]}
    for pid in ("q1", "q2", "q3", "q4", "q5"):
        if only and pid not in only:
            continue
        problem = problems[pid]
        challengers = [c["id"] for c in problem["candidates"] if c["kind"] == "challenger"]
        instances_cfg = problem["instances"]
        ns = instances_cfg.get("N")
        ns = [ns] if isinstance(ns, int) else list(ns)
        for n in ns:
            if max_n is not None and n > max_n:
                continue
            if pid == "q1":
                ks = [n.bit_length() - 1]
                qs = [16]
            elif pid == "q2":
                ks = list(instances_cfg["K_grid"])
                qs = [instances_cfg["q"]]
            elif pid == "q3":
                ks = list(range(1, (n.bit_length() - 1) + 2 + 1))
                qs = [instances_cfg["q"]]
            elif pid == "q4":
                ks = list(instances_cfg["K_grid"])
                qs = [instances_cfg["q"]]
            else:
                ks = list(range(1, min(8, n.bit_length() - 1 + 2) + 1))
                qs = list(instances_cfg["q_grid"])
            for cid in challengers:
                for q in qs:
                    for k in ks:
                        for seed in STOCHASTIC_SEEDS:
                            yield {"problem": pid, "candidate_id": cid, "N": n,
                                   "K": k, "q": q, "seed": seed}


def run_instance(workspace: Path, instance: Dict[str, Any], protocol_sha: str,
                 freeze_sha: str, problem_freeze_sha: str, code_sha: str,
                 command: str, time_cap: Optional[float] = None) -> Dict[str, Any]:
    problem_id = instance["problem"]
    candidate_id = instance["candidate_id"]
    n, k, q, seed = instance["N"], instance["K"], instance["q"], instance["seed"]
    run_id = generate_run_id(problem_id, candidate_id, seed, protocol_sha[:8], code_sha[:8])
    run_dir = workspace / RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    factor_path = run_dir / "factors.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    started = _utc_now()
    start_clock = time.perf_counter()
    failure = None
    status = "FAIL"
    values: Dict[str, Any] = {}
    try:
        target = kron(dft_matrix(4), dft_matrix(8)) if problem_id == "q4" else dft_matrix(n)
        solution = challenger_solution(candidate_id, target, n, k, q, seed)
        if len(solution.factors) != k:
            raise ValueError(f"constructed K={len(solution.factors)}, expected {k}")
        for factor in solution.factors:
            check_finite_square(factor)
        approximation = approximate_matrix(solution.factors, solution.permutation)
        search_rmse = rmse(target, approximation)
        target_sha = canonical_matrix_sha256(target)
        factor_hashes = [matrix_sha256(f) for f in solution.factors]
        row_cap = None if problem_id == "q2" else 2
        row_errors: List[str] = []
        if row_cap is not None:
            for idx, factor in enumerate(solution.factors):
                ok, errors = check_row_sparse(factor, row_cap)
                if not ok:
                    row_errors.extend(f"factor {idx}: {e}" for e in errors)
        alphabet_errors: List[str] = []
        if problem_id != "q1":
            for idx, factor in enumerate(solution.factors):
                ok, errors = check_alphabet(factor, q)
                if not ok:
                    alphabet_errors.extend(f"factor {idx}: {e}" for e in errors)
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
        recompute_ok = (independent_delta <= 1e-10 and target_hash_ok and factor_hash_ok
                        and counts_ok)
        if not constraints_ok or not recompute_ok:
            status = "CONSTRAINT_FAIL"
            failure = {"stage": "L2 independent verification",
                       "error_type": "CONSTRAINT_FAIL",
                       "message": "challenger failed a constraint or independent check"}
        elif problem_id == "q5" and search_rmse > 0.1:
            status = "INFEASIBLE"
            failure = {"stage": "q5 eligibility", "error_type": "INFEASIBLE",
                       "message": "legal challenger has RMSE>0.1; retained as infeasible"}
        else:
            status = "PASS"
        values = {
            "target_sha256": target_sha,
            "factor_sha256s": factor_hashes,
            "constraint_checks": {
                "finite_square": True,
                "row_support": {"status": "PASS" if not row_errors else "FAIL",
                                "errors": row_errors},
                "alphabet": {"status": "NOT_APPLICABLE" if problem_id == "q1"
                             else ("PASS" if not alphabet_errors else "FAIL"),
                             "errors": alphabet_errors},
                "support_lower_bound": {"status": "NOT_APPLICABLE" if bound is None
                                        else ("PASS" if bound_ok else "FAIL"),
                                        "value": bound},
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
        failure = {"stage": "L2 challenger", "error_type": type(exc).__name__,
                   "message": str(exc)}
        _write_text_lf(stderr_path, f"{type(exc).__name__}: {exc}\n")
    wall_clock = time.perf_counter() - start_clock
    if not stderr_path.exists():
        _write_text_lf(stderr_path, "")
    _write_text_lf(stdout_path,
                   f"run_id={run_id}\nproblem={problem_id}\ncandidate={candidate_id}\n"
                   f"N={n}\nK={k}\nq={q}\nseed={seed}\nstatus={status}\n")
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
        "budget": {"wall_clock_s": time_cap, "source": "frozen protocol segmented budget"},
        "wall_clock_s": wall_clock,
        "status": status,
        "constraints_status": "PASS" if status in {"PASS", "INFEASIBLE"} else "FAIL",
        "optimality_claim": "best_found",
        "failure": failure,
        "formal": True,
        "data_class": "third_party_copy",
        "started_at": started,
        "finished_at": _utc_now(),
        "protocol_sha256": protocol_sha,
        "protocol_freeze_sha256": freeze_sha,
        "problem_freeze_sha256": problem_freeze_sha,
        "code_tree_sha256": code_sha,
        "command": command,
        "environment": {"python": sys.version,
                        "implementation": platform.python_implementation(),
                        "platform": platform.platform(),
                        "dependencies": {"third_party": [], "standard_library_only": True}},
        "artifacts": {
            "factors": _artifact_record(factor_path, workspace) if factor_path.exists() else None,
            "stdout": _artifact_record(stdout_path, workspace),
            "stderr": _artifact_record(stderr_path, workspace),
        },
        "diagnostics": values.get("diagnostics"),
    }
    _atomic_json(run_dir / "run_manifest.json", manifest)
    return {
        "run_id": run_id, "problem": problem_id, "candidate_id": candidate_id,
        "N": n, "K": k, "q": q, "seed": seed, "status": status,
        "constraints_status": manifest["constraints_status"],
        "rmse": values.get("rmse"),
        "rmse_recompute_independent": values.get("rmse_recompute_independent"),
        "L": values.get("L"), "C": values.get("C"), "wall_clock_s": wall_clock,
        "run_manifest": (run_dir / "run_manifest.json").relative_to(workspace).as_posix(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", action="append")
    ap.add_argument("--max-n", type=int)
    ap.add_argument("--candidate", action="append")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    workspace = Path(".").resolve()
    gate = check_frozen(str(workspace))
    print("gate allowed =", gate.allowed)
    for reason in gate.reasons:
        print("  -", reason)
    if not gate.allowed:
        print("Refusing to run challengers (protocol not frozen).")
        return 1

    protocol_path = workspace / "03_model" / "tournament_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol_sha = sha256_file(protocol_path)
    freeze_sha = sha256_file(workspace / "00_admin/freezes/tournament_protocol.json")
    problem_freeze_sha = sha256_file(workspace / "00_admin/freezes/problem.json")
    code_sha = _tree_sha256(workspace / "04_code" / "src")

    plan = list(instances(protocol, args.problem, args.max_n))
    if args.candidate:
        wanted = set(args.candidate)
        plan = [i for i in plan if i["candidate_id"] in wanted]
    if args.limit:
        plan = plan[:args.limit]
    print(f"planned challenger runs: {len(plan)}")
    for row in plan[:8]:
        print("   ", row)
    if args.dry_run:
        return 0

    command = "python -X utf8 " + " ".join(sys.argv)
    summaries: List[Dict[str, Any]] = []
    started = time.perf_counter()
    for index, instance in enumerate(plan, 1):
        cap = DEFAULT_BUDGET.get(instance["N"], 60)
        summary = run_instance(workspace, instance, protocol_sha, freeze_sha,
                               problem_freeze_sha, code_sha, command, cap)
        summaries.append(summary)
        if not args.quiet:
            print(f"[{index}/{len(plan)}] {instance['problem']} N={instance['N']} "
                  f"K={instance['K']} q={instance['q']} {instance['candidate_id']} "
                  f"s={instance['seed']} -> {summary['status']} rmse={summary['rmse']} "
                  f"L={summary['L']} C={summary['C']}", flush=True)
    elapsed = time.perf_counter() - started
    counts: Dict[str, int] = {}
    for s in summaries:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    report = {
        "role": "compute",
        "stage": "L2_challengers",
        "protocol_sha256": protocol_sha,
        "protocol_freeze_sha256": freeze_sha,
        "code_tree_sha256": code_sha,
        "command": command,
        "wall_clock_s": elapsed,
        "run_count": len(summaries),
        "status_counts": counts,
        "runs": summaries,
        "generated_at": _utc_now(),
    }
    out = workspace / "05_results" / "challenger_runs.json"
    _atomic_json(out, report)
    print(json.dumps({k: v for k, v in report.items() if k != "runs"},
                     ensure_ascii=False, indent=2))
    print(f"wrote {out.relative_to(workspace).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: this is a non-formal small-budget readiness measurement only.
"""Run one representative N=64 challenger with an explicitly non-formal budget."""

from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE / "04_code/src"))

from dft_integer_approx.formal_baseline_runner import _atomic_json, _tree_sha256  # noqa: E402
from dft_integer_approx.hashing import sha256_file  # noqa: E402
from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402


def _worker(queue) -> None:
    from dft_integer_approx.challengers import challenger_solution
    from dft_integer_approx.independent_search_score import independent_objective
    from dft_integer_approx.search_budget import SearchBudget
    from dft_integer_approx.targets import dft_matrix

    target = dft_matrix(64)
    budget = SearchBudget(wall_clock_s=5.0, sweep_cap=1, patience=1, tolerance=1e-10)
    started = time.perf_counter()
    solution = challenger_solution("q1-c1-palm-row2", target, 64, 6, 16, 17,
                                   smoke=False, budget=budget)
    queue.put({"wall_clock_s": time.perf_counter() - started,
               "rmse_independent_search_scorer": independent_objective(
                   target, solution.factors, solution.permutation) ** 0.5 / 64,
               "diagnostics": solution.diagnostics})


def main() -> int:
    gate = check_frozen(str(WORKSPACE))
    if not gate.allowed:
        raise RuntimeError("freeze gate failed: " + "; ".join(gate.reasons))
    started = time.perf_counter()
    context = mp.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_worker, args=(queue,))
    process.start()
    process.join(12.0)
    if process.is_alive():
        process.terminate()
        process.join(5.0)
        measurement = {"wall_clock_s": time.perf_counter() - started,
                       "rmse_independent_search_scorer": None,
                       "diagnostics": {"stop_reason": "hard_process_deadline",
                                       "performance_blocker": True}}
        status = "NON_FORMAL_READINESS_OVERRUN"
    elif process.exitcode != 0 or queue.empty():
        measurement = {"wall_clock_s": time.perf_counter() - started,
                       "rmse_independent_search_scorer": None,
                       "diagnostics": {"stop_reason": "worker_failure",
                                       "worker_exitcode": process.exitcode,
                                       "performance_blocker": True}}
        status = "NON_FORMAL_READINESS_FAIL"
    else:
        measurement = queue.get()
        status = "NON_FORMAL_READINESS_ONLY"
    result = {"schema_version": "3.0", "status": status,
              "formal": False, "problem": "q1", "candidate_id": "q1-c1-palm-row2",
              "N": 64, "K": 6, "q": 16, "seed": 17,
              "budget": {"in_loop_wall_clock_s": 5.0, "hard_process_deadline_s": 12.0,
                         "sweep_cap": 1, "patience": 1, "tolerance": 1e-10},
              **measurement,
              "protocol_sha256": sha256_file(WORKSPACE / "03_model/tournament_protocol.json"),
              "code_tree_sha256": _tree_sha256(WORKSPACE / "04_code"),
              "created_at": datetime.now(timezone.utc).isoformat(),
              "warning": "Not comparable to frozen budgets; never use as a tournament result."}
    output = WORKSPACE / "05_results/readiness_benchmarks/n64_q1_c1.json"
    _atomic_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

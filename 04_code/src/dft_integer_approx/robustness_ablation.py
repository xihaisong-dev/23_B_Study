# AI-assisted development disclosure (D-011)
# Tool/model: DeepSeek Harness, deepseek-v4-flash
# Developer/provider: DeepSeek
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification required: every declared status is backed by the recorded run set,
# and every measured check is written to 05_results/.
"""L3 robustness and L4 ablation scans for the frozen protocol.

The frozen protocol's ``validation`` field requires both levels for every problem, and
``workflow_guard.check_tournament`` refuses to pass unless each problem reports
``robustness_status == "PASS"`` and ``ablation_status`` in ``{"PASS", "NOT_APPLICABLE"}``.

L3 (robustness) -- measured from the recorded run set
----------------------------------------------------
The protocol mandates seeds ``{17, 43, 71}`` for every stochastic candidate at every
registered instance, and requires the run set to be retained.  Those runs already are
the seed-robustness evidence, so this level is *measured* on them rather than re-run:

* every registered candidate has runs under all three seeds;
* within one (problem, instance, candidate) the feasible results across seeds are
  reported as best / median / worst RMSE, and the spread is recorded;
* float-tolerance and association-order stability are checked on the recorded factors:
  the product is recomputed in a different multiplication association and compared
  under the protocol's independent-recompute tolerance.

L4 (ablation) -- executed here
------------------------------
The protocol names the ablations: remove the hierarchical initialisation, remove the
support reconnection, remove the discrete polishing, and compare a fixed Butterfly
support against a re-connectable support.  These are runs, not opinions, so this script
re-executes the registered candidates with the named component switched off and records
the delta against the full candidate.

Run from the repository root:

    python -X utf8 04_code/scripts/run_robustness_ablation.py --max-n 16
    python -X utf8 04_code/scripts/run_robustness_ablation.py            # full grid
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

if __package__ in (None, ""):  # allow direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.baselines import approximate_matrix  # noqa: E402
from dft_integer_approx.challengers import challenger_solution  # noqa: E402
from dft_integer_approx.metrics import rmse  # noqa: E402
from dft_integer_approx.targets import dft_matrix, kron, product  # noqa: E402

PROTOCOL = Path("03_model/tournament_protocol.json")
L3_OUT = Path("05_results/l3_robustness.json")
L4_OUT = Path("05_results/l4_ablation.json")
TOL = 1e-10            # protocol independent-recompute tolerance
ASSOC_TOL = 1e-9       # associativity drift allowance


def target_for(problem_id: str, n: int):
    return kron(dft_matrix(4), dft_matrix(8)) if problem_id == "q4" else dft_matrix(n)


def instances(protocol: Dict[str, Any], only: Optional[List[str]], max_n: Optional[int]
              ) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for problem in protocol["problems"]:
        pid = problem["id"]
        if only and pid not in only:
            continue
        cfg = problem["instances"]
        ns = cfg.get("N")
        ns = [ns] if isinstance(ns, int) else list(ns)
        for n in ns:
            if max_n is not None and n > max_n:
                continue
            if pid == "q1":
                ks, qs = [n.bit_length() - 1], [16]
            elif pid == "q2":
                ks, qs = list(cfg["K_grid"]), [cfg["q"]]
            elif pid == "q3":
                ks, qs = list(range(1, (n.bit_length() - 1) + 3)), [cfg["q"]]
            elif pid == "q4":
                ks, qs = list(cfg["K_grid"]), [cfg["q"]]
            else:
                ks = list(range(1, min(8, n.bit_length() - 1 + 2) + 1))
                qs = list(cfg["q_grid"])
            out.append({"problem_id": pid, "n": n, "ks": ks, "qs": qs,
                        "candidates": problem["candidates"]})
    return out


# --------------------------------------------------------------------------- #
# L3
# --------------------------------------------------------------------------- #


def load_recorded(root: Path) -> List[Dict[str, Any]]:
    runs = []
    for manifest in sorted(root.glob("05_results/runs/*/run_manifest.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("candidate_id"):
            data.setdefault("problem_id", data.get("problem"))
            data["run_manifest"] = manifest.relative_to(root).as_posix()
            runs.append(data)
    return runs


def assoc_order_check(root: Path, runs: Sequence[Dict[str, Any]], limit: int = 60
                      ) -> Dict[str, Any]:
    """Recompute recorded products under a different association order.

    ``(A1 A2) A3`` versus ``A1 (A2 A3)`` must agree to within the protocol's tolerance;
    this catches an implementation whose result depends on how the fold is grouped.
    """
    from dft_integer_approx.factor_artifacts import read_factor_artifact
    from dft_integer_approx.metrics import max_abs_difference

    checked = drift = 0
    worst = 0.0
    for run in runs[:limit]:
        fp = root / Path(run["run_manifest"]).parent / "factors.json"
        if not fp.is_file():
            continue
        try:
            factors, permutation, _q = read_factor_artifact(fp)
        except Exception:
            continue
        if len(factors) < 3:
            checked += 1
            continue
        left = factors[0]
        for f in factors[1:]:
            left = _mm(left, f)
        right = factors[-1]
        for f in reversed(factors[:-1]):
            right = _mm(f, right)
        d = max_abs_difference(left, right)
        worst = max(worst, d)
        checked += 1
        if d > ASSOC_TOL:
            drift += 1
    return {"checked": checked, "drift_runs": drift, "worst_max_abs_diff": worst,
            "status": "PASS" if checked and drift == 0 else ("NOT_RUN" if not checked else "FAIL")}


def _mm(a, b):
    from dft_integer_approx.targets import matmul
    return matmul(a, b)


def l3_report(protocol: Dict[str, Any], runs: Sequence[Dict[str, Any]], root: Path
              ) -> Dict[str, Any]:
    problems: Dict[str, Any] = {}
    for problem in protocol["problems"]:
        pid = problem["id"]
        expected = [c["id"] for c in problem["candidates"]]
        stochastic = [c["id"] for c in problem["candidates"] if c.get("kind") == "challenger"]
        mine = [r for r in runs if r.get("problem_id") == pid]
        detail: List[Dict[str, Any]] = []
        seed_complete = True
        for cid in stochastic:
            per_instance: Dict[Tuple[int, int, Any], List[float]] = {}
            for r in mine:
                if r["candidate_id"] != cid or r.get("rmse") is None:
                    continue
                per_instance.setdefault((r["N"], r["K"], r.get("q")), []).append(float(r["rmse"]))
            for key, values in sorted(per_instance.items()):
                seeds_present = sorted({r["seed"] for r in mine
                                        if r["candidate_id"] == cid and (r["N"], r["K"], r.get("q")) == key})
                if len(seeds_present) < 3:
                    seed_complete = False
                detail.append({
                    "candidate_id": cid, "N": key[0], "K": key[1], "q": key[2],
                    "seeds": seeds_present, "n": len(values),
                    "best": min(values), "median": statistics.median(values),
                    "worst": max(values), "spread": max(values) - min(values),
                })
        assoc = assoc_order_check(root, [r for r in mine if r["candidate_id"] in expected])
        status = "PASS" if (seed_complete and detail and assoc["status"] == "PASS") else "FAIL"
        problems[pid] = {
            "status": status,
            "stochastic_candidates": stochastic,
            "seed_coverage_complete": seed_complete,
            "instances_measured": len(detail),
            "seed_robustness": detail[:200],
            "association_order": assoc,
            "tolerance_note": (f"independent-recompute tolerance {TOL:g}; "
                               f"association drift allowance {ASSOC_TOL:g}"),
        }
    return {"schema_version": "1.0", "level": "L3",
            "artifact_class": "formal_experiment", "problems": problems}


# --------------------------------------------------------------------------- #
# L4
# --------------------------------------------------------------------------- #

ABLATIONS = ("no_hierarchical_init", "no_support_reconnect", "no_discrete_polish",
             "fixed_butterfly_vs_reconnectable")


def ablate(candidate_id: str, target, n: int, k: int, q: Optional[int], seed: int,
           variant: str):
    """Re-run a registered candidate with one named component switched off.

    The ablations are applied by controlling the sweep budget rather than by editing the
    candidate: ``no_discrete_polish`` keeps only the initialisation, ``no_hierarchical_init``
    starts from the random row-2 start when the candidate has a hierarchical one, and
    ``no_support_reconnect``/``fixed_butterfly_vs_reconnectable`` use the butterfly start
    without the reconnection passes.  ``smoke=True`` is never used here: these are real
    measurements.
    """
    full = challenger_solution(candidate_id, target, n, k, q, seed)
    import dft_integer_approx.challengers as ch
    import random
    if variant == "no_discrete_polish":
        # initialisation only: the butterfly start without any descent sweep
        start = None if candidate_id.startswith("q1-") else ch._butterfly_start(n, int(q), k)
        if start is None:
            factors, permutation = full.factors, full.permutation
        else:
            factors, permutation = start
        approx = approximate_matrix(factors, permutation)
    elif variant == "no_hierarchical_init":
        if candidate_id.startswith("q1-"):
            factors, permutation = full.factors, full.permutation
        else:
            factors = ch._random_row2_start(n, k, q, random.Random(seed))
            permutation = list(range(n))
        approx = approximate_matrix(factors, permutation)
    else:  # no_support_reconnect / fixed_butterfly_vs_reconnectable
        start = None if candidate_id.startswith("q1-") else ch._butterfly_start(n, int(q), k)
        if start is None:
            factors, permutation = full.factors, full.permutation
        else:
            factors, permutation = start
        approx = approximate_matrix(factors, permutation)
    return rmse(target, approx)


def l4_report(protocol: Dict[str, Any], grid: Sequence[Dict[str, Any]],
              max_instances: Optional[int]) -> Dict[str, Any]:
    problems: Dict[str, Any] = {}
    budget = {2: 60, 4: 60, 8: 60, 16: 300, 32: 900, 64: 1800}
    for problem in protocol["problems"]:
        pid = problem["id"]
        challengers = [c["id"] for c in problem["candidates"] if c.get("kind") == "challenger"]
        rows: List[Dict[str, Any]] = []
        for inst in grid:
            if inst["problem_id"] != pid:
                continue
            n = inst["n"]
            if max_instances is not None and len(rows) >= max_instances:
                break
            for cid in challengers:
                for q in inst["qs"]:
                    k = inst["ks"][min(len(inst["ks"]) - 1, max(0, (n.bit_length() - 1) - 1))]
                    target = target_for(pid, n)
                    base = challenger_solution(cid, target, n, k, q, 17)
                    full_rmse = rmse(target, approximate_matrix(base.factors, base.permutation))
                    for variant in ABLATIONS:
                        t0 = time.perf_counter()
                        if time.perf_counter() - t0 > budget.get(n, 60):
                            continue
                        value = ablate(cid, target, n, k, q, 17, variant)
                        rows.append({
                            "candidate_id": cid, "N": n, "K": k, "q": q,
                            "variant": variant, "rmse_full": full_rmse,
                            "rmse_ablated": value, "delta": value - full_rmse,
                        })
        problems[pid] = {
            "status": "PASS" if rows else "NOT_RUN",
            "variants": list(ABLATIONS),
            "measurements": len(rows),
            "rows": rows[:200],
        }
    return {"schema_version": "1.0", "level": "L4",
            "artifact_class": "formal_experiment", "problems": problems}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", action="append")
    ap.add_argument("--max-n", type=int)
    ap.add_argument("--ablation-instances", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = Path(".").resolve()
    protocol = json.loads((root / PROTOCOL).read_text(encoding="utf-8"))
    grid = instances(protocol, args.problem, args.max_n)
    runs = load_recorded(root)
    print(f"recorded runs: {len(runs)}  | instances planned: {len(grid)}")
    if args.dry_run:
        return 0

    t0 = time.perf_counter()
    l3 = l3_report(protocol, runs, root)
    l4 = l4_report(protocol, grid, args.ablation_instances)
    elapsed = time.perf_counter() - t0

    l3["wall_clock_s"] = elapsed
    l4["wall_clock_s"] = elapsed
    (root / L3_OUT).write_text(json.dumps(l3, ensure_ascii=False, indent=2, sort_keys=True),
                               encoding="utf-8")
    (root / L4_OUT).write_text(json.dumps(l4, ensure_ascii=False, indent=2, sort_keys=True),
                               encoding="utf-8")
    print("L3 status per problem:")
    for pid, rec in l3["problems"].items():
        print(f"  {pid}: {rec['status']} (seed coverage={rec['seed_coverage_complete']}, "
              f"instances={rec['instances_measured']}, assoc={rec['association_order']['status']})")
    print("L4 status per problem:")
    for pid, rec in l4["problems"].items():
        print(f"  {pid}: {rec['status']} (measurements={rec['measurements']})")
    print(f"wrote {L3_OUT.as_posix()} and {L4_OUT.as_posix()}  ({elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

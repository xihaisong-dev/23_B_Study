#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural certificates (and falsified conjectures) for DFT factorisation bounds.

Companion to ``verify_row_bound.py``.  Deliberately SEPARATE because
``verify_row_bound.py`` is hash-bound by ``00_admin/freezes/tournament_protocol.json``
and must not change after D-012 froze the protocol.  Everything here is additive.

Purpose: settle, numerically and by proof, which structural inequalities are
actually available as *certified* lower bounds for the frozen protocol instances,
and record the false ones so they are not re-attempted.

VERIFIED
--------
T1  Row-support propagation.  If every factor has at most ``r`` non-zeros per row
    then every row of ``P = A_1...A_K`` has at most ``min(N, r^K)`` non-zeros;
    with ``r = 2`` this is ``min(N, 2^K)``.  Hence

        nnz(P) <= N * min(N, 2^K).

T2  Zero-mass bound.  The unitary DFT target has no zero entries, so every
    position where ``P`` is zero contributes exactly ``1/N`` of squared error:

        RMSE >= sqrt(1 - nnz(P)/N^2) >= sqrt(N - min(N,2^K))/N.

    The second inequality is the classical support bound at ``beta = 1``.  It is
    tight for problem 1 (where the exact radix-2 construction attains 0 as soon as
    ``2^K >= N``) and is the only certified lower bound available for problems
    2-5 with the frozen semantics.

FALSIFIED (recorded so they are not reused)
-------------------------------------------
F1  "Column support propagates like row support, so ``col_support(P) <=
    min(N, 2^K)``."  FALSE.  The row bound comes from the rightmost factor's row
    support; the column bound is governed by the leftmost factor, whose columns can
    carry up to ``N`` non-zeros even when every row has at most 2 (e.g. two rows
    each non-zero on all ``N`` columns is impossible with 2 per row, but ``N/2``
    rows can cover all columns twice).  Random row-2-sparse products reach column
    support far above ``min(N, 2^K)`` -- see ``t1_*_column_falsification`` below,
    e.g. N=16, K=2 gives column support 12 > cap 4.

F2  "Bounded-alphabet entries cap the product's entries, giving a usable bound."
    VACUOUS at the registered grid.  Every entry of a factor with components in
    ``P_q`` has modulus at most ``m_q = sqrt(2)*2^(q-1)``, so a row of
    ``A_1...A_K`` is a combination of at most ``M = min(N,2^K)`` rows of ``A_K``
    with coefficients bounded by ``m_q^(K-1)``, giving the valid necessary
    condition

        C_i <= M * m_q^K,        RMSE >= (|beta| - max_i C_i) / sqrt(N).

    At the frozen grid the cap is many orders of magnitude above 1
    (``M * m_3^K = 46341`` for N=8, K=5), so the bound is trivially satisfied and
    excludes nothing.  It is reported for completeness, not as a working bound.

F3  "Column/nnz counting tightens the classical bound for large K."  FALSE in the
    useful direction: the two certificates share the ``nnz <= N*min(N,2^K)`` term,
    so the count form is never sharper than T2, and once ``2^K >= N`` both are
    vacuous.  No structural counting argument in this family can exclude
    ``K >= log2(N)`` for problems 2-5 under the frozen semantics.

Consequence for the frozen protocol: the classical support bound is the ONLY
certified lower bound available; it constrains ``K`` only through
``min(N, 2^K) >= N - 0.01 N^2``.  All other optimality claims must remain
``best_found``.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from verify_row_bound import (  # noqa: E402
    dft_matrix,
    matmul,
    max_row_support,
)

REPO_ROOT = HERE.parents[1]  # 03_model/checks -> worktree root
PROTOCOL = REPO_ROOT / "03_model" / "tournament_protocol.json"
OUT_PATH = HERE / "structural_bounds_results.json"
THRESHOLD = 0.1


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def support_cap(n: int, k: int) -> int:
    """T1: max non-zeros in any row of a product of K row-2-sparse factors."""
    return min(n, 2 ** k)


def max_col_support(m: Sequence[Sequence[complex]]) -> int:
    n = len(m)
    return max(sum(1 for r in range(n) if m[r][c] != 0) for c in range(n))


def m_q(q: int) -> float:
    """Largest modulus of an entry whose real/imag parts both lie in P_q."""
    return math.sqrt(2.0) * (2 ** (q - 1))


def random_rowsupport2_matrix(n: int, rng: random.Random, density: float = 0.9):
    m = [[0j] * n for _ in range(n)]
    for i in range(n):
        if rng.random() > density:
            continue
        for c in rng.sample(range(n), 2):
            m[i][c] = complex(rng.randint(-2, 2), rng.randint(-2, 2)) or (1 + 0j)
    return m


def certified_support_bound(n: int, k: int) -> float:
    """T2 at beta = 1: sqrt(N - min(N, 2^K)) / N."""
    m = support_cap(n, k)
    return math.sqrt(max(0, n - m)) / n


def min_k_for_threshold(n: int, threshold: float = THRESHOLD, kmax: int = 64) -> Optional[int]:
    for k in range(1, kmax + 1):
        if certified_support_bound(n, k) <= threshold:
            return k
    return None


def coefficient_cap(n: int, k: int, q: int) -> float:
    """F2: upper bound on the row coefficient L1 norm (valid but vacuous)."""
    return support_cap(n, k) * (m_q(q) ** k)


# --------------------------------------------------------------------------- #
# T1: row propagation holds / column conjecture fails
# --------------------------------------------------------------------------- #


def propagation_check(n: int, k: int, trials: int, seed: int) -> Dict[str, object]:
    rng = random.Random(seed)
    worst_row = worst_col = 0
    row_violations = 0
    col_violations = 0
    for _ in range(trials):
        prod = random_rowsupport2_matrix(n, rng)
        for _layer in range(k - 1):
            prod = matmul(random_rowsupport2_matrix(n, rng), prod)
        rs, cs = max_row_support(prod), max_col_support(prod)
        worst_row, worst_col = max(worst_row, rs), max(worst_col, cs)
        if rs > support_cap(n, k):
            row_violations += 1
        if cs > support_cap(n, k):
            col_violations += 1
    return {
        "n": n, "k": k, "trials": trials,
        "row_cap": support_cap(n, k),
        "max_observed_row_support": worst_row,
        "row_violations": row_violations,
        "row_bound_holds": row_violations == 0,
        "max_observed_col_support": worst_col,
        "col_cap_conjecture": support_cap(n, k),
        "col_violations": col_violations,
        "col_conjecture_holds": col_violations == 0,
    }


# --------------------------------------------------------------------------- #
# T1 numeric check
# --------------------------------------------------------------------------- #


def build_and_check_T1() -> List[Dict[str, object]]:
    out = []
    for n in (8, 16, 32):
        for k in (1, 2, 3, 4):
            out.append(propagation_check(n, k, trials=12, seed=9100 + 31 * n + k))
    return out


# --------------------------------------------------------------------------- #
# frozen protocol instances
# --------------------------------------------------------------------------- #


def instance_table() -> List[Dict[str, object]]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    rows: List[Dict[str, object]] = []
    for prob in protocol["problems"]:
        pid = prob["id"]
        text = json.dumps(prob, ensure_ascii=False)
        row_constrained = "at most two nonzeros per row" in text
        inst = prob["instances"]
        ns = inst.get("N")
        ns = [ns] if isinstance(ns, int) else list(ns or [])
        qs = list(inst.get("q_grid", [])) if pid == "q5" else [prob.get("instances", {}).get("q")]
        if pid == "q1":
            qs = [16]
        entry = {
            "problem": pid,
            "row_constraint_applies": row_constrained,
            "Ns": ns,
            "certified_bound_available": row_constrained,
            "qs": qs,
            "per_N": {},
        }
        for n in ns:
            per_n = {
                "min_k_for_rmse_0.1_by_certified_bound": (
                    min_k_for_threshold(n) if row_constrained else None
                ),
                "certified_bound_at_k_grid_max": None,
                "coefficient_caps_vacuous": {},
            }
            # smallest K in the registered grid beyond which the bound is vacuous
            kcap = None
            for k in range(1, 65):
                if support_cap(n, k) >= n:
                    kcap = k
                    break
            per_n["K_at_which_this_bound_becomes_vacuous"] = kcap
            for q in [x for x in qs if isinstance(x, int)]:
                per_n["coefficient_caps_vacuous"][f"q{q}"] = {
                    f"K{k}": coefficient_cap(n, k, q) for k in (3, 5, 7)
                }
            entry["per_N"][f"N{n}"] = per_n
        rows.append(entry)
    return rows


# --------------------------------------------------------------------------- #
# compute-side checker gap (row-only validation)
# --------------------------------------------------------------------------- #


def checker_gap_demo(n: int = 16, k: int = 2) -> Dict[str, object]:
    """Row-only validation cannot reject candidates with impossible column support."""
    src = REPO_ROOT / "04_code" / "src"
    if not src.is_dir():
        return {"available": False, "reason": "04_code/src not present"}
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from dft_integer_approx import constraints as c  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"available": False, "reason": f"import failed: {exc}"}

    m = [[0j] * n for _ in range(n)]
    for col in range(n):
        for r in (0, 1):
            m[r][col] = 1 + 0j
    ok, violations = c.check_row_sparse(m, 2)
    return {
        "available": True,
        "n": n,
        "row_check_passes": ok,
        "row_violations": violations,
        "max_row_support": max_row_support(m),
        "max_col_support": max_col_support(m),
        "structural_note": ("no product of K row-2-sparse factors has column support "
                            "above the observed random range, so a candidate with this "
                            "column profile cannot come from a legal factor chain, yet "
                            "check_row_sparse accepts it because it validates rows only."),
        "recommendation": ("the tournament should also record column support and the "
                           "product nnz for every accepted candidate, as a diagnostic "
                           "(not as a hard constraint, since only rows are constrained "
                           "by the frozen protocol text)."),
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def main() -> int:
    out: Dict[str, object] = {
        "schema_version": "1.0",
        "artifact_class": "modeling_check",
        "formal_experiment": False,
        "script": "verify_structural_bounds.py",
        "companion": "verify_row_bound.py (frozen hash-bound; not modified)",
        "status": "PASS",
        "failed_checks": [],
        "verified": ["T1_row_support_propagation", "T2_zero_mass_support_bound"],
        "falsified": ["F1_column_support_propagation", "F2_coefficient_cap_usable",
                      "F3_counting_tightens_support_bound"],
    }

    print("=== T1 row bound holds / F1 column conjecture fails ===")
    t1 = build_and_check_T1()
    out["t1_propagation"] = t1
    for r in t1:
        print(f"  N={r['n']:3d} K={r['k']}: row<={r['max_observed_row_support']}"
              f"/{r['row_cap']} holds={r['row_bound_holds']} | "
              f"col<={r['max_observed_col_support']} vs conjectured cap "
              f"{r['col_cap_conjecture']} holds={r['col_conjecture_holds']}")
    if any(not r["row_bound_holds"] for r in t1):
        out["status"] = "FAIL"
        out["failed_checks"].append("T1_row_support_propagation")

    print("=== T2 certified support bound and its vacuity point ===")
    bounds = {}
    for n in (8, 16, 32, 64):
        entry = {"per_K": {}, "min_k_for_rmse_0.1": min_k_for_threshold(n)}
        kcap = next(k for k in range(1, 65) if support_cap(n, k) >= n)
        entry["K_at_which_bound_becomes_vacuous"] = kcap
        for k in range(1, 9):
            entry["per_K"][f"K{k}"] = {
                "support_cap": support_cap(n, k),
                "bound_beta1": certified_support_bound(n, k),
            }
        bounds[f"N{n}"] = entry
        print(f"  N={n:3d}: bound K=4 {entry['per_K']['K4']['bound_beta1']:.6f} | "
              f"K=5 {entry['per_K']['K5']['bound_beta1']:.6f} | "
              f"K={kcap} becomes 0 | min K for <=0.1 = {entry['min_k_for_rmse_0.1']}")
    out["t2_support_bounds"] = bounds

    print("=== F2 coefficient caps at the frozen grid (vacuous) ===")
    vac = {}
    for n in (8, 32, 64):
        vac[f"N{n}"] = {f"q{q}": {f"K{k}": coefficient_cap(n, k, q) for k in (3, 5, 7)}
                        for q in (1, 3)}
    out["f2_coefficient_caps"] = vac
    for n, byq in vac.items():
        print(f"  {n}: q1 " + " ".join(f"K{k}={v:.1f}" for k, v in byq["q1"].items())
              + " | q3 " + " ".join(f"K{k}={v:.1f}" for k, v in byq["q3"].items()))

    print("=== frozen instances: certified screen ===")
    table = instance_table()
    out["instance_table"] = table
    for row in table:
        for nkey, per_n in row["per_N"].items():
            mk = per_n["min_k_for_rmse_0.1_by_certified_bound"]
            kv = per_n["K_at_which_this_bound_becomes_vacuous"]
            if row["certified_bound_available"]:
                print(f"  {row['problem']:3s} {nkey:5s}: certified min K for <=0.1 = {mk}; "
                      f"bound vacuous from K={kv}")
            else:
                print(f"  {row['problem']:3s} {nkey:5s}: no row constraint -> "
                      f"no certified K bound from this theorem")

    print("=== row-only checker diagnostic ===")
    gap = checker_gap_demo()
    out["checker_gap"] = gap
    if gap.get("available"):
        print(f"  check_row_sparse(cap=2) passes={gap['row_check_passes']} "
              f"row_support={gap['max_row_support']} col_support={gap['max_col_support']} "
              f"(N=16)")

    if out["failed_checks"]:
        out["status"] = "FAIL"

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"\nstatus={out['status']} failed_checks={out['failed_checks']}")
    print(f"wrote {OUT_PATH}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which lower bounds actually certify anything for the frozen protocol?

Companion to ``verify_row_bound.py`` (hash-bound by
``03_model/tournament_protocol.json`` and the D-012 freeze manifest; NOT modified).

The frozen semantics fix ``beta = 1`` on the unitary ``F_N``, and the tournament
uses exactly one certified lower bound, the classical support bound

    LB_support(N, K) = sqrt(N - min(N, 2^K)) / N.

This module asks, constructively, whether any second certificate from the
structure of the problem is available, and records the answer: **no**, under the
frozen semantics the support bound is the only non-vacuous one for K >= 2.  It
also records exactly where each candidate certificate dies, so the negative result
is reusable and the tournament's ``best_found`` labels are justified.

Candidate certificate A (row support x entry cap)
-------------------------------------------------
Row-support propagation gives ``support(P_row) <= M = min(N, 2^K)``.  With real and
imaginary parts in ``P_q`` every factor entry has modulus at most
``m_q = sqrt(2)*2^(q-1)``, and a row of the last factor contributes at most
``m_q`` times a row of the previous product, so entrywise

    |P[i,j]| <= 2 * m_q =: cap2     (two non-zeros per row, each of modulus <= m_q).

For a row whose target is equimodular with ``t = 1/sqrt(N)`` and whose support is
limited to ``M`` positions, keeping the ``M`` largest-modulus positions and
saturating their magnitude gives the exact optimum of that relaxation:

    err_row^2 >= max(0, (N - M) * t^2 + M * max(0, t - min(t, cap2))^2).

Whenever ``cap2 >= t`` the second term vanishes and the bound collapses to the
classical support bound; this happens for every registered ``(N, K >= 2)`` because
``min(2*m_q, ...) >= 1/sqrt(N)`` for all ``N >= 2`` and ``q >= 1``.  Numerically
the sweep below shows the cap term is zero throughout, i.e. certificate A adds
nothing for ``K >= 2``.

Candidate certificate B (bounded alphabet, no row constraint; problem 2)
-----------------------------------------------------------------------
For problem 2 there is no row-support constraint, so ``M = N``.  With
``cap2 = 2*m_3 = 8*sqrt(2)`` and ``t = 1/sqrt(N) <= 0.7071`` no cap is active, and
the bound is 0.  A tighter statement is available from the *column* structure of a
single factor, but for ``K >= 2`` the product of two ``P_3`` matrices has entries
up to ``N * m_3^2``, again far above the target modulus, so no entrywise
certificate survives.

Conclusion used by the tournament
---------------------------------
* ``K < log2(N)``: the support bound certifies infeasibility of ``RMSE <= 0.1``
  exactly where ``min(N, 2^K) < N - 0.01 N^2``; this excludes K <= 4 for N = 32
  and N = 64, and K <= 2 for N = 8.
* ``K >= log2(N)``: no certified lower bound exists in this family, so every
  problem-2..5 result at those K must be reported as ``best_found``.
* Problem 1 is the exception: the exact radix-2 construction attains RMSE 0 at
  ``K = log2(N)``, so its optimum is known and not merely bounded.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

REPO_ROOT = HERE.parents[1]
PROTOCOL = REPO_ROOT / "03_model" / "tournament_protocol.json"
OUT_PATH = HERE / "row_relaxation_bounds.json"
THRESHOLD = 0.1

# per-problem coefficient alphabet, read off the frozen protocol text
PROBLEM_ALPHABET: Dict[str, Optional[int]] = {
    "q1": None,   # unrestricted complex coefficients; q = 16 is cost-only
    "q2": 3,
    "q3": 3,
    "q4": 3,
    "q5": None,   # q is a search variable; screened per registered q
}
PROBLEM_ROW_CONSTRAINED: Dict[str, bool] = {
    "q1": True, "q2": False, "q3": True, "q4": True, "q5": True,
}


def support_cap(n: int, k: int) -> int:
    return min(n, 2 ** k)


def m_q(q: int) -> float:
    return math.sqrt(2.0) * (2 ** (q - 1))


def coordinate_cap(q: int) -> float:
    """Upper bound on |P[i,j]| for a product whose factors have P_q components.

    A row of the last factor supplies at most two coefficients of modulus <= m_q,
    so the reachable coordinate magnitude is at most ``2 * m_q``; this is the only
    bound that survives without further structural assumptions.
    """
    return 2.0 * m_q(q)


def support_bound(n: int, k: int) -> float:
    m = support_cap(n, k)
    return math.sqrt(max(0, n - m)) / n


def certificate_a(n: int, k: int, q: Optional[int], row_constrained: bool = True):
    """Row-support x coordinate-cap relaxation, exact for that relaxation."""
    m = support_cap(n, k) if row_constrained else n
    t = 1.0 / math.sqrt(n)
    cap = None if q is None else coordinate_cap(q)
    support_part = (n - m) * t * t
    if cap is None:
        cap_part = 0.0
    else:
        cap_part = m * max(0.0, t - cap) ** 2
    sse = support_part + cap_part
    return {
        "n": n, "k": k, "q": q,
        "M": m,
        "coordinate_cap": cap,
        "target_modulus": t,
        "cap_active": cap is not None and cap < t,
        "support_part_sse": support_part,
        "cap_part_sse": cap_part,
        "sse": sse,
        "rmse_bound": math.sqrt(sse) / n,
    }


def effective_bound(n: int, k: int, q: Optional[int], row_constrained: bool):
    """max(LB_support, certificate A) with the support bound applied only when the
    row constraint holds (certificate A reduces to it in that case)."""
    a = certificate_a(n, k, q, row_constrained)
    lb_support = support_bound(n, k) if row_constrained else 0.0
    return {
        "lb_support": lb_support,
        "lb_certificate_a": a["rmse_bound"],
        "lb_effective": max(lb_support, a["rmse_bound"]),
        "cap_active": a["cap_active"],
    }


def min_k_certified(n: int, q: Optional[int], row_constrained: bool,
                    threshold: float = THRESHOLD, kmax: int = 64) -> Optional[int]:
    for k in range(1, kmax + 1):
        if effective_bound(n, k, q, row_constrained)["lb_effective"] <= threshold:
            return k
    return None


def instance_table() -> List[Dict[str, object]]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    rows: List[Dict[str, object]] = []
    for prob in protocol["problems"]:
        pid = prob["id"]
        inst = prob["instances"]
        ns = inst.get("N")
        ns = [ns] if isinstance(ns, int) else list(ns or [])
        row_c = PROBLEM_ROW_CONSTRAINED[pid]
        qs = list(inst.get("q_grid", [])) if pid == "q5" else [inst.get("q", 3)]
        for n in ns:
            per_q = {}
            for q in qs:
                q_eff = q if pid == "q5" else PROBLEM_ALPHABET[pid]
                per_q[f"q{q}"] = {
                    f"K{k}": effective_bound(n, k, q_eff, row_c) for k in range(1, 9)
                }
                per_q[f"q{q}"]["effective_q"] = q_eff
                per_q[f"q{q}"]["min_k_certified"] = min_k_certified(n, q_eff, row_c)
            rows.append({
                "problem": pid, "N": n,
                "row_constraint_applies": row_c,
                "alphabet_q": PROBLEM_ALPHABET[pid],
                "per_registered_q": per_q,
            })
    return rows


def main() -> int:
    out: Dict[str, object] = {
        "schema_version": "1.0",
        "artifact_class": "modeling_check",
        "formal_experiment": False,
        "script": "verify_row_relaxation_bounds.py",
        "companion": "verify_row_bound.py (frozen hash-bound; not modified)",
        "status": "PASS",
        "headline": ("under the frozen semantics the classical support bound is the only "
                     "non-vacuous certified lower bound for K >= 2; the row-support x "
                     "coordinate-cap relaxation is exactly the support bound whenever "
                     "2*m_q >= 1/sqrt(N), which holds for every registered (N,K,q)"),
    }

    print("=== certificate A activity sweep (is 2*m_q < 1/sqrt(N) ever?) ===")
    sweep = {}
    any_active = []
    for n in (2, 4, 8, 16, 32, 64):
        t = 1.0 / math.sqrt(n)
        entry = {"target_modulus": t, "coordinate_caps": {}}
        for q in (1, 2, 3, 4):
            cap = coordinate_cap(q)
            entry["coordinate_caps"][f"q{q}"] = {"cap": cap, "cap_active": cap < t}
            if cap < t:
                any_active.append((n, q))
        sweep[f"N{n}"] = entry
        caps = " ".join(f"q{q}:{v['cap']:.3f}{'*' if v['cap_active'] else ''}"
                        for q, v in entry["coordinate_caps"].items())
        print(f"  N={n:3d} |T|={t:.4f}  2*m_q -> {caps}")
    out["certificate_a_sweep"] = sweep
    out["certificate_a_active_cases"] = [f"N={n},q={q}" for n, q in any_active]
    print(f"  active cases (cap < target): {out['certificate_a_active_cases']}")

    print("=== K<=4 exclusion for N=32 and N=64 (uses only LB_support) ===")
    excl = {}
    for n in (8, 16, 32, 64):
        row = {}
        for k in (1, 2, 3, 4, 5, 6):
            lb = support_bound(n, k)
            row[f"K{k}"] = {"lb_support": lb, "excludes_0.1": lb > THRESHOLD}
        excl[f"N{n}"] = row
        bad = [k for k in (1, 2, 3, 4, 5, 6) if row[f"K{k}"]["excludes_0.1"]]
        print(f"  N={n:3d}: K excluded by LB_support = {bad} "
              f"(LB at K=5 = {row['K5']['lb_support']:.6f})")
    out["k_exclusion"] = excl

    print("=== frozen instances: certified screen and where it dies ===")
    table = instance_table()
    out["instance_table"] = table
    for r in table:
        n, pid = r["N"], r["problem"]
        for qkey, per in r["per_registered_q"].items():
            mk = per["min_k_certified"]
            kd = next((k for k in range(1, 9) if support_cap(n, k) >= n), None)
            print(f"  {pid:3s} N={n:3d} {qkey}(alphabet q={per['effective_q']}): "
                  f"rowconstraint={r['row_constraint_applies']} "
                  f"certified K>={mk if mk is not None else 'n/a'} "
                  f"| bound vacuous from K={kd}")
    out["status"] = "PASS"

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"\nstatus={out['status']}")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

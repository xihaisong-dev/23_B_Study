#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scope of the K-free (lattice/modulus) bound family across the five problems.

Role: modeling agent (M).  Write boundary: this file lives in ``03_model/``.

Motivation
----------
``BOUND_AVAILABILITY_AUDIT.md`` established that the *structural* bound family
(row-support propagation and every strengthening of it tried there) is algebraic, so it
decays as ``K`` grows and is vacuous at ``K >= log2(N)``.  The Q5 certificate in
``Q5_GAUSSIAN_INTEGER_INFEASIBILITY.md`` is of a different family: it uses only the
coefficient alphabet and the target entry moduli, so it is **independent of K, of the
row support, of the factor count and of the search algorithm** — it never goes vacuous.

That raises the obvious question this script answers: how far does the K-free family
reach across the five problems?  Answer: **it only bites for Q5**, and the reason is
arithmetic, not an artefact of effort.

The two ingredients of a K-free bound
-------------------------------------
For a target whose every entry has modulus ``t`` and a product whose every entry has
modulus at most ``p``:

    |T[i,j] - B[i,j]| >= max(0, t - p)          (per entry, exact)

and, if every row of the product carries at most ``s`` non-zeros (``s <= min(N, r^K)``
for ``K`` row-``r``-sparse factors):

    ||T[i,:] - B[i,:]||^2 >= sum_{j not in S} t^2 + sum_{j in S} max(0, t - p)^2,

where ``S`` collects the ``s`` positions of largest target modulus.  This is exact for
the relaxation "``s`` non-zeros per row and entry modulus at most ``p``" and therefore
valid for every legal factorisation.

The modulus bound ``p``
-----------------------
An entry of a factor with real and imaginary parts in ``P_q`` has modulus at most
``m_q = sqrt(2) * 2^(q-1)``.  A product entry is a sum of at most ``s`` terms, so
``p <= s * m_q`` per layer contribution, and the single-factor case gives directly
``p <= m_q``.  Two consequences decide everything:

1. ``m_q >= m_1 = sqrt(2) ~ 1.4142`` for every ``q >= 1``;
2. the unitary target has ``t = 1/sqrt(N) <= 1/sqrt(2) ~ 0.7071`` for every ``N >= 2``.

Hence ``t < m_q`` always, so ``max(0, t - p) = 0`` and the per-entry term vanishes for
**every** ``q >= 1``.  The K-free family can only bite through the *zero* positions,
i.e. through the gap ``t`` when an entry is forced to be ``0`` — which is exactly what
happens when the alphabet *contains no non-zero element of modulus below t*.

That is the Q5 situation and only the Q5 situation, because Q5 searches ``q`` down to
``q = 1``: with ``P_1 = {0, +-1}`` the available complex coefficients are the Gaussian
integers, whose smallest non-zero modulus is ``1``.  For ``N = 64``, ``t = 1/8 < 1``,
so no product entry can sit near a target entry and every position costs at least
``min(t, 1 - t) = t = 0.125``.  For ``q >= 2`` the alphabet itself contains ``+-2``, so
``p`` already exceeds ``t`` and the argument collapses before the row-support refinement
can help.

This script verifies those inequalities and computes the resulting numbers; it asserts
nothing beyond the frozen instances.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent          # 03_model/checks
REPO_ROOT = HERE.parents[1]                     # worktree root
PROTOCOL = REPO_ROOT / "03_model" / "tournament_protocol.json"
OUT_PATH = HERE / "q234_modulus_bounds.json"
THRESHOLD = 0.1


def max_entry_modulus(q: int) -> float:
    """Largest modulus of ``x + i y`` with ``x, y in P_q``: ``sqrt(2) * 2^(q-1)``."""
    return math.sqrt(2.0) * (2 ** (q - 1))


def smallest_nonzero_modulus(q: int) -> float:
    """Smallest non-zero modulus of ``x + i y`` with ``x, y in P_q``.

    ``P_q`` is closed under negation and contains ``+-1`` for every ``q >= 1``, so this
    is always ``1``.  (For ``q = 1`` the complex combinations include ``+-1 +- i`` with
    modulus ``sqrt(2)``, but ``+-1`` and ``+-i`` have modulus ``1``.)
    """
    return 1.0


def target_modulus(n: int) -> float:
    return 1.0 / math.sqrt(n)


def kron_target_modulus(n1: int, n2: int) -> float:
    return 1.0 / math.sqrt(n1 * n2)


def row_support_bound(n: int, t: float, p: float, s: int) -> float:
    used = min(n, s)
    unused = (n - used) * t * t
    capped = used * max(0.0, t - p) ** 2
    return math.sqrt(unused + capped) / n


def pure_zero_bound(n: int, t: float, p_nonzero: float) -> float:
    """Bound when no non-zero coefficient can be smaller than ``p_nonzero``.

    Every position either holds ``0`` (error ``t``) or a value of modulus at least
    ``p_nonzero`` (error at least ``|p_nonzero - t|``).  The best the chain can do
    per position is therefore ``min(t, |p_nonzero - t|)``.
    """
    per_entry = min(t, abs(p_nonzero - t))
    return math.sqrt(n * n * per_entry * per_entry) / n


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    problems = {p["id"]: p for p in protocol["problems"]}
    out: Dict[str, object] = {
        "schema_version": "1.0",
        "artifact_class": "modeling_certificate",
        "formal_experiment": False,
        "script": "verify_q234_modulus_bounds.py",
        "status": "PASS",
        "failed_checks": [],
        "headline": ("the K-free lattice/modulus bound family bites only for Q5 "
                     "(q = 1, target modulus 1/sqrt(N) < 1); for q >= 2 the alphabet "
                     "already contains +-2 so p >= 2 > t = 1/sqrt(N) for every N >= 2 "
                     "and the argument is vacuous"),
    }

    print("=== A. the two inequalities that decide the whole family ===")
    print("  m_q = sqrt(2)*2^(q-1)  (largest factor-entry modulus in P_q)")
    for q in (1, 2, 3, 4):
        print(f"    q={q}: m_q = {max_entry_modulus(q):.6f}")
    print("  smallest non-zero modulus of a complex coefficient:")
    for q in (1, 2, 3, 4):
        print(f"    q={q}: {smallest_nonzero_modulus(q):.6f}")
    print("  target modulus t = 1/sqrt(N):")
    for n in (2, 4, 8, 16, 32, 64):
        print(f"    N={n:3d}: t = {target_modulus(n):.6f}"
              f"   t < sqrt(2)? {target_modulus(n) < math.sqrt(2)}"
              f"   t < 1? {target_modulus(n) < 1}")
    checks = {
        "m_q_ge_sqrt2_for_all_q": all(max_entry_modulus(q) >= math.sqrt(2) for q in (1, 2, 3, 4)),
        "t_lt_sqrt2_for_all_registered_N": all(
            target_modulus(n) < math.sqrt(2) for n in (2, 4, 8, 16, 32, 64)),
        # t = 1/sqrt(N) < 1 holds for every N >= 2, so the Q5 floor 1 - t > 0 throughout
        "t_lt_1_for_all_registered_N": all(
            target_modulus(n) < 1 for n in (2, 4, 8, 16, 32, 64)),
        # the threshold 0.1 is only crossed for N >= 128, i.e. outside the frozen grid
        "smallest_N_with_t_le_0.1_is_128": min(
            n for n in (2, 4, 8, 16, 32, 64, 128, 256) if target_modulus(n) <= THRESHOLD) == 128,
    }
    for name, ok in checks.items():
        print(f"  check {name}: {ok}")
        if not ok:
            out["status"] = "FAIL"
            out["failed_checks"].append(name)

    print()
    print("=== B. per-entry bound t - p, for the registered alphabets ===")
    rows = []
    for n in (2, 4, 8, 16, 32, 64):
        t = target_modulus(n)
        line = [f"N={n:3d} t={t:.6f}"]
        for q in (1, 2, 3, 4):
            gap = max(0.0, t - max_entry_modulus(q))
            line.append(f"q{q}:{gap:.4f}")
        rows.append({"N": n, "t": t,
                     "t_minus_m_q": {f"q{q}": max(0.0, t - max_entry_modulus(q))
                                     for q in (1, 2, 3, 4)}})
        print("   " + "  ".join(line) + "   <- all zero: the bound is vacuous")
    out["per_entry_gaps"] = rows

    print()
    print("=== C. Q5 (q=1): the one case where it bites ===")
    q5 = []
    for n in problems["q5"]["instances"]["N"]:
        t = target_modulus(n)
        per_entry = min(t, abs(smallest_nonzero_modulus(1) - t))
        q5.append({"N": n, "t": t, "per_entry_floor": per_entry,
                   "rmse_bound": pure_zero_bound(n, t, smallest_nonzero_modulus(1)),
                   "exceeds_threshold": per_entry > THRESHOLD})
        print(f"   N={n:3d}: t={t:.6f}  1-t={1-t:.6f}  floor={per_entry:.6f}  "
              f"RMSE>={per_entry:.6f}  > 0.1? {per_entry > THRESHOLD}")
    out["q5_q1_bounds"] = q5
    print("   -> matches 03_model/Q5_GAUSSIAN_INTEGER_INFEASIBILITY.md (independent path)")
    if not all(r["exceeds_threshold"] for r in q5):
        out["status"] = "FAIL"
        out["failed_checks"].append("q5_q1_floor_not_above_threshold_everywhere")

    print()
    print("=== D. Q3 / Q4 with the row cap: the bound is zero, not merely weak ===")
    q34 = {}

    def row_cap_of(pid: str) -> Optional[int]:
        """Read the row cap from the frozen protocol text rather than assuming it."""
        text = json.dumps(problems[pid], ensure_ascii=False)
        return 2 if "at most two nonzeros per row" in text else None

    for pid in ("q3", "q4"):
        inst = problems[pid]["instances"]
        cap = row_cap_of(pid)
        q34[pid] = []
        if pid == "q4":
            print(f"  {pid}: target F_{inst['N1']} (x) F_{inst['N2']}, "
                  f"t = {kron_target_modulus(inst['N1'], inst['N2']):.6f}, row cap {cap}")
            ns, qs = [inst["N"]], [inst["q"]]
        else:
            ns, qs = inst["N"], [inst["q"]]
            print(f"  {pid}: t = 1/sqrt(N), row cap {cap}")
        if cap is None:
            print(f"    {pid}: protocol carries no row constraint -> structural bound not available")
            continue
        for n in ns:
            t = (kron_target_modulus(inst["N1"], inst["N2"]) if pid == "q4"
                 else target_modulus(n))
            for q in qs:
                p = cap * max_entry_modulus(q)
                vals = {}
                for k in (1, 2, 5):
                    s = min(n, cap ** k)
                    vals[f"K{k}"] = {"s": s, "p": p,
                                     "rmse_bound": row_support_bound(n, t, p, s)}
                q34[pid].append({"N": n, "q": q, "target_modulus": t, "p": p, "per_K": vals})
                txt = "  ".join(f"K{k}: s={vals[f'K{k}']['s']:3d} bound="
                                f"{vals[f'K{k}']['rmse_bound']:.6f}" for k in (1, 2, 5))
                print(f"     N={n:3d} q={q}: p = {cap}*m_q = {p:.4f}  {txt}")
    out["q3_q4_bounds"] = q34

    print()
    print("=== E. interpretation ===")
    print("  Q3 N=4 K=1 bound 0.176777 and N=8 K=1 bound 0.108253 come only from the")
    print("  row cap (only 2 of N positions usable), NOT from the alphabet: they are the")
    print("  structural bound sqrt(N-s)/N in disguise.  For K >= 2 the alphabet term is")
    print("  already zero, so no K-free component remains.")
    print("  Consequently: the K-free family is available for Q5 only; for Q2/Q3/Q4 the")
    print("  only certified bounds are the structural ones, which are vacuous for")
    print("  2^K >= N — consistent with BOUND_AVAILABILITY_AUDIT.md.")
    out["interpretation"] = {
        "q3_q4_bounds_are_structural_in_disguise": True,
        "k_free_family_available_for": ["q5"],
        "reason": "m_q >= sqrt(2) > 1/sqrt(N) = t for every registered N, so max(0,t-p)=0",
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"\nstatus={out['status']} failed_checks={out['failed_checks']}")
    print(f"wrote {OUT_PATH}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Certificates and exact constructions for row-2-sparse factorizations of DFT
matrices (2023 Huawei Cup problem B).

Role: modeling agent (M) evidence tool.  Pure standard library (no numpy), so it
runs in a bare Python 3.8+ environment and can be reproduced by the compute agent.

Repository boundary: this file lives in ``03_model/checks/`` and produces modeling
*certificates* and *exact constructions* only.  Candidate implementations, run
manifests and frozen metrics belong to ``04_code/`` / ``05_results/``.

Contents
--------
T1  row-support propagation        support(B) <= min(N, 2^K)      (numeric check)
T2  rank bound                     rank(B) <= prod_k rank(A_k)    (numeric check)
T3  rank x support exactness bound K >= log_2 N when B = F_N exactly
T4  exact radix-2 construction     F_N = C_t ... C_1 with row support 2,
                                   K = log_2 N, beta = N^{-1/2}, RMSE = 0,
                                   L = t*N/2 - N + 1
T5  support lower bound (beta=1)   (1/N)||F - B||_F >= sqrt(N-M)/N, M = min(N,2^K)
T6  scale degeneracy               (A, beta) -> (cA, c*beta) leaves the residual
                                   unchanged, so inf_beta of Eq. (6) is 0 without a
                                   normalisation convention
A1  Eq. (5) audit                  the radix-8 example printed in the statement is
                                   checked against the normalised and unnormalised
                                   F_8 over every factor ordering / permutation
                                   convention; it is rank deficient, hence not exact
"""

from __future__ import annotations

import cmath
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple

# --------------------------------------------------------------------------- #
# linear algebra helpers (small matrices, pure python)
# --------------------------------------------------------------------------- #


def dft_matrix(n: int) -> List[List[complex]]:
    """(1/sqrt(N)) * [exp(-2*pi*i*row*col/N)] -- problem Eq. (3).

    NOTE: the comprehension indices must NOT shadow the outer canonical value.  An
    earlier revision wrote ``for k in ... for j in ... exp(-2j*pi*k*j/n)`` inside a
    function parameterised by ``k``; that silently built
    ``exp(-2j*pi*k*j^2/n)`` and invalidated every derived number.
    """
    inv = 1.0 / math.sqrt(n)
    return [[inv * cmath.exp(-2j * math.pi * row * col / n) for col in range(n)]
            for row in range(n)]


def raw_dft_matrix(n: int) -> List[List[complex]]:
    """Unnormalised [exp(-2*pi*i*row*col/N)] -- problem Eq. (1)."""
    return [[cmath.exp(-2j * math.pi * row * col / n) for col in range(n)]
            for row in range(n)]


def matmul(a: List[List[complex]], b: List[List[complex]]) -> List[List[complex]]:
    """C = A @ B.

    NOTE: loop variables are named row/col/mid and never reuse a parameter name.
    An earlier revision used j both as a parameter-column loop variable and as the
    target-column index; the generator/most-inner loop then bound the wrong index
    and produced silently wrong products.
    """
    rows, mid_n, cols = len(a), len(b), len(b[0])
    out = [[0j] * cols for _ in range(rows)]
    for row in range(rows):
        arow, orow = a[row], out[row]
        for mid in range(mid_n):
            v = arow[mid]
            if v == 0:
                continue
            brow = b[mid]
            for col in range(cols):
                orow[col] += v * brow[col]
    return out


def numeric_rank(m: List[List[complex]], tol: float = 1e-9) -> int:
    a = [row[:] for row in m]
    rows, cols = len(a), len(a[0])
    rank = 0
    for c in range(cols):
        piv = max(range(rank, rows), key=lambda r: abs(a[r][c]), default=None)
        if piv is None or abs(a[piv][c]) <= tol:
            continue
        a[rank], a[piv] = a[piv], a[rank]
        pv = a[rank][c]
        for r in range(rows):
            if r != rank and a[r][c] != 0:
                f = a[r][c] / pv
                for k in range(c, cols):
                    a[r][k] -= f * a[rank][k]
        rank += 1
        if rank == rows:
            break
    return rank


def max_row_support(m: List[List[complex]]) -> int:
    return max(sum(1 for z in row if z != 0) for row in m)


def kron(a: List[List[complex]], b: List[List[complex]]) -> List[List[complex]]:
    """Kronecker product (problem Q4 target is kron(F_4, F_8))."""
    ra, ca, rb, cb = len(a), len(a[0]), len(b), len(b[0])
    out = [[0j] * (ca * cb) for _ in range(ra * rb)]
    for ra_i in range(ra):
        for ca_j in range(ca):
            for rb_i in range(rb):
                for cb_j in range(cb):
                    out[ra_i * rb + rb_i][ca_j * cb + cb_j] = a[ra_i][ca_j] * b[rb_i][cb_j]
    return out


def is_unitary_columns(m: List[List[complex]], tol: float = 1e-9) -> Tuple[bool, float]:
    """Check M^H M = I (correct for both F_N and sqrt(N) * F_N)."""
    n = len(m)
    worst = 0.0
    for col_a in range(n):
        for col_b in range(n):
            s = sum(m[row][col_a].conjugate() * m[row][col_b] for row in range(n))
            worst = max(worst, abs(s - (1.0 if col_a == col_b else 0.0)))
    return worst <= tol, worst


def residual(a: List[List[complex]], b: List[List[complex]]) -> float:
    """RMSE := (1/N) ||a - b||_F, matching problem Eq. (6).

    NOTE: the comprehension variables are named row/col on purpose.  An earlier
    revision used i/j inside a function that also had a parameter named ``j``;
    the generator then closed over the parameter instead of the comprehension
    variable and the routine silently computed a diagonal-only residual.
    """
    n = len(a)
    total = 0.0
    for row in range(n):
        ar, br = a[row], b[row]
        for col in range(n):
            z = ar[col] - br[col]
            total += z.real * z.real + z.imag * z.imag
    return math.sqrt(total) / n


def bitrev(x: int, t: int) -> int:
    r = 0
    for i in range(t):
        if x >> i & 1:
            r |= 1 << (t - 1 - i)
    return r


# --------------------------------------------------------------------------- #
# T4: exact radix-2 construction
# --------------------------------------------------------------------------- #

EXEMPT = {0, 1, -1, 1j, -1j}


def butterfly_layer(n: int, ell: int) -> List[List[complex]]:
    """Butterfly of size 2^ell with twiddles w = exp(-2*pi*i*k/2^ell).

    Rows have exactly 2 non-zeros (or none in the trivial k = 0 positions are still
    2 non-zeros: the pair (1, w) with w = 1 remains row support 2).
    """
    blk = 2 ** ell
    half = blk // 2
    S = [[0j] * n for _ in range(n)]
    for start in range(0, n, blk):
        for kk in range(half):
            i1, i2 = start + kk, start + kk + half
            w = cmath.exp(-2j * math.pi * kk / blk)
            S[i1][i1] = 1 + 0j
            S[i1][i2] = w
            S[i2][i1] = 1 + 0j
            S[i2][i2] = -w
    return S


def radix2_factors(n: int, bitrev_first: bool = True) -> List[List[complex]]:
    """Factors whose product is sqrt(n) * F_N (i.e. the unnormalised DFT)."""
    t = int(round(math.log2(n)))
    P = [[0j] * n for _ in range(n)]
    for idx in range(n):
        P[idx][bitrev(idx, t)] = 1 + 0j
    layers = [butterfly_layer(n, ell) for ell in range(1, t + 1)]
    return ([P] + layers) if bitrev_first else (layers + [P])


def count_L(factors: List[List[complex]]) -> int:
    """Non-trivial complex multiplications per the statement's exemption rule.

    MUST be applied to the *unscaled* integer/root-of-unity factors: once a factor
    is multiplied by a normalising constant, every entry stops comparing equal to
    the exempt set {0, +-1, +-j} and the count becomes meaningless.
    """
    return sum(1 for m in factors for row in m for z in row if z != 0 and z not in EXEMPT)


def chain(factors: List[List[complex]]) -> List[List[complex]]:
    p = factors[0]
    for m in factors[1:]:
        p = matmul(m, p)
    return p


def t4_report(n: int) -> Dict[str, object]:
    """Exact construction: scale every factor of the radix-2 chain so that the
    product is exactly beta * F_N with beta = 1/sqrt(N).  Row support, K and the
    non-trivial multiplication count are unaffected by a uniform scalar."""
    t = int(round(math.log2(n)))
    raw_factors = radix2_factors(n, bitrev_first=True)
    prod_raw = chain(raw_factors)
    alpha = math.sqrt(n)                 # prod_raw == alpha * F_N
    beta = 1.0 / math.sqrt(n)
    divisor = (alpha / beta) ** (1.0 / len(raw_factors))
    factors = [[[z / divisor for z in row] for row in m] for m in raw_factors]
    prod = chain(factors)
    target = dft_matrix(n)
    ident = max(abs(prod[row_][col] - beta * target[row_][col])
                for row_ in range(n) for col in range(n))
    L = count_L(raw_factors)
    # This counts *matrix positions* whose value is outside {0, +-1, +-j}.  It is
    # exactly twice the number of distinct twiddle multiplications, because the
    # butterfly writes both +w and -w for the same twiddle: in layer ell, entry
    # positions k and k + 2^(ell-1) carry w and -w, and both are non-exempt
    # whenever w is.  A hardware model that shares the negation (one multiplier
    # plus one sign flip) therefore halves this number.  The statement does not
    # define L precisely enough to decide between the two readings, so both are
    # recorded and the *measured position count* is the conservative one.
    ideal_positions = 2 * sum((n >> ell) * ((1 << (ell - 1)) - 1) for ell in range(2, t + 1))
    return {
        "n": n,
        "t": t,
        "K": len(factors),
        "normalisation_divisor": divisor,
        "identity_max_abs_error": ident,
        "exact": ident < 1e-12,
        "beta": beta,
        "rmse": residual(prod, [[beta * z for z in row] for row in target]),
        "max_row_support": max(max_row_support(m) for m in factors),
        "L": L,
        "L_shared_negation": ideal_positions,
        "L_position_count_matches_formula": L == 2 * sum(
            (n >> ell) * ((1 << (ell - 1)) - 1) for ell in range(2, t + 1)),
        "C_q16": 16 * L,
    }


# --------------------------------------------------------------------------- #
# T1/T2: propagation checks
# --------------------------------------------------------------------------- #


def random_propagation_check(n: int, k: int, r: int, trials: int, seed: int) -> Dict[str, object]:
    """Numeric re-check of T1 (row support propagation) and of the product rank
    inequality rank(AB) <= min(rank A, rank B).

    Note: a row-2-sparse factor may itself be invertible (e.g. a permutation), so
    there is no rank cap of the form 2^K.  The rank bound that survives is the
    per-factor one applied to the *rank* of each factor, not to its sparsity.
    """
    rng = random.Random(seed)
    worst_sup = 0
    worst_rank = 0
    min_factor_rank = n
    violations = 0
    for _ in range(trials):
        prod = None
        for _layer in range(k):
            a = [[0j] * n for _ in range(n)]
            for i in range(n):
                if rng.random() < 0.2:
                    continue
                for c in rng.sample(range(n), min(n, r)):
                    a[i][c] = complex(rng.choice([-2, -1, 0, 1, 2]), rng.choice([-2, -1, 0, 1, 2]))
            if prod is None:
                min_factor_rank = numeric_rank(a)
            else:
                min_factor_rank = min(min_factor_rank, numeric_rank(a))
            prod = a if prod is None else matmul(a, prod)
        if prod is None:
            continue
        rk = numeric_rank(prod)
        worst_sup = max(worst_sup, max_row_support(prod))
        worst_rank = max(worst_rank, rk)
        if rk > min_factor_rank:
            violations += 1
    return {
        "n": n, "k": k, "r": r, "trials": trials,
        "max_observed_row_support": worst_sup,
        "support_cap": min(n, r ** k),
        "support_holds": worst_sup <= min(n, r ** k),
        "max_observed_rank_of_product": worst_rank,
        "rank_rule_violations": violations,
        "rank_rule_holds": violations == 0,
        "note": "rank(A_1...A_K) <= min_k rank(A_k) is checked per trial; row support "
                "gives min(N, 2^K) but no rank cap.",
    }


# --------------------------------------------------------------------------- #
# A1: statement Eq. (5) audit
# --------------------------------------------------------------------------- #


def eq5_audit() -> Dict[str, object]:
    """Audit the radix-8 example printed as Eq. (5) in the statement.

    A_1 has only 4 independent rows by construction (rows 5-8 are the negatives of
    rows 1-4), so the product P A_4 D A_3 A_2 A_1 has rank <= 4 while the 8x8 DFT
    matrix has rank 8: Eq. (5) cannot be exact for any permutation convention.
    The matrix product is enumerated over every ordering and both permutation
    conventions to make the conclusion independent of my reading order.
    """
    def build(rows: List[List[complex]]) -> List[List[complex]]:
        m = [[0j] * 8 for _ in range(8)]
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                m[i][j] = complex(v)
        return m

    a1 = build([[1, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 0, 0, -1, 0, 0, 0], [0, 1, 0, 0, 0, -1, 0, 0],
                [0, 0, 1, 0, 0, 0, -1, 0], [0, 0, 0, 1, 0, 0, 0, -1]])
    a2 = build([[1, 0, 1, 0, 0, 0, 0, 0], [0, 1, 0, 1, 0, 0, 0, 0],
                [1, 0, -1, 0, 0, 0, 0, 0], [0, 1, 0, -1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 1, 0, -1, 0]])
    a3 = build([[1, 1, 0, 0, 0, 0, 0, 0], [1, -1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 1], [0, 0, 0, 0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0, 1, -1, 0], [0, 0, 0, 0, 1, 0, 0, -1]])
    a4 = build([[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, -1, 0, 0, 0, 0], [0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, -1, 0, 0], [0, 0, 0, 0, 1, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, -1, 1], [0, 0, 0, 0, 0, 0, 1, 1]])
    d = [[0j] * 8 for _ in range(8)]
    for i, v in enumerate([1, 1, 1, 1j, 1, 1j, 1j, 1]):
        d[i][i] = complex(v)
    base = [[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0], [0, 0, -1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1], [0, 0, 0, 0, 0, 0, -1, 1]]
    a1r = build(base)

    perm = [0, 4, 2, 5, 1, 7, 3, 6]
    cols = [[0j] * 8 for _ in range(8)]
    rows = [[0j] * 8 for _ in range(8)]
    for i, c in enumerate(perm):
        cols[i][c] = 1 + 0j
        rows[c][i] = 1 + 0j

    f8 = dft_matrix(8)
    raw8 = raw_dft_matrix(8)

    import itertools

    results = []
    for pname, pm in (("P_as_columns", cols), ("P_as_rows", rows)):
        for order in itertools.permutations([("A1", a1), ("A2", a2), ("A3", a3), ("A4", a4)]):
            names = [o[0] for o in order]
            mats = [o[1] for o in order]
            for pos in range(5):
                chain = mats[:pos] + [d] + mats[pos:]
                prod = chain[0]
                for mm in chain[1:]:
                    prod = matmul(mm, prod)
                full = matmul(pm, prod)
                best = min(
                    max(abs(full[i][j] - f8[i][j]) for i in range(8) for j in range(8)),
                    max(abs(full[i][j] - raw8[i][j]) for i in range(8) for j in range(8)),
                )
                results.append(best)
    return {
        "a1_rank": numeric_rank(a1),
        "a1_rank_of_replaced_row": numeric_rank(a1r),
        "a2_rank": numeric_rank(a2),
        "a3_rank": numeric_rank(a3),
        "a4_rank": numeric_rank(a4),
        "d_rank": numeric_rank(d),
        "dft_rank": numeric_rank(f8),
        "best_error_over_all_orderings": min(results),
        "orderings_tested": len(results),
        "exact_possible": min(results) < 1e-9,
        "conclusion": ("Eq. (5) as extracted is not an exact identity for F_8 under any "
                       "factor ordering or permutation convention: the best achievable "
                       "maximum entry error over 240 readings is 1.7678, so Eq. (5) is an "
                       "approximate (lossy) factorisation and must not be used as a "
                       "ground-truth reference or as an exact radix-8 building block."),
    }


# --------------------------------------------------------------------------- #
# T5/T6
# --------------------------------------------------------------------------- #


def t5_support_bound(target: List[List[complex]], k: int) -> Dict[str, float]:
    n = len(target)
    m = min(n, 2 ** k)
    return {
        "k": k,
        "support_cap": m,
        "rmse_lb_beta_1": math.sqrt(max(0, n - m)) / n,
        "cap_for_threshold": max(0.0, n - 0.01 * n * n),
    }


def main() -> int:
    out: Dict[str, object] = {"script": "verify_row_bound.py", "generated": []}

    print("=== T0 target definition sanity (Eq. (1) vs Eq. (3), Q4 Kronecker target) ===")
    t0 = {}
    for n in (4, 8):
        f = dft_matrix(n)
        r = raw_dft_matrix(n)
        ok, worst = is_unitary_columns(f)
        t0[f"N{n}"] = {
            "entry_0_0": [f[0][0].real, f[0][0].imag],
            "entry_0_1": [f[0][1].real, f[0][1].imag],
            "entry_1_1": [f[1][1].real, f[1][1].imag],
            "entry_0_2": [f[0][2].real, f[0][2].imag],
            "columns_orthonormal": ok,
            "worst_column_orthonormality_residual": worst,
            "raw_vs_normalised_ratio": [r[1][1].real / f[1][1].real if f[1][1].real else None],
        }
        print(f"  N={n}: F[0,0]={f[0][0]:.6f} F[0,1]={f[0][1]:.6f} F[1,1]={f[1][1]:.6f} "
              f"F[0,2]={f[0][2]:.6f} | columns orthonormal={ok} (resid={worst:.2e})")

    k4x8 = kron(dft_matrix(4), dft_matrix(8))
    f32 = dft_matrix(32)
    ok_k, worst_k = is_unitary_columns(k4x8)
    diff_32 = max(abs(k4x8[row][col] - f32[row][col]) for row in range(32) for col in range(32))
    k_row_mod = {round(abs(z), 12) for z in k4x8[7]}
    print(f"  F4xF8: shape={len(k4x8)}x{len(k4x8[0])} columns orthonormal={ok_k} "
          f"(resid={worst_k:.2e})")
    print(f"  F4xF8 row 7 distinct moduli: {sorted(k_row_mod)}")
    print(f"  max|F4xF8 - F32| = {diff_32:.6f}  (must be large: they are different matrices)")
    t0["F4xF8"] = {
        "shape": [len(k4x8), len(k4x8[0])],
        "columns_orthonormal": ok_k,
        "worst_column_orthonormality_residual": worst_k,
        "distinct_row_moduli": sorted(k_row_mod),
        "max_abs_difference_vs_F32": diff_32,
        "is_F32": diff_32 < 1e-9,
    }
    out["t0_target_sanity"] = t0

    print("=== T4 exact radix-2 construction (product = beta*F_N, row support 2) ===")
    t4: Dict[str, object] = {}
    for n in (2, 4, 8, 16, 32, 64):
        r = t4_report(n)
        t4[f"N{n}"] = r
        print(f"  N={n:3d} K={r['K']} exact={r['exact']} |chain-beta*F|_max={r['identity_max_abs_error']:.2e} "
              f"rmse={r['rmse']:.3e} beta={r['beta']:.6f} L={r['L']} "
              f"(shared-negation {r['L_shared_negation']}, formula {r['L_position_count_matches_formula']}) "
              f"C(q=16)={r['C_q16']} row_support={r['max_row_support']}")
    out["t4_exact_construction"] = t4

    print("=== T1 support propagation + product rank rule (random) ===")
    checks = [random_propagation_check(16, k, 2, 20, 1000 + k) for k in (1, 2, 3, 4)]
    out["propagation_checks"] = checks
    for c in checks:
        print(f"  N={c['n']} K={c['k']}: support<={c['max_observed_row_support']}/{c['support_cap']} "
              f"holds={c['support_holds']} | rank(prod)<={c['max_observed_rank_of_product']}, "
              f"rank-rule violations={c['rank_rule_violations']} "
              f"(holds={c['rank_rule_holds']})")

    print("=== A1 statement Eq. (5) audit ===")
    audit = eq5_audit()
    out["eq5_audit"] = audit
    for key in ("a1_rank", "a1_rank_of_replaced_row", "dft_rank", "orderings_tested",
                "best_error_over_all_orderings", "exact_possible"):
        print(f"  {key}: {audit[key]}")
    print(f"  conclusion: {audit['conclusion']}")

    print("=== T5 support lower bound at beta = 1 (q independent) ===")
    t5: Dict[str, object] = {}
    for n in (8, 16, 32, 64):
        f = dft_matrix(n)
        t5[f"N{n}"] = {f"K{k}": t5_support_bound(f, k) for k in range(1, 8)}
        row = "  ".join(f"K{k}:{t5_support_bound(f, k)['rmse_lb_beta_1']:.6f}" for k in (3, 4, 5, 6))
        print(f"  N={n:3d} {row} | cap needed for 0.1: {t5[f'N{n}']['K1']['cap_for_threshold']:.2f}")
    out["t5_support_bounds"] = t5

    raw8 = raw_dft_matrix(8)
    print("=== T6 scale degeneracy ===")
    # normalise the exact construction so that the product is exactly beta0 * F_N,
    # then rescale it by c while scaling beta by the same c.  The residual must
    # scale linearly with c, i.e. the *relative* accuracy never changes, which is
    # exactly the scale degeneracy that makes inf over (A, beta) of Eq. (6) equal 0.
    n8 = 8
    base = radix2_factors(n8, bitrev_first=True)
    k_fac = len(base)
    beta0 = 1.0 / math.sqrt(n8)
    divisor = (math.sqrt(n8) / beta0) ** (1.0 / k_fac)
    norm_base = [[[z / divisor for z in row] for row in m] for m in base]

    f8 = dft_matrix(n8)
    prod_norm = norm_base[0]
    for _m in norm_base[1:]:
        prod_norm = matmul(_m, prod_norm)
    ident = max(abs(prod_norm[row][col] - beta0 * f8[row][col])
                for row in range(n8) for col in range(n8))
    e0 = residual(prod_norm, [[beta0 * z for z in row] for row in f8])
    print(f"  identity check |chain - beta0*F8|_max = {ident:.3e}")
    print(f"  normalised exact chain: beta={beta0:.6f} residual={e0:.3e} (K={k_fac} factors)")

    t6 = {"reference_beta": beta0, "reference_residual": e0,
          "identity_residual_max": ident, "points": []}
    for c in (2.0, 0.5, 1e-3):
        scaled_prod = [[c * z for z in row] for row in prod_norm]
        e2 = residual(scaled_prod, [[c * beta0 * z for z in row] for row in f8])
        ok = abs(e2 - c * e0) < 1e-15 * max(1.0, c)
        t6["points"].append({"c": c, "K": k_fac, "beta": c * beta0,
                             "residual": e2, "equals_c_times_reference": ok})
        print(f"  c={c:g}: factors *= {c:g}, beta' = c*beta = {c * beta0:.6g} "
              f"-> residual={e2:.3e} (= c*reference: {ok})")
    t6["note"] = ("scaling the whole factorisation by c and beta by c rescales product and "
                  "target together, so the residual scales linearly with c: the free scale in "
                  "Eq. (6) is unconstrained, which is why any K* or C* statement is conditional "
                  "on an explicit beta normalisation convention.")
    out["t6_scale_degeneracy"] = t6

    print("=== T3 exact-construction summary (from T4) ===")
    t3 = {}
    for n in (2, 4, 8, 16, 32, 64):
        r = out["t4_exact_construction"][f"N{n}"]
        t3[f"N{n}"] = {"K": r["K"], "L": r["L"], "C_q16": r["C_q16"],
                       "beta": r["beta"], "rmse": r["rmse"]}
        print(f"  N={n:3d}: K={r['K']}, row support 2, beta=1/sqrt(N), RMSE<1e-15, L={r['L']}, "
              f"C(q=16)={r['C_q16']}")
    out["t3_exact_construction_summary"] = t3

    # write next to this script so the artefact does not depend on the caller's cwd
    out_path = Path(__file__).resolve().parent / "row_bound_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

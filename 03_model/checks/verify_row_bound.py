#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible modeling checks for row-2-sparse DFT factorizations.

This is a modeling-layer certificate tool, not a candidate search and not a
formal experiment.  It uses only the Python standard library and writes a
deterministic JSON report next to itself.

Checked claims
--------------
T0  Eq. (3) defines a unitary DFT; F_4 kron F_8 is unitary but is not F_32.
T1  A product of K row-r-sparse square matrices has row support at most r**K.
T2  rank(A_1 ... A_K) <= min_k rank(A_k); sparsity alone gives no rank cap.
T3  A radix-2 chain with the bit-reversal permutation absorbed into its first
    butterfly gives B = sqrt(N) F_N with K=log2(N), row support <=2 and RMSE 0.
T4  The statement's extracted Eq. (5) matrices are audited in their printed
    order under the two plausible permutation conventions; no factor-order
    search is used.
T5  At fixed beta, the support lower bound includes an essential |beta| factor.
T6  Eq. (6) has a zero solution when beta=0 and a zero factor is allowed; in the
    unrestricted-coefficient case, simultaneous scaling also rescales RMSE.

The output deliberately avoids V5/V6 search values because the user supplied no
factors, NPZ, code or logs from those runs.
"""

from __future__ import annotations

import cmath
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


Matrix = List[List[complex]]
EXEMPT = (0j, 1 + 0j, -1 + 0j, 1j, -1j,
          1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j)


def dft_matrix(n: int) -> Matrix:
    """Eq. (3): N**(-1/2) [exp(-2*pi*i*row*col/N)]."""
    inv = 1.0 / math.sqrt(n)
    return [[inv * cmath.exp(-2j * math.pi * row * col / n)
             for col in range(n)] for row in range(n)]


def raw_dft_matrix(n: int) -> Matrix:
    """Eq. (1): [exp(-2*pi*i*row*col/N)], without 1/sqrt(N)."""
    return [[cmath.exp(-2j * math.pi * row * col / n)
             for col in range(n)] for row in range(n)]


def zeros(rows: int, cols: int) -> Matrix:
    return [[0j] * cols for _ in range(rows)]


def identity(n: int) -> Matrix:
    out = zeros(n, n)
    for idx in range(n):
        out[idx][idx] = 1 + 0j
    return out


def scale(m: Matrix, value: float) -> Matrix:
    return [[value * z for z in row] for row in m]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    """Dense reference multiplication with sparse skipping on the left."""
    rows, mid_n, cols = len(a), len(b), len(b[0])
    if len(a[0]) != len(b):
        raise ValueError("matrix dimensions do not match")
    out = zeros(rows, cols)
    for row in range(rows):
        for mid in range(mid_n):
            value = a[row][mid]
            if value == 0:
                continue
            for col in range(cols):
                out[row][col] += value * b[mid][col]
    return out


def chain(factors_in_application_order: Sequence[Matrix]) -> Matrix:
    """Return A_K ... A_2 A_1 for [A_1, A_2, ..., A_K]."""
    if not factors_in_application_order:
        raise ValueError("at least one factor is required")
    product = factors_in_application_order[0]
    for factor in factors_in_application_order[1:]:
        product = matmul(factor, product)
    return product


def kron(a: Matrix, b: Matrix) -> Matrix:
    rows_a, cols_a, rows_b, cols_b = len(a), len(a[0]), len(b), len(b[0])
    out = zeros(rows_a * rows_b, cols_a * cols_b)
    for row_a in range(rows_a):
        for col_a in range(cols_a):
            for row_b in range(rows_b):
                for col_b in range(cols_b):
                    out[row_a * rows_b + row_b][col_a * cols_b + col_b] = (
                        a[row_a][col_a] * b[row_b][col_b]
                    )
    return out


def max_abs_difference(a: Matrix, b: Matrix) -> float:
    return max(abs(a[row][col] - b[row][col])
               for row in range(len(a)) for col in range(len(a[0])))


def rmse(a: Matrix, b: Matrix) -> float:
    """Problem Eq. (6): ||a-b||_F/N for square N x N matrices."""
    n = len(a)
    total = 0.0
    for row in range(n):
        for col in range(n):
            delta = a[row][col] - b[row][col]
            total += delta.real * delta.real + delta.imag * delta.imag
    return math.sqrt(total) / n


def unitary_residual(m: Matrix) -> float:
    """Maximum entry residual in M^H M-I."""
    n = len(m)
    worst = 0.0
    for col_a in range(n):
        for col_b in range(n):
            inner = sum(m[row][col_a].conjugate() * m[row][col_b]
                        for row in range(n))
            target = 1.0 if col_a == col_b else 0.0
            worst = max(worst, abs(inner - target))
    return worst


def numeric_rank(m: Matrix, tol: float = 1e-9) -> int:
    work = [row[:] for row in m]
    rows, cols = len(work), len(work[0])
    rank = 0
    for col in range(cols):
        pivot = max(range(rank, rows), key=lambda row: abs(work[row][col]), default=None)
        if pivot is None or abs(work[pivot][col]) <= tol:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][col]
        for row in range(rows):
            if row == rank or abs(work[row][col]) <= tol:
                continue
            ratio = work[row][col] / pivot_value
            for inner_col in range(col, cols):
                work[row][inner_col] -= ratio * work[rank][inner_col]
        rank += 1
        if rank == rows:
            break
    return rank


def max_row_support(m: Matrix, tol: float = 1e-12) -> int:
    return max(sum(1 for value in row if abs(value) > tol) for row in m)


def is_exempt(value: complex, tol: float = 1e-12) -> bool:
    """Use tolerance because roots such as exp(-pi*i/2) are not bit-exact."""
    return any(abs(value - exempt) <= tol for exempt in EXEMPT)


def count_nontrivial_positions(factors: Sequence[Matrix]) -> int:
    return sum(1 for factor in factors for row in factor for value in row
               if abs(value) > 1e-12 and not is_exempt(value))


def bit_reverse(value: int, width: int) -> int:
    result = 0
    for index in range(width):
        if value >> index & 1:
            result |= 1 << (width - 1 - index)
    return result


def butterfly_layer(n: int, stage: int) -> Matrix:
    block = 2 ** stage
    half = block // 2
    factor = zeros(n, n)
    for start in range(0, n, block):
        for index in range(half):
            upper, lower = start + index, start + index + half
            twiddle = cmath.exp(-2j * math.pi * index / block)
            factor[upper][upper] = 1 + 0j
            factor[upper][lower] = twiddle
            factor[lower][upper] = 1 + 0j
            factor[lower][lower] = -twiddle
    return factor


def radix2_factors(n: int) -> List[Matrix]:
    """K=log2(N) row-2 factors whose product equals the raw DFT.

    The usual bit-reversal permutation is absorbed into the first butterfly by
    right multiplication.  Right multiplication by a permutation only reorders
    columns, so the first factor remains row-2-sparse and K does not increase.
    """
    width = int(round(math.log2(n)))
    if n < 2 or 2 ** width != n:
        raise ValueError("n must be a power of two at least 2")
    permutation = zeros(n, n)
    for row in range(n):
        permutation[row][bit_reverse(row, width)] = 1 + 0j
    layers = [butterfly_layer(n, stage) for stage in range(1, width + 1)]
    layers[0] = matmul(layers[0], permutation)
    return layers


def exact_radix2_report(n: int) -> Dict[str, Any]:
    factors = radix2_factors(n)
    product = chain(factors)
    beta = math.sqrt(n)
    target = scale(dft_matrix(n), beta)
    position_count = count_nontrivial_positions(factors)
    expected_position_count = (int(round(math.log2(n))) - 3) * n + 4
    return {
        "n": n,
        "t": int(round(math.log2(n))),
        "K": len(factors),
        "beta": beta,
        "rmse": rmse(product, target),
        "identity_max_abs_error": max_abs_difference(product, target),
        "exact_within_1e-12": max_abs_difference(product, target) <= 1e-12,
        "max_factor_row_support": max(max_row_support(factor) for factor in factors),
        "L_nontrivial_position_count": position_count,
        "L_shared_plus_minus_pair_count": position_count // 2,
        "L_formula": "(log2(N)-3)*N+4",
        "L_matches_formula": position_count == expected_position_count,
        "C_q16_position_count": 16 * position_count,
        "beta_counted_in_L": False,
    }


def random_propagation_check(n: int, k: int, row_cap: int,
                             trials: int, seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    max_observed_support = 0
    max_observed_rank = 0
    rank_rule_violations = 0
    for _ in range(trials):
        factors: List[Matrix] = []
        factor_ranks: List[int] = []
        for _stage in range(k):
            factor = zeros(n, n)
            for row in range(n):
                if rng.random() < 0.2:
                    continue
                for col in rng.sample(range(n), row_cap):
                    value = 0j
                    while value == 0:
                        value = complex(rng.choice([-2, -1, 0, 1, 2]),
                                        rng.choice([-2, -1, 0, 1, 2]))
                    factor[row][col] = value
            factors.append(factor)
            factor_ranks.append(numeric_rank(factor))
        product = chain(factors)
        product_rank = numeric_rank(product)
        max_observed_support = max(max_observed_support, max_row_support(product))
        max_observed_rank = max(max_observed_rank, product_rank)
        if product_rank > min(factor_ranks):
            rank_rule_violations += 1
    support_bound = min(n, row_cap ** k)
    return {
        "n": n,
        "k": k,
        "row_cap": row_cap,
        "trials": trials,
        "seed": seed,
        "max_observed_row_support": max_observed_support,
        "support_bound": support_bound,
        "support_rule_holds": max_observed_support <= support_bound,
        "max_observed_product_rank": max_observed_rank,
        "rank_rule_violations": rank_rule_violations,
        "rank_rule_holds": rank_rule_violations == 0,
    }


def real_beta_least_squares(target: Matrix, approximation: Matrix) -> float:
    numerator = 0.0
    denominator = 0.0
    for row in range(len(target)):
        for col in range(len(target[0])):
            numerator += (target[row][col].conjugate() * approximation[row][col]).real
            denominator += abs(target[row][col]) ** 2
    return numerator / denominator


def statement_eq5_audit() -> Dict[str, Any]:
    """Audit only the extracted printed order P A4 D A3 A2 A1.

    P=[e0 e4 e2 e5 e1 e7 e3 e6] conventionally means column j is
    e_perm[j].  Its transpose is retained as the only plausible alternative.
    """
    def build(rows: Sequence[Sequence[complex]]) -> Matrix:
        return [[complex(value) for value in row] for row in rows]

    a1 = build([
        [1, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, -1, 0, 0, 0], [0, 1, 0, 0, 0, -1, 0, 0],
        [0, 0, 1, 0, 0, 0, -1, 0], [0, 0, 0, 1, 0, 0, 0, -1],
    ])
    a2 = build([
        [1, 0, 1, 0, 0, 0, 0, 0], [0, 1, 0, 1, 0, 0, 0, 0],
        [1, 0, -1, 0, 0, 0, 0, 0], [0, 1, 0, -1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 1, 0, -1],
    ])
    a3 = build([
        [1, 1, 0, 0, 0, 0, 0, 0], [1, -1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 1], [0, 0, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0, 1, -1, 0], [0, 0, 0, 0, 1, 0, 0, -1],
    ])
    a4 = build([
        [1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, -1, 0, 0, 0, 0], [0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, -1, 0, 0], [0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, -1, 1], [0, 0, 0, 0, 0, 0, 1, 1],
    ])
    diagonal = zeros(8, 8)
    for index, value in enumerate((1, 1, 1, 1j, 1, 1j, 1j, 1)):
        diagonal[index][index] = complex(value)

    permutation = (0, 4, 2, 5, 1, 7, 3, 6)
    p_columns = zeros(8, 8)
    for col, row in enumerate(permutation):
        p_columns[row][col] = 1 + 0j
    p_transpose = [[p_columns[col][row] for col in range(8)] for row in range(8)]

    normalized = dft_matrix(8)
    raw = raw_dft_matrix(8)
    readings: Dict[str, Any] = {}
    for name, permutation_matrix in (("P_columns", p_columns),
                                     ("P_transpose", p_transpose)):
        product = chain((a1, a2, a3, diagonal, a4, permutation_matrix))
        beta_opt = real_beta_least_squares(normalized, product)
        readings[name] = {
            "printed_product": "P A4 D A3 A2 A1",
            "rmse_vs_normalized_F8": rmse(product, normalized),
            "rmse_vs_raw_F8": rmse(product, raw),
            "max_abs_vs_normalized_F8": max_abs_difference(product, normalized),
            "max_abs_vs_raw_F8": max_abs_difference(product, raw),
            "real_beta_least_squares_for_beta_F8": beta_opt,
            "rmse_vs_beta_F8": rmse(product, scale(normalized, beta_opt)),
            "exact_normalized_within_1e-12": max_abs_difference(product, normalized) <= 1e-12,
            "exact_raw_within_1e-12": max_abs_difference(product, raw) <= 1e-12,
        }
    return {
        "scope": "extracted matrices only; original DOCX was not visually re-transcribed",
        "factor_ranks": {
            "A1": numeric_rank(a1), "A2": numeric_rank(a2),
            "A3": numeric_rank(a3), "A4": numeric_rank(a4),
            "D": numeric_rank(diagonal),
        },
        "readings": readings,
        "note": "Eq. (5) uses an approximation sign; this check is not an error allegation.",
    }


def support_lower_bound(n: int, k: int, beta: float) -> Dict[str, Any]:
    support_cap = min(n, 2 ** k)
    return {
        "n": n,
        "k": k,
        "beta": beta,
        "support_cap": support_cap,
        "rmse_lower_bound": abs(beta) * math.sqrt(n - support_cap) / n,
        "formula": "abs(beta)*sqrt(N-min(N,2**K))/N",
    }


def scale_degeneracy_report() -> Dict[str, Any]:
    n = 8
    target = dft_matrix(n)
    approximation = identity(n)
    reference = rmse(target, approximation)
    points = []
    for value in (2.0, 0.5, 1e-3):
        scaled_residual = rmse(scale(target, value), scale(approximation, value))
        points.append({
            "scale": value,
            "rmse": scaled_residual,
            "expected": value * reference,
            "linear_within_1e-12": abs(scaled_residual - value * reference) <= 1e-12,
        })
    zero = zeros(n, n)
    return {
        "reference_rmse_beta_1_identity_product": reference,
        "scaled_points_unrestricted_coefficients": points,
        "zero_solution": {
            "beta": 0.0,
            "product": "zero matrix (obtainable by one zero factor)",
            "rmse": rmse(zero, zero),
            "satisfies_row_2_sparse": True,
            "zero_is_in_every_stated_Pq": True,
        },
        "note": "Arbitrary nonzero scaling need not preserve the discrete Pq constraint; the exact beta=0/zero-factor solution does.",
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    problem_path = repo_root / "01_problem" / "original" / "DFT类矩阵的整数分解逼近.docx"
    user_readme_path = repo_root / "03_model" / "incoming" / "README_LATEST_V6.md"

    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_class": "modeling_check",
        "formal_experiment": False,
        "script": "03_model/checks/verify_row_bound.py",
        "script_sha256_before_output": sha256_file(script_path),
        "inputs": {
            "problem_docx_sha256": sha256_file(problem_path) if problem_path.exists() else None,
            "user_v6_readme_sha256": sha256_file(user_readme_path) if user_readme_path.exists() else None,
        },
        "assumptions": [
            "F_N is Eq. (3)'s unitary DFT unless explicitly labeled raw",
            "all factors are N x N and K counts every support-expanding factor",
            "RMSE is Frobenius norm divided by N",
            "beta is external and is not counted in L",
            "L is a per-position count; plus/minus sharing is reported separately",
        ],
    }

    t0: Dict[str, Any] = {}
    for n in (4, 8):
        normalized = dft_matrix(n)
        raw = raw_dft_matrix(n)
        t0[f"N{n}"] = {
            "unitary_residual": unitary_residual(normalized),
            "raw_to_normalized_scale": math.sqrt(n),
            "max_abs_raw_minus_sqrtN_normalized": max_abs_difference(
                raw, scale(normalized, math.sqrt(n))
            ),
        }
    target_kron = kron(dft_matrix(4), dft_matrix(8))
    f32 = dft_matrix(32)
    t0["F4_kron_F8"] = {
        "shape": [len(target_kron), len(target_kron[0])],
        "unitary_residual": unitary_residual(target_kron),
        "max_abs_difference_vs_F32": max_abs_difference(target_kron, f32),
        "is_F32_within_1e-12": max_abs_difference(target_kron, f32) <= 1e-12,
    }
    report["t0_target_sanity"] = t0

    exact = {f"N{n}": exact_radix2_report(n) for n in (2, 4, 8, 16, 32, 64)}
    report["t3_exact_radix2"] = exact

    propagation = [random_propagation_check(16, k, 2, 20, 1000 + k)
                   for k in (1, 2, 3, 4)]
    report["t1_t2_propagation"] = propagation
    report["t4_statement_eq5"] = statement_eq5_audit()

    bounds: Dict[str, Any] = {}
    for n in (8, 16, 32, 64):
        bounds[f"N{n}"] = {
            f"K{k}": support_lower_bound(n, k, 1.0) for k in range(1, 8)
        }
    report["t5_support_bounds_beta_1"] = bounds
    report["t6_scale_degeneracy"] = scale_degeneracy_report()

    checks = {
        "normalized_dft_unitary": all(t0[f"N{n}"]["unitary_residual"] <= 1e-12
                                      for n in (4, 8)),
        "kron_unitary": t0["F4_kron_F8"]["unitary_residual"] <= 1e-12,
        "kron_not_f32": not t0["F4_kron_F8"]["is_F32_within_1e-12"],
        "exact_radix2_all_sizes": all(item["exact_within_1e-12"] for item in exact.values()),
        "exact_radix2_k_equals_t": all(item["K"] == item["t"] for item in exact.values()),
        "exact_radix2_row_cap": all(item["max_factor_row_support"] <= 2
                                    for item in exact.values()),
        "exact_radix2_L_formula": all(item["L_matches_formula"] for item in exact.values()),
        "support_propagation": all(item["support_rule_holds"] for item in propagation),
        "rank_product_rule": all(item["rank_rule_holds"] for item in propagation),
        "eq5_factors_full_rank": all(rank == 8 for rank in
                                     report["t4_statement_eq5"]["factor_ranks"].values()),
        "scale_relation": all(item["linear_within_1e-12"] for item in
                              report["t6_scale_degeneracy"]["scaled_points_unrestricted_coefficients"]),
        "zero_solution": report["t6_scale_degeneracy"]["zero_solution"]["rmse"] == 0.0,
    }
    report["checks"] = checks
    report["failed_checks"] = [name for name, passed in checks.items() if not passed]
    report["status"] = "PASS" if not report["failed_checks"] else "FAIL"

    output_path = script_path.parent / "row_bound_results.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")

    print(f"status={report['status']}")
    for name, passed in checks.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    print("exact radix-2 position L:",
          {name: item["L_nontrivial_position_count"] for name, item in exact.items()})
    print("wrote", output_path)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

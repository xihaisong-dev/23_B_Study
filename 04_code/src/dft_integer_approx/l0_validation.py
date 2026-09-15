# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: each L0 assertion emits machine-readable evidence and fails closed.
"""Frozen-protocol L0 mathematical, input, and implementation checks."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict

from .baselines import approximate_matrix, exact_q1_baseline
from .constraints import check_alphabet, check_row_sparse
from .hardware import count_nontrivial_positions, hardware_complexity
from .metrics import max_abs_difference, rmse
from .targets import dft_matrix, kron, matmul, product


def support_rmse_lower_bound(n: int, k: int) -> float:
    if n < 1 or k < 1:
        raise ValueError("n and k must be positive")
    return math.sqrt(n - min(n, 2 ** k)) / n


def gaussian_integer_rmse_lower_bound(n: int) -> float:
    """Exact lattice bound for products of Gaussian-integer factor matrices.

    Products of matrices whose real and imaginary parts are integers remain in
    ``Z[i]``.  For entry modulus ``r=1/sqrt(n)``, the reverse triangle inequality
    gives distance at least ``min(r, 1-r)`` to every Gaussian integer: zero gives
    the first branch and every nonzero lattice point has modulus at least one.
    Applying this per entry gives the same RMSE lower bound.
    """
    if n < 2:
        raise ValueError("registered DFT sizes require n>=2")
    radius = 1.0 / math.sqrt(n)
    return min(radius, 1.0 - radius)


def run_l0_checks(workspace: Path) -> Dict[str, Any]:
    checks = []

    manifest = json.loads((workspace / "00_admin/input_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = workspace / item["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        _record(checks, f"input_sha256:{item['path']}", actual == item["sha256"], {"expected": item["sha256"], "actual": actual})

    for n in (2, 4, 8, 16, 32, 64):
        target = dft_matrix(n)
        gram = _conjugate_transpose_product(target)
        identity_error = max(abs(gram[r][c] - (1 if r == c else 0)) for r in range(n) for c in range(n))
        _record(checks, f"unitary_F{n}", identity_error <= 1e-12, {"max_identity_error": identity_error})

    f2 = dft_matrix(2)
    inv_sqrt2 = 1 / math.sqrt(2)
    expected_f2 = [[inv_sqrt2, inv_sqrt2], [inv_sqrt2, -inv_sqrt2]]
    _record(checks, "hand_check_F2", max_abs_difference(f2, expected_f2) <= 1e-12, {"max_difference": max_abs_difference(f2, expected_f2)})
    expected_f4_11 = -0.5j
    _record(checks, "zero_based_F4_1_1", abs(dft_matrix(4)[1][1] - expected_f4_11) <= 1e-12, {"actual": _complex_pair(dft_matrix(4)[1][1])})

    kron_target = kron(dft_matrix(4), dft_matrix(8))
    f32 = dft_matrix(32)
    kron_difference = max_abs_difference(kron_target, f32)
    _record(checks, "F4_kron_F8_not_F32", kron_difference > 1e-3, {"max_difference": kron_difference})

    a = [[1 + 0j, 1 + 0j], [0j, 1 + 0j]]
    b = [[1 + 0j, 0j], [1 + 0j, 1 + 0j]]
    ab = matmul(a, b)
    ba = matmul(b, a)
    _record(checks, "factor_order_A1_A2", product([a, b]) == ab and ab != ba, {"AB": _matrix_pairs(ab), "BA": _matrix_pairs(ba)})

    legal = [[1 + 0j, 2 + 4j], [1 + 2j, 0j]]
    row_ok, row_errors = check_row_sparse(legal, 2)
    alphabet_ok, alphabet_errors = check_alphabet(legal, 3)
    l_value = count_nontrivial_positions([legal])
    c_value = hardware_complexity([legal], 3)
    _record(checks, "row_support_hand_check", row_ok, {"errors": row_errors})
    _record(checks, "P3_hand_check", alphabet_ok, {"errors": alphabet_errors})
    _record(checks, "L_C_hand_check", l_value == 2 and c_value == 6, {"L": l_value, "C": c_value})

    bound = support_rmse_lower_bound(64, 5)
    _record(checks, "support_bound_N64_K5", abs(bound - math.sqrt(32) / 64) <= 1e-15, {"bound": bound})

    integer_bound = gaussian_integer_rmse_lower_bound(64)
    _record(checks, "gaussian_integer_bound_N64",
            abs(integer_bound - 0.125) <= 1e-15 and integer_bound > 0.1,
            {"bound": integer_bound, "threshold": 0.1,
             "certificate": "product of P_q matrices lies in Z[i]"})

    exact = exact_q1_baseline(8)
    exact_approx = approximate_matrix(exact.factors, exact.permutation)
    exact_rmse = rmse(dft_matrix(8), exact_approx)
    row_checks = [check_row_sparse(factor, 2)[0] for factor in exact.factors]
    exact_l = count_nontrivial_positions(exact.factors)
    exact_c = hardware_complexity(exact.factors, 16)
    _record(
        checks,
        "radix2_exact_N8",
        exact_rmse <= 1e-12 and all(row_checks) and exact_l == 20 and exact_c == 320,
        {"rmse": exact_rmse, "K": len(exact.factors), "L": exact_l, "C": exact_c},
    )

    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {"schema_version": "3.0", "status": status, "checks": checks}


def _record(checks, check_id: str, passed: bool, evidence: Dict[str, Any]) -> None:
    checks.append({"id": check_id, "status": "PASS" if passed else "FAIL", "evidence": evidence})


def _conjugate_transpose_product(matrix):
    n = len(matrix)
    out = [[0j] * n for _ in range(n)]
    for row in range(n):
        for col in range(n):
            out[row][col] = sum(matrix[mid][row].conjugate() * matrix[mid][col] for mid in range(n))
    return out


def _complex_pair(value):
    return [value.real, value.imag]


def _matrix_pairs(matrix):
    return [[_complex_pair(value) for value in row] for row in matrix]

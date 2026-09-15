# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: this module reloads persisted factors and independently recomputes every reported metric.
"""Independent recomputation path that does not import search metric/product helpers."""

from __future__ import annotations

import cmath
import math
from pathlib import Path
from typing import Any, Dict, Optional

from .factor_artifacts import read_factor_artifact
from .serialization import canonical_matrix_sha256


def verify_artifact(path: Path, problem_id: str, n: int, expected_q: int, row_cap: Optional[int]) -> Dict[str, Any]:
    factors, permutation, q = read_factor_artifact(path)
    if q != expected_q:
        raise ValueError(f"artifact q={q}, expected {expected_q}")
    target = _target(problem_id, n)
    product = _multiply_chain(factors)
    approximation = _right_permute(product, permutation)
    sse = 0.0
    for row in range(n):
        for col in range(n):
            difference = target[row][col] - approximation[row][col]
            sse += difference.real ** 2 + difference.imag ** 2
    alphabet_errors = []
    row_errors = []
    allowed = _alphabet(q)
    free = {0j, 1 + 0j, -1 + 0j, 1j, -1j, 1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j}
    nontrivial = 0
    factor_hashes = []
    for factor_index, factor in enumerate(factors):
        factor_hashes.append(canonical_matrix_sha256(factor))
        for row_index, row in enumerate(factor):
            support = sum(value != 0 for value in row)
            if row_cap is not None and support > row_cap:
                row_errors.append(f"factor {factor_index} row {row_index}: support {support}>{row_cap}")
            for col_index, value in enumerate(row):
                if problem_id != "q1" and (value.real not in allowed or value.imag not in allowed):
                    alphabet_errors.append(f"factor {factor_index}[{row_index},{col_index}]")
                if value not in free:
                    nontrivial += 1
    return {
        "target_sha256": canonical_matrix_sha256(target),
        "factor_sha256s": factor_hashes,
        "rmse": math.sqrt(sse) / n,
        "L": nontrivial,
        "C": q * nontrivial,
        "K": len(factors),
        "row_support_ok": not row_errors,
        "row_support_errors": row_errors,
        "alphabet_ok": not alphabet_errors,
        "alphabet_errors": alphabet_errors,
    }


def _target(problem_id: str, n: int):
    if problem_id != "q4":
        return _dft(n)
    f4, f8 = _dft(4), _dft(8)
    out = [[0j] * 32 for _ in range(32)]
    for r4 in range(4):
        for c4 in range(4):
            for r8 in range(8):
                for c8 in range(8):
                    out[r4 * 8 + r8][c4 * 8 + c8] = f4[r4][c4] * f8[r8][c8]
    return out


def _dft(n: int):
    scale = 1.0 / math.sqrt(n)
    return [[scale * cmath.exp(-2j * math.pi * row * col / n) for col in range(n)] for row in range(n)]


def _multiply_chain(factors):
    if not factors:
        raise ValueError("empty factor chain")
    result = [row[:] for row in factors[0]]
    for factor in factors[1:]:
        n = len(result)
        next_result = [[0j] * n for _ in range(n)]
        for row in range(n):
            for mid in range(n):
                left = result[row][mid]
                if left != 0:
                    for col in range(n):
                        next_result[row][col] += left * factor[mid][col]
        result = next_result
    return result


def _right_permute(matrix, mapping):
    inverse = [0] * len(mapping)
    for row, col in enumerate(mapping):
        inverse[col] = row
    return [[matrix[row][inverse[col]] for col in range(len(mapping))] for row in range(len(mapping))]


def _alphabet(q: int):
    values = {0}
    for exponent in range(q):
        values.add(2 ** exponent)
        values.add(-(2 ** exponent))
    return values

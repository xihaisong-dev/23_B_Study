# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: target scaling, indexing, Kronecker structure, and factor order are L0 checked.
"""Target construction: Eq. (1) raw DFT, Eq. (3) unitary DFT, Kronecker.

Pure standard library.  ``Matrix`` is ``List[List[complex]]``, row-major,
``M[row][col]``.

Convention
----------
``product([A1, A2, ..., AK]) == A1 @ A2 @ ... @ AK``, i.e. the factors are the
leftmost-first matrix product as written in the problem statement Eq. (6)
(``A_1 A_2 ... A_K``).  This is the convention required by
``04_code/V6_VALIDATOR_SPEC.md`` section 4.2.

The modeling layer's ``03_model/checks/verify_row_bound.py`` uses the opposite
"application order" folding (``chain([A1, A2]) == A2 @ A1``).  That file is the
*independent* recompute path referenced by ``02_retrieval/CANDIDATE_SPECS.md``
section 1; the search/validation code must not import these helpers to produce
the RMSE it compares, so the two numbers come from distinct code paths.
"""

from __future__ import annotations

import cmath
import math
from typing import List, Sequence

Matrix = List[List[complex]]


def dft_matrix(n: int) -> Matrix:
    """Eq. (3) unitary DFT: F_N[k, m] = exp(-2j*pi*k*m/N) / sqrt(N)."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")
    inv = 1.0 / math.sqrt(n)
    return [
        [inv * cmath.exp(-2j * math.pi * row * col / n) for col in range(n)]
        for row in range(n)
    ]


def raw_dft_matrix(n: int) -> Matrix:
    """Eq. (1) DFT without the 1/sqrt(N) factor."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")
    return [
        [cmath.exp(-2j * math.pi * row * col / n) for col in range(n)]
        for row in range(n)
    ]


def kron(a: Matrix, b: Matrix) -> Matrix:
    """Kronecker product ``a ⊗ b`` (matches audit A5's F_4 ⊗ F_8 target)."""
    if not a or not b or not a[0] or not b[0]:
        raise ValueError("kron requires non-empty matrices")
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    out = [[0j] * (cols_a * cols_b) for _ in range(rows_a * rows_b)]
    for ra in range(rows_a):
        for ca in range(cols_a):
            av = a[ra][ca]
            for rb in range(rows_b):
                for cb in range(cols_b):
                    out[ra * rows_b + rb][ca * cols_b + cb] = av * b[rb][cb]
    return out


def zeros(rows: int, cols: int) -> Matrix:
    return [[0j] * cols for _ in range(rows)]


def identity(n: int) -> Matrix:
    out = zeros(n, n)
    for i in range(n):
        out[i][i] = 1 + 0j
    return out


def scale(m: Matrix, value: float) -> Matrix:
    return [[value * z for z in row] for row in m]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    """Dense ``a @ b`` with a sparse skip on the left operand."""
    if len(a[0]) != len(b):
        raise ValueError("matrix dimensions do not match")
    rows, mid, cols = len(a), len(b), len(b[0])
    out = zeros(rows, cols)
    for r in range(rows):
        outr = out[r]
        for k in range(mid):
            v = a[r][k]
            if v == 0:
                continue
            bk = b[k]
            for c in range(cols):
                outr[c] += v * bk[c]
    return out


def product(factors: Sequence[Matrix]) -> Matrix:
    """Leftmost-first product ``A1 @ A2 @ ... @ AK`` for ``[A1, ..., AK]``."""
    if not factors:
        raise ValueError("at least one factor is required")
    n = len(factors[0])
    result = factors[0]
    for factor in factors[1:]:
        if len(factor) != n:
            raise ValueError("all factors must be square and equally sized")
        result = matmul(result, factor)
    return result

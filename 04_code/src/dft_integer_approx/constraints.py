# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: exact alphabet and row-support checks are covered by boundary tests.
"""Constraint 1 (row sparsity) and constraint 2 (alphabet) checks.

Constraint 2 alphabet ``P_q = {0, ±2^r : r = 0..q-1}`` is applied to the real and
imaginary parts independently (Cartesian product).  Membership is exact: a float
that is not exactly equal to a ``P_q`` integer fails (no tolerance), matching
``04_code/IMPLEMENTATION_PLAN.md`` section 5.1.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

Matrix = List[List[complex]]


def alphabet_pq(q: int) -> frozenset:
    """``P_q = {0, ±2^0, ..., ±2^(q-1)}`` as exact integers."""
    if not isinstance(q, int) or q < 1:
        raise ValueError(f"q must be a positive integer, got {q!r}")
    values = {0}
    for r in range(q):
        p = 2 ** r
        values.add(p)
        values.add(-p)
    return frozenset(values)


def is_in_alphabet(value: complex, q: int) -> bool:
    """True iff ``real(value)`` and ``imag(value)`` are both exactly in ``P_q``."""
    allowed = alphabet_pq(q)
    return value.real in allowed and value.imag in allowed


def row_nonzero_count(row: Sequence[complex]) -> int:
    return sum(1 for v in row if v != 0)


def max_row_support(matrix: Matrix) -> int:
    return max(row_nonzero_count(row) for row in matrix)


def check_row_sparse(matrix: Matrix, cap: int) -> Tuple[bool, List[str]]:
    """Constraint 1: each row has at most ``cap`` non-zero entries."""
    if not isinstance(cap, int) or cap < 1:
        raise ValueError(f"cap must be a positive integer, got {cap!r}")
    violations: List[str] = []
    for r, row in enumerate(matrix):
        nnz = row_nonzero_count(row)
        if nnz > cap:
            violations.append(f"row {r}: {nnz} nonzeros > cap {cap}")
    return (not violations, violations)


def check_alphabet(matrix: Matrix, q: int) -> Tuple[bool, List[str]]:
    """Constraint 2: every entry has real/imag parts exactly in ``P_q``."""
    violations: List[str] = []
    for r, row in enumerate(matrix):
        for c, v in enumerate(row):
            if not is_in_alphabet(v, q):
                violations.append(f"[{r}][{c}]={v!r} not in P_{q}")
    return (not violations, violations)


def check_finite_square(matrix: Matrix) -> None:
    """Raise ``ValueError`` unless the matrix is non-empty, square and finite."""
    if not matrix:
        raise ValueError("empty matrix")
    n = len(matrix)
    for row in matrix:
        if len(row) != n:
            raise ValueError("matrix must be square")
        for v in row:
            if not (math.isfinite(v.real) and math.isfinite(v.imag)):
                raise ValueError(f"non-finite coefficient {v!r}")

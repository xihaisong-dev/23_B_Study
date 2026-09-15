# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: reported RMSE is recomputed through a separate persisted-artifact path.
"""RMSE and norm primitives, per D-005 (Eq. (6) with beta fixed to 1)."""

from __future__ import annotations

import math
from typing import List

Matrix = List[List[complex]]


def frobenius_norm(a: Matrix) -> float:
    total = 0.0
    for row in a:
        for v in row:
            total += v.real * v.real + v.imag * v.imag
    return math.sqrt(total)


def rmse(target: Matrix, approx: Matrix) -> float:
    """``RMSE = ||target - approx||_F / N`` for N x N matrices (D-005, beta=1)."""
    n = _dimension(target, approx)
    total = 0.0
    for r in range(n):
        tr = target[r]
        ar = approx[r]
        for c in range(n):
            d = tr[c] - ar[c]
            total += d.real * d.real + d.imag * d.imag
    return math.sqrt(total) / n


def max_abs_difference(a: Matrix, b: Matrix) -> float:
    n = _dimension(a, b)
    worst = 0.0
    for r in range(n):
        ar = a[r]
        br = b[r]
        for c in range(n):
            worst = max(worst, abs(ar[c] - br[c]))
    return worst


def _dimension(a: Matrix, b: Matrix) -> int:
    if not a or len(a) != len(b):
        raise ValueError("matrices must be non-empty and equally sized")
    n = len(a)
    for row in a:
        if len(row) != n:
            raise ValueError("matrices must be square")
    for row in b:
        if len(row) != n:
            raise ValueError("matrices must be square")
    return n

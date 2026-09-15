# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: this scorer intentionally imports neither targets nor production metrics.
"""Independent dense scorer used for all search acceptance and patience decisions."""

from __future__ import annotations

from typing import Optional, Sequence


def independent_objective(target, factors, permutation: Optional[Sequence[int]] = None,
                          *, association: str = "left") -> float:
    """Return squared Frobenius error using a standalone multiplication path."""
    if not factors:
        raise ValueError("empty factor chain")
    if association == "right":
        product = [row[:] for row in factors[-1]]
        for factor in reversed(factors[:-1]):
            product = _multiply(factor, product)
    elif association == "left":
        product = [row[:] for row in factors[0]]
        for factor in factors[1:]:
            product = _multiply(product, factor)
    else:
        raise ValueError(f"unknown association {association!r}")
    if permutation is not None:
        inverse = [0] * len(permutation)
        for source, destination in enumerate(permutation):
            inverse[destination] = source
        product = [[row[inverse[column]] for column in range(len(row))]
                   for row in product]
    total = 0.0
    for target_row, actual_row in zip(target, product):
        for expected, actual in zip(target_row, actual_row):
            delta = expected - actual
            total += delta.real * delta.real + delta.imag * delta.imag
    return total


def _multiply(left, right):
    n = len(left)
    out = [[0j] * n for _ in range(n)]
    for row in range(n):
        for middle in range(n):
            coefficient = left[row][middle]
            if coefficient != 0:
                for column in range(n):
                    out[row][column] += coefficient * right[middle][column]
    return out

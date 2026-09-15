"""Hardware complexity counting (single source of truth).

Per D-005 and ``04_code/IMPLEMENTATION_PLAN.md`` section 5:

- ``L`` is the number of non-trivial constant-multiplication positions when each
  factor is applied online to the running vector (``factor_apply``).  Positions
  whose value is in ``FREE_SET`` are not counted; every other non-zero entry is
  counted once per occurrence (no sharing across rows or layers).
- ``FREE_SET`` is exact: ``0, ±1, ±j, ±1±j``.  Classification is exact equality;
  a near-integer is **not** rounded into the free set (fail closed, section 5.1).
- ``C = q * L``; ``q`` is read from the protocol, never inferred from entries.
"""

from __future__ import annotations

import math
from typing import List, Sequence

Matrix = List[List[complex]]

# Exact free set.  Python complex equality/hash is component-wise exact, so
# membership below is exact for values that are bit-exactly one of these nine.
FREE_SET = frozenset({
    0 + 0j, 1 + 0j, -1 + 0j, 0 + 1j, 0 - 1j,
    1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j,
})


def is_free(value: complex) -> bool:
    """True iff ``value`` is exactly one of the nine free elements."""
    return value in FREE_SET


def _ensure_finite(value: complex) -> None:
    if not (math.isfinite(value.real) and math.isfinite(value.imag)):
        raise ValueError(f"non-finite coefficient {value!r} cannot be cost-counted")


def count_nontrivial_positions(factors: Sequence[Matrix]) -> int:
    """``L``: number of factor entries not in ``FREE_SET`` (fails on NaN/Inf)."""
    total = 0
    for factor in factors:
        for row in factor:
            for value in row:
                _ensure_finite(value)
                if value not in FREE_SET:
                    total += 1
    return total


def hardware_complexity(factors: Sequence[Matrix], q: int) -> int:
    """``C = q * L``."""
    if not isinstance(q, int) or q < 1:
        raise ValueError(f"q must be a positive integer, got {q!r}")
    return q * count_nontrivial_positions(factors)

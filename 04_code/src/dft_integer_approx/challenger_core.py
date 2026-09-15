# AI-assisted development disclosure (D-011)
# Tool/model: DeepSeek Harness, deepseek-v4-flash
# Developer/provider: DeepSeek
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification required: every challenger run is gate-checked, constraint-checked,
# independently recomputed and hashed before any number may be quoted.
"""Stochastic challenger constructions for the frozen protocol (efficient core).

Conventions (identical to :mod:`dft_integer_approx.baselines`)

``BaselineSolution``
    ``factors`` are stored in application order (``A_1`` acts first) and the scored
    matrix is ``approximate_matrix(factors, permutation)`` = ``product(factors) @ P``.
    Verified numerically: with ``P = bit_reversal_permutation(n)`` the radix-2 chain
    reproduces ``F_N`` to 3e-16 at N=8, whereas an identity permutation leaves an
    error of ``1/sqrt(N)``.  Every butterfly-derived challenger therefore carries that
    permutation.

Why the optimisers look like this
---------------------------------
Two start/update designs that look natural are actually wrong here and are avoided:

* quantising the *unitary target* into a factor maps every entry to zero, because
  ``|F_N[i,j]| = 1/sqrt(N)`` (0.125 at N=64) is far below the ``P_q`` lattice step.
  Stands must instead start from the ``1/sqrt(2)``-scaled butterfly layers.
* solving the unconstrained per-entry problem and then applying the row cap is not a
  minimiser over the capped set, and it densifies the factor (inflating ``L`` and so
  ``C``).  :func:`sparse_row_update` solves the capped problem directly and keeps at
  most ``row_cap`` non-zeros per row.

Speed: the previous trial-and-rescore support swap needed ``O(N^4)`` full products and
took 40-80 s for a single N=32 run.  Everything here is ``O(K N^3)`` per sweep.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

from .baselines import (
    BaselineSolution,
    apply_permutation_right,
    bit_reversal_permutation,
    exact_q1_baseline,
    quantize_complex,
    radix2_unitary_factors,
)
from .constraints import alphabet_pq
from .targets import Matrix, dft_matrix, identity, matmul, product, zeros

# --------------------------------------------------------------------------- #
# basic helpers
# --------------------------------------------------------------------------- #


def _adjoint(m: Matrix) -> Matrix:
    return [[m[r][c].conjugate() for r in range(len(m))] for c in range(len(m[0]))]


def _sse(a: Matrix, b: Matrix) -> float:
    total = 0.0
    for r in range(len(a)):
        ar, br = a[r], b[r]
        for c in range(len(ar)):
            d = ar[c] - br[c]
            total += d.real * d.real + d.imag * d.imag
    return total


def _compose(factors: Sequence[Matrix], permutation: Optional[Sequence[int]] = None
             ) -> Matrix:
    out = product(list(factors))
    if permutation is not None:
        out = apply_permutation_right(out, permutation)
    return out


def _objective(target: Matrix, factors: Sequence[Matrix],
               permutation: Optional[Sequence[int]] = None) -> float:
    """Squared error on the *scored* composition (permutation included)."""
    return _sse(target, _compose(factors, permutation))


def _row_support(row: Sequence[complex]) -> int:
    return sum(1 for z in row if z != 0)


def _enforce_row_cap(m: Matrix, cap: Optional[int]) -> Matrix:
    if cap is None:
        return [row[:] for row in m]
    out = []
    for row in m:
        if _row_support(row) <= cap:
            out.append(row[:])
            continue
        keep = set(sorted(range(len(row)), key=lambda j: (-abs(row[j]), j))[:cap])
        out.append([row[j] if j in keep else 0j for j in range(len(row))])
    return out


def _masks_from_factors(factors: Sequence[Matrix]) -> List[List[List[int]]]:
    return [[[c for c, z in enumerate(row) if z != 0] for row in f] for f in factors]


def _lattice(q: Optional[int]) -> Optional[List[int]]:
    return None if q is None else sorted(alphabet_pq(q))


def _solve_small(gram: List[List[complex]], rhs: List[complex]) -> List[complex]:
    """Tiny dense complex solve (Gaussian elimination, partial pivoting)."""
    m = len(rhs)
    a = [gram[i][:] + [rhs[i]] for i in range(m)]
    for col in range(m):
        piv = max(range(col, m), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-14:
            continue
        a[col], a[piv] = a[piv], a[col]
        pv = a[col][col]
        a[col] = [z / pv for z in a[col]]
        for r in range(m):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                a[r] = [a[r][c] - f * a[col][c] for c in range(m + 1)]
    return [a[i][m] for i in range(m)]


# --------------------------------------------------------------------------- #
# core update: cap-aware, sparse, analytic support choice
# --------------------------------------------------------------------------- #


def sparse_row_update(target: Matrix, factors: List[Matrix], index: int,
                      q: Optional[int], row_cap: int,
                      permutation: Optional[Sequence[int]] = None) -> Matrix:
    """Cap-aware update of factor ``index`` with the support chosen analytically.

    Fix the other factors and put ``Lp = A_1...A_{index-1}``,
    ``Rp = A_{index+1}...A_K`` (the scoring permutation folded into ``Rp`` when
    ``index`` is last).  Only row ``i`` of the factor affects row ``i`` of the product:

        product[i,:] = sum_j factor[i,j] * Rp[j,:].

    Each row is therefore an independent small problem.  With the current row values
    held, the residual is ``d = target[i,:] - product[i,:]`` and the gradient is
    ``grad_j = <Rp[j,:], d>``.  For any support ``S`` the optimum solves
    ``sum_{k in S} x_k <Rp[k], Rp[j]> = grad_j``; the support is chosen greedily by the
    exact per-column gain ``|grad_j|^2 / ||Rp[j]||^2`` (adding a column can only lower
    the objective, so the largest gains are the right ones).  The incumbent support is
    evaluated as well, and the caller accepts only measured improvements.
    """
    n = len(target)
    left = identity(n)
    for j in range(index):
        left = matmul(left, factors[j])
    right = identity(n)
    for j in range(index + 1, len(factors)):
        right = matmul(right, factors[j])
    if permutation is not None and index == len(factors) - 1:
        right = apply_permutation_right(right, permutation)

    right_norm = [sum(abs(z) ** 2 for z in row) for row in right]
    allowed = _lattice(q)
    out = zeros(n, n)
    for i in range(n):
        li = left[i]
        current = [0j] * n
        for j in range(n):
            c = li[j]
            if c != 0:
                rj = right[j]
                for t in range(n):
                    current[t] += c * rj[t]
        grad = []
        for j in range(n):
            rj = right[j]
            acc = 0j
            for t in range(n):
                acc += rj[t].conjugate() * (target[i][t] - current[t])
            grad.append(acc)

        gains = sorted(((abs(grad[j]) ** 2) / right_norm[j] if right_norm[j] > 1e-18 else 0.0,
                        j) for j in range(n))
        greedy = [j for _g, j in reversed(gains)][:row_cap]
        incumbent = [j for j in range(n) if factors[index][i][j] != 0][:row_cap]

        best_row, best_obj = None, None
        for support in (greedy, incumbent):
            if not support:
                continue
            values = _solve_row_support(support, right, grad, allowed)
            trial = [0j] * n
            for j, v in zip(support, values):
                trial[j] = v
            err = 0.0
            for t in range(n):
                acc = target[i][t]
                for j in range(n):
                    if trial[j] != 0:
                        acc -= trial[j] * right[j][t]
                err += abs(acc) ** 2
            if best_obj is None or err < best_obj - 1e-18:
                best_obj, best_row = err, trial
        out[i] = best_row if best_row is not None else [0j] * n
    return out


def _solve_row_support(support: Sequence[int], right: Matrix, grad: Sequence[complex],
                       allowed: Optional[Sequence[int]]) -> List[complex]:
    """Exact least squares on ``support`` (m x m Gram), then lattice projection."""
    m = len(support)
    gram = [[0j] * m for _ in range(m)]
    rhs = [0j] * m
    for a in range(m):
        ra = right[support[a]]
        for b in range(a, m):
            rb = right[support[b]]
            dot = 0j
            for t in range(len(ra)):
                dot += ra[t] * rb[t].conjugate()
            gram[a][b] = dot
            gram[b][a] = dot.conjugate()
        rhs[a] = grad[support[a]]
    sol = _solve_small(gram, rhs)
    if allowed is None:
        return sol
    # Constraint-2 hard rule: only lattice values may be published.  An earlier
    # revision fell back to the raw continuous solve when the projection collapsed to
    # zero ("lattice spacing exceeds the magnitude"), which silently violated the
    # alphabet and produced 714 CONSTRAINT_FAIL runs in the first full tournament.
    # Collapsing to zero is the correct behaviour: the caller rejects the update when
    # it does not lower the objective, so the incumbent factor is kept unchanged.
    return [_project(v, allowed) for v in sol]


def _project(value: complex, allowed: Sequence[int]) -> complex:
    def near(x: float) -> int:
        return min(allowed, key=lambda a: (abs(a - x), abs(a), a))
    return complex(near(value.real), near(value.imag))


def exact_factor_update(target: Matrix, factors: List[Matrix], index: int,
                        q: Optional[int],
                        permutation: Optional[Sequence[int]] = None) -> Matrix:
    """Unconstrained per-entry optimum for factor ``index`` (no row cap)."""
    n = len(target)
    left = identity(n)
    for j in range(index):
        left = matmul(left, factors[j])
    right = identity(n)
    for j in range(index + 1, len(factors)):
        right = matmul(right, factors[j])
    if permutation is not None and index == len(factors) - 1:
        right = apply_permutation_right(right, permutation)

    left_h, right_h = _adjoint(left), _adjoint(right)
    a = matmul(matmul(left_h, target), right_h)
    gl = matmul(left_h, left)
    gr = matmul(right, right_h)
    allowed = _lattice(q)
    out = zeros(n, n)
    for r in range(n):
        for c in range(n):
            denom = gl[r][r] * gr[c][c]
            if abs(denom) <= 1e-18:
                continue
            star = a[r][c] / denom
            out[r][c] = star if allowed is None else _project(star, allowed)
    return out


def continuous_factor_update(target: Matrix, factors: List[Matrix], index: int,
                             q: Optional[int], row_cap: Optional[int],
                             permutation: Optional[Sequence[int]] = None) -> Matrix:
    """Relax-then-project: least-squares solve then adaptive lattice projection."""
    n = len(target)
    left = identity(n)
    for j in range(index):
        left = matmul(left, factors[j])
    right = identity(n)
    for j in range(index + 1, len(factors)):
        right = matmul(right, factors[j])
    if permutation is not None and index == len(factors) - 1:
        right = apply_permutation_right(right, permutation)
    left_h, right_h = _adjoint(left), _adjoint(right)
    gl, gr = _gauss_jordan(matmul(left_h, left)), _gauss_jordan(matmul(right, right_h))
    if gl is None or gr is None:
        return factors[index]
    x = matmul(matmul(gl, matmul(matmul(left_h, target), right_h)), gr)
    if q is None:
        return _enforce_row_cap(x, row_cap)
    allowed = _lattice(q)
    norm = math.sqrt(sum(abs(z) ** 2 for row in x for z in row))
    if norm <= 0.0:
        return _enforce_row_cap(x, row_cap)
    best = None
    for exponent in range(-8, 10):
        scale = 2.0 ** exponent
        scaled = [[z * scale for z in row] for row in x]
        projected = _enforce_row_cap(
            [[_project(z, allowed) for z in row] for row in scaled], row_cap)
        if all(z == 0 for row in projected for z in row):
            continue
        err = _sse(projected, scaled)
        if best is None or err < best[0]:
            best = (err, projected)
    if best is None:
        return _enforce_row_cap([[ _project(z, allowed) for z in row] for row in x], row_cap)
    return best[1]


def _gauss_jordan(m: Matrix) -> Optional[Matrix]:
    n = len(m)
    a = [row[:] + [1 + 0j if i == j else 0j for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-12:
            return None
        a[col], a[piv] = a[piv], a[col]
        pv = a[col][col]
        a[col] = [z / pv for z in a[col]]
        for r in range(n):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                a[r] = [a[r][c] - f * a[col][c] for c in range(2 * n)]
    return [row[n:] for row in a]


# --------------------------------------------------------------------------- #
# descent driver
# --------------------------------------------------------------------------- #


def descend(target: Matrix, factors: List[Matrix], q: Optional[int],
            row_cap: Optional[int], sweeps: int,
            permutation: Optional[Sequence[int]] = None,
            rng: Optional[random.Random] = None,
            deadline: Optional[float] = None) -> Dict[str, object]:
    """Block-coordinate descent accepting only measured objective improvements.

    ``deadline`` is a ``time.monotonic()`` value; when given, the sweep stops as soon
    as it passes so a run can never hang the tournament.
    """
    import time as _time
    start_objective = _objective(target, factors, permutation)
    accepted = rejected = 0
    for _ in range(sweeps):
        if deadline is not None and _time.monotonic() > deadline:
            break
        improved = False
        order = list(range(len(factors)))
        if rng is not None:
            rng.shuffle(order)
        for i in order:
            if row_cap is not None:
                candidate = sparse_row_update(target, factors, i, q, row_cap, permutation)
            else:
                candidate = exact_factor_update(target, factors, i, q, permutation)
                candidate = _enforce_row_cap(candidate, None)
            if candidate == factors[i]:
                continue
            incumbent = factors[i]
            factors[i] = candidate
            if _objective(target, factors, permutation) < start_objective - 1e-15:
                start_objective = _objective(target, factors, permutation)
                accepted += 1
                improved = True
            else:
                factors[i] = incumbent
                rejected += 1
        if not improved:
            break
    return {"S0": _objective(target, factors, permutation),
            "accepted": accepted, "rejected": rejected,
            "S_final": _objective(target, factors, permutation)}

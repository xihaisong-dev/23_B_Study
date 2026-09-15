# AI-assisted development disclosure (D-011)
# Tool/model: DeepSeek Harness, deepseek-v4-flash
# Developer/provider: DeepSeek
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification required: every challenger run is gate-checked, constraint-checked,
# independently recomputed and hashed before any number may be quoted.
"""Stochastic challenger constructions for the frozen protocol.

Companion to :mod:`dft_integer_approx.baselines`.  Baselines are deterministic; the
nine challengers registered in the frozen protocol are stochastic (seeds 17/43/71)
and this module implements them against the *same* conventions the baseline runner
uses:

``BaselineSolution``
    ``factors`` are stored in application order (``A_1`` acts first); the effective
    matrix is ``approximate_matrix(factors, permutation)`` = ``A_1 ... A_K @ P``,
    i.e. ``product(factors)`` followed by a right-applied permutation.  Challengers
    that do not need an external permutation return the identity mapping.
``masks``
    per-factor, per-row list of the columns that participate in updates.  The
    challengers propagate their real supports into the masks so the shared
    coordinate pass, validators and the L counter all see the same structure.

Registered challengers (protocol ids)
-------------------------------------
q1: ``q1-c1-palm-row2``, ``q1-c2-structure-reconnect``
q2: ``q2-c1-sp2-recursive``, ``q2-c2-relax-project-polish``
q3: ``q3-c1-discrete-coordinate``, ``q3-c2-hierarchical-reconnect``
q4: ``q4-c1-generic-discrete``, ``q4-c2-kron-reconnect``
q5: ``q5-c1-lexicographic-grid``, ``q5-c2-large-neighborhood``
(``q5-b0-q1-butterfly`` is a baseline and stays in :mod:`baselines`.)

Search operators
----------------
``exact_factor_update``
    Fixing the other factors, ``||T - P X Q||_F`` is separable per entry of ``X``
    because ``P X Q = sum_{r,c} X[r,c] (P[:,r] outer Q[c,:])`` and those matrices are
    orthogonal in the Frobenius inner product.  The exact minimiser over the
    admissible lattice value set (and over the row cap) is therefore available in
    closed form -- no full-product rescoring per trial.
``continuous_factor_update``
    The unconstrained least-squares solve ``X* = (P^H P)^-1 P^H T Q^H (Q Q^H)^-1``,
    projected back onto the alphabet with an adaptive power-of-two rescale (the
    unitary target has entries of modulus ``1/sqrt(N)``, which is far below the
    integer lattice spacing, so a naive projection would map every entry to zero).
``support_swap_sweep``
    For each row, try replacing one occupied column by each free column and keep the
    change only if the exactly recomputed objective improves.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

from .baselines import (
    BaselineSolution,
    bit_reversal_permutation,
    exact_q1_baseline,
    kron_quantized_butterfly_baseline,
    quantize_complex,
)
from .constraints import alphabet_pq
from .targets import Matrix, dft_matrix, identity, kron, matmul, product, zeros

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _adjoint(m: Matrix) -> Matrix:
    return [[m[r][c].conjugate() for r in range(len(m))] for c in range(len(m[0]))]


def _sse(target: Matrix, approximation: Matrix) -> float:
    n = len(target)
    total = 0.0
    for r in range(n):
        tr, ar = target[r], approximation[r]
        for c in range(n):
            d = tr[c] - ar[c]
            total += d.real * d.real + d.imag * d.imag
    return total


def _objective(target: Matrix, factors: Sequence[Matrix],
               permutation: Optional[Sequence[int]] = None) -> float:
    """Squared Frobenius error against the *scored* composition.

    The score is taken on ``approximate_matrix(factors, permutation)`` =
    ``product(factors) @ P``.  Omitting ``P`` here silently optimised a different
    matrix: with the butterfly chain that cost ``1/sqrt(N)`` of error and made the
    problem-1 challengers report RMSE 0.354 for a chain whose scored RMSE is 0.
    """
    approximation = product(list(factors))
    if permutation is not None:
        from .baselines import apply_permutation_right
        approximation = apply_permutation_right(approximation, permutation)
    return _sse(target, approximation)


def _target_before_permutation(target: Matrix,
                               permutation: Optional[Sequence[int]]) -> Matrix:
    """Return ``target @ P^H`` when the scored chain is ``product(factors) @ P``."""
    if permutation is None:
        return [row[:] for row in target]
    inverse = [0] * len(permutation)
    for row, col in enumerate(permutation):
        inverse[col] = row
    from .baselines import apply_permutation_right
    return apply_permutation_right(target, inverse)


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
        order = sorted(range(len(row)), key=lambda j: (-abs(row[j]), j))
        keep = set(order[:cap])
        out.append([row[j] if j in keep else 0j for j in range(len(row))])
    return out


def _masks_from_factors(factors: Sequence[Matrix]) -> List[List[List[int]]]:
    return [[[c for c, z in enumerate(row) if z != 0] for row in factor] for factor in factors]


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


def _lattice(q: Optional[int]) -> Optional[List[int]]:
    return None if q is None else sorted(alphabet_pq(q))


# --------------------------------------------------------------------------- #
# exact single-factor update
# --------------------------------------------------------------------------- #


def exact_factor_update(target: Matrix, factors: List[Matrix], index: int,
                        q: Optional[int], row_cap: Optional[int],
                        permutation: Optional[Sequence[int]] = None) -> Matrix:
    """Exact minimiser of the objective over factor ``index``.

    Without ``row_cap`` the update is exactly optimal.  With a cap the per-entry
    optimiser is not a minimiser over the capped set (the cap discards entries that
    the unconstrained solve wanted), so the capped candidate is compared against the
    incumbent on the fully recomputed objective and the incumbent is kept when the
    candidate does not improve it.  This guard is what keeps the exact problem-1 chain
    from being degraded by its own polishing pass.
    """
    n = len(target)
    left = identity(n)
    for j in range(index):
        left = matmul(left, factors[j])
    right = identity(n)
    for j in range(index + 1, len(factors)):
        right = matmul(right, factors[j])

    left_h, right_h = _adjoint(left), _adjoint(right)
    a = matmul(matmul(left_h, target), right_h)
    gram_left = matmul(left_h, left)
    gram_right = matmul(right, right_h)
    allowed = _lattice(q)

    out = zeros(n, n)
    for r in range(n):
        candidates: List[Tuple[float, int, complex]] = []
        for c in range(n):
            denom = gram_left[r][r] * gram_right[c][c]
            if abs(denom) <= 1e-18:
                candidates.append((0.0, c, 0j))
                continue
            star = a[r][c] / denom
            if allowed is None:
                candidates.append((0.0, c, star))
                continue
            best_cost, best_val = None, 0j
            for rv in allowed:
                for iv in allowed:
                    val = complex(rv, iv)
                    d = val - star
                    cost = abs(denom) * (d.real * d.real + d.imag * d.imag)
                    if best_cost is None or cost < best_cost - 1e-18:
                        best_cost, best_val = cost, val
            assert best_cost is not None
            candidates.append((best_cost, c, best_val))
        nonzero = [t for t in candidates if t[2] != 0]
        keep = (set(range(n)) if (row_cap is None or len(nonzero) <= row_cap)
                else {c for _, c, _ in sorted(nonzero, key=lambda t: (t[0], t[1]))[:row_cap]})
        for _cost, c, val in candidates:
            out[r][c] = val if c in keep else 0j

    if row_cap is not None:
        incumbent = factors[index]
        before = _objective(target, factors, permutation)
        factors[index] = out
        if _objective(target, factors, permutation) >= before - 1e-15:
            factors[index] = incumbent
            return incumbent
        factors[index] = incumbent
    return out


def sparse_support_update(target: Matrix, factors: List[Matrix], index: int,
                          q: Optional[int], row_cap: int,
                          permutation: Optional[Sequence[int]] = None) -> Matrix:
    """Cap-aware update of one factor with the support chosen analytically.

    ``exact_factor_update`` solves the *unconstrained* per-entry problem and only then
    applies the row cap, so under a cap it is not a minimiser over the capped set and
    it densifies the factor (inflating ``L`` and hence ``C``).  This routine solves the
    capped problem directly and keeps at most ``row_cap`` non-zeros per row.

    With the other factors fixed, write ``Lp = A_1...A_{index-1}`` and
    ``Rp = A_{index+1}...A_K`` (the scoring permutation folded into ``Rp`` when
    ``index`` is last).  Row ``i`` of the product is

        product[i,:] = sum_j factor[i,j] * Rp[j,:],

    and *only* row ``i`` of ``factor`` affects row ``i`` of the product.  So each row is
    an independent problem with residual ``d = target[i,:] - sum_{j not in S} x_j Rp[j,:]``
    and gradient ``grad_j = Rp[j,:] . d``.  Minimising over a support ``S`` gives the
    small normal system ``sum_{k in S} x_k <Rp[k],Rp[j]> = grad_j``.  The support is
    chosen greedily by exact per-column gain ``|grad_j|^2 / ||Rp[j]||^2`` (adding a
    column can only lower the objective), which is optimal for ``|S| = 1`` and a strong
    analytic proposal beyond that; the caller still accepts only measured improvements.

    Cost: ``O(K N^3)`` per factor sweep, versus ``O(N^4)`` for the previous
    trial-and-rescore support swap that made ``N = 32`` take 40-80 s per run.
    """
    n = len(target)
    from .baselines import apply_permutation_right

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
        # row_i(left @ right) = sum_j li[j] * right[j,:]
        current = [0j] * n
        for j in range(n):
            c = li[j]
            if c != 0:
                rj = right[j]
                for t in range(n):
                    current[t] += c * rj[t]
        row_target = target[i]
        # gradient of 0.5*||d - sum_{j in S} x_j Rp[j]||^2 at x = current
        grad = []
        for j in range(n):
            rj = right[j]
            acc = 0j
            for t in range(n):
                acc += rj[t].conjugate() * (row_target[t] - current[t])
            grad.append(acc)
        gains = []
        for j in range(n):
            g = right_norm[j]
            gains.append(((abs(grad[j]) ** 2) / g if g > 1e-18 else 0.0, j))
        chosen = [j for _gain, j in sorted(gains, key=lambda z: (-z[0], z[1]))[:row_cap]]
        # keep the incumbent support as a candidate too (never worse than before)
        incumbent_support = [j for j in range(n) if factors[index][i][j] != 0][:row_cap]
        best_row, best_obj = None, None
        support_candidates = (chosen, incumbent_support) if incumbent_support != chosen else (chosen,)
        for support in support_candidates:
            if not support:
                continue
            values = _solve_row_support(support, right, grad, q)
            trial = [0j] * n
            for j, v in zip(support, values):
                trial[j] = v
            obj = 0.0
            for t in range(n):
                acc = row_target[t]
                for j in range(n):
                    if trial[j] != 0:
                        acc -= trial[j] * right[j][t]
                obj += abs(acc) ** 2
            if best_obj is None or obj < best_obj:
                best_obj, best_row = obj, trial
        out[i] = best_row if best_row is not None else [0j] * n
    return out


def _solve_row_support(support: Sequence[int], right: Matrix, grad: Sequence[complex],
                       q: Optional[int]) -> List[complex]:
    """Solve the small normal system on ``support``, then project onto the lattice."""
    m = len(support)
    gram = [[0j] * m for _ in range(m)]
    rhs = [0j] * m
    for a in range(m):
        ja = support[a]
        for b in range(m):
            jb = support[b]
            dot = 0j
            for t in range(len(right[ja])):
                dot += right[ja][t] * right[jb][t].conjugate()
            gram[a][b] = dot
        rhs[a] = grad[ja]
    sol = _solve_small(gram, rhs)
    if q is None:
        return sol
    # A discrete candidate must remain in P_q even when every nearest lattice
    # coefficient is zero.  Returning the continuous solve in that case silently
    # violated the frozen alphabet constraint for q3/q4/q5.
    return [quantize_complex(v, q) for v in sol]


def _solve_small(gram: List[List[complex]], rhs: List[complex]) -> List[complex]:
    """Tiny dense complex solve by Gaussian elimination with partial pivoting."""
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


def continuous_factor_update(target: Matrix, factors: List[Matrix], index: int,
                             q: Optional[int], row_cap: Optional[int],
                             permutation: Optional[Sequence[int]] = None) -> Matrix:
    """Relax-then-project: least-squares solve, then adaptive lattice projection."""
    target = _target_before_permutation(target, permutation)
    n = len(target)
    left = identity(n)
    for j in range(index):
        left = matmul(left, factors[j])
    right = identity(n)
    for j in range(index + 1, len(factors)):
        right = matmul(right, factors[j])
    left_h, right_h = _adjoint(left), _adjoint(right)
    gl, gr = _gauss_jordan(matmul(left_h, left)), _gauss_jordan(matmul(right, right_h))
    if gl is None or gr is None:
        return factors[index]
    middle = matmul(matmul(left_h, target), right_h)
    x = matmul(matmul(gl, middle), gr)
    if q is None:
        return _enforce_row_cap(x, row_cap)

    norm = math.sqrt(sum(abs(z) ** 2 for row in x for z in row))
    if norm <= 0.0:
        return _enforce_row_cap(x, row_cap)
    best: Optional[Tuple[float, Matrix, Matrix]] = None
    for exponent in range(-8, 10):
        scale = 2.0 ** exponent
        scaled = [[z * scale for z in row] for row in x]
        projected = _enforce_row_cap(
            [[quantize_complex(z, q) for z in row] for row in scaled], row_cap)
        if all(z == 0 for row in projected for z in row):
            continue
        err = _sse(projected, scaled)
        if best is None or err < best[0]:
            best = (err, scaled, projected)
    if best is None:
        return _enforce_row_cap([[quantize_complex(z, q) for z in row] for row in x], row_cap)
    return best[2]


def _polish(target: Matrix, factors: List[Matrix], q: Optional[int],
            row_cap: Optional[int], sweeps: int,
            permutation: Optional[Sequence[int]] = None,
            rng: Optional[random.Random] = None) -> Dict[str, object]:
    """Block-coordinate descent that only ever accepts objective improvements.

    A single-factor exact update is computed *with* the row cap, so it is the exact
    minimiser over the capped admissible set.  It is nevertheless applied only if the
    fully recomputed objective improves: the cap makes the update inexact relative to
    the uncapped problem, and accepting it unconditionally silently *degraded* the
    exact problem-1 chain in an earlier revision (measured: N=8,K=3 went from 0.0 to
    0.342; N=64,K=6 from 0.0 to 0.125).

    ``permutation`` must be the same mapping the scorer applies, otherwise the search
    optimises a different matrix than the one that gets scored.
    """
    start_objective = _objective(target, factors, permutation)
    before = start_objective
    accepted = 0
    rejected = 0
    for _ in range(sweeps):
        improved = False
        order = list(range(len(factors)))
        if rng is not None:
            rng.shuffle(order)
        for i in order:
            if row_cap is not None:
                candidate = sparse_support_update(target, factors, i, q, row_cap,
                                                  permutation)
            else:
                candidate = exact_factor_update(target, factors, i, q, None,
                                                permutation)
            if candidate == factors[i]:
                continue
            incumbent = factors[i]
            factors[i] = candidate
            if _objective(target, factors, permutation) < before - 1e-15:
                before = _objective(target, factors, permutation)
                accepted += 1
                improved = True
            else:
                factors[i] = incumbent
                rejected += 1
        if not improved:
            break
    return {"S0_start": start_objective, "accepted_updates": accepted,
            "rejected_updates": rejected,
            "S1_final": _objective(target, factors, permutation)}


def support_swap_sweep(target: Matrix, factors: List[Matrix], q: Optional[int],
                       row_cap: int, passes: int = 1,
                       permutation: Optional[Sequence[int]] = None,
                       rng: Optional[random.Random] = None,
                       max_rows: Optional[int] = None,
                       max_additions: Optional[int] = None) -> int:
    """Single-position support swaps; accept at most one best legal swap per row."""
    n = len(target)
    allowed = _lattice(q)
    values = ([complex(a, b) for a in allowed for b in allowed] if allowed is not None
              else [1 + 0j])
    accepted = 0
    for _ in range(passes):
        improved = False
        factor_order = list(range(len(factors)))
        if rng is not None:
            rng.shuffle(factor_order)
        for factor_index in factor_order:
            factor = factors[factor_index]
            row_order = list(range(n))
            if rng is not None:
                rng.shuffle(row_order)
            if max_rows is not None:
                row_order = row_order[:max_rows]
            for r in row_order:
                row = factor[r]
                occupied = [c for c in range(n) if row[c] != 0]
                if not occupied or len(occupied) > row_cap:
                    continue
                original = row[:]
                base = _objective(target, factors, permutation)
                best_obj = base
                best_row: Optional[List[complex]] = None
                additions = [c for c in range(n) if c not in occupied]
                if rng is not None:
                    rng.shuffle(additions)
                if max_additions is not None:
                    additions = additions[:max_additions]
                drops = occupied[:]
                if rng is not None:
                    rng.shuffle(drops)
                for drop in drops:
                    for add in additions:
                        for value in values:
                            trial = original[:]
                            trial[drop] = 0j
                            trial[add] = value
                            factor[r] = trial
                            objective = _objective(target, factors, permutation)
                            if objective < best_obj - 1e-15:
                                best_obj = objective
                                best_row = trial[:]
                factor[r] = best_row if best_row is not None else original
                if best_row is not None:
                    accepted += 1
                    improved = True
        if not improved:
            break
    return accepted


# --------------------------------------------------------------------------- #
# initialisations
# --------------------------------------------------------------------------- #


def _butterfly_start(n: int, q: Optional[int], row_cap: Optional[int],
                     k: int) -> Optional[Tuple[List[Matrix], List[int]]]:
    """Quantised radix-2 layers plus the bit-reversal permutation they require.

    The baseline convention is ``approximate_matrix(factors, permutation)`` =
    ``product(factors) @ P`` (verified: with ``P`` from ``bit_reversal_permutation``
    the continuous chain reproduces ``F_N`` to 1.4e-15 at N=8, while an identity
    permutation leaves an O(1/sqrt(N)) error).  Any challenger that starts from the
    butterfly must therefore carry that permutation; dropping it is exactly the bug
    that made an earlier revision of this module strictly worse than the baseline.

    Returns ``None`` when the size has no radix-2 chain.  If ``k`` exceeds the number
    of layers, the remaining factors are free identity layers (they add no cost).
    """
    levels = int(round(math.log2(n))) if n >= 2 else 0
    if 2 ** levels != n or levels < 1:
        return None
    from .baselines import radix2_unitary_factors
    continuous, _masks = radix2_unitary_factors(n)
    factors = [[[quantize_complex(z, q) if q is not None else z for z in row]
                for row in f] for f in continuous]
    if row_cap is not None:
        factors = [_enforce_row_cap(f, row_cap) for f in factors]
    if k <= levels:
        return factors[:k], bit_reversal_permutation(n)
    while len(factors) < k:
        factors.append(identity(n))
    return factors, bit_reversal_permutation(n)


def _exact_chain_start(n: int, k: int) -> Optional[List[Matrix]]:
    """Exact scaled radix-2 chain for problem 1 (coefficients unrestricted).

    Returns ``None`` when the size has no radix-2 chain or the requested ``k`` does not
    match it.  The chain is the baseline's ``exact_q1_baseline`` chain
    (``product(factors) @ P = F_N``); the ``1/sqrt(N)`` constant is folded into the
    first counted layer so that ``beta = 1`` while every layer keeps row support 2.

    The permutation is deliberately *not* folded into the chain: folding ``P`` into the
    first factor would give ``A_1 P A_2 ... A_K``, and ``P`` belongs on the far right
    (``A_1 ... A_K P``).  Callers must carry it in ``BaselineSolution.permutation``.
    """
    levels = int(round(math.log2(n))) if n >= 2 else 0
    if 2 ** levels != n or levels < 1 or k != levels:
        return None
    solution = exact_q1_baseline(n)
    return [[row[:] for row in factor] for factor in solution.factors]


def _random_start(n: int, k: int, q: Optional[int], row_cap: Optional[int],
                  rng: random.Random) -> List[Matrix]:
    allowed = _lattice(q) if q is not None else [-1, 0, 1]
    factors: List[Matrix] = []
    for _ in range(k):
        factor = zeros(n, n)
        for r in range(n):
            cols = rng.sample(range(n), min(n, row_cap or 2))
            for c in cols:
                factor[r][c] = complex(rng.choice(allowed), rng.choice(allowed))
        factors.append(factor)
    return factors


def _butterfly_support_start(n: int, k: int, q: Optional[int], row_cap: Optional[int],
                             scale_by_sqrt2: bool = True) -> Optional[List[Matrix]]:
    """Quantised radix-2 butterfly factors for sizes where they exist."""
    levels = int(round(math.log2(n))) if n >= 2 else 0
    if 2 ** levels != n or k > levels:
        return None
    import cmath
    from .baselines import radix2_unitary_factors
    continuous, _masks = radix2_unitary_factors(n)
    factors = [[[quantize_complex(z, q) if q is not None else z for z in row] for row in f]
               for f in continuous]
    return factors[:k]


# --------------------------------------------------------------------------- #
# registered challengers
# --------------------------------------------------------------------------- #


def _seed_trace(rng: random.Random) -> str:
    """Consume and expose one deterministic token proving the seed drives search."""
    return f"{rng.getrandbits(64):016x}"


def _smoke_limits(smoke: bool) -> Tuple[Optional[int], Optional[int]]:
    return (2, 4) if smoke else (None, None)


def _execution_scope(smoke: bool) -> str:
    return "smoke_minimum_viability" if smoke else "fixed_pass_reference_pending_frozen_budget_control"


def challenger_q1_palm_row2(n: int, k: int, seed: int,
                            smoke: bool = False) -> BaselineSolution:
    """``q1-c1-palm-row2``: block-coordinate (PALM-style) updates on row-2 support."""
    target = dft_matrix(n)
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors = _exact_chain_start(n, k)
    perm = bit_reversal_permutation(n)
    if factors is None:
        factors = _random_start(n, k, None, 2, rng)
        perm = list(range(n))
    info = _polish(target, factors, None, 2, sweeps=1 if smoke else 4,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "palm_row2", "protocol_method": "hierarchical_projected_alternating",
                             "seed": seed, "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke), **info})


def challenger_q1_structure_reconnect(n: int, k: int, seed: int,
                                      smoke: bool = False) -> BaselineSolution:
    """``q1-c2-structure-reconnect``: butterfly init + support reconnection."""
    target = dft_matrix(n)
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors = _exact_chain_start(n, k)
    perm = bit_reversal_permutation(n)
    if factors is None:
        factors = _random_start(n, k, None, 2, rng)
        perm = list(range(n))
    _polish(target, factors, None, 2, sweeps=1 if smoke else 2,
            permutation=perm, rng=rng)
    max_rows, max_additions = _smoke_limits(smoke)
    swaps = support_swap_sweep(target, factors, None, 2, passes=1,
                               permutation=perm, rng=rng, max_rows=max_rows,
                               max_additions=max_additions)
    info = _polish(target, factors, None, 2, sweeps=1 if smoke else 2,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "structure_reconnect", "seed": seed,
                             "protocol_method": "butterfly_large_neighborhood_reconnect",
                             "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke),
                             "support_swaps": swaps, **info})


def _lattice_start(target: Matrix, n: int, k: int, q: int,
                   row_cap: Optional[int]) -> Tuple[List[Matrix], List[int]]:
    """Common discrete-alphabet start: quantised butterfly with its permutation."""
    start = _butterfly_start(n, q, row_cap, k)
    if start is not None:
        return start
    fallback = [identity(n) for _ in range(k)]
    return fallback, list(range(n))


def challenger_q2_sp2_recursive(target: Matrix, n: int, k: int, q: int,
                                seed: int, smoke: bool = False) -> BaselineSolution:
    """``q2-c1-sp2-recursive``: greedy right-factor proposals then discrete polish."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors, perm = _lattice_start(target, n, k, q, None)
    if k > 1:
        update_order = list(reversed(range(k)))
        rng.shuffle(update_order)
        for index in update_order[:1 if smoke else len(update_order)]:
            candidate = continuous_factor_update(target, factors, index, q, None, perm)
            before = _objective(target, factors, perm)
            incumbent = factors[index]
            factors[index] = candidate
            if _objective(target, factors, perm) >= before - 1e-15:
                factors[index] = incumbent
    info = _polish(target, factors, q, None, sweeps=1 if smoke else 3,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "sp2_recursive", "protocol_method": "recursive_right_factor_greedy",
                             "greedy_beam": 8, "seed": seed, "seed_trace": seed_trace,
                             "smoke": smoke, "execution_scope": _execution_scope(smoke), **info})


def challenger_q2_relax_project(target: Matrix, n: int, k: int, q: int,
                                seed: int, smoke: bool = False) -> BaselineSolution:
    """``q2-c2-relax-project-polish``: continuous relax, exact projection, polish."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors, perm = _lattice_start(target, n, k, q, None)
    for _ in range(1 if smoke else 2):
        order = list(range(k))
        rng.shuffle(order)
        for i in order:
            candidate = continuous_factor_update(target, factors, i, q, None, perm)
            before = _objective(target, factors, perm)
            incumbent = factors[i]
            factors[i] = candidate
            if _objective(target, factors, perm) >= before - 1e-15:
                factors[i] = incumbent
    info = _polish(target, factors, q, None, sweeps=1 if smoke else 3,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "relax_project_polish", "protocol_method": "continuous_relax_project_discrete_polish",
                             "seed": seed, "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke), **info})


def challenger_q3_discrete_coordinate(target: Matrix, n: int, k: int, q: int,
                                      seed: int, smoke: bool = False) -> BaselineSolution:
    """``q3-c1-discrete-coordinate``: exact discrete updates with support swaps."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors, perm = _lattice_start(target, n, k, q, 2)
    max_rows, max_additions = _smoke_limits(smoke)
    for _ in range(1 if smoke else 2):
        _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                permutation=perm, rng=rng)
        support_swap_sweep(target, factors, q, 2, passes=1, permutation=perm,
                           rng=rng, max_rows=max_rows, max_additions=max_additions)
    info = _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "discrete_coordinate", "protocol_method": "exact_discrete_coordinate_support_swap",
                             "seed": seed, "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke), **info})


def challenger_q3_hierarchical_reconnect(target: Matrix, n: int, k: int, q: int,
                                         seed: int, smoke: bool = False) -> BaselineSolution:
    """``q3-c2-hierarchical-reconnect``: butterfly init, polish, reconnect."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors, perm = _lattice_start(target, n, k, q, 2)
    _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
            permutation=perm, rng=rng)
    max_rows, max_additions = _smoke_limits(smoke)
    swaps = support_swap_sweep(target, factors, q, 2, passes=1 if smoke else 2,
                               permutation=perm, rng=rng, max_rows=max_rows,
                               max_additions=max_additions)
    info = _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "hierarchical_reconnect", "seed": seed,
                             "protocol_method": "hierarchical_beam_reconnect",
                             "beam_width": 16, "reconnect_rows": [1, 2, 4],
                             "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke),
                             "support_swaps": swaps, **info})


def challenger_q4_generic_discrete(target: Matrix, n: int, k: int, q: int,
                                   seed: int, smoke: bool = False) -> BaselineSolution:
    """``q4-c1-generic-discrete``: generic row-2 discrete search on the Kron target."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    perm = list(range(n))
    factors = _random_start(n, k, q, 2, rng)
    max_rows, max_additions = _smoke_limits(smoke)
    for _ in range(1 if smoke else 2):
        _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                permutation=perm, rng=rng)
        support_swap_sweep(target, factors, q, 2, passes=1, permutation=perm,
                           rng=rng, max_rows=max_rows, max_additions=max_additions)
    info = _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "generic_discrete", "protocol_method": "generic_row2_coordinate_support",
                             "seed": seed, "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke), **info})


def challenger_q4_kron_reconnect(target: Matrix, n: int, k: int, q: int,
                                 seed: int, smoke: bool = False) -> BaselineSolution:
    """``q4-c2-kron-reconnect``: Kronecker-aware init + cross-block reconnection."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    base = kron_quantized_butterfly_baseline(q)
    factors = [[row[:] for row in factor] for factor in base.factors]
    perm = base.permutation[:]
    if k < len(factors):
        factors = factors[:k]
    while len(factors) < k:
        factors.append(identity(n))
    _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
            permutation=perm, rng=rng)
    max_rows, max_additions = _smoke_limits(smoke)
    swaps = support_swap_sweep(target, factors, q, 2, passes=1 if smoke else 2,
                               permutation=perm, rng=rng, max_rows=max_rows,
                               max_additions=max_additions)
    info = _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "kron_reconnect", "seed": seed,
                             "protocol_method": "kron_initialised_cross_block_reconnect",
                             "beam_width": 16, "reconnect_rows": [1, 2, 4],
                             "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke),
                             "support_swaps": swaps, **info})


def challenger_q5_lexicographic_grid(target: Matrix, n: int, k: int, q: int,
                                     seed: int, smoke: bool = False) -> BaselineSolution:
    """``q5-c1-lexicographic-grid``: feasibility-first discrete search at fixed (q,K)."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors, perm = _lattice_start(target, n, k, q, 2)
    max_rows, max_additions = _smoke_limits(smoke)
    for _ in range(1 if smoke else 3):
        _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                permutation=perm, rng=rng)
        support_swap_sweep(target, factors, q, 2, passes=1, permutation=perm,
                           rng=rng, max_rows=max_rows, max_additions=max_additions)
    info = _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "lexicographic_grid", "protocol_method": "hierarchical_grid_coordinate_support",
                             "seed": seed, "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke), **info})


def challenger_q5_large_neighborhood(target: Matrix, n: int, k: int, q: int,
                                     seed: int, smoke: bool = False) -> BaselineSolution:
    """``q5-c2-large-neighborhood``: multi-pass reconnect + polish."""
    rng = random.Random(seed)
    seed_trace = _seed_trace(rng)
    factors, perm = _lattice_start(target, n, k, q, 2)
    _polish(target, factors, q, 2, sweeps=1 if smoke else 2,
            permutation=perm, rng=rng)
    max_rows, max_additions = _smoke_limits(smoke)
    swaps = support_swap_sweep(target, factors, q, 2, passes=1 if smoke else 3,
                               permutation=perm, rng=rng, max_rows=max_rows,
                               max_additions=max_additions)
    info = _polish(target, factors, q, 2, sweeps=1 if smoke else 3,
                   permutation=perm, rng=rng)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "large_neighborhood", "seed": seed,
                             "protocol_method": "beam_ranked_multirow_large_neighborhood",
                             "beam_width": 32, "reconnect_rows": [1, 2, 4, 8],
                             "seed_trace": seed_trace, "smoke": smoke,
                             "execution_scope": _execution_scope(smoke),
                             "support_swaps": swaps, **info})


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

_CHALLENGERS: Dict[str, str] = {
    "q1-c1-palm-row2": "q1",
    "q1-c2-structure-reconnect": "q1",
    "q2-c1-sp2-recursive": "q2",
    "q2-c2-relax-project-polish": "q2",
    "q3-c1-discrete-coordinate": "q3",
    "q3-c2-hierarchical-reconnect": "q3",
    "q4-c1-generic-discrete": "q4",
    "q4-c2-kron-reconnect": "q4",
    "q5-c1-lexicographic-grid": "q5",
    "q5-c2-large-neighborhood": "q5",
}


def registered_challenger_ids() -> List[str]:
    return sorted(_CHALLENGERS)


def challenger_solution(candidate_id: str, target: Matrix, n: int, k: int,
                        q: Optional[int], seed: int,
                        smoke: bool = False) -> BaselineSolution:
    pid = _CHALLENGERS.get(candidate_id)
    if pid is None:
        raise KeyError(f"unregistered challenger {candidate_id!r}")
    if candidate_id.startswith("q1-"):
        return (challenger_q1_palm_row2 if candidate_id.endswith("palm-row2")
                else challenger_q1_structure_reconnect)(n, k, seed, smoke)
    if pid == "q2":
        fn = (challenger_q2_sp2_recursive if "sp2" in candidate_id
              else challenger_q2_relax_project)
        return fn(target, n, k, int(q), seed, smoke)
    if pid == "q3":
        fn = (challenger_q3_discrete_coordinate if "discrete-coordinate" in candidate_id
              else challenger_q3_hierarchical_reconnect)
        return fn(target, n, k, int(q), seed, smoke)
    if pid == "q4":
        fn = (challenger_q4_generic_discrete if "generic" in candidate_id
              else challenger_q4_kron_reconnect)
        return fn(target, n, k, int(q), seed, smoke)
    fn = (challenger_q5_lexicographic_grid if "lexicographic" in candidate_id
          else challenger_q5_large_neighborhood)
    return fn(target, n, k, int(q), seed, smoke)

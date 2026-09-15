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

from .baselines import BaselineSolution, bit_reversal_permutation, quantize_complex
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


def continuous_factor_update(target: Matrix, factors: List[Matrix], index: int,
                             q: Optional[int], row_cap: Optional[int]) -> Matrix:
    """Relax-then-project: least-squares solve, then adaptive lattice projection."""
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
            permutation: Optional[Sequence[int]] = None) -> Dict[str, object]:
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
    before = _objective(target, factors, permutation)
    accepted = 0
    rejected = 0
    for _ in range(sweeps):
        improved = False
        for i in range(len(factors)):
            candidate = exact_factor_update(target, factors, i, q, row_cap, permutation)
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
    return {"S0_start": before, "accepted_updates": accepted,
            "rejected_updates": rejected,
            "S1_final": _objective(target, factors, permutation)}


def support_swap_sweep(target: Matrix, factors: List[Matrix], q: Optional[int],
                       row_cap: int, passes: int = 1,
                       permutation: Optional[Sequence[int]] = None) -> int:
    """Single-position support swaps; accepts only objective improvements."""
    n = len(target)
    allowed = _lattice(q)
    values = ([complex(a, b) for a in allowed for b in allowed] if allowed is not None
              else [1 + 0j])
    accepted = 0
    for _ in range(passes):
        improved = False
        for factor in factors:
            for r in range(n):
                row = factor[r]
                occupied = [c for c in range(n) if row[c] != 0]
                if len(occupied) > row_cap:
                    continue
                for drop in occupied:
                    saved = row[drop]
                    row[drop] = 0j
                    base = _objective(target, factors, permutation)
                    for add in range(n):
                        if row[add] != 0:
                            continue
                        best_val, best_obj = 0j, base
                        for v in values:
                            row[add] = v
                            obj = _objective(target, factors)
                            if obj < best_obj - 1e-15:
                                best_obj, best_val = obj, v
                        if best_obj < base - 1e-15:
                            row[add] = best_val
                            accepted += 1
                            improved = True
                        else:
                            row[add] = 0j
                    if row[drop] == 0j and saved != 0j and any(row[c] != 0 for c in range(n)):
                        # the drop was accepted through `add`; keep it
                        pass
                    else:
                        row[drop] = saved
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
    from .baselines import radix2_unitary_factors
    continuous, _masks = radix2_unitary_factors(n)
    inv = 1.0 / math.sqrt(n)
    factors = [row[:] for row in continuous]
    factors[0] = [[z * inv for z in row] for row in factors[0]]
    return factors


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


def challenger_q1_palm_row2(n: int, k: int, seed: int) -> BaselineSolution:
    """``q1-c1-palm-row2``: block-coordinate (PALM-style) updates on row-2 support."""
    target = dft_matrix(n)
    factors = _exact_chain_start(n, k)
    perm = bit_reversal_permutation(n)
    if factors is None:
        factors = _random_start(n, k, None, 2, random.Random(seed))
        perm = list(range(n))
    info = _polish(target, factors, None, 2, sweeps=4, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "palm_row2", "seed": seed, **info})


def challenger_q1_structure_reconnect(n: int, k: int, seed: int) -> BaselineSolution:
    """``q1-c2-structure-reconnect``: butterfly init + support reconnection."""
    target = dft_matrix(n)
    factors = _exact_chain_start(n, k)
    perm = bit_reversal_permutation(n)
    if factors is None:
        factors = _random_start(n, k, None, 2, random.Random(seed))
        perm = list(range(n))
    _polish(target, factors, None, 2, sweeps=2, permutation=perm)
    swaps = support_swap_sweep(target, factors, None, 2, passes=1, permutation=perm)
    info = _polish(target, factors, None, 2, sweeps=2, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "structure_reconnect", "seed": seed,
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
                                seed: int) -> BaselineSolution:
    """``q2-c1-sp2-recursive``: greedy right-factor proposals then discrete polish."""
    factors, perm = _lattice_start(target, n, k, q, None)
    if k > 1:
        factors[0] = continuous_factor_update(target, factors, 0, q, None)
    info = _polish(target, factors, q, None, sweeps=3, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "sp2_recursive", "seed": seed, **info})


def challenger_q2_relax_project(target: Matrix, n: int, k: int, q: int,
                                seed: int) -> BaselineSolution:
    """``q2-c2-relax-project-polish``: continuous relax, exact projection, polish."""
    factors, perm = _lattice_start(target, n, k, q, None)
    for _ in range(2):
        for i in range(k):
            factors[i] = continuous_factor_update(target, factors, i, q, None)
    info = _polish(target, factors, q, None, sweeps=3, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "relax_project_polish", "seed": seed, **info})


def challenger_q3_discrete_coordinate(target: Matrix, n: int, k: int, q: int,
                                      seed: int) -> BaselineSolution:
    """``q3-c1-discrete-coordinate``: exact discrete updates with support swaps."""
    factors, perm = _lattice_start(target, n, k, q, 2)
    for _ in range(2):
        _polish(target, factors, q, 2, sweeps=2, permutation=perm)
        support_swap_sweep(target, factors, q, 2, passes=1, permutation=perm)
    info = _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "discrete_coordinate", "seed": seed, **info})


def challenger_q3_hierarchical_reconnect(target: Matrix, n: int, k: int, q: int,
                                         seed: int) -> BaselineSolution:
    """``q3-c2-hierarchical-reconnect``: butterfly init, polish, reconnect."""
    factors, perm = _lattice_start(target, n, k, q, 2)
    _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    swaps = support_swap_sweep(target, factors, q, 2, passes=2, permutation=perm)
    info = _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "hierarchical_reconnect", "seed": seed,
                             "support_swaps": swaps, **info})


def challenger_q4_generic_discrete(target: Matrix, n: int, k: int, q: int,
                                   seed: int) -> BaselineSolution:
    """``q4-c1-generic-discrete``: generic row-2 discrete search on the Kron target."""
    factors = _random_start(n, k, q, 2, random.Random(seed))
    for _ in range(2):
        _polish(target, factors, q, 2, sweeps=2, permutation=perm)
        support_swap_sweep(target, factors, q, 2, passes=1, permutation=perm)
    info = _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    return BaselineSolution(factors, list(range(n)), _masks_from_factors(factors),
                            {"strategy": "generic_discrete", "seed": seed, **info})


def challenger_q4_kron_reconnect(target: Matrix, n: int, k: int, q: int,
                                 seed: int) -> BaselineSolution:
    """``q4-c2-kron-reconnect``: Kronecker-aware init + cross-block reconnection."""
    # the F_4 (x) F_8 target is Kronecker-structured, so each 32x32 layer is built as
    # (4x4 layer) (x) (8x8 layer): that is the block prior this challenger keeps.
    from .baselines import radix2_unitary_factors
    f4, _ = radix2_unitary_factors(4)
    f8, _ = radix2_unitary_factors(8)
    q4 = [[[quantize_complex(z, q) for z in row] for row in f] for f in f4]
    q8 = [[[quantize_complex(z, q) for z in row] for row in f] for f in f8]
    lifted: List[Matrix] = []
    for a, b in zip(q4, q8):
        lifted.append(_enforce_row_cap(kron(a, b), 2))
    if not lifted:
        factors = _random_start(n, k, q, 2, random.Random(seed))
        perm = list(range(n))
    else:
        factors = lifted[:k] if k <= len(lifted) else lifted + [identity(n)] * (k - len(lifted))
        perm = list(range(n))
    _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    swaps = support_swap_sweep(target, factors, q, 2, passes=2, permutation=perm)
    info = _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "kron_reconnect", "seed": seed,
                             "support_swaps": swaps, **info})


def challenger_q5_lexicographic_grid(target: Matrix, n: int, k: int, q: int,
                                     seed: int) -> BaselineSolution:
    """``q5-c1-lexicographic-grid``: feasibility-first discrete search at fixed (q,K)."""
    factors, perm = _lattice_start(target, n, k, q, 2)
    for _ in range(3):
        _polish(target, factors, q, 2, sweeps=2, permutation=perm)
        support_swap_sweep(target, factors, q, 2, passes=1, permutation=perm)
    info = _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "lexicographic_grid", "seed": seed, **info})


def challenger_q5_large_neighborhood(target: Matrix, n: int, k: int, q: int,
                                     seed: int) -> BaselineSolution:
    """``q5-c2-large-neighborhood``: multi-pass reconnect + polish."""
    factors, perm = _lattice_start(target, n, k, q, 2)
    _polish(target, factors, q, 2, sweeps=2, permutation=perm)
    swaps = support_swap_sweep(target, factors, q, 2, passes=3, permutation=perm)
    info = _polish(target, factors, q, 2, sweeps=3, permutation=perm)
    return BaselineSolution(factors, perm, _masks_from_factors(factors),
                            {"strategy": "large_neighborhood", "seed": seed,
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
                        q: Optional[int], seed: int) -> BaselineSolution:
    pid = _CHALLENGERS.get(candidate_id)
    if pid is None:
        raise KeyError(f"unregistered challenger {candidate_id!r}")
    if candidate_id.startswith("q1-"):
        return (challenger_q1_palm_row2 if candidate_id.endswith("palm-row2")
                else challenger_q1_structure_reconnect)(n, k, seed)
    if pid == "q2":
        fn = (challenger_q2_sp2_recursive if "sp2" in candidate_id
              else challenger_q2_relax_project)
        return fn(target, n, k, int(q), seed)
    if pid == "q3":
        fn = (challenger_q3_discrete_coordinate if "discrete-coordinate" in candidate_id
              else challenger_q3_hierarchical_reconnect)
        return fn(target, n, k, int(q), seed)
    if pid == "q4":
        fn = (challenger_q4_generic_discrete if "generic" in candidate_id
              else challenger_q4_kron_reconnect)
        return fn(target, n, k, int(q), seed)
    fn = (challenger_q5_lexicographic_grid if "lexicographic" in candidate_id
          else challenger_q5_large_neighborhood)
    return fn(target, n, k, int(q), seed)

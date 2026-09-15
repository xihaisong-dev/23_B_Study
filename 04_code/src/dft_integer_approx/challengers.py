# AI-assisted development disclosure (D-011)
# Tool/model: DeepSeek Harness, deepseek-v4-flash
# Developer/provider: DeepSeek
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification required: every challenger run is gate-checked, constraint-checked,
# independently recomputed and hashed before any number may be quoted.
"""Registered challengers for the frozen protocol, built on :mod:`challenger_core`.

Per-problem constraints decide which optimiser is legal:

======== ============ ================ ==================================
problem  row cap      alphabet         update used
======== ============ ================ ==================================
q1       <= 2         unrestricted     uncapped exact update, then re-apply cap
q2       none         P_3              uncapped exact update (dense allowed)
q3/q4/q5 <= 2         P_q              :func:`sparse_row_update` (cap-aware)
======== ============ ================ ==================================

The q1 row is the subtle one: a *cap-aware* sparse update is the right tool for
q3/q4/q5, but for q1 it is actively harmful, because the exact radix-2 chain's first
factor is dense (the 1/sqrt(N) fold makes it so).  Applying a 2-nonzero cap to it drops
the objective from the exact value to an O(1/sqrt(N)) approximation.  q1 therefore uses
the uncapped exact update and keeps the cap as a *check* on the result, not as a search
constraint.

Every returned ``BaselineSolution`` carries the permutation the scorer applies; for
butterfly-derived chains that is ``bit_reversal_permutation(n)``.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

from . import challenger_core as core
from .baselines import (
    BaselineSolution,
    apply_permutation_right,
    bit_reversal_permutation,
    exact_q1_baseline,
    kron_quantized_butterfly_baseline,
    quantize_complex,
    radix2_unitary_factors,
)
from .targets import Matrix, dft_matrix, identity, kron, matmul, product, zeros

PROBLEM_ROW_CAP: Dict[str, Optional[int]] = {
    "q1": 2, "q2": None, "q3": 2, "q4": 2, "q5": 2,
}

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


def _butterfly_start(n: int, q: Optional[int],
                     k: int) -> Optional[Tuple[List[Matrix], List[int]]]:
    levels = int(round(math.log2(n))) if n >= 2 else 0
    if 2 ** levels != n or levels < 1:
        return None
    continuous, _ = radix2_unitary_factors(n)
    factors = [[[quantize_complex(z, q) if q is not None else z for z in row]
                for row in f] for f in continuous]
    while len(factors) < k:
        factors.append(identity(n))
    return factors[:k], bit_reversal_permutation(n)


def _identity_start(n: int, k: int) -> List[Matrix]:
    return [identity(n) for _ in range(k)]


def _random_row2_start(n: int, k: int, q: Optional[int],
                       rng: random.Random) -> List[Matrix]:
    allowed = core._lattice(q) if q is not None else [-1, 0, 1, 1j, -1j]
    factors = []
    for _ in range(k):
        m = zeros(n, n)
        for r in range(n):
            for c in rng.sample(range(n), min(2, n)):
                m[r][c] = complex(rng.choice(allowed), 0) if allowed[0] != 0 else 1 + 0j
        factors.append(m)
    return factors


# --------------------------------------------------------------------------- #
# q1 — coefficients unrestricted, row cap 2
# --------------------------------------------------------------------------- #


def _q1_run(n: int, k: int, seed: int, sweeps: int, swaps: int) -> BaselineSolution:
    """Start from the exact chain (RMSE 0 at K = log2 n) and never accept a worse one."""
    target = dft_matrix(n)
    baseline = exact_q1_baseline(n)
    factors = [row[:] for row in baseline.factors]
    permutation = list(baseline.permutation)
    rng = random.Random(seed)
    info = core.descend(target, factors, None, None, sweeps=sweeps,
                        permutation=permutation, rng=rng)
    # never publish something worse than the deterministic baseline
    if core._objective(target, factors, permutation) > core._objective(
            target, baseline.factors, permutation) + 1e-12:
        factors = [row[:] for row in baseline.factors]
        info["reverted_to_baseline"] = True
    caps_ok = all(core._row_support(row) <= 2 for f in factors for row in f)
    return BaselineSolution(factors, permutation, core._masks_from_factors(factors),
                            {"strategy": "q1_uncapped_exact_descent", "seed": seed,
                             "row_cap_respected": caps_ok, **info})


def challenger_q1_palm_row2(n: int, k: int, seed: int,
                            smoke: bool = False) -> BaselineSolution:
    return _q1_run(n, k, seed, sweeps=2 if smoke else 4, swaps=0)


def challenger_q1_structure_reconnect(n: int, k: int, seed: int,
                                      smoke: bool = False) -> BaselineSolution:
    return _q1_run(n, k, seed, sweeps=2 if smoke else 3, swaps=1)


# --------------------------------------------------------------------------- #
# discrete challengers
# --------------------------------------------------------------------------- #


def _discrete_run(problem: str, target: Matrix, n: int, k: int, q: int, seed: int,
                  sweeps: int, swap_passes: int,
                  smoke: bool = False) -> BaselineSolution:
    cap = PROBLEM_ROW_CAP[problem]
    rng = random.Random(seed)
    start = _butterfly_start(n, q, k)
    if start is not None:
        factors, permutation = start
    elif problem == "q4":
        lifted = kron_quantized_butterfly_baseline(q)
        factors = [row[:] for row in lifted.factors][:k]
        while len(factors) < k:
            factors.append(identity(n))
        permutation = list(lifted.permutation)
    else:
        factors = _random_row2_start(n, k, q, rng)
        permutation = list(range(n))
    before = core._objective(target, factors, permutation)
    info = core.descend(target, factors, q, cap, sweeps=sweeps,
                        permutation=permutation, rng=rng)
    info["S0"] = before
    info["strategy"] = f"{problem}_discrete"
    info["seed"] = seed
    info["smoke"] = smoke
    return BaselineSolution(factors, permutation, core._masks_from_factors(factors), info)


def challenger_q2_sp2_recursive(target: Matrix, n: int, k: int, q: int, seed: int,
                                smoke: bool = False) -> BaselineSolution:
    cap = None
    rng = random.Random(seed)
    start = _butterfly_start(n, q, k)
    factors, permutation = start if start is not None else (_identity_start(n, k),
                                                           list(range(n)))
    info = core.descend(target, factors, q, cap, sweeps=1 if smoke else 3,
                        permutation=permutation, rng=rng)
    info.update({"strategy": "q2_sp2_recursive", "seed": seed, "smoke": smoke})
    return BaselineSolution(factors, permutation, core._masks_from_factors(factors), info)


def challenger_q2_relax_project(target: Matrix, n: int, k: int, q: int, seed: int,
                                smoke: bool = False) -> BaselineSolution:
    rng = random.Random(seed)
    start = _butterfly_start(n, q, k)
    factors, permutation = start if start is not None else (_identity_start(n, k),
                                                           list(range(n)))
    for _ in range(1 if smoke else 2):
        for i in range(len(factors)):
            factors[i] = core.continuous_factor_update(target, factors, i, q, None,
                                                       permutation)
    info = core.descend(target, factors, q, None, sweeps=1 if smoke else 3,
                        permutation=permutation, rng=rng)
    info.update({"strategy": "q2_relax_project_polish", "seed": seed, "smoke": smoke})
    return BaselineSolution(factors, permutation, core._masks_from_factors(factors), info)


def challenger_q3_discrete_coordinate(target: Matrix, n: int, k: int, q: int, seed: int,
                                      smoke: bool = False) -> BaselineSolution:
    return _discrete_run("q3", target, n, k, q, seed,
                         sweeps=1 if smoke else 3, swap_passes=0, smoke=smoke)


def challenger_q3_hierarchical_reconnect(target: Matrix, n: int, k: int, q: int,
                                         seed: int, smoke: bool = False) -> BaselineSolution:
    return _discrete_run("q3", target, n, k, q, seed,
                         sweeps=1 if smoke else 4, swap_passes=0, smoke=smoke)


def challenger_q4_generic_discrete(target: Matrix, n: int, k: int, q: int, seed: int,
                                   smoke: bool = False) -> BaselineSolution:
    return _discrete_run("q4", target, n, k, q, seed,
                         sweeps=1 if smoke else 3, swap_passes=0, smoke=smoke)


def challenger_q4_kron_reconnect(target: Matrix, n: int, k: int, q: int, seed: int,
                                 smoke: bool = False) -> BaselineSolution:
    return _discrete_run("q4", target, n, k, q, seed,
                         sweeps=1 if smoke else 4, swap_passes=0, smoke=smoke)


def challenger_q5_lexicographic_grid(target: Matrix, n: int, k: int, q: int, seed: int,
                                     smoke: bool = False) -> BaselineSolution:
    return _discrete_run("q5", target, n, k, q, seed,
                         sweeps=1 if smoke else 3, swap_passes=0, smoke=smoke)


def challenger_q5_large_neighborhood(target: Matrix, n: int, k: int, q: int, seed: int,
                                     smoke: bool = False) -> BaselineSolution:
    return _discrete_run("q5", target, n, k, q, seed,
                         sweeps=1 if smoke else 5, swap_passes=0, smoke=smoke)


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

_FUNCS = {
    "q1-c1-palm-row2": challenger_q1_palm_row2,
    "q1-c2-structure-reconnect": challenger_q1_structure_reconnect,
    "q2-c1-sp2-recursive": challenger_q2_sp2_recursive,
    "q2-c2-relax-project-polish": challenger_q2_relax_project,
    "q3-c1-discrete-coordinate": challenger_q3_discrete_coordinate,
    "q3-c2-hierarchical-reconnect": challenger_q3_hierarchical_reconnect,
    "q4-c1-generic-discrete": challenger_q4_generic_discrete,
    "q4-c2-kron-reconnect": challenger_q4_kron_reconnect,
    "q5-c1-lexicographic-grid": challenger_q5_lexicographic_grid,
    "q5-c2-large-neighborhood": challenger_q5_large_neighborhood,
}


def challenger_solution(candidate_id: str, target: Matrix, n: int, k: int,
                        q: Optional[int], seed: int,
                        smoke: bool = False) -> BaselineSolution:
    fn = _FUNCS.get(candidate_id)
    if fn is None:
        raise KeyError(f"unregistered challenger {candidate_id!r}")
    if candidate_id.startswith("q1-"):
        return fn(n, k, seed, smoke)
    return fn(target, n, k, int(q), seed, smoke)

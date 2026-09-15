# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: deterministic construction, constraints, hashes, and independent recomputation are required before use.
"""Deterministic L1 baseline constructions fixed by the frozen protocol."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .constraints import alphabet_pq
from .targets import Matrix, identity, kron, matmul, product, zeros


@dataclass
class BaselineSolution:
    factors: List[Matrix]
    permutation: List[int]
    support_masks: List[List[List[int]]]
    diagnostics: dict


def bit_reverse(value: int, width: int) -> int:
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def bit_reversal_permutation(n: int) -> List[int]:
    levels = _power_of_two_levels(n)
    return [bit_reverse(i, levels) for i in range(n)]


def permutation_matrix(mapping: Sequence[int]) -> Matrix:
    n = len(mapping)
    if sorted(mapping) != list(range(n)):
        raise ValueError("mapping is not a permutation")
    out = zeros(n, n)
    for row, col in enumerate(mapping):
        out[row][col] = 1 + 0j
    return out


def radix2_unitary_factors(n: int) -> Tuple[List[Matrix], List[List[List[int]]]]:
    """Return counted factors whose product followed by bit reversal is unitary F_N."""
    levels = _power_of_two_levels(n)
    application_stages: List[Matrix] = []
    application_masks: List[List[List[int]]] = []
    scale = 1.0 / math.sqrt(2.0)
    for level in range(1, levels + 1):
        width = 1 << level
        half = width >> 1
        stage = zeros(n, n)
        masks: List[List[int]] = [[] for _ in range(n)]
        for block in range(0, n, width):
            for offset in range(half):
                top = block + offset
                bottom = top + half
                twiddle = cmath.exp(-2j * math.pi * offset / width)
                stage[top][top] = scale
                stage[top][bottom] = scale * twiddle
                stage[bottom][top] = scale
                stage[bottom][bottom] = -scale * twiddle
                masks[top] = [top, bottom]
                masks[bottom] = [top, bottom]
        application_stages.append(stage)
        application_masks.append(masks)
    return list(reversed(application_stages)), list(reversed(application_masks))


def quantize_component(value: float, q: int) -> int:
    """Nearest P_q component; ties choose smaller magnitude, then smaller value."""
    return min(alphabet_pq(q), key=lambda item: (abs(value - item), abs(item), item))


def quantize_complex(value: complex, q: int) -> complex:
    return complex(quantize_component(value.real, q), quantize_component(value.imag, q))


def quantize_factors(factors: Sequence[Matrix], q: int) -> List[Matrix]:
    return [[[quantize_complex(value, q) for value in row] for row in factor] for factor in factors]


def exact_q1_baseline(n: int) -> BaselineSolution:
    factors, masks = radix2_unitary_factors(n)
    return BaselineSolution(factors, bit_reversal_permutation(n), masks, {"polish_passes": 0})


def onefactor_quantized_baseline(target: Matrix, q: int = 3) -> BaselineSolution:
    factor = [[quantize_complex(value, q) for value in row] for row in target]
    n = len(target)
    masks = [[[col for col in range(n)] for _ in range(n)]]
    return BaselineSolution([factor], list(range(n)), masks, {"polish_passes": 0})


def quantized_butterfly_baseline(n: int, q: int = 3, polish: bool = True) -> BaselineSolution:
    continuous, masks = radix2_unitary_factors(n)
    factors = quantize_factors(continuous, q)
    permutation = bit_reversal_permutation(n)
    diagnostics = {"polish_passes": 0}
    if polish:
        before, after, moves = fixed_order_coordinate_pass(factors, masks, permutation, n, q)
        diagnostics = {
            "polish_passes": 1,
            "accepted_moves": moves,
            "sse_before": before,
            "sse_after": after,
        }
    return BaselineSolution(factors, permutation, masks, diagnostics)


def kron_quantized_butterfly_baseline(q: int = 3) -> BaselineSolution:
    factors4, masks4 = radix2_unitary_factors(4)
    factors8, masks8 = radix2_unitary_factors(8)
    factors4 = quantize_factors(factors4, q)
    factors8 = quantize_factors(factors8, q)
    i4, i8 = identity(4), identity(8)
    lifted: List[Matrix] = []
    lifted_masks: List[List[List[int]]] = []
    for factor, mask in zip(factors4, masks4):
        lifted.append(kron(factor, i8))
        lifted_masks.append(_lift_left_mask(mask, 8))
    for factor, mask in zip(factors8, masks8):
        lifted.append(kron(i4, factor))
        lifted_masks.append(_lift_right_mask(mask, 4, 8))
    p4 = bit_reversal_permutation(4)
    p8 = bit_reversal_permutation(8)
    permutation = [p4[row // 8] * 8 + p8[row % 8] for row in range(32)]
    return BaselineSolution(lifted, permutation, lifted_masks, {"polish_passes": 0})


def q1_cost_baseline(n: int, k: int) -> BaselineSolution:
    """P1 Butterfly baseline at one registered K, followed by one deterministic pass."""
    if k < 1:
        raise ValueError("k must be positive")
    continuous, masks = radix2_unitary_factors(n)
    levels = len(continuous)
    if k <= levels:
        selected = continuous[-k:]
        selected_masks = masks[-k:]
    else:
        extra = k - levels
        selected = []
        selected_masks = []
        for idx in range(extra):
            mask = masks[idx % levels]
            selected.append(_identity_on_mask(n, mask))
            selected_masks.append(mask)
        selected.extend(continuous)
        selected_masks.extend(masks)
    factors = quantize_factors(selected, 1)
    permutation = bit_reversal_permutation(n)
    before, after, moves = fixed_order_coordinate_pass(
        factors, selected_masks, permutation, n, 1
    )
    return BaselineSolution(
        factors,
        permutation,
        selected_masks,
        {
            "polish_passes": 1,
            "accepted_moves": moves,
            "sse_before": before,
            "sse_after": after,
        },
    )


def apply_permutation_right(matrix: Matrix, mapping: Sequence[int]) -> Matrix:
    """Return ``matrix @ P`` for ``P[row,mapping[row]]=1``."""
    n = len(mapping)
    inverse = [0] * n
    for row, col in enumerate(mapping):
        inverse[col] = row
    return [[matrix[r][inverse[c]] for c in range(n)] for r in range(n)]


def approximate_matrix(factors: Sequence[Matrix], mapping: Sequence[int]) -> Matrix:
    return apply_permutation_right(product(factors), mapping)


def fixed_order_coordinate_pass(
    factors: List[Matrix],
    masks: Sequence[Sequence[Sequence[int]]],
    permutation: Sequence[int],
    n: int,
    q: int,
) -> Tuple[float, float, int]:
    """One deterministic exact coordinate pass over registered support slots."""
    from .targets import dft_matrix

    if len(factors) != len(masks):
        raise ValueError("factor/mask length mismatch")
    target = dft_matrix(n)
    pmat = permutation_matrix(permutation)
    suffix: List[Optional[Matrix]] = [None] * (len(factors) + 1)
    suffix[-1] = pmat
    for idx in range(len(factors) - 1, -1, -1):
        suffix[idx] = matmul(factors[idx], suffix[idx + 1])
    approx = suffix[0]
    if approx is None:
        raise ValueError("empty factor chain")
    before = _squared_error(target, approx)
    left = identity(n)
    values = [complex(real, imag) for real in sorted(alphabet_pq(q)) for imag in sorted(alphabet_pq(q))]
    accepted = 0
    for idx, factor in enumerate(factors):
        right = suffix[idx + 1]
        if right is None:
            raise AssertionError("missing suffix")
        for row in range(n):
            u = [left[out_row][row] for out_row in range(n)]
            for col in masks[idx][row]:
                v = right[col]
                current = factor[row][col]
                inner, norm_outer = _outer_error_inner(target, approx, u, v)
                current_sse = _squared_error(target, approx)
                best = current
                best_sse = current_sse
                for candidate in values:
                    delta = candidate - current
                    score = current_sse - 2.0 * (delta.conjugate() * inner).real
                    score += abs(delta) ** 2 * norm_outer
                    key = (score, abs(candidate), candidate.real, candidate.imag)
                    best_key = (best_sse, abs(best), best.real, best.imag)
                    if key < best_key:
                        best = candidate
                        best_sse = score
                if best != current:
                    delta = best - current
                    factor[row][col] = best
                    for out_row in range(n):
                        scale = delta * u[out_row]
                        if scale == 0:
                            continue
                        for out_col in range(n):
                            approx[out_row][out_col] += scale * v[out_col]
                    accepted += 1
        left = matmul(left, factor)
    after = _squared_error(target, approx)
    return before, after, accepted


def _outer_error_inner(target: Matrix, approx: Matrix, u: Sequence[complex], v: Sequence[complex]) -> Tuple[complex, float]:
    inner = 0j
    norm_u = sum(abs(value) ** 2 for value in u)
    norm_v = sum(abs(value) ** 2 for value in v)
    for row, u_value in enumerate(u):
        if u_value == 0:
            continue
        conjugate_u = u_value.conjugate()
        for col, v_value in enumerate(v):
            if v_value != 0:
                inner += conjugate_u * v_value.conjugate() * (target[row][col] - approx[row][col])
    return inner, norm_u * norm_v


def _squared_error(target: Matrix, approx: Matrix) -> float:
    return sum(abs(target[r][c] - approx[r][c]) ** 2 for r in range(len(target)) for c in range(len(target)))


def _identity_on_mask(n: int, mask: Sequence[Sequence[int]]) -> Matrix:
    factor = zeros(n, n)
    for row, columns in enumerate(mask):
        if row not in columns:
            raise ValueError("extension mask must contain the diagonal")
        factor[row][row] = 1 + 0j
    return factor


def _lift_left_mask(mask: Sequence[Sequence[int]], right_n: int) -> List[List[int]]:
    lifted: List[List[int]] = []
    for left_row, columns in enumerate(mask):
        for right_row in range(right_n):
            lifted.append([left_col * right_n + right_row for left_col in columns])
    return lifted


def _lift_right_mask(mask: Sequence[Sequence[int]], left_n: int, right_n: int) -> List[List[int]]:
    lifted: List[List[int]] = []
    for left_row in range(left_n):
        for right_row, columns in enumerate(mask):
            lifted.append([left_row * right_n + right_col for right_col in columns])
    return lifted


def _power_of_two_levels(n: int) -> int:
    if not isinstance(n, int) or n < 2 or n & (n - 1):
        raise ValueError(f"n must be a power of two >=2, got {n!r}")
    return n.bit_length() - 1

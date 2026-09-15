# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: sparse artifact round-trips and SHA-256 bindings are tested before formal use.
"""Sparse, lossless JSON artifacts for factors and pure permutations."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from .targets import Matrix, zeros


def factor_payload(factors: Sequence[Matrix], permutation: Sequence[int], q: int) -> Dict[str, Any]:
    n = len(permutation)
    encoded = []
    for factor in factors:
        entries = []
        for row in range(n):
            for col in range(n):
                value = factor[row][col]
                if value != 0 or _negative_zero(value.real) or _negative_zero(value.imag):
                    entries.append([row, col, value.real, value.imag])
        encoded.append({"shape": [n, n], "nonzero": entries})
    return {
        "schema_version": "1.0",
        "factor_order": "A1@A2@...@AK, followed on the right by the pure permutation",
        "q": q,
        "N": n,
        "K": len(factors),
        "factors": encoded,
        "pure_permutation": {"counted_in_K": False, "mapping": list(permutation)},
    }


def write_factor_artifact(path: Path, factors: Sequence[Matrix], permutation: Sequence[int], q: int) -> None:
    payload = factor_payload(factors, permutation, q)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def read_factor_artifact(path: Path) -> Tuple[list[Matrix], list[int], int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    n = payload["N"]
    factors: list[Matrix] = []
    for encoded in payload["factors"]:
        if encoded["shape"] != [n, n]:
            raise ValueError("factor shape mismatch")
        factor = zeros(n, n)
        seen = set()
        for row, col, real, imag in encoded["nonzero"]:
            key = (row, col)
            if key in seen:
                raise ValueError(f"duplicate factor entry {key}")
            seen.add(key)
            factor[row][col] = complex(real, imag)
        factors.append(factor)
    permutation = payload["pure_permutation"]["mapping"]
    if sorted(permutation) != list(range(n)):
        raise ValueError("invalid pure permutation")
    if len(factors) != payload["K"]:
        raise ValueError("factor count mismatch")
    return factors, permutation, payload["q"]


def _negative_zero(value: float) -> bool:
    return value == 0.0 and math.copysign(1.0, value) < 0

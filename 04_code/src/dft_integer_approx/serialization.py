# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: canonical serialization is tested for order, shape, and determinism.
"""Unambiguous byte serialization for complex matrices, for content hashing."""

from __future__ import annotations

import hashlib
import struct
from typing import List, Sequence

Matrix = List[List[complex]]


def canonical_matrix_bytes(matrix: Matrix) -> bytes:
    """Row-major little-endian float64 real/imag pairs with a shape header.

    The ``(rows, cols)`` uint32 header makes shape explicit and guards against a
    row/column transposition producing an identical byte stream.
    """
    _validate(matrix)
    rows = len(matrix)
    cols = len(matrix[0])
    out = bytearray(struct.pack("<II", rows, cols))
    pack = struct.Struct("<dd")
    for row in matrix:
        for value in row:
            out += pack.pack(value.real, value.imag)
    return bytes(out)


def canonical_matrix_sha256(matrix: Matrix) -> str:
    return hashlib.sha256(canonical_matrix_bytes(matrix)).hexdigest()


def factors_sha256(factors: Sequence[Matrix]) -> str:
    """Content hash of a factor chain; order-sensitive and 0x00-delimited."""
    h = hashlib.sha256()
    for factor in factors:
        h.update(canonical_matrix_bytes(factor))
        h.update(b"\x00")
    return h.hexdigest()


def _validate(matrix: Matrix) -> None:
    if not matrix:
        raise ValueError("empty matrix")
    n = len(matrix)
    for row in matrix:
        if len(row) != n:
            raise ValueError("matrix must be square")

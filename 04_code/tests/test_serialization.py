# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: tests distinguish factor order, shape, and transpose cases.
"""Canonical serialization and content-hashing tests."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import serialization as s  # noqa: E402


class TestSerialization(unittest.TestCase):
    def test_deterministic(self):
        m = [[1 + 0j, 2j], [0j, -1 - 1j]]
        self.assertEqual(s.canonical_matrix_sha256(m), s.canonical_matrix_sha256(m))

    def test_transpose_distinguished(self):
        a = [[1 + 0j, 2 + 0j], [3 + 0j, 4 + 0j]]
        at = [[1 + 0j, 3 + 0j], [2 + 0j, 4 + 0j]]
        self.assertNotEqual(s.canonical_matrix_sha256(a), s.canonical_matrix_sha256(at))

    def test_shape_in_header(self):
        self.assertNotEqual(
            s.canonical_matrix_sha256([[1 + 0j]]),
            s.canonical_matrix_sha256([[1 + 0j, 0j], [0j, 1 + 0j]]),
        )

    def test_factors_order_sensitive(self):
        a = [[0j, 1 + 0j], [1 + 0j, 0j]]
        b = [[1 + 0j, 0j], [0j, -1 + 0j]]
        self.assertNotEqual(s.factors_sha256([a, b]), s.factors_sha256([b, a]))

    def test_non_square_fails(self):
        with self.assertRaises(ValueError):
            s.canonical_matrix_bytes([[1 + 0j, 2 + 0j]])


if __name__ == "__main__":
    unittest.main()

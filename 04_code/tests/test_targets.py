"""Target construction tests (synthetic / hand-worked fixtures only)."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import metrics as m  # noqa: E402
from dft_integer_approx import targets as t  # noqa: E402


def _hermitian_residual(m):
    n = len(m)
    worst = 0.0
    for a in range(n):
        for b in range(n):
            inner = sum(m[r][a].conjugate() * m[r][b] for r in range(n))
            target = 1.0 if a == b else 0.0
            worst = max(worst, abs(inner - target))
    return worst


class TestDFT(unittest.TestCase):
    def test_dft_n2_hand_worked(self):
        f = t.dft_matrix(2)
        inv = 1.0 / math.sqrt(2)
        self.assertAlmostEqual(f[0][0].real, inv, places=14)
        self.assertAlmostEqual(f[0][1].real, inv, places=14)
        self.assertAlmostEqual(f[1][0].real, inv, places=14)
        self.assertAlmostEqual(f[1][1].real, -inv, places=14)

    def test_raw_is_scaled_unitary(self):
        for n in (2, 4, 8):
            raw = t.raw_dft_matrix(n)
            scaled = t.scale(t.dft_matrix(n), math.sqrt(n))
            self.assertLess(m.max_abs_difference(raw, scaled), 1e-12)

    def test_unitary(self):
        for n in (4, 8):
            self.assertLess(_hermitian_residual(t.dft_matrix(n)), 1e-12)


class TestKron(unittest.TestCase):
    def test_f4_kron_f8_not_f32(self):
        target = t.kron(t.dft_matrix(4), t.dft_matrix(8))
        f32 = t.dft_matrix(32)
        self.assertEqual(len(target), 32)
        self.assertEqual(len(target[0]), 32)
        diff = m.max_abs_difference(target, f32)
        self.assertGreater(diff, 0.3)
        self.assertLess(diff, 0.4)
        self.assertLess(_hermitian_residual(target), 1e-12)


class TestProductOrder(unittest.TestCase):
    def test_leftmost_first(self):
        a = [[0j, 1 + 0j], [1 + 0j, 0j]]
        b = [[1 + 0j, 0j], [0j, -1 + 0j]]
        ab = t.product([a, b])
        ba = t.product([b, a])
        # A@B = [[0, -1], [1, 0]]; B@A = [[0, 1], [-1, 0]].
        self.assertEqual(ab[0][1], -1 + 0j)
        self.assertEqual(ab[1][0], 1 + 0j)
        self.assertNotEqual(ab[0][1], ba[0][1])
        self.assertEqual(ba[0][1], 1 + 0j)

    def test_single_factor_identity(self):
        f = t.dft_matrix(2)
        self.assertEqual(t.product([f]), f)

    def test_mismatched_factors_fail(self):
        with self.assertRaises(ValueError):
            t.product([t.dft_matrix(2), t.dft_matrix(4)])


if __name__ == "__main__":
    unittest.main()

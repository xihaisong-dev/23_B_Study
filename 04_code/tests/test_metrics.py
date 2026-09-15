"""RMSE and norm primitive tests (synthetic fixtures only)."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import metrics as m  # noqa: E402
from dft_integer_approx import targets as t  # noqa: E402


class TestRMSE(unittest.TestCase):
    def test_identical_zero(self):
        f = t.dft_matrix(2)
        self.assertEqual(m.rmse(f, f), 0.0)

    def test_known_single_entry(self):
        # ||[[1,0],[0,1]] - [[1,0],[0,0]]||_F / 2 = 1 / 2.
        target = [[1 + 0j, 0j], [0j, 1 + 0j]]
        approx = [[1 + 0j, 0j], [0j, 0j]]
        self.assertAlmostEqual(m.rmse(target, approx), 0.5, places=14)

    def test_beta1_f2_chain_contract(self):
        # V6_VALIDATOR_SPEC section 7 item 1: A1 = F2, beta = 1 -> RMSE 0.
        f = t.dft_matrix(2)
        self.assertEqual(m.rmse(f, t.product([f])), 0.0)

    def test_frobenius_homogeneous(self):
        target = t.dft_matrix(4)
        approx = t.identity(4)
        self.assertAlmostEqual(
            m.rmse(t.scale(target, 2.0), t.scale(approx, 2.0)),
            2.0 * m.rmse(target, approx),
            places=12,
        )

    def test_mismatched_fails(self):
        with self.assertRaises(ValueError):
            m.rmse(t.dft_matrix(2), t.dft_matrix(4))


if __name__ == "__main__":
    unittest.main()

"""Constraint 1 (row sparsity) and constraint 2 (alphabet) tests."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import constraints as c  # noqa: E402


class TestRowSparse(unittest.TestCase):
    def test_two_free_nonzeros_ok(self):
        m = [[1 + 0j, 1 + 0j], [0j, 0j]]
        ok, violations = c.check_row_sparse(m, 2)
        self.assertTrue(ok)
        self.assertEqual(violations, [])

    def test_three_nonzeros_fail_even_if_free(self):
        m = [[1 + 0j, 1 + 0j, 1 + 0j],
             [0j, 0j, 0j],
             [0j, 0j, 0j]]
        ok, violations = c.check_row_sparse(m, 2)
        self.assertFalse(ok)
        self.assertTrue(any("row 0" in v for v in violations))

    def test_max_row_support(self):
        m = [[1 + 0j, 0j], [1 + 0j, 1j]]
        self.assertEqual(c.max_row_support(m), 2)


class TestAlphabet(unittest.TestCase):
    def test_pq_q3(self):
        self.assertEqual(c.alphabet_pq(3), frozenset({0, 1, -1, 2, -2, 4, -4}))

    def test_q3_legal_and_illegal(self):
        self.assertTrue(c.is_in_alphabet(2 + 4j, 3))
        self.assertTrue(c.is_in_alphabet(0j, 3))
        self.assertFalse(c.is_in_alphabet(3 + 0j, 3))
        self.assertFalse(c.is_in_alphabet(8 + 0j, 3))
        self.assertFalse(c.is_in_alphabet(1.0000000001 + 0j, 3))

    def test_q1(self):
        self.assertTrue(c.is_in_alphabet(1 + 1j, 1))
        self.assertFalse(c.is_in_alphabet(2 + 0j, 1))

    def test_cartesian_parts(self):
        self.assertTrue(c.is_in_alphabet(2 + 0j, 3))
        self.assertTrue(c.is_in_alphabet(0 + 4j, 3))
        self.assertFalse(c.is_in_alphabet(2 + 3j, 3))

    def test_invalid_q(self):
        with self.assertRaises(ValueError):
            c.alphabet_pq(0)


class TestFiniteSquare(unittest.TestCase):
    def test_non_square_fails(self):
        with self.assertRaises(ValueError):
            c.check_finite_square([[1 + 0j, 2 + 0j, 3 + 0j]])

    def test_nan_fails(self):
        nan = complex(float("nan"), 0.0)
        with self.assertRaises(ValueError):
            c.check_finite_square([[nan, 0j], [0j, 0j]])

    def test_finite_square_ok(self):
        c.check_finite_square([[1 + 0j, 0j], [0j, 1 + 0j]])


if __name__ == "__main__":
    unittest.main()

"""Hardware L / C counting tests (problem hand-worked example + synthetic)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import hardware as h  # noqa: E402


class TestFreeSet(unittest.TestCase):
    def test_nine_free_elements(self):
        free = [0j, 1 + 0j, -1 + 0j, 1j, -1j,
                1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j]
        for v in free:
            self.assertTrue(h.is_free(v), msg=repr(v))

    def test_all_free_matrix_zero_L(self):
        m = [[0j, 1 + 0j, -1 + 0j],
             [1j, -1j, 1 + 1j],
             [1 - 1j, -1 + 1j, -1 - 1j]]
        self.assertEqual(h.count_nontrivial_positions([m]), 0)


class TestCount(unittest.TestCase):
    def test_nonfree_counted_once(self):
        # 2, 2j, 1+2j are non-free; 0 is free -> L = 3.
        m = [[2 + 0j, 2j], [1 + 2j, 0j]]
        self.assertEqual(h.count_nontrivial_positions([m]), 3)

    def test_problem_hand_worked_single_factor(self):
        # Problem statement: left matrix alone gives L=2, q=3, C=6.
        left = [[1 + 0j, 2 + 4j], [1 + 2j, 0j]]
        self.assertEqual(h.count_nontrivial_positions([left]), 2)
        self.assertEqual(h.hardware_complexity([left], 3), 6)

    def test_problem_hand_worked_both_factors(self):
        # Both matrices as factors sum to L=4, C=12 (factor_apply semantics).
        left = [[1 + 0j, 2 + 4j], [1 + 2j, 0j]]
        right = [[0j, 1 + 0j], [2 + 4j, 2 - 4j]]
        self.assertEqual(h.count_nontrivial_positions([left, right]), 4)
        self.assertEqual(h.hardware_complexity([left, right], 3), 12)

    def test_additive_and_order_independent(self):
        a = [[2 + 0j, 0j], [0j, 0j]]
        b = [[0j, 0j], [0j, -1 + 1j]]
        self.assertEqual(h.count_nontrivial_positions([a, b]),
                         h.count_nontrivial_positions([a]) + h.count_nontrivial_positions([b]))
        self.assertEqual(h.count_nontrivial_positions([a, b]),
                         h.count_nontrivial_positions([b, a]))

    def test_near_one_not_rounded_into_free(self):
        # Fail closed: 1.0000000001 is not exactly 1, so it is counted.
        m = [[1.0000000001 + 0j, 0j], [0j, 0j]]
        self.assertEqual(h.count_nontrivial_positions([m]), 1)


class TestFailClosed(unittest.TestCase):
    def test_nonfinite_fails(self):
        nan = complex(float("nan"), 0.0)
        with self.assertRaises(ValueError):
            h.count_nontrivial_positions([[[nan, 0j], [0j, 0j]]])

    def test_invalid_q_fails(self):
        with self.assertRaises(ValueError):
            h.hardware_complexity([[[1 + 0j, 0j], [0j, 0j]]], 0)
        with self.assertRaises(ValueError):
            h.hardware_complexity([[[1 + 0j, 0j], [0j, 0j]]], 2.5)


if __name__ == "__main__":
    unittest.main()

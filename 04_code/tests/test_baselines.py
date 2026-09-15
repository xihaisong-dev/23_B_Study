# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: deterministic baseline properties are asserted on hand-checkable sizes.
"""Tests for deterministic baseline constructions."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.baselines import (  # noqa: E402
    approximate_matrix,
    exact_q1_baseline,
    kron_quantized_butterfly_baseline,
    onefactor_quantized_baseline,
    q1_cost_baseline,
    quantized_butterfly_baseline,
)
from dft_integer_approx.constraints import check_alphabet, check_row_sparse  # noqa: E402
from dft_integer_approx.hardware import count_nontrivial_positions  # noqa: E402
from dft_integer_approx.metrics import rmse  # noqa: E402
from dft_integer_approx.targets import dft_matrix, kron  # noqa: E402


class TestBaselines(unittest.TestCase):
    def test_q1_exact_registered_small_sizes(self):
        expected_l = {2: 4, 4: 8, 8: 20, 16: 52}
        for n in (2, 4, 8, 16):
            solution = exact_q1_baseline(n)
            self.assertEqual(len(solution.factors), n.bit_length() - 1)
            self.assertLessEqual(rmse(dft_matrix(n), approximate_matrix(solution.factors, solution.permutation)), 1e-12)
            self.assertTrue(all(check_row_sparse(factor, 2)[0] for factor in solution.factors))
            self.assertEqual(count_nontrivial_positions(solution.factors), expected_l[n])

    def test_q2_onefactor_is_p3(self):
        target = dft_matrix(4)
        solution = onefactor_quantized_baseline(target, 3)
        self.assertTrue(check_alphabet(solution.factors[0], 3)[0])
        self.assertEqual(len(solution.factors), 1)

    def test_q3_quantized_butterfly_is_legal(self):
        solution = quantized_butterfly_baseline(8, 3, polish=True)
        self.assertTrue(all(check_row_sparse(factor, 2)[0] for factor in solution.factors))
        self.assertTrue(all(check_alphabet(factor, 3)[0] for factor in solution.factors))
        self.assertLessEqual(solution.diagnostics["sse_after"], solution.diagnostics["sse_before"] + 1e-10)

    def test_q4_kron_baseline_shape_and_constraints(self):
        solution = kron_quantized_butterfly_baseline(3)
        self.assertEqual(len(solution.factors), 5)
        self.assertEqual(len(approximate_matrix(solution.factors, solution.permutation)), 32)
        self.assertTrue(all(check_row_sparse(factor, 2)[0] for factor in solution.factors))
        self.assertTrue(all(check_alphabet(factor, 3)[0] for factor in solution.factors))
        self.assertTrue(rmse(kron(dft_matrix(4), dft_matrix(8)), approximate_matrix(solution.factors, solution.permutation)) >= 0)

    def test_q5_all_p1_coefficients_are_free(self):
        for k in (1, 3, 5):
            solution = q1_cost_baseline(8, k)
            self.assertEqual(len(solution.factors), k)
            self.assertTrue(all(check_row_sparse(factor, 2)[0] for factor in solution.factors))
            self.assertTrue(all(check_alphabet(factor, 1)[0] for factor in solution.factors))
            self.assertEqual(count_nontrivial_positions(solution.factors), 0)


if __name__ == "__main__":
    unittest.main()

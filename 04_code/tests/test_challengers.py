# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Human verification: tests cover every frozen challenger, constraints, permutation scoring, and seed determinism.

import math
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from dft_integer_approx.baselines import approximate_matrix  # noqa: E402
from dft_integer_approx.challengers import (  # noqa: E402
    _objective,
    challenger_solution,
    registered_challenger_ids,
    support_swap_sweep,
)
from dft_integer_approx.constraints import check_alphabet, check_row_sparse  # noqa: E402
from dft_integer_approx.hardware import count_nontrivial_positions  # noqa: E402
from dft_integer_approx.metrics import rmse  # noqa: E402
from dft_integer_approx.targets import dft_matrix, identity, kron, zeros  # noqa: E402


EXPECTED = {
    "q1-c1-palm-row2", "q1-c2-structure-reconnect",
    "q2-c1-sp2-recursive", "q2-c2-relax-project-polish",
    "q3-c1-discrete-coordinate", "q3-c2-hierarchical-reconnect",
    "q4-c1-generic-discrete", "q4-c2-kron-reconnect",
    "q5-c1-lexicographic-grid", "q5-c2-large-neighborhood",
}


class TestChallengers(unittest.TestCase):
    def test_registry_is_exactly_the_ten_frozen_challengers(self):
        self.assertEqual(set(registered_challenger_ids()), EXPECTED)

    def test_minimum_viability_all_ten(self):
        for candidate in sorted(EXPECTED):
            pid = candidate[:2]
            if pid == "q4" and "kron" in candidate:
                n, k, q = 32, 5, 3
                target = kron(dft_matrix(4), dft_matrix(8))
            else:
                n, k, q = 4, 2, 16 if pid == "q1" else (2 if pid == "q5" else 3)
                target = dft_matrix(n)
            with self.subTest(candidate=candidate):
                solution = challenger_solution(candidate, target, n, k, q, 17, smoke=True)
                self.assertEqual(len(solution.factors), k)
                self.assertEqual(sorted(solution.permutation), list(range(n)))
                value = rmse(target, approximate_matrix(solution.factors, solution.permutation))
                self.assertTrue(math.isfinite(value))
                if pid != "q2":
                    self.assertTrue(all(check_row_sparse(factor, 2)[0] for factor in solution.factors))
                if pid != "q1":
                    self.assertTrue(all(check_alphabet(factor, q)[0] for factor in solution.factors))
                self.assertEqual(solution.diagnostics["seed"], 17)
                self.assertTrue(solution.diagnostics["seed_trace"])

    def test_q1_exact_start_has_one_scale_and_correct_count(self):
        for candidate in ("q1-c1-palm-row2", "q1-c2-structure-reconnect"):
            solution = challenger_solution(candidate, dft_matrix(8), 8, 3, 16, 17, smoke=True)
            self.assertLessEqual(rmse(dft_matrix(8), approximate_matrix(solution.factors, solution.permutation)), 1e-12)
            self.assertEqual(count_nontrivial_positions(solution.factors), 20)

    def test_seed_is_deterministic_and_changes_random_search(self):
        candidate = "q4-c1-generic-discrete"
        target = dft_matrix(4)
        a = challenger_solution(candidate, target, 4, 2, 3, 17, smoke=True)
        b = challenger_solution(candidate, target, 4, 2, 3, 17, smoke=True)
        c = challenger_solution(candidate, target, 4, 2, 3, 43, smoke=True)
        self.assertEqual(a.factors, b.factors)
        self.assertEqual(a.permutation, b.permutation)
        self.assertNotEqual(a.diagnostics["seed_trace"], c.diagnostics["seed_trace"])
        self.assertNotEqual(a.factors, c.factors)

    def test_support_swap_scores_the_supplied_permutation(self):
        factor = identity(4)
        factor[0][0], factor[0][1] = 0j, 1 + 0j
        factors = [factor]
        permutation = [1, 0, 2, 3]
        target = approximate_matrix(factors, permutation)
        before = _objective(target, factors, permutation)
        support_swap_sweep(target, factors, None, 2, permutation=permutation,
                           max_rows=4, max_additions=4)
        self.assertLessEqual(_objective(target, factors, permutation), before + 1e-15)


if __name__ == "__main__":
    unittest.main()

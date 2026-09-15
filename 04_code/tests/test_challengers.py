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
from dft_integer_approx.search_budget import SearchBudget  # noqa: E402
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

    def test_q1c2_n8k3_executes_all_reconnect_rates_and_permutation_moves(self):
        solution = challenger_solution("q1-c2-structure-reconnect", dft_matrix(8),
                                       8, 3, 16, 17, smoke=True)
        diagnostics = solution.diagnostics
        self.assertEqual([item["rate"] for item in diagnostics["reconnect_trace"]],
                         [0.05, 0.1, 0.2])
        kinds = {item["kind"] for item in diagnostics["proposal_trace"]}
        self.assertIn("beam_state", kinds)
        self.assertIn("permutation_swap", kinds)
        self.assertGreater(diagnostics["evaluated_proposals"], 0)

    def test_q2c1_beam8_and_q2c2_projection_metrics_are_real(self):
        target = dft_matrix(4)
        c1 = challenger_solution("q2-c1-sp2-recursive", target, 4, 2, 3, 17,
                                 smoke=True)
        self.assertEqual(c1.diagnostics["right_factor_beam"]["evaluated"], 8)
        self.assertTrue(any(event["kind"] == "right_factor_beam"
                            for event in c1.diagnostics["proposal_trace"]))
        c2 = challenger_solution("q2-c2-relax-project-polish", target, 4, 2, 3,
                                 17, smoke=True)
        self.assertTrue(math.isfinite(c2.diagnostics["pre_projection_rmse"]))
        self.assertTrue(math.isfinite(c2.diagnostics["post_projection_rmse"]))
        self.assertTrue(all(check_alphabet(factor, 3)[0] for factor in c2.factors))

    def test_q3_exact_single_row_and_beam_mvt(self):
        target = dft_matrix(8)
        c1 = challenger_solution("q3-c1-discrete-coordinate", target, 8, 3, 3,
                                 17, smoke=True)
        support_sweeps = [event for event in c1.diagnostics["improvement_trace"]
                          if event["phase"] == "N_times_K_single_row_swaps"]
        self.assertTrue(support_sweeps)
        self.assertEqual(support_sweeps[0]["evaluated"], 8 * 3)
        c2 = challenger_solution("q3-c2-hierarchical-reconnect", target, 8, 3,
                                 3, 17, smoke=True)
        self.assertEqual(c2.diagnostics["beam_trace"]["evaluated"], 16 * 3)
        self.assertEqual(c2.diagnostics["beam_trace"]["retained"], 16)

    def test_q5c2_n8_q1_k3_has_real_large_neighborhood_trace(self):
        solution = challenger_solution("q5-c2-large-neighborhood", dft_matrix(8),
                                       8, 3, 1, 17, smoke=True)
        self.assertFalse(solution.diagnostics["safely_pruned"])
        self.assertEqual(solution.diagnostics["beam_trace"]["evaluated"], 32 * 4)
        self.assertTrue(solution.diagnostics["proposal_trace"])
        self.assertTrue(all(check_alphabet(factor, 1)[0] for factor in solution.factors))

    def test_q5c1_executes_q1_q2_by_two_k_grid_cells(self):
        target = dft_matrix(4)
        cells = []
        for q in (1, 2):
            for k in (1, 2):
                solution = challenger_solution("q5-c1-lexicographic-grid", target,
                                               4, k, q, 17, smoke=True)
                self.assertGreater(solution.diagnostics["evaluated_proposals"], 0)
                self.assertTrue(solution.diagnostics["proposal_trace"])
                self.assertTrue(all(check_alphabet(factor, q)[0]
                                    for factor in solution.factors))
                cells.append((q, k, solution))
        self.assertEqual({(q, k) for q, k, _solution in cells},
                         {(1, 1), (1, 2), (2, 1), (2, 2)})


class TestSearchBudget(unittest.TestCase):
    def test_deadline_sweep_cap_patience_and_trace(self):
        now = [0.0]
        state = SearchBudget(5.0, 10, patience=2, tolerance=1e-10).start(lambda: now[0])
        state.finish_sweep(1.0, 1, phase="x", evaluated=2, accepted=1)
        state.finish_sweep(1.0, 1, phase="x", evaluated=2, accepted=0)
        state.finish_sweep(1.0, 1, phase="x", evaluated=2, accepted=0)
        self.assertTrue(state.should_stop())
        self.assertEqual(state.stop_reason, "patience")
        self.assertEqual(state.evaluated_proposals, 6)
        deadline = SearchBudget(1.0, 10).start(lambda: now[0])
        now[0] = 2.0
        self.assertTrue(deadline.should_stop())
        self.assertEqual(deadline.stop_reason, "wall_deadline")


if __name__ == "__main__":
    unittest.main()

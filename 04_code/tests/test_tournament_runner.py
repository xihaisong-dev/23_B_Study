# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Human verification: plan expansion is checked against the frozen Cartesian product.

import json
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))

from dft_integer_approx.formal_tournament_runner import build_plan  # noqa: E402


class TestTournamentPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((WORKSPACE / "03_model/tournament_protocol.json").read_text(encoding="utf-8"))

    def test_full_l2_grid_has_all_1442_tuples(self):
        plan = build_plan(self.protocol)
        self.assertEqual(len(plan), 1442)
        tuples = {(x["problem"], x["candidate_id"], x["N"], x["K"], x["q"], x["seed"]) for x in plan}
        self.assertEqual(len(tuples), 1442)
        self.assertEqual({x["seed"] for x in plan if x["kind"] == "challenger"}, {17, 43, 71})

    def test_smoke_has_one_case_for_every_candidate(self):
        plan = build_plan(self.protocol, smoke=True)
        expected = {candidate["id"] for problem in self.protocol["problems"] for candidate in problem["candidates"]}
        self.assertEqual(len(plan), 15)
        self.assertEqual({x["candidate_id"] for x in plan}, expected)

    def test_problem_and_candidate_filters(self):
        plan = build_plan(self.protocol, problems=["q4"], candidates=["q4-c1-generic-discrete"])
        self.assertEqual(len(plan), 21)
        self.assertTrue(all(x["problem"] == "q4" and x["candidate_id"] == "q4-c1-generic-discrete" for x in plan))

    def test_unknown_filter_fails_closed(self):
        with self.assertRaises(ValueError):
            build_plan(self.protocol, candidates=["not-registered"])


if __name__ == "__main__":
    unittest.main()

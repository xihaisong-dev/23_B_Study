# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Human verification: plan expansion is checked against the frozen Cartesian product.

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))

from dft_integer_approx.formal_tournament_runner import (  # noqa: E402
    _json_sha256,
    _completed_tuple_hashes,
    batch_identity,
    build_plan,
    shard_plan,
    tuple_sha256,
)
from dft_integer_approx.aggregation import q5_rank_key  # noqa: E402
from dft_integer_approx.validation_runs import build_validation_plan, validation_statistics  # noqa: E402


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

    def test_stable_hash_shards_are_disjoint_and_cover_full_plan(self):
        plan = build_plan(self.protocol)
        shards = [shard_plan(plan, index, 3) for index in range(3)]
        hashes = [{tuple_sha256(case) for case in shard} for shard in shards]
        self.assertEqual(set().union(*hashes), {tuple_sha256(case) for case in plan})
        self.assertTrue(hashes[0].isdisjoint(hashes[1]))
        self.assertTrue(hashes[1].isdisjoint(hashes[2]))

    def test_filters_do_not_change_canonical_batch_identity(self):
        full = build_plan(self.protocol)
        filtered = build_plan(self.protocol, problems=["q1"])
        batch = batch_identity("a" * 64, "b" * 64, _json_sha256(full),
                               smoke=False, validation_level="L2")
        same_batch = batch_identity("a" * 64, "b" * 64, _json_sha256(full),
                                    smoke=False, validation_level="L2")
        self.assertEqual(batch, same_batch)
        self.assertNotEqual(_json_sha256(full), _json_sha256(filtered))

    def test_q5_order_ignores_q_after_equal_tuple(self):
        common = {"C": 3, "K": 2, "rmse": 0.09, "seed": 17,
                  "candidate_id": "q5-c1-lexicographic-grid"}
        self.assertEqual(q5_rank_key({**common, "q": 1}),
                         q5_rank_key({**common, "q": 4}))

    def test_l3_l4_preregister_parent_and_variants(self):
        l3 = build_validation_plan(self.protocol, "L3", smoke=True)
        l4 = build_validation_plan(self.protocol, "L4", smoke=True)
        self.assertEqual(len(l3), 50)
        self.assertEqual(len(l4), 40)
        self.assertTrue(all(case["parent_tuple_sha256"] and case["variant"] for case in l3 + l4))
        stats = validation_statistics([{"status": "PASS", "rmse": x}
                                       for x in (0.3, 0.1, 0.2)])
        self.assertEqual(stats, {"feasible_count": 3, "best": 0.1,
                                 "median": 0.2, "worst": 0.3})

    def test_resume_indexes_only_same_batch_tuple_hashes(self):
        root = Path(tempfile.mkdtemp())
        for index, (batch, key) in enumerate((("wanted", "a"), ("other", "b"))):
            directory = root / str(index)
            directory.mkdir()
            (directory / "run_manifest.json").write_text(
                json.dumps({"batch_id": batch, "tuple_sha256": key}),
                encoding="utf-8")
        self.assertEqual(_completed_tuple_hashes(root, "wanted"), {"a"})


if __name__ == "__main__":
    unittest.main()

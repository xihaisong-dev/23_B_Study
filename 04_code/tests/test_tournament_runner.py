# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: plan expansion is checked against the frozen Cartesian product.

import json
import shutil
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
    run_plan,
    shard_plan,
    tuple_sha256,
)
from dft_integer_approx.aggregation import q5_rank_key  # noqa: E402
from dft_integer_approx.hashing import sha256_file  # noqa: E402
from dft_integer_approx.validation_runs import (build_validation_plan,
                                                select_validation_parents,
                                                validation_statistics)  # noqa: E402


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
        self.assertEqual(sum(x["problem"] == "q5" for x in plan), 825)

    def test_smoke_has_one_case_for_every_candidate(self):
        plan = build_plan(self.protocol, smoke=True)
        expected = {candidate["id"] for problem in self.protocol["problems"] for candidate in problem["candidates"]}
        self.assertEqual(len(plan), 15)
        self.assertEqual({x["candidate_id"] for x in plan}, expected)
        self.assertTrue(all(x["budget"]["wall_clock_s"] == 20 for x in plan))
        self.assertTrue(all(x["budget"]["sweep_cap"] == 8 for x in plan
                            if x["kind"] == "challenger"))

    def test_real_l2_parent_ids_bind_into_validation_plan(self):
        root = Path(tempfile.mkdtemp())
        runs = root / "05_results/runs"
        challenger_cases = [case for case in build_plan(self.protocol, smoke=True)
                            if case["kind"] == "challenger"]
        for index, case in enumerate(challenger_cases):
            directory = runs / f"parent-{index}"
            directory.mkdir(parents=True)
            manifest = {**case, "run_id": f"parent-{index}", "batch_id": "l2-real",
                        "validation_level": "L2", "tuple_sha256": tuple_sha256(case),
                        "status": "PASS", "rmse": 0.2 + index / 100}
            (directory / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        parents = select_validation_parents(root, "l2-real", self.protocol)
        l3 = build_validation_plan(self.protocol, "L3", parents=parents)
        self.assertEqual(len(parents), 10)
        self.assertEqual(len(l3), 50)
        self.assertTrue(all(case["parent_run_id"].startswith("parent-") for case in l3))
        self.assertTrue(all(case["parent_batch_id"] == "l2-real" for case in l3))

    def test_readiness_only_q5_certificate_writes_auditable_artifact(self):
        root = Path(tempfile.mkdtemp())
        for name in ("00_admin", "01_problem", "02_retrieval", "03_model", "04_code"):
            shutil.copytree(WORKSPACE / name, root / name)
        case = next(case for case in build_plan(self.protocol, smoke=True)
                    if case["candidate_id"] == "q5-c1-lexicographic-grid")
        summary = run_plan(root, [case], command="unit-test-readiness-certificate",
                           smoke=True, batch_plan=[case], validation_level="L2",
                           q5_certificate_shortcut=True)
        manifest_path = root / summary["runs"][0]["run_manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        certificate_record = manifest["artifacts"]["q5_certificate"]
        certificate_path = root / certificate_record["path"]
        self.assertEqual(manifest["status"], "INFEASIBLE")
        self.assertEqual(manifest["constraints_status"], "PASS")
        self.assertIsNone(manifest["artifacts"]["factors"])
        self.assertEqual(sha256_file(certificate_path), certificate_record["sha256"])
        self.assertEqual(manifest["diagnostics"]["stop_reason"],
                         "exact_infeasibility_certificate")
        with self.assertRaisesRegex(RuntimeError, "frozen protocol amendment"):
            run_plan(root, [case], command="must-refuse-formal-certificate",
                     smoke=False, batch_plan=[case], validation_level="L2",
                     q5_certificate_shortcut=True)

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

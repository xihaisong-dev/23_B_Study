# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: incomplete and duplicate formal batches fail closed.

import json
import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from dft_integer_approx.aggregation import (aggregate_formal_batch,
                                            _artifact_record,
                                            _tournament,
                                            _verify_artifact_record,
                                            _verify_manifest)  # noqa: E402
from dft_integer_approx.formal_baseline_runner import _tree_sha256  # noqa: E402
from dft_integer_approx.formal_tournament_runner import (batch_identity,
                                                         _json_sha256, _run_case,
                                                         build_plan,
                                                         tuple_sha256)  # noqa: E402
from dft_integer_approx.hashing import sha256_file  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[2]


class TestAggregationFailClosed(unittest.TestCase):
    def _workspace(self):
        root = Path(tempfile.mkdtemp())
        for name in ("00_admin", "01_problem", "02_retrieval", "03_model", "04_code"):
            shutil.copytree(WORKSPACE / name, root / name)
        protocol_path = root / "03_model/tournament_protocol.json"
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        tuples = build_plan(protocol)
        input_manifest_path = root / "00_admin/input_manifest.json"
        input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
        record = input_manifest["files"][0]
        protocol_sha = sha256_file(protocol_path)
        code_sha = _tree_sha256(root / "04_code")
        plan_sha = _json_sha256(tuples)
        batch_id = batch_identity(protocol_sha, code_sha, plan_sha,
                                  smoke=False, validation_level="L2")
        batch = root / "05_results/batches" / batch_id
        runs = root / "05_results/runs"
        batch.mkdir(parents=True)
        runs.mkdir(parents=True)
        (batch / "plan.json").write_text(json.dumps({"schema_version": "3.0",
            "batch_id": batch_id, "formal": True, "validation_level": "L2",
            "tuple_count": 1442, "tuples": tuples}), encoding="utf-8")
        config = {"schema_version": "3.0", "formal": True,
                  "validation_level": "L2", "batch_id": batch_id,
                  "protocol_sha256": protocol_sha,
                  "protocol_freeze_sha256": sha256_file(root / "00_admin/freezes/tournament_protocol.json"),
                  "problem_freeze_sha256": sha256_file(root / "00_admin/freezes/problem.json"),
                  "code_tree_sha256": code_sha,
                  "input_manifest_sha256": sha256_file(input_manifest_path),
                  "problem_input_sha256": sha256_file(root / record["path"]),
                  "plan_content_sha256": plan_sha,
                  "data_class": record["data_class"],
                  "target_generation": "deterministic formula from the practice-authorized third-party-copy problem statement",
                  "q5_certificate_shortcut": False,
                  "stop_rule": {"patience": 50, "tolerance": 1e-10,
                                "deadline": "monotonic in-loop",
                                "sweep_cap": "per frozen N segment"}}
        (batch / "config.json").write_text(json.dumps(config), encoding="utf-8")
        return root, runs, tuples, batch_id, config, record

    def test_incomplete_batch_cannot_aggregate(self):
        root, _runs, _tuples, batch_id, _config, _record = self._workspace()
        with self.assertRaisesRegex(ValueError, "missing tuples"):
            aggregate_formal_batch(root, batch_id, write=False)

    def test_duplicate_tuple_cannot_aggregate(self):
        root, runs, tuples, batch_id, _config, _record = self._workspace()
        key = tuple_sha256(tuples[0])
        for index in (1, 2):
            directory = runs / str(index)
            directory.mkdir()
            (directory / "run_manifest.json").write_text(
                json.dumps({"batch_id": batch_id, "tuple_sha256": key,
                            "status": "PASS"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate tuple"):
            aggregate_formal_batch(root, batch_id, write=False)

    def test_ordered_canonical_plan_drift_fails(self):
        root, _runs, _tuples, batch_id, _config, _record = self._workspace()
        plan_path = root / "05_results/batches" / batch_id / "plan.json"
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
        payload["tuples"][0], payload["tuples"][1] = payload["tuples"][1], payload["tuples"][0]
        plan_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ordered canonical"):
            aggregate_formal_batch(root, batch_id, write=False)

    def test_tampered_batch_id_fails_recomputation(self):
        root, _runs, _tuples, batch_id, _config, _record = self._workspace()
        wrong = "l2-00000000-00000000-00000000"
        old_dir = root / "05_results/batches" / batch_id
        new_dir = root / "05_results/batches" / wrong
        old_dir.rename(new_dir)
        for name in ("plan.json", "config.json"):
            path = new_dir / name
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["batch_id"] = wrong
            path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "canonical protocol/code/plan/level"):
            aggregate_formal_batch(root, wrong, write=False)

    def _formal_manifest_fixture(self):
        root, runs, tuples, batch_id, config, problem_record = self._workspace()
        case = next(item for item in tuples
                    if item["candidate_id"] == "q1-b0-scaled-radix2" and item["N"] == 2)
        batch_dir = root / "05_results/batches" / batch_id
        plan_record = _artifact_record(batch_dir / "plan.json", root)
        config_record = _artifact_record(batch_dir / "config.json", root)
        summary = _run_case(
            root, runs, case, config["protocol_sha256"],
            config["protocol_freeze_sha256"], config["problem_freeze_sha256"],
            config["code_tree_sha256"], batch_id, config["plan_content_sha256"],
            plan_record, config_record, config["input_manifest_sha256"],
            problem_record, "unit-test-formal-single-tuple", False, "L2", False)
        manifest_path = root / summary["run_manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return (root, manifest_path, manifest, case, config, plan_record,
                config_record, problem_record)

    def test_real_formal_single_tuple_verifies_end_to_end(self):
        fixture = self._formal_manifest_fixture()
        _verify_manifest(*fixture)

    def test_manifest_strict_schema_tampering_fails(self):
        fixture = self._formal_manifest_fixture()
        root, path, manifest, case, config, plan, config_record, record = fixture
        mutations = (
            ("problem_id", "q2", "problem_id/problem"),
            ("beta", 2, "beta"),
            ("optimality_claim", None, "optimality_claim"),
            ("wall_clock_s", float("nan"), "wall_clock_s"),
        )
        for field, value, message in mutations:
            with self.subTest(field=field):
                altered = copy.deepcopy(manifest)
                altered[field] = value
                with self.assertRaisesRegex(ValueError, message):
                    _verify_manifest(root, path, altered, case, config, plan,
                                     config_record, record)
        altered = copy.deepcopy(manifest)
        altered["failure"] = {"stage": "x", "error_type": "PASS", "message": "x"}
        with self.assertRaisesRegex(ValueError, "PASS requires"):
            _verify_manifest(root, path, altered, case, config, plan,
                             config_record, record)

    def test_q5_no_winner_has_machine_gate_incompatibility(self):
        result = _tournament([{"problem": "q5", "N": 4,
                               "candidate_id": "q5-c1-lexicographic-grid",
                               "run_id": "r", "status": "INFEASIBLE"}], "batch")
        q5 = next(problem for problem in result["problems"] if problem["id"] == "q5")
        self.assertIsNone(q5["winner_id"])
        self.assertEqual(q5["gate_incompatibility"]["status"], "RECORDED")
        self.assertEqual(result["gate_incompatibilities"][0]["problem_id"], "q5")

    def test_artifact_path_size_and_sha_are_all_enforced(self):
        root = Path(tempfile.mkdtemp())
        run_dir = root / "05_results/runs/r1"
        run_dir.mkdir(parents=True)
        artifact = run_dir / "stdout.txt"
        artifact.write_text("evidence\n", encoding="utf-8")
        record = {"path": artifact.relative_to(root).as_posix(),
                  "size": artifact.stat().st_size, "sha256": sha256_file(artifact)}
        self.assertEqual(_verify_artifact_record(root, record, run_dir), artifact)
        artifact.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "artifact byte lineage"):
            _verify_artifact_record(root, record, run_dir)


if __name__ == "__main__":
    unittest.main()

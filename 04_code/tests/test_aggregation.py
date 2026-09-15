# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: incomplete and duplicate formal batches fail closed.

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from dft_integer_approx.aggregation import (aggregate_formal_batch,
                                            _verify_artifact_record)  # noqa: E402
from dft_integer_approx.formal_baseline_runner import _tree_sha256  # noqa: E402
from dft_integer_approx.formal_tournament_runner import (_json_sha256, build_plan,
                                                         tuple_sha256)  # noqa: E402
from dft_integer_approx.hashing import sha256_file  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[2]


class TestAggregationFailClosed(unittest.TestCase):
    def _workspace(self):
        root = Path(tempfile.mkdtemp())
        for name in ("00_admin", "01_problem", "02_retrieval", "03_model", "04_code"):
            shutil.copytree(WORKSPACE / name, root / name)
        batch = root / "05_results/batches/test-batch"
        runs = root / "05_results/runs"
        batch.mkdir(parents=True)
        runs.mkdir(parents=True)
        protocol_path = root / "03_model/tournament_protocol.json"
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        tuples = build_plan(protocol)
        (batch / "plan.json").write_text(json.dumps({"schema_version": "3.0",
            "batch_id": "test-batch", "formal": True, "validation_level": "L2",
            "tuple_count": 1442, "tuples": tuples}), encoding="utf-8")
        input_manifest_path = root / "00_admin/input_manifest.json"
        input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
        record = input_manifest["files"][0]
        config = {"formal": True, "validation_level": "L2", "batch_id": "test-batch",
                  "protocol_sha256": sha256_file(protocol_path),
                  "protocol_freeze_sha256": sha256_file(root / "00_admin/freezes/tournament_protocol.json"),
                  "problem_freeze_sha256": sha256_file(root / "00_admin/freezes/problem.json"),
                  "code_tree_sha256": _tree_sha256(root / "04_code"),
                  "input_manifest_sha256": sha256_file(input_manifest_path),
                  "problem_input_sha256": sha256_file(root / record["path"]),
                  "plan_content_sha256": _json_sha256(tuples),
                  "data_class": record["data_class"], "q5_certificate_shortcut": False}
        (batch / "config.json").write_text(json.dumps(config), encoding="utf-8")
        return root, runs, tuples

    def test_incomplete_batch_cannot_aggregate(self):
        root, _runs, _tuples = self._workspace()
        with self.assertRaisesRegex(ValueError, "missing tuples"):
            aggregate_formal_batch(root, "test-batch", write=False)

    def test_duplicate_tuple_cannot_aggregate(self):
        root, runs, tuples = self._workspace()
        key = tuple_sha256(tuples[0])
        for index in (1, 2):
            directory = runs / str(index)
            directory.mkdir()
            (directory / "run_manifest.json").write_text(
                json.dumps({"batch_id": "test-batch", "tuple_sha256": key,
                            "status": "PASS"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate tuple"):
            aggregate_formal_batch(root, "test-batch", write=False)

    def test_ordered_canonical_plan_drift_fails(self):
        root, _runs, _tuples = self._workspace()
        plan_path = root / "05_results/batches/test-batch/plan.json"
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
        payload["tuples"][0], payload["tuples"][1] = payload["tuples"][1], payload["tuples"][0]
        plan_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ordered canonical"):
            aggregate_formal_batch(root, "test-batch", write=False)

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

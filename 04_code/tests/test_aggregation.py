# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Human verification: incomplete and duplicate formal batches fail closed.

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from dft_integer_approx.aggregation import aggregate_formal_batch  # noqa: E402
from dft_integer_approx.formal_tournament_runner import tuple_sha256  # noqa: E402


class TestAggregationFailClosed(unittest.TestCase):
    def _workspace(self):
        root = Path(tempfile.mkdtemp())
        batch = root / "05_results/batches/test-batch"
        runs = root / "05_results/runs"
        batch.mkdir(parents=True)
        runs.mkdir(parents=True)
        tuples = [{"problem": "q1", "candidate_id": "c", "N": 2,
                   "K": 1, "q": 16, "seed": index}
                  for index in range(1442)]
        (batch / "plan.json").write_text(json.dumps({"tuple_count": 1442,
                                                      "tuples": tuples}), encoding="utf-8")
        (batch / "config.json").write_text(json.dumps({"formal": True,
                                                        "validation_level": "L2"}), encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()

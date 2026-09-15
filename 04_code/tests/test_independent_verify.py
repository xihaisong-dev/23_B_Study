# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: persisted factors are reloaded and checked against independent arithmetic.
"""Independent artifact recomputation tests."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.baselines import exact_q1_baseline, kron_quantized_butterfly_baseline  # noqa: E402
from dft_integer_approx.factor_artifacts import read_factor_artifact, write_factor_artifact  # noqa: E402
from dft_integer_approx.independent_verify import verify_artifact  # noqa: E402
from dft_integer_approx.serialization import canonical_matrix_sha256  # noqa: E402


class TestIndependentVerify(unittest.TestCase):
    def test_sparse_artifact_round_trip_and_exact_q1(self):
        solution = exact_q1_baseline(4)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "factors.json"
            write_factor_artifact(path, solution.factors, solution.permutation, 16)
            factors, permutation, q = read_factor_artifact(path)
            self.assertEqual(q, 16)
            self.assertEqual(permutation, solution.permutation)
            self.assertEqual(factors, solution.factors)
            verified = verify_artifact(path, "q1", 4, 16, 2)
            self.assertLessEqual(verified["rmse"], 1e-12)
            self.assertTrue(verified["row_support_ok"])

    def test_q4_signed_zero_round_trip_preserves_hashes(self):
        solution = kron_quantized_butterfly_baseline(3)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "factors.json"
            write_factor_artifact(path, solution.factors, solution.permutation, 3)
            factors, _, _ = read_factor_artifact(path)
            expected = [canonical_matrix_sha256(factor) for factor in solution.factors]
            actual = [canonical_matrix_sha256(factor) for factor in factors]
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()

# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: L0 must pass in the repository before baseline execution.
"""L0 suite integration test."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.l0_validation import (gaussian_integer_rmse_lower_bound,
                                              run_l0_checks,
                                              support_rmse_lower_bound)  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestL0Validation(unittest.TestCase):
    def test_support_bound(self):
        self.assertGreater(support_rmse_lower_bound(64, 5), 0)
        self.assertEqual(support_rmse_lower_bound(32, 5), 0)

    def test_gaussian_integer_bounds_all_frozen_sizes(self):
        expected = {2: 1 - 1 / (2 ** 0.5), 4: 0.5,
                    8: 1 / (8 ** 0.5), 16: 0.25,
                    32: 1 / (32 ** 0.5), 64: 0.125}
        for n, value in expected.items():
            self.assertAlmostEqual(gaussian_integer_rmse_lower_bound(n), value)
            self.assertGreater(value, 0.1)

    def test_repository_l0(self):
        result = run_l0_checks(REPO_ROOT)
        self.assertEqual(result["status"], "PASS", msg=result)


if __name__ == "__main__":
    unittest.main()

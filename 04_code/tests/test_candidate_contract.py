"""Candidate contract and gate-first runner tests (fake candidates only)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import metrics as m  # noqa: E402
from dft_integer_approx import targets as t  # noqa: E402
from dft_integer_approx.candidate_api import (  # noqa: E402
    CandidateContext,
    CandidateOutput,
    FailingCandidate,
    FakeCandidate,
    FailureRecord,
)
from dft_integer_approx.protocol_gate import ProtocolNotFrozenError  # noqa: E402
from dft_integer_approx.runner import run_candidate  # noqa: E402

REPO_ROOT = str(Path(__file__).resolve().parents[2])


class TestOutputValidation(unittest.TestCase):
    def test_success_requires_factors_and_beta(self):
        with self.assertRaises(ValueError):
            CandidateOutput(status="SUCCESS")
        with self.assertRaises(ValueError):
            CandidateOutput(status="SUCCESS", factors=(), beta=1.0)

    def test_fail_requires_failure(self):
        with self.assertRaises(ValueError):
            CandidateOutput(status="FAIL")

    def test_unknown_status(self):
        with self.assertRaises(ValueError):
            CandidateOutput(status="MAYBE")


class TestFakeCandidates(unittest.TestCase):
    def test_fake_success(self):
        factors = (t.dft_matrix(2),)
        out = FakeCandidate(factors).solve(
            CandidateContext("q1", "fake", 0, "run-0", ".")
        )
        self.assertEqual(out.status, "SUCCESS")
        self.assertEqual(out.beta, 1.0)
        self.assertEqual(out.factors, factors)

    def test_failing_candidate(self):
        out = FailingCandidate().solve(
            CandidateContext("q1", "failing", 0, "run-0", ".")
        )
        self.assertEqual(out.status, "FAIL")
        self.assertIsInstance(out.failure, FailureRecord)

    def test_independent_scoring_composes(self):
        # Fake candidate returns A1 = F2; independently recompute RMSE = 0.
        factors = (t.dft_matrix(2),)
        out = FakeCandidate(factors).solve(
            CandidateContext("q1", "fake", 0, "run-0", ".")
        )
        self.assertEqual(m.rmse(t.dft_matrix(2), t.product(out.factors)), 0.0)


class TestGateFirstRunner(unittest.TestCase):
    def test_refuses_unfrozen(self):
        with self.assertRaises(ProtocolNotFrozenError):
            run_candidate(
                FakeCandidate((t.dft_matrix(2),)),
                CandidateContext("q1", "fake", 0, "run-0", "."),
                workspace=REPO_ROOT,
            )


if __name__ == "__main__":
    unittest.main()

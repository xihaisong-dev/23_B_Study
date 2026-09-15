"""Fail-closed protocol gate tests (temp workspaces, no 05_results writes)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import protocol_gate as g  # noqa: E402

REPO_ROOT = str(Path(__file__).resolve().parents[2])


def _write_workspace(freeze_status=None, protocol_status=None, problems=True):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    model = root / "03_model"
    model.mkdir(parents=True)
    admin = root / "00_admin" / "freezes"
    admin.mkdir(parents=True)

    protocol = {
        "schema_version": "3.0",
        "status": protocol_status if protocol_status is not None else "NOT_RUN",
        "problems": [{"problem_id": "q1"}] if problems else [],
    }
    (model / "tournament_protocol.json").write_text(
        json.dumps(protocol), encoding="utf-8"
    )
    if freeze_status is not None:
        (admin / "tournament_protocol.json").write_text(
            json.dumps({"status": freeze_status}), encoding="utf-8"
        )
    return tmp, root


class TestGateAgainstRepo(unittest.TestCase):
    def test_current_repo_refuses(self):
        result = g.check_frozen(REPO_ROOT)
        self.assertFalse(result.allowed)
        joined = " ".join(result.reasons)
        self.assertIn("NOT_RUN", joined)
        self.assertIn("freeze", joined)


class TestGateOnTempWorkspaces(unittest.TestCase):
    def test_frozen_but_no_freeze_file_refuses(self):
        tmp, root = _write_workspace(
            protocol_status="FROZEN", freeze_status=None, problems=True
        )
        try:
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("freeze" in r for r in result.reasons))
        finally:
            tmp.cleanup()

    def test_all_preconditions_allow(self):
        tmp, root = _write_workspace(
            protocol_status="FROZEN", freeze_status="FROZEN", problems=True
        )
        try:
            result = g.check_frozen(str(root))
            self.assertTrue(result.allowed, msg=result.reasons)
            self.assertEqual(result.reasons, [])
        finally:
            tmp.cleanup()

    def test_empty_problems_refuses(self):
        tmp, root = _write_workspace(
            protocol_status="FROZEN", freeze_status="FROZEN", problems=False
        )
        try:
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("problems" in r for r in result.reasons))
        finally:
            tmp.cleanup()

    def test_missing_protocol_refuses(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            result = g.check_frozen(tmp.name)
            self.assertFalse(result.allowed)
            self.assertTrue(any("protocol" in r for r in result.reasons))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

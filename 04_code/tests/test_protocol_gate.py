# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: tests cover valid freezes, hash drift, and fail-closed states.
"""Fail-closed protocol gate tests (temp workspaces, no 05_results writes)."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx import protocol_gate as g  # noqa: E402

REPO_ROOT = str(Path(__file__).resolve().parents[2])


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _entry(root, relative):
    path = root / relative
    return {"path": relative, "size": path.stat().st_size, "sha256": _sha256(path)}


def _write_workspace(protocol_status="PASS", problems=True, with_freeze=True):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    model = root / "03_model"
    model.mkdir(parents=True)
    freeze_dir = root / "00_admin" / "freezes"
    freeze_dir.mkdir(parents=True)

    protocol = {
        "schema_version": "3.0",
        "status": protocol_status,
        "problems": [{"problem_id": "q1"}] if problems else [],
    }
    protocol_path = model / "tournament_protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")

    if with_freeze:
        rules_path = root / "00_admin" / "rules.json"
        rules_path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
        problem_freeze = freeze_dir / "problem.json"
        problem_freeze.write_text(
            json.dumps(
                {
                    "schema_version": "3.0",
                    "stage": "problem",
                    "status": "PASS",
                    "dependencies": [],
                    "files": [_entry(root, "00_admin/rules.json")],
                }
            ),
            encoding="utf-8",
        )
        (freeze_dir / "tournament_protocol.json").write_text(
            json.dumps(
                {
                    "schema_version": "3.0",
                    "stage": "tournament_protocol",
                    "status": "PASS",
                    "dependencies": [
                        {"stage": "problem", "manifest_sha256": _sha256(problem_freeze)}
                    ],
                    "files": [_entry(root, "03_model/tournament_protocol.json")],
                }
            ),
            encoding="utf-8",
        )
    return tmp, root


class TestGateAgainstRepo(unittest.TestCase):
    def test_current_repo_accepts_verified_freeze(self):
        result = g.check_frozen(REPO_ROOT)
        self.assertTrue(result.allowed, msg=result.reasons)
        self.assertEqual(result.reasons, [])


class TestGateOnTempWorkspaces(unittest.TestCase):
    def test_pass_but_no_freeze_file_refuses(self):
        tmp, root = _write_workspace(with_freeze=False)
        try:
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("freeze" in reason for reason in result.reasons))
        finally:
            tmp.cleanup()

    def test_frozen_status_token_is_refused(self):
        tmp, root = _write_workspace(protocol_status="FROZEN")
        try:
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("expected 'PASS'" in reason for reason in result.reasons))
        finally:
            tmp.cleanup()

    def test_verified_pass_protocol_allows(self):
        tmp, root = _write_workspace()
        try:
            result = g.check_frozen(str(root))
            self.assertTrue(result.allowed, msg=result.reasons)
            self.assertEqual(result.reasons, [])
        finally:
            tmp.cleanup()

    def test_protocol_hash_drift_refuses(self):
        tmp, root = _write_workspace()
        try:
            path = root / "03_model" / "tournament_protocol.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("frozen file changed" in reason for reason in result.reasons))
        finally:
            tmp.cleanup()

    def test_dependency_hash_drift_refuses(self):
        tmp, root = _write_workspace()
        try:
            path = root / "00_admin" / "freezes" / "problem.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("dependency changed" in reason for reason in result.reasons))
        finally:
            tmp.cleanup()

    def test_empty_problems_refuses(self):
        tmp, root = _write_workspace(problems=False)
        try:
            result = g.check_frozen(str(root))
            self.assertFalse(result.allowed)
            self.assertTrue(any("problems" in reason for reason in result.reasons))
        finally:
            tmp.cleanup()

    def test_missing_protocol_refuses(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            result = g.check_frozen(tmp.name)
            self.assertFalse(result.allowed)
            self.assertTrue(any("protocol" in reason for reason in result.reasons))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

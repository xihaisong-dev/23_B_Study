"""Fail-closed protocol gate for formal tournament runs.

The protocol is ready only when its machine status is ``PASS`` and the
workflow freeze manifest verifies against the current workspace. A freeze is
not represented by a ``FROZEN`` status token: it is represented by
``00_admin/freezes/tournament_protocol.json`` and its SHA-256 file/dependency
bindings.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PASS_STATUS = "PASS"
PROTOCOL_PATH = Path("03_model/tournament_protocol.json")
FREEZE_DIR = Path("00_admin/freezes")
FREEZE_STAGE = "tournament_protocol"
FREEZE_DEPENDENCIES = {"problem": None, "tournament_protocol": "problem"}


class ProtocolNotFrozenError(RuntimeError):
    """Raised by the runner when the gate refuses a formal run."""


@dataclass
class GateResult:
    allowed: bool
    reasons: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {"allowed": self.allowed, "reasons": self.reasons}


def _load_json_object(path: Path, label: str, reasons: List[str]) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            value = json.load(fh)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        reasons.append(f"cannot read {label}: {exc}")
        return None
    if not isinstance(value, dict):
        reasons.append(f"{label} JSON root is not an object")
        return None
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inside(root: Path, relative: str, reasons: List[str]) -> Optional[Path]:
    try:
        target = (root / relative).resolve()
        target.relative_to(root)
    except (OSError, ValueError):
        reasons.append(f"frozen path escapes workspace: {relative!r}")
        return None
    return target


def _verify_freeze(root: Path, stage: str, active: Optional[Set[str]] = None) -> List[str]:
    """Verify a workflow freeze manifest, including its dependency and file hashes."""
    reasons: List[str] = []
    active = set() if active is None else active
    if stage in active:
        return [f"freeze dependency cycle at {stage}"]
    active.add(stage)

    freeze_path = root / FREEZE_DIR / f"{stage}.json"
    if not freeze_path.is_file():
        active.remove(stage)
        return [f"missing freeze artifact {freeze_path.relative_to(root).as_posix()}"]

    manifest = _load_json_object(freeze_path, f"freeze artifact {stage}", reasons)
    if manifest is None:
        active.remove(stage)
        return reasons
    if manifest.get("status") != PASS_STATUS or manifest.get("stage") != stage:
        reasons.append(f"freeze artifact {stage} metadata is not PASS/consistent")

    expected_dependency = FREEZE_DEPENDENCIES.get(stage)
    dependencies = manifest.get("dependencies")
    if expected_dependency is None:
        if dependencies not in ([], None):
            reasons.append(f"freeze artifact {stage} has unexpected dependencies")
    elif not isinstance(dependencies, list) or len(dependencies) != 1:
        reasons.append(f"freeze artifact {stage} must bind dependency {expected_dependency}")
    else:
        dependency = dependencies[0]
        dependency_path = root / FREEZE_DIR / f"{expected_dependency}.json"
        if not dependency_path.is_file():
            reasons.append(f"dependent freeze missing: {expected_dependency}")
        elif not isinstance(dependency, dict) or dependency.get("stage") != expected_dependency:
            reasons.append(f"freeze artifact {stage} dependency metadata is invalid")
        elif _sha256(dependency_path) != dependency.get("manifest_sha256"):
            reasons.append(f"freeze artifact {stage} dependency changed: {expected_dependency}")
        else:
            reasons.extend(
                f"upstream {expected_dependency}: {reason}"
                for reason in _verify_freeze(root, expected_dependency, active)
            )

    entries = manifest.get("files")
    frozen_paths: Set[str] = set()
    if not isinstance(entries, list) or not entries:
        reasons.append(f"freeze artifact {stage} contains no files")
    else:
        for entry in entries:
            if not isinstance(entry, dict):
                reasons.append(f"freeze artifact {stage} has invalid file entry")
                continue
            relative = entry.get("path")
            if not isinstance(relative, str) or not relative:
                reasons.append(f"freeze artifact {stage} has entry without path")
                continue
            if relative in frozen_paths:
                reasons.append(f"freeze artifact {stage} duplicates {relative}")
            frozen_paths.add(relative)
            target = _inside(root, relative, reasons)
            if target is None:
                continue
            if not target.is_file():
                reasons.append(f"frozen file missing: {relative}")
                continue
            if _sha256(target) != entry.get("sha256"):
                reasons.append(f"frozen file changed: {relative}")
            if target.stat().st_size != entry.get("size"):
                reasons.append(f"frozen file size changed: {relative}")

    if stage == FREEZE_STAGE and PROTOCOL_PATH.as_posix() not in frozen_paths:
        reasons.append(f"freeze artifact {stage} does not bind {PROTOCOL_PATH.as_posix()}")

    active.remove(stage)
    return reasons


def check_frozen(workspace: str = ".") -> GateResult:
    """Allow only a PASS protocol with a fully verified workflow freeze."""
    root = Path(workspace).resolve()
    reasons: List[str] = []

    protocol_path = root / PROTOCOL_PATH
    if not protocol_path.is_file():
        return GateResult(False, [f"missing protocol {PROTOCOL_PATH.as_posix()}"])

    protocol = _load_json_object(protocol_path, "protocol", reasons)
    if protocol is None:
        return GateResult(False, reasons)

    status = protocol.get("status")
    if status != PASS_STATUS:
        reasons.append(f"protocol status is {status!r}, expected {PASS_STATUS!r}")

    problems = protocol.get("problems")
    if not isinstance(problems, list) or not problems:
        reasons.append("protocol 'problems' is empty or missing")

    reasons.extend(_verify_freeze(root, FREEZE_STAGE))
    return GateResult(len(reasons) == 0, reasons)

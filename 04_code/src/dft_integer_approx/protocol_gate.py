"""Fail-closed protocol gate: refuse formal runs until the protocol is frozen.

The frozen-status token ``FROZEN`` and the freeze artifact path are defined by
the modeling proposal ``00_admin/proposals/modeling/TOURNAMENT_PROTOCOL_FREEZE_PACKET.md``
(``status`` is ``FROZEN`` when frozen) and by the ``verify-freeze`` stage that
requires ``00_admin/freezes/tournament_protocol.json`` (see the prior compute
handoff).  The gate checks only the known preconditions; it does not invent the
schema of the not-yet-frozen ``problems`` entries.  Every missing precondition is
reported and the gate refuses unless all hold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

FROZEN_STATUS = "FROZEN"
PROTOCOL_PATH = Path("03_model/tournament_protocol.json")
FREEZE_ARTIFACT = Path("00_admin/freezes/tournament_protocol.json")


class ProtocolNotFrozenError(RuntimeError):
    """Raised by the runner when the gate refuses a formal run."""


@dataclass
class GateResult:
    allowed: bool
    reasons: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {"allowed": self.allowed, "reasons": self.reasons}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def check_frozen(workspace: str = ".") -> GateResult:
    """Return ``GateResult(allowed=True)`` only when every freeze precondition holds."""
    root = Path(workspace)
    reasons: List[str] = []

    protocol_path = root / PROTOCOL_PATH
    if not protocol_path.exists():
        return GateResult(False, [f"missing protocol {PROTOCOL_PATH}"])

    protocol = _load_json(protocol_path)

    status = protocol.get("status")
    if status != FROZEN_STATUS:
        reasons.append(f"protocol status is {status!r}, expected {FROZEN_STATUS!r}")

    problems = protocol.get("problems")
    if not isinstance(problems, list) or not problems:
        reasons.append("protocol 'problems' is empty or missing")

    freeze_path = root / FREEZE_ARTIFACT
    if not freeze_path.exists():
        reasons.append(f"missing freeze artifact {FREEZE_ARTIFACT}")
    else:
        frozen = _load_json(freeze_path)
        if frozen.get("status") != FROZEN_STATUS:
            reasons.append("freeze artifact status is not FROZEN")
        # Hash consistency between protocol and freeze artifact is validated by
        # the integrator's verify-freeze stage; here we only require both exist.

    return GateResult(len(reasons) == 0, reasons)

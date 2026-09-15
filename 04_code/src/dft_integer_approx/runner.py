# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: no candidate is invoked unless the frozen protocol gate passes.
"""Gate-first runner: the single choke point before any candidate executes.

Before the protocol is frozen the only legal executions are unit tests and the
fail-closed gate itself.  This module enforces that invariant: no candidate (real
or fake) runs for a formal result while the gate refuses.
"""

from __future__ import annotations

from typing import Optional

from .candidate_api import Candidate, CandidateContext, CandidateOutput
from .protocol_gate import ProtocolNotFrozenError, check_frozen


def run_candidate(candidate: Candidate, context: CandidateContext,
                  workspace: str = ".") -> CandidateOutput:
    """Run a candidate only after the protocol gate passes.

    Raises :class:`ProtocolNotFrozenError` (fail closed) while the gate refuses,
    instead of degrading to a non-formal run.
    """
    gate = check_frozen(workspace)
    if not gate.allowed:
        raise ProtocolNotFrozenError(
            "protocol not frozen; refusing to run candidate: " + "; ".join(gate.reasons)
        )
    return candidate.solve(context)

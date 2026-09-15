#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: formal execution remains gate-first and retains every failure.
"""Tournament entrypoint; refuses until the protocol is frozen.

Post-freeze this maps the real candidates and runs L0-L4; it is intentionally not
implemented while the gate is still refusing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402


def main() -> int:
    gate = check_frozen(".")
    print("run_tournament: gate allowed =", gate.allowed)
    for reason in gate.reasons:
        print("  -", reason)
    if not gate.allowed:
        print("Refusing to run the tournament (protocol not frozen).")
        return 1
    print("Not implemented: candidate mapping and execution happen only after freeze.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

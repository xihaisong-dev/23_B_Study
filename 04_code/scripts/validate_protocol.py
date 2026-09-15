#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: the protocol and recursive freeze bindings are verified before execution.
"""Fail-closed CLI over the protocol gate: exit 0 only when the protocol is frozen."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402


def main() -> int:
    result = check_frozen(".")
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    if result.allowed:
        print("PROTOCOL PASS + FREEZE VERIFIED: formal runs are permitted.")
        return 0
    print("PROTOCOL/FREEZE NOT VERIFIED: formal runs refused (fail-closed).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

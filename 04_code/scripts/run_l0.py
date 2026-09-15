#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: machine-readable L0 evidence is reviewed before formal baselines.
"""Run L0 checks without executing candidates."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.l0_validation import run_l0_checks  # noqa: E402
from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402


def main() -> int:
    gate = check_frozen(".")
    if not gate.allowed:
        print(json.dumps(gate.as_dict(), ensure_ascii=False, indent=2))
        return 1
    result = run_l0_checks(Path(".").resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

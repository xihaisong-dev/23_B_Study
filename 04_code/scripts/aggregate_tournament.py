# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: strict batch-bijection and frozen-protocol review are mandatory.
"""Strictly aggregate one already-completed formal L2 batch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
SRC = WORKSPACE / "04_code/src"
sys.path.insert(0, str(SRC))

from dft_integer_approx.aggregation import aggregate_formal_batch  # noqa: E402
from dft_integer_approx.formal_tournament_runner import assert_gate_ready  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    assert_gate_ready(WORKSPACE)
    result = aggregate_formal_batch(WORKSPACE, args.batch_id,
                                    write=not args.check_only)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

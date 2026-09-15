#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: this milestone runs only frozen deterministic baselines and never selects a winner.
"""Execute all L0/L1 deterministic baselines registered in the frozen protocol."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.formal_baseline_runner import run_all  # noqa: E402


def main() -> int:
    command = "python -X utf8 04_code/scripts/run_baselines.py"
    result = run_all(Path("."), command)
    counts = {}
    for run in result["runs"]:
        counts[run["status"]] = counts.get(run["status"], 0) + 1
    print(json.dumps({"l0": result["l0"]["status"], "runs": len(result["runs"]), "status_counts": counts}, ensure_ascii=False, indent=2))
    return 0 if result["l0"]["status"] == "PASS" and all(run["status"] in {"PASS", "INFEASIBLE"} for run in result["runs"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

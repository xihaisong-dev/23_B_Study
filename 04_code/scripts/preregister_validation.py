#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: this writes configs only; every validation status remains NOT_RUN.
"""Persist executable L3/L4 parent/variant configs without running them."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.formal_baseline_runner import _atomic_json  # noqa: E402
from dft_integer_approx.formal_tournament_runner import _json_sha256  # noqa: E402
from dft_integer_approx.hashing import sha256_file  # noqa: E402
from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402
from dft_integer_approx.validation_runs import build_validation_plan  # noqa: E402


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    gate = check_frozen(str(workspace))
    if not gate.allowed:
        print("protocol/freeze gate failed:", "; ".join(gate.reasons))
        return 1
    protocol = json.loads((workspace / "03_model/tournament_protocol.json").read_text(encoding="utf-8"))
    l3 = build_validation_plan(protocol, "L3", smoke=False)
    l4 = build_validation_plan(protocol, "L4", smoke=False)
    registry = {"schema_version": "3.0", "status": "BLOCKED",
                "execution_status": "NOT_RUN",
                "parent_requirement": "complete frozen L2 batch run ids",
                "L3": {"status": "NOT_RUN", "config_count": len(l3),
                       "config_sha256": _json_sha256(l3), "configs": l3,
                       "summary": ["best", "median", "worst"]},
                "L4": {"status": "NOT_RUN", "config_count": len(l4),
                       "config_sha256": _json_sha256(l4), "configs": l4},
                "command": "python 04_code/scripts/run_tournament.py --execute-full --level <L3|L4> --resume"}
    path = workspace / "05_results/validation_registry.json"
    _atomic_json(path, registry)
    validation_path = workspace / "05_results/validation_plan.json"
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["registry"] = {"path": "05_results/validation_registry.json",
                                  "sha256": sha256_file(path),
                                  "status": "NOT_RUN"}
        _atomic_json(validation_path, validation)
    print(json.dumps({"status": "BLOCKED", "L3": len(l3), "L4": len(l4)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

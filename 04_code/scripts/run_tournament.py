#!/usr/bin/env python3
# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: formal execution remains gate-first and retains every failure.
"""Unified dry-run, smoke, filtered, and full frozen-tournament entrypoint."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.formal_tournament_runner import build_plan, run_plan  # noqa: E402
from dft_integer_approx.protocol_gate import check_frozen  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", choices=("L2", "L3", "L4"), default="L2")
    parser.add_argument("--problem", action="append", dest="problems")
    parser.add_argument("--candidate", action="append", dest="candidates")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--execute-full", action="store_true")
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[2]
    gate = check_frozen(str(workspace))
    print("run_tournament: gate allowed =", gate.allowed)
    for reason in gate.reasons:
        print("  -", reason)
    if not gate.allowed:
        print("Refusing to run the tournament (protocol not frozen).")
        return 1
    if args.level != "L2":
        print(f"{args.level} execution is framework-only until formal L2 completes.")
        return 1
    protocol = json.loads((workspace / "03_model/tournament_protocol.json").read_text(encoding="utf-8"))
    plan = build_plan(protocol, smoke=args.smoke, problems=args.problems,
                      candidates=args.candidates)
    if args.dry_run:
        print(json.dumps({"schema_version": "3.0", "level": args.level,
                          "mode": "dry-run", "run_count": len(plan),
                          "plan": plan}, ensure_ascii=False, indent=2))
        return 0
    command = " ".join(sys.argv)
    summary = run_plan(workspace, plan, command=command, smoke=args.smoke)
    print(json.dumps({"status": summary["status"], "phase_status": summary["phase_status"],
                      "run_count": summary["run_count"],
                      "status_counts": summary["status_counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

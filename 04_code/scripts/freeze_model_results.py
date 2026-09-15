# AI-assisted development disclosure (D-011)
# Tool/model: DeepSeek Harness, deepseek-v4-flash
# Developer/provider: DeepSeek
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification required: hashes are computed from the working tree; the integrator
# must re-run this after any further edit and review the resulting diff.
"""Freeze the model-results stage: write ``00_admin/freezes/model_results.json``.

Why this file is written by a script
------------------------------------
``workflow_guard.verify_freeze`` binds a stage to the SHA-256 and byte size of named
files and to the SHA-256 of the upstream freeze manifest, and ``check_model_results``
additionally requires the freeze to name five specific artefacts plus at least one
``04_code/`` file.  Hand-writing that manifest is error prone and silently goes stale;
generating it from the tree keeps the hashes honest.

Ordering matters: this must run **after** the aggregates are final, because regenerating
``05_results/metrics.json`` or ``tournament.json`` changes their hashes and invalidates
the freeze.
"""

from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

FREEZE = Path("00_admin/freezes/model_results.json")
UPSTREAM = Path("00_admin/freezes/tournament_protocol.json")

# required by check_model_results
REQUIRED = [
    "03_model/ANALYSIS_MODELING_REPORT.md",
    "03_model/tournament_protocol.json",
    "05_results/metrics.json",
    "05_results/tournament.json",
    "05_results/RESULTS_REPORT.md",
]
# named evidence beyond the required five
EXTRA = [
    "05_results/challenger_runs.json",
    "05_results/l3_robustness.json",
    "05_results/l4_ablation.json",
    "00_admin/freezes/tournament_protocol.json",
    "04_code/src/dft_integer_approx/aggregate_results.py",
    "04_code/src/dft_integer_approx/robustness_ablation.py",
    "04_code/src/dft_integer_approx/challengers.py",
    "04_code/src/dft_integer_approx/challenger_core.py",
    "04_code/src/dft_integer_approx/formal_challenger_runner.py",
    "04_code/scripts/run_challengers.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = Path(".").resolve()
    if not UPSTREAM.is_file():
        raise SystemExit(f"upstream freeze missing: {UPSTREAM}")
    upstream_sha = sha256(root / UPSTREAM)

    entries: List[dict] = []
    missing: List[str] = []
    for rel in REQUIRED + EXTRA:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        entries.append({"path": rel, "sha256": sha256(path), "size": path.stat().st_size})
    if missing:
        raise SystemExit(f"cannot freeze, missing files: {missing}")

    manifest = {
        "schema_version": "3.0",
        "stage": "model_results",
        "status": "PASS",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "actor": "compute-agent",
        "change_request": None,
        "dependencies": [{"stage": "tournament_protocol", "manifest_sha256": upstream_sha}],
        "files": entries,
    }
    out = root / FREEZE
    # newline="\n" is required: .gitattributes declares *.json text eol=lf, so the committed
    # blob is LF and a fresh checkout writes LF.  Writing CRLF here would make the manifest's
    # own bytes (recorded as a dependency hash by the downstream paper freeze) differ between
    # this working tree and a fresh clone.
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"wrote {FREEZE.as_posix()} with {len(entries)} file bindings")
    for e in entries:
        print(f"  {e['path']}  {e['size']:>9} bytes  {e['sha256'][:16]}...")
    print(f"  dependency tournament_protocol  {upstream_sha[:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

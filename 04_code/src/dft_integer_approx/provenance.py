"""Run identifiers, environment summary and (minimal) run manifest."""

from __future__ import annotations

import datetime as _dt
import json
import platform
import sys
from typing import Any, Dict, Optional


def utc_now_us() -> str:
    """UTC timestamp in the run-id field format: ``YYYYMMDDTHHMMSSffffffZ``."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f") + "Z"


def generate_run_id(problem_id: str, candidate_id: str, seed: int,
                    protocol_sha8: str, code_sha8: str,
                    now_us: Optional[str] = None) -> str:
    """Run id per ``04_code/IMPLEMENTATION_PLAN.md`` section 4.2."""
    now_us = now_us or utc_now_us()
    for component in (problem_id, candidate_id):
        _assert_safe(component)
    return f"{now_us}__{problem_id}__{candidate_id}__s{seed}__p{protocol_sha8}__c{code_sha8}"


def _assert_safe(s: str) -> None:
    if not s or not all(c.isalnum() or c in "-_." for c in s):
        raise ValueError(f"unsafe identifier component {s!r}")


def environment_summary() -> Dict[str, Any]:
    return {
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def build_run_manifest(run_id: str, problem_id: str, candidate_id: str, seed: int,
                       status: str, formal: bool = False,
                       protocol_sha256: str = "", code_sha256: str = "",
                       artifacts: Optional[Dict[str, str]] = None,
                       environment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Minimal manifest; ``formal`` marks whether this was a frozen-protocol run."""
    return {
        "schema_version": "3.0",
        "run_id": run_id,
        "problem_id": problem_id,
        "candidate_id": candidate_id,
        "seed": seed,
        "status": status,
        "formal": formal,
        "environment": environment or environment_summary(),
        "protocol_sha256": protocol_sha256,
        "code_sha256": code_sha256,
        "artifacts": artifacts or {},
    }


def manifest_to_json(manifest: Dict[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)

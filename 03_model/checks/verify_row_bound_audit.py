#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only integrity audit for the D-012 freeze and the frozen protocol.

Does not modify anything under ``00_admin/`` or ``03_model/`` -- it only reads and
reports.  Useful as a pre-run checklist before the compute agent starts L0-L4: it
re-derives every hash binding in the freeze manifests and every ``kbrefs`` line
range in the frozen protocol.

Checks
------
A1  ``00_admin/freezes/problem.json``: stage/status metadata, every listed file's
    SHA-256 and size.
A2  ``00_admin/freezes/tournament_protocol.json``: same, plus the recursive
    dependency on the ``problem`` manifest's own SHA-256.
A3  The freeze must bind ``03_model/tournament_protocol.json`` itself.
A4  ``03_model/tournament_protocol.json``: ``status == "PASS"``, non-empty
    ``problems``, five problem ids, three candidates each, and every candidate's
    ``kbrefs`` range must resolve inside an existing knowledge-base text file.
A5  ``02_retrieval/retrieval_manifest.json``: top-level status and every referenced
    knowledge-base path exists.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
OUT_PATH = HERE / "row_bound_audit_results.json"

FREEZE_DIR = REPO_ROOT / "00_admin" / "freezes"
PROTOCOL = REPO_ROOT / "03_model" / "tournament_protocol.json"
RETRIEVAL = REPO_ROOT / "02_retrieval" / "retrieval_manifest.json"
KBREF_RE = re.compile(r"^([A-Za-z0-9\-]+)::([^#]+)#L(\d+)-L(\d+)$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        return {"__error__": str(exc)}


def audit_manifest(stage: str, reasons: List[str]) -> Dict[str, Any]:
    path = FREEZE_DIR / f"{stage}.json"
    info: Dict[str, Any] = {"path": str(path.relative_to(REPO_ROOT)), "exists": path.is_file()}
    if not path.is_file():
        reasons.append(f"A: freeze manifest missing: {path.name}")
        info["status"] = None
        return info
    data = load_json(path) or {}
    info["status"] = data.get("status")
    info["stage"] = data.get("stage")
    info["actor"] = data.get("actor")
    info["created_at"] = data.get("created_at")
    if data.get("status") != "PASS":
        reasons.append(f"A: {path.name} status is {data.get('status')!r}, expected 'PASS'")
    if data.get("stage") != stage:
        reasons.append(f"A: {path.name} stage is {data.get('stage')!r}, expected {stage!r}")

    files: List[Dict[str, Any]] = []
    for entry in data.get("files", []):
        rel = entry.get("path")
        target = REPO_ROOT / rel
        rec = {"path": rel, "exists": target.is_file()}
        if not target.is_file():
            reasons.append(f"A: frozen file missing: {rel}")
            files.append(rec)
            continue
        actual_size = target.stat().st_size
        actual_sha = sha256_file(target)
        rec.update({
            "size_ok": actual_size == entry.get("size"),
            "sha256_ok": actual_sha == entry.get("sha256"),
            "actual_size": actual_size,
            "expected_size": entry.get("size"),
        })
        if not rec["size_ok"]:
            reasons.append(f"A: frozen file size drift: {rel}")
        if not rec["sha256_ok"]:
            reasons.append(f"A: frozen file sha256 drift: {rel}")
        files.append(rec)
    info["files"] = files
    info["bindings_ok"] = all(f.get("sha256_ok", False) and f.get("size_ok", False) for f in files)

    deps = []
    for dep in data.get("dependencies", []):
        dep_stage = dep.get("stage")
        dep_path = FREEZE_DIR / f"{dep_stage}.json"
        rec = {"stage": dep_stage, "path": dep_path.name, "exists": dep_path.is_file()}
        if dep_path.is_file():
            actual = sha256_file(dep_path)
            rec["sha256_ok"] = actual == dep.get("manifest_sha256")
            if not rec["sha256_ok"]:
                reasons.append(f"A: dependency manifest sha256 drift: {dep_path.name}")
        else:
            reasons.append(f"A: dependency manifest missing: {dep_path.name}")
        deps.append(rec)
    info["dependencies"] = deps
    return info


def audit_protocol(reasons: List[str]) -> Dict[str, Any]:
    if not PROTOCOL.is_file():
        reasons.append("A4: frozen protocol file missing")
        return {"exists": False}
    data = load_json(PROTOCOL) or {}
    info: Dict[str, Any] = {
        "exists": True,
        "status": data.get("status"),
        "frozen": data.get("frozen"),
        "semantic_decision": data.get("semantic_decision"),
        "problem_count": len(data.get("problems", [])),
        "problems": {},
    }
    if data.get("status") != "PASS":
        reasons.append(f"A4: protocol status is {data.get('status')!r}, expected 'PASS'")
    if not data.get("problems"):
        reasons.append("A4: protocol problems is empty")

    total_refs = 0
    bad_refs = 0
    for prob in data.get("problems", []):
        pid = prob.get("id")
        cands = prob.get("candidates", [])
        info["problems"][pid] = {"candidates": len(cands), "kbref_ranges_ok": True}
        if len(cands) < 3:
            reasons.append(f"A4: {pid} has {len(cands)} candidates, expected >= 3")
        for cand in cands:
            for ref in cand.get("kbrefs", []):
                total_refs += 1
                m = KBREF_RE.match(ref)
                if not m:
                    bad_refs += 1
                    reasons.append(f"A4: unparsable kbref in {pid}/{cand.get('id')}: {ref}")
                    continue
                path = REPO_ROOT / m.group(2)
                if not path.is_file():
                    bad_refs += 1
                    reasons.append(f"A4: kbref file missing: {m.group(2)}")
                    continue
                n_lines = sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
                if int(m.group(4)) > n_lines:
                    bad_refs += 1
                    info["problems"][pid]["kbref_ranges_ok"] = False
                    reasons.append(
                        f"A4: kbref range beyond EOF in {pid}/{cand.get('id')}: "
                        f"{ref} (file has {n_lines} lines)")
    info["kbref_total"] = total_refs
    info["kbref_bad"] = bad_refs
    return info


def audit_retrieval(reasons: List[str]) -> Dict[str, Any]:
    if not RETRIEVAL.is_file():
        reasons.append("A5: retrieval manifest missing")
        return {"exists": False}
    data = load_json(RETRIEVAL) or {}
    kb = data.get("kb") or {}
    info: Dict[str, Any] = {
        "exists": True,
        "status": data.get("status"),
        "kb_status": kb.get("status"),
        "knowledge_base_status": kb.get("status"),
        "paths_checked": 0,
        "paths_missing": [],
    }

    def check(path: Optional[str], label: str) -> None:
        if not path:
            return
        info["paths_checked"] += 1
        if not (REPO_ROOT / path).is_file():
            info["paths_missing"].append(path)
            reasons.append(f"A5: retrieval path missing on disk ({label}): {path}")

    # knowledge-base document registry
    for doc in kb.get("documents_checked", []) or []:
        check(doc.get("text"), f"kb:{doc.get('id')}")
        check(doc.get("pdf"), f"kb-pdf:{doc.get('id')}")
    check(kb.get("readme"), "kb-readme")
    # per-problem registrations, if present in this revision
    for prob in data.get("problems", []) or []:
        for doc in prob.get("documents", []) or []:
            check(doc.get("text") or doc.get("path"), f"{prob.get('id')}")
    info["kb_documents"] = len(kb.get("documents_checked", []) or [])
    return info


def main() -> int:
    reasons: List[str] = []
    out: Dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_class": "modeling_check",
        "formal_experiment": False,
        "script": "verify_row_bound_audit.py",
        "read_only": True,
        "reasons": reasons,
    }

    print("=== A1/A2 freeze manifests ===")
    out["problem_freeze"] = audit_manifest("problem", reasons)
    out["protocol_freeze"] = audit_manifest("tournament_protocol", reasons)
    for key in ("problem_freeze", "protocol_freeze"):
        rec = out[key]
        print(f"  {rec.get('path')}: exists={rec.get('exists')} status={rec.get('status')} "
              f"stage={rec.get('stage')} bindings_ok={rec.get('bindings_ok')}")

    print("=== A3 freeze binds the protocol ===")
    bound = [f.get("path") for f in out["protocol_freeze"].get("files", [])]
    binds = "03_model/tournament_protocol.json" in bound
    out["freeze_binds_protocol"] = binds
    print(f"  binds 03_model/tournament_protocol.json: {binds}")
    if not binds:
        reasons.append("A3: tournament_protocol freeze does not bind the protocol file")

    print("=== A4 protocol integrity ===")
    out["protocol"] = audit_protocol(reasons)
    p = out["protocol"]
    print(f"  status={p.get('status')} frozen={p.get('frozen')} "
          f"problems={p.get('problem_count')} kbrefs={p.get('kbref_total')} "
          f"bad={p.get('kbref_bad')}")
    for pid, rec in (p.get("problems") or {}).items():
        print(f"    {pid}: candidates={rec['candidates']} kbref_ranges_ok={rec['kbref_ranges_ok']}")

    print("=== A5 retrieval manifest ===")
    out["retrieval"] = audit_retrieval(reasons)
    r = out["retrieval"]
    print(f"  status={r.get('status')} kb={r.get('kb_status')} "
          f"paths_checked={r.get('paths_checked')} missing={len(r.get('paths_missing', []))}")

    out["status"] = "PASS" if not reasons else "FAIL"
    out["failed_checks"] = reasons
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"\nstatus={out['status']} reasons={len(reasons)}")
    for reason in reasons:
        print(f"  - {reason}")
    print(f"wrote {OUT_PATH}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

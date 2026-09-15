"""Normalise line endings to LF for the text files that the freezes bind.

Why this is needed
------------------
`.gitattributes` declares ``*.json|*.md|*.py|*.tex text eol=lf``.  Git therefore *stores*
these files with LF and *checks them out* with LF.  Any working-tree copy that currently
holds CRLF is normalised by the clean filter on the way into the index, so it looks clean
in ``git status`` -- but a freeze manifest computed from the raw working-tree bytes records
the CRLF hash.  The guard hashes raw bytes::

    def sha256(path: Path) -> str:
        with path.open("rb") as handle: ...

so on a fresh checkout (equally: after this branch is merged into ``main``, where git
writes the blobs out with LF) the manifest hash no longer matches and ``verify-freeze``
fails.  Converting the working tree to LF *before* freezing makes the recorded hash equal
to the hash of the committed content, so the freeze survives a fresh checkout.

Implementation notes
--------------------
* The conversion is done on **bytes**.  Decoding with ``utf-8-sig`` and re-encoding would
  silently drop a UTF-8 BOM, i.e. change file content beyond line endings.
* ``io.open(..., newline="\\n")`` is **not** sufficient and was a bug in the first draft of
  this script: the ``newline`` argument only suppresses the ``\\n`` -> ``os.linesep``
  translation on write.  It does not remove ``\\r`` characters that are already present in
  the string, so the file was rewritten byte-identically and reported as "normalised".
* A lone ``\\r`` (not part of CRLF) is *reported* but not rewritten: it can be legitimate
  data, and none of the frozen files contain one.

Scope
-----
Only ``.json/.md/.py/.tex`` are touched, matching ``.gitattributes``.  ``.toml`` is
deliberately excluded: it has no ``text eol=lf`` attribute, so its CRLF bytes are stored
verbatim in the blob and are stable across checkouts.

Run before `freeze_model_results.py`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

TEXT_SUFFIXES = {".json", ".md", ".py", ".tex"}
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def normalise(root: Path) -> tuple[list[str], list[str]]:
    """Rewrite CRLF as LF. Returns (changed, lone_cr_skipped)."""
    changed: list[str] = []
    lone_cr: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if SKIP_PARTS & set(path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue

        raw = path.read_bytes()
        if b"\r" not in raw:
            continue

        stripped = raw.count(b"\r") - raw.count(b"\r\n")
        if stripped:
            lone_cr.append(path.relative_to(root).as_posix())
        if b"\r\n" not in raw:
            continue

        new = raw.replace(b"\r\n", b"\n")
        path.write_bytes(new)
        if path.read_bytes() != new:  # pragma: no cover - defensive
            raise RuntimeError(f"write did not stick: {path}")
        changed.append(path.relative_to(root).as_posix())
    return changed, lone_cr


def main() -> int:
    root = Path(".").resolve()
    changed, lone_cr = normalise(root)
    print(f"converted {len(changed)} file(s) from CRLF to LF")
    for rel in changed:
        print("   ", rel)

    if lone_cr:
        print(f"WARNING: {len(lone_cr)} file(s) contain a lone CR and were left unchanged:")
        for rel in lone_cr:
            print("   ", rel)
    else:
        print("no lone-CR files found")

    # Round-trip check: the conversion must be idempotent and must not have changed
    # anything other than line endings.
    again, _ = normalise(root)
    if again:
        print(f"ERROR: {len(again)} file(s) still CRLF after conversion")
        return 1
    print("verified: every text file under .gitattributes is now LF (idempotent)")

    # Report the remaining CRLF text files by suffix for transparency.
    remaining: dict[str, int] = {}
    for path in root.rglob("*"):
        if not path.is_file() or SKIP_PARTS & set(path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES and b"\r\n" in path.read_bytes():
            remaining[path.suffix] = remaining.get(path.suffix, 0) + 1
    print(f"remaining CRLF text files: {remaining or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

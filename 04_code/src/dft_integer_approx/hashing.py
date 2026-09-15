"""SHA-256 helpers for files and bytes."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))

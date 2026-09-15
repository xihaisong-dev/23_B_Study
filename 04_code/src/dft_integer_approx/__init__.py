# AI-assisted development disclosure (D-011)
# Tool/model: OpenAI Codex desktop, GPT-5 family (exact deployment version undisclosed)
# Developer/provider: OpenAI
# Version release date: exact deployed model date undisclosed by host; see 00_admin/AI_USE_LOG.md
# Human verification: all exported functions require tests and independent result checks.
"""Compute-side scaffold for 2023 Huawei Cup problem B.

DFT integer-factorization approximation: pure standard library, no third-party
dependencies.  Matrices are row-major lists of lists of ``complex``.

This package is the *validation / scoring* layer only.  Before the protocol is
frozen it must never run a formal tournament or write ``05_results/``; the
fail-closed gate in :mod:`dft_integer_approx.protocol_gate` enforces that.
"""

from . import constraints, hardware, metrics, targets  # noqa: F401

__version__ = "0.1.0"
__all__ = ["constraints", "hardware", "metrics", "targets", "__version__"]

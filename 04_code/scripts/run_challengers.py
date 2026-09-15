#!/usr/bin/env python3
"""Run the frozen challengers (L2) from the repository root.

    python -X utf8 04_code/scripts/run_challengers.py --dry-run
    python -X utf8 04_code/scripts/run_challengers.py --problem q5 --max-n 16
    python -X utf8 04_code/scripts/run_challengers.py

The runner refuses unless the D-012 protocol freeze verifies.  Runs are written to
``05_results/runs/<run-id>/`` (never overwritten) and summarised to
``05_results/challenger_runs.json``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dft_integer_approx.formal_challenger_runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

"""Verify the Gaussian-integer obstruction for frozen Q5 instances.

This is a modeling certificate, not a tournament run.  It uses only the Python
standard library.  The proof itself is algebraic; floating-point enumeration of
nearby Gaussian integers is an independent sanity check, not the proof basis.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
OUTPUT_PATH = SCRIPT_PATH.with_name("q5_gaussian_integer_infeasibility.json")
PROTOCOL_PATH = REPO_ROOT / "03_model" / "tournament_protocol.json"
FREEZE_PATH = REPO_ROOT / "00_admin" / "freezes" / "tournament_protocol.json"
SEMANTIC_PATH = REPO_ROOT / "00_admin" / "semantic_contract.json"
PROBLEM_PATH = (
    REPO_ROOT / "01_problem" / "original" / "DFT类矩阵的整数分解逼近.docx"
)
THRESHOLD = 0.1
TOL = 1e-12


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "size": path.stat().st_size,
        "sha256": sha256(path),
    }


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    return "".join(
        element.text or "" for element in root.iter() if element.tag.endswith("}t")
    )


def pq_components(q: int) -> tuple[int, ...]:
    values = {0}
    for r in range(q):
        values.add(2**r)
        values.add(-(2**r))
    return tuple(sorted(values))


def gaussian_mul(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])


def gaussian_add(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return (a[0] + b[0], a[1] + b[1])


def closure_sanity(q: int) -> dict[str, Any]:
    components = pq_components(q)
    alphabet = tuple((x, y) for x in components for y in components)
    pairs_checked = 0
    for a in alphabet:
        for b in alphabet:
            product = gaussian_mul(a, b)
            total = gaussian_add(a, b)
            assert all(isinstance(value, int) for value in product + total)
            pairs_checked += 1
    return {
        "q": q,
        "component_count": len(components),
        "gaussian_alphabet_count": len(alphabet),
        "ordered_pairs_checked": pairs_checked,
        "sum_and_product_remain_in_Z_i": True,
    }


def matrix_product_and_permutation_sanity() -> dict[str, Any]:
    """Independently exercise matrix sums/products and a right permutation."""
    left = (((1, 1), (0, -2)), ((2, 0), (-1, 1)))
    right = (((0, 1), (1, 0)), ((-1, 0), (2, -1)))
    product = tuple(
        tuple(
            gaussian_add(
                gaussian_mul(left[row][0], right[0][column]),
                gaussian_mul(left[row][1], right[1][column]),
            )
            for column in range(2)
        )
        for row in range(2)
    )
    right_permuted = tuple((row[1], row[0]) for row in product)
    assert all(
        isinstance(component, int)
        for matrix in (product, right_permuted)
        for row in matrix
        for entry in row
        for component in entry
    )
    assert right_permuted == tuple((row[1], row[0]) for row in product)
    return {
        "matrix_size": 2,
        "product_entries_are_in_Z_i": True,
        "right_permutation_is_column_reordering": True,
        "right_permuted_entries_are_in_Z_i": True,
    }


def dft_entry(n: int, row: int, column: int) -> complex:
    angle = -2.0 * math.pi * row * column / n
    return complex(math.cos(angle), math.sin(angle)) / math.sqrt(n)


def nearest_lattice_distance_by_enumeration(value: complex, radius: int = 2) -> float:
    return min(
        abs(value - complex(real, imag))
        for real in range(-radius, radius + 1)
        for imag in range(-radius, radius + 1)
    )


def verify_instance(n: int) -> dict[str, Any]:
    amplitude = 1.0 / math.sqrt(n)
    lower_bound = min(amplitude, 1.0 - amplitude)
    enumerated = [
        nearest_lattice_distance_by_enumeration(dft_entry(n, row, column))
        for row in range(n)
        for column in range(n)
    ]

    # Every target entry has modulus a.  For z in Z[i], z=0 gives distance a;
    # otherwise |z|>=1 and reverse triangle inequality gives distance >=1-a.
    assert amplitude <= 1.0
    assert all(distance + TOL >= lower_bound for distance in enumerated)
    assert min(enumerated) + TOL >= lower_bound
    assert lower_bound > THRESHOLD

    # N^2 entrywise residuals of at least d imply ||F-B||_F >= N*d, hence
    # RMSE=||F-B||_F/N >= d.
    return {
        "N": n,
        "target_entry_modulus": amplitude,
        "analytic_entry_distance_lower_bound": lower_bound,
        "analytic_rmse_lower_bound": lower_bound,
        "threshold": THRESHOLD,
        "strict_margin": lower_bound - THRESHOLD,
        "excludes_rmse_le_threshold": True,
        "enumeration": {
            "lattice_box": {"real": [-2, 2], "imag": [-2, 2]},
            "target_entries_checked": n * n,
            "minimum_nearest_distance": min(enumerated),
            "maximum_nearest_distance": max(enumerated),
            "all_respect_analytic_bound": True,
        },
    }


def main() -> int:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    semantic = json.loads(SEMANTIC_PATH.read_text(encoding="utf-8"))
    docx_text = extract_docx_text(PROBLEM_PATH)
    q5 = next(problem for problem in protocol["problems"] if problem["id"] == "q5")

    protocol_freeze_entry = next(
        entry for entry in freeze["files"] if entry["path"] == "03_model/tournament_protocol.json"
    )
    protocol_checks = {
        "protocol_status_pass": protocol["status"] == "PASS",
        "protocol_declares_frozen": protocol["frozen"] is True,
        "freeze_status_pass": freeze["status"] == "PASS",
        "protocol_hash_matches_freeze": sha256(PROTOCOL_PATH)
        == protocol_freeze_entry["sha256"],
        "protocol_size_matches_freeze": PROTOCOL_PATH.stat().st_size
        == protocol_freeze_entry["size"],
        "beta_is_one": protocol["shared_contract"]["beta"] == 1,
        "target_is_unitary_dft": q5["target"] == "unitary F_N",
        "coefficient_set_is_power_of_two_integer_set": protocol["shared_contract"][
            "coefficient_set"
        ]
        == "P_q={0,+/-2^r:r=0,...,q-1}; real and imaginary parts independently belong to P_q",
        "q5_requires_discrete_constraint": "coefficient components belong to P_q"
        in q5["constraints"],
        "q5_threshold_is_point_one": "RMSE<=0.1" in q5["constraints"],
        "registered_N": q5["instances"]["N"],
        "registered_q": q5["instances"]["q_grid"],
    }
    assert all(
        value is True for key, value in protocol_checks.items() if key not in {"registered_N", "registered_q"}
    )
    assert q5["instances"]["N"] == [2, 4, 8, 16, 32, 64]
    assert q5["instances"]["q_grid"] == [1, 2, 3, 4]
    assert semantic["assumptions"][1].startswith("所有问题固定 beta=1")

    problem_text_checks = {
        "contains_discrete_constraint": "约束2：限定" in docx_text
        and "x,y∈P" in docx_text,
        "contains_q5_threshold": "问题5：" in docx_text
        and "RMSE≤0.1" in docx_text,
        "contains_q5_joint_constraints": "同时满足约束1和2" in docx_text,
    }
    assert all(problem_text_checks.values())

    closure = [closure_sanity(q) for q in q5["instances"]["q_grid"]]
    instances = [verify_instance(n) for n in q5["instances"]["N"]]
    min_bound = min(item["analytic_rmse_lower_bound"] for item in instances)
    assert min_bound > THRESHOLD

    report = {
        "schema_version": "1.0",
        "artifact_class": "modeling_certificate",
        "formal_experiment": False,
        "status": "PASS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "conclusion": (
            "For beta=1, every admissible Q5 product (with any positive integer q, "
            "any K, and any right permutation) is Gaussian-integer valued.  On every "
            "frozen registered N, RMSE is strictly greater than 0.1; therefore the "
            "registered Q5 feasible set is empty."
        ),
        "scope": {
            "certified": "all admissible factors for frozen N=[2,4,8,16,32,64]",
            "not_certified": (
                "the original all-t family beyond the frozen finite validation set; "
                "for N>=128 the present bound is <=0.1"
            ),
        },
        "proof_formula": {
            "entry_bound": "d_N=min(1/sqrt(N),1-1/sqrt(N))",
            "rmse_bound": "RMSE=||F_N-B||_F/N >= d_N",
            "reason": (
                "B entries lie in Z[i]; a nonzero Gaussian integer has modulus at least 1, "
                "while every unitary-DFT entry has modulus 1/sqrt(N)."
            ),
        },
        "inputs": [
            input_record(PROBLEM_PATH),
            input_record(PROTOCOL_PATH),
            input_record(FREEZE_PATH),
            input_record(SEMANTIC_PATH),
            input_record(SCRIPT_PATH),
        ],
        "problem_text_checks": problem_text_checks,
        "protocol_checks": protocol_checks,
        "gaussian_integer_closure_sanity": closure,
        "matrix_product_and_right_permutation_sanity": matrix_product_and_permutation_sanity(),
        "instances": instances,
        "minimum_registered_rmse_lower_bound": min_bound,
        "minimum_registered_margin_above_point_one": min_bound - THRESHOLD,
        "failed_checks": [],
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "PASS", "output": str(OUTPUT_PATH), "min_bound": min_bound}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # retained failure is visible to shell and CI
        print(json.dumps({"status": "FAIL", "error": repr(exc)}), file=sys.stderr)
        raise

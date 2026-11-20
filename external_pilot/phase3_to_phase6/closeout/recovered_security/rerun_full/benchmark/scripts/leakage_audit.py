#!/usr/bin/env python3
"""
leakage_audit.py — Audit the benchmark split assignment for data leakage.

Checks performed
----------------
A. BASE_PROGRAM_LEAKAGE      — no program_id in both train and test
B. TRANSFORMATION_FAMILY_LEAKAGE — every transformation type in test must
                                   also appear in train
C. CATEGORY_LEAKAGE          — no category appears ONLY in test
D. NEAR_DUPLICATE_CHECK      — pairs with >95% token-overlap (Jaccard on
                               whitespace-split tokens)
E. FILENAME_COLLISION        — no two programs share the same filename

Writes benchmark/splits/leakage_audit_report.json when run standalone.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH  = REPO_ROOT / "benchmark" / "corpus" / "programs_manifest.json"
SPLITS_PATH    = REPO_ROOT / "benchmark" / "splits" / "split_assignment.json"
BASE_PROG_DIR  = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
REPORT_PATH    = REPO_ROOT / "benchmark" / "splits" / "leakage_audit_report.json"

NEAR_DUP_THRESHOLD = 0.95     # Jaccard similarity threshold


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Split source into non-whitespace tokens for overlap calculation."""
    return re.findall(r"\S+", text)


def _jaccard(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Jaccard similarity between two token multisets (as sets for speed)."""
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def _load_source(filename: str) -> str | None:
    """Read source of a program by its filename; return None if missing."""
    path = BASE_PROG_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_base_program_leakage(
    splits: dict[str, list[str]],
) -> tuple[bool, list[str]]:
    """
    Return (leakage_found, issues).
    leakage_found=True means there IS a problem (audit fails).
    """
    train_set = set(splits.get("train", []))
    test_set  = set(splits.get("test",  []))
    overlap   = sorted(train_set & test_set)
    issues    = [f"BASE_PROGRAM_LEAKAGE: '{pid}' in both train and test" for pid in overlap]
    return bool(overlap), issues


def check_transformation_family_leakage(
    splits: dict[str, list[str]],
    preserving_manifest: dict,
    mutation_manifest: dict,
) -> tuple[bool, list[str]]:
    """
    A transformation family must appear in train if it appears in test.

    Because transformations are applied per-program and the split is at the
    BASE-PROGRAM level, every transformation *type* is implicitly available
    for all split subsets.  We check the declared transformation IDs from
    the manifests against the split to confirm coverage.

    Strategy: we derive the set of transformation families applicable to
    each program from the manifests (all transformations apply to all
    programs in the current design), so the check is:
        - if test is non-empty → all transformation types are "in test"
        - all transformation types must also be represented in train
        (they will be, as long as train is non-empty)

    If future manifests declare program-specific transformations, the caller
    can extend this function.
    """
    issues: list[str] = []
    sp_ids = [t["id"] for t in preserving_manifest.get("transformations", [])]
    sc_ids = [t["id"] for t in mutation_manifest.get("mutation_types",   [])]
    all_tx = sp_ids + sc_ids

    train_empty = len(splits.get("train", [])) == 0
    test_empty  = len(splits.get("test",  [])) == 0

    if test_empty:
        return False, []  # nothing to audit

    for tx_id in all_tx:
        if train_empty:
            issues.append(
                f"TRANSFORMATION_FAMILY_LEAKAGE: '{tx_id}' present in test "
                f"but train split is empty"
            )

    return bool(issues), issues


def check_category_leakage(
    programs: list[dict],
    splits: dict[str, list[str]],
) -> tuple[bool, list[str]]:
    """No category should appear ONLY in test (must also appear in train)."""
    pid_to_cat: dict[str, str] = {p["program_id"]: p["category_prefix"] for p in programs}

    train_cats = {pid_to_cat[pid] for pid in splits.get("train", []) if pid in pid_to_cat}
    test_cats  = {pid_to_cat[pid] for pid in splits.get("test",  []) if pid in pid_to_cat}

    test_only = sorted(test_cats - train_cats)
    issues = [
        f"CATEGORY_LEAKAGE: category '{cat}' appears in test but not in train"
        for cat in test_only
    ]
    return bool(test_only), issues


def check_near_duplicates(
    programs: list[dict],
    threshold: float = NEAR_DUP_THRESHOLD,
) -> tuple[int, list[str]]:
    """
    Brute-force O(n²) pairwise Jaccard check across ALL programs.
    Returns (near_dup_count, issues).
    """
    issues: list[str] = []
    sources: dict[str, list[str]] = {}

    for prog in programs:
        src = _load_source(prog["filename"])
        if src is not None:
            sources[prog["program_id"]] = _tokenize(src)

    ids = sorted(sources.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            sim = _jaccard(sources[a], sources[b])
            if sim > threshold:
                issues.append(
                    f"NEAR_DUPLICATE: '{a}' and '{b}' have Jaccard similarity "
                    f"{sim:.4f} (>{threshold})"
                )
    return len(issues), issues


def check_filename_collisions(programs: list[dict]) -> tuple[int, list[str]]:
    """No two programs may share the same filename."""
    seen: dict[str, list[str]] = {}
    for prog in programs:
        fn = prog["filename"]
        seen.setdefault(fn, []).append(prog["program_id"])

    issues = []
    collision_count = 0
    for fn, pids in sorted(seen.items()):
        if len(pids) > 1:
            collision_count += 1
            issues.append(
                f"FILENAME_COLLISION: filename '{fn}' shared by {pids}"
            )
    return collision_count, issues


# ---------------------------------------------------------------------------
# Top-level audit
# ---------------------------------------------------------------------------

def run_audit(
    manifest: dict,
    split_assignment: dict,
    preserving_manifest: dict,
    mutation_manifest: dict,
) -> dict[str, Any]:
    programs: list[dict] = manifest["programs"]
    splits:   dict       = split_assignment["splits"]

    all_issues: list[str] = []

    # A — base program leakage
    bp_leak, bp_issues = check_base_program_leakage(splits)
    all_issues.extend(bp_issues)

    # B — transformation family leakage
    tx_leak, tx_issues = check_transformation_family_leakage(
        splits, preserving_manifest, mutation_manifest
    )
    all_issues.extend(tx_issues)

    # C — category leakage
    cat_leak, cat_issues = check_category_leakage(programs, splits)
    all_issues.extend(cat_issues)

    # D — near duplicates (whole corpus)
    dup_count, dup_issues = check_near_duplicates(programs)
    all_issues.extend(dup_issues)

    # E — filename collisions
    fn_col_count, fn_col_issues = check_filename_collisions(programs)
    all_issues.extend(fn_col_issues)

    audit_passed = not (
        bp_leak or tx_leak or cat_leak or dup_count > 0 or fn_col_count > 0
    )

    return {
        "base_program_leakage":          bp_leak,
        "transformation_family_leakage": tx_leak,
        "category_leakage":              cat_leak,
        "near_duplicate_count":          dup_count,
        "filename_collisions":           fn_col_count,
        "audit_passed":                  audit_passed,
        "issues":                        all_issues,
    }


# ---------------------------------------------------------------------------
# Standalone entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    with open(MANIFEST_PATH)  as fh: manifest  = json.load(fh)
    with open(SPLITS_PATH)    as fh: split_assignment = json.load(fh)

    preserving_mf_path = (
        REPO_ROOT / "benchmark" / "transformations" / "preserving" / "manifest.json"
    )
    mutation_mf_path = (
        REPO_ROOT / "benchmark" / "transformations" / "mutations" / "manifest.json"
    )
    with open(preserving_mf_path) as fh: preserving_manifest = json.load(fh)
    with open(mutation_mf_path)   as fh: mutation_manifest   = json.load(fh)

    report = run_audit(manifest, split_assignment, preserving_manifest, mutation_manifest)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)

    status = "PASSED ✓" if report["audit_passed"] else "FAILED ✗"
    print(f"Leakage audit {status}")
    print(f"  base_program_leakage         : {report['base_program_leakage']}")
    print(f"  transformation_family_leakage: {report['transformation_family_leakage']}")
    print(f"  category_leakage             : {report['category_leakage']}")
    print(f"  near_duplicate_count         : {report['near_duplicate_count']}")
    print(f"  filename_collisions          : {report['filename_collisions']}")
    if report["issues"]:
        print("\nIssues:")
        for issue in report["issues"]:
            print(f"  • {issue}")
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()

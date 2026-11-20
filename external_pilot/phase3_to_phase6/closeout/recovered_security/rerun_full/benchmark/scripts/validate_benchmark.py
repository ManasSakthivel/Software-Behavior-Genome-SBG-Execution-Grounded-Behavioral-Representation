#!/usr/bin/env python3
"""
benchmark/scripts/validate_benchmark.py
=========================================
Validate a generated benchmark dataset.

Checks:
1. All variant files exist
2. All variant files are valid Python
3. pair_id uniqueness
4. Label consistency (SP→EQUIVALENT, SC→CHANGED)
5. No base program appears in both train and test variant sets
6. Class balance per split
7. Writes benchmark/splits/validation_report.json

Usage:
  python3 benchmark/scripts/validate_benchmark.py [--splits train dev val test]
"""
import argparse
import ast
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = REPO_ROOT / "benchmark" / "datasets"
SPLITS_PATH = REPO_ROOT / "benchmark" / "splits" / "split_assignment.json"


def load_pairs(split_name: str) -> list:
    pairs_path = DATASETS_DIR / f"pairs_{split_name}.jsonl"
    if not pairs_path.exists():
        return []
    pairs = []
    with open(pairs_path) as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def validate_split(split_name: str, pairs: list) -> dict:
    issues = []
    pair_ids_seen = set()
    base_ids_in_split = set()

    missing_variant_files = 0
    invalid_python_files = 0
    duplicate_pair_ids = 0
    label_inconsistencies = 0

    sp_count = 0
    sc_count = 0

    for pair in pairs:
        pair_id = pair.get("pair_id", "")
        variant_path = REPO_ROOT / pair.get("variant_path", "")
        transformation_type = pair.get("transformation_type", "")
        semantic_relation = pair.get("semantic_relation", "")

        # Check pair_id uniqueness
        if pair_id in pair_ids_seen:
            duplicate_pair_ids += 1
            issues.append(f"Duplicate pair_id: {pair_id}")
        pair_ids_seen.add(pair_id)

        # Check variant file exists
        if not variant_path.exists():
            missing_variant_files += 1
            issues.append(f"Missing variant file: {variant_path}")
            continue

        # Check valid Python
        try:
            src = variant_path.read_text()
            ast.parse(src)
        except SyntaxError as e:
            invalid_python_files += 1
            issues.append(f"Invalid Python in {variant_path.name}: {e}")

        # Check label consistency
        if transformation_type.startswith("SP-") and semantic_relation != "EQUIVALENT":
            label_inconsistencies += 1
            issues.append(f"SP transformation labeled {semantic_relation} (expected EQUIVALENT): {pair_id}")
        elif transformation_type.startswith("SC-") and semantic_relation != "CHANGED":
            label_inconsistencies += 1
            issues.append(f"SC mutation labeled {semantic_relation} (expected CHANGED): {pair_id}")

        if semantic_relation == "EQUIVALENT":
            sp_count += 1
        else:
            sc_count += 1

        base_ids_in_split.add(pair.get("base_id", ""))

    total = len(pairs)
    balance_ratio = sp_count / sc_count if sc_count > 0 else float("inf")

    return {
        "split": split_name,
        "total_pairs": total,
        "equivalent_pairs": sp_count,
        "changed_pairs": sc_count,
        "balance_ratio_sp_sc": round(balance_ratio, 3),
        "missing_variant_files": missing_variant_files,
        "invalid_python_files": invalid_python_files,
        "duplicate_pair_ids": duplicate_pair_ids,
        "label_inconsistencies": label_inconsistencies,
        "unique_base_programs": len(base_ids_in_split),
        "issues_count": len(issues),
        "issues": issues[:20],  # cap at 20 for readability
        "passed": (missing_variant_files + invalid_python_files + duplicate_pair_ids + label_inconsistencies) == 0,
    }


def check_cross_split_leakage(all_pairs: dict) -> list:
    """Check no base_id appears in both train and test."""
    issues = []
    train_bases = {p["base_id"] for p in all_pairs.get("train", [])}
    test_bases = {p["base_id"] for p in all_pairs.get("test", [])}
    overlap = train_bases & test_bases
    if overlap:
        issues.append(f"Base program leakage train→test: {sorted(overlap)}")
    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate SBG benchmark dataset")
    parser.add_argument("--splits", nargs="+", default=["train", "dev", "val", "test"])
    args = parser.parse_args()

    all_pairs = {}
    split_reports = {}
    overall_passed = True

    for split_name in args.splits:
        pairs = load_pairs(split_name)
        if not pairs:
            print(f"[{split_name}] No pairs file found — skipping")
            continue
        print(f"\n[{split_name}] Validating {len(pairs)} pairs...")
        report = validate_split(split_name, pairs)
        split_reports[split_name] = report
        all_pairs[split_name] = pairs

        print(f"  EQUIVALENT: {report['equivalent_pairs']}")
        print(f"  CHANGED:    {report['changed_pairs']}")
        print(f"  Missing files: {report['missing_variant_files']}")
        print(f"  Invalid Python: {report['invalid_python_files']}")
        print(f"  Label issues: {report['label_inconsistencies']}")
        print(f"  Passed: {'✓' if report['passed'] else '✗'}")

        if not report["passed"]:
            overall_passed = False

    # Cross-split leakage check
    leakage_issues = check_cross_split_leakage(all_pairs)
    if leakage_issues:
        overall_passed = False
        print(f"\nCROSS-SPLIT LEAKAGE: {leakage_issues}")

    report_path = REPO_ROOT / "benchmark" / "splits" / "validation_report.json"
    full_report = {
        "overall_passed": overall_passed,
        "splits": split_reports,
        "cross_split_leakage_issues": leakage_issues,
        "total_pairs": sum(r["total_pairs"] for r in split_reports.values()),
        "total_equivalent": sum(r["equivalent_pairs"] for r in split_reports.values()),
        "total_changed": sum(r["changed_pairs"] for r in split_reports.values()),
    }
    with open(report_path, "w") as f:
        json.dump(full_report, f, indent=2)
    print(f"\nValidation report written to: {report_path}")
    print(f"\nOVERALL: {'PASS ✓' if overall_passed else 'FAIL ✗'}")
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())

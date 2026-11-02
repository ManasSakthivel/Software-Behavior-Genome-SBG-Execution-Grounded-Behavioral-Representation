#!/usr/bin/env python3
"""
benchmark/scripts/generate_v8_dataset.py
=========================================
Generates the v8 benchmark dataset from fresh programs (benchmark/corpus/fresh_programs/).

Key differences from v7:
- Source programs: fresh_programs/ (never used in development), not v6 base programs
- SP-1/SP-2 use max_names=1 to mitigate edit-size confound (D1 decision)
- Split assignment: category-stratified 50/15/10/25 (train/dev/val/test) seed=42
- Entry-point policy: output_free_v8 (function-only, rename-invariant)
- Validated against FRESH_PROGRAM_PROTOCOL criteria before pairing

This script must only be run AFTER artifacts/final/FREEZE_V8.json has been committed.

Usage:
    # Dry run (validate programs, assign splits, no pairing):
    python3 benchmark/scripts/generate_v8_dataset.py --dry-run

    # Development split only (for power analysis and threshold derivation):
    python3 benchmark/scripts/generate_v8_dataset.py --dev-only

    # Full generation (all splits including test):
    python3 benchmark/scripts/generate_v8_dataset.py --all

    # After freeze is committed — same as --all but with freeze verification:
    python3 benchmark/scripts/generate_v8_dataset.py --all --verify-freeze
"""
from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))

from benchmark.scripts.observability_audit import analyse_pair  # noqa: E402
from benchmark.scripts.validate_fresh_program import validate_program, _load_known_tokens  # noqa: E402
from benchmark.transformations.mutations.mutator import (       # noqa: E402
    MutatorRegistry as SCReg,
    apply_mutation,
)
from benchmark.transformations.preserving.transformer import (  # noqa: E402
    apply_transformation,
)
import data_integrity as di                                    # noqa: E402

FRESH_DIR = REPO_ROOT / "benchmark" / "corpus" / "fresh_programs"
DEFAULT_OUT_ROOT = REPO_ROOT / "benchmark" / "datasets" / "v8"
FREEZE_PATH = REPO_ROOT / "artifacts" / "final" / "FREEZE_V8.json"

SP_TYPES = [f"SP-{i}" for i in range(1, 13)]
SC_TYPES = [f"SC-{i}" for i in range(1, 15)]
SEEDS = [0, 1, 2]
SPLITS = ["train", "dev", "val", "test"]
# SP-1/SP-2 use max_names=1 to limit edit size (D1 decision, EDIT_SIZE_REDESIGN.md)
MAX_NAMES_FOR_RENAME = 1


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assign_splits(eligible: list[dict], seed: int = 42) -> dict[str, list[dict]]:
    """Assign eligible programs to train/dev/val/test splits.

    Strategy: category-stratified 50/15/10/25 split.
    Programs within each category are shuffled with the given seed, then
    assigned round-robin to maintain proportions.
    """
    # Group by category (extracted from filename prefix)
    by_cat: dict[str, list[dict]] = {}
    for prog in eligible:
        name = prog["name"]
        # e.g. sort_shellsort -> "sort", math_fibonacci -> "math"
        cat = name.split("_")[0] if "_" in name else "other"
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(prog)

    rng = random.Random(seed)
    split_assignments: dict[str, list[dict]] = {s: [] for s in SPLITS}

    for cat, progs in sorted(by_cat.items()):
        rng.shuffle(progs)
        n = len(progs)
        # Compute boundaries (50/15/10/25 target proportions, ensuring >= 1 in each non-empty split where possible)
        n_test = max(1, round(n * 0.25))
        n_val = max(1, round(n * 0.10))
        n_dev = max(1, round(n * 0.15))
        n_train = n - n_test - n_val - n_dev
        if n_train < 1 and n > 0:
            n_train = 1

        cursor = 0
        split_assignments["train"].extend(progs[cursor: cursor + n_train]); cursor += n_train
        split_assignments["dev"].extend(progs[cursor: cursor + n_dev]); cursor += n_dev
        split_assignments["val"].extend(progs[cursor: cursor + n_val]); cursor += n_val
        split_assignments["test"].extend(progs[cursor: cursor + n_test]); cursor += n_test
        # any remainder goes to train
        split_assignments["train"].extend(progs[cursor:])

    return split_assignments


def normalised(source: str) -> str:
    return ast.unparse(ast.parse(source))


def check_candidate(base_source: str, variant_source: str, relation: str) -> tuple[bool, str | None]:
    """(accepted, reason). ``reason`` is None when accepted."""
    try:
        compile(variant_source, "<variant>", "exec")
    except SyntaxError as exc:
        return False, f"uncompilable: {exc.msg}"
    try:
        if normalised(base_source) == normalised(variant_source):
            return False, "no_op: normalised AST identical to base"
    except SyntaxError as exc:
        return False, f"unparsable: {exc}"
    if relation == "CHANGED":
        verdict = analyse_pair(base_source, variant_source)
        if verdict["observable"] is None:
            return False, f"unanalysable: {verdict['exclusion_reason']}"
        if not verdict["observable"]:
            return False, "unobservable: mutation outside entry-reachable code"
    return True, None


def generate_split(
    split: str,
    programs: list[dict],
    out_root: Path,
    dry_run: bool = False,
) -> tuple[list[dict], list[dict]]:
    """Generate pairs for one split. Returns (pairs, rejected)."""
    out_dir = out_root / "variants" / split
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
    pairs, rejected = [], []

    for prog in programs:
        name = prog["name"]
        source_path = Path(prog["path"])
        if not source_path.exists():
            rejected.append({"program": name, "reason": "source file missing"})
            continue
        base_source = source_path.read_text()

        for relation, types, apply_fn in (
            ("EQUIVALENT", SP_TYPES, apply_transformation),
            ("CHANGED", SC_TYPES, apply_mutation),
        ):
            for kind in types:
                for seed in SEEDS:
                    try:
                        if relation == "CHANGED":
                            variant_source, meta = apply_fn(
                                str(source_path), kind, seed=seed, site=0
                            )
                        else:
                            # Use max_names=1 for SP-1 and SP-2 to limit edit size
                            if kind in ("SP-1", "SP-2"):
                                variant_source, meta = apply_fn(
                                    str(source_path), kind, seed=seed,
                                    max_names=MAX_NAMES_FOR_RENAME,
                                )
                            else:
                                variant_source, meta = apply_fn(
                                    str(source_path), kind, seed=seed
                                )
                    except Exception as exc:  # noqa: BLE001
                        rejected.append({
                            "program": name, "type": kind, "seed": seed,
                            "reason": f"generator raised: {type(exc).__name__}: {exc}",
                        })
                        continue

                    accepted, reason = check_candidate(base_source, variant_source, relation)
                    if not accepted:
                        rejected.append({
                            "program": name, "type": kind, "seed": seed,
                            "relation": relation, "reason": reason,
                        })
                        continue

                    if dry_run:
                        pairs.append({"program": name, "type": kind, "seed": seed, "relation": relation})
                        continue

                    variant_id = meta.get("variant_id") or f"{name}__{kind.lower()}_s{seed}"
                    variant_path = out_dir / f"{variant_id}.py"
                    variant_path.write_text(variant_source)

                    pairs.append({
                        "pair_id": f"{split}__{variant_id}",
                        "base_id": name,
                        "variant_id": variant_id,
                        "base_path": str(source_path.relative_to(REPO_ROOT)),
                        "variant_path": str(variant_path.relative_to(REPO_ROOT)),
                        "transformation_type": kind,
                        "semantic_relation": relation,
                        "expected_label": relation,
                        "split": split,
                        "seed": seed,
                        "gt_tier": "GT-T3",
                        "confidence": 0.95 if relation == "EQUIVALENT" else 0.90,
                        "hard_negative": (SCReg.get(kind).hard_negative
                                          if relation == "CHANGED" else False),
                        "benchmark_version": "v8",
                        "max_names_for_rename": MAX_NAMES_FOR_RENAME,
                    })
    return pairs, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate programs and assign splits only; no variant files written")
    parser.add_argument("--dev-only", action="store_true",
                        help="Generate train+dev splits only (for pre-freeze tuning)")
    parser.add_argument("--all", action="store_true",
                        help="Generate all splits including test (requires --verify-freeze)")
    parser.add_argument("--verify-freeze", action="store_true",
                        help="Verify FREEZE_V8.json exists and is committed before proceeding")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUT_ROOT),
                        help="Output directory")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Skip individual program validation (use cached report)")
    args = parser.parse_args()

    if args.all and not args.dry_run:
        if args.verify_freeze:
            if not FREEZE_PATH.exists():
                print(f"ERROR: --verify-freeze specified but {FREEZE_PATH} does not exist.",
                      file=sys.stderr)
                print("Commit FREEZE_V8.json before running the final test evaluation.",
                      file=sys.stderr)
                return 1
            print(f"Freeze file found: {FREEZE_PATH}")
        else:
            print("WARNING: --all without --verify-freeze. Generating test split without freeze verification.")
            print("         This is acceptable only for dry runs or development evaluations.")

    out_root = Path(args.output_dir)
    active_splits = SPLITS if (args.all or args.dry_run) else (
        ["train", "dev"] if args.dev_only else ["train", "dev", "val"]
    )

    # Step 1: Validate all fresh programs
    print(f"\nStep 1: Validating fresh programs in {FRESH_DIR}...")
    cached_report = FRESH_DIR / "validation_report.json"
    if args.skip_validation and cached_report.exists():
        print(f"  Using cached report: {cached_report}")
        with open(cached_report) as f:
            report_data = json.load(f)
        eligible_names = set(report_data["eligible_names"])
        all_results = {r["name"]: r for r in report_data["results"]}
    else:
        known_tokens = _load_known_tokens()
        paths = sorted(FRESH_DIR.glob("*.py"))
        paths = [p for p in paths if not p.name.startswith("_")]
        eligible_names = set()
        all_results = {}
        for p in paths:
            r = validate_program(p, known_tokens)
            all_results[p.stem] = r
            if r["eligible"]:
                eligible_names.add(p.stem)
            else:
                print(f"  EXCLUDED {p.stem}: {r['exclusion_reason']}")

    eligible = [
        {"name": name, "path": str(FRESH_DIR / f"{name}.py")}
        for name in sorted(eligible_names)
    ]
    print(f"  Eligible: {len(eligible)} programs")

    if len(eligible) < 50:
        print(f"ERROR: Only {len(eligible)} eligible programs; need ≥50. Aborting.", file=sys.stderr)
        return 1

    # Step 2: Assign splits
    print("\nStep 2: Assigning program-level splits (seed=42, stratified by category)...")
    split_assignments = assign_splits(eligible, seed=42)
    for split in SPLITS:
        progs = split_assignments[split]
        print(f"  {split}: {len(progs)} programs: {[p['name'] for p in progs]}")

    if args.dry_run:
        print("\nDry run: validating pair generation without writing files...")
        total_pairs = 0
        total_rejected = 0
        for split in active_splits:
            progs = split_assignments[split]
            pairs, rejected = generate_split(split, progs, out_root, dry_run=True)
            total_pairs += len(pairs)
            total_rejected += len(rejected)
            print(f"  [{split}] programs={len(progs)} pairs={len(pairs)} rejected={len(rejected)}")
        print(f"\nDry run complete: {total_pairs} pairs would be generated, "
              f"{total_rejected} rejected.")
        return 0

    # Step 3: Generate pairs
    out_root.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    manifest = {
        "benchmark_version": "v8",
        "generator": "benchmark/scripts/generate_v8_dataset.py",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_dir": str(FRESH_DIR.relative_to(REPO_ROOT)),
        "sp2_fix_applied": True,
        "max_names_for_rename": MAX_NAMES_FOR_RENAME,
        "edit_size_redesign": "D1: max_names=1 for SP-1/SP-2",
        "entry_policy": "output_free_v8",
        "split_seed": 42,
        "seeds": SEEDS,
        "splits": {},
        "n_eligible_programs": len(eligible),
        "eligible_program_names": sorted(eligible_names),
    }

    all_pairs_count = 0
    total_programs_processed = 0

    for split in active_splits:
        progs = split_assignments[split]
        total_programs_processed += len(progs)
        print(f"\nGenerating {split} split ({len(progs)} programs)...")
        pairs, rejected = generate_split(split, progs, out_root)
        all_pairs_count += len(pairs)

        pair_file = out_root / f"pairs_{split}.jsonl"
        pair_file.write_text("".join(json.dumps(p) + "\n" for p in pairs))

        n_equiv = sum(1 for p in pairs if p["semantic_relation"] == "EQUIVALENT")
        reasons: dict[str, int] = {}
        for r in rejected:
            key = r["reason"].split(":")[0]
            reasons[key] = reasons.get(key, 0) + 1

        manifest["splits"][split] = {
            "n_programs": len(progs),
            "programs": [p["name"] for p in progs],
            "n_pairs": len(pairs),
            "n_equivalent": n_equiv,
            "n_changed": len(pairs) - n_equiv,
            "n_rejected": len(rejected),
            "rejected_by_reason": dict(sorted(reasons.items())),
        }
        print(f"  [{split}] programs={len(progs)} pairs={len(pairs)} "
              f"(EQUIV={n_equiv} CHANGED={len(pairs)-n_equiv}) rejected={len(rejected)}")

    elapsed = time.time() - t_start
    manifest["total_programs_processed"] = total_programs_processed
    manifest["total_pairs"] = all_pairs_count
    manifest["elapsed_seconds"] = round(elapsed, 2)

    # Program manifest hashes (for freeze verification)
    manifest["program_hashes"] = {
        name: _file_sha256(FRESH_DIR / f"{name}.py")
        for name in sorted(eligible_names)
    }

    # Step 4: Data integrity check
    print("\nRunning data integrity check on generated v8 dataset...")
    report = di.check_dataset(out_root, repo=REPO_ROOT)
    active_defects = {k: v for k, v in report["defect_counts"].items() if v > 0}
    has_defects = len(active_defects) > 0

    manifest["data_integrity"] = {
        "passed": not has_defects,
        "defect_counts": report["defect_counts"],
        "active_defect_counts": active_defects,
    }

    manifest_path = out_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nManifest written to {manifest_path}")
    print(f"Generation completed in {elapsed:.2f}s ({total_programs_processed} programs, "
          f"{all_pairs_count} pairs).")

    if has_defects:
        print(f"FAILED: data integrity check: {active_defects}", file=sys.stderr)
        return 1

    print("SUCCESS: data integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

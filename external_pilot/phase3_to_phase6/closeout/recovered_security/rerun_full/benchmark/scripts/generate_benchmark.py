#!/usr/bin/env python3
"""
benchmark/scripts/generate_benchmark.py
=========================================
Generate the full SBG pair dataset from the corpus + transformations.

For each program in each split:
  - Apply all 12 SP transformation types (seeds 0,1,2) → EQUIVALENT pairs
  - Apply all 14 SC mutation types (seeds 0,1,2) → CHANGED pairs
  - Write variant .py files to benchmark/datasets/variants/{split}/
  - Write pair records to benchmark/datasets/pairs_{split}.jsonl

Usage:
  python3 benchmark/scripts/generate_benchmark.py [--dry-run] [--splits train dev val test]
  python3 benchmark/scripts/generate_benchmark.py --dry-run
  python3 benchmark/scripts/generate_benchmark.py --splits test
"""
import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from benchmark.transformations.preserving.transformer import apply_transformation, TransformationRegistry as SPReg
from benchmark.transformations.mutations.mutator import apply_mutation, MutatorRegistry as SCReg

CORPUS_DIR = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
MANIFEST_PATH = REPO_ROOT / "benchmark" / "corpus" / "programs_manifest.json"
SPLITS_PATH = REPO_ROOT / "benchmark" / "splits" / "split_assignment.json"
DATASETS_DIR = REPO_ROOT / "benchmark" / "datasets"

SP_TYPES = [f"SP-{i}" for i in range(1, 13)]
SC_TYPES = [f"SC-{i}" for i in range(1, 15)]
SEEDS = [0, 1, 2]


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def load_splits():
    with open(SPLITS_PATH) as f:
        return json.load(f)


def generate_pairs(split_name: str, program_ids: list, dry_run: bool = False) -> list:
    out_dir = DATASETS_DIR / "variants" / split_name
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    pairs = []
    for prog_id in program_ids:
        src_path = CORPUS_DIR / f"{prog_id}.py"
        if not src_path.exists():
            print(f"  WARNING: {src_path} not found, skipping", file=sys.stderr)
            continue

        # --- Semantics-PRESERVING pairs ---
        for sp_type in SP_TYPES:
            for seed in SEEDS:
                try:
                    new_src, meta = apply_transformation(str(src_path), sp_type, seed=seed)
                except Exception as e:
                    continue
                applied = meta.get("applied", False)
                if not applied and new_src == open(src_path).read():
                    continue  # transformation was a no-op
                variant_id = meta.get("variant_id") or meta.get("base_id", prog_id) + f"__{sp_type.lower()}_s{seed}"
                variant_path = out_dir / f"{variant_id}.py"
                if not dry_run:
                    with open(variant_path, "w") as f:
                        f.write(new_src)
                pair = {
                    "pair_id": f"{split_name}__{variant_id}",
                    "base_id": prog_id,
                    "variant_id": variant_id,
                    "base_path": str(src_path.relative_to(REPO_ROOT)),
                    "variant_path": str(variant_path.relative_to(REPO_ROOT)) if not dry_run else f"benchmark/datasets/variants/{split_name}/{variant_id}.py",
                    "transformation_type": sp_type,
                    "semantic_relation": "EQUIVALENT",
                    "expected_label": "EQUIVALENT",
                    "split": split_name,
                    "seed": seed,
                    "gt_tier": "GT-T3",
                    "confidence": 0.95,
                    "hard_negative": False,
                }
                pairs.append(pair)

        # --- Semantics-CHANGING pairs ---
        for sc_type in SC_TYPES:
            for seed in SEEDS:
                try:
                    new_src, meta = apply_mutation(str(src_path), sc_type, seed=seed, site=0)
                except Exception as e:
                    continue
                if not meta.get("applied", False):
                    continue  # mutation was a no-op
                variant_id = meta["variant_id"]
                variant_path = out_dir / f"{variant_id}.py"
                if not dry_run:
                    with open(variant_path, "w") as f:
                        f.write(new_src)
                pair = {
                    "pair_id": f"{split_name}__{variant_id}",
                    "base_id": prog_id,
                    "variant_id": variant_id,
                    "base_path": str(src_path.relative_to(REPO_ROOT)),
                    "variant_path": str(variant_path.relative_to(REPO_ROOT)) if not dry_run else f"benchmark/datasets/variants/{split_name}/{variant_id}.py",
                    "transformation_type": sc_type,
                    "semantic_relation": "CHANGED",
                    "expected_label": "CHANGED",
                    "split": split_name,
                    "seed": seed,
                    "gt_tier": "GT-T3",
                    "confidence": 0.90,
                    "hard_negative": SCReg.get(sc_type).hard_negative,
                }
                pairs.append(pair)

    return pairs


def write_pairs(split_name: str, pairs: list):
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATASETS_DIR / f"pairs_{split_name}.jsonl"
    with open(out_path, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate SBG benchmark pairs")
    parser.add_argument("--dry-run", action="store_true", help="Count pairs without writing files")
    parser.add_argument("--splits", nargs="+", default=["train", "dev", "val", "test"],
                        help="Which splits to generate (default: all)")
    args = parser.parse_args()

    split_data = load_splits()
    splits = split_data["splits"]

    total_pairs = 0
    total_sp = 0
    total_sc = 0

    for split_name in args.splits:
        if split_name not in splits:
            print(f"WARNING: split '{split_name}' not in split_assignment.json", file=sys.stderr)
            continue
        program_ids = splits[split_name]
        print(f"\n[{split_name}] Generating pairs for {len(program_ids)} programs...")
        pairs = generate_pairs(split_name, program_ids, dry_run=args.dry_run)
        sp_pairs = [p for p in pairs if p["semantic_relation"] == "EQUIVALENT"]
        sc_pairs = [p for p in pairs if p["semantic_relation"] == "CHANGED"]
        print(f"  SP (EQUIVALENT): {len(sp_pairs)}")
        print(f"  SC (CHANGED):    {len(sc_pairs)}")
        print(f"  Total:           {len(pairs)}")
        total_sp += len(sp_pairs)
        total_sc += len(sc_pairs)
        total_pairs += len(pairs)
        if not args.dry_run:
            out_path = write_pairs(split_name, pairs)
            print(f"  Written to: {out_path}")

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}TOTAL PAIRS GENERATED: {total_pairs}")
    print(f"  EQUIVALENT: {total_sp}")
    print(f"  CHANGED:    {total_sc}")

    # Write summary manifest
    if not args.dry_run:
        summary = {
            "total_pairs": total_pairs,
            "equivalent_pairs": total_sp,
            "changed_pairs": total_sc,
            "splits_generated": args.splits,
        }
        summary_path = DATASETS_DIR / "generation_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary written to: {summary_path}")


if __name__ == "__main__":
    main()

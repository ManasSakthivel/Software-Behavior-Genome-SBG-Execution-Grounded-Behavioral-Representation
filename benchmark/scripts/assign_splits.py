#!/usr/bin/env python3
"""
assign_splits.py — Deterministically assign the 60 base programs to
train/dev/val/test splits, stratified by category_prefix.

Ratios  : 50% train | 15% dev | 15% val | 20% test
Seed    : 42
Guarantee: every category with < 5 programs gets at least 1 in test.

Output  : benchmark/splits/split_assignment.json
"""

from __future__ import annotations

import json
import math
import os
import random
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "benchmark" / "corpus" / "programs_manifest.json"
SPLITS_DIR = REPO_ROOT / "benchmark" / "splits"
OUTPUT_PATH = SPLITS_DIR / "split_assignment.json"

# ---------------------------------------------------------------------------
# Split ratios  (must sum to 1.0)
# ---------------------------------------------------------------------------
SPLIT_RATIOS: dict[str, float] = {
    "train": 0.50,
    "dev":   0.15,
    "val":   0.15,
    "test":  0.20,
}
SEED = 42
SMALL_CATEGORY_THRESHOLD = 5   # categories with fewer programs need special care


def assign_splits(
    programs: list[dict],
    *,
    seed: int = SEED,
    ratios: dict[str, float] | None = None,
    small_threshold: int = SMALL_CATEGORY_THRESHOLD,
) -> dict[str, list[str]]:
    """Return {'train': [...], 'dev': [...], 'val': [...], 'test': [...]}."""
    if ratios is None:
        ratios = SPLIT_RATIOS

    rng = random.Random(seed)

    # Group programs by category_prefix
    by_prefix: dict[str, list[str]] = defaultdict(list)
    for prog in programs:
        by_prefix[prog["category_prefix"]].append(prog["program_id"])

    splits: dict[str, list[str]] = {s: [] for s in ratios}

    for prefix, ids in sorted(by_prefix.items()):          # sorted → deterministic
        shuffled = ids[:]
        rng.shuffle(shuffled)
        n = len(shuffled)

        if n < small_threshold:
            # Guarantee ≥1 in test; distribute remainder as best as possible
            test_ids = shuffled[:1]
            rest = shuffled[1:]
            r = len(rest)
            # Proportional fill for the remaining split slots
            train_n = max(1, round(r * ratios["train"] / (1 - ratios["test"])))
            dev_n   = max(0, round(r * ratios["dev"]   / (1 - ratios["test"])))
            val_n   = r - train_n - dev_n
            if val_n < 0:
                # rebalance
                dev_n += val_n
                val_n = 0

            splits["test"]  += test_ids
            splits["train"] += rest[:train_n]
            splits["dev"]   += rest[train_n:train_n + dev_n]
            splits["val"]   += rest[train_n + dev_n:]
        else:
            # Standard stratified split
            test_n  = max(1, round(n * ratios["test"]))
            dev_n   = max(1, round(n * ratios["dev"]))
            val_n   = max(1, round(n * ratios["val"]))
            train_n = n - test_n - dev_n - val_n
            if train_n < 1:
                # donate excess from largest slice
                test_n -= (1 - train_n)
                train_n = 1

            ptr = 0
            splits["train"] += shuffled[ptr: ptr + train_n];  ptr += train_n
            splits["dev"]   += shuffled[ptr: ptr + dev_n];    ptr += dev_n
            splits["val"]   += shuffled[ptr: ptr + val_n];    ptr += val_n
            splits["test"]  += shuffled[ptr: ptr + test_n]

    return splits


def build_category_split_counts(
    programs: list[dict],
    splits: dict[str, list[str]],
) -> dict[str, dict[str, int]]:
    """Per-category breakdown: {category_prefix: {split: count}}."""
    pid_to_prefix = {p["program_id"]: p["category_prefix"] for p in programs}
    result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for split_name, ids in splits.items():
        for pid in ids:
            prefix = pid_to_prefix.get(pid, "unknown")
            result[prefix][split_name] += 1
    return {k: dict(v) for k, v in sorted(result.items())}


def main() -> None:
    with open(MANIFEST_PATH) as fh:
        manifest = json.load(fh)

    programs: list[dict] = manifest["programs"]

    splits = assign_splits(programs)

    split_counts = {s: len(ids) for s, ids in splits.items()}
    category_split_counts = build_category_split_counts(programs, splits)

    output = {
        "seed": SEED,
        "method": "stratified_by_category",
        "splits": splits,
        "split_counts": split_counts,
        "category_split_counts": category_split_counts,
    }

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"Split assignment written to {OUTPUT_PATH}")
    total = sum(split_counts.values())
    for split_name, count in split_counts.items():
        pct = count / total * 100
        print(f"  {split_name:6s}: {count:3d} ({pct:.1f}%)")


if __name__ == "__main__":
    main()

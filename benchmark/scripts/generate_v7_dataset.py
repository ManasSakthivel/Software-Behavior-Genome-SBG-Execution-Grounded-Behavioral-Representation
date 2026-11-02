#!/usr/bin/env python3
"""
benchmark/scripts/generate_v7_dataset.py
========================================
Generates the v7 benchmark dataset with the repaired SP-2 transformation operator
(attribute reference renaming fix) into ``benchmark/datasets/v7/``.

Features:
- Reads all base programs and split assignments from ``benchmark/datasets/v6/``
  (serving as the source of truth for base programs and program-to-split assignments)
- Re-applies all semantics-preserving (SP-1 .. SP-12) and semantic-changing (SC-1 .. SC-14)
  transformations across seeds [0, 1, 2]
- Validates each candidate variant:
    * compiles without SyntaxError
    * differs from normalized base AST (not a no-op)
    * is observable from entry points for CHANGED relations (SC mutations)
- Writes variants to ``benchmark/datasets/v7/variants/<split>/``
- Writes JSONL pair files ``benchmark/datasets/v7/pairs_<split>.jsonl``
- Runs data integrity verification (``experiments/final/data_integrity.py --strict``)
- Records dataset manifest at ``benchmark/datasets/v7/manifest.json``

Usage:
    # Smoke test on 2-3 representative programs (default):
    python3 benchmark/scripts/generate_v7_dataset.py --smoke-test

    # Full generation for all 60 programs:
    python3 benchmark/scripts/generate_v7_dataset.py --all
"""
from __future__ import annotations

import argparse
import ast
import datetime
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))

from benchmark.scripts.observability_audit import analyse_pair  # noqa: E402
from benchmark.transformations.mutations.mutator import (       # noqa: E402
    MutatorRegistry as SCReg,
    apply_mutation,
)
from benchmark.transformations.preserving.transformer import (  # noqa: E402
    apply_transformation,
)
import data_integrity as di                                    # noqa: E402

V6_ROOT = REPO_ROOT / "benchmark" / "datasets" / "v6"
DEFAULT_OUT_ROOT = REPO_ROOT / "benchmark" / "datasets" / "v7"

SP_TYPES = [f"SP-{i}" for i in range(1, 13)]
SC_TYPES = [f"SC-{i}" for i in range(1, 15)]
SEEDS = [0, 1, 2]
SPLITS = ["train", "dev", "val", "test"]

# Representative programs for smoke testing (covers train, dev, and test splits with class-based code)
SMOKE_TEST_PROGRAMS = ["api_rest_crud_mock", "api_event_bus", "api_rate_limiter"]


def load_programs_from_v6(v6_dir: Path) -> dict[str, list[dict]]:
    """Extract program ids and base paths by split from v6 dataset pairs files."""
    split_programs: dict[str, list[dict]] = {s: [] for s in SPLITS}
    for split in SPLITS:
        pair_file = v6_dir / f"pairs_{split}.jsonl"
        if not pair_file.exists():
            continue
        seen = set()
        for line in pair_file.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            base_id = row["base_id"]
            if base_id not in seen:
                seen.add(base_id)
                split_programs[split].append({
                    "base_id": base_id,
                    "base_path": row["base_path"],
                })
    return split_programs


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
    repo_root: Path = REPO_ROOT,
) -> tuple[list[dict], list[dict]]:
    out_dir = out_root / "variants" / split
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs, rejected = [], []

    for prog_info in programs:
        base_id = prog_info["base_id"]
        source_path = repo_root / prog_info["base_path"]
        if not source_path.exists():
            rejected.append({"program": base_id, "reason": "source file missing"})
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
                            variant_source, meta = apply_fn(str(source_path), kind, seed=seed, site=0)
                        else:
                            variant_source, meta = apply_fn(str(source_path), kind, seed=seed)
                    except Exception as exc:  # noqa: BLE001
                        rejected.append({
                            "program": base_id,
                            "type": kind,
                            "seed": seed,
                            "reason": f"generator raised: {type(exc).__name__}: {exc}",
                        })
                        continue

                    accepted, reason = check_candidate(base_source, variant_source, relation)
                    if not accepted:
                        rejected.append({
                            "program": base_id,
                            "type": kind,
                            "seed": seed,
                            "relation": relation,
                            "reason": reason,
                        })
                        continue

                    variant_id = meta.get("variant_id") or f"{base_id}__{kind.lower()}_s{seed}"
                    variant_path = out_dir / f"{variant_id}.py"
                    variant_path.write_text(variant_source)
                    pairs.append({
                        "pair_id": f"{split}__{variant_id}",
                        "base_id": base_id,
                        "variant_id": variant_id,
                        "base_path": str(source_path.relative_to(repo_root)),
                        "variant_path": str(variant_path.relative_to(repo_root)),
                        "transformation_type": kind,
                        "semantic_relation": relation,
                        "expected_label": relation,
                        "split": split,
                        "seed": seed,
                        "gt_tier": "GT-T3",
                        "confidence": 0.95 if relation == "EQUIVALENT" else 0.90,
                        "hard_negative": (SCReg.get(kind).hard_negative if relation == "CHANGED" else False),
                        "benchmark_version": "v7",
                    })
    return pairs, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", default=False,
                        help="Run smoke test on 2-3 representative programs only")
    parser.add_argument("--all", action="store_true", default=False,
                        help="Generate the entire dataset across all 60 programs")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUT_ROOT),
                        help="Output directory for v7 dataset")
    parser.add_argument("--v6-dir", type=str, default=str(V6_ROOT),
                        help="Path to v6 dataset directory")
    parser.add_argument("--programs", nargs="+", default=None,
                        help="Explicit list of program IDs to generate")
    args = parser.parse_args()

    # Default to smoke test unless --all or explicit programs specified
    is_smoke_test = args.smoke_test or (not args.all and args.programs is None)
    out_root = Path(args.output_dir)
    v6_dir = Path(args.v6_dir)

    print(f"Loading program split definitions from {v6_dir}...")
    split_programs = load_programs_from_v6(v6_dir)
    total_progs_in_v6 = sum(len(p) for p in split_programs.values())
    print(f"Found {total_progs_in_v6} base programs across {len(split_programs)} splits in v6.")

    if is_smoke_test and args.programs is None:
        print(f"Running smoke test on representative programs: {SMOKE_TEST_PROGRAMS}")
        selected_programs = set(SMOKE_TEST_PROGRAMS)
        for split in SPLITS:
            split_programs[split] = [p for p in split_programs[split] if p["base_id"] in selected_programs]
    elif args.programs is not None:
        selected_programs = set(args.programs)
        for split in SPLITS:
            split_programs[split] = [p for p in split_programs[split] if p["base_id"] in selected_programs]

    out_root.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    manifest = {
        "benchmark_version": "v7",
        "generator": "benchmark/scripts/generate_v7_dataset.py",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_dataset": str(v6_dir.relative_to(REPO_ROOT) if v6_dir.is_relative_to(REPO_ROOT) else v6_dir),
        "sp2_fix_applied": True,
        "is_smoke_test": is_smoke_test,
        "seeds": SEEDS,
        "splits": {},
    }

    all_pairs_count = 0
    total_programs_processed = 0

    for split in SPLITS:
        progs = split_programs.get(split, [])
        total_programs_processed += len(progs)
        pairs, rejected = generate_split(split, progs, out_root)
        pair_file = out_root / f"pairs_{split}.jsonl"
        pair_file.write_text("".join(json.dumps(p) + "\n" for p in pairs))
        all_pairs_count += len(pairs)

        n_equiv = sum(1 for p in pairs if p["semantic_relation"] == "EQUIVALENT")
        reasons: dict[str, int] = {}
        for r in rejected:
            key = r["reason"].split(":")[0]
            reasons[key] = reasons.get(key, 0) + 1

        manifest["splits"][split] = {
            "n_programs": len(progs),
            "programs": [p["base_id"] for p in progs],
            "n_pairs": len(pairs),
            "n_equivalent": n_equiv,
            "n_changed": len(pairs) - n_equiv,
            "n_rejected": len(rejected),
            "rejected_by_reason": dict(sorted(reasons.items())),
        }
        print(f"[{split}] programs={len(progs)} pairs={len(pairs)} "
              f"(EQUIV={n_equiv} CHANGED={len(pairs) - n_equiv}) "
              f"rejected={len(rejected)}")

    elapsed = time.time() - t_start
    manifest["total_programs"] = total_programs_processed
    manifest["total_pairs"] = all_pairs_count
    manifest["elapsed_seconds"] = round(elapsed, 2)
    estimated_full_runtime_s = round((elapsed / max(1, total_programs_processed)) * total_progs_in_v6, 1)
    manifest["estimated_full_runtime_seconds"] = estimated_full_runtime_s

    print(f"\nGeneration completed in {elapsed:.2f}s ({total_programs_processed} programs).")
    print(f"Estimated full dataset generation runtime (60 programs): ~{estimated_full_runtime_s:.1f}s.")

    # Run data integrity validation
    print("\nRunning data integrity check on generated v7 dataset...")
    report = di.check_dataset(out_root, repo=REPO_ROOT)
    active_defects = {k: v for k, v in report["defect_counts"].items() if v > 0}
    has_defects = len(active_defects) > 0

    manifest["data_integrity"] = {
        "passed": not has_defects,
        "defect_counts": report["defect_counts"],
        "active_defect_counts": active_defects,
        "sp2_dangling_by_split": report.get("sp2_dangling_by_split", {}),
    }

    manifest_path = out_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Manifest written to {manifest_path.relative_to(REPO_ROOT)}")

    if has_defects:
        print(f"FAILED data integrity check: active defects found: {active_defects}", file=sys.stderr)
        return 1

    print(f"SUCCESS: Data integrity check passed with 0 defects (dangling SP-2 references: 0).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
benchmark/scripts/generate_benchmark_v6.py
==========================================
Regenerates the pair benchmark with the corrected transformation operators,
into ``benchmark/datasets/v6/``. The original dataset under
``benchmark/datasets/`` is left untouched so the published result stays
reproducible and the two can be compared.

What changed relative to ``generate_benchmark.py``
--------------------------------------------------
The operators themselves were fixed (see the module docstrings of
``benchmark/transformations/mutations/mutator.py`` and
``.../preserving/transformations/sp3_dead_code_insert.py``). This script adds
three post-conditions that the original generator did not enforce:

  compiles          the variant must pass ``compile()``, not merely
                    ``ast.parse()``. 103 of the original 3 577 variants do not
                    compile; every pair using one was dropped from the
                    evaluation denominator without being counted.

  differs           the variant's normalised AST must differ from the base's.
                    A transformation that silently no-ops produces a pair that
                    is free for every method and tells the benchmark nothing.

  observable (SC)   the mutation must intersect code reachable from the entry
                    function, using ``benchmark/scripts/observability_audit.py``.
                    In the original test split 135 of 336 CHANGED pairs fail
                    this, i.e. 40% of the positive class is mislabelled.

Splits, program assignment and seeds are unchanged, so the program-disjointness
of train/dev/val/test is preserved exactly. Every rejected candidate is written
to the generation report with its reason; nothing is dropped silently.

Usage:
    python3 benchmark/scripts/generate_benchmark_v6.py [--splits test dev ...]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from benchmark.scripts.observability_audit import analyse_pair          # noqa: E402
from benchmark.transformations.mutations.mutator import (               # noqa: E402
    MutatorRegistry as SCReg, apply_mutation,
)
from benchmark.transformations.preserving.transformer import (          # noqa: E402
    apply_transformation,
)

CORPUS_DIR = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
SPLITS_PATH = REPO_ROOT / "benchmark" / "splits" / "split_assignment.json"
OUT_ROOT = REPO_ROOT / "benchmark" / "datasets" / "v6"

SP_TYPES = [f"SP-{i}" for i in range(1, 13)]
SC_TYPES = [f"SC-{i}" for i in range(1, 15)]
SEEDS = [0, 1, 2]


def normalised(source: str) -> str:
    return ast.unparse(ast.parse(source))


def check_candidate(base_source: str, variant_source: str, relation: str) -> tuple:
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


def generate_split(split: str, program_ids: list) -> tuple:
    out_dir = OUT_ROOT / "variants" / split
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs, rejected = [], []

    for program_id in program_ids:
        source_path = CORPUS_DIR / f"{program_id}.py"
        if not source_path.exists():
            rejected.append({"program": program_id, "reason": "corpus file missing"})
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
                            variant_source, meta = apply_fn(str(source_path), kind,
                                                            seed=seed, site=0)
                        else:
                            variant_source, meta = apply_fn(str(source_path), kind, seed=seed)
                    except Exception as exc:                    # noqa: BLE001
                        rejected.append({"program": program_id, "type": kind, "seed": seed,
                                         "reason": f"generator raised: "
                                                   f"{type(exc).__name__}: {exc}"})
                        continue

                    accepted, reason = check_candidate(base_source, variant_source, relation)
                    if not accepted:
                        rejected.append({"program": program_id, "type": kind,
                                         "seed": seed, "relation": relation,
                                         "reason": reason})
                        continue

                    variant_id = (meta.get("variant_id")
                                  or f"{program_id}__{kind.lower()}_s{seed}")
                    variant_path = out_dir / f"{variant_id}.py"
                    variant_path.write_text(variant_source)
                    pairs.append({
                        "pair_id": f"{split}__{variant_id}",
                        "base_id": program_id,
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
                        "benchmark_version": "v6",
                    })
    return pairs, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splits", nargs="+",
                        default=["train", "dev", "val", "test"])
    args = parser.parse_args()

    splits = json.loads(SPLITS_PATH.read_text())["splits"]
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {"benchmark_version": "v6",
              "generator": "benchmark/scripts/generate_benchmark_v6.py",
              "seeds": SEEDS, "splits": {}}

    for split in args.splits:
        if split not in splits:
            print(f"WARNING: unknown split {split!r}", file=sys.stderr)
            continue
        pairs, rejected = generate_split(split, splits[split])
        (OUT_ROOT / f"pairs_{split}.jsonl").write_text(
            "".join(json.dumps(p) + "\n" for p in pairs))
        n_equiv = sum(1 for p in pairs if p["semantic_relation"] == "EQUIVALENT")
        reasons: dict = {}
        for row in rejected:
            key = row["reason"].split(":")[0]
            reasons[key] = reasons.get(key, 0) + 1
        report["splits"][split] = {
            "n_programs": len(splits[split]),
            "n_pairs": len(pairs),
            "n_equivalent": n_equiv,
            "n_changed": len(pairs) - n_equiv,
            "n_rejected": len(rejected),
            "rejected_by_reason": dict(sorted(reasons.items())),
            "rejected": rejected,
        }
        print(f"[{split}] programs={len(splits[split])} pairs={len(pairs)} "
              f"(EQUIV={n_equiv} CHANGED={len(pairs) - n_equiv}) "
              f"rejected={len(rejected)} {dict(sorted(reasons.items()))}")

    (OUT_ROOT / "generation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {(OUT_ROOT / 'generation_report.json').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

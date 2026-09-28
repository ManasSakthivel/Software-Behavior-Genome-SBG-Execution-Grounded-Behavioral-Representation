"""
experiments/final/run_main_evaluation.py
========================================
Scores every pair of a split under one protocol and writes the raw per-pair
record. No metric is computed here: this stage only produces evidence.

Every pair of the split appears in the output exactly once, either with its
predictor distances or with the reason it could not be evaluated. Nothing is
dropped silently, which is what made the published "744 test pairs" claim
irreconcilable with its own 643-pair denominator.

Usage
-----
    python3 experiments/final/run_main_evaluation.py --split test --protocol published
    python3 experiments/final/run_main_evaluation.py --split test --protocol output_free_v6

Output
------
    artifacts/final/pairs_<split>_<protocol>.jsonl     one row per pair
    artifacts/final/programs_<split>_<protocol>.json   one row per program
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.final.extraction import (           # noqa: E402
    PROTOCOLS, extract_program, score_pair,
)


def load_pairs(split: str, dataset_dir: pathlib.Path) -> list:
    path = dataset_dir / f"pairs_{split}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run(split: str, protocol: str, out_dir: pathlib.Path,
        dataset_dir: pathlib.Path = None, tag: str = None,
        progress_every: int = 25) -> dict:
    dataset_dir = (dataset_dir or (REPO_ROOT / "benchmark" / "datasets")).resolve()
    tag = tag or split
    pairs = load_pairs(split, dataset_dir)
    cache: dict = {}
    rows = []
    started = time.time()

    for index, pair in enumerate(pairs, start=1):
        base = extract_program(str(REPO_ROOT / pair["base_path"]), cache, protocol)
        variant = extract_program(str(REPO_ROOT / pair["variant_path"]), cache, protocol)
        scores = score_pair(base, variant)

        row = {
            "pair_id": pair["pair_id"],
            "base_id": pair["base_id"],
            "split": split,
            "protocol": protocol,
            "dataset": str(dataset_dir.relative_to(REPO_ROOT)),
            "transformation_type": pair["transformation_type"],
            "semantic_relation": pair["semantic_relation"],
            "label": 0 if pair["semantic_relation"] == "EQUIVALENT" else 1,
            "base_entry": base.entry_discovery,
            "variant_entry": variant.entry_discovery,
            "base_exception_fraction": base.stats.get("exception_fraction"),
            "variant_exception_fraction": variant.stats.get("exception_fraction"),
            "base_n_traces": base.stats.get("n_traces"),
            "base_n_events": base.stats.get("n_events"),
            "variant_n_events": variant.stats.get("n_events"),
            "base_truncated": base.stats.get("n_truncated_traces"),
            "variant_truncated": variant.stats.get("n_truncated_traces"),
        }
        if scores is None:
            row["evaluated"] = False
            failed = base if not base.ok else variant
            row["failure_side"] = "base" if not base.ok else "variant"
            row["failure_kind"] = failed.failure_kind
            row["failure_detail"] = failed.failure_detail
        else:
            row["evaluated"] = True
            row["scores"] = scores
        rows.append(row)

        if index % progress_every == 0 or index == len(pairs):
            elapsed = time.time() - started
            rate = index / elapsed if elapsed else 0.0
            print(f"  [{protocol}/{split}] {index}/{len(pairs)} pairs  "
                  f"{elapsed:6.1f}s  {rate:5.2f} pairs/s", flush=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    pairs_path = out_dir / f"pairs_{tag}_{protocol}.jsonl"
    pairs_path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    programs = {path: record.summary() for path, record in cache.items()}
    programs_path = out_dir / f"programs_{tag}_{protocol}.json"
    programs_path.write_text(json.dumps({
        "split": split,
        "protocol": protocol,
        "dataset": str(dataset_dir.relative_to(REPO_ROOT)),
        "n_programs": len(programs),
        "n_ok": sum(1 for r in programs.values() if r["ok"]),
        "wall_time_s": round(time.time() - started, 1),
        "programs": programs,
    }, indent=2) + "\n")

    n_eval = sum(1 for r in rows if r["evaluated"])
    print(f"[{protocol}/{split}] {n_eval}/{len(rows)} pairs evaluated; "
          f"wrote {pairs_path.name}, {programs_path.name}")
    return {"n_pairs": len(rows), "n_evaluated": n_eval}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="test",
                        choices=["train", "dev", "val", "test"])
    parser.add_argument("--protocol", default="published", choices=list(PROTOCOLS))
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "artifacts" / "final"))
    parser.add_argument("--dataset-dir", default=None,
                        help="defaults to benchmark/datasets; pass "
                             "benchmark/datasets/v6 for the corrected benchmark")
    parser.add_argument("--tag", default=None,
                        help="name used in the output filenames (default: the split)")
    args = parser.parse_args()
    run(args.split, args.protocol, pathlib.Path(args.out_dir),
        pathlib.Path(args.dataset_dir) if args.dataset_dir else None, args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

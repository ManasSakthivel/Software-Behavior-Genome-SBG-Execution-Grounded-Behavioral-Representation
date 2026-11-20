#!/usr/bin/env python3
"""
benchmark/scripts/build_manifest.py
===================================
Builds ``benchmark/benchmark_manifest.json``: the single authoritative count
for every program and every pair in the benchmark.

Why one file
------------
The repository previously carried four mutually inconsistent accounts of its
own size -- 3 777 pairs in the README against 3 577 on disk, 99 corpus programs
against 64 files and 60 programs actually assigned to splits, and a test-split
AUROC reported over 744 pairs that was computed over 643. Each of those numbers
had been typed into prose independently. This manifest is generated from the
files, and ``experiments/final/consistency_check.py`` fails the build when a
document disagrees with it.

Counts recorded per split: programs, nominal pairs, compilable pairs,
protocol-executable pairs, statically valid pairs, and every exclusion with its
reason. Split intersections are recorded explicitly so program-level
disjointness is verifiable rather than asserted.

Usage:
    python3 benchmark/scripts/build_manifest.py
"""
from __future__ import annotations

import collections
import hashlib
import itertools
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

CORPUS_DIR = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
SPLITS_PATH = REPO_ROOT / "benchmark" / "splits" / "split_assignment.json"
DATASETS = {
    "v5_published": REPO_ROOT / "benchmark" / "datasets",
    "v6_corrected": REPO_ROOT / "benchmark" / "datasets" / "v6",
}
AUDITS = {
    "v5_published": REPO_ROOT / "artifacts" / "final" / "BENCHMARK_VALIDITY_AUDIT.json",
    "v6_corrected": REPO_ROOT / "artifacts" / "final" / "BENCHMARK_VALIDITY_AUDIT_V6.json",
}
SPLITS = ("train", "dev", "val", "test")


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_inventory(assigned: set) -> dict:
    files = sorted(CORPUS_DIR.glob("*.py"))
    programs = {p.stem: {"path": str(p.relative_to(REPO_ROOT)),
                         "sha256": sha256_of(p),
                         "assigned_to_split": p.stem in assigned}
                for p in files}
    unassigned = sorted(name for name, info in programs.items()
                        if not info["assigned_to_split"])
    return {
        "n_files_on_disk": len(files),
        "n_assigned_to_splits": len(files) - len(unassigned),
        "n_unassigned": len(unassigned),
        "unassigned_programs": unassigned,
        "unassigned_reason": (
            "present in benchmark/corpus/base_programs but not listed in "
            "benchmark/splits/split_assignment.json; excluded from every "
            "experiment and from every reported count"
        ),
        "programs": programs,
    }


def dataset_counts(dataset_dir: pathlib.Path, audit_path: pathlib.Path) -> dict:
    audit = (json.loads(audit_path.read_text()) if audit_path.exists() else None)
    by_pair = ({row["pair_id"]: row for row in audit["pairs"]} if audit else {})

    out = {"dataset_dir": str(dataset_dir.relative_to(REPO_ROOT)),
           "validity_audit": (str(audit_path.relative_to(REPO_ROOT))
                              if audit else None),
           "splits": {}, "totals": {}}
    grand = collections.Counter()

    for split in SPLITS:
        path = dataset_dir / f"pairs_{split}.jsonl"
        if not path.exists():
            continue
        pairs = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        programs = sorted({p["base_id"] for p in pairs})
        n_changed = sum(1 for p in pairs if p["semantic_relation"] != "EQUIVALENT")

        uncompilable = no_entry = changed_unobservable = equivalent_noop = 0
        for pair in pairs:
            verdict = by_pair.get(pair["pair_id"])
            if verdict is None:
                continue
            if verdict.get("status") == "uncompilable":
                uncompilable += 1
            elif verdict.get("exclusion_reason") == "no_entry_function":
                no_entry += 1
            elif verdict.get("observable") is False:
                if pair["semantic_relation"] == "EQUIVALENT":
                    equivalent_noop += 1
                else:
                    changed_unobservable += 1

        valid = len(pairs) - uncompilable - no_entry - changed_unobservable
        block = {
            "n_programs": len(programs),
            "programs": programs,
            "nominal_pairs": len(pairs),
            "changed_pairs": n_changed,
            "equivalent_pairs": len(pairs) - n_changed,
            "excluded_uncompilable": uncompilable,
            "excluded_no_entry_function": no_entry,
            "excluded_changed_unobservable": changed_unobservable,
            "statically_valid_pairs": valid,
            "equivalent_noop_pairs": equivalent_noop,
            "by_transformation": dict(sorted(collections.Counter(
                p["transformation_type"] for p in pairs).items())),
            "pairs_file": str(path.relative_to(REPO_ROOT)),
            "pairs_file_sha256": sha256_of(path),
        }
        out["splits"][split] = block
        for key in ("nominal_pairs", "changed_pairs", "equivalent_pairs",
                    "excluded_uncompilable", "excluded_no_entry_function",
                    "excluded_changed_unobservable", "statically_valid_pairs"):
            grand[key] += block[key]
        grand["n_programs"] += block["n_programs"]

    out["totals"] = dict(grand)

    intersections = {}
    for a, b in itertools.combinations(
            [s for s in SPLITS if s in out["splits"]], 2):
        shared = sorted(set(out["splits"][a]["programs"])
                        & set(out["splits"][b]["programs"]))
        intersections[f"{a}|{b}"] = shared
    out["split_program_intersections"] = intersections
    out["all_intersections_empty"] = all(not v for v in intersections.values())
    return out


def main() -> int:
    split_data = json.loads(SPLITS_PATH.read_text())
    assigned = {name for names in split_data["splits"].values() for name in names}

    manifest = {
        "manifest": "SBG_BENCHMARK_MANIFEST",
        "generated_by": "benchmark/scripts/build_manifest.py",
        "authority": (
            "This file is the single source for every program and pair count. "
            "Any count in a README, manuscript, table or figure must be derived "
            "from it; experiments/final/consistency_check.py enforces that."
        ),
        "split_assignment": {
            "path": str(SPLITS_PATH.relative_to(REPO_ROOT)),
            "seed": split_data["seed"],
            "method": split_data["method"],
            "counts": split_data["split_counts"],
            "n_programs_assigned": len(assigned),
        },
        "corpus": corpus_inventory(assigned),
        "datasets": {name: dataset_counts(path, AUDITS[name])
                     for name, path in DATASETS.items()
                     if (path / "pairs_test.jsonl").exists()},
    }

    out = REPO_ROOT / "benchmark" / "benchmark_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")

    corpus = manifest["corpus"]
    print(f"corpus: {corpus['n_files_on_disk']} files, "
          f"{corpus['n_assigned_to_splits']} assigned, "
          f"{corpus['n_unassigned']} unassigned {corpus['unassigned_programs']}")
    for name, block in manifest["datasets"].items():
        print(f"\n[{name}] {block['dataset_dir']}  "
              f"intersections_empty={block['all_intersections_empty']}")
        for split, s in block["splits"].items():
            print(f"  {split:6s} programs={s['n_programs']:3d} nominal={s['nominal_pairs']:5d} "
                  f"valid={s['statically_valid_pairs']:5d} "
                  f"(uncompilable={s['excluded_uncompilable']}, "
                  f"no_entry={s['excluded_no_entry_function']}, "
                  f"unobservable={s['excluded_changed_unobservable']})")
        print(f"  TOTAL  nominal={block['totals']['nominal_pairs']} "
              f"valid={block['totals']['statically_valid_pairs']}")
    print(f"\nwrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

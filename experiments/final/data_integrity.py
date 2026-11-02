"""
Static integrity checks for a benchmark dataset (pairs_*.jsonl + variants).

Nothing here executes benchmark code or reads any method's score, and nothing
changes a label. It reports defects; it never repairs them.

Checks
------
* duplicate pair ids (within and across splits)
* malformed records (missing keys, label/relation disagreement)
* missing base / variant files
* uncompilable base or variant
* a base program appearing in more than one split (cluster leakage)
* SP-2 dangling method references: a variant labelled EQUIVALENT whose
  ``def`` of a method was renamed while an attribute reference to the old
  name (``self.allow(...)``) was left untouched. The variant then raises
  ``AttributeError`` where the base does not, so the EQUIVALENT label is not
  valid for it. ``sp2_function_rename.py`` only rewrites ``Name`` call sites.

Usage:  python experiments/final/data_integrity.py [--dataset benchmark/datasets/v6]
        [--json OUT] [--strict]
Exit status is 1 with ``--strict`` if any defect is found.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
import warnings
from collections import Counter, defaultdict
from typing import Dict, List, Set

REPO = pathlib.Path(__file__).resolve().parents[2]
REQUIRED_KEYS = ("pair_id", "base_id", "base_path", "variant_path",
                 "transformation_type", "semantic_relation", "expected_label",
                 "split")
SPLITS = ("train", "dev", "val", "test")


def load_pairs(dataset_dir: pathlib.Path) -> List[dict]:
    rows = []
    for split in SPLITS:
        path = dataset_dir / f"pairs_{split}.jsonl"
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rows.append({"_malformed": f"{path.name}:{n}", "split": split})
                continue
            row["_origin"] = f"{path.name}:{n}"
            rows.append(row)
    return rows


def _defined_functions(tree: ast.AST) -> Set[str]:
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _attribute_names(tree: ast.AST) -> Set[str]:
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def dangling_method_references(base_src: str, variant_src: str) -> List[str]:
    """Attribute names the variant still uses whose definition it dropped.

    Returns [] when either source does not parse. Only names that the *base*
    defines as a function and that the variant no longer defines are reported,
    so ordinary library attributes (``list.append``) never match.
    """
    try:
        base_tree, var_tree = ast.parse(base_src), ast.parse(variant_src)
    except SyntaxError:
        return []
    renamed_away = _defined_functions(base_tree) - _defined_functions(var_tree)
    return sorted(renamed_away & _attribute_names(var_tree))


def check_dataset(dataset_dir: pathlib.Path, repo: pathlib.Path = REPO) -> dict:
    rows = load_pairs(dataset_dir)
    defects: Dict[str, List] = defaultdict(list)

    malformed = [r for r in rows if "_malformed" in r]
    for r in malformed:
        defects["malformed_json"].append(r["_malformed"])
    rows = [r for r in rows if "_malformed" not in r]

    ids = Counter(r.get("pair_id") for r in rows)
    for pid, n in ids.items():
        if n > 1:
            defects["duplicate_pair_id"].append({"pair_id": pid, "count": n})

    program_splits: Dict[str, Set[str]] = defaultdict(set)
    for r in rows:
        missing = [k for k in REQUIRED_KEYS if k not in r]
        if missing:
            defects["missing_keys"].append({"pair_id": r.get("pair_id"),
                                            "missing": missing})
            continue
        program_splits[r["base_id"]].add(r["split"])
        if r["split"] not in SPLITS or r["split"] != r.get("split"):
            defects["bad_split"].append(r["pair_id"])
        if r["semantic_relation"] != r["expected_label"]:
            defects["label_relation_disagree"].append(r["pair_id"])
        if r["semantic_relation"] not in ("EQUIVALENT", "CHANGED"):
            defects["unknown_relation"].append(r["pair_id"])
        paths = {}
        for side in ("base_path", "variant_path"):
            p = repo / r[side]
            if not p.is_file():
                defects[f"missing_{side}"].append(r["pair_id"])
                continue
            paths[side] = p.read_text()
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    compile(paths[side], str(p), "exec")
            except SyntaxError:
                defects[f"uncompilable_{side}"].append(r["pair_id"])
        if (r["semantic_relation"] == "EQUIVALENT"
                and r["transformation_type"] == "SP-2"
                and len(paths) == 2):
            dangling = dangling_method_references(paths["base_path"],
                                                  paths["variant_path"])
            if dangling:
                defects["sp2_dangling_method_reference"].append(
                    {"pair_id": r["pair_id"], "base_id": r["base_id"],
                     "split": r["split"], "names": dangling})

    for prog, splits in sorted(program_splits.items()):
        if len(splits) > 1:
            defects["program_in_multiple_splits"].append(
                {"base_id": prog, "splits": sorted(splits)})

    sp2 = [r for r in rows if r.get("transformation_type") == "SP-2"
           and r.get("semantic_relation") == "EQUIVALENT"]
    dangling_by_split = Counter(d["split"]
                                for d in defects["sp2_dangling_method_reference"])
    sp2_by_split = Counter(r["split"] for r in sp2)
    return {
        "dataset": str(dataset_dir.relative_to(repo)
                       if dataset_dir.is_relative_to(repo) else dataset_dir),
        "n_pairs": len(rows),
        "n_programs": len(program_splits),
        "defect_counts": {k: len(v) for k, v in sorted(defects.items())},
        "sp2_equivalent_pairs_by_split": dict(sp2_by_split),
        "sp2_dangling_by_split": dict(dangling_by_split),
        "defects": {k: v for k, v in sorted(defects.items())},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="benchmark/datasets/v6")
    ap.add_argument("--json", default=None)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    report = check_dataset(REPO / args.dataset)
    if args.json:
        out = pathlib.Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "defects"}, indent=2))
    has_defects = sum(report["defect_counts"].values()) > 0
    return 1 if (args.strict and has_defects) else 0


if __name__ == "__main__":
    sys.exit(main())

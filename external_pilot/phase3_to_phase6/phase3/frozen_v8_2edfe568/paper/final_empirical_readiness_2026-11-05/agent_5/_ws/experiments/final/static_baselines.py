#!/usr/bin/env python3
"""
experiments/final/static_baselines.py
=====================================
Adds the two structural baselines to an existing per-pair record.

Why they belong in the same table
---------------------------------
SBG's premise is that *executing* a program tells you something about its
behaviour that reading its source does not. That premise is only tested against
a structural baseline. The published comparison ran token and AST baselines in
`baselines/b01_token.py` and `baselines/b02_ast.py`, but under a different
extraction pass from the one the dynamic methods used, so the two were never
strictly comparable.

Both baselines here are computed from source text alone, so they need no
execution and can be merged into a per-pair record after the fact. They are
scored on exactly the pairs the dynamic predictors were scored on.

What to expect
--------------
These baselines should do *badly*, and badly in a specific direction. The
semantics-preserving transformations rewrite the source heavily -- renames, dead
code, loop rewrites -- while the semantics-changing mutations alter one operator
or one constant. Structural distance is therefore larger for the EQUIVALENT
class than for the CHANGED class, and the AUROC lands below 0.5. That inversion
is the phenomenon the project set out to address, and it is worth reporting as a
number rather than as a motivation.

Usage:
    python3 experiments/final/static_baselines.py \
        --pairs artifacts/final/pairs_test_published.jsonl \
        --dataset benchmark/datasets
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import sys
import tokenize
from io import StringIO
from typing import Dict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

STATIC_PREDICTORS = ("static_token", "static_ast")


def token_multiset(source: str) -> collections.Counter:
    """Counter over token (type, text), dropping comments, strings and layout.

    Identifier text is kept, so a rename registers as a difference. That is the
    point: it is what makes a structural baseline fail on semantics-preserving
    renames.
    """
    counts: collections.Counter = collections.Counter()
    try:
        for token in tokenize.generate_tokens(StringIO(source).readline):
            if token.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                              tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER,
                              tokenize.STRING):
                continue
            counts[(token.type, token.string)] += 1
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return collections.Counter()
    return counts


def ast_multiset(source: str) -> collections.Counter:
    """Counter over AST node type names, plus operator and identifier names."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return collections.Counter()
    counts: collections.Counter = collections.Counter()
    for node in ast.walk(tree):
        counts[type(node).__name__] += 1
        if isinstance(node, ast.Name):
            counts[f"Name:{node.id}"] += 1
        elif isinstance(node, ast.Constant):
            counts[f"Const:{node.value!r}"] += 1
    return counts


def multiset_distance(a: collections.Counter, b: collections.Counter) -> float:
    """1 - weighted Jaccard. 0 when identical, 1 when disjoint."""
    if not a and not b:
        return 0.0
    keys = set(a) | set(b)
    intersection = sum(min(a[k], b[k]) for k in keys)
    union = sum(max(a[k], b[k]) for k in keys)
    return 1.0 - (intersection / union if union else 0.0)


def load_paths(dataset_dir: pathlib.Path) -> Dict[str, tuple]:
    paths = {}
    for split in ("train", "dev", "val", "test"):
        path = dataset_dir / f"pairs_{split}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            pair = json.loads(line)
            paths[pair["pair_id"]] = (pair["base_path"], pair["variant_path"])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True,
                        help="per-pair JSONL written by run_main_evaluation.py")
    parser.add_argument("--dataset", default=str(REPO_ROOT / "benchmark" / "datasets"))
    args = parser.parse_args()

    pairs_path = pathlib.Path(args.pairs)
    lookup = load_paths(pathlib.Path(args.dataset))
    cache: Dict[str, tuple] = {}

    def features(relative: str):
        if relative not in cache:
            source = (REPO_ROOT / relative).read_text()
            cache[relative] = (token_multiset(source), ast_multiset(source))
        return cache[relative]

    rows, added, skipped = [], 0, 0
    for line in pairs_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        entry = lookup.get(row["pair_id"])
        if entry is None or not row.get("evaluated"):
            # A structural baseline could score an unevaluated pair, but scoring
            # it there and not the dynamic predictors would make the comparison
            # unfair in the baseline's favour. Same pairs or no comparison.
            skipped += 1
            rows.append(row)
            continue
        base_tokens, base_ast = features(entry[0])
        variant_tokens, variant_ast = features(entry[1])
        row["scores"]["static_token"] = round(
            multiset_distance(base_tokens, variant_tokens), 9)
        row["scores"]["static_ast"] = round(
            multiset_distance(base_ast, variant_ast), 9)
        added += 1
        rows.append(row)

    pairs_path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"added static baselines to {added} evaluated pairs in "
          f"{pairs_path.name} ({skipped} rows left unscored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

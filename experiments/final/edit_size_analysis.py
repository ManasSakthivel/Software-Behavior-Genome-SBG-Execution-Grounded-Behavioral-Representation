"""Standalone edit-size confound analysis for the SBG v6 benchmark.

Computes forward/reversed edit-size AUROCs, per-bin SBG AUROC (using the same
EDIT_BINS as audit_recompute.py), and per-transformation-type statistics.

Usage:
    python experiments/final/edit_size_analysis.py --split test \\
        --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl
    python experiments/final/edit_size_analysis.py --split dev \\
        --pairs-file artifacts/final/pairs_v6dev_output_free_v7.jsonl --no-write
"""
from __future__ import annotations
import argparse, ast, difflib, json, pathlib, statistics as stat, sys
from collections import defaultdict
from typing import Dict, List, Tuple

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from sbg.statistics import auroc  # noqa: E402

EDIT_BINS: List[Tuple[int, int]] = [
    (0, 2), (3, 5), (6, 10), (11, 20), (21, 40), (41, 10 ** 9)]
_META_FILE = {"test": "pairs_test.jsonl", "dev": "pairs_dev.jsonl"}


def _canonical_lines(path: pathlib.Path) -> List[str]:
    return ast.unparse(ast.parse(path.read_text())).splitlines()


def _edit_size(base_path: str, variant_path: str) -> int:
    a = _canonical_lines(REPO / base_path)
    b = _canonical_lines(REPO / variant_path)
    n = 0
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            n += 1
    return n


def _bin_idx(n: int) -> int:
    for i, (lo, hi) in enumerate(EDIT_BINS):
        if lo <= n <= hi:
            return i
    return len(EDIT_BINS) - 1


def _load_evaluated(pairs_file: pathlib.Path) -> List[dict]:
    return [r for r in
            (json.loads(l) for l in pairs_file.read_text().splitlines() if l.strip())
            if r.get("evaluated")]


def _load_meta(split: str) -> Dict[str, dict]:
    p = REPO / "benchmark" / "datasets" / "v6" / _META_FILE[split]
    return {json.loads(l)["pair_id"]: json.loads(l)
            for l in p.read_text().splitlines() if l.strip()}


def analyse(split: str, pairs_file: pathlib.Path) -> dict:
    evaluated = _load_evaluated(pairs_file)
    meta = _load_meta(split)
    sizes: List[int] = []
    labels: List[int] = []
    sbg_scores: List[float] = []
    bins: List[int] = []
    by_type: Dict[str, dict] = defaultdict(lambda: {"sizes": [], "labels": [], "sbg": []})

    for r in evaluated:
        m = meta.get(r["pair_id"])
        if m is None:
            continue
        s = _edit_size(m["base_path"], m["variant_path"])
        b = _bin_idx(s)
        lbl = r["label"]
        sc = r["scores"]["sbg_v5"]
        sizes.append(s); labels.append(lbl); sbg_scores.append(sc); bins.append(b)
        tt = m["transformation_type"]
        by_type[tt]["sizes"].append(s); by_type[tt]["labels"].append(lbl); by_type[tt]["sbg"].append(sc)

    fwd = round(auroc([float(s) for s in sizes], labels), 6)
    rev = round(1.0 - fwd, 6)
    sbg_auc = round(auroc(sbg_scores, labels), 6)

    bin_results = {}
    for i, (lo, hi) in enumerate(EDIT_BINS):
        idx = [k for k, bk in enumerate(bins) if bk == i]
        lab = [labels[k] for k in idx]
        sc = [sbg_scores[k] for k in idx]
        npos, nneg = sum(lab), len(lab) - sum(lab)
        entry: dict = {"range": [lo, hi if hi < 10 ** 9 else None],
                       "n": len(idx), "n_changed": npos, "n_equivalent": nneg, "sbg_auroc": None}
        if npos and nneg:
            entry["sbg_auroc"] = round(auroc(sc, lab), 6)
        bin_results[str(i)] = entry

    type_results = {}
    for tt, d in sorted(by_type.items()):
        szs, labs = d["sizes"], d["labels"]
        chng_szs = [s for s, l in zip(szs, labs) if l == 1]
        equiv_szs = [s for s, l in zip(szs, labs) if l == 0]
        type_results[tt] = {
            "n": len(szs), "n_changed": sum(labs), "n_equivalent": len(labs) - sum(labs),
            "mean": round(stat.mean(szs), 2) if szs else None,
            "median": stat.median(szs) if szs else None,
            "min": min(szs) if szs else None,
            "max": max(szs) if szs else None,
            "all_changed_small_le5": all(s <= 5 for s in chng_szs) if chng_szs else None,
            "any_equivalent_large_ge6": any(s >= 6 for s in equiv_szs) if equiv_szs else None,
        }

    return {"split": split, "n": len(sizes),
            "n_changed": sum(labels), "n_equivalent": len(labels) - sum(labels),
            "edit_size_forward_auroc": fwd, "edit_size_reversed_auroc": rev,
            "sbg_v5_auroc": sbg_auc, "bins": bin_results,
            "by_transformation_type": type_results}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=["test", "dev"], required=True)
    ap.add_argument("--pairs-file", required=True)
    ap.add_argument("--out-dir", default=str(REPO / "reports/remediation/results"))
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    pairs_file = pathlib.Path(args.pairs_file)
    if not pairs_file.is_absolute():
        pairs_file = REPO / pairs_file

    result = analyse(args.split, pairs_file)
    print(json.dumps(result, indent=2))

    if not args.no_write:
        out_dir = pathlib.Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"edit_size_analysis_{args.split}.json"
        out_path.write_text(json.dumps(result, indent=2) + "\n")
        print(f"\nReport written to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Independent recomputation of the headline numbers from committed per-pair
records.

Purpose
-------
The IEEE Access audit asked that headline AUROCs, denominators, tie rates,
leave-one-cluster-out sensitivity, entry-point correspondence and an
edit-size confound analysis be recomputed from the per-pair artifacts rather
than quoted. This script does that with ``sbg.statistics`` only; it never
re-runs any program and never reads the benchmark answer key beyond the
``label`` already stored in each per-pair record.

It FAILS (exit 1) if any of the six reference AUROCs, taken from the
committed ``MAIN_EVALUATION_*`` artifacts, does not reproduce within 1e-6.

It writes only under ``--out-dir`` (default ``reports/remediation/results``).
The old test split is observed / possibly contaminated; the numbers produced
here are descriptive re-computations of historical results, not new evidence.

Usage:  python experiments/final/audit_recompute.py [--out-dir DIR] [--shuffles N]
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import pathlib
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))

from sbg.statistics import (auroc, cluster_bootstrap_ci,  # noqa: E402
                            label_shuffle_noise_floor)
from analyse_results import build_sets, load_rows, load_validity, vectors  # noqa: E402
import entry_policy  # noqa: E402

ART = REPO / "artifacts" / "final"
SEED = 42
EDIT_BINS = [(0, 2), (3, 5), (6, 10), (11, 20), (21, 40), (41, 10 ** 9)]

# (result_id, pairs file, validity audit, set, predictor, expected)
REFERENCES = [
    ("v6test_evaluable_sbg_v5", "pairs_v6test_output_free_v6.jsonl",
     "BENCHMARK_VALIDITY_AUDIT_V6.json", "EVALUABLE", "sbg_v5", 0.60127),
    ("v6test_evaluable_static_ast", "pairs_v6test_output_free_v6.jsonl",
     "BENCHMARK_VALIDITY_AUDIT_V6.json", "EVALUABLE", "static_ast", 0.104743),
    ("v6test_all_sbg_v5", "pairs_v6test_output_free_v6.jsonl",
     "BENCHMARK_VALIDITY_AUDIT_V6.json", "ALL", "sbg_v5", 0.523592),
    ("v6test_all_static_ast", "pairs_v6test_output_free_v6.jsonl",
     "BENCHMARK_VALIDITY_AUDIT_V6.json", "ALL", "static_ast", 0.350996),
    ("published_evaluable_sbg_v5", "pairs_test_published.jsonl",
     "BENCHMARK_VALIDITY_AUDIT.json", "EVALUABLE", "sbg_v5", 0.545743),
    ("published_valid_sbg_v5", "pairs_test_published.jsonl",
     "BENCHMARK_VALIDITY_AUDIT.json", "VALID", "sbg_v5", 0.640032),
]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def _a(rows: List[dict], predictor: str) -> Optional[float]:
    d, l, _ = vectors(rows, predictor)
    if not l or sum(l) in (0, len(l)):
        return None
    return auroc(d, l)


def leave_one_cluster_out(rows: List[dict], predictor: str) -> Dict[str, Optional[float]]:
    out = {}
    for c in sorted({r["base_id"] for r in rows}):
        rest = [r for r in rows if r["base_id"] != c]
        v = _a(rest, predictor)
        out[c] = None if v is None else round(v, 6)
    return out


def per_cluster(rows: List[dict], predictor: str) -> Dict[str, dict]:
    by = defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(r)
    out = {}
    for c, rs in sorted(by.items()):
        v = _a(rs, predictor)
        out[c] = {"n": len(rs), "n_changed": sum(r["label"] for r in rs),
                  "auroc": None if v is None else round(v, 6)}
    return out


def ties(rows: List[dict], predictor: str) -> dict:
    d, _, _ = vectors(rows, predictor)
    zero = sum(1 for x in d if x == 0.0)
    return {"n": len(d), "n_zero": zero,
            "frac_zero": round(zero / len(d), 4) if d else None,
            "n_distinct": len(set(d))}


def _function_by_name(source: str, name: str) -> Optional[ast.FunctionDef]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _module_functions(source: str) -> set:
    return {n.name for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef)}


def entry_correspondence(pair_rows: List[dict], pair_meta: Dict[str, dict]) -> dict:
    """Count evaluated EQUIVALENT pairs whose base and variant traced entries
    do not correspond.

    SP-2 (function rename) is matched structurally (name-free fingerprint);
    every other transformation must trace the identical entry name.
    """
    mismatches, naive_name_diff, driver_traced = [], 0, []
    n_eq = 0
    for r in pair_rows:
        if not r["evaluated"] or r["label"] != 0:
            continue
        n_eq += 1
        b = (r["base_entry"] or "").split(":", 1)[-1]
        v = (r["variant_entry"] or "").split(":", 1)[-1]
        if b != v:
            naive_name_diff += 1
        meta = pair_meta.get(r["pair_id"])
        if not meta:
            continue
        base_src = (REPO / meta["base_path"]).read_text()
        var_src = (REPO / meta["variant_path"]).read_text()
        if r["transformation_type"] == "SP-2":
            fb, fv = _function_by_name(base_src, b), _function_by_name(var_src, v)
            if fb is None or fv is None:
                same = False
            else:
                same = (entry_policy.structural_id(fb, _module_functions(base_src))
                        == entry_policy.structural_id(fv, _module_functions(var_src)))
        else:
            same = b == v
        if not same:
            mismatches.append({"pair_id": r["pair_id"], "base_entry": b,
                               "variant_entry": v})
        for side, name in (("base", b), ("variant", v)):
            bare = name[3:] if name.startswith("fn_") else name
            if bare.startswith("test_"):
                driver_traced.append({"pair_id": r["pair_id"], "side": side,
                                      "entry": name})
    return {"n_evaluated_equivalent": n_eq,
            "n_name_inequality_naive": naive_name_diff,
            "n_structural_mismatch": len(mismatches),
            "mismatches": mismatches,
            "driver_traced": driver_traced}


def _canonical_lines(source: str) -> List[str]:
    # Variants are emitted through ast.unparse; comparing raw text would count
    # reformatting as edits. Canonicalise both sides the same way first.
    return ast.unparse(ast.parse(source)).splitlines()


def edit_size(meta: dict) -> int:
    a = _canonical_lines((REPO / meta["base_path"]).read_text())
    b = _canonical_lines((REPO / meta["variant_path"]).read_text())
    n = 0
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            n += 1
    return n


def _bin(n: int) -> int:
    for i, (lo, hi) in enumerate(EDIT_BINS):
        if lo <= n <= hi:
            return i
    return len(EDIT_BINS) - 1


def edit_size_analysis(rows: List[dict], pair_meta: Dict[str, dict],
                       predictor: str) -> dict:
    sizes, labels, scores, bins = [], [], [], []
    for r in rows:
        meta = pair_meta.get(r["pair_id"])
        if meta is None:
            continue
        s = edit_size(meta)
        sizes.append(s)
        labels.append(r["label"])
        scores.append(r["scores"][predictor])
        bins.append(_bin(s))
    if not labels or sum(labels) in (0, len(labels)):
        return {"note": "degenerate"}
    out = {"edit_size_alone_auroc": round(auroc([float(s) for s in sizes], labels), 6),
           "n": len(labels), "bins": {},
           # Mutations are small edits and the EQUIVALENT transformations touch
           # many lines, so the informative direction is "smaller edit =
           # CHANGED". 1 - AUROC is exact for the reversed score (tie-aware).
           "edit_size_reversed_auroc": round(
               1.0 - auroc([float(s) for s in sizes], labels), 6)}
    # AUROC within bins, weighted by the number of mixed (pos, neg) pairs.
    num = den = 0.0
    for i, (lo, hi) in enumerate(EDIT_BINS):
        idx = [k for k, b in enumerate(bins) if b == i]
        lab = [labels[k] for k in idx]
        npos, nneg = sum(lab), len(lab) - sum(lab)
        entry = {"range": [lo, hi if hi < 10 ** 9 else None], "n": len(idx),
                 "n_changed": npos, "n_equivalent": nneg, "auroc": None}
        if npos and nneg:
            v = auroc([scores[k] for k in idx], lab)
            entry["auroc"] = round(v, 6)
            num += v * npos * nneg
            den += npos * nneg
        out["bins"][str(i)] = entry
    out["stratified_auroc"] = round(num / den, 6) if den else None
    out["stratified_weight_pairs"] = den
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(REPO / "reports/remediation/results"))
    ap.add_argument("--shuffles", type=int, default=2000)
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    out_dir = pathlib.Path(args.out_dir)

    revision = git_revision()
    manifest: List[dict] = []
    failures: List[str] = []

    def record(result_id, value, n, inputs, protocol, split, split_status,
               evaluation_status, extra=None):
        entry = {"result_id": result_id, "value": value, "n": n,
                 "input_artifacts": {p.name: sha256(p) for p in inputs},
                 "protocol": protocol, "split": split,
                 "split_status": split_status,
                 "evaluation_status": evaluation_status,
                 "code_revision": revision,
                 "generator": "experiments/final/audit_recompute.py"}
        if extra:
            entry.update(extra)
        manifest.append(entry)

    # 1. Reference AUROC reproduction ---------------------------------
    reproduced = {}
    for rid, pairs_f, audit_f, set_name, predictor, expected in REFERENCES:
        pairs_p, audit_p = ART / pairs_f, ART / audit_f
        rows = load_rows(pairs_p)
        sets = build_sets(rows, load_validity(audit_p))
        d, l, _ = vectors(sets[set_name], predictor)
        got = auroc(d, l)
        ok = abs(got - expected) <= 1e-5
        reproduced[rid] = {"expected": expected, "recomputed": round(got, 6),
                           "n": len(l), "match": ok}
        if not ok:
            failures.append(f"{rid}: expected {expected} got {got:.6f}")
        protocol = rows[0]["protocol"]
        record(rid, round(got, 6), len(l), [pairs_p, audit_p], protocol, "test",
               "observed_possibly_contaminated",
               "independently_recomputed_historical")

    # 2. Detailed analysis of the v6 test record ----------------------
    pairs_p = ART / "pairs_v6test_output_free_v6.jsonl"
    audit_p = ART / "BENCHMARK_VALIDITY_AUDIT_V6.json"
    rows = load_rows(pairs_p)
    sets = build_sets(rows, load_validity(audit_p))
    ev = sets["EVALUABLE"]
    meta = {json.loads(l)["pair_id"]: json.loads(l)
            for l in (REPO / "benchmark/datasets/v6/pairs_test.jsonl")
            .read_text().splitlines() if l.strip()}

    detail: dict = {
        "denominators": {k: len(v) for k, v in sets.items()},
        "label_balance": {k: {"changed": sum(r["label"] for r in v),
                              "equivalent": len(v) - sum(r["label"] for r in v)}
                          for k, v in sets.items()},
        "n_clusters": {k: len({r["base_id"] for r in v}) for k, v in sets.items()},
        "n_clusters_with_both_classes": sum(
            1 for c in {r["base_id"] for r in ev}
            if len({r["label"] for r in ev if r["base_id"] == c}) == 2),
        "missingness": {
            "n_unevaluated": len(rows) - len(ev),
            "by_kind": {},
            "programs_without_any_evaluated_pair": sorted(
                {r["base_id"] for r in rows} - {r["base_id"] for r in ev}),
        },
    }
    for r in rows:
        if not r["evaluated"]:
            k = f'{r.get("failure_side")}:{r.get("failure_kind")}'
            detail["missingness"]["by_kind"][k] = detail["missingness"]["by_kind"].get(k, 0) + 1

    for predictor in ("sbg_v5", "static_ast", "exception_fraction"):
        d, l, c = vectors(ev, predictor)
        lo, hi, n_eff = cluster_bootstrap_ci(d, l, c, n_bootstrap=2000, seed=SEED)
        detail[predictor] = {
            "auroc_evaluable": round(auroc(d, l), 6),
            "ci95_cluster_bootstrap": [lo, hi],
            "n_clusters": len(set(c)),
            "ties": ties(ev, predictor),
            "leave_one_cluster_out": leave_one_cluster_out(ev, predictor),
            "per_cluster": per_cluster(ev, predictor),
        }
    # A comparable sample: pairs on which sbg_v5, static_ast and
    # exception_fraction are all defined (same pairs for every method).
    comparable = [r for r in ev if all(
        p in r["scores"] for p in ("sbg_v5", "static_ast", "exception_fraction"))]
    detail["comparable_sample"] = {
        "n": len(comparable),
        "auroc": {p: round(_a(comparable, p), 6)
                  for p in ("sbg_v5", "static_ast", "exception_fraction")}}

    corr = entry_correspondence(rows, meta)
    detail["entry_correspondence"] = corr
    keep = {m["pair_id"] for m in corr["mismatches"]}
    clean = [r for r in ev if r["pair_id"] not in keep]
    d, l, c = vectors(clean, "sbg_v5")
    detail["sbg_v5_excluding_entry_mismatch"] = {
        "n": len(clean), "auroc": round(auroc(d, l), 6),
        "caveat": ("post-hoc exclusion on the observed test split; descriptive "
                   "sensitivity analysis, not a corrected result")}
    detail["edit_size"] = edit_size_analysis(ev, meta, "sbg_v5")

    d, l, c = vectors(ev, "sbg_v5")
    nf = label_shuffle_noise_floor(d, l, c, n_shuffles=args.shuffles, seed=SEED)
    detail["noise_floor_sbg_v5_evaluable"] = {"n_shuffles": args.shuffles,
                                              "result": nf}

    for rid, val, n in (
            ("v6test_evaluable_sbg_v5_excluding_entry_mismatch",
             detail["sbg_v5_excluding_entry_mismatch"]["auroc"], len(clean)),
            ("v6test_edit_size_alone_auroc",
             detail["edit_size"].get("edit_size_alone_auroc"), len(ev)),
            ("v6test_edit_size_reversed_auroc",
             detail["edit_size"].get("edit_size_reversed_auroc"), len(ev)),
            ("v6test_edit_size_stratified_sbg_v5",
             detail["edit_size"].get("stratified_auroc"), len(ev))):
        record(rid, val, n, [pairs_p, audit_p], "output_free_v6", "test",
               "observed_possibly_contaminated",
               "independently_recomputed_historical_sensitivity")

    result = {"revision": revision, "seed": SEED, "reproduction": reproduced,
              "v6test": detail}

    if not args.no_write:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "audit_recompute.json").write_text(
            json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
        (out_dir / "results_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(json.dumps({"reproduction": reproduced,
                      "denominators": detail["denominators"],
                      "entry_mismatch": corr["n_structural_mismatch"],
                      "naive_name_inequality": corr["n_name_inequality_naive"],
                      "sbg_v5_excl_mismatch": detail["sbg_v5_excluding_entry_mismatch"],
                      "edit_size": {k: v for k, v in detail["edit_size"].items()
                                    if k != "bins"}},
                     indent=2))
    if failures:
        print("REPRODUCTION FAILED:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

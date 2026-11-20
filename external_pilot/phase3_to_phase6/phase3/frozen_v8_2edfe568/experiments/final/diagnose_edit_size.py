"""Diagnostic: why does reversed edit size beat SBG?  (train/dev/v8-dev only; refuses test.)

Tests, with independent re-implementations where possible:
  D1  metric correctness: brute-force O(n^2) AUROC vs sbg.statistics.auroc
  D2  orientation/pairing: edit size recomputed three ways (canonical AST-line diff,
      raw text-line diff, raw character diff); forward vs reversed AUROC
  D3  label construction: label is a deterministic function of transformation family
      (SC-* => CHANGED, SP-* => EQUIVALENT); edit-size distribution per family
  D4  size-controlled SBG performance: stratified (within exact edit-size) AUROC and
      a size-matched subset; cluster bootstrap by base program
  D5  does SBG itself track edit size? Spearman(SBG, size) within each label
  D6  per-family SBG distance and detection rate at frozen tau*

    python3 experiments/final/diagnose_edit_size.py
"""
from __future__ import annotations

import difflib
import json
import math
import pathlib
import random
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from experiments.final.build_paper_evidence import RUNS, DATASETS, valid_rows, jl, src   # noqa: E402
from experiments.final.edit_size_analysis import _edit_size                            # noqa: E402
from sbg.statistics import auroc                                                       # noqa: E402

OUT = REPO / "artifacts" / "paper_evidence" / "DIAGNOSTIC_EDIT_SIZE.json"
TAU = json.loads((REPO / "artifacts/final/THRESHOLD_FROZEN.json").read_text())["tau_star"]


def brute_auroc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    w = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return w / (len(pos) * len(neg))


def raw_line_diff(a, b):
    n = 0
    for l in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0):
        if l.startswith(("+", "-")) and not l.startswith(("+++", "---")):
            n += 1
    return n


def char_diff(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal")


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 3:
        return None
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return round(num / den, 4) if den else None


def stratified_auroc(scores, labels, strata):
    """Pooled within-stratum Mann-Whitney: only compares CHANGED vs EQUIVALENT pairs of equal edit size."""
    g = defaultdict(lambda: ([], []))
    for s, l, k in zip(scores, labels, strata):
        g[k][l].append(s)
    num = den = 0.0
    for neg, pos in g.values():
        if neg and pos:
            for p in pos:
                for n in neg:
                    num += 1.0 if p > n else 0.5 if p == n else 0.0
            den += len(pos) * len(neg)
    return (num / den if den else None), den


def boot_stratified(scores, labels, strata, clusters, n=1000, seed=42):
    rng = random.Random(seed)
    by = defaultdict(list)
    for i, c in enumerate(clusters):
        by[c].append(i)
    keys = sorted(by)
    vals = []
    for _ in range(n):
        idx = [i for c in (rng.choice(keys) for _ in keys) for i in by[c]]
        a, _d = stratified_auroc([scores[i] for i in idx], [labels[i] for i in idx], [strata[i] for i in idx])
        if a is not None:
            vals.append(a)
    vals.sort()
    if len(vals) < 50:
        return None
    return [round(vals[int(0.025 * len(vals))], 6), round(vals[int(0.975 * len(vals)) - 1], 6), len(vals)]


def diagnose(run):
    r = RUNS[run]
    assert r["split"] != "test"
    meta = {}
    for sp in ("train", "dev", "val"):
        for m in jl(f"{DATASETS[r['dataset']]}/pairs_{sp}.jsonl"):
            meta[m["pair_id"]] = m
    rows = valid_rows(run)
    y = [x["label"] for x in rows]
    cl = [x["base_id"] for x in rows]
    sbg = [x["scores"]["sbg_v5"] for x in rows]
    ast_sz, raw_sz, chr_sz = [], [], []
    for x in rows:
        m = meta[x["pair_id"]]
        a = (REPO / m["base_path"]).read_text()
        b = (REPO / m["variant_path"]).read_text()
        ast_sz.append(_edit_size(m["base_path"], m["variant_path"]))
        raw_sz.append(raw_line_diff(a, b))
        chr_sz.append(char_diff(a, b))
    out = {"run": run, "n": len(rows), "sources": {"pairs": src(r["pairs"]), "audit": src(r["audit"])}}

    # D1 metric correctness
    out["D1_metric_check"] = {
        "sbg_v5": {"library": round(auroc(sbg, y), 6), "brute_force": round(brute_auroc(sbg, y), 6)},
        "neg_ast_size": {"library": round(auroc([-s for s in ast_sz], y), 6),
                         "brute_force": round(brute_auroc([-s for s in ast_sz], y), 6)}}

    # D2 orientation and measurement-independence
    out["D2_edit_size_measures"] = {
        name: {"forward_auroc_size_predicts_changed": round(auroc([float(s) for s in v], y), 6),
               "reversed_auroc": round(auroc([-float(s) for s in v], y), 6),
               "mean_changed": round(sum(s for s, l in zip(v, y) if l) / sum(y), 3),
               "mean_equivalent": round(sum(s for s, l in zip(v, y) if not l) / (len(y) - sum(y)), 3)}
        for name, v in (("canonical_ast_lines", ast_sz), ("raw_text_lines", raw_sz), ("raw_char_edit", chr_sz))}

    # D3 label construction
    fam = defaultdict(lambda: {"labels": set(), "sizes": [], "sbg": [], "n": 0})
    for x, s in zip(rows, ast_sz):
        f = fam[x["transformation_type"]]
        f["labels"].add(x["label"]); f["sizes"].append(s); f["sbg"].append(x["scores"]["sbg_v5"]); f["n"] += 1
    d3 = {}
    for t, f in sorted(fam.items()):
        sz = sorted(f["sizes"])
        d3[t] = {"label": sorted(f["labels"]), "n": f["n"], "edit_size_median": sz[len(sz) // 2],
                 "edit_size_mean": round(sum(sz) / len(sz), 2), "edit_size_max": sz[-1],
                 "frac_size_le2": round(sum(1 for s in sz if s <= 2) / len(sz), 3),
                 "sbg_mean": round(sum(f["sbg"]) / f["n"], 4),
                 "detect_rate_at_tau": round(sum(1 for s in f["sbg"] if s > TAU) / f["n"], 3)}
    out["D3_by_family"] = d3
    out["D3_label_is_function_of_family"] = all(len(f["labels"]) == 1 for f in fam.values())
    out["D3_families_with_label"] = {"CHANGED": [t for t, f in fam.items() if 1 in f["labels"]],
                                     "EQUIVALENT": [t for t, f in fam.items() if 0 in f["labels"]]}

    # D4 size-controlled SBG performance
    a, den = stratified_auroc(sbg, y, ast_sz)
    out["D4_size_controlled"] = {
        "stratified_exact_size_auroc_sbg_v5": None if a is None else round(a, 6),
        "n_cross_label_comparisons": den,
        "ci95_cluster_bootstrap_1000": boot_stratified(sbg, y, ast_sz, cl),
        "fraction_of_all_cross_label_pairs_retained": round(den / (sum(y) * (len(y) - sum(y))), 4),
        "note": "compares only CHANGED vs EQUIVALENT pairs with identical canonical edit size; "
                "edit size alone gives AUROC 0.5 by construction in this estimator"}
    sub = [i for i, s in enumerate(ast_sz) if 1 <= s <= 5]
    ys = [y[i] for i in sub]
    if sum(ys) >= 5 and len(ys) - sum(ys) >= 5:
        out["D4_size_controlled"]["subset_size_1_to_5"] = {
            "n": len(sub), "n_changed": sum(ys), "n_equivalent": len(ys) - sum(ys),
            "sbg_auroc": round(auroc([sbg[i] for i in sub], ys), 6),
            "edit_size_reversed_auroc": round(auroc([-float(ast_sz[i]) for i in sub], ys), 6)}

    # D5 does SBG track size?
    out["D5_spearman_sbg_vs_edit_size"] = {
        "within_changed": spearman([s for s, l in zip(sbg, y) if l], [s for s, l in zip(ast_sz, y) if l]),
        "within_equivalent": spearman([s for s, l in zip(sbg, y) if not l], [s for s, l in zip(ast_sz, y) if not l]),
        "all": spearman(sbg, [float(s) for s in ast_sz])}

    # D6 family-restricted comparisons: SBG on same-family label contrast is impossible (labels are family-determined)
    eq_small = [i for i in range(len(rows)) if y[i] == 0 and ast_sz[i] <= 2]
    out["D6_equivalent_pairs_with_size_le2"] = {
        "n": len(eq_small), "of_equivalent": len(y) - sum(y),
        "families": sorted({rows[i]["transformation_type"] for i in eq_small}),
        "sbg_mean_these": round(sum(sbg[i] for i in eq_small) / max(1, len(eq_small)), 4),
        "sbg_mean_all_changed": round(sum(s for s, l in zip(sbg, y) if l) / sum(y), 4)}
    return out


def main():
    res = {"purpose": "Decompose why reversed edit size (AUROC ~0.85-0.96) outperforms SBG V5 (~0.67-0.74).",
           "scope": "v6 train, v6 dev, v8 dev only; no test split read",
           "runs": {k: diagnose(k) for k in ("v6train_v7", "v6dev_v7", "v8dev_v8_rescore")}}
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    for k, v in res["runs"].items():
        print("==", k, v["n"])
        print(" D1", v["D1_metric_check"])
        print(" D2", {n: (m["forward_auroc_size_predicts_changed"], m["reversed_auroc"], m["mean_changed"], m["mean_equivalent"])
                      for n, m in v["D2_edit_size_measures"].items()})
        print(" D3 label fn of family:", v["D3_label_is_function_of_family"])
        for t, f in v["D3_by_family"].items():
            print("   ", t, f["label"], f["n"], "med", f["edit_size_median"], "mean", f["edit_size_mean"], "le2", f["frac_size_le2"],
                  "sbg", f["sbg_mean"], "det", f["detect_rate_at_tau"])
        print(" D4", v["D4_size_controlled"])
        print(" D5", v["D5_spearman_sbg_vs_edit_size"])
        print(" D6", v["D6_equivalent_pairs_with_size_le2"])


if __name__ == "__main__":
    main()

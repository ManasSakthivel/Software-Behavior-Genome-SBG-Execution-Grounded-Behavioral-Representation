#!/usr/bin/env python3
"""ab05 -- edit-size confounding diagnostics on saved dev/train predictions (EXP-A4R-006).  Own stdlib code; reads saved predictions only.

(1) composition of matched sets: number of sets where edit(CHANGED partner) >  / == / < edit(EQUIVALENT partner)
(2) exact-edit-stratified AUROC (only cross-label pairs with IDENTICAL edit size; same semantics as eval_lib.stratified_auroc_exact_edit, own code) + program-cluster bootstrap CI
(3) matched-set concordance (strict and ties-half), compared with the trivial 'edit' predictor
"""
from __future__ import annotations

import collections
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import ab02_independent_dev_stats as S  # noqa: E402

WP = HERE.parent
OUT = WP / "raw" / "EXP-A4R-006"
OUT.mkdir(parents=True, exist_ok=True)
METHODS = ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal", "edit", "LR_EX", "LR_EXx", "forest|RF_d4|EXx", "pathspectra|shape|covset|max", "trace_len_mean",
           "traceseq|cre|full|kgram4|max", "static|tce_ast", "valuespectra|entry_exit|full|raw|max", "output_indep|frac40", "oracle|frac11"]


def exact_edit_auroc(s, y, e):
    g = collections.defaultdict(lambda: ([], []))
    for a, b, c in zip(s, y, e):
        g[c][b].append(a)
    num = den = 0.0
    for neg, pos in g.values():
        for a in pos:
            for b in neg:
                num += 1.0 if a > b else 0.5 if a == b else 0.0
        den += len(pos) * len(neg)
    return (num / den if den else float("nan")), den


def main():
    out = {}
    for pop in ("v9c_dev", "v9c_train"):
        meta, cols, rows, info = S.load_pop(pop)
        pair, y, base, group = ([r[i] for r in rows] for i in range(4))
        e = cols["edit"]
        gm = collections.defaultdict(dict)
        for i, g in enumerate(group):
            gm[g][y[i]] = i
        gt = eq = lt = 0
        diffs = []
        for g, d in gm.items():
            if 0 in d and 1 in d:
                dd = e[d[1]] - e[d[0]]
                diffs.append(dd)
                gt += dd > 0
                eq += dd == 0
                lt += dd < 0
        res = {"n_sets": len(diffs), "edit_changed_gt_equiv": gt, "equal": eq, "lt": lt, "mean_edit_diff": sum(diffs) / len(diffs), "methods": {}}
        keys = sorted(set(base))
        by = collections.defaultdict(list)
        for i, b in enumerate(base):
            by[b].append(i)
        B = 1000
        rng = random.Random(S.SEED + 11)
        draws = [[rng.choice(keys) for _ in keys] for _ in range(B)]
        for m in METHODS:
            if m not in cols:
                continue
            s = cols[m]
            val, den = exact_edit_auroc(s, y, e)
            bs = []
            for dr in draws:
                idx = [i for k in dr for i in by[k]]
                v, _ = exact_edit_auroc([s[i] for i in idx], [y[i] for i in idx], [e[i] for i in idx])
                if v == v:
                    bs.append(v)
            conc = tie = tot = 0
            for g, d in gm.items():
                if 0 in d and 1 in d:
                    tot += 1
                    conc += s[d[1]] > s[d[0]]
                    tie += s[d[1]] == s[d[0]]
            res["methods"][m] = {"exact_edit_auroc": val, "n_cross_pairs_equal_edit": den, "ci95": [S.pct(bs, .025), S.pct(bs, .975)], "pooled_auroc": S.auroc(s, y),
                                 "matched_strict": conc / tot, "matched_ties_half": (conc + tie / 2) / tot, "matched_n": tot}
        out[pop] = res
        print(pop, {k: v for k, v in res.items() if k != "methods"})
        for m, v in res["methods"].items():
            print(f"  {m:36s} pooled={v['pooled_auroc']:.3f} exactEdit={v['exact_edit_auroc']:.3f} [{v['ci95'][0]:.3f},{v['ci95'][1]:.3f}] n={int(v['n_cross_pairs_equal_edit'])} matched={v['matched_strict']:.3f}/{v['matched_ties_half']:.3f}")
    (OUT / "edit_confounding.json").write_text(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()

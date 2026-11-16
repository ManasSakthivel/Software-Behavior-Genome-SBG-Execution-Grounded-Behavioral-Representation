#!/usr/bin/env python3
"""EXP-A3-014: edit-size confound analysis. (1) edit-size distribution by label; (2) AUROC within edit-size QUANTILE strata (terciles of the pooled edit distribution);
(3) exact-edit stratified AUROC (repo-style) ; (4) matched-set tie/direction decomposition: in how many matched sets does CH have larger / equal / smaller edit than its EQ partner,
and concordance of every predictor inside matched sets (ties = 0.5); (5) AUROC of V5 within sets where edit is TIED (edit cannot discriminate).
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_014_edit_strata.py"""
import csv, json, pathlib, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L
rows_out = []; summ = {}
for design in ("v10_test", "v9c_val"):   # v8_test has no matched sets (unmatched design)
    if design == "v10_test": _, pop = L.build_v10(with_static=False)
    elif design == "v9c_val": _, pop = L.build_v9c("val")
    else: _, pop = L.build_v8_test()
    preds = ["sbg_v5", "sbg_state", "edit", "coverage_size", "exception_fraction"]
    ed = sorted(r["edit"] for r in pop); q1, q2 = ed[len(ed) // 3], ed[2 * len(ed) // 3]
    strata = {"T1 (edit<=%g)" % q1: lambda e: e <= q1, "T2 (%g<edit<=%g)" % (q1, q2): lambda e: q1 < e <= q2, "T3 (edit>%g)" % q2: lambda e: e > q2}
    s = {"n": len(pop), "mean_edit": {lab: round(sum(r["edit"] for r in pop if r["label"] == lab) / sum(1 for r in pop if r["label"] == lab), 3) for lab in (0, 1)},
         "median_edit": {lab: sorted(r["edit"] for r in pop if r["label"] == lab)[sum(1 for r in pop if r["label"] == lab) // 2] for lab in (0, 1)}, "strata": {}}
    for name, f in strata.items():
        sub = [r for r in pop if f(r["edit"])]; y = [r["label"] for r in sub]
        d = {"n": len(sub), "n_changed": sum(y)}
        for p in preds: d[p] = round(L.auroc([r["scores"][p] for r in sub], y), 4) if 0 < sum(y) < len(y) else None
        s["strata"][name] = d
        rows_out.append({"design": design, "stratum": name, **d})
    # exact-edit stratified
    g = collections.defaultdict(lambda: ([], []))
    for r in pop: g[r["edit"]][r["label"]].append(r)
    ex = {}
    for p in preds:
        num = den = 0.0
        for neg, pos in g.values():
            for a in pos:
                for b in neg:
                    num += 1 if a["scores"][p] > b["scores"][p] else .5 if a["scores"][p] == b["scores"][p] else 0
            den += len(pos) * len(neg)
        ex[p] = round(num / den, 4)
    s["exact_edit_stratified"] = ex; s["n_cross_label_within_same_edit"] = int(den)
    # matched-set decomposition
    sets = collections.defaultdict(dict)
    for r in pop: sets[r["group"]][r["label"]] = r
    dirs = collections.Counter(("CH>EQ" if v[1]["edit"] > v[0]["edit"] else "tie" if v[1]["edit"] == v[0]["edit"] else "CH<EQ") for v in sets.values() if len(v) == 2)
    conc = {}
    for p in preds:
        c = [1 if v[1]["scores"][p] > v[0]["scores"][p] else .5 if v[1]["scores"][p] == v[0]["scores"][p] else 0 for v in sets.values() if len(v) == 2]
        conc[p] = round(sum(c) / len(c), 4)
    tie_sets = [v for v in sets.values() if len(v) == 2 and v[1]["edit"] == v[0]["edit"]]
    conc_tie = {p: round(sum(1 if v[1]["scores"][p] > v[0]["scores"][p] else .5 if v[1]["scores"][p] == v[0]["scores"][p] else 0 for v in tie_sets) / len(tie_sets), 4) for p in preds} if tie_sets else None
    s["matched_set_edit_direction"] = dict(dirs); s["matched_set_concordance_all"] = conc; s["matched_set_concordance_edit_tied_sets"] = conc_tie; s["n_sets"] = len(sets)
    # within-set edit difference (CH - EQ) distribution
    dd = sorted(v[1]["edit"] - v[0]["edit"] for v in sets.values() if len(v) == 2); s["within_set_edit_diff_CH_minus_EQ"] = {"min": dd[0], "median": dd[len(dd) // 2], "max": dd[-1], "mean": round(sum(dd) / len(dd), 3)}
    summ[design] = s
    print(design, json.dumps(s, indent=1))
(L.PKG / "results/raw/EXP-A3-014").mkdir(parents=True, exist_ok=True)
(L.PKG / "results/raw/EXP-A3-014/edit_strata.json").write_text(json.dumps(summ, indent=1))
with open(L.PKG / "results/tables/EXP-A3-014_edit_quantile_strata.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0])); w.writeheader(); w.writerows(rows_out)
with open(L.PKG / "results/tables/EXP-A3-014_matched_set_concordance.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["design", "predictor", "pooled_auroc_ref", "matched_set_concordance", "concordance_in_edit_tied_sets", "exact_edit_stratified_auroc", "n_sets", "sets_CH_edit_gt_EQ", "sets_tie", "sets_CH_lt_EQ"])
    for dsg, s in summ.items():
        for p in s["matched_set_concordance_all"]:
            w.writerow([dsg, p, "", s["matched_set_concordance_all"][p], (s["matched_set_concordance_edit_tied_sets"] or {}).get(p, ""), s["exact_edit_stratified"][p], s["n_sets"],
                        s["matched_set_edit_direction"].get("CH>EQ", 0), s["matched_set_edit_direction"].get("tie", 0), s["matched_set_edit_direction"].get("CH<EQ", 0)])

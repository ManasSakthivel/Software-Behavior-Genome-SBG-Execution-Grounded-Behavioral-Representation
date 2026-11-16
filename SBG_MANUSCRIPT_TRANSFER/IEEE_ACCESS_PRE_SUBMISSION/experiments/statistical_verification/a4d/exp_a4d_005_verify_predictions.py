#!/usr/bin/env python3
"""A4D Phase 2: verification of A4C's head-to-head benchmark predictions.   Usage:
   python exp_a4d_005_verify_predictions.py --pred-root results/raw/EXP-A4C-003 --pops v9c_dev --exp EXP-A4D-005 [--eval-glob 'EXP-A4C-*/eval_{pop}.json']

Consumes ONLY: A4C prediction files + meta.json, configs/populations, raw dataset metadata (via a4dlib) and (for comparison of reported numbers) A4C's eval json.
Never imports A4/A4C code.  Outputs under results/raw/<exp>/, tables under results/tables/<exp>_*.
"""
import argparse
import csv
import glob
import hashlib
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4dlib as L  # noqa: E402
import a4d_analysis as A  # noqa: E402

RAWROOT = L.PKG / "results" / "raw"
TABLES = L.PKG / "results" / "tables"
EXC3 = ["exception_fraction", "call_count", "coverage_size"]
EXX3 = ["n_functions", "n_events", "trace_len_mean"]
REFS = ["sbg_state", "sbg_v3", "sbg_temporal"]
ORACLE_PREFIX = ("oracle__", "changeguard_cmp__")


def stem(method):
    return method.replace("|", "__")


def load_pred_file(path):
    d = json.loads(open(path).read())
    return d


def pop_rows(name, excluded):
    rows = L.load_pop(name)
    rows = [r for r in rows if r["base_id"] not in excluded]
    return sorted(rows, key=lambda r: r["pair_id"])


def load_columns(pred_dir, rows, methods, report):
    """Return {method_stem: [score aligned with rows]} and fill `report` with consistency findings."""
    ids = [r["pair_id"] for r in rows]
    idset = set(ids)
    cols, findings = {}, {"missing_file": [], "pair_set_mismatch": [], "label_mismatch": [], "group_mismatch": [], "base_mismatch": [], "nonfinite": [],
                          "duplicate_pairs": [], "orientation_not_declared": [], "constant_scores": []}
    by_id = {r["pair_id"]: r for r in rows}
    for m in methods:
        p = os.path.join(pred_dir, m + ".json")
        if not os.path.exists(p):
            findings["missing_file"].append(m)
            continue
        d = load_pred_file(p)
        if d.get("orientation") != "higher=CHANGED":
            findings["orientation_not_declared"].append((m, d.get("orientation")))
        got = [x["pair_id"] for x in d["rows"]]
        if len(got) != len(set(got)):
            findings["duplicate_pairs"].append(m)
        if set(got) != idset:
            findings["pair_set_mismatch"].append((m, len(set(got) - idset), len(idset - set(got))))
            continue
        sc = {}
        for x in d["rows"]:
            r = by_id[x["pair_id"]]
            if x["label"] != r["label"]:
                findings["label_mismatch"].append((m, x["pair_id"]))
            if x["group"] != r["group"]:
                findings["group_mismatch"].append((m, x["pair_id"]))
            if x["base_id"] != r["base_id"]:
                findings["base_mismatch"].append((m, x["pair_id"]))
            v = x["score"]
            if v is None or (isinstance(v, float) and not math.isfinite(v)):
                findings["nonfinite"].append((m, x["pair_id"]))
                v = float("nan")
            sc[x["pair_id"]] = v
        vec = [sc[i] for i in ids]
        if any(isinstance(v, float) and math.isnan(v) for v in vec):
            continue
        if len(set(vec)) == 1:
            findings["constant_scores"].append(m)
        cols[m] = vec
    report.update({k: (v if len(v) < 50 else v[:50] + [f"... {len(v)} total"]) for k, v in findings.items()})
    report["n_methods_loaded"] = len(cols)
    report["n_rows"] = len(ids)
    return cols


def check_meta_and_freeze(root, meta, pops, report):
    """(a) provenance: all methods share code_sha / frozen-config sha; frozen config + models predate held-out predictions."""
    mm = meta["methods"]
    report["n_methods_meta"] = len(mm)
    report["code_sha256_set"] = sorted({v["code_sha256"] for v in mm.values()})
    report["frozen_config_sha256_set"] = sorted({v["frozen_config_sha256"] for v in mm.values()})
    fc = L.PKG / meta["frozen_config"]
    if fc.exists():
        report["frozen_config_file_sha256"] = hashlib.sha256(fc.read_bytes()).hexdigest()
        report["frozen_config_sha_matches_meta"] = report["frozen_config_file_sha256"] in report["frozen_config_sha256_set"]
        report["frozen_config_mtime"] = os.path.getmtime(fc)
        mp = fc.parent / "models.pkl"
        report["models_pkl_mtime"] = os.path.getmtime(mp) if mp.exists() else None
        later = {}
        for pop in pops:
            if pop in ("v10_test", "v9c_val"):
                d = os.path.join(root, "predictions", pop)
                if os.path.isdir(d):
                    mt = [os.path.getmtime(os.path.join(d, f)) for f in os.listdir(d) if f.endswith(".json")]
                    later[pop] = {"first_prediction_mtime": min(mt), "last_prediction_mtime": max(mt), "n": len(mt),
                                  "frozen_config_older_than_all_predictions": report["frozen_config_mtime"] < min(mt),
                                  "models_pkl_older_than_all_predictions": (report["models_pkl_mtime"] or 0) < min(mt)}
        report["heldout_prediction_timing"] = later
    report["orientation_set"] = sorted({v["orientation"] for v in mm.values()})
    report["privileged_methods"] = sorted(k for k, v in mm.items() if v.get("privileged_output_reading"))
    report["roles"] = {r: sum(1 for v in mm.values() if v["role"] == r) for r in sorted({v["role"] for v in mm.values()})}


def recompute_train_thresholds(train_cols, ytr, meta):
    out = {}
    for m, vec in train_cols.items():
        thr, j = L.youden(vec, ytr)
        rep = meta["methods"].get(m, {}).get("train_threshold_youden")
        # Youden J at A4C's own threshold, to separate tie-breaking differences from genuine errors
        jr = None
        if rep is not None:
            pr = L.prf(vec, ytr, rep)
            jr = pr["recall"] - pr["fpr"]
        out[m] = {"thr_a4d": thr, "J_a4d": j, "thr_a4c": rep, "J_at_a4c_thr": jr, "abs_diff_thr": None if rep is None else abs(thr - rep),
                  "J_equal": None if jr is None else abs(jr - j) < 1e-9}
    return out


def refit_check(meta, tr_cols, ytr, cols, y):
    """Independent refit of every fitted-combiner method (features given in meta config) with A4D's own logistic code; compare held-out score ordering."""
    res = {}
    for m, v in meta["methods"].items():
        cfg = v.get("config")
        feats = cfg.get("features") if isinstance(cfg, dict) else None
        if m in ("LR_EX", "LR_X", "LR_EXx", "LR_Xx"):
            feats = {"LR_EX": ["edit"] + EXC3, "LR_X": EXC3, "LR_EXx": ["edit"] + EXC3 + EXX3, "LR_Xx": EXC3 + EXX3}[m]
        if not feats or m not in cols:
            continue
        fs = [stem(f) for f in feats]
        if any(f not in tr_cols or f not in cols for f in fs):
            res[m] = {"status": "feature_columns_missing", "features": fs}
            continue
        row = {"features": fs}
        for tag, l2 in (("pen2", 2.0), ("pen1", 1.0)):
            mod = L.fit_logistic_newton([[tr_cols[f][i] for f in fs] for i in range(len(ytr))], ytr, l2=l2)
            sc = [L.logit_apply(mod, [cols[f][i] for f in fs]) for i in range(len(y))]
            row[tag] = {"auroc_refit": L.auroc(sc, y), "auroc_a4c": L.auroc(cols[m], y), "abs_diff_auroc": abs(L.auroc(sc, y) - L.auroc(cols[m], y))}
            # Spearman correlation between refit and A4C score
            r1, r2 = L.midranks(sc), L.midranks(cols[m])
            n = len(r1)
            m1, m2 = sum(r1) / n, sum(r2) / n
            cov = sum((a - m1) * (b - m2) for a, b in zip(r1, r2))
            den = math.sqrt(sum((a - m1) ** 2 for a in r1) * sum((b - m2) ** 2 for b in r2))
            row[tag]["spearman_vs_a4c"] = cov / den if den else None
        res[m] = row
    return res


def to_float(x):
    return float(x) if x is not None else None


def compare_reported(pop, a4c_eval, eng, methods, singles, cmp, thr_a4c, rows, comp):
    """Compare each number A4C reports (eval json) with A4D's recomputation.  Appends to `comp`."""
    def add(m, q, mine, theirs, tol=1e-6):
        if mine is None or theirs is None:
            return
        comp.append({"population": pop, "method": m, "quantity": q, "a4d": mine, "a4c": theirs, "abs_diff": abs(mine - theirs), "tol": tol})
    for m in methods:
        rep = a4c_eval["methods"].get(m)
        if rep is None:
            continue
        s = singles[m]
        add(m, "auroc", s["auroc"], rep.get("auroc"))
        add(m, "auroc_ci_lo", s["ci95"][0], rep["auroc_ci95"][0])
        add(m, "auroc_ci_hi", s["ci95"][1], rep["auroc_ci95"][1])
        add(m, "auprc", s["auprc"], rep.get("auprc"))
        det = rep.get("detail", {})
        add(m, "cliff_delta", s["cliffs_delta"], det.get("cliff_delta"))
        if "exact_edit_auroc" in det and det["exact_edit_auroc"] is not None:
            add(m, "exact_edit_auroc", s["exact_edit_auroc"]["auroc"], det["exact_edit_auroc"])
            add(m, "exact_edit_n_cross", s["exact_edit_auroc"]["n_cross_pairs"], det.get("exact_edit_n_cross"))
        for t, q in zip(s["terciles"], det.get("edit_quantile_strata", [])):
            add(m, f"tercile{t['stratum']}_auroc", t["auroc"], q.get("auroc"))
            add(m, f"tercile{t['stratum']}_n", t["n"], q.get("n"))
        mc = det.get("matched_concordance")
        if mc and "matched_concordance" in s:
            add(m, "matched_concordance", s["matched_concordance"]["conc"], mc["concordance"])
            add(m, "matched_concordance_ci_lo", s["matched_concordance"]["ci95"][0], mc["ci95"][0])
            add(m, "matched_concordance_ci_hi", s["matched_concordance"]["ci95"][1], mc["ci95"][1])
        if "perm_p_one_sided_vs_0.5" in s and det.get("perm_p_one_sided_vs_0.5") is not None:
            add(m, "perm_p_one_sided", s["perm_p_one_sided_vs_0.5"], det["perm_p_one_sided_vs_0.5"], 2e-3)  # different RNG stream is possible
        thr_rep = det.get("threshold_train_youden")
        if thr_rep is not None:
            pr = L.prf(eng.cols[m], eng.d.y, thr_rep)
            for q in ("precision", "recall", "f1", "fpr"):
                if q in det.get("prf", {}):
                    add(m, f"prf_{q}@a4c_thr", pr[q], det["prf"][q])
            for q in ("tp", "fp", "fn", "tn"):
                if q in det.get("prf", {}):
                    add(m, f"prf_{q}@a4c_thr", pr[q], det["prf"][q])
        dv = rep.get("delta_v5_minus_method")
        if dv and m in cmp:
            c = cmp[m]
            add(m, "delta_v5_minus_method", c["delta"], dv["delta"])
            add(m, "delta_ci_lo", c["ci95"][0], dv["ci95"][0])
            add(m, "delta_ci_hi", c["ci95"][1], dv["ci95"][1])
            comp.append({"population": pop, "method": m, "quantity": "delta_p_two_sided(plain|corrected)", "a4d": c["p_boot_plain"], "a4c": dv["p_two_sided"],
                         "abs_diff": min(abs(c["p_boot_plain"] - dv["p_two_sided"]), abs(c["p_boot_corrected"] - dv["p_two_sided"])), "tol": 2e-3})
        pp = det.get("per_program_auroc")
        if pp:
            mine = L.per_program_auroc(eng.d, eng.cols[m])
            for k, v in pp.items():
                add(m, f"per_program_auroc[{k}]", mine.get(k), v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-root", required=True)
    ap.add_argument("--pops", nargs="+", required=True)
    ap.add_argument("--exp", required=True)
    ap.add_argument("--eval-glob", default="EXP-A4C-*/eval_{pop}.json")
    ap.add_argument("--no-recompute-all", action="store_true")
    ap.add_argument("--fast", action="store_true", help="skip heavy family analysis (testing)")
    args = ap.parse_args()
    t0 = time.time()
    root = args.pred_root if os.path.isabs(args.pred_root) else str(L.PKG / args.pred_root)
    OUT = RAWROOT / args.exp
    OUT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    meta = json.loads(open(os.path.join(root, "predictions", "meta.json")).read())
    excluded = set(meta.get("train_excluded_programs", []))
    mm = meta["methods"]
    report = {"pred_root": root, "pops": args.pops, "meta_experiment": meta.get("experiment")}
    check_meta_and_freeze(root, meta, args.pops, report)
    methods = sorted(mm)

    # ---- train predictions: thresholds / refit basis
    train_rows = pop_rows("v9c_train", excluded)
    ytr = [r["label"] for r in train_rows]
    rep_tr = {}
    tr_cols = load_columns(os.path.join(root, "predictions", "v9c_train"), train_rows, methods, rep_tr)
    report["train_consistency"] = rep_tr
    report["train_methods_missing_vs_meta"] = [m for m in methods if m not in tr_cols]
    thr_check = recompute_train_thresholds(tr_cols, ytr, meta)
    report["train_threshold_check"] = {"n": len(thr_check), "n_thr_equal_1e-9": sum(1 for v in thr_check.values() if v["abs_diff_thr"] is not None and v["abs_diff_thr"] < 1e-9),
                                       "n_J_equal": sum(1 for v in thr_check.values() if v["J_equal"]), "n_thr_differ_but_J_equal": sum(1 for v in thr_check.values() if (v["abs_diff_thr"] or 0) >= 1e-9 and v["J_equal"]),
                                       "n_J_differ": sum(1 for v in thr_check.values() if v["J_equal"] is False),
                                       "J_differ_methods": [m for m, v in thr_check.items() if v["J_equal"] is False][:50]}
    # reported train/dev AUROC check
    tr_auc = {m: L.auroc(v, ytr) for m, v in tr_cols.items()}
    report["train_auroc_max_abs_diff"] = max(abs(tr_auc[m] - mm[m]["train_auroc"]) for m in tr_auc if mm[m].get("train_auroc") is not None)
    thr = {m: v["thr_a4d"] for m, v in thr_check.items()}

    allpop = {}
    for pop in args.pops:
        print(f"=== {pop}", round(time.time() - t0, 1), flush=True)
        rows = pop_rows(pop, set())
        y = [r["label"] for r in rows]
        prep = {}
        pdir = os.path.join(root, "predictions", pop)
        cols = load_columns(pdir, rows, methods, prep)
        info = json.loads(open(os.path.join(pdir, "_population_info.json")).read()) if os.path.exists(os.path.join(pdir, "_population_info.json")) else {}
        prep["population_info"] = info
        prep["n_programs"] = len({r["base_id"] for r in rows})
        # extra predictions not in meta
        extra = sorted(f[:-5] for f in os.listdir(pdir) if f.endswith(".json") and not f.startswith("_") and f[:-5] not in mm)
        prep["prediction_files_not_in_meta"] = extra
        d = L.data_from_rows(rows)
        eng = A.Engine(d, cols)
        # ---- representatives (independent re-selection on dev)
        reps = {}
        sel_path = os.path.join(root, "..", "EXP-A4C-002", "selection.json")
        sel = json.loads(open(sel_path).read()) if os.path.exists(sel_path) else {}
        dev_rows = pop_rows("v9c_dev", set())
        dev_cols = load_columns(os.path.join(root, "predictions", "v9c_dev"), dev_rows, methods, {})
        ydev = [r["label"] for r in dev_rows]
        sel_check = {}
        for fam, v in sel.items():
            cands = [stem(c) if "|" in c else c for c in v["candidates"]]
            cands = [c for c in cands if c in dev_cols]
            if not cands:
                continue
            aucs = {c: L.auroc(dev_cols[c], ydev) for c in cands}
            best = max(aucs.values())
            winners = [c for c in cands if abs(aucs[c] - best) < 1e-12]
            rep_a4c = stem(v["representative"])
            sel_check[fam] = {"a4c_rep": rep_a4c, "a4d_argmax_dev": winners, "match": rep_a4c in winners, "tie": len(winners) > 1, "dev_auroc_a4d": best,
                              "dev_auroc_a4c": v["dev_auroc"]}
            reps[fam] = rep_a4c
        prep["representative_selection_check"] = sel_check
        # ---- recompute all metrics for every method
        t1 = time.time()
        singles = {}
        perm_set = set(reps.values()) | {"sbg_v5"} | set(REFS)
        for m in cols:
            s = {"auroc": eng.auroc(m), "ci95": L.pct_ci(eng.vec(m)), "ci95_alt_seed": L.pct_ci(eng.vec(m, True)), "auprc": L.auprc(cols[m], y),
                 "cliffs_delta": L.cliffs_delta(cols[m], y), "exact_edit_auroc": eng.strat_point(m, "edit"), "terciles": eng.tercile_table(m),
                 "matched_concordance": L.concordance_boot(L.matched_sets(d, cols[m]), None, d.K, eng.res), "n_unique": len(set(cols[m]))}
            if m in perm_set:
                s["perm_p_one_sided_vs_0.5"] = L.perm_label_auroc_p(d, cols[m])
            thr_m = thr.get(m)
            if thr_m is not None:
                s["prf_at_a4d_train_thr"] = {"thr": thr_m, **L.prf(cols[m], y, thr_m)}
            singles[m] = s
        print("  singles done", round(time.time() - t1, 1), flush=True)
        cmpall = {}
        if "sbg_v5" in cols:
            for m in cols:
                if m != "sbg_v5":
                    cmpall[m] = eng.compare("sbg_v5", m, full=False)
        # ---- (b) discrepancy vs A4C-reported
        comp = []
        evals = glob.glob(str(RAWROOT / args.eval_glob.format(pop=pop)))
        prep["a4c_eval_files"] = evals
        if evals:
            a4c_eval = json.loads(open(evals[0]).read())
            compare_reported(pop, a4c_eval, eng, [m for m in cols], singles, cmpall, None, rows, comp)
            # holm table reported
            hp = a4c_eval.get("holm_family_plan", {})
            prep["a4c_holm_m"] = hp.get("m")
            prep["a4c_holm_members"] = hp.get("members")
            prep["a4c_holm_p"] = hp.get("holm_p")
            prep["a4c_holm_raw_p"] = hp.get("raw_p")
        # ---- (c) family analysis with full inference
        fam_members = sorted(set(reps.values()))
        others_desc = [m for m in cols if m != "sbg_v5" and m in ("edit_rev", "edit") ] + [m for m in cols if m.startswith(ORACLE_PREFIX) or m.startswith("output_indep__")]
        full_others = [m for m in fam_members if m != "sbg_v5"]
        extra_desc = [m for m in dict.fromkeys(others_desc) if m not in full_others and m in cols]
        thr_pop = {m: thr[m] for m in thr if m in cols}
        analysis = None
        if not args.fast:
            subsets = {"dedup_AST": A.dedup_indices(rows)}
            if pop == "v9c_val":
                for sc in ("S1", "S2", "S3"):
                    subsets[f"clean_{sc}"] = A.clean_val_indices(rows, sc)
            analysis = A.analyse(pop, rows, cols, "sbg_v5", full_others + extra_desc, family=full_others, thr=thr_pop, subsets=subsets)
            # Holm with m=18 as A4C (alt)
            fam = {o: analysis["cmp"][o]["p_boot_corrected"] for o in full_others}
            analysis["holm_corrected_m18"] = L.holm(fam, m=18)
            analysis["holm_corrected_m19"] = L.holm(fam, m=19)
            analysis["fam_to_method"] = reps
        # ---- (d) incremental value
        inc = None
        if not args.fast and all(c in cols and c in tr_cols for c in ["edit"] + EXC3 + ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal"]):
            tr_c = {k: tr_cols[k] for k in tr_cols}
            xs = ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal"]
            for fam_ in ("valuespectra*", "traceseq_rename_robust*", "pathspectra*", "output_indep_frac40"):
                if fam_ in reps and reps[fam_] in cols:
                    xs.append(reps[fam_])
            have = lambda lst: all(c in cols and c in tr_cols for c in lst)  # noqa: E731
            bases = {"EX": ["edit"] + EXC3}
            if have(["edit"] + EXC3 + EXX3):
                bases["EXx"] = ["edit"] + EXC3 + EXX3
            bases["E"] = ["edit"]
            bases["state"] = ["sbg_state"]
            if "traceseq_rename_robust*" in reps:
                bases["traceseq_rr"] = [reps["traceseq_rename_robust*"]]
                bases["EX+state+traceseq_rr"] = ["edit"] + EXC3 + ["sbg_state", reps["traceseq_rename_robust*"]]
            inc = A.incremental_matrix(eng, tr_c, ytr, bases, xs)
            # Holm over the 8 deltas of the primary cell (base EX, LR) per plan section 6.3
            prim = [r for r in inc if r["base"] == "EX" and r["learner"] == "lr"]
            hp = L.holm({r["x"]: r["p_boot_corrected"] for r in prim}, m=8)
            for r in prim:
                r["holm_p_8"] = hp[r["x"]]
        # ---- refit check of fitted combiners (leak / consistency)
        refit = refit_check(meta, tr_cols, ytr, cols, y)
        # ---- (e) suspicious
        sus = []
        for m, s in singles.items():
            a = s["auroc"]
            role = mm[m]["role"] if m in mm else None
            if a >= 0.97:
                sus.append({"method": m, "auroc": a, "flag": "AUROC>=0.97", "role": role, "privileged": mm.get(m, {}).get("privileged_output_reading"),
                            "oracle_ceiling": role == "diag:oracle_ceiling" or m.startswith(ORACLE_PREFIX)})
            if a < 0.5:
                sus.append({"method": m, "auroc": a, "flag": "AUROC<0.5", "ci_hi": s["ci95"][1], "role": role, "significantly_below_0.5": s["ci95"][1] < 0.5})
            if s["n_unique"] <= 2:
                sus.append({"method": m, "auroc": a, "flag": f"only {s['n_unique']} distinct scores (ties dominate)", "role": role})
        allpop[pop] = {"consistency": prep, "singles": singles, "cmp_vs_v5_all_methods": cmpall, "analysis": analysis, "incremental": inc,
                       "refit_check": refit, "suspicious": sus, "n_discrepancy_rows": len(comp)}
        if comp:
            with open(TABLES / f"{args.exp}_{pop}_reported_vs_recomputed.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["population", "method", "quantity", "a4d", "a4c", "abs_diff", "tol"])
                w.writeheader()
                w.writerows(comp)
            bad = [c for c in comp if c["abs_diff"] > c["tol"]]
            allpop[pop]["reported_vs_recomputed"] = {"n_compared": len(comp), "max_abs_diff": max(c["abs_diff"] for c in comp), "n_over_tol": len(bad),
                                                      "over_tol_examples": bad[:60], "by_quantity_max": {q: max(c["abs_diff"] for c in comp if c["quantity"].split("[")[0] == q) for q in sorted({c["quantity"].split("[")[0] for c in comp})}}
        # per-method table
        with open(TABLES / f"{args.exp}_{pop}_recomputed_metrics.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["method", "role", "family", "privileged", "auroc", "ci_lo", "ci_hi", "auprc", "cliffs_delta", "f1@train_thr", "precision", "recall", "fpr", "delta_v5_minus_method", "d_ci_lo", "d_ci_hi", "p_boot_plain", "p_boot_corrected"])
            for m, s in sorted(singles.items(), key=lambda kv: -kv[1]["auroc"]):
                pr = s.get("prf_at_a4d_train_thr") or {}
                c = cmpall.get(m, {})
                w.writerow([m, mm.get(m, {}).get("role"), mm.get(m, {}).get("family"), mm.get(m, {}).get("privileged_output_reading"), round(s["auroc"], 6),
                            round(s["ci95"][0], 6), round(s["ci95"][1], 6), round(s["auprc"], 6), round(s["cliffs_delta"], 6), round(pr.get("f1", float("nan")), 6),
                            round(pr.get("precision", float("nan")), 6), round(pr.get("recall", float("nan")), 6), round(pr.get("fpr", float("nan")), 6),
                            round(c.get("delta", float("nan")), 6), *(round(v, 6) for v in c.get("ci95", [float("nan")] * 2)), c.get("p_boot_plain"), c.get("p_boot_corrected")])
        (OUT / f"{pop}_verification.json").write_text(json.dumps(allpop[pop], indent=1, default=str))
        print(pop, "written", round(time.time() - t0, 1), flush=True)
    report["thresholds"] = thr_check
    (OUT / "verification_report.json").write_text(json.dumps({"report": report, "n_pops": len(allpop)}, indent=1, default=str))
    print("done", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()

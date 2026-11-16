#!/usr/bin/env python3
"""EXP-A4D-002  Phase-1 unit test of the A4D verifier on the frozen SBG score columns in configs/populations.

Reproduces (with A4D's own code) SBG V5 / state / edit / exec-stat AUROC, CI (seed 42 + alternate seed), AUPRC, train-Youden P/R/F1,
H1-H6 style tests on v10_test / v9c_val, and compares every number with A3's independently validated values
(results/raw/EXP-A3-002/*_reconstruction.json, read-only).  Combiners are refit with A4D's own logistic code on v9c_train
(gradient-descent recipe = reproduction of the repo recipe; Newton = exact optimum cross-check).

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a4d_002_phase1_sbg_columns.py
"""
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4dlib as L  # noqa: E402

EXP = "EXP-A4D-002"
RAW = L.PKG / "results" / "raw" / EXP
TAB = L.PKG / "results" / "tables"
RAW.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
ALT_SEED = 1234
FROZEN = json.loads((L.REPO / "artifacts/final/V10_MODELS_FROZEN.json").read_text())
A3 = {n: json.loads((L.PKG / f"results/raw/EXP-A3-002/{n}_reconstruction.json").read_text()) for n in ("v10_test", "v9c_val")}
EXC3 = ["exception_fraction", "call_count", "coverage_size"]
MODEL_FEATS = {"E": ["edit"], "X": EXC3, "EX": ["edit"] + EXC3, "E+V5": ["edit", "sbg_v5"], "EX+V5": ["edit", "sbg_v5"] + EXC3,
               "E+V6": ["edit", "sbg_v6"], "EX+V6": ["edit", "sbg_v6"] + EXC3}
GD_CACHE = RAW / "gd_fits.json"


def feat(r, f):
    return r["edit"] if f == "edit" else r["scores"][f]


def main():
    t0 = time.time()
    train = L.load_pop("v9c_train")
    ytr = [r["label"] for r in train]
    cache = json.loads(GD_CACHE.read_text()) if GD_CACHE.exists() else {}
    models, newton, fitlog = {}, {}, {}
    for name, fs in MODEL_FEATS.items():
        fz = FROZEN["models"][name]
        order = fz["features"]
        if "V6" in name:   # v9c_train population has no sbg_v6 column -> use frozen parameters (cannot be refit from the population files)
            m = {"b": fz["bias"], "w": fz["weights_standardised"], "mu": fz["feature_means"], "sd": fz["feature_stds"]}
            models[name] = (order, m)
            fitlog[name] = {"features": order, "note": "frozen parameters used (no V6 column in v9c_train population)"}
            continue
        X = [[feat(r, f) for f in fs] for r in train]
        # repo recipe = gradient of mean log-loss + L2*|w|^2/n  ->  penalty gradient 2*L2*w/n  (eval_lib uses L2*w/n; documented difference)
        newton[name] = L.fit_logistic_newton(X, ytr, l2=2.0)
        if name not in cache:
            cache[name] = L.fit_logistic_gd(X, ytr, l2=2.0)
            GD_CACHE.write_text(json.dumps(cache))
        m = cache[name]
        models[name] = (fs, m)
        idx = [fs.index(f) for f in order]
        dw = max(abs(m["w"][i] - w) for i, w in zip(idx, fz["weights_standardised"]))
        dwn = max(abs(newton[name]["w"][i] - m["w"][i]) for i in range(len(fs)))
        fitlog[name] = {"features": fs, "gd_w": m["w"], "gd_b": m["b"], "newton_w": newton[name]["w"], "newton_b": newton[name]["b"],
                        "frozen_w": fz["weights_standardised"], "frozen_b": fz["bias"], "max_abs_dw_gd_vs_frozen": dw,
                        "abs_db_gd_vs_frozen": abs(m["b"] - fz["bias"]), "max_abs_dw_newton_vs_gd": dwn,
                        "newton_l2_1_w": L.fit_logistic_newton(X, ytr, l2=1.0)["w"]}
        print(f"fit {name:6s} |dw| GD-vs-repo = {dw:.2e}  |db| = {abs(m['b'] - fz['bias']):.2e}  |dw| Newton-vs-GD = {dwn:.2e}", flush=True)
    thr_log = {}
    cols_tr = {k: [r["scores"][k] for r in train] for k in ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token"]}
    cols_tr["edit"] = [r["edit"] for r in train]
    for name, (fs, m) in models.items():
        if "V6" in name:
            continue
        cols_tr["M_" + name] = [L.logit_apply(m, [feat(r, f) for f in fs]) for r in train]
    for k, v in cols_tr.items():
        thr, j = L.youden(v, ytr)
        frozen = FROZEN["thresholds_youden_train"].get(k)
        thr_log[k] = {"own_thr": thr, "J": j, "frozen_thr": frozen, "abs_diff": None if frozen is None else abs(thr - frozen)}
    print("max |thr diff| vs frozen thresholds:", max(v["abs_diff"] for v in thr_log.values() if v["abs_diff"] is not None), flush=True)

    allres, comp = {}, []

    def cmp(pop, key, mine, theirs, tol=2e-6):
        if theirs is None or mine is None:
            return
        comp.append({"population": pop, "quantity": key, "a4d": mine, "a3_validated": theirs, "abs_diff": abs(mine - theirs), "tol": tol})

    for pop in ("v10_test", "v9c_val"):
        rows = L.load_pop(pop)
        d = L.data_from_rows(rows)
        y = d.y
        cols = {k: [r["scores"][k] for r in rows] for k in rows[0]["scores"]}
        cols["edit"] = [r["edit"] for r in rows]
        cols["edit_reversed"] = [-r["edit"] for r in rows]
        for name, (fs, m) in models.items():
            if "V6" in name and pop != "v10_test":
                continue
            cols["M_" + name] = [L.logit_apply(m, [feat(r, f) for f in fs]) for r in rows]
        res42, resalt = L.Resamples(d.K, seed=42), L.Resamples(d.K, seed=ALT_SEED)
        mats = {k: L.pair_matrices(d, v) for k, v in cols.items()}
        out = {"n": d.n, "programs": d.K, "changed": sum(y), "predictors": {}, "deltas": {}}
        a3p = A3[pop]["predictors"]
        vecs = {}
        for k, v in cols.items():
            U, D = mats[k]
            pt = L.auroc_from_matrices(U, D)
            vecs[k] = L.boot_vec(U, D, res42)
            valt = L.boot_vec(U, D, resalt)
            thr = thr_log.get(k, {}).get("own_thr")
            pr = L.prf(v, y, thr) if thr is not None else None
            out["predictors"][k] = {"auroc": pt, "auroc_mannwhitney": L.auroc(v, y), "ci95_seed42": L.pct_ci(vecs[k]), "ci95_alt_seed": L.pct_ci(valt),
                                    "ci95_interp_seed42": L.pct_ci(vecs[k], "interp"), "boot_sd": L.sd(vecs[k]), "auprc": L.auprc(v, y),
                                    "cliffs_delta": L.cliffs_delta(v, y), "train_thr": thr, "prf": pr}
            if k in a3p:
                cmp(pop, f"{k}.auroc", pt, a3p[k]["auroc"])
                cmp(pop, f"{k}.ci_lo", out["predictors"][k]["ci95_seed42"][0], a3p[k]["ci95"][0])
                cmp(pop, f"{k}.ci_hi", out["predictors"][k]["ci95_seed42"][1], a3p[k]["ci95"][1])
                ap = a3p[k].get("pr_auc", a3p[k].get("auprc"))
                cmp(pop, f"{k}.auprc", out["predictors"][k]["auprc"], ap)
                if pr and "prf_at_frozen_thr" in a3p[k]:
                    f = a3p[k]["prf_at_frozen_thr"]
                    for q in ("precision", "recall", "f1"):
                        cmp(pop, f"{k}.{q}@train_thr", pr[q], f[q])
        out["H1_perm_p_sbg_v5"] = L.perm_label_auroc_p(d, cols["sbg_v5"])
        cmp(pop, "H1_perm_p", out["H1_perm_p_sbg_v5"], A3[pop]["H1_perm_p"], 1e-9)
        if pop == "v10_test":
            jobs = {"H2_E+V5_minus_E": ("M_E+V5", "M_E"), "H3_V5_minus_edit_forward": ("sbg_v5", "edit"), "H4_EX+V5_minus_EX": ("M_EX+V5", "M_EX"),
                    "H5_V6_minus_V5": ("sbg_v6", "sbg_v5"), "H6_EX+V6_minus_EX": ("M_EX+V6", "M_EX"),
                    "V5_minus_edit_reversed": ("sbg_v5", "edit_reversed"), "V5_minus_exception_fraction": ("sbg_v5", "exception_fraction"),
                    "V5_minus_static_ast": ("sbg_v5", "static_ast"), "V5_minus_static_token": ("sbg_v5", "static_token"),
                    "V5_minus_state (extra)": ("sbg_v5", "sbg_state"), "V5_minus_M_EX (extra)": ("sbg_v5", "M_EX"),
                    "V5_minus_coverage_size (extra)": ("sbg_v5", "coverage_size"), "state_minus_M_EX (extra)": ("sbg_state", "M_EX")}
            holm_names = ["H2_E+V5_minus_E", "H3_V5_minus_edit_forward", "H4_EX+V5_minus_EX", "H5_V6_minus_V5", "H6_EX+V6_minus_EX"]
        else:
            jobs = {"H2": ("M_E+V5", "M_E"), "H3": ("sbg_v5", "edit"), "H4": ("M_EX+V5", "M_EX"), "sbg_v5_minus_sbg_v3": ("sbg_v5", "sbg_v3"),
                    "sbg_v5_minus_sbg_temporal": ("sbg_v5", "sbg_temporal"), "sbg_v5_minus_sbg_state": ("sbg_v5", "sbg_state"),
                    "sbg_v5_minus_exception_fraction": ("sbg_v5", "exception_fraction"), "sbg_v5_minus_call_count": ("sbg_v5", "call_count"),
                    "sbg_v5_minus_coverage_size": ("sbg_v5", "coverage_size"), "sbg_v5_minus_static_ast": ("sbg_v5", "static_ast"),
                    "sbg_v5_minus_static_token": ("sbg_v5", "static_token"), "sbg_v5_minus_edit": ("sbg_v5", "edit"),
                    "V5_minus_M_EX (extra)": ("sbg_v5", "M_EX"), "state_minus_M_EX (extra)": ("sbg_state", "M_EX")}
            holm_names = ["H2", "H3", "H4"]
        for jn, (a, b) in jobs.items():
            r = L.delta_boot(out["predictors"][a]["auroc"], out["predictors"][b]["auroc"], vecs[a], vecs[b])
            r["jackknife_t"] = {k: v for k, v in L.jackknife_delta(d, *mats[a], *mats[b]).items() if k != "loo"}
            r["delong"] = L.delong_test(cols[a], cols[b], y)
            r["perm_label_p"] = L.perm_label_delta_p(d, cols[a], cols[b], B=1000, seed=42)
            out["deltas"][jn] = r
            ref = A3[pop]["deltas"].get(jn)
            if ref:
                cmp(pop, f"{jn}.delta", r["delta"], ref["delta"])
                cmp(pop, f"{jn}.ci_lo", r["ci95"][0], ref["ci_lower"])
                cmp(pop, f"{jn}.ci_hi", r["ci95"][1], ref["ci_upper"])
                cmp(pop, f"{jn}.p_two_sided(corrected)", r["p_boot_corrected"], ref["p_two_sided"])
        fam = {"H1": out["H1_perm_p_sbg_v5"], **{h: out["deltas"][h]["p_boot_corrected"] for h in holm_names}}
        fam_r = {k: round(v, 6) for k, v in fam.items()}
        out["holm_family"] = {"raw": fam, "holm": L.holm(fam_r), "bh_sensitivity": L.benjamini_hochberg(fam_r)}
        for h, v in out["holm_family"]["holm"].items():
            ref = next((vv for kk, vv in A3[pop]["holm"].items() if kk == h or kk.startswith(h + "_")), None)
            if ref:
                cmp(pop, f"holm.{h}", v, ref["p_adjusted"], 1.5e-3)
        sets = {k: L.matched_sets(d, cols[k]) for k in ("sbg_v5", "sbg_state", "edit", "exception_fraction", "sbg_v3", "sbg_temporal") if k in cols}
        out["concordance"] = {k: L.concordance_boot(v, None, d.K, res42) for k, v in sets.items()}
        for k, c in out["concordance"].items():
            ref = A3[pop]["concordance"].get(k)
            if ref:
                cmp(pop, f"concordance.{k}", c["conc"], ref["concordance"])
        Ue = {}
        for k in ("sbg_v5", "sbg_state", "edit", "sbg_v3", "sbg_temporal"):
            if k in cols:
                U, D = L.pair_matrices(d, cols[k], d.edit)
                Ue[k] = L.auroc_from_matrices(U, D)
                ref = A3[pop]["strat"].get(k)
                if ref:
                    cmp(pop, f"exact_edit_strat.{k}", Ue[k], ref["auroc"])
        out["exact_edit_stratified_auroc"] = Ue
        pp = {k: L.per_program_auroc(d, cols[k]) for k in ("sbg_v5", "sbg_state", "M_EX", "coverage_size", "edit", "sbg_v3", "sbg_temporal") if k in cols}
        ptab = {}
        for b in ("sbg_state", "M_EX", "coverage_size", "edit", "sbg_v3", "sbg_temporal"):
            if b in pp:
                dif = [pp["sbg_v5"][k] - pp[b][k] for k in d.keys]
                sp, w, l = L.sign_test_p(dif)
                wp, _ = L.wilcoxon_exact_p(dif)
                ptab[b] = {"v5_higher": w, "v5_lower": l, "ties": len(dif) - w - l, "sign_p": sp, "wilcoxon_p": wp}
        out["per_program_v5_vs"] = ptab
        out["per_program"] = pp
        allres[pop] = out
        print(pop, "done", round(time.time() - t0, 1), "s", flush=True)

    maxd = max(c["abs_diff"] for c in comp)
    bad = [c for c in comp if c["abs_diff"] > c["tol"]]
    summary = {"n_compared": len(comp), "max_abs_diff": maxd, "n_over_tolerance": len(bad), "over_tolerance": bad, "fit_log": fitlog, "threshold_log": thr_log,
               "runtime_s": time.time() - t0}
    (RAW / "phase1_results.json").write_text(json.dumps({"summary": summary, "results": allres}, indent=1, default=str))
    with open(TAB / f"{EXP}_vs_A3_comparison.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["population", "quantity", "a4d", "a3_validated", "abs_diff", "tol"])
        w.writeheader()
        w.writerows(comp)
    print(json.dumps({k: summary[k] for k in ("n_compared", "max_abs_diff", "n_over_tolerance")}))
    for c in bad[:40]:
        print("OVER", c)


if __name__ == "__main__":
    main()

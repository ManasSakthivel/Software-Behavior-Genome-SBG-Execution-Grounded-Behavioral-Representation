#!/usr/bin/env python3
"""EXP-A4D-004  Phase-1 dry run of the full verification pipeline (a4d_analysis.analyse) on the frozen SBG score columns:
SBG V5 vs {state, V3, temporal, edit, exec-stat singles, M_E, M_X, M_EX combiners, static distances} on v10_test and v9c_val, with
cluster CIs (2 seeds), Holm/BH, DeLong, jackknife-t, label-permutation, per-program sign/Wilcoxon, matched-set concordance,
design effect / ICC, LOPO influence, edit-stratified (exact + terciles), MDE/power, de-duplicated and v9c_val clean-label sensitivity.
Combiners use the repo-recipe GD fits cached by EXP-A4D-002.   This is a pipeline test: the 'family' here is descriptive only.

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a4d_004_phase1_dependence.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4dlib as L  # noqa: E402
import a4d_analysis as A  # noqa: E402

EXP = "EXP-A4D-004"
RAW = L.PKG / "results" / "raw" / EXP
RAW.mkdir(parents=True, exist_ok=True)
GD = json.loads((L.PKG / "results/raw/EXP-A4D-002/gd_fits.json").read_text())
EXC3 = ["exception_fraction", "call_count", "coverage_size"]
FEATS = {"E": ["edit"], "X": EXC3, "EX": ["edit"] + EXC3}
OTHERS = ["sbg_state", "sbg_v3", "sbg_temporal", "edit", "edit_reversed", "exception_fraction", "call_count", "coverage_size", "n_functions", "static_token",
          "static_ast", "M_E", "M_X", "M_EX"]


def main():
    t0 = time.time()
    res = {}
    train = L.load_pop("v9c_train")
    ytr = [r["label"] for r in train]
    for pop in ("v10_test", "v9c_val"):
        rows = L.load_pop(pop)
        cols = {k: [r["scores"][k] for r in rows] for k in rows[0]["scores"]}
        cols["edit"] = [r["edit"] for r in rows]
        cols["edit_reversed"] = [-r["edit"] for r in rows]
        thr = {}
        for n, fs in FEATS.items():
            m = GD[n]
            f = lambda r, x: r["edit"] if x == "edit" else r["scores"][x]  # noqa: E731
            cols["M_" + n] = [L.logit_apply(m, [f(r, x) for x in fs]) for r in rows]
            thr["M_" + n] = L.youden([L.logit_apply(m, [f(r, x) for x in fs]) for r in train], ytr)[0]
        for k in ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "coverage_size", "n_functions", "static_ast", "static_token"]:
            thr[k] = L.youden([r["scores"][k] for r in train], ytr)[0]
        thr["edit"] = L.youden([r["edit"] for r in train], ytr)[0]
        subsets = {"dedup_AST": A.dedup_indices(rows)}
        if pop == "v9c_val":
            for sc in ("S1", "S2", "S3"):
                subsets[f"clean_{sc}"] = A.clean_val_indices(rows, sc)
        res[pop] = A.analyse(pop, rows, cols, "sbg_v5", OTHERS, family=OTHERS, thr=thr, subsets=subsets)
        print(pop, "done", round(time.time() - t0, 1), flush=True)
        (RAW / f"phase1_pipeline_{pop}.json").write_text(json.dumps(res[pop], indent=1, default=str))
    print("runtime", time.time() - t0)
    for pop in res:
        print("==", pop)
        for o in OTHERS:
            c = res[pop]["cmp"][o]
            print(f"{o:20s} A_b={c['auroc_b']:.4f} d={c['delta']:+.4f} CI[{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] p={c['p_boot_corrected']:.3f} holm={c['holm_p']:.3f} "
                  f"dl_p={c['delong']['p']:.3g} jk_p={c['jackknife_t']['p_t']:.3g} DE={c['design_effect_delta']:.1f} MDE={c['power']['mde_t']:.3f} {c['verdict']}")


if __name__ == "__main__":
    main()

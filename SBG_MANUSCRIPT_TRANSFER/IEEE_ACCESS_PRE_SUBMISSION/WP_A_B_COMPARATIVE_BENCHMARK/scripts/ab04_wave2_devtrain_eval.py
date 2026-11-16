#!/usr/bin/env python3
"""ab04 -- evaluate the wave-2 competitor scores (EXP-A4R-004) on v9c_train / v9c_dev and compare with SBG V5 and wave-1 baselines (EXP-A4R-005).

DEV-ONLY, EXPLORATORY.  Reads: EXP-A4R-004 scores, A4C-003 predictions (sbg_v5 etc., rows+labels), the frozen A4C config (read-only).
Policy (copied from run_competitors.py so wave-2 is comparable with wave-1): not-computable (null) -> 0.0 ("no evidence of change") and counted;
representative of a module = config with highest v9c_dev AUROC (ties -> sorted name order); threshold = Youden on v9c_train scores of the same config.
Nothing here is a frozen config: NO frozen_config.json / registry entry is written (held-out use would require the user's authorisation).
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import ab02_independent_dev_stats as S  # noqa: E402  (own stdlib metric implementations)

WP = HERE.parent
PKG = WP.parent
SC = WP / "raw" / "EXP-A4R-004" / "scores"
OUT = WP / "raw" / "EXP-A4R-005"
TAB = WP / "tables"
OUT.mkdir(parents=True, exist_ok=True)
MODULES = ["static_tce", "static_ted", "static_srclev", "static_tfidf", "birthmark_kgram", "trace_align", "obs_points_outfree", "obs_points_outreading", "diffexec_same_input"]
PRIV = {"obs_points_outreading", "diffexec_same_input"}          # output-reading => same-input label-oracle ceilings (module docstrings)
B = 4000


def load_scores(pop, mod):
    d = SC / pop / mod
    out, errs = {}, 0
    for f in sorted(d.glob("*.json")):
        j = json.loads(f.read_text())
        out.update(j["scores"])
        errs += len(j["errors"])
    return out, errs


def main():
    t0 = time.time()
    rep = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "policy": __doc__, "pops": {}}
    pred = S.PRED
    base_cols = {}
    meta, _, _, _ = None, None, None, None
    pops = {}
    for pop in ("v9c_train", "v9c_dev"):
        meta, cols, rows, info = S.load_pop(pop)
        pops[pop] = (cols, rows)
    fc = json.loads((S.RAW / "EXP-A4C-002" / "frozen_config.json").read_text())
    reps_w1 = fc["representatives"]
    scored = {}
    for pop in ("v9c_train", "v9c_dev"):
        cols, rows = pops[pop]
        pair = [r[0] for r in rows]
        y = [r[1] for r in rows]
        scored[pop] = {}
        for m in MODULES:
            sc, errs = load_scores(pop, m)
            cfgs = sorted({k for v in sc.values() for k in v})
            colm, nnull = {}, {}
            for k in cfgs:
                raw = [sc.get(p, {}).get(k) for p in pair]
                nnull[k] = sum(1 for x in raw if x is None)
                colm[k] = [0.0 if x is None else x for x in raw]
            missing = sum(1 for p in pair if p not in sc)
            scored[pop][m] = {"cols": colm, "n_null": nnull, "n_missing_pairs": missing, "n_pair_errors": errs, "n_rows": len(pair)}
    # config tables
    cfg_tab = {}
    for m in MODULES:
        cfg_tab[m] = {}
        for k in scored["v9c_dev"][m]["cols"]:
            row = {}
            for pop in ("v9c_train", "v9c_dev"):
                cols, rows = pops[pop]
                y = [r[1] for r in rows]
                s = scored[pop][m]["cols"].get(k)
                row[pop] = {"auroc": S.auroc(s, y), "n_null": scored[pop][m]["n_null"].get(k)} if s is not None else None
            cfg_tab[m][k] = row
    reps = {}
    for m in MODULES:
        ks = sorted(cfg_tab[m])
        # '__default__' is a duplicate of one named config for most modules; keep it as a candidate (declared default) in sorted order
        best = max(ks, key=lambda k: round(cfg_tab[m][k]["v9c_dev"]["auroc"], 12))
        reps[m] = best
    colsD, rowsD = pops["v9c_dev"]
    colsT, rowsT = pops["v9c_train"]
    yD = [r[1] for r in rowsD]
    yT = [r[1] for r in rowsT]
    clD, clT = S.Clu([r[2] for r in rowsD], yD), S.Clu([r[2] for r in rowsT], yT)
    WD, WT = S.resample_weights(clD.K, B, S.SEED), S.resample_weights(clT.K, 1000, S.SEED)
    v5D, v5T = colsD["sbg_v5"], colsT["sbg_v5"]
    ref = {"sbg_v5": "sbg_v5", "sbg_state": "sbg_state", "forest_EXx": "forest|RF_d4|EXx", "pathspectra": "pathspectra|shape|covset|max", "output_indep_frac40": "output_indep|frac40",
           "tce_ast_w1": "static|tce_ast", "traceseq_rename_robust": "traceseq|cre|full|kgram4|max", "edit": "edit"}
    out = {"representatives_by_dev_auroc": reps, "modules": {}, "reference_dev": {}}
    CmD = {}
    for name, key in ref.items():
        CmD[name] = clD.matrix(colsD[key])
        bs = [clD.auroc_w(CmD[name], w) for w in WD]
        out["reference_dev"][name] = {"method": key, "auroc": S.auroc(colsD[key], yD), "ci95": [S.pct(bs, .025), S.pct(bs, .975)], "auprc": S.ap(colsD[key], yD)}
    pvals = {}
    for m in MODULES:
        k = reps[m]
        sD, sT = scored["v9c_dev"][m]["cols"][k], scored["v9c_train"][m]["cols"][k]
        C = clD.matrix(sD)
        bs = [clD.auroc_w(C, w) for w in WD]
        ts = S.tie_stats(sD, yD)
        thr = S.youden(sT, yT)
        pred_ = [1 if v >= thr else 0 for v in sD]
        tp = sum(1 for a, b in zip(pred_, yD) if a and b)
        fp = sum(1 for a, b in zip(pred_, yD) if a and not b)
        fn = sum(1 for a, b in zip(pred_, yD) if not a and b)
        tn = sum(1 for a, b in zip(pred_, yD) if not a and not b)
        prec = tp / (tp + fp) if tp + fp else float("nan")
        recl = tp / (tp + fn)
        f1 = 2 * prec * recl / (prec + recl) if prec == prec and prec + recl else float("nan")
        per = clD.per_cluster(sD)
        perT = clT.per_cluster(sT)
        d = {"representative": k, "dev_auroc": S.auroc(sD, yD), "dev_ci95": [S.pct(bs, .025), S.pct(bs, .975)], "dev_auprc": S.ap(sD, yD),
             "train_auroc": S.auroc(sT, yT), "n_configs": len(cfg_tab[m]), "dev_macro_auroc": sum(per.values()) / len(per),
             "n_dev_programs_auroc_gt_half": sum(1 for v in per.values() if v > .5), "n_train_programs_auroc_gt_half": sum(1 for v in perT.values() if v > .5), "n_train_programs": len(perT),
             "train_youden_thr": thr, "dev_precision@thr": prec, "dev_recall@thr": recl, "dev_f1@thr": f1, "dev_fpr@thr": fp / (fp + tn), **{"dev_" + a: b for a, b in ts.items()},
             "n_null_dev": scored["v9c_dev"][m]["n_null"][k], "n_null_train": scored["v9c_train"][m]["n_null"][k], "n_pair_errors_dev": scored["v9c_dev"][m]["n_pair_errors"],
             "n_pair_errors_train": scored["v9c_train"][m]["n_pair_errors"], "n_missing_pairs_dev": scored["v9c_dev"][m]["n_missing_pairs"], "n_missing_pairs_train": scored["v9c_train"][m]["n_missing_pairs"],
             "privileged_output_reading": m in PRIV, "dev_config_range": [min(v["v9c_dev"]["auroc"] for v in cfg_tab[m].values()), max(v["v9c_dev"]["auroc"] for v in cfg_tab[m].values())]}
        # paired deltas vs references on dev
        d["paired_dev"] = {}
        for name in ("sbg_v5", "sbg_state", "forest_EXx", "pathspectra"):
            ds = [clD.auroc_w(CmD[name], w) - clD.auroc_w(C, w) for w in WD]
            ds = [x for x in ds if x == x]
            nle, nge = sum(1 for x in ds if x <= 0), sum(1 for x in ds if x >= 0)
            pb = min(1.0, 2 * (min(nle, nge) + 1) / (len(ds) + 1))
            pv, pm = clD.per_cluster(colsD[ref[name]]), per
            dk = [pv[q] - pm[q] for q in clD.keys]
            K, obs = len(dk), sum(dk) / len(dk)
            cnt = sum(1 for mask in range(1 << K) if abs(sum(x if (mask >> i) & 1 else -x for i, x in enumerate(dk)) / K) >= abs(obs) - 1e-12)
            d["paired_dev"][name] = {"delta_ref_minus_competitor": S.auroc(colsD[ref[name]], yD) - d["dev_auroc"], "ci95": [S.pct(ds, .025), S.pct(ds, .975)], "p_boot": pb,
                                     "p_signflip_exact": cnt / (1 << K), "n_prog_ref_better": sum(1 for x in dk if x > 0), "n_prog_comp_better": sum(1 for x in dk if x < 0)}
        pvals[m] = d["paired_dev"]["sbg_v5"]["p_boot"]
        # train paired vs V5
        CT = clT.matrix(sT)
        CTv5 = clT.matrix(v5T)
        dsT = [x for x in (clT.auroc_w(CTv5, w) - clT.auroc_w(CT, w) for w in WT) if x == x]
        d["paired_train_v5"] = {"delta_v5_minus": S.auroc(v5T, yT) - d["train_auroc"], "ci95": [S.pct(dsT, .025), S.pct(dsT, .975)]}
        out["modules"][m] = d
    h9 = S.holm(pvals)
    # joint family with the 19 pre-declared dev p-values (from EXP-A4R-003)
    prev = json.loads((WP / "raw" / "EXP-A4R-003" / "independent_stats.json").read_text())["populations"]["v9c_dev"]["holm_family"]
    allp = {f"w1:{f}": v["p_boot"] for f, v in prev.items()}
    allp.update({f"w2:{m}": pvals[m] for m in pvals})
    h28 = S.holm(allp)
    for m in MODULES:
        out["modules"][m]["p_boot_vs_v5"] = pvals[m]
        out["modules"][m]["p_holm_wave2_m9"] = h9[m]
        out["modules"][m]["p_holm_joint_m%d" % len(allp)] = h28[f"w2:{m}"]
    out["config_table"] = cfg_tab
    (OUT / "wave2_dev_train_results.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    with open(TAB / "EXP-A4R-005_wave2_dev_representatives.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["module", "representative_config", "privileged", "dev_auroc", "ci_lo", "ci_hi", "dev_auprc", "train_auroc", "dev_prog_gt_half(13)", "train_prog_gt_half", "tie_pair_share_dev",
                    "dev_f1@trainYouden", "d_v5_minus", "d_ci_lo", "d_ci_hi", "p_boot", "p_signflip_exact", "p_holm_w2_m9", "p_holm_joint", "n_null_dev", "n_null_train", "n_configs"])
        for m in MODULES:
            d = out["modules"][m]
            p = d["paired_dev"]["sbg_v5"]
            w.writerow([m, d["representative"], d["privileged_output_reading"], f"{d['dev_auroc']:.4f}", f"{d['dev_ci95'][0]:.4f}", f"{d['dev_ci95'][1]:.4f}", f"{d['dev_auprc']:.4f}", f"{d['train_auroc']:.4f}",
                        d["n_dev_programs_auroc_gt_half"], d["n_train_programs_auroc_gt_half"], f"{d['dev_tie_pair_share']:.3f}", f"{d['dev_f1@thr']:.3f}", f"{p['delta_ref_minus_competitor']:+.4f}",
                        f"{p['ci95'][0]:+.4f}", f"{p['ci95'][1]:+.4f}", f"{p['p_boot']:.4f}", f"{p['p_signflip_exact']:.5f}", f"{d['p_holm_wave2_m9']:.4f}", f"{d['p_holm_joint_m28']:.4f}", d["n_null_dev"], d["n_null_train"], d["n_configs"]])
    with open(TAB / "EXP-A4R-005_wave2_all_configs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["module", "config", "train_auroc", "dev_auroc", "n_null_train", "n_null_dev"])
        for m in MODULES:
            for k, v in sorted(cfg_tab[m].items(), key=lambda kv: -kv[1]["v9c_dev"]["auroc"]):
                w.writerow([m, k, f"{v['v9c_train']['auroc']:.4f}", f"{v['v9c_dev']['auroc']:.4f}", v["v9c_train"]["n_null"], v["v9c_dev"]["n_null"]])
    print("done", round(time.time() - t0), "s")
    for m in MODULES:
        d = out["modules"][m]
        print(f"{m:22s} {d['representative']:34s} dev {d['dev_auroc']:.4f} [{d['dev_ci95'][0]:.3f},{d['dev_ci95'][1]:.3f}] train {d['train_auroc']:.4f} dV5 {d['paired_dev']['sbg_v5']['delta_ref_minus_competitor']:+.4f} p={d['paired_dev']['sbg_v5']['p_boot']:.3f} holm9={d['p_holm_wave2_m9']:.3f} nnull={d['n_null_dev']}/{d['n_null_train']}")
    print({k: (round(v['auroc'], 4), [round(x, 3) for x in v['ci95']]) for k, v in out["reference_dev"].items()})


if __name__ == "__main__":
    main()

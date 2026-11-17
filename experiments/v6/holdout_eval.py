"""Frozen holdout evaluation (HOLDOUT_ANALYSIS_PLAN.md). Fit ONCE on all DEV; score holdouts; no tuning, no seed selection.
  OMP_NUM_THREADS=1 python experiments/v6/holdout_eval.py            -> artifacts/v6/holdout/results/
  python experiments/v6/holdout_eval.py --smoke                      -> DEV-only dry run (train -> val) into the scratchpad path given by SMOKE_OUT"""
import json, sys, os, pathlib, hashlib, time, platform
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import experiments.v6.evaluate as ev
from experiments.v6.evaluate import REPO, SEEDS, auroc, neutral, fit_predict, load
from experiments.v6.final_pipeline import SPEC, fit_p1, C1, V6B, CONVC
from scipy.stats import rankdata
SMOKE = "--smoke" in sys.argv
OUT = pathlib.Path(os.environ["SMOKE_OUT"]) if SMOKE else REPO / "artifacts/v6/holdout/results"; OUT.mkdir(parents=True, exist_ok=True)
B, BSEED = 2000, 42
MODELS = ["C0g_V6B_gated", "C1_V6B_minusE", "CONV", "CONV+C0g", "CONV+C1", "V5", "R2:DIFF", "R2:C1+R", "R2:CONV+DIFF", "R2:CONV+DIFF+C1"]
RAW = {"V5raw": "sbg_v5", "V6raw": "d_v6", "d_A": "d_A", "d_B": "d_B", "d_C": "d_C", "g": "g", "alpha": "alpha", "static_token": "static_token", "static_ast": "static_ast",
       "edit_lines": "edit_lines", "call_count": "call_count", "coverage_size": "coverage_size", "R2:delta_out": "delta_out", "R2:d_R": "d_R"}
# ---- fast, tie-correct metrics (match sklearn roc_auc_score / average_precision_score)
def auc(y, s):
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (rankdata(s)[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def ap(y, s):
    n1 = int(y.sum())
    if n1 == 0: return np.nan
    o = np.argsort(-s, kind="stable"); ss, yy = s[o], y[o]; tp = np.cumsum(yy)
    idx = np.r_[np.where(np.diff(ss) != 0)[0], len(ss) - 1]; prec = tp[idx] / (idx + 1); rec = tp[idx] / n1
    return float(np.sum(np.diff(np.r_[0, rec]) * prec))
class Cl:
    def __init__(s, g): s.u, s.inv = np.unique(g, return_inverse=True); s.idx = [np.where(s.inv == i)[0] for i in range(len(s.u))]
    def draws(s, B, seed):
        rs = np.random.RandomState(seed); return [np.concatenate([s.idx[i] for i in rs.randint(0, len(s.u), len(s.u))]) for _ in range(B)]
def ci(v): v = np.array([x for x in v if not np.isnan(x)]); return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) > 20 else [None, None]
def metric_row(y, s, cl, draws):
    a, p = auc(y, s), ap(y, s)
    ba, bp = zip(*[(auc(y[d], s[d]), ap(y[d], s[d])) for d in draws])
    return {"n": int(len(y)), "n_pos": int(y.sum()), "prevalence": float(y.mean()), "clusters": int(len(cl.u)), "auroc": a, "auroc_ci95": ci(ba), "auprc": p, "auprc_ci95": ci(bp)}
def paired(y, s1, s2, cl, draws, seed=BSEED):
    d0 = auc(y, s1) - auc(y, s2); bd = [auc(y[d], s1[d]) - auc(y[d], s2[d]) for d in draws]
    rs = np.random.RandomState(seed + 1); hit = 0
    for _ in range(B):
        sw = (rs.rand(len(cl.u)) < .5)[cl.inv]; a = np.where(sw, s2, s1); b = np.where(sw, s1, s2); hit += abs(auc(y, a) - auc(y, b)) >= abs(d0) - 1e-12
    return {"delta_auroc": float(d0), "ci95": ci(bd), "p_two_sided": float((hit + 1) / (B + 1)), "delta_auprc": float(ap(y, s1) - ap(y, s2))}
def inferential(y, cl):
    both = sum(1 for ix in cl.idx if 0 < y[ix].sum() < len(ix)); return len(cl.u) >= 15 and both >= 10
def main():
    t0 = time.time()
    ev.ART = REPO / "artifacts/v6/repro"; dev = load(["v8train"]) if SMOKE else load(["v8train", "v8val"])
    H = {}
    if SMOKE: H["smoke_v8val"] = load(["v8val"])
    else:
        ev.ART = REPO / "artifacts/v6/holdout"
        for n in ("v8test", "v10", "quixbugs_declared", "quixbugs_canonical", "bugsinpy"): H[n] = load([n])
    ydev, gdev, actdev = dev.label.values.astype(int), dev.base_id.values, dev.st_act.values.astype(bool)
    res = {"meta": {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "python": sys.version.split()[0], "platform": platform.platform(), "dev_pairs": len(dev), "smoke": SMOKE, "B": B, "bootstrap_seed": BSEED}, "bench": {}}
    allpred = []
    for name, df in H.items():
        df = df[df.label >= 0].reset_index(drop=True) if (df.label < 0).sum() == 0 else df.reset_index(drop=True)
        lost_unknown_label = int((df.label < 0).sum())
        y = df.label.values.astype(int); g = df.base_id.astype(str).values; act = df.st_act.values.astype(bool); v5ev = df.v5_evaluated.fillna(False).values.astype(bool)
        cl = Cl(g); draws = cl.draws(B, BSEED); S = {}; extra = {}
        for m in MODELS:
            cols, pol = SPEC[m]
            for kind in ("LR", "GBM"):
                Xd, Xh = dev[cols].values, df[cols].values
                if pol == "frozen": p = fit_predict(kind, Xd, ydev, gdev, Xh)[0]
                else:
                    p, med = fit_p1(kind, Xd, ydev, gdev, Xh, actdev if pol == "P1" else np.ones(len(dev), bool))
                    if pol == "P1": p[~act] = med; extra[f"{m}|{kind}|abstain_fill_median"] = med
                S[f"{m}|{kind}"] = p
        for k, c in RAW.items():
            ref = dev[c] if c in dev else None
            S[f"raw:{k}"] = (df[c].fillna(ref.median() if ref is not None else 0).values if c in df else np.zeros(len(df)))
            if k in ("edit_lines", "static_token", "static_ast", "V5raw", "V6raw"): S[f"raw:{k}(reversed)"] = -S[f"raw:{k}"]
        views = {"ALL_PAIRS": np.ones(len(df), bool), "EVALUABLE_ACTIVATED": act, "INTERSECT_ACT_AND_V5EVAL": act & v5ev}
        bres = {"n_pairs": len(df), "clusters": int(len(cl.u)), "n_pos": int(y.sum()), "n_lost_unknown_label": lost_unknown_label,
                "status_counts": df.status.value_counts().to_dict(), "coverage": {k: float(v.mean()) for k, v in views.items()}, "v5_evaluated_frac": float(v5ev.mean()),
                "abstained": int((~act).sum()), "abstained_pos": int(y[~act].sum()), "unknown_reasons": {}, "inferential_ok": bool(inferential(y, cl)), "fill": extra, "metrics": {}}
        bres["metrics"] = {}
        for vname, mask in views.items():
            if mask.sum() < 5 or y[mask].min() == y[mask].max(): bres["metrics"][vname] = "undefined (one class or <5 pairs)"; continue
            clm = Cl(g[mask]); dr = clm.draws(B, BSEED); bres["metrics"][vname] = {k: metric_row(y[mask], s[mask], clm, dr) for k, s in S.items()}
        # ---- contrasts (ALL_PAIRS view; evaluable views repeated as exploratory)
        CON = {"a: CONV+C0g - CONV [LR]": ("CONV+C0g|LR", "CONV|LR"), "b: CONV+C0g - CONV [GBM]": ("CONV+C0g|GBM", "CONV|GBM"), "c: C0g - V5 [LR]": ("C0g_V6B_gated|LR", "V5|LR"),
               "x: C0g - C1 [LR]": ("C0g_V6B_gated|LR", "C1_V6B_minusE|LR"), "x: C0g - C1 [GBM]": ("C0g_V6B_gated|GBM", "C1_V6B_minusE|GBM"), "x: C0g - V5 [GBM]": ("C0g_V6B_gated|GBM", "V5|GBM"),
               "x: CONV+C1 - CONV [LR]": ("CONV+C1|LR", "CONV|LR"), "x: CONV+C1 - CONV [GBM]": ("CONV+C1|GBM", "CONV|GBM"), "x: C0g - CONV [LR]": ("C0g_V6B_gated|LR", "CONV|LR"),
               "x: C0g - reversed edit size": ("C0g_V6B_gated|LR", "raw:edit_lines(reversed)"),
               "R2: CONV+DIFF+C1 - CONV+DIFF [LR]": ("R2:CONV+DIFF+C1|LR", "R2:CONV+DIFF|LR"), "R2: CONV+DIFF+C1 - CONV+DIFF [GBM]": ("R2:CONV+DIFF+C1|GBM", "R2:CONV+DIFF|GBM")}
        bres["contrasts"] = {}
        for vname in ("ALL_PAIRS", "EVALUABLE_ACTIVATED"):
            mask = views[vname]
            if mask.sum() < 5 or y[mask].min() == y[mask].max(): continue
            clm = Cl(g[mask]); dr = clm.draws(B, BSEED); ok = inferential(y[mask], clm)
            for k, (a, b) in CON.items():
                r = paired(y[mask], S[a][mask], S[b][mask], clm, dr); r["inferential"] = bool(ok)
                if not ok: r["p_two_sided"] = None; r["note"] = "descriptive only: <15 clusters or <10 clusters with both classes"
                bres["contrasts"][f"{vname}|{k}"] = r
        # ---- mutation-family / pair-kind performance (vs all label-0 pairs of the benchmark), ALL_PAIRS
        fam = df.transformation_type.astype(str).map(lambda t: t.split("+")[0] if t.startswith("SC") else t).values
        bres["by_family"] = {}
        for t in sorted(set(fam[y == 1])):
            m = (fam == t) | (y == 0); d = {"n_pos": int((fam == t).sum()), "abstained_frac": float((~act[fam == t]).mean())}
            for k in ("C0g_V6B_gated|LR", "C1_V6B_minusE|LR", "CONV|LR", "V5|LR", "raw:V6raw", "raw:V5raw", "raw:edit_lines(reversed)", "raw:R2:delta_out"):
                d[k] = float(auc(y[m], S[k][m]))
            bres["by_family"][t] = d
        bres["by_negative_type_mean_score_C0g_LR"] = {t: {"n": int((fam == t).sum()), "mean": float(S["C0g_V6B_gated|LR"][fam == t].mean()), "abstained_frac": float((~act[fam == t]).mean())} for t in sorted(set(fam[y == 0]))}
        # ---- failure cases (C0g LR, ALL_PAIRS)
        s = S["C0g_V6B_gated|LR"]; cols_keep = ["pair_id", "base_id", "transformation_type", "label", "status", "d_A", "d_C", "alpha", "edit_lines", "delta_out"]
        fn = df.assign(score=s)[y == 1].sort_values("score").head(15)[cols_keep + ["score"]]; fp = df.assign(score=s)[y == 0].sort_values("score", ascending=False).head(15)[cols_keep + ["score"]]
        fn.assign(kind="lowest_scored_positive").to_csv(OUT / f"failures_{name}_FN.csv", index=False); fp.assign(kind="highest_scored_negative").to_csv(OUT / f"failures_{name}_FP.csv", index=False)
        un = df[df.status == "UNKNOWN"]; bres["unknown_reasons"] = pd.Series([str(r)[:70] for r in un.get("reasons", pd.Series(dtype=object))]).value_counts().to_dict() if len(un) else {}
        res["bench"][name] = bres
        pr = df[["pair_id", "base_id", "label", "status", "transformation_type"]].copy()
        for k, v in S.items(): pr[k] = v
        pr.insert(0, "benchmark", name); pr.to_csv(OUT / f"predictions_{name}.csv", index=False); allpred.append(name)
        print(name, "done", round(time.time() - t0), "s", flush=True)
    # ---- Holm over the declared family (a,b,c on ALL_PAIRS, inferential benchmarks only)
    fam = [(n, k) for n, b in res["bench"].items() for k in b["contrasts"] if k.startswith("ALL_PAIRS|") and k.split("|")[1][0] in "abc" and b["contrasts"][k]["p_two_sided"] is not None]
    fam.sort(key=lambda nk: res["bench"][nk[0]]["contrasts"][nk[1]]["p_two_sided"]); run = 0
    for i, (n, k) in enumerate(fam): run = max(run, min(1.0, res["bench"][n]["contrasts"][k]["p_two_sided"] * (len(fam) - i))); res["bench"][n]["contrasts"][k]["p_holm"] = run
    res["holm_family_size"] = len(fam)
    json.dump(res, open(OUT / "HOLDOUT_RESULTS.json", "w"), indent=1, default=float); print("done", round(time.time() - t0), "s")
if __name__ == "__main__": main()

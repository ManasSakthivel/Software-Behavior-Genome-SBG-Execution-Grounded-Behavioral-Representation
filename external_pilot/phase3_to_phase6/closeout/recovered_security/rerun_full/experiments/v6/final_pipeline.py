"""PROTOCOL_V2 pipeline. Reads ONLY re-extracted DEV features (artifacts/v6/repro). Every model is re-fit; nothing is reused from earlier OOF files.
  OMP_NUM_THREADS=1 python experiments/v6/final_pipeline.py -> artifacts/v6/final/{FINAL_RESULTS.json,predictions_final.csv,OOF_final.npz}"""
import json, sys, pathlib, hashlib, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import experiments.v6.evaluate as ev
from experiments.v6.evaluate import *   # noqa
ev.ART = REPO / "artifacts/v6/repro"
OUT = REPO / "artifacts/v6/final"; OUT.mkdir(exist_ok=True)
E_COLS = ["alpha", "conf", "st_act", "st_nact", "st_unk"]
V6B = ["d_A", "d_C", "cfg0", "cfg1", "cfg2", "alpha", "conf", "st_act", "st_nact", "st_unk"]
C1 = [c for c in V6B if c not in E_COLS]; C2 = [c for c in C1 if c != "d_A"]
CONVC = STAT + ["edit_lines"] + EXV
SPEC = {  # name -> (columns, policy)   policy: frozen | P1 (no E indicator + abstain) | nogate (no indicator, no abstain)
    "C0_V6B_as_frozen": (V6B, "frozen"), "C0g_V6B_gated": (V6B, "P1"), "C1_V6B_minusE": (C1, "P1"), "C2_V6B_minusE_minusA": (C2, "P1"),
    "V6_full_as_frozen": (V6C, "frozen"), "V5": (V5C, "frozen"),
    "CONV": (CONVC, "nogate"), "CONV+C0g": (CONVC + V6B, "nogate"), "CONV+C1": (CONVC + C1, "nogate"), "CONV+C2": (CONVC + C2, "nogate"),
    "R2:C1+R": (C1 + ["d_R"], "nogate"), "R2:DIFF": (["delta_out"], "nogate"), "R2:CONV+DIFF": (CONVC + ["delta_out"], "nogate"),
    "R2:CONV+DIFF+C1": (CONVC + ["delta_out"] + C1, "nogate")}
LOFO_SET = {"C0_V6B_as_frozen", "C0g_V6B_gated", "C1_V6B_minusE", "C2_V6B_minusE_minusA", "CONV", "CONV+C1", "CONV+C2"}
def mk(kind):
    if kind == "LR":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000))
    return make_pipeline(SimpleImputer(strategy="median"), HistGradientBoostingClassifier(random_state=0))
def fit_p1(kind, Xtr, ytr, gtr, Xte, act_tr):
    gs = GridSearchCV(mk(kind), GRID[kind], cv=GroupKFold(3), scoring="roc_auc", n_jobs=1).fit(Xtr, ytr, groups=gtr)
    oof = np.zeros(len(ytr))
    for a, b in GroupKFold(3).split(Xtr, ytr, gtr):
        oof[b] = mk(kind).set_params(**gs.best_params_).fit(Xtr[a], ytr[a]).predict_proba(Xtr[b])[:, 1]
    return gs.predict_proba(Xte)[:, 1], float(np.median(oof[act_tr]))
DF = None
def task(a):
    global DF
    name, kind, mode = a
    if DF is None: DF = load(["v8train", "v8val"])
    df = DF; y, g, t = df.label.values.astype(int), df.base_id.values, df.transformation_type.values
    cols, pol = SPEC[name]; X = df[cols].values; act = df.st_act.values.astype(bool); oof = np.zeros(len(df))
    sp = folds(g, mode) if mode != "lofo" else [(np.where(t != u)[0], np.where(t == u)[0]) for u in sorted(set(t))]
    for tr, te in sp:
        if pol == "frozen": oof[te] = fit_predict(kind, X[tr], y[tr], g[tr], X[te])[0]
        else:
            p, med = fit_p1(kind, X[tr], y[tr], g[tr], X[te], act[tr] if pol == "P1" else np.ones(len(tr), bool))
            if pol == "P1": p[~act[te]] = med          # abstain: NOT_ACTIVATED / UNKNOWN never counted as evidence of equivalence
            oof[te] = p
    return a, oof
def _b(a):   # (y,s1,s2,g) -> bootstrap CI of delta (s2 None -> single AUROC)
    y, s1, s2, g, B = a; return list(cluster_boot(y, s1, g, B=B, s2=s2))
def _p(a):
    y, s1, s2, g = a; return min(1.0, 2 * min(cluster_perm_p(y, s1, s2, g, B=1000), cluster_perm_p(y, s2, s1, g, B=1000)))
def main():
    t0 = time.time(); df = load(["v8train", "v8val"]); y, g = df.label.values.astype(int), df.base_id.values
    jobs = [(n, k, s) for n in SPEC for k in ("LR", "GBM") for s in SEEDS] + [(n, k, "lofo") for n in LOFO_SET for k in ("LR", "GBM")]
    with ProcessPoolExecutor(12) as ex: R = dict(ex.map(task, jobs)); print("fits done", round(time.time() - t0), flush=True)
    np.savez_compressed(OUT / "OOF_final.npz", **{"|".join(map(str, k)): v for k, v in R.items()})
    M = lambda n, k: np.mean([R[(n, k, s)] for s in SEEDS], 0)
    q = pd.qcut(df.edit_lines.fillna(df.edit_lines.median()).rank(method="first"), 3, labels=["small", "mid", "large"]).values
    meta = {}
    for f in ("train", "val"):
        for l in open(REPO / f"benchmark/datasets/v8/pairs_{f}.jsonl"):
            r = json.loads(l); meta[r["pair_id"]] = hashlib.sha256((REPO / r["variant_path"]).read_bytes()).hexdigest()
    vh = df.pair_id.map(meta); w = 1.0 / vh.map(vh.value_counts()).values        # each distinct variant file weighs 1
    act = df.st_act.values.astype(bool); pool = ProcessPoolExecutor(12); res = {"table": {}}
    jb = {}; 
    for n in SPEC:
        for k in ("LR", "GBM"):
            s = M(n, k); per = [auroc(y, R[(n, k, sd)]) for sd in SEEDS]
            res["table"][f"{n}|{k}"] = {"auroc": auroc(y, s), "per_seed": per, "seed_sd": float(np.std(per)), "activated_only_auroc": auroc(y[act], s[act]),
                "dedup_weighted_auroc": float(roc_auc_score(y, s, sample_weight=w)), "strata": {z: auroc(y[q == z], s[q == z]) for z in ("small", "mid", "large")},
                "lofo": auroc(y, R[(n, k, "lofo")]) if (n, k, "lofo") in R else None}
            jb[f"{n}|{k}"] = pool.submit(_b, (y, s, None, g, 1000))
    # abstention profile
    res["abstention"] = {"rate": float((~act).mean()), "n": int((~act).sum()), "label_mix_changed_frac": float(y[~act].mean()), "status_counts": df.status.value_counts().to_dict(),
        "by_type": df[~act].groupby("transformation_type").size().to_dict()}
    # ---- selection among candidates (alone, LR, P1)  [PROTOCOL_V2]
    cands = ["C0g_V6B_gated", "C1_V6B_minusE", "C2_V6B_minusE_minusA"]; nf = {c: len(SPEC[c][0]) for c in cands}
    prim = {c: auroc(y, M(c, "LR")) for c in cands}; best = max(prim, key=prim.get); rule = {"primary_auroc": prim, "best": best, "n_features": nf, "cands": {}}
    fut = {}
    for c in cands:
        if c == best: continue
        s, sb = M(c, "LR"), M(best, "LR")
        fut[c] = {"all": pool.submit(_b, (y, s, sb, g, 2000)), "lofo": pool.submit(_b, (y, R[(c, "LR", "lofo")], R[(best, "LR", "lofo")], g, 2000))}
        for z in ("small", "mid", "large"):
            m = q == z; fut[c][z] = pool.submit(_b, (y[m], s[m], sb[m], g[m], 2000))
    for c in cands:
        if c == best: rule["cands"][c] = {"delta_vs_best": 0, "ties_best": True, "noninferior": True}; continue
        f = {k: v.result() for k, v in fut[c].items()}; d = auroc(y, M(c, "LR")) - prim[best]
        rule["cands"][c] = {"delta_vs_best": d, "ci95": f["all"], "ties_best": bool(f["all"][0] <= 0 <= f["all"][1]),
            "noninferior_lower95": {k: f[k][0] for k in ("small", "mid", "large", "lofo")}, "noninferior": bool(all(f[k][0] > -0.02 for k in ("small", "mid", "large", "lofo")))}
    elig = [c for c in cands if rule["cands"][c]["ties_best"] and rule["cands"][c]["noninferior"]]
    rule["eligible"] = elig; rule["selected_by_rule"] = min(elig, key=lambda c: (nf[c], c)); res["rule"] = rule
    # ---- paired contrasts (identical folds/seeds): E removal, A removal, gating effect, increments over CONV, R2
    pc = {"C1_minusE vs C0g (LR)": ("C1_V6B_minusE", "C0g_V6B_gated", "LR"), "C1_minusE vs C0g (GBM)": ("C1_V6B_minusE", "C0g_V6B_gated", "GBM"),
          "C2_minusA vs C1 (LR)": ("C2_V6B_minusE_minusA", "C1_V6B_minusE", "LR"), "C2_minusA vs C1 (GBM)": ("C2_V6B_minusE_minusA", "C1_V6B_minusE", "GBM"),
          "gating effect: C0g vs C0_as_frozen (LR)": ("C0g_V6B_gated", "C0_V6B_as_frozen", "LR"), "gating effect: C0g vs C0_as_frozen (GBM)": ("C0g_V6B_gated", "C0_V6B_as_frozen", "GBM"),
          "CONV+C1 vs CONV (LR)": ("CONV+C1", "CONV", "LR"), "CONV+C1 vs CONV (GBM)": ("CONV+C1", "CONV", "GBM"), "CONV+C2 vs CONV (LR)": ("CONV+C2", "CONV", "LR"), "CONV+C2 vs CONV (GBM)": ("CONV+C2", "CONV", "GBM"),
          "C1 vs V5 (LR)": ("C1_V6B_minusE", "V5", "LR"), "C1 vs V5 (GBM)": ("C1_V6B_minusE", "V5", "GBM"), "CONV+C1 vs CONV+C0g (GBM)": ("CONV+C1", "CONV+C0g", "GBM"),
          "R2: C1+R vs C1 (LR)": ("R2:C1+R", "C1_V6B_minusE", "LR"), "R2: CONV+DIFF+C1 vs CONV+DIFF (LR)": ("R2:CONV+DIFF+C1", "R2:CONV+DIFF", "LR"), "R2: CONV+DIFF+C1 vs CONV+DIFF (GBM)": ("R2:CONV+DIFF+C1", "R2:CONV+DIFF", "GBM")}
    pf = {k: (pool.submit(_b, (y, M(a, kd), M(b, kd), g, 2000)), pool.submit(_p, (y, M(a, kd), M(b, kd), g))) for k, (a, b, kd) in pc.items()}
    res["paired"] = {}
    for k, (a, b, kd) in pc.items():
        res["paired"][k] = {"delta": auroc(y, M(a, kd)) - auroc(y, M(b, kd)), "ci95": pf[k][0].result(), "p_two_sided": pf[k][1].result(),
                            "per_seed": [auroc(y, R[(a, kd, s)]) - auroc(y, R[(b, kd, s)]) for s in SEEDS]}
    for k, v in jb.items(): res["table"][k]["ci95"] = v.result()
    # Holm over the paired family
    ks = sorted(res["paired"], key=lambda k: res["paired"][k]["p_two_sided"]); run = 0
    for i, k in enumerate(ks): run = max(run, min(1.0, res["paired"][k]["p_two_sided"] * (len(ks) - i))); res["paired"][k]["p_holm"] = run
    json.dump(res, open(OUT / "FINAL_RESULTS.json", "w"), indent=1, default=float)
    rows = []
    for n in SPEC:
        for k in ("LR", "GBM"):
            s = M(n, k); rows += [(p, n, k, float(s[i])) for i, p in enumerate(df.pair_id)]
    pr = pd.DataFrame(rows, columns=["pair_id", "model", "clf", "oof_score_mean3seeds"]); pr = pr.merge(df[["pair_id", "label", "status", "transformation_type"]], on="pair_id")
    pr.to_csv(OUT / "predictions_final.csv", index=False); print("done", round(time.time() - t0), "s;", "selected:", rule["selected_by_rule"], flush=True)
if __name__ == "__main__": main()

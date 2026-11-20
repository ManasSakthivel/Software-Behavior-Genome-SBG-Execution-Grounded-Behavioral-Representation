"""Multi-seed ablations, paired V5-vs-V6, edit-size strata, pooled LOFO and the predeclared selection rule (DEV only).
Reads only features_v8train/val. Rule operationalisation: artifacts/v6/audit/SELECTION_RULE_OPERATIONALISATION.json (fixed beforehand).
  python experiments/v6/audit_selection.py  -> artifacts/v6/audit/{OOF.npz,SELECTION_RESULTS.json}
"""
import json, sys, pathlib, itertools
import numpy as np
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.v6.evaluate import *   # noqa
OUT = REPO / "artifacts/v6/audit"
CONVC = STAT + ["edit_lines"] + EXV
CFG = ["cfg0", "cfg1", "cfg2"]; EVID = ["alpha", "conf", "st_act", "st_nact", "st_unk"]
SETS = {"V5": V5C, "FAM-A": ["d_A"], "FAM-B": ["d_B", "g"], "FAM-C": ["d_C"] + CFG, "FAM-E": EVID + ["g"], "V6": V6C,
        "V6-A": [c for c in V6C if c != "d_A"], "V6-B": [c for c in V6C if c not in ("d_B", "g")],
        "V6-C": [c for c in V6C if c not in ["d_C"] + CFG], "V6-E": [c for c in V6C if c not in EVID + ["g"]],
        "V6+R": V6C + ["d_R"], "V6+temporal": V6C + ["sbg_temporal"], "V6-cfg": [c for c in V6C if c not in CFG]}
DF = None
def _df():
    global DF
    if DF is None: DF = load(["v8train", "v8val"])
    return DF
def task(a):
    name, ctx, kind, mode = a            # mode: seed int or "lofo"
    df = _df(); y, g, t = df.label.values.astype(int), df.base_id.values, df.transformation_type.values
    cols = (CONVC if ctx == "CONV+" else []) + (SETS[name] if name != "CONV" else [])
    X = df[cols].values; oof = np.zeros(len(df))
    sp = folds(g, mode) if mode != "lofo" else [(np.where(t != u)[0], np.where(t == u)[0]) for u in sorted(set(t))]
    for tr, te in sp:
        oof[te] = fit_predict(kind, X[tr], y[tr], g[tr], X[te])[0]
    return a, oof
def _pair(a):
    n, s, base, y, g = a; d, ci = delta(y, s, base, g)
    p = cluster_perm_p(y, s, base, g, B=1000); p2 = cluster_perm_p(y, base, s, g, B=1000)
    return n, d, ci, min(1.0, 2 * min(p, p2))
def delta(y, s1, s2, g, B=2000):
    return auroc(y, s1) - auroc(y, s2), cluster_boot(y, s1, g, B=B, s2=s2)
def main():
    df = _df(); y, g = df.label.values.astype(int), df.base_id.values
    jobs = []
    for kind in ("LR", "GBM"):
        for n in SETS: jobs += [(n, "alone", kind, s) for s in SEEDS] + [(n, "alone", kind, "lofo")]
        for n in ["CONV"] + list(SETS):
            if n != "CONV" and (n.startswith("V6") and n not in ("V6", "V6-A", "V6-B", "V6-C", "V6-E", "V6+R")): continue
            jobs += [(n, "CONV+", kind, s) for s in SEEDS] + ([(n, "CONV+", kind, "lofo")] if n in ("CONV", "V5", "V6") else [])
    if (OUT / "OOF.npz").exists():   # reuse the saved out-of-fold scores (fits are deterministic given seeds)
        Z = np.load(OUT / "OOF.npz"); R = {}
        for k in Z.files:
            a = k.split("|"); R[(a[0], a[1], a[2], a[3] if a[3] == "lofo" else int(a[3]))] = Z[k]
    else:
        with ProcessPoolExecutor(12) as ex:
            R = dict(ex.map(task, jobs))
        np.savez_compressed(OUT / "OOF.npz", **{"|".join(map(str, k)): v for k, v in R.items()})
    def M(n, ctx, kind):  return np.mean([R[(n, ctx, kind, s)] for s in SEEDS], 0)
    def L(n, ctx, kind):  return R[(n, ctx, kind, "lofo")]
    q = pd.qcut(df.edit_lines.fillna(df.edit_lines.median()).rank(method="first"), 3, labels=["small", "mid", "large"]).values
    res = {"seeds": list(SEEDS), "table": {}, "paired_vs_V6": {}, "paired_V5_vs_V6": {}, "rule": {}}
    for kind in ("LR", "GBM"):
        for ctx in ("alone", "CONV+"):
            for n in (["CONV"] if ctx == "CONV+" else []) + list(SETS):
                if (n, ctx, kind, SEEDS[0]) not in R: continue
                s = M(n, ctx, kind); per = [auroc(y, R[(n, ctx, kind, sd)]) for sd in SEEDS]
                res["table"][f"{ctx}|{n}|{kind}"] = {"auroc_meanscore": auroc(y, s), "per_seed": per, "seed_sd": float(np.std(per)),
                    "ci95": list(cluster_boot(y, s, g, B=1000)), "lofo_pooled": auroc(y, L(n, ctx, kind)) if (n, ctx, kind, "lofo") in R else None,
                    "strata": {k: auroc(y[q == k], s[q == k]) for k in ("small", "mid", "large")}}
    # paired contrasts vs V6 full, identical folds/seeds/families; Holm within each (ctx,kind) family
    for kind in ("LR", "GBM"):
        for ctx, ref in (("alone", "V6"), ("CONV+", "CONV")):
            base = M(ref if ctx == "alone" else "CONV", ctx, kind)
            fam = []
            for n in SETS:
                if n == ref or (n, ctx, kind, SEEDS[0]) not in R: continue
                fam.append((n, M(n, ctx, kind)))
            with ProcessPoolExecutor(12) as ex:
                out = list(ex.map(_pair, [(n, s, base, y, g) for n, s in fam]))
            fam = [list(o) for o in out]
            fam.sort(key=lambda r: r[3]); m = len(fam); run = 0
            for i, r in enumerate(fam):
                run = max(run, min(1.0, r[3] * (m - i))); r.append(run)
            res["paired_vs_V6"][f"{ctx}|{kind}|ref={ref}"] = [{"variant": r[0], "delta": r[1], "ci95": r[2], "p_two_sided": r[3], "p_holm": r[4]} for r in fam]
    for kind in ("LR", "GBM"):
        for ctx in ("alone", "CONV+"):
            a, b = M("V6", ctx, kind), M("V5", ctx, kind)
            d, ci = delta(y, a, b, g); res["paired_V5_vs_V6"][f"{ctx}|{kind}"] = {"delta_V6_minus_V5": d, "ci95": ci,
                "p_two_sided": min(1, 2 * min(cluster_perm_p(y, a, b, g, B=1000), cluster_perm_p(y, b, a, g, B=1000))),
                "per_seed_delta": [auroc(y, R[("V6", ctx, kind, s)]) - auroc(y, R[("V5", ctx, kind, s)]) for s in SEEDS],
                "lofo_delta": auroc(y, L("V6", ctx, kind)) - auroc(y, L("V5", ctx, kind)) if ("V6", ctx, kind, "lofo") in R else None}
    # ---- predeclared selection rule, mechanically (LR, oracle-free, 'alone') ----
    cands = ["V5", "FAM-A", "FAM-B", "FAM-C", "FAM-E", "V6", "V6-A", "V6-B", "V6-C", "V6-E"]
    nfeat = {c: len(SETS[c]) for c in cands}
    prim = {c: auroc(y, M(c, "alone", "LR")) for c in cands}; best = max(prim, key=prim.get)
    rule = {"primary_auroc": prim, "best": best, "n_features": nfeat, "candidates": {}}
    for c in cands:
        s, sb = M(c, "alone", "LR"), M(best, "alone", "LR")
        d, ci = delta(y, s, sb, g) if c != best else (0.0, (0.0, 0.0))
        ni = {}
        for st in ("small", "mid", "large"):
            m = q == st; ni[st] = (list(delta(y[m], s[m], sb[m], g[m])[1]) if c != best else [0, 0])
        ni["LOFO"] = list(delta(y, L(c, "alone", "LR"), L(best, "alone", "LR"), g)[1]) if c != best else [0, 0]
        ok_ni = all(v[0] > -0.02 for v in ni.values()); tie = ci[0] <= 0 <= ci[1]
        rule["candidates"][c] = {"delta_vs_best": d, "ci95": list(ci), "ties_best": bool(tie), "noninferior_lower95": ni, "noninferior": bool(ok_ni)}
    elig = [c for c, v in rule["candidates"].items() if v["ties_best"] and v["noninferior"]]
    rule["eligible_after_tie_and_noninferiority"] = elig
    rule["selected_by_rule"] = min(elig, key=lambda c: (nfeat[c], c))
    # raw-distance track
    rawc = {"d_A": "d_A", "d_B": "d_B", "d_C": "d_C", "V6raw": "d_v6", "V5raw": "sbg_v5"}
    rule["raw_track"] = {k: auroc(y, neutral(df, c).values) for k, c in rawc.items()}
    res["rule"] = rule
    json.dump(res, open(OUT / "SELECTION_RESULTS.json", "w"), indent=1, default=float)
    print(json.dumps(rule, indent=1, default=float)[:3000])
if __name__ == "__main__": main()

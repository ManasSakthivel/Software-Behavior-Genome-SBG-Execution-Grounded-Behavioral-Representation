"""DEV evaluation (grouped CV) per reports/v6_redesign/spec/SBG_V6_EXPERIMENTAL_PROTOCOL.md.

  python experiments/v6/evaluate.py dev            # fit/evaluate on v8 train+val only
Also importable: `load`, `FEATSETS`, `make_model`, `fit_predict` for the frozen post-freeze runs.
All raw per-pair predictions are written to artifacts/v6/predictions_<tag>.csv.
"""
import json, pathlib, sys, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
REPO = pathlib.Path(__file__).resolve().parents[2]
ART = REPO / "artifacts" / "v6"
SEEDS = (42, 43, 44)
STAT = ["static_token", "static_ast"]
EXV = ["call_count", "coverage_size", "n_functions", "exception_fraction"]
V5C = ["sbg_v3", "sbg_temporal", "sbg_state"]
V6C = ["d_A", "d_B", "d_C", "cfg0", "cfg1", "cfg2", "g", "alpha", "conf", "st_act", "st_nact", "st_unk"]
FEATSETS = {
    "EDIT": STAT + ["edit_lines"], "EXECVOL": EXV, "CONV": STAT + ["edit_lines"] + EXV,
    "V5": V5C, "V6": V6C,
    "CONV+V5": STAT + ["edit_lines"] + EXV + V5C, "CONV+V6": STAT + ["edit_lines"] + EXV + V6C,
    # R2 (oracle-available): differential testing is mandatory
    "DIFF": ["delta_out"], "CONV+DIFF": STAT + ["edit_lines"] + EXV + ["delta_out"],
    "V6+R": V6C + ["d_R"], "CONV+V6+R": STAT + ["edit_lines"] + EXV + V6C + ["d_R"],
    "CONV+DIFF+V6": STAT + ["edit_lines"] + EXV + ["delta_out"] + V6C,
}
RAW = {"V5raw": "sbg_v5", "V6raw": "d_v6", "d_A": "d_A", "d_B": "d_B", "d_C": "d_C", "g": "g",
       "static_token": "static_token", "static_ast": "static_ast", "edit_lines": "edit_lines",
       "call_count": "call_count", "coverage_size": "coverage_size", "temporal(V5)": "sbg_temporal",
       "state(V5)": "sbg_state", "delta_out(R2)": "delta_out"}


def load(names):
    rows = []
    for n in names:
        for l in open(ART / f"features_{n}.jsonl"):
            r = json.loads(l)
            d = {k: r.get(k) for k in ("pair_id", "base_id", "label", "transformation_type", "split", "status",
                                       "d_A", "d_B", "d_C", "d_R", "delta_out", "g", "alpha", "conf", "d_v6",
                                       "edit_lines", "v5_evaluated")}
            for k, v in (r.get("v5_stored") or {}).items():
                d[k] = v
            cs = r.get("cfg_size") or [None] * 3
            d.update(cfg0=cs[0], cfg1=cs[1], cfg2=cs[2], st_act=r["status"] == "ACTIVATED",
                     st_nact=r["status"] == "NOT_ACTIVATED", st_unk=r["status"] == "UNKNOWN")
            rows.append(d)
    df = pd.DataFrame(rows)
    for c in set(sum(FEATSETS.values(), [])) | set(RAW.values()):
        if c not in df:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c].astype(float), errors="coerce")
    return df


def make_model(kind, **hp):
    if kind == "LR":
        return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                             LogisticRegression(max_iter=2000, **hp))
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                         HistGradientBoostingClassifier(random_state=0, **hp))


GRID = {"LR": {"logisticregression__C": [0.1, 1, 10]},
        "GBM": {"histgradientboostingclassifier__max_depth": [2, 3],
                "histgradientboostingclassifier__max_iter": [50, 100]}}


def _logit(q):
    q = np.clip(q, 1e-6, 1 - 1e-6)
    return np.log(q / (1 - q)).reshape(-1, 1)


def fit_predict(kind, Xtr, ytr, gtr, Xte):
    """Inner grouped-CV tuning on the training fold only; Platt calibration on inner OOF scores."""
    gs = GridSearchCV(make_model(kind), GRID[kind], cv=GroupKFold(3), scoring="roc_auc", n_jobs=1)
    gs.fit(Xtr, ytr, groups=gtr)
    p = gs.best_estimator_.predict_proba(Xte)[:, 1]
    oof = np.zeros(len(ytr))
    for a, b in GroupKFold(3).split(Xtr, ytr, gtr):
        oof[b] = make_model(kind).set_params(**gs.best_params_).fit(Xtr[a], ytr[a]).predict_proba(Xtr[b])[:, 1]
    pl = LogisticRegression().fit(_logit(oof), ytr)
    return p, pl.predict_proba(_logit(p))[:, 1], gs.best_params_


def folds(groups, seed, k=5):
    ug = np.array(sorted(set(groups)))
    np.random.RandomState(seed).shuffle(ug)
    fid = {g: i % k for i, g in enumerate(ug)}
    f = np.array([fid[g] for g in groups])
    return [(np.where(f != i)[0], np.where(f == i)[0]) for i in range(k)]


def auroc(y, s):
    return float("nan") if len(set(y)) < 2 else roc_auc_score(y, s)


def cluster_boot(y, s, g, B=2000, seed=42, s2=None):
    """Program-cluster bootstrap. If s2 given: paired delta AUROC(s)-AUROC(s2)."""
    rs, ug = np.random.RandomState(seed), np.unique(g)
    idx = {u: np.where(g == u)[0] for u in ug}
    out = []
    for _ in range(B):
        ii = np.concatenate([idx[u] for u in rs.choice(ug, len(ug))])
        a = auroc(y[ii], s[ii])
        out.append(a - auroc(y[ii], s2[ii]) if s2 is not None else a)
    out = np.array(out)
    return float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


def cluster_perm_p(y, s1, s2, g, B=2000, seed=42):
    """Paired cluster permutation test for AUROC(s1) > AUROC(s2) (swap the two models' scores per cluster)."""
    rs, ug = np.random.RandomState(seed), np.unique(g)
    obs = auroc(y, s1) - auroc(y, s2)
    gi = {u: np.where(g == u)[0] for u in ug}
    ge = 0
    for _ in range(B):
        a, b = s1.copy(), s2.copy()
        for u in ug:
            if rs.rand() < 0.5:
                ii = gi[u]; a[ii], b[ii] = s2[ii], s1[ii]
        ge += (auroc(y, a) - auroc(y, b)) >= obs
    return (ge + 1) / (B + 1)


def ece(y, p, bins=10):
    e, n = 0.0, len(y)
    b = np.minimum((p * bins).astype(int), bins - 1)
    for i in range(bins):
        m = b == i
        if m.any():
            e += m.sum() / n * abs(y[m].mean() - p[m].mean())
    return e


def neutral(df, col, ref=None):
    """Abstained/undefined -> median of the reference scores; never silently 0."""
    ref = df[col] if ref is None else ref
    return df[col].fillna(ref.median())


def run_dev(tag="dev"):
    df = load(["v8train", "v8val"])
    y, g = df.label.values.astype(int), df.base_id.values
    res = {"n_pairs": len(df), "n_programs": int(df.base_id.nunique()), "n_changed": int(y.sum()),
           "status_counts": df.status.value_counts().to_dict(),
           "v5_not_evaluated": int((~df.v5_evaluated.astype(bool)).sum())}
    raw = {}
    for name, col in RAW.items():
        s = neutral(df, col).values
        ev = df[col].notna().values
        a = auroc(y, s)
        raw[name] = {"auroc_forward": a, "auroc_reversed": 1 - a, "ci95_forward": list(cluster_boot(y, s, g)),
                     "n_undefined": int((~ev).sum()),
                     "auroc_forward_evaluable_only": auroc(y[ev], df[col].values[ev]) if ev.sum() else None}
    res["raw"] = raw
    preds, mean_oof = [], {}
    for fs, cols in FEATSETS.items():
        X = df[cols].values
        for kind in ("LR", "GBM"):
            oof = np.zeros((len(SEEDS), len(df))); cal = np.zeros_like(oof)
            for si, seed in enumerate(SEEDS):
                for tr, te in folds(g, seed):
                    oof[si, te], cal[si, te], _ = fit_predict(kind, X[tr], y[tr], g[tr], X[te])
            m, mc = oof.mean(0), cal.mean(0)
            mean_oof[(fs, kind)] = m
            per_seed = [auroc(y, oof[i]) for i in range(len(SEEDS))]
            lo, hi = cluster_boot(y, m, g, B=1000)
            res.setdefault("cv", {})[f"{fs}|{kind}"] = {
                "auroc_seed_mean": float(np.mean(per_seed)), "auroc_seeds": per_seed, "auroc_meanscore": auroc(y, m),
                "ci95_cluster_boot": [lo, hi], "ap": float(average_precision_score(y, m)),
                "brier_raw": float(brier_score_loss(y, m)), "ece_raw": float(ece(y, m)),
                "brier_platt": float(brier_score_loss(y, mc)), "ece_platt": float(ece(y, mc))}
            preds += [(pid, fs, kind, float(m[i]), float(mc[i])) for i, pid in enumerate(df.pair_id)]
            print(f"{fs:14s}{kind:4s} AUROC {np.mean(per_seed):.3f} [{lo:.3f},{hi:.3f}]", flush=True)
    pd.DataFrame(preds, columns=["pair_id", "featset", "model", "oof_score", "oof_score_platt"]).to_csv(
        ART / f"predictions_{tag}.csv", index=False)
    cmp = {}
    for kind in ("LR", "GBM"):
        for a, b in (("CONV+V6", "CONV"), ("CONV+V5", "CONV"), ("V6", "V5"), ("V6", "CONV"), ("V5", "CONV"),
                     ("CONV+V6", "CONV+V5"), ("CONV+DIFF+V6", "CONV+DIFF"), ("CONV+V6+R", "CONV+DIFF")):
            s1, s2 = mean_oof[(a, kind)], mean_oof[(b, kind)]
            cmp[f"{a} vs {b} [{kind}]"] = {"delta_auroc": auroc(y, s1) - auroc(y, s2),
                                           "ci95": list(cluster_boot(y, s1, g, B=1000, s2=s2)),
                                           "perm_p_one_sided": cluster_perm_p(y, s1, s2, g, B=500)}
    v6 = neutral(df, "d_v6").values
    for b in ("sbg_v5", "static_token", "static_ast", "edit_lines"):
        sb = neutral(df, b).values
        for orient, sgn in (("forward", 1), ("reversed", -1)):
            s2 = sgn * sb
            cmp[f"V6raw vs {b} ({orient})"] = {"delta_auroc": auroc(y, v6) - auroc(y, s2),
                                              "ci95": list(cluster_boot(y, v6, g, B=1000, s2=s2)),
                                              "perm_p_one_sided": cluster_perm_p(y, v6, s2, g, B=500)}
    res["paired"] = cmp
    q = pd.qcut(df.edit_lines.fillna(df.edit_lines.median()).rank(method="first"), 3, labels=["small", "mid", "large"])
    strat = {}
    for lab in ("small", "mid", "large"):
        m = (q == lab).values
        d = {"n": int(m.sum()), "frac_changed": float(y[m].mean())}
        for name, col in (("V5raw", "sbg_v5"), ("V6raw", "d_v6"), ("static_token", "static_token"), ("edit_lines", "edit_lines")):
            d[name] = auroc(y[m], neutral(df, col).values[m])
        for key in (("CONV", "LR"), ("V5", "LR"), ("V6", "LR"), ("CONV+V6", "LR"), ("CONV+V6", "GBM"), ("CONV", "GBM")):
            d[f"{key[0]}|{key[1]}"] = auroc(y[m], mean_oof[key][m])
        strat[lab] = d
    res["edit_size_stratified"] = strat
    pt, eq = {}, (y == 0)
    for t in sorted(df.transformation_type.unique()):
        m = (df.transformation_type == t).values
        if y[m].mean() == 1:
            mm = m | eq
            pt[t] = {"n": int(m.sum()), "V6raw": auroc(y[mm], v6[mm]), "V5raw": auroc(y[mm], neutral(df, "sbg_v5").values[mm]),
                     "delta_out_detect_rate": float((df.delta_out[m] > 0).mean())}
    res["per_changed_type"] = pt
    res["label_validity_R2"] = {
        "equiv_pairs_with_output_diff": int(((df.delta_out > 0) & eq).sum()), "equiv_total": int(eq.sum()),
        "changed_pairs_with_no_output_diff": int(((df.delta_out == 0) & ~eq).sum()), "changed_total": int((~eq).sum())}
    (ART / f"RESULTS_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    run_dev(sys.argv[1] if len(sys.argv) > 1 else "dev")

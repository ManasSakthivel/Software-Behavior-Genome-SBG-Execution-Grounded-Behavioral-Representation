"""V8 Mac statistical reanalysis. DEVELOPMENT DATA ONLY, EXPLORATORY, NOT INDEPENDENT VALIDATION. Never touches existing results/v8_dev_* outputs.
usage: .venv/bin/python experiments/v8/run_mac_reanalysis.py [--records datasets/v8/dev_records.jsonl] [--boot 10000] [--perms 100] [--quick]
Writes results/v8_mac_reanalysis_<ts>/{<policy>/..., slope_diagnostics_<policy>.json, ers_placebo_<policy>.json, run_meta.json}. Both eligibility policies (sbgv8.policy v8.0, v8.1)."""
import argparse, datetime, hashlib, json, os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT)
from sbgv8 import baselines, calibrate, evaluate, policy, schema, stats  # noqa: E402

POLICIES = ("v8.0", "v8.1")
LAMS = (0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 1000.0)
SETS = {"b7_cov_only": schema.FEATURE_SETS["cov_only"], "cov_rep": schema.FEATURE_SETS["cov_rep"], "cov_mult": schema.FEATURE_SETS["cov_mult"],
        "cov_infl": schema.FEATURE_SETS["cov_infl"], "mult_only": ["mu_min"], "b9_full_profile": schema.FEATURE_SETS["full_profile"]}
jd = lambda o: o.tolist() if hasattr(o, "tolist") else str(o)


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def oof_fixed(recs, names, seed, lam, k=5):
    """Project-grouped outer-fold predictions with a FIXED ridge penalty (no inner selection)."""
    return calibrate.oof_risks(recs, names, k, seed, lam)


def baserate_oof(recs, seed, k=5):
    fold = stats.project_folds([r.project for r in recs], k, seed); out = np.full(len(recs), 0.5)
    for f in set(fold):
        tr = [r.y for r, g in zip(recs, fold) if g != f and calibrate.is_eligible(r)]
        out[fold == f] = np.clip(np.mean(tr) if tr else 0.5, 1e-3, 1 - 1e-3)
    return out


def metrics(p, y, el):
    a, b = stats.calibration_slope_intercept(p[el], y[el])
    return {"logloss": stats.logloss(p[el], y[el]), "brier": stats.brier(p[el], y[el]), "slope": b, "intercept": a}


def summ(v):
    v = np.array([x for x in v if x == x]); return {"median": float(np.median(v)), "q10": float(np.quantile(v, .1)), "q90": float(np.quantile(v, .9)), "min": float(v.min()), "max": float(v.max()), "n": int(len(v))}


def slope_diagnostics(recs, n_seeds, n_null, B):
    y = np.array([r.y for r in recs], float); proj = np.array([r.project for r in recs]); el = np.array([calibrate.is_eligible(r) for r in recs])
    out = {"n_labelled": len(recs), "n_eligible": int(el.sum()), "eligible_base_rate": float(y[el].mean()), "n_eligible_projects": len(set(proj[el])),
           "eligible_by_project_top5": sorted(((u, int((proj[el] == u).sum())) for u in set(proj[el])), key=lambda t: -t[1])[:5],
           "eligible_power_icc": stats.power_report(proj, y, el)}
    out["eligible_by_arm"] = {a: {"n": sum(1 for r, e in zip(recs, el) if e and r.meta.get("arm") == a), "y1": int(sum(r.y for r, e in zip(recs, el) if e and r.meta.get("arm") == a))}
                              for a in sorted({r.meta.get("arm") for r in recs})}
    # (1) fold-assignment seeds x lambda: distribution of OOF slope / log loss
    grid = {}
    for sn, names in SETS.items():
        for lam in LAMS:
            ms = [metrics(oof_fixed(recs, names, s, lam), y, el) for s in range(n_seeds)]
            grid[f"{sn}|lam={lam}"] = {k: summ([m[k] for m in ms]) for k in ("slope", "intercept", "logloss", "brier")}
    out["seed_lambda_grid"] = grid
    br = [metrics(baserate_oof(recs, s), y, el) for s in range(n_seeds)]; out["base_rate_predictor"] = {k: summ([m[k] for m in br]) for k in ("logloss", "brier")}
    # (2) selected-lambda (inner-CV) pipeline, as in evaluate.run, across seeds
    sel = {}
    for sn in ("b7_cov_only", "b9_full_profile", "mult_only"):
        ms = []
        for s in range(min(n_seeds, 10)):
            fold = stats.project_folds(proj, 5, s); sc, e2, _, cf = evaluate._cv_model(recs, sn, fold, sorted(set(fold)), s, 60, None, None, {}, SETS[sn], False)
            ms.append({**metrics(sc, y, e2), "lambdas": [c["lambda"] for c in cf]})
        sel[sn] = {**{k: summ([m[k] for m in ms]) for k in ("slope", "intercept", "logloss")}, "chosen_lambdas": sorted({l for m in ms for l in m["lambdas"]})}
    out["selected_lambda_pipeline"] = sel
    # (3) cluster-bootstrap slope CI, seed 0, lam=1 and lam=100
    out["slope_cluster_ci_seed0"] = {f"{sn}|lam={lam}": {**metrics(p := oof_fixed(recs, SETS[sn], 0, lam), y, el), **stats.slope_cluster_ci(p[el], y[el], proj[el], B, 0)}
                                     for sn in ("b7_cov_only", "b9_full_profile", "mult_only") for lam in (1.0, 100.0)}
    # (4) null: shuffle y among eligible records -> OOF slope distribution of a predictor with NO signal (what slope does this pipeline give for pure noise?)
    rng = np.random.default_rng(0); idx = np.flatnonzero(el); nul = {}
    for sn in ("b7_cov_only", "b9_full_profile"):
        sl = []
        for _ in range(n_null):
            yp = y.copy(); yp[idx] = y[rng.permutation(idx)]
            rp = [r for r in recs]; saved = [r.y for r in recs]
            for r, v in zip(rp, yp): r.y = int(v)
            try: p = oof_fixed(rp, SETS[sn], 0, 1.0); sl.append(stats.calibration_slope_intercept(p[el], yp[el])[1])
            finally:
                for r, v in zip(rp, saved): r.y = v
        nul[sn] = {**summ(sl), "observed_slope_seed0_lam1": metrics(oof_fixed(recs, SETS[sn], 0, 1.0), y, el)["slope"]}
        nul[sn]["frac_null_slope_le_observed"] = float(np.mean(np.array(sl) <= nul[sn]["observed_slope_seed0_lam1"]))
    out["permuted_y_null_slope"] = nul
    # (5) dominant project / arm removal, seed 0, lam=1
    sub = {}
    for label, keep in (("all", np.ones(len(recs), bool)), ("without_quixbugs_project", proj != "quixbugs"),
                        ("without_quixbugs_neg_arm", np.array([r.meta.get("arm") != "quixbugs_neg" for r in recs]))):
        rr = [r for r, k in zip(recs, keep) if k]
        if len(rr) < 20: continue
        yy = np.array([r.y for r in rr], float); ee = np.array([calibrate.is_eligible(r) for r in rr])
        sub[label] = {sn: {**metrics(oof_fixed(rr, SETS[sn], 0, 1.0), yy, ee), "n_eligible": int(ee.sum())} for sn in ("b7_cov_only", "b9_full_profile", "mult_only")}
    out["dominant_removal_seed0_lam1"] = sub
    # (6) separation / dead features: nearly unpenalised full-profile fit on eligible
    m = calibrate.fit(recs, SETS["b9_full_profile"], lam=1e-4); X = np.array([[calibrate.default_profile(r)[n] for n in schema.FEATURES] for r in recs])[el]
    pin = np.array([m.predict_risk(r) for r, e in zip(recs, el) if e]); ye = y[el]
    out["separation"] = {"insample_pred_lt_0.02_or_gt_0.98": float(np.mean((pin < .02) | (pin > .98))), "insample_logloss_lam1e-4": stats.logloss(pin, ye),
                         "max_abs_std_coef": float(np.abs(m.coef).max()), "constant_features_among_eligible": [n for n, s in zip(schema.FEATURES, X.std(0)) if s < 1e-12],
                         "act_frac_distinct": sorted({round(float(v), 3) for v in X[:, 0]}), "branch_cov_min_distinct_n": int(len(set(np.round(X[:, 1], 3))))}
    # (7) cov_act == cov_only (dedupe): identical predictions
    a = oof_fixed(recs, schema.FEATURE_SETS["cov_act"], 0, 1.0); b = oof_fixed(recs, schema.FEATURE_SETS["cov_only"], 0, 1.0)
    out["cov_act_identical_to_cov_only"] = bool(np.allclose(a, b))
    # (8) paired project-cluster logloss: each set vs base rate, vs b7 (seed 0, lam=1 and 100)
    pc = {}
    for lam in (1.0, 100.0):
        base = baserate_oof(recs, 0); P = {sn: oof_fixed(recs, nm, 0, lam) for sn, nm in SETS.items()}
        for sn in SETS:
            pc[f"{sn}|lam={lam}|vs_base_rate"] = stats.paired_logloss(P[sn][el], base[el], y[el], proj[el], B, 0)
            if sn != "b7_cov_only": pc[f"{sn}|lam={lam}|vs_b7"] = stats.paired_logloss(P[sn][el], P["b7_cov_only"][el], y[el], proj[el], B, 0)
    out["paired_logloss_note"] = "point = logloss(reference) - logloss(set); positive = set better"; out["paired_logloss"] = pc
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--records", default=os.path.join(ROOT, "datasets/v8/dev_records.jsonl"))
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--boot-extra", type=int, default=2000); ap.add_argument("--perms", type=int, default=100)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2]); ap.add_argument("--slope-seeds", type=int, default=20); ap.add_argument("--null-reps", type=int, default=100)
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--tag", default=""); a = ap.parse_args()
    if a.quick: a.boot = a.boot_extra = 200; a.perms = 5; a.slope_seeds = 3; a.null_reps = 5; a.seeds = [0]
    allrecs = evaluate.load_records(a.records); lab = sorted([r for r in allrecs if r.y is not None], key=lambda r: (r.project, r.pair_id))
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out = os.path.join(ROOT, f"results/v8_mac_reanalysis_{ts}{a.tag}"); os.makedirs(out)
    meta = {"records": a.records, "records_sha256_16": sha(a.records), "timestamp": ts, "args": vars(a), "n_records": len(allrecs), "n_labelled": len(lab),
            "code_sha256_16": {f: sha(os.path.join(ROOT, f)) for f in ("sbgv8/policy.py", "sbgv8/calibrate.py", "sbgv8/evaluate.py", "sbgv8/stats.py", "sbgv8/baselines.py", "sbgv8/ers.py", "sbgv8/perturb.py", "sbgv8/profile.py")},
            "note": "ers.py/perturb.py are owned by another agent and may change; hashes pin the code used"}
    json.dump(meta, open(os.path.join(out, "run_meta.json"), "w"), indent=1)
    for pol in POLICIES:
        with policy.use(pol):
            for k, s in enumerate(a.seeds):
                r = evaluate.run(allrecs, os.path.join(out, pol, f"seed{s}"), s, B=a.boot if k == 0 else a.boot_extra, policy_name=pol)
                fr = evaluate.frozen_eval(allrecs, s, B=a.boot if k == 0 else a.boot_extra)
                json.dump(fr, open(os.path.join(out, pol, f"seed{s}", "frozen_threshold.json"), "w"), indent=1, default=jd)
                print(pol, "seed", s, "eligible n", r["systems"][-1].get("n_eligible_scored"), "ERS:", r.get("ers_added_value"), flush=True)
            json.dump(slope_diagnostics(lab, a.slope_seeds, a.null_reps, min(a.boot, 2000)), open(os.path.join(out, f"slope_diagnostics_{pol}.json"), "w"), indent=1, default=jd)
            pl = [evaluate.ers_placebo(allrecs, s, n_perm=a.perms) for s in a.seeds]
            json.dump(pl, open(os.path.join(out, f"ers_placebo_{pol}.json"), "w"), indent=1, default=jd)
            print(pol, "placebo", [(round(p.get("observed_gain_b9_minus_b8", float("nan")), 4), p.get("placebo_p")) for p in pl], flush=True)
    print("wrote", out)


if __name__ == "__main__":
    main()

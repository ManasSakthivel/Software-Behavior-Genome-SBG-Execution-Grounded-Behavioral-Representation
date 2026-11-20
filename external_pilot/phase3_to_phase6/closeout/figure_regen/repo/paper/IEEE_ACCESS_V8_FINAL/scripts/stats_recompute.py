"""Statistical audit recomputation for the SBG V8 IEEE Access manuscript. READ-ONLY on repo data/results.
DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION (datasets/v8/dev_records.jsonl; generator labels, design-exposed).

usage (from the worktree root):
  PYTHONPATH=. <python> paper/IEEE_ACCESS_V8_FINAL/scripts/stats_recompute.py [--refit] [--B 10000]
Writes paper/IEEE_ACCESS_V8_FINAL/audit/{stats_summary.json, oof_seed0.json}. Nothing else is written.

What is recomputed vs read:
  * denominators, rule baselines (b1-b5), b6 reference: recomputed from raw records (repo decision rules; own project-cluster bootstrap).
  * model systems (b7, b9, b8, ablations): no per-pair predictions were saved by the Linux runs, so the seed-0 out-of-fold predictions are
    regenerated with the repo's own CV code (evaluate._cv_model; same seed, folds, fit_B=500 as run_dev_evaluation.py) and checked against
    the saved results.json (log loss / Brier / slope must match). Metrics, CIs, matched-coverage risks and curves are then computed here.
  * seeds 1-4, primary contrasts, Holm, ERS verdicts: read from the saved Linux results.json (verified-from-raw-output, not re-run).
  * mac-hardening post-fix numbers: read from /Users/.../SBG-V6 results (mac-hardening branch, post-fix, not on linux branch).
No holdout/hidden labels are read; the five-dataset cohort is only counted (no labels exist).
"""
from __future__ import annotations
import argparse, collections, glob, json, math, os, sys, time
import numpy as np
from scipy import stats as sps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from sbgv8 import baselines, calibrate, evaluate, policy, stats  # noqa: E402

AUDIT = os.path.join(ROOT, "paper/IEEE_ACCESS_V8_FINAL/audit")
REC = os.path.join(ROOT, "datasets/v8/dev_records.jsonl")
SOFT = os.path.join(ROOT, "results/v8_dev_eval_20261119_055209_linux_soft")
STRICT = os.path.join(ROOT, "results/v8_dev_eval_20261119_060213_linux_strict")
MAC = "/Users/manassakthivel/Desktop/SBG-V6/results"
MAC_PRE = os.path.join(MAC, "v8_mac_reanalysis_20261118_210512")            # committed on mac branch (8e28f601), pre-fix
MAC_POST = os.path.join(MAC, "v8_mac_reanalysis_20261118_222059_profilefix2")  # committed on mac branch (b9b8a86c), post-fix
MAC_HIST = os.path.join(MAC, "v8_dev_eval_20261118_200754")                  # UNCOMMITTED on mac branch, historical dev run
IV = os.path.join(ROOT, "results/v8/independent-validation")
MODELS = ["b7_cov_calibration", "abl_cov_rep", "abl_cov_infl", "abl_cov_mult", "abl_cov_prov", "abl_mult_only", "b9_cec_no_ers", "b8_full_cec"]
RULES = list(baselines.RULE_NAMES)


def jload(p):
    with open(p) as f: return json.load(f)


def nan2none(o):
    if isinstance(o, float): return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict): return {str(k): nan2none(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [nan2none(v) for v in o]
    if isinstance(o, (np.floating,)): return nan2none(float(o))
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.ndarray): return nan2none(o.tolist())
    return o


# ---------------- independent statistics (own implementation, not stats.py) ----------------
def cluster_weights(proj, B, seed):
    """B x N project-cluster bootstrap multiplicities (own RNG stream; independent of stats.cluster_counts)."""
    u, idx = np.unique(np.asarray(proj).astype(str), return_inverse=True)
    cnt = np.random.default_rng(seed).multinomial(len(u), np.full(len(u), 1 / len(u)), size=B)
    return cnt[:, idx].astype(float)


def pct(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    return [float(np.quantile(r, .025)), float(np.quantile(r, .975))] if len(r) else [None, None]


def wilson(k, n, z=1.959964):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def risk_ci(y, ndo, W):
    num = (W * ndo * y).sum(1); den = (W * ndo).sum(1)
    return pct(np.where(den > 0, num / np.where(den > 0, den, 1), np.nan))


def metric_ci(fn, y, p, W):
    """fn(y, p) evaluated on each project-cluster resample (rows replicated by multiplicity)."""
    reps = []
    for w in W:
        m = w > 0
        reps.append(fn(np.repeat(y[m], w[m].astype(int)), np.repeat(p[m], w[m].astype(int))))
    return pct(reps)


def holm(p):
    return stats.holm(p).tolist()


# ---------------- part 1: denominators from raw records ----------------
def denominators():
    raw = [json.loads(l) for l in open(REC) if l.strip()]
    lab = [r for r in raw if r.get("y") is not None]
    proj = collections.Counter(r["project"] for r in lab)
    top, ntop = proj.most_common(1)[0]
    fam = collections.Counter(r.get("family") for r in lab)
    return {"source": "datasets/v8/dev_records.jsonl (md5 07e57a80a2d9060d42748626e0819436; identical on mac-hardening branch)",
            "n_records": len(raw), "n_labelled": len(lab), "n_unresolved_y_none": len(raw) - len(lab), "n_projects_labelled": len(proj),
            "n_projects_all": len({r["project"] for r in raw}), "n_y1": int(sum(r["y"] for r in lab)), "base_rate": sum(r["y"] for r in lab) / len(lab),
            "dominant_project": top, "dominant_n": ntop, "dominant_share": ntop / len(lab), "splits": sorted({r.get("split") for r in raw}),
            "n_families_labelled": len(fam)}


# ---------------- part 2/3: OOF predictions (repo CV code) ----------------
def refit_oof(strict, seed=0, fit_B=500):
    calibrate.STRICT_BLOCKERS = bool(strict)
    with policy.use("v8.0"):
        recs = sorted([r for r in evaluate.load_records(REC) if r.y is not None], key=lambda r: (r.project, r.pair_id))
        y = np.array([r.y for r in recs], float); proj = np.array([r.project for r in recs])
        fold = stats.project_folds(proj, 5, seed); folds = sorted(set(fold))
        out = {"pair_id": [r.pair_id for r in recs], "project": proj.tolist(), "y": y.tolist(), "fold": fold.tolist(),
               "witness": [bool(calibrate.has_witness(r)) for r in recs], "rules": {}, "models": {}}
        for n in RULES:
            sc, nd, dv = evaluate._cv_rule(recs, n, None); out["rules"][n] = {"ndo": nd.tolist(), "div": dv.tolist()}
        ers = evaluate.default_ers_factory(); cache = {}
        for n in MODELS:
            names, with_ers = baselines.MODEL_SPECS[n]
            t0 = time.time()
            sc, el, nd, _ = evaluate._cv_model(recs, n, fold, folds, seed, fit_B, None, ers, cache, names, with_ers)
            out["models"][n] = {"score": sc.tolist(), "elig": el.tolist(), "rscore": evaluate.rank_scores(sc, el, fold).tolist(),
                                "ndo_alpha015": nd[0.15].tolist(), "fit_seconds": time.time() - t0}
    calibrate.STRICT_BLOCKERS = False
    return out


def oof_base_rate(y, fold, elig):
    """Honest base-rate predictor: training-fold prevalence among eligible pairs (same project folds)."""
    p = np.full(len(y), np.nan)
    for f in set(fold):
        tr = (fold != f) & elig; p[(fold == f) & elig] = y[tr].mean()
    return p


def analyse_policy(o, saved, B, seed):
    y = np.array(o["y"]); proj = np.array(o["project"]); fold = np.array(o["fold"]); N = len(y)
    W = cluster_weights(proj, B, seed)
    savedsys = {s["system"]: s for s in saved["systems"]}
    res = {"rules": {}, "models": {}, "checks": []}
    for n in RULES:
        nd = np.array(o["rules"][n]["ndo"], float); k = int(nd.sum()); fa = int((nd * y).sum())
        pr = [y[(proj == u) & (nd > 0)].mean() for u in np.unique(proj) if ((proj == u) & (nd > 0)).any()]
        res["rules"][n] = {"coverage": k / N, "n_ndo": k, "n_fa": fa, "risk": fa / k if k else None, "risk_ci95_cluster": risk_ci(y, nd, W),
                           "risk_ci95_wilson_iid": wilson(fa, k), "n_projects_with_ndo": len(pr), "risk_project_macro": float(np.mean(pr)) if pr else None,
                           "saved_risk": savedsys[n]["risk"], "saved_ci95_B2000": savedsys[n]["risk_ci95"]}
        res["checks"].append((f"rule {n} risk", abs((fa / k if k else 0) - (savedsys[n]["risk"] if savedsys[n]["risk"] == savedsys[n]["risk"] else 0)) < 1e-12))
    b3 = np.array(o["rules"]["b3_v7b_gate"]["ndo"], float); c7 = b3.sum() / N
    nonwit = ~np.array(o["witness"])
    res["v7b_gate_coverage"] = c7
    res["b6_random_abstention"] = {"risk_expectation": float(y[nonwit].mean()), "n_pool": int(nonwit.sum()), "note": "expected risk of random abstention among B1-issuable pairs = B1 risk at any coverage"}
    for n in MODELS:
        m = o["models"][n]; sc = np.array(m["score"]); el = np.array(m["elig"], bool); rs = np.array(m["rscore"])
        p = sc[el]; yy = y[el]; We = W[:, el]
        ci_, sl = stats.calibration_slope_intercept(p, yy)
        pb = oof_base_rate(y, fold, el)[el]
        mr = stats.matched_risk(rs, el, y, c7); reps = stats.matched_risk(rs, el, y, c7, W)
        r = {"n_eligible": int(el.sum()), "n_eligible_y1": int(yy.sum()), "n_projects_eligible": int(len(set(proj[el]))),
             "brier": stats.brier(p, yy), "brier_ci95": metric_ci(lambda a, b: stats.brier(b, a), yy, p, We),
             "logloss": stats.logloss(p, yy), "logloss_ci95": metric_ci(lambda a, b: stats.logloss(b, a), yy, p, We),
             "calib_slope": sl, "calib_intercept": ci_, "slope_intercept_ci95": stats.slope_cluster_ci(p, yy, proj[el], B=min(B, 2000), seed=seed),
             "brier_insample_base_rate": stats.brier(np.full(len(yy), yy.mean()), yy),
             "brier_oof_base_rate": stats.brier(pb, yy), "logloss_oof_base_rate": stats.logloss(pb, yy),
             "matched_cstar": c7, "matched_n_ndo": c7 * N, "matched_risk": mr, "matched_risk_ci95_cluster": pct(reps),
             "matched_valid_resample_share": float(np.isfinite(reps).mean()),
             "matched_risk_c02": stats.matched_risk(rs, el, y, 0.2), "matched_risk_c03": stats.matched_risk(rs, el, y, 0.3),
             "risk_coverage_curve": stats.risk_coverage_curve(rs, el, y),
             "reliability_q5": [dict(b, wilson95=wilson(round(b["obs_rate"] * b["n"]), b["n"])) for b in stats.reliability_bins(p, yy, 5, quantile=True)],
             "ece_range": [min(stats.ece_sensitivity(p, yy).values()), max(stats.ece_sensitivity(p, yy).values())],
             "nested_threshold_alpha015_n_ndo": int(np.array(m["ndo_alpha015"]).sum()), "fit_seconds": m["fit_seconds"]}
        s = savedsys.get(n)
        if s:
            r["saved"] = {k: s.get(k) for k in ("logloss", "brier", "calib_slope", "calib_intercept")}
            ok = all(abs(r[k] - s[k]) < 1e-9 for k in ("logloss", "brier"))
            res["checks"].append((f"model {n} logloss/brier reproduce saved", ok))
        res["models"][n] = r
    # paired contrasts at c*=gate coverage, own bootstrap; positive = CEC (b8) safer
    a = o["models"]["b8_full_cec"]; ra = stats.matched_risk(np.array(a["rscore"]), np.array(a["elig"], bool), y, c7, W)
    pa = stats.matched_risk(np.array(a["rscore"]), np.array(a["elig"], bool), y, c7)
    con = {}
    for n in ["b7_cov_calibration", "b9_cec_no_ers", "abl_mult_only"]:
        b = o["models"][n]; rb = stats.matched_risk(np.array(b["rscore"]), np.array(b["elig"], bool), y, c7, W)
        pbp = stats.matched_risk(np.array(b["rscore"]), np.array(b["elig"], bool), y, c7); d = rb - ra
        con[f"{n}_minus_b8"] = {"diff": pbp - pa, "ci95": pct(d), "valid_share": float(np.isfinite(d).mean()), "p_one_sided": stats.boot_p_one_sided(d)}
    rb3 = stats.matched_risk(np.zeros(N), b3 > 0, y, c7, W); d = rb3 - ra
    con["b3_minus_b8"] = {"diff": float(y[b3 > 0].mean() - pa), "ci95": pct(d), "valid_share": float(np.isfinite(d).mean()), "p_one_sided": stats.boot_p_one_sided(d)}
    # log-loss contrasts on the common eligible set
    for x, z in (("b7_cov_calibration", "b9_cec_no_ers"), ("b9_cec_no_ers", "b8_full_cec"), ("b7_cov_calibration", "b8_full_cec"), ("abl_mult_only", "b8_full_cec")):
        el = np.array(o["models"][x]["elig"], bool) & np.array(o["models"][z]["elig"], bool)
        lx = stats.logloss_each(np.array(o["models"][x]["score"])[el], y[el]); lz = stats.logloss_each(np.array(o["models"][z]["score"])[el], y[el])
        Wd = W[:, el]; reps = (Wd * (lx - lz)).sum(1) / Wd.sum(1)
        con[f"logloss_{x}_minus_{z}"] = {"diff": float((lx - lz).mean()), "ci95": pct(reps), "valid_share": 1.0, "p_one_sided": stats.boot_p_one_sided(reps)}
    ks = list(con); hp = holm([con[k]["p_one_sided"] for k in ks])
    for k, h in zip(ks, hp): con[k]["p_holm_family_of_%d" % len(ks)] = h
    res["contrasts_own_bootstrap"] = con
    res["power"] = power(y, b3 > 0, proj)
    return res


# ---------------- part 7: power ----------------
def power(y, ndo, proj):
    rep = stats.power_report(proj, y, ndo)
    n = int(ndo.sum()); p0 = float(y[ndo].mean()); deff = rep["design_effect"]; neff = n / deff
    za, zb = 1.959964, 0.841621
    two_sample = {}
    for nn in (n, 100, 200, 400, 800):
        ne = nn / deff
        d = next((d for d in np.arange(0.005, 0.6, 0.0025) if p0 - d > 0 and
                  (za * math.sqrt(2 * p0 * (1 - p0)) + zb * math.sqrt(p0 * (1 - p0) + (p0 - d) * (1 - p0 + d))) / d <= math.sqrt(ne)), None)
        two_sample[str(nn)] = d
    paired = {}
    for q in (0.05, 0.10, 0.15, 0.25):
        paired[str(q)] = next((float(d) for d in np.arange(0.005, 0.5, 0.0025) if d * d < q and ((za * math.sqrt(q) + zb * math.sqrt(q - d * d)) / d) ** 2 * deff <= n), None)
    need5 = {}
    for q in (0.10, 0.15, 0.25):
        d = 0.05; need5[str(q)] = math.ceil(((za * math.sqrt(q) + zb * math.sqrt(q - d * d)) / d) ** 2 * deff)
    return {"repo_power_report": rep, "n_ndo": n, "risk": p0, "deff": deff, "n_eff": neff,
            "ci_halfwidth_cluster_normal": 1.959964 * math.sqrt(p0 * (1 - p0) / neff),
            "mde_two_independent_systems_reduction_from_p0": two_sample,
            "mde_paired_mcnemar_by_discordant_share": paired, "n_ndo_needed_for_5pp_paired_by_discordant_share": need5,
            "assumptions": "two-sided alpha 0.05, power 0.80, normal approximations, variance inflated by the observed design effect of the V7-B NDO set"}


# ---------------- part 4: multi-seed saved results ----------------
def seeds_table(run):
    rows = []
    for f in sorted(glob.glob(os.path.join(run, "seed*/results.json"))):
        d = jload(f); s = {x["system"]: x for x in d["systems"]}; p = d["primary"]; sec = d["secondary"]
        rows.append({"seed": d["seed"], "B": d["bootstrap_B"], "runtime_s": d["runtime_seconds"], "fold_sizes": d["fold_sizes"],
                     "vs_b7": {k: p["vs_b7@v7b_gate"][k] for k in ("risk_a", "risk_b", "diff_b_minus_a", "ci95_pct", "p_one_sided", "n_valid_boot")},
                     "vs_b3": {k: p["vs_b3@v7b_gate"][k] for k in ("risk_a", "risk_b", "diff_b_minus_a", "ci95_pct", "p_one_sided", "n_valid_boot")},
                     "vs_b6": {k: p["vs_b6@v7b_gate"][k] for k in ("risk_a", "risk_b", "diff_b_minus_a", "ci95_pct", "p_one_sided", "n_valid_boot")},
                     "holm": p["holm_family"]["p_holm"],
                     "ers_logloss_b9_minus_b8": sec["logloss_b9_cec_no_ers_minus_b8_full_cec"],
                     "ers_matched_b9_minus_b8_gate": {k: sec["matched_risk_b9_cec_no_ers_minus_b8_full_cec@v7b_gate"][k] for k in ("diff_b_minus_a", "ci95_pct", "p_one_sided", "n_valid_boot")},
                     "h1a_logloss_b7_minus_b9": sec["logloss_b7_cov_calibration_minus_b9_cec_no_ers"],
                     "ers_verdict": d["ers_added_value"],
                     "models": {n: {k: s[n][k] for k in ("logloss", "brier", "calib_slope", "calib_intercept", "n_eligible_scored")} for n in ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec", "abl_mult_only")}})
    agg = {}
    for key in ("logloss", "brier", "calib_slope"):
        for n in ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec", "abl_mult_only"):
            v = [r["models"][n][key] for r in rows]; agg[f"{n}.{key}"] = {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)), "min": min(v), "max": max(v)}
    for c in ("vs_b7", "vs_b3", "vs_b6"):
        v = [r[c]["diff_b_minus_a"] for r in rows]; pv = [r[c]["p_one_sided"] for r in rows]
        agg[f"{c}.diff"] = {"mean": float(np.mean(v)), "min": min(v), "max": max(v)}; agg[f"{c}.p_raw"] = {"min": min(pv), "max": max(pv)}
    v = [r["ers_logloss_b9_minus_b8"]["point"] for r in rows]
    agg["ers_logloss_gain"] = {"mean": float(np.mean(v)), "min": min(v), "max": max(v), "n_ci_excludes_0": sum(r["ers_logloss_b9_minus_b8"]["ci95"][0] > 0 for r in rows)}
    return {"run": os.path.relpath(run, ROOT), "run_meta": jload(os.path.join(run, "run_meta.json")), "per_seed": rows, "aggregate": agg}


def report_claims_check(soft, strict):
    """Numbers stated in reports/v8/linux/*.md vs raw results.json."""
    claimed_p_b7 = [0.4195, 0.4310, 0.3980, 0.4450, 0.4120]; claimed_p_b3 = [0.3420, 0.3550, 0.3210, 0.3600, 0.3390]
    raw_b7 = [r["vs_b7"]["p_one_sided"] for r in soft["per_seed"]]; raw_b3 = [r["vs_b3"]["p_one_sided"] for r in soft["per_seed"]]
    s0 = strict["per_seed"][0]
    return {"STATISTICAL_ANALYSIS_REPORT.per_seed_p_vs_b7": {"claimed": claimed_p_b7, "raw": raw_b7},
            "STATISTICAL_ANALYSIS_REPORT.per_seed_p_vs_b3": {"claimed": claimed_p_b3, "raw": raw_b3},
            "STATISTICAL_ANALYSIS_REPORT.strict_coverage": {"claimed": "18.22% (47 pairs), R 0.2128 (10 FA)", "raw": "V7-B gate coverage 0.2364 (61 pairs), all model systems R 0.2131 (13 FA) at c*; eligible pool 61"},
            "STATISTICAL_ANALYSIS_REPORT.calibration_slope": {"claimed": "soft 0.942 [0.72,1.18]; strict 0.915 [0.68,1.22]",
                                                              "raw": {"soft_b8_seeds": [r["models"]["b8_full_cec"]["calib_slope"] for r in soft["per_seed"]],
                                                                      "strict_b8_seeds": [r["models"]["b8_full_cec"]["calib_slope"] for r in strict["per_seed"]]}},
            "STATISTICAL_ANALYSIS_REPORT.ers_all_seeds_no_gain": {"claimed": "no ERS gain all seeds (soft only reported)", "raw_strict_verdicts": [r["ers_verdict"] for r in strict["per_seed"]]},
            "MATCHED_COVERAGE_REPORT.sign": "column labelled Risk_b8 - Risk_base but values are base - b8 for b7/b3 rows and b8 - base for the b6 row; CIs are of (base - b8) throughout",
            "strict_seed0_vs_b7": s0["vs_b7"]}


def mac_compare():
    out = {"label": "mac-hardening branch (SBG-V6 checkout); post-fix = commit b9b8a86c results/v8_mac_reanalysis_20261118_222059_profilefix2 (committed); NOT on linux branch"}
    for pol in ("v8.0", "v8.1"):
        rows = []
        for sd in (0, 1, 2):
            pre = jload(os.path.join(MAC_PRE, pol, f"seed{sd}", "results.json")); post = jload(os.path.join(MAC_POST, pol, f"seed{sd}", "results.json"))
            sp = {x["system"]: x for x in pre["systems"]}; so = {x["system"]: x for x in post["systems"]}
            rows.append({"seed": sd, "pre_B": pre["bootstrap_B"], "post_B": post["bootstrap_B"],
                         "b8_logloss": [sp["b8_full_cec"]["logloss"], so["b8_full_cec"]["logloss"]],
                         "b9_logloss": [sp["b9_cec_no_ers"]["logloss"], so["b9_cec_no_ers"]["logloss"]],
                         "b8_brier": [sp["b8_full_cec"]["brier"], so["b8_full_cec"]["brier"]],
                         "b8_slope": [sp["b8_full_cec"]["calib_slope"], so["b8_full_cec"]["calib_slope"]],
                         "ers_gain": [pre["secondary"]["logloss_b9_cec_no_ers_minus_b8_full_cec"], post["secondary"]["logloss_b9_cec_no_ers_minus_b8_full_cec"]],
                         "vs_b7_gate_diff": [pre["primary"]["vs_b7@v7b_gate"]["diff_b_minus_a"], post["primary"]["vs_b7@v7b_gate"]["diff_b_minus_a"]],
                         "ers_verdict": [pre["ers_added_value"], post["ers_added_value"]]})
        out[pol] = rows
    # does linux soft == mac pre-fix v8.0 and linux strict == mac pre-fix v8.1 (point values)?
    eq = {}
    for lin, pol in ((SOFT, "v8.0"), (STRICT, "v8.1")):
        for sd in (0, 1, 2):
            a = {x["system"]: x for x in jload(os.path.join(lin, f"seed{sd}", "results.json"))["systems"]}
            b = {x["system"]: x for x in jload(os.path.join(MAC_PRE, pol, f"seed{sd}", "results.json"))["systems"]}
            eq[f"{os.path.basename(lin)}_seed{sd}_vs_mac_pre_{pol}"] = all(abs(a[n]["logloss"] - b[n]["logloss"]) < 1e-9 for n in ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec", "abl_mult_only"))
    out["linux_equals_mac_prefix_point_values"] = eq
    return out


def five_dataset():
    R = [json.loads(l) for l in open(os.path.join(IV, "execution_results.jsonl"))]
    M = {p["pair_id"]: p for p in jload(os.path.join(IV, "pair_manifest.json"))}
    import csv
    adj = list(csv.DictReader(open(os.path.join(IV, "blinded_adjudication_template.csv"))))
    cons = collections.Counter()
    for r in R:
        trig = any(t.get("purpose") == "trigger_discriminating" for t in M[r["pair_id"]]["test_suite"])
        cons[f"trigger_inputs={trig}|verdict={r['verdict']}"] += 1
    return {"n_pairs": len(R), "n_projects": len({r["project"] for r in R}), "by_dataset": dict(collections.Counter(r["dataset"] for r in R)),
            "verdicts": dict(collections.Counter(r["verdict"] for r in R)), "n_adjudication_rows": len(adj),
            "n_adjudicated": sum(bool(a["adjudicator_verdict"].strip()) for a in adj),
            "generator_consistency": dict(cons),
            "note": "pairs are generated by sbgv8/independent_validation/datasets.py (templated base_src/variant_src with built-in trigger_discriminating inputs); "
                    "no adjudicated labels exist, so false-assurance risk is not estimable; benchmark change_type is a design category, not ground truth"}


PROVENANCE = {
    "dev_records": {"verdict": "PASSES", "evidence": "experiments/v8/dev_collect.py runs each pair as a subprocess `python -m sbgv8 compare base variant` "
                    "(V7-B engine) and builds records via adapter.load_record; all 312 records carry run_meta rc=0 with wall time and a verified log head; "
                    "all 1976 inputs have provenance 'declared'; outcomes SAME 1863 / CONFIRMED_DIFF 84 / LIMIT_ASYMMETRIC 22 / NO_RUN 6 / QUARANTINED 1.",
                    "labels": "scripts/build_dev_pairs_csv.py: quixbugs Y=1 iff the benchmark's declared tests distinguish buggy from fixed (B2 oracle); synthetic Y from "
                              "generator mutation label (CHANGED vs semantics-preserving); quixbugs_neg Y=0 by construction; bugsinpy_units unlabelled. Not derived from SBG verdicts.",
                    "leakage": "profile.py / ers.py / perturb.py / policy.py never read rec.y or rec.meta (docstrings + grep); calibrate reads y only for training/threshold fitting on training folds.",
                    "caveats": "(i) quixbugs arm: label oracle and SBG evidence use the same declared inputs (shared-input coupling; a Y=1 quixbugs pair is almost always a witness/DIV, so it rarely reaches NDO); "
                               "(ii) labels are generator/benchmark labels, not adjudicated; (iii) raw run directories (results/repro/v8_dev_20261118_195446) are not present in this worktree, so logs were not re-verified here."},
    "linux_dev_eval": {"verdict": "PASSES (inherits dev_records)", "evidence": "results/v8_dev_eval_20261119_* are evaluate.run over datasets/v8/dev_records.jsonl (same md5 as mac); no new execution; "
                       "seed-0 OOF predictions re-generated here reproduce saved log loss/Brier exactly."},
    "linux_perturbation_ers": {"verdict": "POST-HOC ONLY", "evidence": "results/v8/linux/perturb/posthoc_matrix.* and ers/ers_matrix.json are recorded-evidence transformations (P2/P5/P6 marked 'synthetic recorded input'); "
                               "no Linux real-execution perturbation raw files exist under results/v8/linux, so real-execution claims in the Linux reports are report-only."},
    "five_dataset": {"verdict": "INVALID AS EVIDENCE", "evidence": "sbgv8/independent_validation/executor.py assigns CONFIRMED_DIFF/SAME from change_type and test purpose (no program execution); "
                     "pairs are templates from datasets.py; verdict == construction for 250/250. Excluded from all tables and figures."},
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--refit", action="store_true"); ap.add_argument("--B", type=int, default=10000); ap.add_argument("--seed", type=int, default=20261119)
    a = ap.parse_args()
    os.makedirs(AUDIT, exist_ok=True)
    cache = os.path.join(AUDIT, "oof_seed0.json")
    if a.refit or not os.path.exists(cache):
        t0 = time.time(); oof = {"soft_v8.0": refit_oof(False), "strict_v8.0s": refit_oof(True), "seconds": None}
        oof["seconds"] = time.time() - t0
        oof["note"] = "seed-0 out-of-fold predictions regenerated with linux-branch repo code (unfixed profile.py); DEVELOPMENT DATA"
        json.dump(nan2none(oof), open(cache, "w"))
    oof = jload(cache)
    for pol in ("soft_v8.0", "strict_v8.0s"):
        for m in oof[pol]["models"].values(): m["score"] = [np.nan if v is None else v for v in m["score"]]; m["rscore"] = [np.inf if v is None else v for v in m["rscore"]]
    soft_s, strict_s = seeds_table(SOFT), seeds_table(STRICT)
    out = {"banner": "DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
           "bootstrap": {"B": a.B, "seed": a.seed, "unit": "project", "note": "own numpy multinomial project-cluster bootstrap, independent RNG stream from the repo runs"},
           "denominators": denominators(),
           "seed0_recomputed": {"soft_v8.0": analyse_policy(oof["soft_v8.0"], jload(os.path.join(SOFT, "seed0/results.json")), a.B, a.seed),
                                "strict_v8.0s": analyse_policy(oof["strict_v8.0s"], jload(os.path.join(STRICT, "seed0/results.json")), a.B, a.seed)},
           "oof_regeneration_seconds": oof.get("seconds"),
           "linux_multiseed_saved": {"soft": soft_s, "strict": strict_s},
           "linux_report_claims_vs_raw": report_claims_check(soft_s, strict_s),
           "mac_branch_comparison": mac_compare(),
           "five_dataset": five_dataset(),
           "provenance_audit": PROVENANCE}
    json.dump(nan2none(out), open(os.path.join(AUDIT, "stats_summary.json"), "w"), indent=1)
    bad = [c for p in out["seed0_recomputed"].values() for c in p["checks"] if not c[1]]
    print("checks failed:", bad if bad else "none")
    assert not bad, "recomputation does not reproduce saved results"


if __name__ == "__main__":
    main()

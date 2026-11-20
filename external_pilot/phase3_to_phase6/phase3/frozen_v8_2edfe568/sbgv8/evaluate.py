"""Evaluation driver: nested project-grouped CV of all baselines/ablations, primary matched-coverage comparison, tables, plots.
run(records, out_dir, seed) -> results dict (also results.json, tables/*.csv|md, plots/*.png).
Leakage rules: outer folds are by project; lambda and tau are chosen only on INNER project folds of the outer-train set; the outer test fold
is touched only by predict_risk/decide (no y). Pooled out-of-fold predictions are then scored. Evaluation is on y-known pairs; y=None
pairs are counted and reported, never dropped silently. Unresolved handling beyond that (worst-case sensitivity) is reported in the plan."""
from __future__ import annotations
import csv, json, math, os, time
import numpy as np
from . import baselines, calibrate, policy, schema, stats
from .schema import EvidenceRecord

BANNER = "DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION"
INDEPENDENT_SPLITS = ("evaluation", "holdout")
ALPHAS = stats.ALPHA_GRID
GROUPS = {"coverage": ["act_frac", "branch_cov_min"], "multiplicity": ["mu_min", "mu_mean", "n_same"], "repetition": ["n_rep", "repro_frac"],
          "influence_proxy": ["obs_react"], "diversity": ["n_eff", "n_eff_prov"], "observation": ["lossy_frac", "chan_complete"],
          "trust": ["prov_ok", "integrity_ok", "env_ok"]}
MODEL_SYSTEMS = ["b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec", "abl_mult_only", "abl_cov_rep", "abl_cov_mult", "abl_cov_infl", "abl_cov_prov"]


def load_records(path):
    with open(path) as f:
        return [EvidenceRecord.from_json(l) for l in f if l.strip()]


def default_ers_factory(pids=None):
    """model -> (extra_features_fn, extra_names) using sbgv8.ers (None if ers/perturb unavailable)."""
    try:
        from . import ers
    except Exception:
        return None
    use = tuple(pids or schema.PERTURBATIONS)
    def factory(model, seed=0):
        cache = {}
        def fn(rec):
            k = rec.pair_id + rec.digest()[:12]
            if k not in cache: cache[k] = ers.ers_vector(rec, model, pids=use, seed=seed)
            return cache[k]
        return fn, [f"ers_{p}_delta" for p in use]
    return factory


def _arr(recs, idx): return [recs[i] for i in idx]


def _cv_model(recs, name, fold, folds, seed, B, profile_fn, ers_factory, cache, names=None, with_ers=False):
    """Pooled outer-fold predictions for one model system."""
    N = len(recs); score = np.full(N, np.nan); elig = np.zeros(N, bool); ndo = {a: np.zeros(N, bool) for a in ALPHAS}; coefs = []
    for f in folds:
        tr = [i for i in range(N) if fold[i] != f]; te = [i for i in range(N) if fold[i] == f]
        trr = _arr(recs, tr)
        kw = dict(profile_fn=profile_fn, alphas=ALPHAS, seed=seed, B=B)
        if with_ers:
            m9 = cache.get(("b9_cec_no_ers", f))
            if m9 is None or ers_factory is None: raise RuntimeError("ERS unavailable")
            fn, en = ers_factory(m9, seed=seed)
            kw.update(extra_features_fn=fn, extra_names=en)
        m = calibrate.fit_select(trr, names, **kw)
        cache[(name, f)] = m
        for i in te:
            r = recs[i]; score[i] = m.predict_risk(r); elig[i] = calibrate.is_eligible(r)
            for a in ALPHAS: ndo[a][i] = elig[i] and not calibrate.is_div(r) and score[i] <= m.taus[a]
        coefs.append(m.coef_report())
    return score, elig, ndo, coefs


def rank_scores(score, elig, fold):
    """Within-fold average-rank of the risk among eligible pairs, scaled to (0,1]. Pooled outer-fold models have different intercepts, so raw
    risks are not comparable ACROSS folds (with strong shrinkage the pooled order would just be fold identity); ranking within each fold and
    pooling removes that artefact while keeping ties (equal rounded risks) tied. Used for matched-coverage/risk-coverage only."""
    from scipy.stats import rankdata
    out = np.full(len(score), np.inf)
    for f in sorted(set(fold)):
        m = (fold == f) & elig
        if m.any(): out[m] = rankdata(np.round(score[m], 10), method="average") / m.sum()
    return out


def _cv_rule(recs, name, profile_fn):
    pr = baselines.make(name, None, profile_fn=profile_fn)
    v = [pr.decide(r)[0] for r in recs]
    ndo = np.array([x == schema.VERDICTS[2] for x in v])
    return np.where(ndo, 0.0, 1.0), ndo, np.array([x == schema.VERDICTS[0] for x in v])


def _sys_summary(name, y, proj, ndo, B, seed):
    W = stats.cluster_counts(proj, B, seed)
    cov = stats.coverage(ndo); n = int(ndo.sum())
    num = (W * ndo * y).sum(1); den = (W * ndo).sum(1)
    reps = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
    pr = [y[(proj == u) & ndo].mean() for u in sorted(set(proj)) if ((proj == u) & ndo).any()]
    return {"system": name, "risk_project_macro": float(np.mean(pr)) if pr else None, "n_projects_with_ndo": len(pr), "coverage": cov, "n_issued_ndo": n, "n_false_assurance": int((ndo * y).sum()),
            "risk": stats.selective_risk(y, ndo), "risk_ci95": list(stats.pct_ci(reps)),
            "coverage_ci95": list(stats.pct_ci((W * ndo).sum(1) / W.sum(1)))}


def run(*a, policy_name=None, **kw):
    """Evaluation under a named eligibility policy (sbgv8.policy; None = whatever is active, default v8.0); restored afterwards."""
    with policy.use(policy_name or policy.current()):
        return _run(*a, **kw)


def _run(records, out_dir, seed=0, B=stats.B_DEFAULT, outer_k=5, profile_fn=None, ers_factory="default", fit_B=500, plots=True, extra_banner=None, strict_blockers=False):
    calibrate.STRICT_BLOCKERS = bool(strict_blockers)
    t0 = time.time(); os.makedirs(os.path.join(out_dir, "tables"), exist_ok=True)
    allrecs = list(records)
    labelled = [r for r in allrecs if r.y is not None]
    recs = sorted(labelled, key=lambda r: (r.project, r.pair_id))
    y = np.array([r.y for r in recs], float); proj = np.array([r.project for r in recs])
    dev = any(r.split not in INDEPENDENT_SPLITS for r in allrecs)
    banner = BANNER if dev else "evaluation/holdout split records only"
    if ers_factory == "default": ers_factory = default_ers_factory()
    res = {"banner": banner, "policy": policy.current(), "seed": seed, "strict_blockers": bool(strict_blockers), "soft_blockers": sorted(calibrate.SOFT_BLOCKERS), "bootstrap_B": B, "outer_k": outer_k, "n_records": len(allrecs), "n_labelled": len(recs),
           "n_unresolved_y_none": len(allrecs) - len(recs), "n_projects": len(set(proj)), "base_rate_y": float(y.mean()) if len(y) else None,
           "splits_present": sorted({r.split for r in allrecs}), "schema": schema.SCHEMA_VERSION, "note": extra_banner}
    if len(recs) < 10 or len(set(proj)) < 3:
        res["error"] = "too few labelled pairs/projects"; _write(out_dir, res); return res
    fold = stats.project_folds(proj, outer_k, seed); folds = sorted(set(fold))
    for f in folds: assert not (set(proj[fold == f]) & set(proj[fold != f]))   # leakage guard
    res["fold_sizes"] = [int((fold == f).sum()) for f in folds]

    S = {}   # name -> dict(score, elig, ndo{alpha}, kind)
    for n in baselines.RULE_NAMES:
        sc, nd, dv = _cv_rule(recs, n, profile_fn); S[n] = {"score": sc, "rscore": sc, "elig": nd, "ndo": {a: nd for a in ALPHAS}, "kind": "rule", "div": dv}
    cache = {}; coefs = {}; unavailable = {}
    for n in MODEL_SYSTEMS:
        names, with_ers = baselines.MODEL_SPECS[n]
        try:
            sc, el, nd, cf = _cv_model(recs, n, fold, folds, seed, fit_B, profile_fn, ers_factory, cache, names, with_ers)
        except RuntimeError as e:
            unavailable[n] = str(e); continue
        S[n] = {"score": sc, "rscore": rank_scores(sc, el, fold), "elig": el, "ndo": nd, "kind": "model"}; coefs[n] = cf
    res["unavailable_systems"] = unavailable

    # ---- per-system summaries ----
    rows = []
    for n, s in S.items():
        nd = s["ndo"][0.15] if s["kind"] == "model" else s["ndo"][0.15]
        row = _sys_summary(n, y, proj, nd, B, seed)
        if s["kind"] == "model":
            m = s["elig"]; p = s["score"][m]; yy = y[m]
            ci, sl = stats.calibration_slope_intercept(p, yy)
            row.update(alpha=0.15, brier=stats.brier(p, yy), logloss=stats.logloss(p, yy), calib_intercept=ci, calib_slope=sl,
                       ece_sensitivity=stats.ece_sensitivity(p, yy), n_eligible_scored=int(m.sum()),
                       brier_base_rate=stats.brier(np.full(len(yy), yy.mean()), yy), reliability=stats.reliability_bins(p, yy, 10),
                       risk_coverage=stats.risk_coverage_curve(s["rscore"], s["elig"], y)[::max(1, len(recs) // 60)])
            row["coverage_at_risk_oracle"] = {str(a): stats.coverage_at_risk(stats.risk_coverage_curve(s["rscore"], s["elig"], y), a) for a in ALPHAS}
            row["nested_threshold"] = {str(a): _sys_summary(n, y, proj, s["ndo"][a], B, seed) for a in ALPHAS}
        rows.append(row)
    res["systems"] = rows
    # sensitivity: y=None pairs counted as false assurance when a RULE system issues NDO on them (worst case)
    unl = [r for r in allrecs if r.y is None]
    res["unresolved_worst_case"] = {n: {"n_unresolved_issued_ndo": sum(baselines.make(n, None, profile_fn=profile_fn).decide(r)[0] == schema.VERDICTS[2] for r in unl),
                                        "risk_if_all_counted_false_assurance": None} for n in baselines.RULE_NAMES}
    for n, d in res["unresolved_worst_case"].items():
        nd = S[n]["ndo"][0.15]; k = int(nd.sum()); den = k + d["n_unresolved_issued_ndo"]
        d["risk_if_all_counted_false_assurance"] = (float((y * nd).sum() + d["n_unresolved_issued_ndo"]) / den) if den else None
    cnt = {u: int((proj == u).sum()) for u in sorted(set(proj))}; top = max(cnt, key=cnt.get)
    res["dominant_project"] = {"project": top, "n_pairs": cnt[top], "share": cnt[top] / len(y)}
    res["abstention_rate"] = {r["system"]: 1 - r["coverage"] for r in rows}
    res["detection_recall_div_on_y1"] = {n: float((S[n]["div"] & (y == 1)).sum() / max((y == 1).sum(), 1)) for n in baselines.RULE_NAMES}

    # ---- matched coverage ----
    v7 = S["b3_v7b_gate"]; c7 = stats.coverage(v7["ndo"][0.15]); res["v7b_gate_coverage"] = c7
    grid = [("v7b_gate", c7)] + [(f"c={c}", c) for c in stats.CSTAR_GRID]
    mc = []
    for n, s in S.items():
        for lab, c in grid:
            if s["kind"] == "model":
                W = stats.cluster_counts(proj, B, seed); reps = stats.matched_risk(s["rscore"], s["elig"], y, c, W)
                mc.append({"system": n, "cstar": lab, "coverage": c, "risk": stats.matched_risk(s["rscore"], s["elig"], y, c), "ci95": list(stats.pct_ci(reps))})
            elif lab == "v7b_gate" and n == "b3_v7b_gate" or (s["kind"] == "rule" and abs(stats.coverage(s["ndo"][0.15]) - c) < 1e-12):
                mc.append({"system": n, "cstar": lab, "coverage": c, "risk": stats.selective_risk(y, s["ndo"][0.15]), "ci95": None})
    b1 = S["b1_plain_dt"]["ndo"][0.15]
    for lab, c in grid:   # baseline 6: random abstention, 1,000 seeded draws; ci omitted (expectation equals the B1-issuable base rate)
        mc.append({"system": "b6_matched_abstention", "cstar": lab, "coverage": c, "risk": baselines.matched_abstention_risk(recs, c, 1000, seed), "ci95": None})
    res["matched_coverage"] = mc
    res["b1_risk_all_nonwitness"] = stats.selective_risk(y, b1)

    # ---- primary comparison: CEC vs coverage-only calibration, at the V7-B gate coverage ----
    cec = "b8_full_cec" if "b8_full_cec" in S else "b9_cec_no_ers"
    res["primary_system"] = cec; res["primary_is_full_cec_with_ers"] = cec == "b8_full_cec"
    prim = {}; pv = []
    nonwit = np.array([not calibrate.has_witness(r) for r in recs])
    for lab, c in grid:
        d = stats.paired_matched(S[cec]["rscore"], S[cec]["elig"], S["b7_cov_calibration"]["rscore"], S["b7_cov_calibration"]["elig"], y, proj, c, B, seed)
        prim[f"vs_b7@{lab}"] = d
        if lab == "v7b_gate":
            pv.append(d["p_one_sided"])
            d3 = stats.paired_matched(S[cec]["rscore"], S[cec]["elig"], np.zeros(len(y)), v7["ndo"][0.15], y, proj, c, B, seed)
            d6 = stats.paired_matched(S[cec]["rscore"], S[cec]["elig"], np.zeros(len(y)), nonwit, y, proj, c, B, seed)
            prim["vs_b3@v7b_gate"] = d3; prim["vs_b6@v7b_gate"] = d6; pv += [d3["p_one_sided"], d6["p_one_sided"]]
    hp = stats.holm(pv)
    prim["holm_family"] = {"tests": ["vs_b7", "vs_b3", "vs_b6"], "p_raw": pv, "p_holm": hp.tolist(), "practical_threshold_pp": 5.0}
    for k in ("vs_b7@v7b_gate", "vs_b3@v7b_gate", "vs_b6@v7b_gate"):
        d = prim[k]; d["meets_H2"] = bool(d["diff_b_minus_a"] == d["diff_b_minus_a"] and d["diff_b_minus_a"] >= 0.05 and d["lower97.5_one_sided"] > 0)
    # secondary: H1a (logloss), H3 (b8 vs b9)
    sec = {}
    em = S["b7_cov_calibration"]["elig"] & S["b9_cec_no_ers"]["elig"]
    for a_, b_ in (("b9_cec_no_ers", "b7_cov_calibration"), ("b8_full_cec", "b9_cec_no_ers")):
        if a_ in S and b_ in S:
            la = stats.logloss_each(np.clip(S[a_]["score"][em], 1e-6, 1 - 1e-6), y[em]); lb = stats.logloss_each(np.clip(S[b_]["score"][em], 1e-6, 1 - 1e-6), y[em])
            W = stats.cluster_counts(proj[em], B, seed); d = (W * (lb - la)).sum(1) / W.sum(1)   # positive = a better
            sec[f"logloss_{b_}_minus_{a_}"] = {"point": float((lb - la).mean()), "ci95": list(stats.pct_ci(d)), "p_one_sided": stats.boot_p_one_sided(d)}
            for lab, c in grid:
                sec[f"matched_risk_{b_}_minus_{a_}@{lab}"] = stats.paired_matched(S[a_]["rscore"], S[a_]["elig"], S[b_]["rscore"], S[b_]["elig"], y, proj, c, B, seed, jackknife=False)
    res["primary"] = prim; res["secondary"] = sec
    res["ers_added_value"] = _ers_verdict(res, S)

    # ---- redundancy & leave-one-group-out ----
    pf = profile_fn or calibrate.default_profile
    X = np.array([[pf(r)[n] for n in schema.FEATURES] for r in recs])[S["b9_cec_no_ers"]["elig"]]
    res["redundancy"] = stats.redundancy_table(X, schema.FEATURES)
    logo = []
    full = schema.FEATURE_SETS["full_profile"]
    for g, fs in GROUPS.items():
        names = [n for n in full if n not in fs]
        sc, el, nd, _ = _cv_model(recs, "logo_" + g, fold, folds, seed, fit_B, profile_fn, ers_factory, cache, names, False)
        m = el; rs = rank_scores(sc, el, fold)
        logo.append({"left_out": g, "logloss": stats.logloss(sc[m], y[m]), "matched_risk@v7b_gate": stats.matched_risk(rs, el, y, c7),
                     "matched_risk@c=0.3": stats.matched_risk(rs, el, y, 0.3)})
    res["leave_one_group_out"] = logo
    # power
    pw = {}
    for n in ("b3_v7b_gate", cec):
        o, st = stats._groups(S[n]["rscore"], S[n]["elig"], y)
        k = int(round(c7 * len(y))); mask = np.zeros(len(y), bool); mask[o[:k]] = True
        pw[n] = stats.power_report(proj, y, mask if S[n]["kind"] == "model" else S[n]["ndo"][0.15])
    res["power"] = pw
    res["model_coefficients_fold0"] = {n: c[0] for n, c in coefs.items()}
    res["runtime_seconds"] = time.time() - t0
    _write(out_dir, res)
    if plots: _plots(out_dir, res, S, y)
    return res


def _ers_verdict(res, S):
    if "b8_full_cec" not in S:
        return "ERS unavailable in this run; H3 not assessed"
    k = [v for key, v in res["secondary"].items() if key.startswith("matched_risk_b9_cec_no_ers_minus_b8_full_cec@v7b")]
    ll = res["secondary"].get("logloss_b9_cec_no_ers_minus_b8_full_cec")
    if not k or ll is None: return "not assessed"
    d = k[0]
    gain = (ll["ci95"][0] > 0) or (d["diff_b_minus_a"] == d["diff_b_minus_a"] and d["lower97.5_one_sided"] > 0 and d["diff_b_minus_a"] > 0)
    return ("ERS shows a project-cluster-resolvable gain over CEC-without-ERS on this data (exploratory)" if gain else
            "NO demonstrated ERS gain: CIs for the log-loss and matched-risk differences (b9 minus b8) include 0 or favour b9")


def _fmt(v):
    return "" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))


def _table(path, rows, cols):
    with open(path + ".csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols); [w.writerow([_fmt(r.get(c)) if not isinstance(r.get(c), list) else json.dumps(r.get(c)) for c in cols]) for r in rows]
    with open(path + ".md", "w") as f:
        f.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows: f.write("| " + " | ".join(_fmt(r.get(c)) if not isinstance(r.get(c), list) else "[" + ", ".join(_fmt(x) for x in r[c]) + "]" for c in cols) + " |\n")


def _write(out_dir, res):
    os.makedirs(os.path.join(out_dir, "tables"), exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f: json.dump(res, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    t = os.path.join(out_dir, "tables")
    if "systems" in res:
        _table(os.path.join(t, "systems"), res["systems"], ["system", "coverage", "n_issued_ndo", "n_false_assurance", "risk", "risk_ci95", "brier", "logloss", "calib_intercept", "calib_slope"])
        _table(os.path.join(t, "matched_coverage"), res["matched_coverage"], ["system", "cstar", "coverage", "risk", "ci95"])
        _table(os.path.join(t, "primary"), [dict(test=k, **{c: v.get(c) for c in ("cstar", "risk_a", "risk_b", "diff_b_minus_a", "ci95_pct", "ci95_bca", "lower97.5_one_sided", "p_one_sided")})
                                           for k, v in res["primary"].items() if isinstance(v, dict) and "diff_b_minus_a" in v],
               ["test", "cstar", "risk_a", "risk_b", "diff_b_minus_a", "ci95_pct", "ci95_bca", "lower97.5_one_sided", "p_one_sided"])
        _table(os.path.join(t, "leave_one_group_out"), res["leave_one_group_out"], ["left_out", "logloss", "matched_risk@v7b_gate", "matched_risk@c=0.3"])
    with open(os.path.join(out_dir, "BANNER.txt"), "w") as f: f.write(res["banner"] + "\n")


def _plots(out_dir, res, S, y):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception:
        return
    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 4))
    for n, s in S.items():
        if s["kind"] != "model" or n not in ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec"): continue
        c = stats.risk_coverage_curve(s["rscore"], s["elig"], y)
        ax.plot([a for a, _, _ in c], [b for _, b, _ in c], label=n)
    for n in baselines.RULE_NAMES:
        r = [x for x in res["systems"] if x["system"] == n][0]; ax.scatter([r["coverage"]], [r["risk"]], marker="x", label=n)
    ax.set_xlabel("NDO coverage"); ax.set_ylabel("selective false-assurance risk"); ax.set_title(res["banner"], fontsize=6); ax.legend(fontsize=5)
    fig.savefig(os.path.join(out_dir, "plots", "risk_coverage.png"), dpi=130, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(4, 4)); ax.plot([0, 1], [0, 1], "k:")
    for r in res["systems"]:
        if "reliability" in r and r["system"] in ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec"):
            ax.plot([b["mean_pred"] for b in r["reliability"]], [b["obs_rate"] for b in r["reliability"]], "o-", label=r["system"])
    ax.set_xlabel("predicted risk"); ax.set_ylabel("observed rate"); ax.set_title(res["banner"], fontsize=6); ax.legend(fontsize=6)
    fig.savefig(os.path.join(out_dir, "plots", "reliability.png"), dpi=130, bbox_inches="tight"); plt.close(fig)


# ======================= FROZEN-THRESHOLD evaluation (deployable policy) + ERS placebo (mac hardening) =======================
FROZEN_ALPHAS = (0.10, 0.15, 0.20)
FROZEN_RULES = [("ub", a) for a in FROZEN_ALPHAS] + [("pt", a) for a in FROZEN_ALPHAS] + [("cov",)]
FROZEN_SYSTEMS = ("b7_cov_calibration", "b9_cec_no_ers", "b8_full_cec")


class Frozen:
    """A model plus thresholds learnt on calibration (training) PROJECTS only. Immutable after freeze()."""
    def __init__(self, name, model, taus, target_cov): self.name, self.model, self.taus, self.target_cov = name, model, taus, target_cov


def _fit_system(train, name, seed, fit_B, alphas, profile_fn, ers_factory):
    names, with_ers = baselines.MODEL_SPECS[name]
    kw = dict(profile_fn=profile_fn, alphas=alphas, seed=seed, B=fit_B)
    if with_ers:
        if ers_factory is None: raise RuntimeError("ERS unavailable")
        m9 = calibrate.fit_select(train, baselines.MODEL_SPECS["b9_cec_no_ers"][0], **kw)
        fn, en = ers_factory(m9, seed=seed); kw.update(extra_features_fn=fn, extra_names=en)
    return calibrate.fit_select(train, names, **kw)


def gate_coverage(records):
    """Coverage of the recorded V7-B gate (b3) over the labelled records: a property of V7-B verdicts, not of any held-out label."""
    lab = [r for r in records if r.y is not None]
    return sum(r.v7b_verdict == schema.VERDICTS[2] for r in lab) / max(len(lab), 1)


def freeze(train, name, seed=0, alphas=FROZEN_ALPHAS, B=1000, fit_B=300, profile_fn=None, ers_factory=None, target_cov="gate"):
    """Learn model + thresholds from `train` (development/calibration projects) only. Reads train labels, never any other data."""
    m = _fit_system(train, name, seed, fit_B, alphas, profile_fn, ers_factory)
    tc = gate_coverage(train) if target_cov == "gate" else target_cov
    return Frozen(name, m, calibrate.frozen_thresholds(m.oof, alphas, tc, B, seed), tc)


def apply_frozen(fz, test):
    """Decisions for held-out records. Pure function of (frozen model, frozen thresholds, evidence): NEVER touches rec.y, and the
    cut never depends on the distribution of held-out scores. -> (risk array, {rule: bool NDO array})."""
    risk = np.array([fz.model.predict_risk(r) for r in test])
    base = np.array([r.integrity_ok and not calibrate.is_div(r) and calibrate.is_eligible(r) for r in test])
    return risk, {rule: base & (risk <= tau) for rule, tau in fz.taus.items()}


def _boot_pair(ndo_a, ndo_b, y, W):
    def rj(nd):
        num = (W * nd * y).sum(1); den = (W * nd).sum(1)
        return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan), num / W.sum(1), den / W.sum(1)
    (ra, ja, ca), (rb, jb, cb) = rj(ndo_a), rj(ndo_b)
    one = lambda x: stats.selective_risk(y, x)
    return {"risk_diff_b_minus_a": (one(ndo_b) - one(ndo_a)) if ndo_a.any() and ndo_b.any() else None, "risk_diff_ci95": list(stats.pct_ci(rb - ra)),
            "fa_mass_diff_b_minus_a": float((ndo_b * y).mean() - (ndo_a * y).mean()), "fa_mass_diff_ci95": list(stats.pct_ci(jb - ja)),
            "coverage_diff_b_minus_a": float(ndo_b.mean() - ndo_a.mean()), "coverage_diff_ci95": list(stats.pct_ci(cb - ca))}


def frozen_eval(records, seed=0, outer_k=5, B=10000, fit_B=300, systems=FROZEN_SYSTEMS, profile_fn=None, ers_factory="default"):
    """Project-grouped outer CV in which every held-out fold is scored by thresholds FROZEN on the other projects (see freeze/apply_frozen).
    Realised coverage differs across models and folds; that is the point. Reports pooled held-out coverage, false-assurance risk, FA mass
    (P(NDO and Y=1) over all labelled pairs; comparable across coverages) with project-clustered CIs, per-fold coverage, and paired contrasts."""
    recs = sorted([r for r in records if r.y is not None], key=lambda r: (r.project, r.pair_id))
    y = np.array([r.y for r in recs], float); proj = np.array([r.project for r in recs]); N = len(recs)
    if ers_factory == "default": ers_factory = default_ers_factory()
    fold = stats.project_folds(proj, outer_k, seed); folds = sorted(set(fold))
    ndo = {(n, rule): np.zeros(N, bool) for n in systems for rule in FROZEN_RULES}; fold_cov = {k: [] for k in ndo}; taus = {}; unavailable = {}
    for f in folds:
        tr = [i for i in range(N) if fold[i] != f]; te = [i for i in range(N) if fold[i] == f]
        assert not (set(proj[tr]) & set(proj[te]))
        for n in systems:
            if n in unavailable: continue
            try: fz = freeze(_arr(recs, tr), n, seed, FROZEN_ALPHAS, B=fit_B, fit_B=fit_B, profile_fn=profile_fn, ers_factory=ers_factory)
            except RuntimeError as e: unavailable[n] = str(e); continue
            _, dec = apply_frozen(fz, _arr(recs, te)); taus[f"{n}|fold{f}"] = {"|".join(map(str, k)): t for k, t in fz.taus.items()}
            taus[f"{n}|fold{f}"]["target_cov"] = fz.target_cov
            for rule, d in dec.items(): ndo[(n, rule)][te] = d; fold_cov[(n, rule)].append(float(d.mean()))
    W = stats.cluster_counts(proj, B, seed); rows = []
    for (n, rule), d in ndo.items():
        if n in unavailable: continue
        s = _sys_summary(n, y, proj, d, B, seed)
        reps = (W * d * y).sum(1) / W.sum(1)
        s.update(rule="|".join(map(str, rule)), fa_mass=float((d * y).mean()), fa_mass_ci95=list(stats.pct_ci(reps)), fold_coverage=fold_cov[(n, rule)])
        rows.append(s)
    refs = []
    for n in baselines.RULE_NAMES:
        d = _cv_rule(recs, n, profile_fn)[1]
        s = _sys_summary(n, y, proj, d, B, seed); s.update(rule="rule"); refs.append(s)
    pairs = []
    for rule in FROZEN_RULES:
        for a_, b_ in (("b7_cov_calibration", "b9_cec_no_ers"), ("b7_cov_calibration", "b8_full_cec"), ("b9_cec_no_ers", "b8_full_cec")):
            if a_ in unavailable or b_ in unavailable or a_ not in systems or b_ not in systems: continue
            pairs.append({"rule": "|".join(map(str, rule)), "a": a_, "b": b_, **_boot_pair(ndo[(a_, rule)], ndo[(b_, rule)], y, W)})
    return {"banner": BANNER, "policy": policy.current(), "seed": seed, "outer_k": outer_k, "n_labelled": N, "n_projects": len(set(proj)), "bootstrap_B": B,
            "target_coverage": "V7-B gate coverage of the calibration (training) projects of each fold", "systems": rows, "reference_rules": refs, "paired": pairs,
            "thresholds_per_fold": taus, "unavailable": unavailable}


def ers_placebo(records, seed=0, outer_k=5, n_perm=100, fit_B=50, profile_fn=None, ers_factory="default"):
    """Is the held-out log-loss gain of full CEC (with ERS) over CEC-without-ERS distinguishable from noise? Placebo: the ERS response vectors are
    shuffled across records (train set and test set of each outer project fold separately, so the marginal ERS distribution is kept and
    its link to the record/label is broken); the model is refit and rescored identically. p = P(null gain >= observed gain). Eligible pairs only."""
    recs = sorted([r for r in records if r.y is not None], key=lambda r: (r.project, r.pair_id))
    y = np.array([r.y for r in recs], float); proj = np.array([r.project for r in recs]); N = len(recs)
    if ers_factory == "default": ers_factory = default_ers_factory()
    if ers_factory is None: return {"error": "ERS unavailable"}
    fold = stats.project_folds(proj, outer_k, seed); folds = sorted(set(fold))
    names9 = baselines.MODEL_SPECS["b9_cec_no_ers"][0]; kw = dict(profile_fn=profile_fn, alphas=(0.15,), seed=seed, B=fit_B)
    elig = np.array([calibrate.is_eligible(r) for r in recs]); p9 = np.full(N, np.nan); p8 = np.full(N, np.nan); pp = np.full((n_perm, N), np.nan)
    for f in folds:
        tr = [i for i in range(N) if fold[i] != f]; te = [i for i in range(N) if fold[i] == f]
        m9 = calibrate.fit_select(_arr(recs, tr), names9, **kw); fn, en = ers_factory(m9, seed=seed)
        vec = {recs[i].pair_id: fn(recs[i]) for i in tr + te}
        names8 = baselines.MODEL_SPECS["b8_full_cec"][0]
        def fit8(vmap):
            return calibrate.fit_select(_arr(recs, tr), names8, extra_features_fn=lambda r: vmap[r.pair_id], extra_names=en, **kw)
        for i in te: p9[i] = m9.predict_risk(recs[i])
        m8 = fit8(vec)
        for i in te: p8[i] = m8.predict_risk(recs[i])
        for k in range(n_perm):
            rng = stats.rng_for(seed, f"placebo{f}_{k}"); vm = {}
            for grp in (tr, te):
                perm = rng.permutation(len(grp))
                for a, b in zip(grp, perm): vm[recs[a].pair_id] = vec[recs[grp[b]].pair_id]
            mk = fit8(vm)
            for i in te: pp[k, i] = mk.predict_risk(recs[i])
    ll9 = stats.logloss(p9[elig], y[elig]); gain = ll9 - stats.logloss(p8[elig], y[elig])
    null = np.array([ll9 - stats.logloss(pp[k][elig], y[elig]) for k in range(n_perm)])
    return {"policy": policy.current(), "n_eligible": int(elig.sum()), "logloss_b9": ll9, "observed_gain_b9_minus_b8": float(gain),
            "paired_cluster_bootstrap": stats.paired_logloss(p8[elig], p9[elig], y[elig], proj[elig], 2000, seed) | {"note": "point = logloss(b9)-logloss(b8) via paired_logloss(a=b8,b=b9); positive = ERS better"},
            "placebo_null_mean": float(null.mean()), "placebo_null_q95": float(np.quantile(null, 0.95)), "placebo_p": stats.permutation_p(gain, null), "n_perm": n_perm}


def cli_register(sub):
    p = sub.add_parser("evaluate", help="nested project-CV evaluation of all baselines on a records jsonl (development data = exploratory)")
    p.add_argument("--records", required=True); p.add_argument("--out", required=True); p.add_argument("--seed", type=int, default=0)
    p.add_argument("--boot", type=int, default=stats.B_DEFAULT)
    p.set_defaults(func=lambda a: (run(load_records(a.records), a.out, a.seed, a.boot), 0)[1])

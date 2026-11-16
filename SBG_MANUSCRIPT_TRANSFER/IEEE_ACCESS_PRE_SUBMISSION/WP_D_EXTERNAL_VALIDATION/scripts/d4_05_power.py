"""d4_05_power.py -- Task 5 (POST-HOC, APPROXIMATE, SIMULATION-BASED; nothing pre-registered).

A. What each observed CI rules out (reads 02_inference.json): for thresholds 0.5/0.6/0.7/0.75/0.8/0.897 whether the
   95% two-sided percentile CI and the 95% one-sided upper bound exclude AUROC >= threshold.  (0.897 = V10 internal
   test AUROC quoted in the handoff; used only as a reference line, V10 files are NOT read.)
B. Simulation of power / minimum detectable effect (MDE) under a simple generative model, labelled APPROXIMATION:
     latent z = mu*y + sqrt(rho_p)*u_project + sqrt(rho_b)*v_bug + sqrt(1-rho_p-rho_b)*e ,  score s = max(z - kappa, 0)
   (censored binormal: reproduces the point mass at 0). kappa is set so that P(s=0|neg) equals the observed negative
   zero fraction of the design.  Design (clusters, labels per cluster) is the observed one.  True AUROC theta(mu) is
   computed by numerical integration.  Test: cluster-jackknife Wald test of theta_hat > 0.5 (one-sided 2.5%),
   jackknife by bug and (BugsInPy) by project (t_{G-1} critical value).  Size at mu=0 is reported to show calibration.
   ICC (rank-based one-way ANOVA on NEGATIVES only, no labels of positives used) gives the 'estimated' rho.
Outputs: raw/WPD-D4_stats/05_power.json
"""
import json
import math
import random
import sys
import zlib
from pathlib import Path
from statistics import NormalDist

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

NSIM = 1500
ND = NormalDist()
C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
S = get_sets(C, audit)
THRESH = [0.5, 0.6, 0.7, 0.75, 0.8, 0.897]
T_CRIT = {10: 2.228, 9: 2.262, 11: 2.201}   # two-sided 95% t quantiles (project-level G-1 df)

out = {"script": "scripts/d4_05_power.py", "status": "POST-HOC APPROXIMATION", "NSIM": NSIM,
       "input_manifest": input_manifest()}

# ------------------------------------------------------------------ A. what CIs rule out
inf = json.load(open(OUT / "02_inference.json"))
rule = {}
for sid, r in inf["results"].items():
    rule[sid] = {"auroc": r["auroc"], "status": r["status"], "levels": {}}
    for lv, d in r["levels"].items():
        lo, hi = d["ci95"]["percentile"]
        ub = d["one_sided_95_upper_bound"]
        rule[sid]["levels"][lv] = {
            "ci95_percentile": [lo, hi], "bca": d["ci95"]["bca"], "one_sided_95_upper": ub,
            "n_clusters": d["n_clusters"],
            "ci_width": round(hi - lo, 4),
            "two_sided_CI_excludes_theta>=": [t for t in THRESH if t > hi],
            "one_sided_upper_excludes_theta>=": [t for t in THRESH if t > ub],
            "CI_includes_0.5": lo <= 0.5 <= hi,
            "bootstrap_tail_P(theta*>=x)": d["boot_P(theta*>=x)"]}
out["what_cis_rule_out"] = rule


# ------------------------------------------------------------------ B. simulation
def theta_of_mu(mu, kappa):
    """True tie-aware AUROC of censored binormal (neg N(0,1), pos N(mu,1), s=max(z-kappa,0))."""
    pn0 = ND.cdf(kappa)                       # P(neg score 0)
    pp0 = ND.cdf(kappa - mu)
    val = pn0 * ((1 - pp0) + 0.5 * pp0)       # neg=0
    # neg>0: integrate density over x>kappa, P(z_p > x)
    n, hi = 6000, 10.0
    h = (hi - kappa) / n
    acc = 0.0
    for i in range(n + 1):
        x = kappa + i * h
        w = 0.5 if i in (0, n) else 1.0
        acc += w * ND.pdf(x) * (1 - ND.cdf(x - mu))
    return val + acc * h


def icc_rank(values, clusters):
    """Rank-based one-way ANOVA ICC(1) (unbalanced n0 correction)."""
    n = len(values)
    order = sorted(range(n), key=values.__getitem__)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    g = {}
    for r, c in zip(ranks, clusters):
        g.setdefault(c, []).append(r)
    k = len(g)
    grand = sum(ranks) / n
    ssb = sum(len(v) * (sum(v) / len(v) - grand) ** 2 for v in g.values())
    ssw = sum(sum((x - sum(v) / len(v)) ** 2 for x in v) for v in g.values())
    if n - k <= 0 or k < 2:
        return None
    msb, msw = ssb / (k - 1), ssw / (n - k)
    n0 = (n - sum(len(v) ** 2 for v in g.values()) / n) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw)


def jack_se(sc, lab, groups):
    ths = [a for _, a in jackknife_clusters(sc, lab, groups) if a is not None]
    G = len(ths)
    m = sum(ths) / G
    return math.sqrt((G - 1) / G * sum((t - m) ** 2 for t in ths)), G


def simulate(design, kappa, mu, rho_p, rho_b, nsim, seed, levels):
    """design: list of (bug, project, label). Returns reject fractions + mean CI half-width per level."""
    rng = random.Random(seed)
    bugs = [d[0] for d in design]
    projs = [d[1] for d in design]
    lab = [d[2] for d in design]
    gb = groups_of(bugs)
    gp = groups_of(projs) if levels.get("project") else None
    rej = {k: 0 for k in levels}
    hw = {k: 0.0 for k in levels}
    ths = []
    for _ in range(nsim):
        ua = {p: rng.gauss(0, 1) for p in set(projs)}
        va = {b: rng.gauss(0, 1) for b in set(bugs)}
        sc = []
        for (b, p, y) in design:
            z = mu * y + math.sqrt(rho_p) * ua[p] + math.sqrt(rho_b) * va[b] + math.sqrt(max(1e-9, 1 - rho_p - rho_b)) * rng.gauss(0, 1)
            sc.append(max(z - kappa, 0.0))
        th = auroc(sc, lab)
        ths.append(th)
        for lv, groups in (("bug", gb), ("project", gp)):
            if lv not in levels:
                continue
            se, G = jack_se(sc, lab, groups)
            crit = 1.96 if G >= 30 else T_CRIT.get(G - 1, 2.3)
            if se > 0 and (th - 0.5) / se > crit:
                rej[lv] += 1
            hw[lv] += crit * se
    return ({k: rej[k] / nsim for k in levels}, {k: hw[k] / nsim for k in levels}, sum(ths) / nsim)


designs = {"BP-v7-EVAL": "bugsinpy", "BP-v8-exSP2": "bugsinpy", "QC-v7-ALL": "quixbugs", "QC-v8-exSP2": "quixbugs"}
MUS = [0.0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0]
sim = {}
for sid, corp in designs.items():
    s = S[sid]
    recs = s["recs"]
    sc = vecs(recs, "sbg_v5", s["src"], s["impute"])
    neg0 = sum(1 for x, r in zip(sc, recs) if r["label"] == 0 and x == 0) / sum(1 - r["label"] for r in recs)
    kappa = ND.inv_cdf(neg0)
    design = [(r["bug"], r["project"] or r["bug"], r["label"]) for r in recs]
    negidx = [i for i, r in enumerate(recs) if r["label"] == 0]
    icc_b = icc_rank([sc[i] for i in negidx], [recs[i]["bug"] for i in negidx])
    icc_p = icc_rank([sc[i] for i in negidx], [recs[i]["project"] for i in negidx]) if corp == "bugsinpy" else None
    rho_p_est = max(0.0, icc_p) if icc_p is not None else 0.0
    rho_b_est = max(0.0, (icc_b or 0.0) - rho_p_est)
    levels = {"bug": True}
    if corp == "bugsinpy":
        levels["project"] = True
    d = {"n": len(recs), "n_pos": sum(r["label"] for r in recs), "neg_zero_frac_used_for_kappa": round(neg0, 4),
         "kappa": round(kappa, 4), "icc_bug_rank_negatives": None if icc_b is None else round(icc_b, 4),
         "icc_project_rank_negatives": None if icc_p is None else round(icc_p, 4),
         "rho_p_est": round(rho_p_est, 4), "rho_b_est": round(rho_b_est, 4), "scenarios": {}}
    for scen, (rp, rb) in {"rho0": (0.0, 0.0), "rho_est": (rho_p_est, rho_b_est), "rho_high(0.2/0.2)": (0.2, 0.2) if corp == "bugsinpy" else (0.0, 0.2)}.items():
        rows = []
        for mu in MUS:
            th_true = theta_of_mu(mu, kappa)
            rj, hw, mth = simulate(design, kappa, mu, rp, rb, NSIM, zlib.crc32((sid + scen + str(mu)).encode()), levels)
            rows.append({"mu": mu, "theta_true": round(th_true, 4), "mean_theta_hat": round(mth, 4),
                         "power_or_size": {k: round(v, 3) for k, v in rj.items()},
                         "mean_95CI_halfwidth(jackknife-approx)": {k: round(v, 4) for k, v in hw.items()}})
        # MDE (80% power) by linear interpolation of theta_true vs power, per level
        mde = {}
        for lv in levels:
            pts = [(r["theta_true"], r["power_or_size"][lv]) for r in rows]
            m = None
            for (t0, p0), (t1, p1) in zip(pts, pts[1:]):
                if p0 < 0.8 <= p1:
                    m = round(t0 + (0.8 - p0) * (t1 - t0) / (p1 - p0), 3)
                    break
            mde[lv] = m
        d["scenarios"][scen] = {"rho_p": rp, "rho_b": rb, "rows": rows, "MDE_theta_at_80pct_power": mde,
                                "size_at_mu0": rows[0]["power_or_size"]}
        print(sid, scen, "size", rows[0]["power_or_size"], "MDE", mde, "halfwidth@0", rows[0]["mean_95CI_halfwidth(jackknife-approx)"], flush=True)
    sim[sid] = d
out["simulation"] = sim
write_json("05_power.json", out)

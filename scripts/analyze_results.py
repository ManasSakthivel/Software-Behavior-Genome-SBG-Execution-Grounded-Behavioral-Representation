#!/usr/bin/env python
"""Pre-declared analysis of per-pair results (see research/evaluation/STATISTICAL_ANALYSIS_PLAN.md).

Input CSV columns: project,pair_id,system,verdict,sufficiency,truth,cpu_s,mem_mb  (+ optional dataset).
Output: <out>/*.json and *.csv. Unit of analysis is the project; all CIs resample projects.
Usage: python scripts/analyze_results.py results/processed/pairs.csv --out results/statistics \
           --reference B1 --seed 42 --boot 10000
"""
import argparse, itertools, json, zlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

DIV, NDO, INS = "DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED", "INSUFFICIENT"
LEVEL = {"S0": 0, "S1": 1, "S2": 2, "S3": 3}
COLS = ["project", "pair_id", "system", "verdict", "sufficiency", "truth", "cpu_s", "mem_mb"]
PRIMARY_OUT = ["false_assurance", "detection"]          # Holm family 1
SECONDARY_OUT = ["abstention", "false_alarm"]           # Holm family 2 (exploratory)
SIGN = {"detection": 1, "false_assurance": -1, "abstention": -1, "false_alarm": -1}  # improvement = SIGN*diff


def load(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    miss = [c for c in COLS if c not in df.columns]
    if miss:
        raise ValueError(f"missing columns {miss}")
    if "dataset" not in df.columns:
        df["dataset"] = "all"
    if df.duplicated(["system", "pair_id"]).any():
        raise ValueError("duplicate (system, pair_id) rows")
    # ITT: anything that is not a recognised verdict (timeout, crash, blank) is a failed run = abstention.
    df["verdict_n"] = np.where(df.verdict.isin([DIV, NDO, INS]), df.verdict, "FAILED")
    df["level"] = df.sufficiency.map(LEVEL).fillna(-1).astype(int)
    if (df.groupby("pair_id").truth.nunique() > 1).any():
        raise ValueError("truth differs across systems for the same pair_id")
    return df


def outcome_frame(df):
    """One row per (system, pair) over the full pair universe; absent rows become FAILED (missing data = failure)."""
    pairs = df.drop_duplicates("pair_id")[["pair_id", "project", "dataset", "truth"]]
    pairs = pairs[pairs.truth.isin(["DIV", "NO_OBS_DIFF"])]  # primary-eligible only (plan sec. 3)
    parts = []
    for s in sorted(df.system.unique()):
        d = pairs.merge(df[df.system == s][["pair_id", "verdict_n", "level", "cpu_s", "mem_mb"]], on="pair_id", how="left")
        d["system"] = s
        d["verdict_n"] = d.verdict_n.fillna("FAILED")
        d["level"] = d.level.fillna(-1).astype(int)
        parts.append(d)
    o = pd.concat(parts, ignore_index=True)
    isdiv, isno = o.truth == "DIV", o.truth == "NO_OBS_DIFF"
    o["detection"] = ((o.verdict_n == DIV) & isdiv).astype(int)
    o["false_assurance"] = ((o.verdict_n == NDO) & isdiv).astype(int)
    o["false_alarm"] = ((o.verdict_n == DIV) & isno).astype(int)
    o["abstention"] = (~o.verdict_n.isin([DIV, NDO])).astype(int)
    o["den_div"], o["den_no"], o["den_all"] = isdiv.astype(int), isno.astype(int), 1
    return o


DEN = {"detection": "den_div", "false_assurance": "den_div", "false_alarm": "den_no", "abstention": "den_all"}


def _rng(seed, label):
    return np.random.default_rng([seed, zlib.crc32(label.encode())])


def ratio_ci(num, den, boot, seed, label, level=0.95):
    """Cluster bootstrap of sum(num)/sum(den); arrays are per-project. Percentile CI."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    K = len(num)
    if K == 0 or den.sum() == 0:
        return dict(est=None, lo=None, hi=None, K=K, n=int(den.sum()))
    idx = _rng(seed, label).integers(0, K, (boot, K))
    d = den[idx].sum(1)
    r = num[idx].sum(1)[d > 0] / d[d > 0]
    a = (1 - level) / 2
    lo, hi = np.quantile(r, [a, 1 - a])
    return dict(est=float(num.sum() / den.sum()), lo=float(lo), hi=float(hi), K=K, n=int(den.sum()))


def sign_flip_p(d, n_mc=20000, seed=42, exact_max=16):
    """Two-sided project-level sign-flip permutation test on per-project sums d_j; exact if K<=exact_max."""
    d = np.asarray(d, float)
    d = d[d != 0]
    if len(d) == 0:
        return 1.0
    obs = abs(d.sum())
    if len(d) <= exact_max:
        signs = np.array(list(itertools.product([-1, 1], repeat=len(d))))
        return float(np.mean(np.abs(signs @ d) >= obs - 1e-9))
    s = np.random.default_rng(seed).choice([-1.0, 1.0], size=(n_mc, len(d)))
    return float((1 + np.sum(np.abs(s @ d) >= obs - 1e-9)) / (1 + n_mc))


def mcnemar_exact(b, c):
    return 1.0 if b + c == 0 else float(stats.binomtest(min(b, c), b + c, 0.5).pvalue)


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def icc_anova(y, g):
    """One-way ANOVA ICC estimator (unbalanced, Smith correction); clipped to [0,1]."""
    y, g = np.asarray(y, float), np.asarray(g)
    u, inv, m = np.unique(g, return_inverse=True, return_counts=True)
    K, N = len(u), len(y)
    if K < 2 or N == K:
        return 0.0
    means = np.bincount(inv, y) / m
    msb = np.sum(m * (means - y.mean()) ** 2) / (K - 1)
    msw = np.sum((y - means[inv]) ** 2) / (N - K)
    m0 = (N - np.sum(m ** 2) / N) / (K - 1)
    den = msb + (m0 - 1) * msw
    return float(np.clip((msb - msw) / den, 0, 1)) if den > 0 else 0.0


def design_stats(groups, y=None):
    _, m = np.unique(groups, return_counts=True)
    n, K = int(m.sum()), len(m)
    rho = icc_anova(y, groups) if y is not None else None
    mt = float((m ** 2).sum() / m.sum())
    deff = 1 + (mt - 1) * rho if rho is not None else None
    return dict(pairs=n, projects=K, mean_cluster=float(n / K), max_cluster=int(m.max()), icc=rho,
                design_effect=deff, kish_n=float(n / deff) if deff else None)


def per_project(o, metric):
    g = o.groupby("project")
    return g[metric].sum().to_numpy(), g[DEN[metric]].sum().to_numpy()


def risk_coverage(o, boot, seed):
    rows = []
    for s, d in o.groupby("system"):
        for thr in ["none", "S1", "S2", "S3"]:
            need = -1 if thr == "none" else LEVEL[thr]
            dec_ndo = (d.verdict_n == NDO) & (d.level >= need)
            decided = (d.verdict_n == DIV) | dec_ndo
            err = (dec_ndo & (d.truth == "DIV")) | ((d.verdict_n == DIV) & (d.truth == "NO_OBS_DIFF"))
            t = pd.DataFrame(dict(project=d.project, dec=decided.astype(int), err=err.astype(int), one=1))
            g = t.groupby("project").sum()
            cov = ratio_ci(g.dec, g.one, boot, seed, f"cov{s}{thr}")
            rk = ratio_ci(g.err, g.dec, boot, seed, f"risk{s}{thr}")
            rows.append(dict(system=s, min_sufficiency_for_NDO=thr, coverage=cov["est"], cov_lo=cov["lo"], cov_hi=cov["hi"],
                             risk=rk["est"], risk_lo=rk["lo"], risk_hi=rk["hi"], decided=int(g.dec.sum()), eligible=int(g.one.sum())))
    return pd.DataFrame(rows)


def system_metrics(o, boot, seed):
    rows = []
    for s, d in o.groupby("system"):
        for m in PRIMARY_OUT + SECONDARY_OUT:
            num, den = per_project(d, m)
            r = ratio_ci(num, den, boot, seed, f"{s}{m}")
            rows.append(dict(system=s, outcome=m, family="primary" if m in PRIMARY_OUT else "secondary", **r))
    return pd.DataFrame(rows)


def paired(o, systems, ref, boot, seed, n_perm):
    pairs = [(s, ref) for s in systems if s != ref] if ref else list(itertools.combinations(systems, 2))
    rows = []
    for t, r in pairs:
        a, b = o[o.system == t].set_index("pair_id"), o[o.system == r].set_index("pair_id")
        for m in PRIMARY_OUT + SECONDARY_OUT:
            den = a[DEN[m]] == 1
            yt, yr = a.loc[den, m], b.loc[den.index[den], m]
            proj = a.loc[den, "project"]
            bb, cc = int(((yt == 1) & (yr == 0)).sum()), int(((yt == 0) & (yr == 1)).sum())
            dj = (yt - yr).groupby(proj).sum()
            n = len(yt)
            ci = ratio_ci(dj.to_numpy(), proj.groupby(proj).size().reindex(dj.index).to_numpy(), boot, seed, f"{t}-{r}{m}")
            diff = ci["est"]
            imp = None if diff is None else SIGN[m] * diff
            ilo, ihi = (None, None) if diff is None else sorted([SIGN[m] * ci["lo"], SIGN[m] * ci["hi"]])
            rr = float(yr.mean())
            rows.append(dict(test=t, reference=r, outcome=m, family="primary" if m in PRIMARY_OUT else "secondary",
                             n_pairs=n, projects=int(proj.nunique()), rate_test=float(yt.mean()) if n else None, rate_ref=rr if n else None,
                             diff=diff, diff_lo=ci["lo"], diff_hi=ci["hi"], improvement=imp, impr_lo=ilo, impr_hi=ihi,
                             rel_change=(None if not rr else diff / rr), b_test_only=bb, c_ref_only=cc,
                             discordance=(bb + cc) / n if n else None, odds_b_over_c=(bb / cc if cc else None),
                             p_signflip=sign_flip_p(dj.to_numpy(), n_perm, seed), p_mcnemar_exact_pairlevel=mcnemar_exact(bb, cc)))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for fam in ["primary", "secondary"]:
        k = df.family == fam
        df.loc[k, "p_holm"] = holm(df.loc[k, "p_signflip"].to_numpy())
    # +10pp practical-significance rule (P0 D8): Holm-adjusted p<.05 AND lower 95% cluster-bootstrap bound of the improvement > 0.10.
    df["meets_plus10pp"] = (df.family == "primary") & (df.p_holm < 0.05) & (df.impr_lo > 0.10)
    return df


def run(inp, out, ref=None, seed=42, boot=10000, n_perm=20000):
    df = load(inp)
    o = outcome_frame(df)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    systems = sorted(o.system.unique())
    counts = (df.groupby(["system", "truth", "verdict_n"]).size().rename("n").reset_index())
    per_proj = o.groupby(["system", "project"])[["detection", "false_assurance", "false_alarm", "abstention", "den_div", "den_no", "den_all"]].sum().reset_index()
    per_ds = o.groupby(["system", "dataset"])[["detection", "false_assurance", "false_alarm", "abstention", "den_div", "den_no", "den_all"]].sum().reset_index()
    cost = df.assign(cpu_s=pd.to_numeric(df.cpu_s, errors="coerce"), mem_mb=pd.to_numeric(df.mem_mb, errors="coerce")) \
        .groupby("system")[["cpu_s", "mem_mb"]].agg(["median", "max", "sum"]).round(3)
    cost.columns = ["_".join(c) for c in cost.columns]
    sm, rc, pc = system_metrics(o, boot, seed), risk_coverage(o, boot, seed), paired(o, systems, ref, boot, seed, n_perm)
    d0 = o[(o.system == systems[0]) & (o.truth == "DIV")]
    ex = df[~df.truth.isin(["DIV", "NO_OBS_DIFF"])].drop_duplicates("pair_id").truth.value_counts().to_dict()
    for name, t in [("class_counts", counts), ("per_project", per_proj), ("per_dataset", per_ds), ("system_metrics", sm),
                    ("risk_coverage", rc), ("paired_comparisons", pc), ("cost", cost.reset_index())]:
        t.to_csv(out / f"{name}.csv", index=False)
        (out / f"{name}.json").write_text(json.dumps(json.loads(t.to_json(orient="records")), indent=1))
    summary = dict(input=str(inp), seed=seed, bootstrap_reps=boot, signflip_mc=n_perm, reference=ref, systems=systems,
                   excluded_from_primary_denominators=ex, failed_or_missing_runs=int((o.verdict_n == "FAILED").sum()),
                   design_div_pairs=design_stats(d0.project.to_numpy()), pairs_total_primary=int(o.pair_id.nunique()))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", default="results/statistics")
    ap.add_argument("--reference", default=None, help="reference system; default all unordered pairs")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--perm", type=int, default=20000)
    a = ap.parse_args()
    print(json.dumps(run(a.input, a.out, a.reference, a.seed, a.boot, a.perm), indent=1))

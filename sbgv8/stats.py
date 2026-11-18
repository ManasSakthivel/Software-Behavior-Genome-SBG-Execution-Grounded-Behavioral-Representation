"""V8 statistics: project-clustered bootstrap, selective risk, matched coverage, calibration metrics, Holm, power report.
Pure numpy/scipy. Arrays are per-pair; `proj` is a per-pair project label. Unit of resampling is the PROJECT (analyze_results.py convention).
Conventions: y in {0,1} (y=None pairs are removed by the caller and counted); `score` = predicted false-assurance risk (lower = safer);
`elig` = pair may receive NDO at all (False => never issued, score ignored). Coverage c = P(NDO) over ALL labelled pairs.
"""
from __future__ import annotations
import math, zlib
import numpy as np
from scipy import optimize, stats as sps

ALPHA_GRID = (0.10, 0.15)
CSTAR_GRID = (0.2, 0.3, 0.4)
B_DEFAULT = 10000


def rng_for(seed, label=""):
    return np.random.default_rng([int(seed), zlib.crc32(label.encode())])


def _codes(proj):
    u, idx = np.unique(np.asarray(proj, dtype=object).astype(str), return_inverse=True)
    return u, idx


def cluster_counts(proj, B=B_DEFAULT, seed=0):
    """B x N matrix of resample weights: project drawn with replacement, every pair of a drawn project gets its multiplicity.
    Same (proj, B, seed) -> identical draws, so paired comparisons share resamples."""
    u, idx = _codes(proj)
    P = len(u)
    cnt = rng_for(seed, "cluster").multinomial(P, np.full(P, 1.0 / P), size=B)
    return cnt[:, idx].astype(float)


def pct_ci(reps, level=0.95):
    r = np.asarray(reps, float); r = r[~np.isnan(r)]
    if len(r) == 0: return (float("nan"), float("nan"))
    a = (1 - level) / 2
    return float(np.quantile(r, a)), float(np.quantile(r, 1 - a))


def bca_ci(theta, reps, jack, level=0.95):
    """BCa interval; `jack` = leave-one-project-out estimates."""
    r = np.asarray(reps, float); r = r[~np.isnan(r)]; j = np.asarray(jack, float); j = j[~np.isnan(j)]
    if len(r) < 20 or len(j) < 3 or np.isnan(theta): return pct_ci(reps, level)
    z0 = sps.norm.ppf(np.clip((r < theta).mean() + 0.5 * (r == theta).mean(), 1e-6, 1 - 1e-6))
    d = j.mean() - j; den = 6 * (np.sum(d ** 2) ** 1.5)
    acc = np.sum(d ** 3) / den if den > 0 else 0.0
    out = []
    for q in ((1 - level) / 2, 1 - (1 - level) / 2):
        zq = sps.norm.ppf(q); adj = sps.norm.cdf(z0 + (z0 + zq) / (1 - acc * (z0 + zq)))
        out.append(float(np.quantile(r, np.clip(adj, 0, 1))))
    return tuple(out)


def selective_risk(y, ndo, w=None):
    """R = P(Y=1 | NDO) ; nan if no NDO. `ndo` may be fractional (0..1)."""
    y = np.asarray(y, float); ndo = np.asarray(ndo, float); w = np.ones_like(y) if w is None else w
    n = (w * ndo).sum()
    return float((w * ndo * y).sum() / n) if n > 0 else float("nan")


def coverage(ndo, w=None):
    ndo = np.asarray(ndo, float); w = np.ones_like(ndo) if w is None else w
    return float((w * ndo).sum() / w.sum())


# ---------------- matched coverage ----------------
def _groups(score, elig, y):
    """Eligible items sorted by score; returns (order, starts) where equal scores form one group (fractional inclusion at the boundary)."""
    ei = np.flatnonzero(elig)
    o = ei[np.argsort(np.asarray(score)[ei], kind="stable")]
    s = np.asarray(score)[o]
    starts = np.r_[0, np.flatnonzero(np.diff(s) != 0) + 1] if len(o) else np.array([], int)
    return o, starts


def matched_risk(score, elig, y, cstar, w=None):
    """Selective risk when the lowest-score eligible pairs are issued until coverage == cstar (fractional at ties). w: B x N weights or None.
    Returns scalar (w None) or length-B array; nan if cstar exceeds eligible share."""
    y = np.asarray(y, float); N = len(y)
    one = w is None
    W = np.ones((1, N)) if one else w
    o, st = _groups(score, np.asarray(elig, bool), y)
    out = np.full(len(W), np.nan)
    if len(o):
        gw = np.add.reduceat(W[:, o], st, axis=1); gy = np.add.reduceat(W[:, o] * y[o], st, axis=1)
        k = cstar * W.sum(1, keepdims=True)
        prev = np.cumsum(gw, 1) - gw
        take = np.clip(k - prev, 0, gw)
        frac = np.divide(take, gw, out=np.zeros_like(take), where=gw > 0)
        n = take.sum(1); fp = (frac * gy).sum(1)
        ok = (np.cumsum(gw, 1)[:, -1] >= k[:, 0] - 1e-9) & (n > 0)
        out = np.where(ok, fp / np.where(n > 0, n, 1), np.nan)
    return float(out[0]) if one else out


def risk_coverage_curve(score, elig, y):
    """Points (coverage, risk, n_ndo) as the threshold sweeps up over distinct eligible scores."""
    y = np.asarray(y, float); o, st = _groups(score, np.asarray(elig, bool), y)
    if not len(o): return []
    s = np.asarray(score)[o]; ends = np.r_[st[1:], len(o)] - 1
    cy = np.cumsum(y[o]); N = len(y)
    return [(float((e + 1) / N), float(cy[e] / (e + 1)), int(e + 1)) for e in ends]


def coverage_at_risk(curve, alpha):
    """Largest coverage with empirical risk <= alpha (optimistic: threshold picked on the same data)."""
    ok = [c for c, r, _ in curve if r <= alpha]
    return max(ok) if ok else 0.0


def select_threshold(score, elig, y, proj, alpha, B=1000, seed=0, level=0.95):
    """Largest-coverage threshold whose one-sided upper project-cluster-bootstrap bound on selective risk <= alpha.
    Returns (tau, info); tau=-inf (issue nothing) if no threshold qualifies. Pairs with score<=tau and elig are issued."""
    y = np.asarray(y, float); score = np.asarray(score, float); elig = np.asarray(elig, bool)
    o, st = _groups(score, elig, y)
    if not len(o): return -math.inf, {"coverage": 0.0, "risk": float("nan"), "ub": float("nan")}
    ends = np.r_[st[1:], len(o)] - 1
    W = cluster_counts(proj, B, seed)[:, o]
    cn = np.cumsum(W, 1)[:, ends]; cf = np.cumsum(W * y[o], 1)[:, ends]
    ub = np.quantile(np.where(cn > 0, cf / np.where(cn > 0, cn, 1), 0.0), level, axis=0)
    cum_n = np.arange(1, len(o) + 1)[ends]; cum_f = np.cumsum(y[o])[ends]
    good = np.flatnonzero(ub <= alpha)
    if not len(good): return -math.inf, {"coverage": 0.0, "risk": float("nan"), "ub": float(ub.min())}
    g = good[-1]
    return float(score[o][ends[g]]), {"coverage": float(cum_n[g] / len(y)), "risk": float(cum_f[g] / cum_n[g]), "ub": float(ub[g])}


# ---------------- probabilistic metrics ----------------
def brier(p, y): return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def logloss_each(p, y, eps=1e-6):
    p = np.clip(np.asarray(p, float), eps, 1 - eps); y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def logloss(p, y): return float(np.mean(logloss_each(p, y)))


def _logit(p, eps=1e-6):
    p = np.clip(np.asarray(p, float), eps, 1 - eps); return np.log(p / (1 - p))


def calibration_slope_intercept(p, y):
    """slope: logistic regression of y on logit(p); intercept: calibration-in-the-large with slope fixed to 1 (offset-only fit).
    Undefined (nan) if y is constant."""
    y = np.asarray(y, float); z = _logit(p)
    if y.min() == y.max() or len(y) < 5: return float("nan"), float("nan")
    nll = lambda b, X: np.sum(np.logaddexp(0, X @ b) - y * (X @ b)) + 1e-8 * np.sum(b ** 2)
    X = np.c_[np.ones_like(z), z]
    slope = optimize.minimize(nll, [0.0, 1.0], args=(X,), method="BFGS").x[1]
    off = optimize.minimize_scalar(lambda a: np.sum(np.logaddexp(0, z + a) - y * (z + a)))
    return float(off.x), float(slope)


def reliability_bins(p, y, nbins=10, quantile=False):
    p = np.asarray(p, float); y = np.asarray(y, float)
    edges = np.quantile(p, np.linspace(0, 1, nbins + 1)) if quantile else np.linspace(0, 1, nbins + 1)
    b = np.clip(np.searchsorted(edges[1:-1], p, side="right"), 0, nbins - 1)
    return [{"bin": i, "n": int((b == i).sum()), "mean_pred": float(p[b == i].mean()), "obs_rate": float(y[b == i].mean())}
            for i in range(nbins) if (b == i).any()]


def ece(p, y, nbins=10, quantile=False):
    bins = reliability_bins(p, y, nbins, quantile); n = len(p)
    return float(sum(b["n"] / n * abs(b["mean_pred"] - b["obs_rate"]) for b in bins))


def ece_sensitivity(p, y):
    """ECE under several binnings; must be reported as a range and never alone (it is binning-dependent)."""
    return {f"{'q' if q else 'u'}{k}": ece(p, y, k, q) for k in (5, 10, 15) for q in (False, True)}


# ---------------- multiplicity ----------------
def holm(pvals):
    p = np.asarray(pvals, float); m = len(p); o = np.argsort(p); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1.0, run)
    return adj


def boot_p_one_sided(diff_reps):
    """H1: diff > 0 (baseline risk minus system risk). p = (1+#{diff<=0})/(B+1) over valid replicates."""
    d = np.asarray(diff_reps, float); d = d[~np.isnan(d)]
    return float((1 + (d <= 0).sum()) / (len(d) + 1)) if len(d) else float("nan")


def paired_matched(score_a, elig_a, score_b, elig_b, y, proj, cstar, B=B_DEFAULT, seed=0, jackknife=True):
    """Risk(B) - Risk(A) at the same coverage cstar (positive = A safer), paired project-cluster bootstrap. Returns dict."""
    y = np.asarray(y, float); W = cluster_counts(proj, B, seed)
    ra = matched_risk(score_a, elig_a, y, cstar, W); rb = matched_risk(score_b, elig_b, y, cstar, W)
    pa = matched_risk(score_a, elig_a, y, cstar); pb = matched_risk(score_b, elig_b, y, cstar)
    d = rb - ra; pt = pb - pa
    jack = []
    if jackknife and not np.isnan(pt):
        u, idx = _codes(proj)
        for k in range(len(u)):
            m = idx != k
            jack.append(matched_risk(np.asarray(score_b)[m], np.asarray(elig_b)[m], y[m], cstar) -
                        matched_risk(np.asarray(score_a)[m], np.asarray(elig_a)[m], y[m], cstar))
    lo, hi = pct_ci(d)
    lo1 = float(np.nanquantile(d, 0.025)) if np.isfinite(d).any() else float("nan")  # one-sided 97.5% lower bound
    return {"cstar": cstar, "risk_a": pa, "risk_b": pb, "diff_b_minus_a": pt, "ci95_pct": [lo, hi],
            "ci95_bca": list(bca_ci(pt, d, jack)) if jack else None, "lower97.5_one_sided": lo1,
            "p_one_sided": boot_p_one_sided(d), "n_valid_boot": int((~np.isnan(d)).sum())}


def boot_metric(fn, y, p, proj, B=2000, seed=0):
    """Percentile CI of a metric fn(y, p) under project-cluster resampling (rows replicated by multiplicity)."""
    u, idx = _codes(proj); y = np.asarray(y); p = np.asarray(p)
    members = [np.flatnonzero(idx == k) for k in range(len(u))]
    cnt = rng_for(seed, "metric").multinomial(len(u), np.full(len(u), 1 / len(u)), size=B)
    reps = []
    for c in cnt:
        ii = np.concatenate([np.repeat(members[k], c[k]) for k in np.flatnonzero(c)])
        v = fn(y[ii], p[ii]); reps.append(v if np.isscalar(v) else v[0])
    return pct_ci(reps)


# ---------------- folds ----------------
def project_folds(proj, k, seed=0):
    """Deterministic project-grouped fold id per pair; a project is in exactly one fold. Greedy size balancing after seeded shuffle."""
    u, idx = _codes(proj); k = min(k, len(u))
    order = rng_for(seed, "folds").permutation(len(u))
    sizes = np.bincount(idx, minlength=len(u)); load = np.zeros(k); fold_of = np.zeros(len(u), int)
    for j in sorted(order, key=lambda j: -sizes[j]):
        f = int(np.argmin(load)); fold_of[j] = f; load[f] += sizes[j]
    return fold_of[idx]


# ---------------- redundancy ----------------
def redundancy_table(X, names, thresh=0.8):
    """Spearman correlation matrix, VIF per feature, and the list of |rho|>=thresh pairs."""
    X = np.asarray(X, float)
    R = np.array(sps.spearmanr(X).correlation).reshape(len(names), len(names)) if X.shape[1] > 1 else np.ones((1, 1))
    R = np.nan_to_num(R, nan=0.0); np.fill_diagonal(R, 1.0)
    vif = np.diag(np.linalg.pinv(R))
    pairs = [(names[i], names[j], float(R[i, j])) for i in range(len(names)) for j in range(i + 1, len(names)) if abs(R[i, j]) >= thresh]
    return {"names": list(names), "spearman": R.tolist(), "vif": {n: float(v) for n, v in zip(names, vif)}, "redundant_pairs": pairs}


# ---------------- power / precision ----------------
def power_report(proj, y, ndo, target_delta=0.05):
    """Precision from the ACTUAL cluster structure of issued-NDO pairs. Status downgrades to pilot/exploratory when
    issued NDO < 100 or projects < 60. ICC by one-way ANOVA estimator on the error indicator; DEFF = 1+(m-1)*icc (floored at 1)."""
    y = np.asarray(y, float); ndo = np.asarray(ndo, bool)
    pr = np.asarray(proj).astype(str)[ndo]; yy = y[ndo]; n = len(yy)
    allp = len(set(np.asarray(proj).astype(str)))
    rep = {"n_pairs": int(len(y)), "n_projects_total": allp, "n_issued_ndo": int(n), "n_projects_with_ndo": len(set(pr))}
    if n < 2:
        rep.update(status="pilot/exploratory", note="fewer than 2 issued NDO verdicts")
        return rep
    u, idx = np.unique(pr, return_inverse=True); sz = np.bincount(idx); K = len(u)
    p = yy.mean(); gm = np.bincount(idx, weights=yy) / sz
    msb = np.sum(sz * (gm - p) ** 2) / max(K - 1, 1); msw = np.sum((yy - gm[idx]) ** 2) / max(n - K, 1)
    m0 = (n - np.sum(sz ** 2) / n) / max(K - 1, 1)
    icc = float(np.clip((msb - msw) / (msb + (m0 - 1) * msw), 0, 1)) if (msb + (m0 - 1) * msw) > 0 else 0.0
    mbar = n / K; deff = max(1.0, 1 + (mbar - 1) * icc); neff = n / deff
    hw = 1.96 * math.sqrt(max(p * (1 - p), 1e-12) / neff)
    q = 0.15  # assumed discordant share (design doc 06: 10-20%)
    mde = next((d for d in np.arange(0.01, 0.5, 0.005) if d * d < q and
                ((1.96 * math.sqrt(q) + 0.8416 * math.sqrt(q - d * d)) / d) ** 2 * deff <= n), float("nan"))
    small = n < 100 or allp < 60
    rep.update(cluster_size_mean=float(mbar), cluster_size_max=int(sz.max()), icc=icc, design_effect=float(deff), effective_n=float(neff),
               risk_point=float(p), ci_halfwidth_normal=float(hw), approx_mde_paired_pp=float(mde * 100) if mde == mde else None,
               mde_assumptions="McNemar normal approx, discordant share 0.15, 80% power, alpha .05, cluster-inflated; crude",
               status="pilot/exploratory" if small else "adequately-sized-by-count",
               note=("issued NDO < 100 or projects < 60: results are pilot/exploratory; non-significance must not be read as no effect"
                     if small else "count thresholds met; precision still given by the interval, not by this label"))
    return rep

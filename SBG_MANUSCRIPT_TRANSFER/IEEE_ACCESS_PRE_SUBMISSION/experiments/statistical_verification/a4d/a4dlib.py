"""A4D independent statistical-verification library (pure stdlib).

Written from scratch for agent A4D.  It does NOT import A4/A4C code, sbg/statistics.py or eval_lib (eval_lib is only imported by
`crosscheck_evallib.py` as a secondary cross-check).

Design: every pairwise-concordance statistic (AUROC, stratified AUROC, tercile AUROC) is expressed through the *cluster-pair
matrices*  U[a][b] = sum_{i in CHANGED(a), j in EQUIV(b)} psi(s_i, s_j)  (psi = 1 / 0.5 / 0 for >, =, <)  and
D[a][b] = number of admissible (i, j).  For a cluster-bootstrap resample with multiplicities m_a:
AUROC* = sum m_a m_b U_ab / sum m_a m_b D_ab (exactly the tie-aware Mann-Whitney AUROC of the resampled rows).
This makes paired cluster bootstraps (same resamples for all methods) cheap and exact.
"""
from __future__ import annotations

import ast
import bisect
import collections
import difflib
import json
import math
import pathlib
import random
from statistics import NormalDist

PKG = pathlib.Path(__file__).resolve().parents[3]
REPO = PKG.parent / "SBG"
POP_DIR = PKG / "configs" / "populations"
B_DEFAULT, SEED_DEFAULT = 2000, 42
_N = NormalDist()


# ----------------------------------------------------------------------------------------------- basic metrics
def midranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def auroc(s, y):
    """Tie-aware AUROC = P(s_pos > s_neg) + 0.5 P(tie), via Mann-Whitney midranks."""
    P = sum(y)
    N = len(y) - P
    if P == 0 or N == 0:
        return float("nan")
    r = midranks(s)
    return (sum(r[i] for i in range(len(y)) if y[i] == 1) - P * (P + 1) / 2.0) / (P * N)


def auroc_bruteforce(s, y):
    pos = [a for a, b in zip(s, y) if b == 1]
    neg = [a for a, b in zip(s, y) if b == 0]
    t = 0.0
    for a in pos:
        for b in neg:
            t += 1.0 if a > b else 0.5 if a == b else 0.0
    return t / (len(pos) * len(neg))


def cliffs_delta(s, y):
    """Cliff's delta = P(pos > neg) - P(pos < neg), computed directly (equals 2*AUROC-1)."""
    pos = [a for a, b in zip(s, y) if b == 1]
    neg = sorted(a for a, b in zip(s, y) if b == 0)
    gt = lt = 0
    for a in pos:
        lo, hi = bisect.bisect_left(neg, a), bisect.bisect_right(neg, a)
        gt += lo
        lt += len(neg) - hi
    return (gt - lt) / (len(pos) * len(neg))


def auprc(s, y):
    """Average precision with tie groups entering together: sum_k (R_k - R_{k-1}) P_k over distinct thresholds."""
    P = sum(y)
    if P == 0:
        return float("nan")
    d = collections.defaultdict(lambda: [0, 0])
    for a, b in zip(s, y):
        d[a][b] += 1
    tp = fp = 0
    prev_r = 0.0
    ap = 0.0
    for t in sorted(d, reverse=True):
        fp += d[t][0]
        tp += d[t][1]
        rec = tp / P
        ap += (rec - prev_r) * (tp / (tp + fp))
        prev_r = rec
    return ap


def youden(s, y):
    """Threshold maximising J = TPR - FPR over distinct scores; predicts CHANGED iff score >= thr; ties in J -> smallest thr."""
    P = sum(y)
    N = len(y) - P
    d = collections.defaultdict(lambda: [0, 0])
    for a, b in zip(s, y):
        d[a][b] += 1
    tp, fp = P, N  # threshold below everything: all predicted CHANGED
    best, thr = None, None
    for t in sorted(d):
        # predict CHANGED iff score >= t  -> counts of scores >= t
        j = tp / P - fp / N
        if best is None or j > best + 1e-12:
            best, thr = j, t
        fp -= d[t][0]
        tp -= d[t][1]
    return thr, best


def prf(s, y, thr):
    tp = sum(1 for a, b in zip(s, y) if a >= thr and b == 1)
    fp = sum(1 for a, b in zip(s, y) if a >= thr and b == 0)
    fn = sum(1 for a, b in zip(s, y) if a < thr and b == 1)
    tn = sum(1 for a, b in zip(s, y) if a < thr and b == 0)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0, "fpr": fp / (fp + tn) if fp + tn else 0.0,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


# ----------------------------------------------------------------------------------------------- distributions
def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c
        c = c if abs(c) > 1e-300 else 1e-300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c
        c = c if abs(c) > 1e-300 else 1e-300
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    p = 0.5 * betai(df / 2.0, 0.5, x)
    return 1.0 - p if t > 0 else p


def t_ppf(q, df):
    lo, hi = -200.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def t_two_sided_p(t, df):
    return min(1.0, 2 * (1 - t_cdf(abs(t), df)))


def norm_two_sided_p(z):
    return min(1.0, 2 * (1 - _N.cdf(abs(z))))


# ----------------------------------------------------------------------------------------------- data container
class Data:
    """One evaluation set: label vector, cluster (program) id, optional group (matched set), edit size."""

    def __init__(self, y, cluster, group=None, edit=None, ids=None):
        self.n = len(y)
        self.y = list(y)
        self.cluster = list(cluster)
        self.group = list(group) if group is not None else None
        self.edit = list(edit) if edit is not None else None
        self.ids = list(ids) if ids is not None else list(range(self.n))
        self.keys = sorted(set(cluster))
        self.K = len(self.keys)
        kix = {k: i for i, k in enumerate(self.keys)}
        self.cid = [kix[c] for c in cluster]
        self.members = [[] for _ in self.keys]
        for i, c in enumerate(self.cid):
            self.members[c].append(i)
        self.npos = [sum(self.y[i] for i in m) for m in self.members]
        self.nneg = [len(m) - p for m, p in zip(self.members, self.npos)]

    def subset(self, idx):
        idx = list(idx)
        return Data([self.y[i] for i in idx], [self.cluster[i] for i in idx],
                    [self.group[i] for i in idx] if self.group else None,
                    [self.edit[i] for i in idx] if self.edit else None, [self.ids[i] for i in idx])


def pair_matrices(data, s, strata=None, only=None):
    """U, D cluster-pair matrices for score vector s.  strata: optional per-row stratum key; only same-stratum (pos,neg) pairs count;
    only: if given, restrict to pairs inside that single stratum value."""
    K = data.K
    st = strata if strata is not None else [0] * data.n
    negs = {}
    for i in range(data.n):
        if data.y[i] == 0 and (only is None or st[i] == only):
            negs.setdefault((data.cid[i], st[i]), []).append(s[i])
    for v in negs.values():
        v.sort()
    stratset = sorted(set(st))
    U = [[0.0] * K for _ in range(K)]
    D = [[0.0] * K for _ in range(K)]
    for i in range(data.n):
        if data.y[i] != 1 or (only is not None and st[i] != only):
            continue
        a, t = data.cid[i], st[i]
        for b in range(K):
            v = negs.get((b, t))
            if not v:
                continue
            lo = bisect.bisect_left(v, s[i])
            hi = bisect.bisect_right(v, s[i])
            U[a][b] += lo + 0.5 * (hi - lo)
            D[a][b] += len(v)
    return U, D


def auroc_from_matrices(U, D, m=None):
    K = len(U)
    if m is None:
        m = [1] * K
    nz = [a for a in range(K) if m[a]]
    num = den = 0.0
    for a in nz:
        ma, Ua, Da = m[a], U[a], D[a]
        for b in nz:
            w = ma * m[b]
            num += w * Ua[b]
            den += w * Da[b]
    return num / den if den > 0 else None


class Resamples:
    """Cluster-bootstrap multiplicities. Draw order: for _ in range(K): rng.randrange(K) (keys sorted) - documented protocol."""

    def __init__(self, K, B=B_DEFAULT, seed=SEED_DEFAULT):
        rng = random.Random(seed)
        self.B, self.seed, self.K = B, seed, K
        self.counts = []
        for _ in range(B):
            m = [0] * K
            for _ in range(K):
                m[rng.randrange(K)] += 1
            self.counts.append(m)


def boot_vec(U, D, res):
    return [auroc_from_matrices(U, D, m) for m in res.counts]


def pct_ci(vals, mode="repo"):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    if n == 0:
        return [None, None]
    if mode == "repo":
        return [v[int(0.025 * n)], v[min(n - 1, int(math.ceil(0.975 * n)) - 1)]]

    def q(p):
        h = (n - 1) * p
        lo = int(math.floor(h))
        return v[lo] + (h - lo) * (v[min(lo + 1, n - 1)] - v[lo])
    return [q(0.025), q(0.975)]


def sd(vals):
    v = [x for x in vals if x is not None]
    mu = sum(v) / len(v)
    return math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1))


def delta_boot(pt_a, pt_b, va, vb):
    """Paired cluster-bootstrap summary for A-B (same resamples)."""
    d = [x - z for x, z in zip(va, vb) if x is not None and z is not None]
    n = len(d)
    k_le = sum(1 for x in d if x <= 0)
    k_ge = sum(1 for x in d if x >= 0)
    kmin = min(k_le, k_ge)
    return {"delta": pt_a - pt_b, "ci95": pct_ci(d), "ci95_interp": pct_ci(d, "interp"), "boot_sd": sd(d), "n_valid": n,
            "p_boot_plain": min(1.0, max(2 * kmin / n, 1.0 / n)), "p_boot_corrected": min(1.0, 2 * (kmin + 1) / (n + 1))}


def jackknife_delta(data, Ua, Da, Ub, Db):
    """Leave-one-cluster-out jackknife of dAUROC: SE, t-CI (df=K-1), p."""
    K = data.K
    theta = auroc_from_matrices(Ua, Da) - auroc_from_matrices(Ub, Db)
    loo = []
    for k in range(K):
        m = [1] * K
        m[k] = 0
        a, b = auroc_from_matrices(Ua, Da, m), auroc_from_matrices(Ub, Db, m)
        loo.append(None if a is None or b is None else a - b)
    v = [x for x in loo if x is not None]
    kk = len(v)
    mu = sum(v) / kk
    se = math.sqrt((kk - 1) / kk * sum((x - mu) ** 2 for x in v))
    tc = t_ppf(0.975, kk - 1)
    ps = [kk * theta - (kk - 1) * x for x in v]  # pseudo-values
    pm = sum(ps) / kk
    se_ps = math.sqrt(sum((x - pm) ** 2 for x in ps) / (kk - 1) / kk)
    return {"theta": theta, "loo": loo, "se_jack": se_ps if se_ps > 0 else se,
            "ci95_t": [pm - tc * se_ps, pm + tc * se_ps], "p_t": t_two_sided_p(pm / se_ps, kk - 1) if se_ps > 0 else 1.0,
            "pseudo_mean": pm}


# ----------------------------------------------------------------------------------------------- permutation tests
def perm_label_auroc_p(data, s, B=B_DEFAULT, seed=SEED_DEFAULT):
    """One-sided H1: AUROC > 0.5, labels permuted within program; p = (k+1)/(B+1)."""
    obs = auroc(s, data.y)
    rng = random.Random(seed)
    k = 0
    for _ in range(B):
        yy = list(data.y)
        for mem in data.members:
            lab = [data.y[i] for i in mem]
            rng.shuffle(lab)
            for i, v in zip(mem, lab):
                yy[i] = v
        if auroc(s, yy) >= obs - 1e-12:
            k += 1
    return (k + 1) / (B + 1)


def perm_label_delta_p(data, sa, sb, B=B_DEFAULT, seed=SEED_DEFAULT):
    """Two-sided; null = labels exchangeable within program (both predictors signal-free). |dAUROC_perm| >= |obs|."""
    obs = abs(auroc(sa, data.y) - auroc(sb, data.y))
    rng = random.Random(seed)
    k = 0
    for _ in range(B):
        yy = list(data.y)
        for mem in data.members:
            lab = [data.y[i] for i in mem]
            rng.shuffle(lab)
            for i, v in zip(mem, lab):
                yy[i] = v
        if abs(auroc(sa, yy) - auroc(sb, yy)) >= obs - 1e-12:
            k += 1
    return (k + 1) / (B + 1)


def per_program_auroc(data, s):
    out = {}
    for ki, key in enumerate(data.keys):
        idx = data.members[ki]
        out[key] = auroc([s[i] for i in idx], [data.y[i] for i in idx]) if data.npos[ki] and data.nneg[ki] else None
    return out


def program_weights(data):
    return {key: data.npos[ki] * data.nneg[ki] for ki, key in enumerate(data.keys)}


def signflip_weighted_p(d, w, B=20000, seed=SEED_DEFAULT, exact_max=14):
    """Sign-flip permutation test of the weighted mean of per-program differences d_p (H0: symmetric about 0)."""
    items = [(x, wi) for x, wi in zip(d, w) if x is not None and abs(x) > 1e-15]
    if not items:
        return 1.0
    obs = abs(sum(x * wi for x, wi in items))
    K = len(items)
    if K <= exact_max:
        k = 0
        for mask in range(1 << K):
            t = sum((x if (mask >> i) & 1 else -x) * wi for i, (x, wi) in enumerate(items))
            if abs(t) >= obs - 1e-12:
                k += 1
        return k / (1 << K)
    rng = random.Random(seed)
    k = 0
    for _ in range(B):
        t = sum((x if rng.random() < 0.5 else -x) * wi for x, wi in items)
        if abs(t) >= obs - 1e-12:
            k += 1
    return (k + 1) / (B + 1)


def sign_test_p(d, tol=1e-12):
    pos = sum(1 for x in d if x is not None and x > tol)
    neg = sum(1 for x in d if x is not None and x < -tol)
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    k = min(pos, neg)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p), pos, neg


def wilcoxon_exact_p(d, tol=1e-12):
    """Two-sided exact Wilcoxon signed-rank (zeros dropped, midranks for tied |d|; exact DP on doubled ranks)."""
    v = [x for x in d if x is not None and abs(x) > tol]
    n = len(v)
    if n == 0:
        return 1.0, 0.0
    ab = [abs(x) for x in v]
    # group ties on rounded magnitude
    order = sorted(range(n), key=lambda i: ab[i])
    rk = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(ab[order[j + 1]] - ab[order[i]]) < tol:
            j += 1
        for k in range(i, j + 1):
            rk[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    r2 = [int(round(2 * x)) for x in rk]
    total = sum(r2)
    dist = {0: 1}
    for r in r2:
        nd = dict(dist)
        for s_, c in dist.items():
            nd[s_ + r] = nd.get(s_ + r, 0) + c
        dist = nd
    wplus2 = sum(r2[i] for i in range(n) if v[i] > 0)
    tot = 2 ** n
    lo = sum(c for s_, c in dist.items() if s_ <= min(wplus2, total - wplus2))
    p = min(1.0, 2 * lo / tot)
    return p, wplus2 / 2.0


# ----------------------------------------------------------------------------------------------- multiple testing
def holm(pvals, m=None):
    """Holm step-down over dict name->p; m = declared family size (>= len(pvals); missing members are treated as p = 1)."""
    names = sorted(pvals, key=lambda k: (pvals[k], k))
    m = m or len(names)
    out, run = {}, 0.0
    for i, k in enumerate(names):
        run = max(run, min(1.0, (m - i) * pvals[k]))
        out[k] = run
    return out


def benjamini_hochberg(pvals, m=None):
    names = sorted(pvals, key=lambda k: (pvals[k], k))
    m = m or len(names)
    adj = {}
    prev = 1.0
    for i in range(len(names) - 1, -1, -1):
        k = names[i]
        prev = min(prev, pvals[k] * m / (i + 1))
        adj[k] = min(1.0, prev)
    return adj


# ----------------------------------------------------------------------------------------------- DeLong
def delong_components(s, y):
    pos_idx = [i for i in range(len(y)) if y[i] == 1]
    neg_idx = [i for i in range(len(y)) if y[i] == 0]
    X = [s[i] for i in pos_idx]
    Y = [s[i] for i in neg_idx]
    Ys, Xs = sorted(Y), sorted(X)
    n, m = len(Y), len(X)
    v10 = []
    for x in X:
        lo, hi = bisect.bisect_left(Ys, x), bisect.bisect_right(Ys, x)
        v10.append((lo + 0.5 * (hi - lo)) / n)
    v01 = []
    for yv in Y:
        lo, hi = bisect.bisect_left(Xs, yv), bisect.bisect_right(Xs, yv)
        v01.append(1.0 - (lo + 0.5 * (hi - lo)) / m)
    return v10, v01


def delong_test(sa, sb, y):
    """Pair-level (iid) DeLong test for correlated AUROCs. Returns delta, se, z, p, ci."""
    a10, a01 = delong_components(sa, y)
    b10, b01 = delong_components(sb, y)
    m, n = len(a10), len(a01)
    auc_a = sum(a10) / m
    auc_b = sum(b10) / m

    def cov(u, v):
        mu, mv = sum(u) / len(u), sum(v) / len(v)
        return sum((x - mu) * (z - mv) for x, z in zip(u, v)) / (len(u) - 1)
    var = lambda u1, u2, w1, w2: cov(u1, u2) / m + cov(w1, w2) / n  # noqa: E731
    vaa, vbb, vab = var(a10, a10, a01, a01), var(b10, b10, b01, b01), var(a10, b10, a01, b01)
    vd = vaa + vbb - 2 * vab
    d = auc_a - auc_b
    if vd <= 0:
        return {"delta": d, "se": 0.0, "z": None, "p": 0.0 if abs(d) > 1e-12 else 1.0, "ci95": [d, d], "auc_a": auc_a, "auc_b": auc_b,
                "se_a": math.sqrt(vaa), "se_b": math.sqrt(vbb)}
    se = math.sqrt(vd)
    z = d / se
    return {"delta": d, "se": se, "z": z, "p": norm_two_sided_p(z), "ci95": [d - 1.959964 * se, d + 1.959964 * se],
            "auc_a": auc_a, "auc_b": auc_b, "se_a": math.sqrt(vaa), "se_b": math.sqrt(vbb)}


# ----------------------------------------------------------------------------------------------- matched sets
def matched_sets(data, s):
    """[(program_index, concordance in {0,.5,1})] for each matched set group having exactly one CHANGED and one EQUIV member."""
    g = collections.defaultdict(dict)
    for i in range(data.n):
        g[data.group[i]].setdefault(data.y[i], []).append(i)
    out = []
    for key in sorted(g):
        v = g[key]
        if 0 in v and 1 in v and len(v[0]) == 1 and len(v[1]) == 1:
            a, b = s[v[1][0]], s[v[0][0]]
            out.append((data.cid[v[1][0]], 1.0 if a > b else 0.5 if a == b else 0.0, key))
    return out


def concordance_boot(sets_a, sets_b, K, res):
    """Set concordance (and paired difference if sets_b given) with program-cluster bootstrap on the same multiplicities."""
    by_a = [[] for _ in range(K)]
    for (p, c, _), (p2, c2, _) in zip(sets_a, sets_b if sets_b else sets_a):
        by_a[p].append((c, c2))
    sa = [sum(x for x, _ in v) for v in by_a]
    sb = [sum(z for _, z in v) for v in by_a]
    cnt = [len(v) for v in by_a]
    obs_a, obs_b = sum(sa) / sum(cnt), sum(sb) / sum(cnt)
    va, vb = [], []
    for m in res.counts:
        n_ = sum(m[k] * cnt[k] for k in range(K))
        if n_ == 0:
            continue
        va.append(sum(m[k] * sa[k] for k in range(K)) / n_)
        vb.append(sum(m[k] * sb[k] for k in range(K)) / n_)
    out = {"conc": obs_a, "ci95": pct_ci(va), "n_sets": sum(cnt)}
    if sets_b:
        d = [x - z for x, z in zip(va, vb)]
        kmin = min(sum(1 for x in d if x <= 0), sum(1 for x in d if x >= 0))
        out.update({"conc_b": obs_b, "delta": obs_a - obs_b, "delta_ci95": pct_ci(d), "p_boot_plain": min(1.0, max(2 * kmin / len(d), 1.0 / len(d)))})
    return out


# ----------------------------------------------------------------------------------------------- dependence
def icc1(values, clusters):
    """One-way ANOVA ICC(1) with unbalanced-cluster n0; returns (icc, n0, k, MSB, MSW)."""
    g = collections.defaultdict(list)
    for v, c in zip(values, clusters):
        g[c].append(v)
    k = len(g)
    N = len(values)
    grand = sum(values) / N
    ssb = sum(len(v) * (sum(v) / len(v) - grand) ** 2 for v in g.values())
    ssw = sum(sum((x - sum(v) / len(v)) ** 2 for x in v) for v in g.values())
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n0 = (N - sum(len(v) ** 2 for v in g.values()) / N) / (k - 1)
    den = msb + (n0 - 1) * msw
    return ((msb - msw) / den if den > 0 else 0.0), n0, k, msb, msw


def placements(s, y):
    """Per-observation DeLong placement values (aligned with row order): pos -> V10, neg -> V01."""
    v10, v01 = delong_components(s, y)
    out = [0.0] * len(y)
    ip = iter(v10)
    ineg = iter(v01)
    for i in range(len(y)):
        out[i] = next(ip) if y[i] == 1 else next(ineg)
    return out


def iid_row_bootstrap_vec(data, s, B=B_DEFAULT, seed=SEED_DEFAULT):
    """Row-level (iid) bootstrap AUROC vector, for design-effect comparison (not a valid CI)."""
    rng = random.Random(seed)
    n = data.n
    out = []
    for _ in range(B):
        idx = [rng.randrange(n) for _ in range(n)]
        yy = [data.y[i] for i in idx]
        if 0 < sum(yy) < n:
            out.append(auroc([s[i] for i in idx], yy))
    return out


# ----------------------------------------------------------------------------------------------- power
def mde(se, df, alpha=0.05, power=0.80):
    z = _N.inv_cdf(1 - alpha / 2) + _N.inv_cdf(power)
    t = t_ppf(1 - alpha / 2, df) + t_ppf(power, df)
    return {"mde_normal": z * se, "mde_t": t * se}


def power_at(delta, se, df, alpha=0.05):
    """Approximate power (central-t distribution shifted by delta/se; exact alpha at delta=0) of a two-sided test for a true difference `delta`."""
    if se <= 0:
        return 1.0
    tc = t_ppf(1 - alpha / 2, df)
    sh = abs(delta) / se
    return 1 - t_cdf(tc - sh, df) + t_cdf(-tc - sh, df)


# ----------------------------------------------------------------------------------------------- logistic regression
def _standardise(X):
    n, d = len(X), len(X[0])
    mu = [sum(r[j] for r in X) / n for j in range(d)]
    sdv = [math.sqrt(sum((r[j] - mu[j]) ** 2 for r in X) / n) or 1.0 for j in range(d)]
    return mu, sdv, [[(r[j] - mu[j]) / sdv[j] for j in range(d)] for r in X]


def _solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


def fit_logistic_newton(X, y, l2=1.0, iters=60):
    """Exact optimum of mean-NLL + l2/(2n)|w|^2 on standardised features (bias unpenalised); own Newton/IRLS."""
    n, d = len(X), len(X[0])
    mu, sdv, Z = _standardise(X)
    w = [0.0] * (d + 1)  # w[0] bias
    for _ in range(iters):
        g = [0.0] * (d + 1)
        H = [[0.0] * (d + 1) for _ in range(d + 1)]
        for z, t in zip(Z, y):
            zz = [1.0] + z
            u = sum(a * b for a, b in zip(w, zz))
            p = 1 / (1 + math.exp(-max(-35.0, min(35.0, u))))
            wt = p * (1 - p)
            for i in range(d + 1):
                g[i] += (p - t) * zz[i]
                for j in range(i, d + 1):
                    H[i][j] += wt * zz[i] * zz[j]
        for i in range(d + 1):
            for j in range(i):
                H[i][j] = H[j][i]
        for i in range(1, d + 1):
            g[i] += l2 * w[i]
            H[i][i] += l2
        step = _solve(H, g)
        w = [a - b for a, b in zip(w, step)]
        if max(abs(x) for x in step) < 1e-11:
            break
    return {"b": w[0], "w": w[1:], "mu": mu, "sd": sdv}


def fit_logistic_gd(X, y, l2=1.0, lr=0.5, iters=5000):
    """Full-batch gradient descent recipe documented in the plan (standardised, L2=1, lr=0.5, 5000 its); own implementation."""
    n, d = len(X), len(X[0])
    mu, sdv, Z = _standardise(X)
    w, b0 = [0.0] * d, 0.0
    for _ in range(iters):
        gw, gb = [0.0] * d, 0.0
        for z, t in zip(Z, y):
            u = b0 + sum(a * c for a, c in zip(w, z))
            p = 1 / (1 + math.exp(-max(-30.0, min(30.0, u))))
            e = p - t
            gb += e
            for j in range(d):
                gw[j] += e * z[j]
        w = [wj - lr * (gj / n + l2 * wj / n) for wj, gj in zip(w, gw)]
        b0 -= lr * gb / n
    return {"b": b0, "w": w, "mu": mu, "sd": sdv}


def logit_apply(m, x):
    return m["b"] + sum(w * (v - mu) / s for w, v, mu, s in zip(m["w"], x, m["mu"], m["sd"]))


# ----------------------------------------------------------------------------------------------- simple non-learned combiners
def fit_zsum(X, y):
    """z-score sum with train-orientation: component weight = sign(train AUROC-0.5) (declared; no fitted magnitudes)."""
    d = len(X[0])
    mu = [sum(r[j] for r in X) / len(X) for j in range(d)]
    sdv = [math.sqrt(sum((r[j] - mu[j]) ** 2 for r in X) / len(X)) or 1.0 for j in range(d)]
    sg = [1.0 if auroc([r[j] for r in X], y) >= 0.5 else -1.0 for j in range(d)]
    return {"mu": mu, "sd": sdv, "sign": sg}


def zsum_apply(m, x):
    return sum(sg * (v - mu) / s for sg, v, mu, s in zip(m["sign"], x, m["mu"], m["sd"]))


def fit_rankavg(X, y):
    """Rank-average: each component -> train-ECDF mid-percentile, oriented by sign of train AUROC-0.5; mean of percentiles."""
    d = len(X[0])
    cols = [sorted(r[j] for r in X) for j in range(d)]
    sg = [1.0 if auroc([r[j] for r in X], y) >= 0.5 else -1.0 for j in range(d)]
    return {"cols": cols, "sign": sg}


def rankavg_apply(m, x):
    t = 0.0
    for j, v in enumerate(x):
        c = m["cols"][j]
        lo, hi = bisect.bisect_left(c, v), bisect.bisect_right(c, v)
        pc = (lo + hi) / 2.0 / len(c)
        t += pc if m["sign"][j] > 0 else 1 - pc
    return t / len(x)


# ----------------------------------------------------------------------------------------------- populations / raw re-derivation
def load_pop(name, primary=True):
    d = json.loads((POP_DIR / f"{name}.json").read_text())
    rows = d["rows"]
    return [r for r in rows if r.get("in_primary_population")] if primary else rows


def data_from_rows(rows, ids_key="pair_id"):
    return Data([r["label"] for r in rows], [r["base_id"] for r in rows], [r["group"] for r in rows], [r["edit"] for r in rows],
                [r[ids_key] for r in rows])


def _jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def raw_labels_groups(name):
    """Independent derivation (from raw dataset metadata) of {pair_id: (label, group, base_id, base_path, variant_path)}."""
    ds = REPO / "benchmark" / "datasets"
    out = {}
    if name == "v10_test":
        for m in _jl(ds / "v10_independent" / "pairs_test.jsonl"):
            lab = 1 if m["semantic_relation"] == "CHANGED" else 0
            grp = m["matched_pair_id"] if lab else m["pair_id"]
            out[m["pair_id"]] = (lab, grp, m["base_id"], m["base_path"], m["variant_path"])
    else:
        split = name.split("_")[1]
        v9 = {m["pair_id"]: m for m in _jl(ds / "v9_composed" / f"pairs_{split}.jsonl")}
        v8 = {m["pair_id"]: m for m in _jl(ds / "v8" / f"pairs_{split}.jsonl")}
        for pid, m in v9.items():
            if m["semantic_relation"] == "CHANGED":
                out[pid] = (1, m["matched_equivalent_pair_id"], m["base_id"], m["base_path"], m["variant_path"])
                e = v8.get(m["matched_equivalent_pair_id"])
                if e is not None:
                    out[e["pair_id"]] = (0, e["pair_id"], e["base_id"], e["base_path"], e["variant_path"])
    return out


def edit_size(base_path, variant_path):
    """changed lines of canonical (ast.unparse) unified diff, n=0 -- re-implemented from the definition."""
    a = ast.unparse(ast.parse((REPO / base_path).read_text())).splitlines()
    b = ast.unparse(ast.parse((REPO / variant_path).read_text())).splitlines()
    return sum(1 for ln in difflib.unified_diff(a, b, lineterm="", n=0) if ln[:1] in "+-" and not ln.startswith(("+++", "---")))


def ast_hash(path):
    import hashlib
    return hashlib.sha1(ast.dump(ast.parse((REPO / path).read_text())).encode()).hexdigest()

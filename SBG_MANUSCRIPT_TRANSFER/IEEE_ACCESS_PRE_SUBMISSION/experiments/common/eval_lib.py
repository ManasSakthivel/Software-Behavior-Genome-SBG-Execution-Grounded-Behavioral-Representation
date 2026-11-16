"""Shared common-protocol evaluation library (pure standard library).

Written for this validation package.  It deliberately does NOT import sbg.statistics so that it can be used to
cross-check the repository's own statistics.  Used by competitor baselines (Agent 4) and ablations (Agent 5).

Protocol constants (PROTOCOL.md): B=2000 cluster-bootstrap resamples, seed 42, 95% percentile CI, cluster = base program,
tie-aware AUROC, tie-aware average precision (AUPRC), Youden-J thresholds chosen on TRAIN only, Holm over declared family.
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import random

PKG = pathlib.Path(__file__).resolve().parents[2]
POP_DIR = PKG / "configs" / "populations"
B, SEED = 2000, 42


# ------------------------------------------------------------------ populations
def load_population(name: str, primary_only: bool = True):
    """Rows of a frozen population (configs/populations/<name>.json); primary = matched-complete sets."""
    d = json.loads((POP_DIR / f"{name}.json").read_text())
    rows = d["rows"]
    return [r for r in rows if r.get("in_primary_population")] if primary_only else rows


# ------------------------------------------------------------------ metrics
def auroc(s, y):
    pos = [a for a, b in zip(s, y) if b == 1]
    neg = [a for a, b in zip(s, y) if b == 0]
    if not pos or not neg:
        return 0.5
    order = sorted(range(len(s)), key=lambda i: s[i])
    ranks = [0.0] * len(s)
    i = 0
    while i < len(order):
        j = i
        while j < len(order) and s[order[j]] == s[order[i]]:
            j += 1
        for k in range(i, j):
            ranks[order[k]] = (i + 1 + j) / 2.0
        i = j
    rp = sum(ranks[i] for i in range(len(s)) if y[i] == 1)
    return (rp - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def auprc(s, y):
    """Average precision; all items tied at one score enter together (tie-aware)."""
    P = sum(y)
    if P == 0:
        return float("nan")
    order = sorted(zip(s, y), key=lambda t: -t[0])
    tp = fp = 0
    ap = prev = 0.0
    i = 0
    while i < len(order):
        j = i
        while j < len(order) and order[j][0] == order[i][0]:
            j += 1
        for _, lab in order[i:j]:
            tp += lab
            fp += 1 - lab
        rec = tp / P
        ap += (rec - prev) * tp / (tp + fp)
        prev = rec
        i = j
    return ap


def prf(s, y, thr):
    """Precision / recall / F1 / FPR with rule: predict CHANGED iff score >= thr."""
    tp = sum(1 for a, b in zip(s, y) if a >= thr and b == 1)
    fp = sum(1 for a, b in zip(s, y) if a >= thr and b == 0)
    fn = sum(1 for a, b in zip(s, y) if a < thr and b == 1)
    tn = sum(1 for a, b in zip(s, y) if a < thr and b == 0)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "fpr": fp / (fp + tn) if fp + tn else 0.0, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def youden_threshold(s, y):
    """Threshold maximising TPR-FPR (ties -> smallest threshold); to be called on TRAIN scores only."""
    P, N = sum(y), len(y) - sum(y)
    best, thr = -2.0, None
    for t in sorted(set(s)):
        tpr = sum(1 for a, b in zip(s, y) if a >= t and b == 1) / P
        fpr = sum(1 for a, b in zip(s, y) if a >= t and b == 0) / N
        if tpr - fpr > best + 1e-12:
            best, thr = tpr - fpr, t
    return thr


# ------------------------------------------------------------------ cluster resampling statistics
def _clusters(c):
    d = collections.defaultdict(list)
    for i, k in enumerate(c):
        d[k].append(i)
    return d


def cluster_bootstrap_ci(s, y, c, b=B, seed=SEED, metric=auroc):
    d = _clusters(c)
    keys = sorted(d)
    rng = random.Random(seed)
    vals = []
    for _ in range(b):
        idx = [i for _ in keys for i in d[keys[rng.randrange(len(keys))]]]
        yy = [y[i] for i in idx]
        if 0 < sum(yy) < len(yy):
            vals.append(metric([s[i] for i in idx], yy))
    vals.sort()
    n = len(vals)
    return [vals[int(0.025 * n)], vals[min(n - 1, int(math.ceil(0.975 * n)) - 1)]]


def paired_delta(sa, sb, y, c, b=B, seed=SEED, metric=auroc):
    """AUROC(a)-AUROC(b) on identical rows; cluster bootstrap (same resamples for both); two-sided bootstrap p."""
    d = _clusters(c)
    keys = sorted(d)
    rng = random.Random(seed)
    obs = metric(sa, y) - metric(sb, y)
    ds = []
    for _ in range(b):
        idx = [i for _ in keys for i in d[keys[rng.randrange(len(keys))]]]
        yy = [y[i] for i in idx]
        if 0 < sum(yy) < len(yy):
            ds.append(metric([sa[i] for i in idx], yy) - metric([sb[i] for i in idx], yy))
    ds.sort()
    n = len(ds)
    p = 2 * min(sum(1 for v in ds if v <= 0), sum(1 for v in ds if v >= 0)) / n
    return {"delta": obs, "ci95": [ds[int(0.025 * n)], ds[min(n - 1, int(math.ceil(0.975 * n)) - 1)]], "p_two_sided": min(1.0, max(p, 1.0 / n)),
            "n_valid_resamples": n}


def cluster_permutation_p(s, y, c, b=B, seed=SEED):
    """One-sided H1: AUROC>0.5; labels permuted WITHIN program cluster; p=(k+1)/(B+1)."""
    d = _clusters(c)
    obs = auroc(s, y)
    rng = random.Random(seed)
    k = 0
    for _ in range(b):
        yy = list(y)
        for idx in d.values():
            lab = [y[i] for i in idx]
            rng.shuffle(lab)
            for i, v in zip(idx, lab):
                yy[i] = v
        if auroc(s, yy) >= obs - 1e-12:
            k += 1
    return (k + 1) / (b + 1)


def holm(pvals: dict):
    names = sorted(pvals, key=lambda k: pvals[k])
    m, out, run = len(names), {}, 0.0
    for i, k in enumerate(names):
        run = max(run, min(1.0, (m - i) * pvals[k]))
        out[k] = run
    return out


def matched_concordance(rows, key, b=B, seed=SEED):
    """P(score(CHANGED partner) > score(EQUIVALENT partner)) within matched sets; ties 0.5; cluster bootstrap."""
    g = collections.defaultdict(dict)
    for r in rows:
        g[r["group"]][r["label"]] = r
    sets = [(v[1]["base_id"], 1.0 if key(v[1]) > key(v[0]) else 0.5 if key(v[1]) == key(v[0]) else 0.0) for v in g.values() if 0 in v and 1 in v]
    by = collections.defaultdict(list)
    for p, v in sets:
        by[p].append(v)
    ks, rng, vals = sorted(by), random.Random(seed), []
    for _ in range(b):
        sm = [v for k in (rng.choice(ks) for _ in ks) for v in by[k]]
        vals.append(sum(sm) / len(sm))
    vals.sort()
    return {"concordance": sum(v for _, v in sets) / len(sets), "n_sets": len(sets), "ci95": [vals[int(0.025 * b)], vals[int(0.975 * b) - 1]]}


def stratified_auroc_exact_edit(rows, key):
    """AUROC restricted to cross-label pairs with EQUAL edit size (edit-size-matched concordance); returns (value, n_cross_pairs)."""
    g = collections.defaultdict(lambda: ([], []))
    for r in rows:
        g[r["edit"]][r["label"]].append(key(r))
    num = den = 0.0
    for neg, pos in g.values():
        for a in pos:
            for b_ in neg:
                num += 1.0 if a > b_ else 0.5 if a == b_ else 0.0
        den += len(pos) * len(neg)
    return (num / den if den else None), den


def edit_quantile_strata(rows, key, q=3):
    """AUROC inside edit-size quantile strata (q bins on the evaluated population)."""
    es = sorted(r["edit"] for r in rows)
    cuts = [es[int(len(es) * i / q)] for i in range(1, q)]
    out = []
    for lo, hi in zip([-1e18] + cuts, cuts + [1e18]):
        sub = [r for r in rows if lo <= r["edit"] < hi]
        yy = [r["label"] for r in sub]
        out.append({"edit_range": [lo if lo > -1e17 else None, hi if hi < 1e17 else None], "n": len(sub), "n_changed": sum(yy),
                    "auroc": auroc([key(r) for r in sub], yy) if 0 < sum(yy) < len(yy) else None})
    return out


# ------------------------------------------------------------------ small L2 logistic regression (for combiner baselines)
def fit_logistic(X, y, l2=1.0, lr=0.5, iters=5000):
    """Full-batch gradient descent on standardised features; mirrors the repo's combiner recipe but is re-implemented here."""
    n, d = len(X), len(X[0])
    mu = [sum(r[j] for r in X) / n for j in range(d)]
    sd = [math.sqrt(sum((r[j] - mu[j]) ** 2 for r in X) / n) or 1.0 for j in range(d)]
    Z = [[(r[j] - mu[j]) / sd[j] for j in range(d)] for r in X]
    w, b0 = [0.0] * d, 0.0
    for _ in range(iters):
        gw, gb = [0.0] * d, 0.0
        for z, t in zip(Z, y):
            u = b0 + sum(wj * zj for wj, zj in zip(w, z))
            p = 1 / (1 + math.exp(-max(-30, min(30, u))))
            for j in range(d):
                gw[j] += (p - t) * z[j]
            gb += p - t
        w = [wj - lr * (gj / n + l2 * wj / n) for wj, gj in zip(w, gw)]
        b0 -= lr * gb / n
    return {"w": w, "b": b0, "mu": mu, "sd": sd}


def logit_score(m, x):
    z = [(x[j] - m["mu"][j]) / m["sd"][j] for j in range(len(x))]
    return m["b"] + sum(w * v for w, v in zip(m["w"], z))


# ------------------------------------------------------------------ one-call summary
def summarise(rows, score_fn, train_thr=None, b=B):
    s = [score_fn(r) for r in rows]
    y = [r["label"] for r in rows]
    c = [r["base_id"] for r in rows]
    out = {"n": len(rows), "n_programs": len(set(c)), "auroc": auroc(s, y), "auroc_ci95": cluster_bootstrap_ci(s, y, c, b=b), "auprc": auprc(s, y),
           "prevalence": sum(y) / len(y)}
    if train_thr is not None:
        out["at_train_threshold"] = {"threshold": train_thr, **prf(s, y, train_thr)}
    return out

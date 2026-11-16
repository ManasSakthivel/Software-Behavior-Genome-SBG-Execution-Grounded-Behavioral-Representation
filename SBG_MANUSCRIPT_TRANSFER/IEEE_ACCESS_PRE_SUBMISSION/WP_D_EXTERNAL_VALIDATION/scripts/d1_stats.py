"""Pure-stdlib statistics used by the WP-D D1 scripts (own implementation; does not import SBG or PKG/eval_lib).

auroc            tie-aware Mann-Whitney AUROC (positive = label 1, higher score = more 'changed')
cluster_boot_ci  percentile cluster bootstrap (resample clusters with replacement), B=2000, seed 42
within_cluster_auroc  AUROC over cross-label pairs that share a cluster only
"""
import random
from collections import defaultdict


def auroc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    # rank-based, tie aware
    pairs = sorted(zip(scores, labels))
    ranks = {}
    i = 0
    n = len(pairs)
    sum_pos = 0.0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            if pairs[k][1] == 1:
                sum_pos += avg
        i = j + 1
    return (sum_pos - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def cluster_boot_ci(scores, labels, clusters, B=2000, seed=42):
    by = defaultdict(list)
    for s, y, c in zip(scores, labels, clusters):
        by[c].append((s, y))
    keys = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        samp = [x for k in (rng.choice(keys) for _ in keys) for x in by[k]]
        a = auroc([s for s, _ in samp], [y for _, y in samp])
        if a is not None:
            vals.append(a)
    vals.sort()
    if not vals:
        return None, None, 0
    lo = vals[int(0.025 * len(vals))]
    hi = vals[min(len(vals) - 1, int(0.975 * len(vals)) - 1)]
    return round(lo, 4), round(hi, 4), len(vals)


def within_cluster_auroc(scores, labels, clusters):
    """AUROC restricted to (pos, neg) pairs in the same cluster; ties count 0.5. Returns (auroc, n_comparisons)."""
    by = defaultdict(list)
    for s, y, c in zip(scores, labels, clusters):
        by[c].append((s, y))
    num = den = 0.0
    for items in by.values():
        pos = [s for s, y in items if y == 1]
        neg = [s for s, y in items if y == 0]
        for p in pos:
            for q in neg:
                den += 1
                num += 1.0 if p > q else (0.5 if p == q else 0.0)
    return (round(num / den, 4) if den else None), int(den)


def summarize(rows, key, label_key="label", cluster_key="cluster", B=2000):
    """rows: list of dicts. Returns dict with auroc, ci, n, n_pos, n_neg, n_clusters, within-cluster auroc."""
    rows = [r for r in rows if r.get(key) is not None]
    s = [r[key] for r in rows]
    y = [r[label_key] for r in rows]
    c = [r[cluster_key] for r in rows]
    a = auroc(s, y)
    if a is None:
        return {"n": len(rows), "auroc": None}
    lo, hi, neff = cluster_boot_ci(s, y, c, B=B)
    w, nw = within_cluster_auroc(s, y, c)
    return {"n": len(rows), "n_pos": sum(y), "n_neg": len(y) - sum(y), "n_clusters": len(set(c)),
            "auroc": round(a, 4), "ci95_cluster_bootstrap": [lo, hi], "boot_effective": neff,
            "within_cluster_auroc": w, "n_within_cluster_comparisons": nw,
            "n_exact_zero_score": sum(1 for v in s if v == 0)}

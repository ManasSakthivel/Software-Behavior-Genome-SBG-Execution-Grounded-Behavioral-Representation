"""
d4_lib.py -- WP-D / subagent D4 (independent statistical assessment).

Own pure-stdlib implementation. NOT imported from SBG/sbg or from
PKG/experiments/statistical_verification. Inputs are read-only.

Contents
  * data loading / unification of the three external pair files + v8 rescore
  * tie-aware AUROC (mid-rank), brute-force checker
  * cluster bootstrap (percentile / basic / BCa), paired delta bootstrap
  * within-cluster permutation test (Monte-Carlo, (b+1)/(m+1)), exact stratified test
  * Fisher exact test, Wilson interval
All randomness is seeded; PYTHONHASHSEED=0 should be set by callers.
"""
import hashlib
import itertools
import json
import math
import os
import random
from pathlib import Path
from statistics import NormalDist

ND = NormalDist()

HERE = Path(__file__).resolve().parent
WPD = HERE.parent                      # .../WP_D_EXTERNAL_VALIDATION
OUT = WPD / "raw" / "WPD-D4_stats"
SBG = Path(os.environ.get("SBG_ROOT", str(HERE.parents[2] / "SBG")))
FINAL = SBG / "artifacts" / "final"
PE = SBG / "artifacts" / "paper_evidence"
RAW = PE / "raw"

INPUT_FILES = {
    "bugsinpy_v7": FINAL / "pairs_bugsinpy_output_free_v7.jsonl",
    "bugsinpy_v6": FINAL / "pairs_bugsinpy_output_free_v6.jsonl",
    "quixbugs_canonical_v7": FINAL / "pairs_quixbugs_canonical_output_free_v7.jsonl",
    "quixbugs_declared_v7": FINAL / "pairs_quixbugs_declared_output_free_v7.jsonl",
    "external_rescore_v8_pairs": RAW / "external_rescore_v8_pairs.json",
    "bugsinpy_purge_rescore": RAW / "bugsinpy_purge_rescore.json",
    "EXTERNAL_RESCORE_V8": PE / "EXTERNAL_RESCORE_V8.json",
    "EXTERNAL_NEGATIVE_AUDIT": PE / "EXTERNAL_NEGATIVE_AUDIT.json",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_manifest():
    return {k: {"path": str(v.relative_to(SBG.parent)), "sha256": sha256(v)}
            for k, v in INPUT_FILES.items()}


def write_json(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    with open(p, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=str)
    return p


# ----------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------

def _jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def _norm(rec):
    return rec


def load_corpora():
    """Return dict corpus -> list of unified records.

    Unified record keys:
      pair_id, corpus, label, kind ('real' or 'SP-x'), bug (cluster 1), project (cluster 2
      or None), family (project::file::unit or base_id), ev7 (evaluated in committed v7 file),
      s7 (v7 scores dict or None), static (static scores, always present), ev8, s8 (v8 rescore
      scores dict or None; None if corpus has no rescore or pair absent),
      self_dist8 (v8 base self-distance), failure_kind/side/detail, base_path, variant_path
    """
    out = {}
    # ---- BugsInPy -----------------------------------------------------------
    rows = _jsonl(INPUT_FILES["bugsinpy_v7"])
    v8 = {r["pair_id"]: r for r in json.load(open(INPUT_FILES["external_rescore_v8_pairs"]))["bugsinpy"]}
    v6 = {r["pair_id"]: r for r in _jsonl(INPUT_FILES["bugsinpy_v6"])}
    recs = []
    for r in rows:
        w = v8.get(r["pair_id"])
        recs.append(dict(
            pair_id=r["pair_id"], corpus="bugsinpy", label=r["label"],
            kind="real" if r["label"] == 1 else r["transformation"],
            bug=r["bug_id"], project=r["project"],
            family="%s::%s::%s" % (r["project"], r["file"], r["unit"]),
            ev7=bool(r["evaluated"]), s7=r["scores"], static=r["static_scores"],
            ev8=bool(w["evaluated"]) if w else None, s8=w["scores"] if w else None,
            self_dist8=w["base_self_distance_v5"] if w else None,
            ev6=bool(v6[r["pair_id"]]["evaluated"]) if r["pair_id"] in v6 else None,
            s6=v6[r["pair_id"]]["scores"] if r["pair_id"] in v6 else None,
            failure_kind=r["failure_kind"], failure_side=r["failure_side"],
            failure_detail=r["failure_detail"],
            base_path=r["base_path"], variant_path=r["variant_path"]))
    out["bugsinpy"] = recs
    # ---- QuixBugs -----------------------------------------------------------
    v8q = {r["pair_id"]: r for r in json.load(open(INPUT_FILES["external_rescore_v8_pairs"]))["quixbugs_canonical"]}
    for corpus, key in (("quixbugs_canonical", "quixbugs_canonical_v7"),
                        ("quixbugs_declared", "quixbugs_declared_v7")):
        recs = []
        for r in _jsonl(INPUT_FILES[key]):
            w = v8q.get(r["pair_id"]) if corpus == "quixbugs_canonical" else None
            kind = "real" if r["label"] == 1 else r["pair_kind"].split(":")[1]
            sc = r["scores"]
            recs.append(dict(
                pair_id=r["pair_id"], corpus=corpus, label=r["label"], kind=kind,
                bug=r["base_id"], project=None, family=r["base_id"],
                ev7=bool(r["evaluated"]), s7=sc,
                static={k: sc[k] for k in ("static_ast", "static_token")} if sc else None,
                ev8=bool(w["evaluated"]) if w else None, s8=w["scores"] if w else None,
                self_dist8=w["base_self_distance_v5"] if w else None,
                ev6=None, s6=None,
                failure_kind=r["failure_kind"], failure_side=r["failure_side"],
                failure_detail=r["failure_detail"],
                base_path=r["base_path"], variant_path=r["variant_path"]))
        out[corpus] = recs
    return out


# ----------------------------------------------------------------------------
# AUROC
# ----------------------------------------------------------------------------

def auroc(scores, labels):
    """Tie-aware AUROC = P(s_pos > s_neg) + 0.5 P(s_pos == s_neg). None if single-class."""
    n = len(scores)
    npos = sum(labels)
    nneg = n - npos
    if npos == 0 or nneg == 0:
        return None
    order = sorted(range(n), key=scores.__getitem__)
    sp = 0.0
    i = 0
    while i < n:
        j = i
        s = scores[order[i]]
        while j + 1 < n and scores[order[j + 1]] == s:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            if labels[order[k]] == 1:
                sp += r
        i = j + 1
    return (sp - npos * (npos + 1) / 2.0) / (npos * nneg)


def auroc_bruteforce(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    t = 0.0
    for p in pos:
        for q in neg:
            t += 1.0 if p > q else (0.5 if p == q else 0.0)
    return t / (len(pos) * len(neg))


def auroc_tie_bounds(scores, labels):
    """(ties->0, ties->0.5, ties->1) AUROC."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    g = e = 0
    for p in pos:
        for q in neg:
            if p > q:
                g += 1
            elif p == q:
                e += 1
    n = len(pos) * len(neg)
    return g / n, (g + 0.5 * e) / n, (g + e) / n


def groups_of(clusters):
    d = {}
    for i, c in enumerate(clusters):
        d.setdefault(c, []).append(i)
    return list(d.values())


def quantile(sorted_vals, q):
    """Linear-interpolation quantile on a sorted list."""
    n = len(sorted_vals)
    if n == 0:
        return None
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, n - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


# ----------------------------------------------------------------------------
# bootstrap
# ----------------------------------------------------------------------------

def cluster_boot(preds, labels, groups, B=10000, seed=1234):
    """Cluster bootstrap. preds: dict name -> score list (aligned with labels).
    Returns dict name -> list of B (possibly None for single-class resamples) AUROCs.
    Resamples are shared across predictors (needed for paired deltas)."""
    rng = random.Random(seed)
    G = len(groups)
    names = list(preds)
    res = {n: [] for n in names}
    for _ in range(B):
        idx = []
        for _g in range(G):
            idx.extend(groups[rng.randrange(G)])
        lab = [labels[i] for i in idx]
        s = sum(lab)
        if s == 0 or s == len(lab):
            for n in names:
                res[n].append(None)
            continue
        for n in names:
            sc = preds[n]
            res[n].append(auroc([sc[i] for i in idx], lab))
    return res


def jackknife_clusters(scores, labels, groups):
    """Leave-one-cluster-out AUROC list (None entries dropped) with the removed cluster index."""
    out = []
    allidx = set(range(len(scores)))
    for gi, g in enumerate(groups):
        keep = sorted(allidx - set(g))
        a = auroc([scores[i] for i in keep], [labels[i] for i in keep])
        out.append((gi, a))
    return out


def ci_from_boot(theta, boot, scores=None, labels=None, groups=None, alpha=0.05):
    vals = sorted(v for v in boot if v is not None)
    n = len(vals)
    res = {"n_effective": n, "n_degenerate": len(boot) - n}
    if n == 0:
        return res
    lo, hi = quantile(vals, alpha / 2), quantile(vals, 1 - alpha / 2)
    res["percentile"] = [round(lo, 4), round(hi, 4)]
    res["basic"] = [round(2 * theta - hi, 4), round(2 * theta - lo, 4)]
    res["boot_mean"] = round(sum(vals) / n, 4)
    res["boot_sd"] = round((sum((v - sum(vals) / n) ** 2 for v in vals) / (n - 1)) ** 0.5, 4) if n > 1 else None
    # BCa
    if scores is not None:
        below = sum(1 for v in vals if v < theta) + 0.5 * sum(1 for v in vals if v == theta)
        frac = min(max(below / n, 0.5 / n), 1 - 0.5 / n)
        z0 = ND.inv_cdf(frac)
        jk = [a for _, a in jackknife_clusters(scores, labels, groups) if a is not None]
        if len(jk) >= 3:
            m = sum(jk) / len(jk)
            num = sum((m - a) ** 3 for a in jk)
            den = 6.0 * (sum((m - a) ** 2 for a in jk) ** 1.5)
            acc = num / den if den > 0 else 0.0
        else:
            acc = 0.0

        def adj(za):
            d = 1.0 - acc * (z0 + za)
            if d <= 0:
                return 0.0 if za < 0 else 1.0
            return ND.cdf(z0 + (z0 + za) / d)
        a1, a2 = adj(ND.inv_cdf(alpha / 2)), adj(ND.inv_cdf(1 - alpha / 2))
        res["bca"] = [round(quantile(vals, a1), 4), round(quantile(vals, a2), 4)]
        res["bca_z0"] = round(z0, 4)
        res["bca_acc"] = round(acc, 4)
    return res


def one_sided_upper_bound(boot, alpha=0.05):
    """Percentile one-sided (1-alpha) upper confidence bound."""
    vals = sorted(v for v in boot if v is not None)
    return quantile(vals, 1 - alpha) if vals else None


def one_sided_lower_bound(boot, alpha=0.05):
    vals = sorted(v for v in boot if v is not None)
    return quantile(vals, alpha) if vals else None


def paired_delta_boot(a_boot, b_boot):
    """Elementwise delta; drops degenerate."""
    return [x - y for x, y in zip(a_boot, b_boot) if x is not None and y is not None]


def delta_summary(theta_delta, deltas, alpha=0.05):
    vals = sorted(deltas)
    n = len(vals)
    lo, hi = quantile(vals, alpha / 2), quantile(vals, 1 - alpha / 2)
    # bootstrap two-sided p (percentile-inversion style): 2*min(P(d<=0),P(d>=0))
    le = sum(1 for v in vals if v <= 0)
    ge = sum(1 for v in vals if v >= 0)
    p2 = min(1.0, 2 * min((le + 1) / (n + 1), (ge + 1) / (n + 1)))
    return {"delta": round(theta_delta, 4), "ci95_percentile": [round(lo, 4), round(hi, 4)],
            "p_two_sided_boot": round(p2, 4), "n_effective": n}


# ----------------------------------------------------------------------------
# permutation tests
# ----------------------------------------------------------------------------

def perm_within_clusters(scores, labels, groups, M=20000, seed=4321):
    """Monte-Carlo within-cluster label permutation. Returns observed, p_lower (<=), p_upper (>=),
    p_two (|a-0.5| >=), with (b+1)/(M+1)."""
    rng = random.Random(seed)
    obs = auroc(scores, labels)
    mixed = [g for g in groups if len(g) > 1 and 0 < sum(labels[i] for i in g) < len(g)]
    lab = list(labels)
    n_le = n_ge = n_two = 0
    dev = abs(obs - 0.5)
    for _ in range(M):
        for g in mixed:
            vals = [labels[i] for i in g]
            rng.shuffle(vals)
            for i, v in zip(g, vals):
                lab[i] = v
        a = auroc(scores, lab)
        if a <= obs + 1e-12:
            n_le += 1
        if a >= obs - 1e-12:
            n_ge += 1
        if abs(a - 0.5) >= dev - 1e-12:
            n_two += 1
    return {"observed": round(obs, 4), "M": M, "n_mixed_clusters": len(mixed),
            "p_auroc_lt_0.5_lower_tail": round((n_le + 1) / (M + 1), 5),
            "p_auroc_gt_0.5_upper_tail": round((n_ge + 1) / (M + 1), 5),
            "p_two_sided": round((n_two + 1) / (M + 1), 5)}


def exact_stratified(scores, labels, groups):
    """Exact within-cluster permutation test of the pooled within-cluster AUROC
    T = sum_c U_c / sum_c (p_c q_c), where U_c is the Mann-Whitney count inside cluster c.
    Distribution by exhaustive enumeration of which p_c members of each cluster carry the
    positive label, convolved across clusters (integer arithmetic on 2*U)."""
    dist = {0: 1}
    denom = 0
    obs2U = 0
    ncl = 0
    for g in groups:
        p = sum(labels[i] for i in g)
        q = len(g) - p
        if p == 0 or q == 0:
            continue
        ncl += 1
        denom += p * q
        sc = [scores[i] for i in g]
        # observed
        pos = [sc[k] for k, i in enumerate(g) if labels[i] == 1]
        neg = [sc[k] for k, i in enumerate(g) if labels[i] == 0]
        obs2U += sum(2 if a > b else (1 if a == b else 0) for a in pos for b in neg)
        cd = {}
        for S in itertools.combinations(range(len(g)), p):
            Sset = set(S)
            u2 = 0
            for a in S:
                for b in range(len(g)):
                    if b not in Sset:
                        u2 += 2 if sc[a] > sc[b] else (1 if sc[a] == sc[b] else 0)
            cd[u2] = cd.get(u2, 0) + 1
        nd = {}
        for k1, c1 in dist.items():
            for k2, c2 in cd.items():
                nd[k1 + k2] = nd.get(k1 + k2, 0) + c1 * c2
        dist = nd
    total = sum(dist.values())
    le = sum(c for k, c in dist.items() if k <= obs2U)
    ge = sum(c for k, c in dist.items() if k >= obs2U)
    mid2 = denom  # 2U at AUROC=0.5 is denom (since 2U_max = 2*denom)
    two = sum(c for k, c in dist.items() if abs(k - mid2) >= abs(obs2U - mid2))
    return {"T_obs": round(obs2U / (2.0 * denom), 4), "n_clusters_informative": ncl,
            "n_cross_label_pairs": denom,
            "p_lower_tail_T<=obs": le / total, "p_upper_tail_T>=obs": ge / total,
            "p_two_sided": two / total, "n_arrangements_log10": round(math.log10(total), 2)}


# ----------------------------------------------------------------------------
# small exact tests
# ----------------------------------------------------------------------------

def fisher_exact(a, b, c, d):
    """Two-sided Fisher exact for 2x2 [[a,b],[c,d]] (sum of probabilities <= observed)."""
    n1, n2, k = a + b, c + d, a + c
    n = n1 + n2

    def pr(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n, k)
    lo, hi = max(0, k - n2), min(k, n1)
    p0 = pr(a)
    two = sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9))
    less = sum(pr(x) for x in range(lo, a + 1))
    greater = sum(pr(x) for x in range(a, hi + 1))
    return {"p_two_sided": min(1.0, two), "p_a_le": less, "p_a_ge": greater}


def wilson(k, n, z=1.959963985):
    if n == 0:
        return None
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 4), round(c + h, 4)]


# ----------------------------------------------------------------------------
# set helpers
# ----------------------------------------------------------------------------

def vecs(recs, pred, source, impute=0.0):
    """Score vector for a score source ('s7'|'s8'|'static'|'s6'); missing -> impute."""
    out = []
    for r in recs:
        s = r.get(source)
        v = None if s is None else s.get(pred)
        out.append(float(v) if v is not None else impute)
    return out


def bug_cluster(recs):
    return [r["bug"] for r in recs]


def project_cluster(recs):
    return [r["project"] if r["project"] is not None else r["bug"] for r in recs]


def family_cluster(recs):
    return [r["family"] for r in recs]

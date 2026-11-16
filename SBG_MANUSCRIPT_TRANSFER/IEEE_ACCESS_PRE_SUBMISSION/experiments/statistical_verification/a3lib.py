"""A3 independent statistics + data library (pure standard library).

Written by Agent A3 from the *definitions* (not by importing) of: SBG/sbg/statistics.py, evaluate_v9.py, evaluate_v10.py,
fit_weights.py, edit_size_analysis.py, static_baselines.py.  It imports NOTHING from SBG/ and nothing from experiments/common.
Only raw data files are read: dataset pair metadata, frozen scored pair files, validity-audit JSONs, frozen model JSONs.

The RNG call order of the repository's bootstrap / permutation procedures is re-implemented so that, for the same seed,
identical resamples are produced (so CIs can be compared digit-for-digit).
"""
from __future__ import annotations

import ast
import collections
import difflib
import hashlib
import json
import math
import pathlib
import random
import tokenize
from io import StringIO

PKG = pathlib.Path(__file__).resolve().parents[2]
REPO = PKG.parent / "SBG"
ART = REPO / "artifacts" / "final"
EV = REPO / "artifacts" / "paper_evidence"
V8D = REPO / "benchmark" / "datasets" / "v8"
V9D = REPO / "benchmark" / "datasets" / "v9_composed"
V10D = REPO / "benchmark" / "datasets" / "v10_independent"
B, SEED = 2000, 42


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ----------------------------------------------------------------------------- edit size / static baselines
def canonical_lines(path):
    return ast.unparse(ast.parse((REPO / path).read_text())).splitlines()


def edit_size(base_path, variant_path):
    """Number of added+removed lines in a zero-context unified diff of the ast.unparse()-canonicalised sources."""
    n = 0
    for line in difflib.unified_diff(canonical_lines(base_path), canonical_lines(variant_path), lineterm="", n=0):
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            n += 1
    return n


def token_multiset(src):
    c = collections.Counter()
    skip = (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.STRING)
    try:
        for t in tokenize.generate_tokens(StringIO(src).readline):
            if t.type in skip:
                continue
            c[(t.type, t.string)] += 1
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return collections.Counter()
    return c


def ast_multiset(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return collections.Counter()
    c = collections.Counter()
    for node in ast.walk(tree):
        c[type(node).__name__] += 1
        if isinstance(node, ast.Name):
            c[f"Name:{node.id}"] += 1
        elif isinstance(node, ast.Constant):
            c[f"Const:{node.value!r}"] += 1
    return c


def ms_distance(a, b):
    if not a and not b:
        return 0.0
    keys = set(a) | set(b)
    inter = sum(min(a[k], b[k]) for k in keys)
    uni = sum(max(a[k], b[k]) for k in keys)
    return 1.0 - (inter / uni if uni else 0.0)


# ----------------------------------------------------------------------------- metrics
def auroc(s, y):
    n = len(s)
    npos = sum(y)
    nneg = n - npos
    if n == 0 or npos == 0 or nneg == 0:
        return 0.5
    order = sorted(range(n), key=s.__getitem__)
    rank_sum = 0.0
    i = 0
    while i < n:
        j = i
        v = s[order[i]]
        while j < n and s[order[j]] == v:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            if y[order[k]] == 1:
                rank_sum += avg
        i = j
    return max(0.0, min(1.0, (rank_sum - npos * (npos + 1) / 2.0) / (npos * nneg)))


def auprc(s, y):
    P = sum(y)
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


def prf_at(s, y, thr):
    tp = sum(1 for a, b in zip(s, y) if a >= thr and b == 1)
    fp = sum(1 for a, b in zip(s, y) if a >= thr and b == 0)
    fn = sum(1 for a, b in zip(s, y) if a < thr and b == 1)
    tn = sum(1 for a, b in zip(s, y) if a < thr and b == 0)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"thr": thr, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": p, "recall": r,
            "f1": 2 * p * r / (p + r) if p + r else 0.0, "specificity": tn / (tn + fp) if tn + fp else 0.0,
            "accuracy": (tp + tn) / len(s)}


def youden(s, y):
    """argmax over distinct score values t of TPR(>=t) - FPR(>=t); first (smallest) maximiser."""
    P, N = sum(y), len(y) - sum(y)
    best, thr = -1.0, None
    for t in sorted(set(s)):
        tpr = sum(1 for a, b in zip(s, y) if b and a >= t) / P
        fpr = sum(1 for a, b in zip(s, y) if not b and a >= t) / N
        if tpr - fpr > best:
            best, thr = tpr - fpr, t
    return thr


def best_f1_threshold(s, y):
    best, thr = -1.0, None
    for t in sorted(set(s)):
        f = prf_at(s, y, t)["f1"]
        if f > best:
            best, thr = f, t
    return thr, best


# ----------------------------------------------------------------------------- repository-identical resampling
def by_cluster(c):
    d = collections.defaultdict(list)
    for i, k in enumerate(c):
        d[k].append(i)
    return d


def resample_plan(n_keys, b=B, seed=SEED):
    """The cluster-index draws made by the repo: for each replicate, n_keys calls of rng.randrange(n_keys)."""
    rng = random.Random(seed)
    return [[rng.randrange(n_keys) for _ in range(n_keys)] for _ in range(b)]


def _round6(v):
    return round(v, 6)


def boot_stat_values(fn, c, y, plan=None, b=B, seed=SEED):
    """Evaluate fn(idx_list) on each cluster-bootstrap replicate; discards replicates lacking one class (as the repo)."""
    d = by_cluster(c)
    keys = sorted(d)
    plan = plan if plan is not None else resample_plan(len(keys), b, seed)
    out = []
    for draw in plan:
        idx = []
        for k in draw:
            idx.extend(d[keys[k]])
        yy = [y[i] for i in idx]
        if 0 < sum(yy) < len(yy):
            out.append(fn(idx, yy))
    return out


def pct_ci(vals):
    v = sorted(vals)
    n = len(v)
    lo = v[max(0, int(math.floor(0.05 / 2 * n)))]
    hi = v[min(n - 1, int(math.ceil((1 - 0.05 / 2) * n)) - 1)]
    return _round6(lo), _round6(hi), n


def boot_ci(s, y, c, plan=None, b=B, seed=SEED):
    vals = boot_stat_values(lambda idx, yy: auroc([s[i] for i in idx], yy), c, y, plan, b, seed)
    return pct_ci(vals)


def paired_delta(sa, sb, y, c, plan=None, b=B, seed=SEED):
    obs = auroc(sa, y) - auroc(sb, y)
    vals = boot_stat_values(lambda idx, yy: auroc([sa[i] for i in idx], yy) - auroc([sb[i] for i in idx], yy), c, y, plan, b, seed)
    lo, hi, m = pct_ci(vals)
    n_le = sum(1 for d in vals if d <= 0.0)
    n_ge = sum(1 for d in vals if d >= 0.0)
    p = min(1.0, 2.0 * min(n_le + 1, n_ge + 1) / (m + 1))
    return {"delta": _round6(obs), "ci_lower": lo, "ci_upper": hi, "p_two_sided": _round6(p), "n_effective": m}


def perm_p(s, y, c, b=B, seed=SEED):
    """One-sided within-cluster label permutation; clusters visited in first-appearance order (as the repo)."""
    obs = auroc(s, y)
    d = by_cluster(c)
    rng = random.Random(seed)
    perm = list(y)
    k = 0
    for _ in range(b):
        for idx in d.values():
            pool = [y[i] for i in idx]
            rng.shuffle(pool)
            for slot, v in zip(idx, pool):
                perm[slot] = v
        if auroc(s, perm) >= obs:
            k += 1
    return (k + 1) / (b + 1)


def holm(p):
    names = sorted(p, key=lambda k: p[k])
    m, run, out = len(names), 0.0, {}
    for r, k in enumerate(names):
        run = max(run, min(1.0, (m - r) * p[k]))
        out[k] = {"p_raw": round(p[k], 6), "p_adjusted": round(run, 6), "rank": r + 1}
    return out


def matched_concordance(rows, key, b=B, seed=SEED):
    g = collections.defaultdict(dict)
    for r in rows:
        g[r["group"]][r["label"]] = r
    sets = [(v[1]["base_id"], 1.0 if key(v[1]) > key(v[0]) else 0.5 if key(v[1]) == key(v[0]) else 0.0) for v in g.values() if 0 in v and 1 in v]
    by = collections.defaultdict(list)
    for p, v in sets:
        by[p].append(v)
    ks, rng, vals = sorted(by), random.Random(seed), []
    for _ in range(b):
        sm = [c for k in (rng.choice(ks) for _ in ks) for c in by[k]]
        vals.append(sum(sm) / len(sm))
    vals.sort()
    return {"concordance": round(sum(v for _, v in sets) / len(sets), 6), "n_matched_sets": len(sets),
            "ci95": [round(vals[int(.025 * b)], 6), round(vals[int(.975 * b) - 1], 6)]}


def exact_edit_stratified(rows, key):
    g = collections.defaultdict(lambda: ([], []))
    for r in rows:
        g[r["edit"]][r["label"]].append(key(r))
    num = den = 0.0
    for neg, pos in g.values():
        for a in pos:
            for bb in neg:
                num += 1.0 if a > bb else .5 if a == bb else 0.0
        den += len(pos) * len(neg)
    return (round(num / den, 6) if den else None), den


# ----------------------------------------------------------------------------- logistic model
def sigmoid(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def fit_logistic(X, y, l2=1.0, lr=0.5, iters=5000):
    """Full-batch GD on mean log-loss + l2*||w||^2/n; standardised features (population std); zero init."""
    n, k = len(X), len(X[0])
    means = [sum(r[j] for r in X) / n for j in range(k)]
    stds = []
    for j in range(k):
        var = sum((r[j] - means[j]) ** 2 for r in X) / n
        stds.append(math.sqrt(var) if var > 0 else 1.0)
    Z = [[(r[j] - means[j]) / stds[j] for j in range(k)] for r in X]
    w, b = [0.0] * k, 0.0
    for _ in range(iters):
        gw, gb = [0.0] * k, 0.0
        for z, t in zip(Z, y):
            err = sigmoid(b + sum(wj * zj for wj, zj in zip(w, z))) - t
            gb += err
            for j in range(k):
                gw[j] += err * z[j]
        b -= lr * gb / n
        w = [wj - lr * (gj / n + 2.0 * l2 * wj / n) for wj, gj in zip(w, gw)]
    return {"weights_standardised": [round(v, 9) for v in w], "bias": round(b, 9),
            "feature_means": [round(v, 12) for v in means], "feature_stds": [round(v, 12) for v in stds]}


def lin_score(m, sc):
    z = m["bias"]
    for j, f in enumerate(m["features"]):
        z += m["weights_standardised"][j] * ((sc[f] - m["feature_means"][j]) / m["feature_stds"][j])
    return round(z, 9)


# ----------------------------------------------------------------------------- population construction (from raw files)
def matched_complete(rows, valid_key="_valid"):
    ok = collections.OrderedDict()
    for r in rows:
        if r.get(valid_key):
            ok.setdefault(r["group"], []).append(r)
    return [x for g in ok.values() if len(g) == 2 and {z["label"] for z in g} == {0, 1} for x in g]


def build_v10(with_static=True):
    """Return (all_rows, primary_rows).  Raw files only: pairs_test.jsonl (meta) + frozen scored file."""
    meta = {m["pair_id"]: m for m in jl(V10D / "pairs_test.jsonl")}
    scored = {r["pair_id"]: r for r in jl(ART / "pairs_v10_test_v6exp.jsonl")}
    rows, cache = [], {}
    for pid, m in meta.items():
        r = scored[pid]
        if not r["evaluated"]:
            rows.append({"pair_id": pid, "evaluated": False, "_valid": False, "base_id": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
                         "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"], "transformation_type": m["transformation_type"]})
            continue
        sc = dict(r["scores"])
        sc["sbg_v6"], sc["sbg_state_v6"] = r["sbg_v6"], r["sbg_state_v6"]
        e = float(edit_size(m["base_path"], m["variant_path"]))
        sc["edit"] = e
        if with_static:
            for pth in (m["base_path"], m["variant_path"]):
                if pth not in cache:
                    src = (REPO / pth).read_text()
                    cache[pth] = (token_multiset(src), ast_multiset(src))
            sc["static_token"] = ms_distance(cache[m["base_path"]][0], cache[m["variant_path"]][0])
            sc["static_ast"] = ms_distance(cache[m["base_path"]][1], cache[m["variant_path"]][1])
        rows.append({"pair_id": pid, "evaluated": True, "_valid": True, "base_id": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
                     "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"],
                     "transformation_type": m["transformation_type"], "sc_type": m.get("sc_type"), "sp_type": m.get("sp_type"),
                     "base_path": m["base_path"], "variant_path": m["variant_path"], "edit": e, "scores": sc})
    return rows, matched_complete(rows)


def stale_programs():
    return {s["program"] for s in json.loads((EV / "DIAGNOSTIC_V8_STALE_VARIANTS.json").read_text())["stale_programs"]}


def build_v9c(split, v6exp=False):
    """v9c matched-complete population for a split. Raw: v9c pairs meta, v8 pairs meta, scored v9c + v8 files, validity audits."""
    stale = stale_programs()
    meta = {m["pair_id"]: m for m in jl(V9D / f"pairs_{split}.jsonl")}
    v8meta = {m["pair_id"]: m for m in jl(V8D / f"pairs_{split}.jsonl")}
    wanted = {m["matched_equivalent_pair_id"] for m in meta.values()}
    for k in wanted:
        meta[k] = v8meta[k]
    v8file = {"train": "pairs_v8train_output_free_v8.jsonl", "dev": "pairs_v8devrescore_output_free_v8.jsonl", "val": "pairs_v8val_output_free_v8.jsonl"}[split]
    rows = jl(ART / f"pairs_v9c_{split}_output_free_v8.jsonl") + [r for r in jl(ART / v8file) if r["pair_id"] in wanted]
    audit = {r["pair_id"]: r for r in json.loads((ART / "BENCHMARK_VALIDITY_AUDIT_V9C.json").read_text())["pairs"] if r["split"] == split}
    audit.update({r["pair_id"]: r for r in json.loads((ART / "BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json").read_text())["pairs"]
                  if r["split"] == split and r["pair_id"] in wanted})
    v6 = {r["pair_id"]: r for r in jl(ART / f"pairs_v9c_{split}_v6exp.jsonl")} if v6exp else {}
    out = []
    for r in rows:
        if r["base_id"] in stale:
            continue
        m = meta[r["pair_id"]]
        r["label"] = int(m["semantic_relation"] == "CHANGED")
        v = audit.get(r["pair_id"])
        r["_valid"] = bool(r["evaluated"] and v and v.get("status") == "ok" and (r["label"] == 0 or v.get("observable") is True))
        r["group"] = m.get("matched_equivalent_pair_id") if r["label"] else r["pair_id"]
        r["transformation_type"] = m["transformation_type"]
        r["sc_type"], r["sp_type"] = m.get("sc_type"), m.get("sp_type")
        r["base_path"], r["variant_path"] = m["base_path"], m["variant_path"]
        if r["evaluated"]:
            r["edit"] = float(edit_size(m["base_path"], m["variant_path"]))
            r["scores"]["edit"] = r["edit"]
            if v6exp:
                q = v6[r["pair_id"]]
                r["scores"]["sbg_v6"], r["scores"]["sbg_state_v6"] = q["sbg_v6"], q["sbg_state_v6"]
        out.append(r)
    return out, matched_complete(out)


def build_v8_test():
    """v8 original design TEST (non-stale), 'valid' pairs (evaluated, audit ok, CHANGED observable); label from meta."""
    stale = stale_programs()
    meta = {m["pair_id"]: m for m in jl(V8D / "pairs_test.jsonl")}
    audit = {r["pair_id"]: r for r in json.loads((ART / "BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json").read_text())["pairs"] if r["split"] == "test"}
    out = []
    for r in jl(ART / "pairs_v8test_output_free_v8.jsonl"):
        if r["base_id"] in stale:
            continue
        m = meta[r["pair_id"]]
        r["label"] = int(m["semantic_relation"] == "CHANGED")
        v = audit.get(r["pair_id"])
        r["_valid"] = bool(r["evaluated"] and v and v.get("status") == "ok" and (r["label"] == 0 or v.get("observable") is True))
        r["transformation_type"] = m["transformation_type"]
        r["base_path"], r["variant_path"] = m["base_path"], m["variant_path"]
        if r["evaluated"]:
            r["edit"] = float(edit_size(m["base_path"], m["variant_path"]))
            r["scores"]["edit"] = r["edit"]
            r["scores"]["edit_size_reversed"] = -r["edit"]
        out.append(r)
    return out, [r for r in out if r["_valid"]]


def vec(rows, p):
    return [r["scores"][p] for r in rows], [r["label"] for r in rows], [r["base_id"] for r in rows]

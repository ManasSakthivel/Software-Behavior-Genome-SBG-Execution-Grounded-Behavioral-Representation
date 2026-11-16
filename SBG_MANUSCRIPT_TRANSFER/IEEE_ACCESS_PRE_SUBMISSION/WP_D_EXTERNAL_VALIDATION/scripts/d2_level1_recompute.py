#!/usr/bin/env python3
"""WP-D / D2 Task A -- Level-1 recomputation of the external AUROCs from the committed
per-pair score files, with OWN stdlib code (no import of SBG's sbg.statistics,
PKG/experiments/statistical_verification or any repo module).

    d2_level1_recompute.py SBG_ROOT OUT_DIR

Inputs (read-only):
  SBG/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl
  SBG/artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl
  SBG/artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl
  SBG/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json

Outputs (OUT dir): level1_results.json, level1_summary.md, dropped_pairs.csv

AUROC definition (own implementation): P(score_pos > score_neg) + 0.5 P(tie), computed by
direct pair counting; a rank-sum implementation is used inside the bootstrap and
asserted equal to the direct count at the point estimate.

Cluster bootstrap: B=2000, seed=42, resample whole clusters (bug_id / base program) with
replacement, discard single-class resamples, percentile interval. Two percentile
conventions are reproduced because the two committed code paths differ:
  "repo"    : lower=s[floor(.025 n)], upper=s[ceil(.975 n)-1], rounded to 6 d.p.   (sbg.statistics)
  "rescore" : lower=s[int(.025 n)],   upper=s[int(.975 n)-1],  rounded to 4 d.p.   (rescore_external_v8._ci)
"""
import collections
import csv
import json
import math
import pathlib
import random
import sys

SBG = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
FINAL = SBG / "artifacts/final"
B, SEED = 2000, 42


# ------------------------------------------------------------------ statistics (own code)
def auroc_direct(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    gt = eq = 0
    for p in pos:
        for n in neg:
            if p > n:
                gt += 1
            elif p == n:
                eq += 1
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def auroc_rank(scores, labels):
    n = len(scores)
    order = sorted(range(n), key=lambda i: scores[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    npos = sum(labels)
    nneg = n - npos
    if npos == 0 or nneg == 0:
        return None
    rs = sum(ranks[i] for i in range(n) if labels[i] == 1)
    return (rs - npos * (npos + 1) / 2.0) / (npos * nneg)


def boot_ci(scores, labels, clusters, convention):
    by = collections.defaultdict(list)
    for i, c in enumerate(clusters):
        by[c].append(i)
    keys = sorted(by)
    rng = random.Random(SEED)
    vals = []
    for _ in range(B):
        idx = []
        for _k in keys:
            idx.extend(by[keys[rng.randrange(len(keys))]])
        lab = [labels[i] for i in idx]
        if 0 < sum(lab) < len(lab):
            vals.append(auroc_rank([scores[i] for i in idx], lab))
    vals.sort()
    m = len(vals)
    if convention == "repo":
        lo = vals[max(0, int(math.floor(0.025 * m)))]
        hi = vals[min(m - 1, int(math.ceil(0.975 * m)) - 1)]
        return [round(lo, 6), round(hi, 6)], m
    lo = vals[int(0.025 * m)]
    hi = vals[int(0.975 * m) - 1]
    return [round(lo, 4), round(hi, 4)], m


def evaluate(rows, score_key, convention, zero_fill):
    """rows: dicts with label, cluster, evaluated, <score_key>. zero_fill: unevaluated -> 0.0
    else unevaluated rows are dropped."""
    use = [r for r in rows if r["evaluated"] or zero_fill]
    s = [(r[score_key] if r["evaluated"] and r[score_key] is not None else 0.0) for r in use]
    y = [r["label"] for r in use]
    c = [r["cluster"] for r in use]
    npos = sum(y)
    out = {"n_pairs": len(use), "n_pos": npos, "n_neg": len(use) - npos, "n_clusters": len(set(c)),
           "n_unevaluated_included_as_zero": sum(1 for r in use if not r["evaluated"])}
    if npos == 0 or npos == len(use):
        out.update(auroc=None, ci95=None)
        return out
    a1, a2 = auroc_direct(s, y), auroc_rank(s, y)
    assert abs(a1 - a2) < 1e-12, (a1, a2)
    ci, m = boot_ci(s, y, c, convention)
    ps = [v for v, l in zip(s, y) if l == 1]
    ns = [v for v, l in zip(s, y) if l == 0]
    gt = sum(1 for p in ps for n in ns if p > n)
    eq = sum(1 for p in ps for n in ns if p == n)
    out.update(auroc=round(a1, 6), ci95_cluster_bootstrap=ci, ci_convention=convention, ci_n_effective=m,
               P_pos_gt_neg=round(gt / (len(ps) * len(ns)), 6), P_tie=round(eq / (len(ps) * len(ns)), 6),
               P_pos_lt_neg=round(1 - (gt + eq) / (len(ps) * len(ns)), 6),
               pos_exactly_zero=sum(1 for v in ps if v == 0.0), neg_exactly_zero=sum(1 for v in ns if v == 0.0))
    return out


# ------------------------------------------------------------------ load
def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def load_v7():
    res = {}
    b = []
    for r in jl(FINAL / "pairs_bugsinpy_output_free_v7.jsonl"):
        b.append({"corpus": "bugsinpy", "regime": "canonical", "pair_id": r["pair_id"], "cluster": r["bug_id"],
                  "label": r["label"], "transformation": r["transformation"], "evaluated": r["evaluated"],
                  "sbg_v5_v7": r["scores"]["sbg_v5"] if r["evaluated"] else None,
                  "failure": f"{r['failure_side']}:{r['failure_kind']}" if not r["evaluated"] else "",
                  "failure_detail": (r.get("failure_detail") or "")[:160]})
    res["bugsinpy"] = b
    for reg in ("canonical", "declared"):
        q = []
        for r in jl(FINAL / f"pairs_quixbugs_{reg}_output_free_v7.jsonl"):
            tr = "real_bug" if r["pair_kind"] == "real_bug" else r["pair_kind"].split(":")[1]
            q.append({"corpus": "quixbugs", "regime": reg, "pair_id": r["pair_id"], "cluster": r["base_id"],
                      "label": r["label"], "transformation": tr, "evaluated": r["evaluated"],
                      "sbg_v5_v7": r["scores"]["sbg_v5"] if r["evaluated"] else None,
                      "failure": f"{r['failure_side']}:{r['failure_kind']}" if not r["evaluated"] else "",
                      "failure_detail": (r.get("failure_detail") or "")[:160]})
        res[f"quixbugs_{reg}"] = q
    return res


def load_v8():
    d = json.loads((SBG / "artifacts/paper_evidence/raw/external_rescore_v8_pairs.json").read_text())
    out = {}
    for name, rows in d.items():
        out[name] = [{"pair_id": r["pair_id"], "cluster": r["cluster"], "label": r["label"],
                      "transformation": r["transformation"], "evaluated": r["evaluated"],
                      "sbg_v5_v8": r["sbg_v5"], "committed_v7_in_v8file": r.get("committed_sbg_v5"),
                      "failure": r.get("failure_kind") or "",
                      "base_self_distance_v5": r.get("base_self_distance_v5")} for r in rows]
    return out


v7 = load_v7()
v8 = load_v8()
res = {"seed": SEED, "n_bootstrap": B, "variants": [], "consistency": {}}


def add(name, corpus_rows, score_key, convention, exclude_sp2, zero_fill, note=""):
    rows = [r for r in corpus_rows if not (exclude_sp2 and r["transformation"] == "SP-2")]
    r = evaluate(rows, score_key, convention, zero_fill)
    r.update(variant=name, score_source=score_key, exclude_SP2=exclude_sp2,
             unevaluated_handling="scored_0.0" if zero_fill else "dropped", note=note)
    res["variants"].append(r)
    return r


# ---- v7 committed scores (from the v7 pairs files) -------------------------------------
for key in ("bugsinpy", "quixbugs_canonical", "quixbugs_declared"):
    for ex in (False, True):
        for zf in (False, True):
            add(f"{key} | v7 committed | {'SP-2 excluded' if ex else 'all pairs'} | "
                f"{'unevaluated=0' if zf else 'evaluated only'}", v7[key], "sbg_v5_v7", "repo", ex, zf)

# ---- v8 rescored (EXTERNAL_RESCORE_V8 pair dump) ----------------------------------------
for key in ("bugsinpy", "quixbugs_canonical"):
    rows = list(v8[key])
    for ex in (False, True):
        tag = "SP-2 excluded" if ex else "all pairs"
        add(f"{key} | v8 rescore | {tag} | evaluated only", rows, "sbg_v5_v8", "rescore", ex, False)
        add(f"{key} | v8 rescore | {tag} | unevaluated=0 (v8 dump rows only)", rows, "sbg_v5_v8", "rescore", ex, True,
            note="only rows present in the v8 dump; BugsInPy v7-unevaluated rows were never loaded by "
                 "rescore_external_v8.load_source")
        crow = [dict(r, evaluated=(r["evaluated"] and r["committed_v7_in_v8file"] is not None),
                     sbg_v5_c=r["committed_v7_in_v8file"]) for r in rows]
        add(f"{key} | v7 committed scores on the v8-dump pair set | {tag} | evaluated only", crow, "sbg_v5_c",
            "rescore", ex, False,
            note="pairs evaluated under v8 AND with a committed v7 score (= 'committed_v7_same_pairs' in EXTERNAL_RESCORE_V8.json); rescore-style CI")

# ---- v8 scores + the v7-unevaluated BugsInPy rows scored 0 (200-pair population) --------
v8by = {r["pair_id"]: r for r in v8["bugsinpy"]}
full = []
for r in v7["bugsinpy"]:
    x = v8by.get(r["pair_id"])
    if x is not None:
        full.append({"cluster": r["cluster"], "label": r["label"], "transformation": r["transformation"],
                     "evaluated": x["evaluated"], "s": x["sbg_v5_v8"]})
    else:
        full.append({"cluster": r["cluster"], "label": r["label"], "transformation": r["transformation"],
                     "evaluated": False, "s": None})
for ex in (False, True):
    add(f"bugsinpy | v8 rescore + 53 v7-unevaluated rows scored 0 (200-pair population) | "
        f"{'SP-2 excluded' if ex else 'all pairs'} | unevaluated=0", full, "s", "rescore", ex, True,
        note="constructed by D2: the v8 rescore omitted the 53 v7-unevaluated rows; they are added back at 0")

# ---- cross-file consistency --------------------------------------------------------------
cons = {}
for key in ("bugsinpy", "quixbugs_canonical"):
    v7map = {r["pair_id"]: r for r in v7[key]}
    n_in_v7 = n_missing = n_eq = n_diff_ev = 0
    maxabs = 0.0
    for r in v8[key]:
        o = v7map.get(r["pair_id"])
        if o is None:
            n_missing += 1
            continue
        n_in_v7 += 1
        if r["committed_v7_in_v8file"] is None or o["sbg_v5_v7"] is None:
            if (r["committed_v7_in_v8file"] is None) != (o["sbg_v5_v7"] is None):
                n_diff_ev += 1
            continue
        d = abs(r["committed_v7_in_v8file"] - o["sbg_v5_v7"])
        maxabs = max(maxabs, d)
        n_eq += d == 0.0
    deltas = [(r["sbg_v5_v8"] - r["committed_v7_in_v8file"]) for r in v8[key]
              if r["evaluated"] and r["committed_v7_in_v8file"] is not None]
    cons[key] = {"v8_rows": len(v8[key]), "joined_to_v7_by_pair_id": n_in_v7, "not_in_v7_file": n_missing,
                 "embedded_committed_equals_v7_file_exactly": n_eq,
                 "embedded_committed_vs_v7_file_max_abs_diff": maxabs,
                 "evaluated_status_disagreements": n_diff_ev,
                 "v8_minus_v7_score": {"n": len(deltas), "n_identical": sum(1 for d in deltas if d == 0.0),
                                       "n_changed": sum(1 for d in deltas if d != 0.0),
                                       "max_abs": max((abs(d) for d in deltas), default=None),
                                       "mean": round(sum(deltas) / len(deltas), 6) if deltas else None}}
res["consistency"] = cons

# ---- funnel ------------------------------------------------------------------------------
fun = {}
b7 = v7["bugsinpy"]
fun["bugsinpy"] = {
    "v7_pairs_total": len(b7), "v7_pos": sum(r["label"] for r in b7),
    "v7_clusters(bugs with an eligible unit)": len({r["cluster"] for r in b7}),
    "v7_unevaluated": sum(not r["evaluated"] for r in b7),
    "v7_unevaluated_by_reason": dict(collections.Counter(r["failure"] for r in b7 if not r["evaluated"])),
    "v7_unevaluated_positives": sum(1 for r in b7 if not r["evaluated"] and r["label"] == 1),
    "v7_unevaluated_negatives": sum(1 for r in b7 if not r["evaluated"] and r["label"] == 0),
    "v7_unevaluated_clusters": len({r["cluster"] for r in b7 if not r["evaluated"]}),
    "v7_evaluated": sum(r["evaluated"] for r in b7),
    "v7_evaluated_pos": sum(r["label"] for r in b7 if r["evaluated"]),
    "v7_evaluated_clusters": len({r["cluster"] for r in b7 if r["evaluated"]}),
    "v8_file_rows": len(v8["bugsinpy"]),
    "v7_evaluated_by_transformation": dict(collections.Counter(r["transformation"] for r in b7 if r["evaluated"])),
    "v7_unevaluated_by_transformation": dict(collections.Counter(r["transformation"] for r in b7 if not r["evaluated"])),
}
for key in ("quixbugs_canonical", "quixbugs_declared"):
    q = v7[key]
    fun[key] = {"v7_pairs_total": len(q), "v7_pos": sum(r["label"] for r in q),
                "v7_unevaluated": sum(not r["evaluated"] for r in q),
                "v7_unevaluated_by_reason": dict(collections.Counter(r["failure"] for r in q if not r["evaluated"])),
                "v7_unevaluated_positives": sum(1 for r in q if not r["evaluated"] and r["label"] == 1),
                "v7_evaluated_by_transformation": dict(collections.Counter(r["transformation"] for r in q if r["evaluated"]))}
fun["quixbugs_canonical"]["v8_file_rows"] = len(v8["quixbugs_canonical"])
fun["quixbugs_canonical"]["v8_unevaluated"] = [(r["pair_id"], r["failure"]) for r in v8["quixbugs_canonical"]
                                               if not r["evaluated"]]
res["funnel"] = fun

# ---- dropped-pairs CSV -------------------------------------------------------------------
rows_csv = []
for key in ("bugsinpy", "quixbugs_canonical", "quixbugs_declared"):
    v8map = {r["pair_id"]: r for r in v8.get(key, [])}
    for r in v7[key]:
        x = v8map.get(r["pair_id"])
        reasons = []
        in_v7_all = in_v7_ex = in_v8_all = in_v8_ex = False
        if r["evaluated"]:
            in_v7_all = True
            in_v7_ex = r["transformation"] != "SP-2"
        else:
            reasons.append(f"v7_unevaluated({r['failure']})")
        if key in v8:
            if x is None:
                reasons.append("absent_from_v8_rescore(loader skipped v7-unevaluated row)")
            elif not x["evaluated"]:
                reasons.append(f"v8_unevaluated({x['failure']})")
            else:
                in_v8_all = True
                in_v8_ex = r["transformation"] != "SP-2"
        if r["transformation"] == "SP-2":
            reasons.append("excluded_SP-2(post-hoc, decided after v7 results)")
        rows_csv.append({
            "corpus_regime": key, "pair_id": r["pair_id"], "cluster": r["cluster"], "label": r["label"],
            "transformation": r["transformation"], "v7_evaluated": r["evaluated"],
            "v7_sbg_v5": "" if r["sbg_v5_v7"] is None else r["sbg_v5_v7"],
            "v8_in_dump": x is not None, "v8_evaluated": "" if x is None else x["evaluated"],
            "v8_sbg_v5": "" if (x is None or x["sbg_v5_v8"] is None) else x["sbg_v5_v8"],
            "in_v7_evaluated_all": in_v7_all, "in_v7_evaluated_exSP2": in_v7_ex,
            "in_v8_evaluated_all": in_v8_all if key in v8 else "n/a",
            "in_v8_evaluated_exSP2": in_v8_ex if key in v8 else "n/a",
            "drop_reasons": "; ".join(reasons), "failure_detail": r["failure_detail"]})
with open(OUT / "dropped_pairs.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_csv[0]))
    w.writeheader()
    w.writerows(rows_csv)
res["csv_rows"] = len(rows_csv)
res["csv_rows_with_any_drop_reason"] = sum(1 for r in rows_csv if r["drop_reasons"])

(OUT / "level1_results.json").write_text(json.dumps(res, indent=1) + "\n")

# ---- console / markdown summary ------------------------------------------------------------
lines = ["| variant | n | pos/neg | clusters | AUROC | 95% CI (cluster bootstrap) | P(pos>neg) / P(tie) |",
         "|---|---|---|---|---|---|---|"]
for v in res["variants"]:
    lines.append(f"| {v['variant'].replace(' | ', ' ; ')} | {v['n_pairs']} | {v['n_pos']}/{v['n_neg']} | {v['n_clusters']} | "
                 f"{v['auroc']} | {v.get('ci95_cluster_bootstrap')} ({v.get('ci_convention')}) | "
                 f"{v.get('P_pos_gt_neg')} / {v.get('P_tie')} |")
(OUT / "level1_summary.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
print(json.dumps(res["consistency"], indent=1))
print(json.dumps(res["funnel"], indent=1))

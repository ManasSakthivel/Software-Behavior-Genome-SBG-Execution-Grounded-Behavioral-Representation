"""FINAL SPRINT Part 4 -- review-budget triage metrics (EXPLORATORY, post-hoc, read-only over frozen scores).

Question: if a reviewer inspects only the top-ranked fraction of pairs (ranked by a predictor), what fraction of the
behaviour-CHANGING pairs is found?  Metric definitions and interpretation limits were fixed in this
file before it was run (see PRACTICAL_SIGNIFICANCE_ASSESSMENT.md):
  * populations are matched-complete benchmark populations with 50% CHANGED prevalence BY CONSTRUCTION, so precision is
    NOT an estimate of real-world precision; recall and the ranking effort are the only quantities interpreted;
  * ties (many exact-zero SBG scores) are handled by expected value (random tie order), never optimistically;
  * 95% CIs are percentile bootstrap over programs (cluster = base_id), seed 42, 2000 resamples (as sprint_incremental).
No model is fitted here; all predictors are frozen (V10_MODELS_FROZEN.json / V9_MODELS_FROZEN.json).

Run:  cd experiments/final && PYTHONHASHSEED=0 ../../../venvs/py313/bin/python sprint_practical.py
"""
from __future__ import annotations

import collections
import json
import random

import sprint_common as C

SEED, NBOOT = 42, 2000
PRED = ("sbg_v5", "edit", "M_EX", "M_EX+V5")
BUDGETS = (0.10, 0.25, 0.50)
RECALL_TARGETS = (0.5, 0.8, 0.95)


def ranked_groups(rows, pred):
    """Descending score tie groups: list of (n_items, n_changed)."""
    g = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: -r["scores"][pred]):
        k = r["scores"][pred]
        n, c = g.get(k, (0, 0))
        g[k] = (n + 1, c + r["label"])
    return list(g.values())


def recall_at_budget(rows, pred, frac):
    """Expected fraction of CHANGED pairs inside the top ceil-free fraction `frac` of the list (ties split proportionally)."""
    N = len(rows)
    P = sum(r["label"] for r in rows)
    budget = frac * N
    found = used = 0.0
    for n, c in ranked_groups(rows, pred):
        if used + n <= budget:
            found += c
            used += n
        else:
            found += c * (budget - used) / n
            break
    return found / P


def effort_for_recall(rows, pred, target):
    """Expected fraction of the ranked list that must be reviewed to reach `target` recall of CHANGED pairs."""
    N = len(rows)
    P = sum(r["label"] for r in rows)
    need = target * P
    found = used = 0.0
    for n, c in ranked_groups(rows, pred):
        if found + c >= need:
            frac_in_group = (need - found) / c if c else 0.0
            return (used + frac_in_group * n) / N
        found += c
        used += n
    return 1.0


def at_frozen_threshold(rows, pred, thr):
    tp = sum(1 for r in rows if r["label"] == 1 and r["scores"][pred] > thr)
    fn = sum(1 for r in rows if r["label"] == 1 and r["scores"][pred] <= thr)
    fp = sum(1 for r in rows if r["label"] == 0 and r["scores"][pred] > thr)
    tn = sum(1 for r in rows if r["label"] == 0 and r["scores"][pred] <= thr)
    return {"threshold": thr, "TP": tp, "FN": fn, "FP": fp, "TN": tn,
            "sensitivity": tp / (tp + fn), "false_positive_rate": fp / (fp + tn),
            "flagged_fraction": (tp + fp) / len(rows)}


def metrics(rows, thr):
    out = {}
    for p in PRED:
        out[p] = {
            "recall_at_budget": {str(b): recall_at_budget(rows, p, b) for b in BUDGETS},
            "effort_for_recall": {str(t): effort_for_recall(rows, p, t) for t in RECALL_TARGETS},
        }
        if p in thr and p == "sbg_v5":
            out[p]["at_frozen_train_youden_threshold"] = at_frozen_threshold(rows, p, thr[p])
    return out


def boot(rows, key_fn, n=NBOOT, seed=SEED):
    by = collections.defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(r)
    progs = sorted(by)
    rng = random.Random(seed)
    draws = []
    for _ in range(n):
        s = [x for p in (rng.choice(progs) for _ in progs) for x in by[p]]
        draws.append(key_fn(s))
    draws.sort()
    return [draws[int(0.025 * n)], draws[int(0.975 * n) - 1]]


def run(name, rows, thr):
    res = {"n_pairs": len(rows), "n_programs": len({r["base_id"] for r in rows}),
           "n_changed": sum(r["label"] for r in rows), "point": metrics(rows, thr), "ci95": {}}
    for p in PRED:
        res["ci95"][p] = {
            "recall_at_budget": {str(b): boot(rows, lambda s, p=p, b=b: recall_at_budget(s, p, b)) for b in BUDGETS},
            "effort_for_recall": {str(t): boot(rows, lambda s, p=p, t=t: effort_for_recall(s, p, t)) for t in RECALL_TARGETS},
        }
    # paired differences (SBG V5 minus edit; SBG V5 minus M_EX) on recall@25% and effort@80%
    res["paired_diff_ci95"] = {}
    for other in ("edit", "M_EX"):
        res["paired_diff_ci95"][f"sbg_v5_minus_{other}"] = {
            "recall_at_0.25": {"point": recall_at_budget(rows, "sbg_v5", .25) - recall_at_budget(rows, other, .25),
                               "ci95": boot(rows, lambda s, o=other: recall_at_budget(s, "sbg_v5", .25) - recall_at_budget(s, o, .25))},
            "effort_for_recall_0.8": {"point": effort_for_recall(rows, "sbg_v5", .8) - effort_for_recall(rows, other, .8),
                                      "ci95": boot(rows, lambda s, o=other: effort_for_recall(s, "sbg_v5", .8) - effort_for_recall(s, o, .8))},
        }
    return res


def miss_profile(rows):
    """Which CHANGED pairs would be missed by the frozen 'any non-zero SBG V5' rule?  (counts by SC family)."""
    miss = collections.Counter(); tot = collections.Counter()
    for r in rows:
        if r["label"] == 1:
            fam = (r.get("sc_type") or r.get("transformation_type") or "?")
            tot[fam] += 1
            if r["scores"]["sbg_v5"] <= 7.955e-05:
                miss[fam] += 1
    return {k: {"changed": tot[k], "missed_by_sbg_v5_threshold": miss[k]} for k in sorted(tot)}


def main():
    thr = json.loads(C.V10_MODELS.read_text())["thresholds_youden_train"]
    pop10, _ = C.load_v10_population()
    pop9 = C.load_v9c_population("val")
    out = {"artifact": "PRACTICAL_SIGNIFICANCE_ANALYSIS", "status": "EXPLORATORY post-hoc, no fitted model, frozen predictors",
           "seed": SEED, "n_bootstrap": NBOOT, "budgets": BUDGETS, "recall_targets": RECALL_TARGETS,
           "v10": run("v10", pop10, thr), "v9c_val": run("v9c_val", pop9, thr),
           "v10_miss_profile_by_sc_family": miss_profile(pop10)}
    (C.OUT / "PRACTICAL_SIGNIFICANCE_ANALYSIS.json").write_text(json.dumps(out, indent=1, default=str))
    for ds in ("v10", "v9c_val"):
        d = out[ds]
        print(ds, d["n_pairs"], "pairs", d["n_programs"], "programs")
        for p in PRED:
            rb, ef = d["point"][p]["recall_at_budget"], d["point"][p]["effort_for_recall"]
            print(f"  {p:8s} recall@10/25/50% = {rb['0.1']:.3f} {rb['0.25']:.3f} {rb['0.5']:.3f} | effort for 50/80/95% recall = {ef['0.5']:.3f} {ef['0.8']:.3f} {ef['0.95']:.3f}")
        print("  frozen threshold:", d["point"]["sbg_v5"]["at_frozen_train_youden_threshold"])
        print("  paired:", json.dumps(d["paired_diff_ci95"], default=str)[:600])


if __name__ == "__main__":
    main()

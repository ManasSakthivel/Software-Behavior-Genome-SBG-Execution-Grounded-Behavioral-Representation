#!/usr/bin/env python3
"""Controlled DEVELOPMENT experiment: SBG V5 vs V5-corrected (none needed) vs EXPERIMENTAL V6-graded, with all required baselines.

Population: v9c matched-complete sets (evaluate_v9.matched_complete) -- identical eligibility rule for every predictor.
Models are fitted on v9c TRAIN only (fit_weights.fit_logistic, same as V9), evaluated on DEV (exploratory/development; nothing is fitted on dev).
v9c VAL and the v8 test split are not read.  Thresholds are chosen on TRAIN (Youden J on the predictor's own train scores), applied to DEV.

    python experiments/final/evaluate_v4_dev.py            -> artifacts/paper_evidence/V4_DEV_EVALUATION.json
Requires artifacts/final/pairs_v9c_{train,dev}_v6exp.jsonl (score_v6_experimental.py).
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
import evaluate_v9 as e                                                         # noqa: E402
from sbg.statistics import auroc, holm_bonferroni                                # noqa: E402

ART, EV = e.ART, e.EV
OUT = EV / "V4_DEV_EVALUATION.json"
SBG_FEATS = {"V5": "sbg_v5", "V6": "sbg_v6"}
EXEC = ["exception_fraction", "call_count", "coverage_size"]
STATIC = ["static_ast", "static_token"]
MODELS = {                                              # pre-declared; features exist for every pair
    "E": ["edit"], "X": EXEC, "ST": STATIC, "EX": ["edit"] + EXEC, "EST": ["edit"] + STATIC,
    "E+V5": ["edit", "sbg_v5"], "E+V6": ["edit", "sbg_v6"],
    "EX+V5": ["edit", "sbg_v5"] + EXEC, "EX+V6": ["edit", "sbg_v6"] + EXEC,
    "EX+V5+V6": ["edit", "sbg_v5", "sbg_v6"] + EXEC}
SINGLE = ["sbg_v5", "sbg_v6", "sbg_state", "sbg_state_v6", "edit"] + EXEC + STATIC


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def population(split):
    rows = e.load("v9c", split)
    v6 = {r["pair_id"]: r for r in e.jl(ART / f"pairs_v9c_{split}_v6exp.jsonl")}
    for r in rows:
        q = v6.get(r["pair_id"])
        if r["evaluated"]:
            assert q and q["evaluated"], r["pair_id"]
            for k in ("sbg_v5", "sbg_state"):                                    # V5 re-derived == frozen scored file
                assert q["scores"][k] == r["scores"][k], (r["pair_id"], k)
            r["scores"]["sbg_v6"], r["scores"]["sbg_state_v6"] = q["sbg_v6"], q["sbg_state_v6"]
    return rows, e.matched_complete(rows)


def pr_auc(scores, labels):
    """Average precision with tie handling (all items tied at a score enter together)."""
    pairs = sorted(zip(scores, labels), key=lambda t: -t[0])
    P = sum(labels)
    tp = fp = 0
    ap = prev_recall = 0.0
    i = 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        for _, y in pairs[i:j]:
            tp += y
            fp += 1 - y
        recall = tp / P
        ap += (recall - prev_recall) * (tp / (tp + fp))
        prev_recall = recall
        i = j
    return ap


def youden_threshold(scores, labels):
    best, thr = -1.0, None
    P, N = sum(labels), len(labels) - sum(labels)
    for t in sorted(set(scores)):
        tpr = sum(1 for s, y in zip(scores, labels) if y and s >= t) / P
        fpr = sum(1 for s, y in zip(scores, labels) if not y and s >= t) / N
        if tpr - fpr > best:
            best, thr = tpr - fpr, t
    return thr


def sens_spec(scores, labels, thr):
    P, N = sum(labels), len(labels) - sum(labels)
    return (round(sum(1 for s, y in zip(scores, labels) if y and s >= thr) / P, 4),
            round(sum(1 for s, y in zip(scores, labels) if not y and s < thr) / N, 4))


def block(pop, tr_pop, pred):
    s, y, c = e.vec(pop, pred)
    ts, ty, _ = e.vec(tr_pop, pred)
    thr = youden_threshold(ts, ty)
    sen, spe = sens_spec(s, y, thr)
    zc = [r["scores"][pred] == 0 for r in pop if r["label"] == 1]
    ze = [r["scores"][pred] == 0 for r in pop if r["label"] == 0]
    return {"auroc": round(auroc(s, y), 6), "ci95_cluster_bootstrap": e.ci(s, y, c), "pr_auc": round(pr_auc(s, y), 6),
            "train_chosen_threshold_youden": thr, "sensitivity": sen, "specificity": spe,
            "exact_zero_rate": round(sum(1 for r in pop if r["scores"][pred] == 0) / len(pop), 4),
            "exact_zero_rate_changed": round(sum(zc) / len(zc), 4), "exact_zero_rate_equivalent": round(sum(ze) / len(ze), 4)}


def by_family(pop, pred):
    out = {}
    for fam in sorted({r["transformation_type"].split("+")[0] for r in pop if r["label"] == 1}):
        ch = [r for r in pop if r["label"] == 1 and r["transformation_type"].startswith(fam)]
        out[fam] = {"n_changed": len(ch), "zero_rate": round(sum(1 for r in ch if r["scores"][pred] == 0) / len(ch), 4),
                    "median": sorted(r["scores"][pred] for r in ch)[len(ch) // 2]}
    return out


def main():
    rows_tr, tr = population("train")
    rows_dv, dv = population("dev")
    X = lambda rows, feats: [[r["scores"][f] for f in feats] for r in rows]       # noqa: E731
    ytr = [r["label"] for r in tr]
    models = {n: {"features": f, **e.fit_logistic(X(tr, f), ytr)} for n, f in MODELS.items()}
    frozen = json.loads(e.MODELS_FILE.read_text())["models"]
    consistency = {"ESX(V9 frozen) == EX+V5 refit: max |weight diff|": max(
        abs(a - b) for a, b in zip(frozen["ESX"]["weights_standardised"], models["EX+V5"]["weights_standardised"]))}
    for pop in (tr, dv):
        for r in pop:
            for n, m in models.items():
                r["scores"][f"M_{n}"] = e.lin_score(m, m["features"], r["scores"])
    preds = SINGLE + [f"M_{n}" for n in MODELS]
    res = {"artifact": "V4_DEV_EVALUATION",
           "status": "EXPLORATORY / DEVELOPMENT. Models fitted on v9c train; evaluated on v9c dev; thresholds from train. NOT confirmatory; v9c val and v8 test not read.",
           "sources": {f"v9c_{s}_v6exp": {"path": f"artifacts/final/pairs_v9c_{s}_v6exp.jsonl", "sha256": sha(ART / f"pairs_v9c_{s}_v6exp.jsonl")} for s in ("train", "dev")},
           "v6_module_sha256": sha(REPO / "sbg/v6/state_transition_genome_v6.py"),
           "script_sha256": sha(__file__), "model_consistency_with_frozen_v9": consistency,
           "models_fitted_on_train": {n: {k: v for k, v in m.items()} for n, m in models.items()}}
    for tag, pop in (("dev", dv), ("train_in_sample", tr)):
        allr = rows_dv if tag == "dev" else rows_tr
        r = {"n_pairs": len(pop), "n_matched_sets": len(pop) // 2, "n_programs": len({x["base_id"] for x in pop}),
             "n_changed": sum(x["label"] for x in pop),
             "invalid_score_rate": round(sum(1 for x in allr if x["evaluated"] and x["scores"].get("sbg_v5") is not None and not (0 <= x["scores"]["sbg_v5"] <= 1)) / len(allr), 4),
             "unevaluated_pairs_in_file": sum(1 for x in allr if not x["evaluated"]),
             "predictors": {p: block(pop, tr, p) for p in preds}}
        # edit-reversed baseline (the published shortcut, orientation known from earlier splits)
        for x in pop:
            x["scores"]["edit_reversed"] = -x["scores"]["edit"]
        for x in tr:
            x["scores"]["edit_reversed"] = -x["scores"]["edit"]
        r["predictors"]["edit_reversed"] = block(pop, tr, "edit_reversed")
        d = lambda a, b: e.delta(e.vec(pop, a), e.vec(pop, b))                      # noqa: E731
        pairs = {"V6_minus_V5 (sbg)": ("sbg_v6", "sbg_v5"), "state_V6_minus_state_V5": ("sbg_state_v6", "sbg_state"),
                 "E+V5_minus_E": ("M_E+V5", "M_E"), "E+V6_minus_E": ("M_E+V6", "M_E"),
                 "EX+V5_minus_EX (H4-style, V5)": ("M_EX+V5", "M_EX"), "EX+V6_minus_EX (H4-style, V6)": ("M_EX+V6", "M_EX"),
                 "EX+V6_minus_EX+V5": ("M_EX+V6", "M_EX+V5"), "EX+V5+V6_minus_EX+V5": ("M_EX+V5+V6", "M_EX+V5"),
                 "V5_minus_edit_forward": ("sbg_v5", "edit"), "V6_minus_edit_forward": ("sbg_v6", "edit"),
                 "EX_minus_E": ("M_EX", "M_E"), "EX+V5_minus_X": ("M_EX+V5", "M_X"), "V5_minus_static_ast": ("sbg_v5", "static_ast")}
        dl = {k: d(*v) for k, v in pairs.items()}
        r["paired_deltas"] = dl
        r["paired_deltas_holm"] = holm_bonferroni({k: v["p_two_sided"] for k, v in dl.items()})
        r["edit_size_exact_stratified"] = {p: dict(zip(("auroc", "n_cross_label_comparisons"), e.strat(pop, p))) for p in ("sbg_v5", "sbg_v6", "edit")}
        r["matched_set_concordance"] = {p: e.matched_concordance(pop, p) for p in ("sbg_v5", "sbg_v6", "edit", "exception_fraction")}
        r["zero_rate_by_sc_family"] = {"sbg_v5": by_family(pop, "sbg_v5"), "sbg_v6": by_family(pop, "sbg_v6")}
        eq = collections.defaultdict(list)
        for x in pop:
            if x["label"] == 0:
                eq[x["transformation_type"]].append(x)
        r["zero_rate_by_sp_family_equivalent"] = {t: {"n": len(v), "sbg_v5": round(sum(1 for x in v if x["scores"]["sbg_v5"] == 0) / len(v), 4),
                                                       "sbg_v6": round(sum(1 for x in v if x["scores"]["sbg_v6"] == 0) / len(v), 4)} for t, v in sorted(eq.items())}
        # rescued CHANGED zeros
        zc = [x for x in pop if x["label"] == 1 and x["scores"]["sbg_v5"] == 0]
        r["changed_v5_zero"] = {"n": len(zc), "v6_still_zero": sum(1 for x in zc if x["scores"]["sbg_v6"] == 0)}
        ze = [x for x in pop if x["label"] == 0 and x["scores"]["sbg_v5"] == 0]
        r["equivalent_v5_zero"] = {"n": len(ze), "v6_still_zero": sum(1 for x in ze if x["scores"]["sbg_v6"] == 0)}
        per = {}
        for p in sorted({x["base_id"] for x in pop}):
            ps = [x for x in pop if x["base_id"] == p]
            yy = [x["label"] for x in ps]
            per[p] = {"n": len(ps), **{k: round(auroc([x["scores"][k] for x in ps], yy), 4) for k in ("sbg_v5", "sbg_v6", "edit", "M_EX", "M_EX+V5", "M_EX+V6")}}
        r["per_program_auroc"] = per
        res[tag] = r
    OUT.write_text(json.dumps(res, indent=2, default=str) + "\n")
    d = res["dev"]
    print("DEV n_pairs", d["n_pairs"], "programs", d["n_programs"])
    for p in ("sbg_v5", "sbg_v6", "sbg_state", "sbg_state_v6", "edit", "edit_reversed", "M_X", "M_ST", "M_E", "M_EX", "M_E+V5", "M_E+V6", "M_EX+V5", "M_EX+V6"):
        b = d["predictors"][p]
        print(f"  {p:14s} AUROC {b['auroc']:.4f} {b['ci95_cluster_bootstrap']} PR {b['pr_auc']:.3f} zero {b['exact_zero_rate']:.3f} sens {b['sensitivity']} spec {b['specificity']}")
    for k, v in d["paired_deltas"].items():
        print(f"  Δ {k:36s} {v['delta']:+.4f} [{v['ci_lower']:+.4f},{v['ci_upper']:+.4f}] p={v['p_two_sided']}")
    print("  changed zeros", d["changed_v5_zero"], "equiv zeros", d["equivalent_v5_zero"])
    print("  consistency", consistency)


if __name__ == "__main__":
    main()

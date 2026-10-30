#!/usr/bin/env python3
"""v10 independent evaluation (single run, frozen before scoring).

  python evaluate_v10.py fit      # fit logistic models on v9c TRAIN only (matched-complete)     -> artifacts/final/V10_MODELS_FROZEN.json
  python evaluate_v10.py run      # REFUSES unless FREEZE_V10.json pins script, models, dataset, scorer and the scored file; single run
                                  #                                                            -> artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json

Population: benchmark/datasets/v10_independent (19 programs never in any v8/v9 split; labels validated by a dynamic oracle).
Primary population = matched sets (EQ, CH) in which both members were evaluated.  Cluster = base program.
Pre-declared hypothesis family (Holm over H1-H6):
  H1 AUROC(sbg_v5) > 0.5 (cluster permutation, one-sided)
  H2 AUROC(M_E+V5) - AUROC(M_E)        H3 AUROC(sbg_v5) - AUROC(edit forward)
  H4 AUROC(M_EX+V5) - AUROC(M_EX)      H5 AUROC(sbg_v6) - AUROC(sbg_v5)       H6 AUROC(M_EX+V6) - AUROC(M_EX)
Thresholds: Youden on v9c TRAIN scores per predictor, applied unchanged.  No quantity here is chosen from v10 scores.
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
import evaluate_v9 as e                                                                  # noqa: E402
import evaluate_v4_dev as d4                                                             # noqa: E402
from edit_size_analysis import _edit_size                                                # noqa: E402
from static_baselines import token_multiset, ast_multiset, multiset_distance             # noqa: E402
from sbg.statistics import auroc, cluster_permutation_p, holm_bonferroni                 # noqa: E402

ART, EV = e.ART, e.EV
V10 = REPO / "benchmark" / "datasets" / "v10_independent"
SCORED = ART / "pairs_v10_test_v6exp.jsonl"
MODELS = ART / "V10_MODELS_FROZEN.json"
FREEZE = ART / "FREEZE_V10.json"
OUT = EV / "V10_INDEPENDENT_EVALUATION.json"
sha = d4.sha


def stage_fit():
    if OUT.exists():
        raise SystemExit("REFUSED: v10 evaluation already exists")
    _, tr = d4.population("train")
    y = [r["label"] for r in tr]
    models = {n: {"features": f, **e.fit_logistic(d4_X(tr, f), y)} for n, f in d4.MODELS.items()}
    thr = {}
    for r in tr:
        r["scores"]["edit_reversed"] = -r["scores"]["edit"]
    for p in d4.SINGLE + ["edit_reversed"]:
        s, yy, _ = e.vec(tr, p)
        thr[p] = d4.youden_threshold(s, yy)
    for r in tr:
        for n, m in models.items():
            r["scores"][f"M_{n}"] = e.lin_score(m, m["features"], r["scores"])
    for n in models:
        s, yy, _ = e.vec(tr, f"M_{n}")
        thr[f"M_{n}"] = d4.youden_threshold(s, yy)
    MODELS.write_text(json.dumps({"artifact": "V10_MODELS_FROZEN", "fitted_on": {"design": "v9c", "split": "train", "population": "matched-complete",
                                  "n_pairs": len(tr), "n_programs": len({r['base_id'] for r in tr}),
                                  "scored_v6exp_sha256": sha(ART / "pairs_v9c_train_v6exp.jsonl")},
                                  "fit": "fit_weights.fit_logistic (L2=1.0, lr=0.5, 5000 its, standardised); logit scores",
                                  "models": models, "thresholds_youden_train": thr}, indent=2) + "\n")
    print("fitted", list(models), "->", MODELS.relative_to(REPO))


def d4_X(rows, feats):
    return [[r["scores"][f] for f in feats] for r in rows]


def check_freeze():
    if not FREEZE.exists():
        raise SystemExit("REFUSED: FREEZE_V10.json missing")
    fz = json.loads(FREEZE.read_text())
    want = fz["sha256"]
    bad = [k for k, p in {"experiments/final/evaluate_v10.py": __file__, "experiments/final/evaluate_v4_dev.py": d4.__file__,
                          "experiments/final/evaluate_v9.py": e.__file__,
                          "artifacts/final/V10_MODELS_FROZEN.json": MODELS, "benchmark/datasets/v10_independent/pairs_test.jsonl": V10 / "pairs_test.jsonl",
                          "benchmark/datasets/v10_independent/manifest.json": V10 / "manifest.json",
                          "sbg/v6/state_transition_genome_v6.py": REPO / "sbg/v6/state_transition_genome_v6.py",
                          "experiments/final/score_v6_experimental.py": REPO / "experiments/final/score_v6_experimental.py",
                          "experiments/final/extraction.py": REPO / "experiments/final/extraction.py"}.items() if want.get(k) != sha(p)]
    if bad:
        raise SystemExit("REFUSED: hash mismatch vs FREEZE_V10.json: " + ", ".join(bad))
    sc = ART / "FREEZE_V10_SCORED.json"        # written AFTER scoring, BEFORE this evaluation; pins the scored file
    if not sc.exists() or json.loads(sc.read_text())["scored_file_sha256"] != sha(SCORED):
        raise SystemExit("REFUSED: FREEZE_V10_SCORED.json missing or scored file differs")
    return fz


def stage_run():
    fz = check_freeze()
    if OUT.exists():
        raise SystemExit("REFUSED: single-run evaluation already written")
    mf = json.loads(MODELS.read_text())
    models, thr = mf["models"], mf["thresholds_youden_train"]
    meta = {m["pair_id"]: m for m in e.jl(V10 / "pairs_test.jsonl")}
    scored = {r["pair_id"]: r for r in e.jl(SCORED)}
    rows, cache = [], {}
    for pid, m in meta.items():
        r = scored[pid]
        if not r["evaluated"]:
            rows.append({"pair_id": pid, "evaluated": False, "base_id": m["base_id"], "failure": r.get("failure")})
            continue
        sc = dict(r["scores"])
        sc["sbg_v6"], sc["sbg_state_v6"] = r["sbg_v6"], r["sbg_state_v6"]
        sc["edit"] = float(_edit_size(m["base_path"], m["variant_path"]))
        for pth in (m["base_path"], m["variant_path"]):
            if pth not in cache:
                src = (REPO / pth).read_text()
                cache[pth] = (token_multiset(src), ast_multiset(src))
        sc["static_token"] = multiset_distance(cache[m["base_path"]][0], cache[m["variant_path"]][0])
        sc["static_ast"] = multiset_distance(cache[m["base_path"]][1], cache[m["variant_path"]][1])
        rows.append({"pair_id": pid, "evaluated": True, "base_id": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
                     "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"],
                     "transformation_type": m["transformation_type"], "_edit": int(sc["edit"]), "scores": sc})
    ok = collections.defaultdict(list)
    for r in rows:
        if r["evaluated"]:
            ok[r["group"]].append(r)
    pop = [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]
    for r in pop:
        r["scores"]["edit_reversed"] = -r["scores"]["edit"]
        for n, m in models.items():
            r["scores"][f"M_{n}"] = e.lin_score(m, m["features"], r["scores"])
    y = [r["label"] for r in pop]
    preds = d4.SINGLE + ["edit_reversed"] + [f"M_{n}" for n in models]
    res = {"artifact": "V10_INDEPENDENT_EVALUATION",
           "status": "CONFIRMATORY-BY-FREEZE for the pre-declared hypotheses H1-H6 (single run; dataset, models, scorer, script frozen in FREEZE_V10.json before any v10 pair was scored). "
                     "V6 arm is EXPERIMENTAL. Independence caveat: the 19 programs are unseen but algorithmic siblings of development programs (novelty-excluded from v8 by token-Jaccard 0.10-0.15).",
           "freeze_sha256": sha(FREEZE), "n_pairs_in_dataset": len(rows), "n_unevaluated": sum(1 for r in rows if not r["evaluated"]),
           "n_pairs": len(pop), "n_matched_sets": len(pop) // 2, "n_programs": len({r["base_id"] for r in pop}), "n_changed": sum(y), "n_equivalent": len(y) - sum(y),
           "per_program_counts": {p: sum(1 for r in pop if r["base_id"] == p) for p in sorted({r["base_id"] for r in pop})},
           "mean_edit": {n: round(sum(r["_edit"] for r in pop if r["label"] == l) / sum(1 for r in pop if r["label"] == l), 3) for n, l in (("CHANGED", 1), ("EQUIVALENT", 0))}}
    P = {}
    for p in preds:
        s, yy, cc = e.vec(pop, p)
        sen, spe = d4.sens_spec(s, yy, thr[p]) if p in thr else (None, None)
        P[p] = {"auroc": round(auroc(s, yy), 6), "ci95_cluster_bootstrap": e.ci(s, yy, cc), "pr_auc": round(d4.pr_auc(s, yy), 6),
                "train_threshold": thr.get(p), "sensitivity": sen, "specificity": spe,
                "exact_zero_rate": round(sum(1 for v in s if v == 0) / len(s), 4),
                "exact_zero_rate_changed": round(sum(1 for r in pop if r["label"] == 1 and r["scores"][p] == 0) / sum(y), 4),
                "exact_zero_rate_equivalent": round(sum(1 for r in pop if r["label"] == 0 and r["scores"][p] == 0) / (len(y) - sum(y)), 4)}
    sv = e.vec(pop, "sbg_v5")
    P["sbg_v5"]["permutation_p_one_sided_vs_0.5"] = round(cluster_permutation_p(sv[0], sv[1], sv[2], n_permutations=e.NBOOT, seed=e.SEED), 6)
    res["predictors"] = P
    D = lambda a, b: e.delta(e.vec(pop, a), e.vec(pop, b))                                # noqa: E731
    dl = {"H2_E+V5_minus_E": D("M_E+V5", "M_E"), "H3_V5_minus_edit_forward": D("sbg_v5", "edit"), "H4_EX+V5_minus_EX": D("M_EX+V5", "M_EX"),
          "H5_V6_minus_V5": D("sbg_v6", "sbg_v5"), "H6_EX+V6_minus_EX": D("M_EX+V6", "M_EX")}
    ps = {"H1_sbg_v5_above_chance": P["sbg_v5"]["permutation_p_one_sided_vs_0.5"], **{k: v["p_two_sided"] for k, v in dl.items()}}
    res["pre_declared_tests"] = {"deltas": dl, "holm": holm_bonferroni(ps)}
    res["supplementary_deltas_not_in_holm_family"] = {k: D(*v) for k, v in {
        "V5_minus_edit_reversed": ("sbg_v5", "edit_reversed"), "V5_minus_exception_fraction": ("sbg_v5", "exception_fraction"),
        "V5_minus_static_ast": ("sbg_v5", "static_ast"), "V5_minus_static_token": ("sbg_v5", "static_token"),
        "EX_minus_E": ("M_EX", "M_E"), "state_V6_minus_state_V5": ("sbg_state_v6", "sbg_state"), "E+V6_minus_E": ("M_E+V6", "M_E"),
        "EX+V6_minus_EX+V5": ("M_EX+V6", "M_EX+V5")}.items()}
    res["edit_size_exact_stratified"] = {p: dict(zip(("auroc", "n_cross_label_comparisons"), e.strat(pop, p))) for p in ("sbg_v5", "sbg_v6", "edit")}
    res["matched_set_concordance"] = {p: e.matched_concordance(pop, p) for p in ("sbg_v5", "sbg_v6", "edit", "exception_fraction")}
    per = {}
    for p in sorted({r["base_id"] for r in pop}):
        ps_ = [r for r in pop if r["base_id"] == p]
        yy = [r["label"] for r in ps_]
        per[p] = {"n": len(ps_), **{k: round(auroc([r["scores"][k] for r in ps_], yy), 4) for k in ("sbg_v5", "sbg_v6", "edit", "M_EX")}}
    res["per_program_auroc"] = per
    fam = collections.defaultdict(list)
    for r in pop:
        if r["label"] == 1:
            fam[r["transformation_type"].split("+")[0]].append(r)
    res["changed_zero_rate_by_sc_family"] = {k: {"n": len(v), "sbg_v5": round(sum(1 for r in v if r["scores"]["sbg_v5"] == 0) / len(v), 4),
                                                 "sbg_v6": round(sum(1 for r in v if r["scores"]["sbg_v6"] == 0) / len(v), 4)} for k, v in sorted(fam.items())}
    eq = collections.defaultdict(list)
    for r in pop:
        if r["label"] == 0:
            eq[r["transformation_type"]].append(r)
    res["equivalent_zero_rate_by_sp_family"] = {k: {"n": len(v), "sbg_v5": round(sum(1 for r in v if r["scores"]["sbg_v5"] == 0) / len(v), 4),
                                                    "median_sbg_v5": sorted(r["scores"]["sbg_v5"] for r in v)[len(v) // 2]} for k, v in sorted(eq.items())}
    OUT.write_text(json.dumps(res, indent=2, default=str) + "\n")
    print(f"v10: {res['n_pairs']} pairs, {res['n_matched_sets']} matched sets, {res['n_programs']} programs; unevaluated {res['n_unevaluated']}")
    for p in ("sbg_v5", "sbg_v6", "sbg_state", "edit", "edit_reversed", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token", "M_E", "M_EX", "M_E+V5", "M_EX+V5", "M_EX+V6"):
        b = P[p]
        print(f"  {p:18s} AUROC {b['auroc']:.4f} {b['ci95_cluster_bootstrap']} PR {b['pr_auc']:.3f} zero {b['exact_zero_rate']:.3f}")
    for k, v in dl.items():
        print(f"  Δ {k:28s} {v['delta']:+.4f} [{v['ci_lower']:+.4f},{v['ci_upper']:+.4f}] p={v['p_two_sided']}")
    print("  H1 p", ps["H1_sbg_v5_above_chance"], " Holm:", {k: (v["adjusted_p"] if "adjusted_p" in v else v) for k, v in res["pre_declared_tests"]["holm"].items()})


if __name__ == "__main__":
    {"fit": stage_fit, "run": stage_run}[sys.argv[1]]()

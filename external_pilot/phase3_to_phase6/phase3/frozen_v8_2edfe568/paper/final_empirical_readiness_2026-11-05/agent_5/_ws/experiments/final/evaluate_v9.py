#!/usr/bin/env python3
"""
experiments/final/evaluate_v9.py  --  controlled (edit-size-decoupled) evaluation, FROZEN before the val run.

Design: docs/current/EVALUATION_PLAN_V9.md.  Population = benchmark/datasets/v9_composed (each v8 EQUIVALENT pair reused verbatim +
one composed CHANGED partner SP_t,s(SC_k(p)) compared with the ORIGINAL program p).  Secondary population = v8 (original design).

  python evaluate_v9.py fit                 # fit the logistic models on v9c TRAIN only            -> artifacts/final/V9_MODELS_FROZEN.json
  python evaluate_v9.py run --split dev     # descriptive, exploratory                              -> artifacts/paper_evidence/V9_DEV_EVALUATION.json
  python evaluate_v9.py run --split train   # in-sample (descriptive only)                          -> V9_TRAIN_EVALUATION.json
  python evaluate_v9.py run --split val     # FINAL; refuses unless FREEZE_V9.json pins this script, the models and the scored files
                                            #                                                       -> V9_VAL_EVALUATION.json (never overwritten)

The test split is NOT touched by this script.  Stale-variant programs are excluded by name (DIAGNOSTIC_V8_STALE_VARIANTS.json).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import random
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
from sbg.statistics import (auroc, cluster_bootstrap_ci, cluster_permutation_p, holm_bonferroni,    # noqa: E402
                            paired_cluster_bootstrap_delta)
from edit_size_analysis import _edit_size                                                            # noqa: E402
from fit_weights import fit_logistic, score as lin_score                                             # noqa: E402

ART = REPO / "artifacts" / "final"
EV = REPO / "artifacts" / "paper_evidence"
V9 = REPO / "benchmark" / "datasets" / "v9_composed"
V8 = REPO / "benchmark" / "datasets" / "v8"
AUDIT9 = ART / "BENCHMARK_VALIDITY_AUDIT_V9C.json"
AUDIT8 = ART / "BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json"
MODELS_FILE = ART / "V9_MODELS_FROZEN.json"
FREEZE = ART / "FREEZE_V9.json"
STALE = {s["program"] for s in json.loads((EV / "DIAGNOSTIC_V8_STALE_VARIANTS.json").read_text())["stale_programs"]}
PAIRS9 = {s: ART / f"pairs_v9c_{s}_output_free_v8.jsonl" for s in ("train", "dev", "val")}
PAIRS8 = {"train": ART / "pairs_v8train_output_free_v8.jsonl", "dev": ART / "pairs_v8devrescore_output_free_v8.jsonl",
          "val": ART / "pairs_v8val_output_free_v8.jsonl"}
OUT = {s: EV / f"V9_{s.upper()}_EVALUATION.json" for s in ("train", "dev", "val")}
SEED, NBOOT = 42, 2000

# Pre-declared model family (features are all available for every pair; none uses labels or the pair's group).
MODELS = {"E": ["edit"], "ES": ["edit", "sbg_v5"], "EX": ["edit", "exception_fraction", "call_count", "coverage_size"],
          "ESX": ["edit", "sbg_v5", "exception_fraction", "call_count", "coverage_size"],
          "E+v3": ["edit", "sbg_v3"], "E+temporal": ["edit", "sbg_temporal"], "E+state": ["edit", "sbg_state"]}
SINGLE = ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token")
EXEC_BASELINES = ("exception_fraction", "call_count", "coverage_size", "static_ast", "static_token")


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def load(design, split):
    """Scored rows with `_valid`, `edit`; adds `group` (matched-set id) for v9c."""
    if design == "v9c":
        # CHANGED partners come from the v9c file; the EQUIVALENT members are the v8 EQUIVALENT pairs, reused verbatim
        # (their scores come from the v8 scored file -- same pair, same variant file, same scorer).
        meta = {m["pair_id"]: m for m in jl(V9 / f"pairs_{split}.jsonl")}
        v8meta = {m["pair_id"]: m for m in jl(V8 / f"pairs_{split}.jsonl")}
        wanted = {m["matched_equivalent_pair_id"] for m in meta.values()}
        meta.update({k: v8meta[k] for k in wanted})
        rows = jl(PAIRS9[split]) + [r for r in jl(PAIRS8[split]) if r["pair_id"] in wanted]
        audit = {r["pair_id"]: r for r in json.loads(AUDIT9.read_text())["pairs"] if r["split"] == split}
        audit.update({r["pair_id"]: r for r in json.loads(AUDIT8.read_text())["pairs"] if r["split"] == split and r["pair_id"] in wanted})
    else:
        meta = {m["pair_id"]: m for m in jl(V8 / f"pairs_{split}.jsonl")}
        rows = jl(PAIRS8[split])
        audit = {r["pair_id"]: r for r in json.loads(AUDIT8.read_text())["pairs"] if r["split"] == split}
    out = []
    for r in rows:
        if r["base_id"] in STALE:
            continue
        m = meta[r["pair_id"]]
        r["label"] = int(m["semantic_relation"] == "CHANGED")
        v = audit.get(r["pair_id"])
        r["_valid"] = bool(r["evaluated"] and v and v.get("status") == "ok" and (r["label"] == 0 or v.get("observable") is True))
        r["group"] = m.get("matched_equivalent_pair_id") if r["label"] else r["pair_id"]
        if r["evaluated"]:
            r["_edit"] = _edit_size(m["base_path"], m["variant_path"])
            r["scores"]["edit"] = float(r["_edit"])
        out.append(r)
    return out


def matched_complete(rows):
    """v9c primary population: matched sets (EQUIVALENT + its composed CHANGED) in which BOTH members are valid."""
    ok = collections.defaultdict(list)
    for r in rows:
        if r["_valid"]:
            ok[r["group"]].append(r)
    return [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]


def vec(rows, p):
    return [r["scores"][p] for r in rows], [r["label"] for r in rows], [r["base_id"] for r in rows]


def fit_models(rows):
    out = {}
    y = [r["label"] for r in rows]
    for name, feats in MODELS.items():
        X = [[r["scores"][f] for f in feats] for r in rows]
        out[name] = {"features": feats, **fit_logistic(X, y)}
    return out


def attach_model_scores(rows, models):
    for r in rows:
        for name, m in models.items():
            r["scores"][f"M_{name}"] = lin_score(m, m["features"], r["scores"])


def ci(s, y, c):
    lo, hi, _ = cluster_bootstrap_ci(s, y, c, n_bootstrap=NBOOT, seed=SEED)
    return [lo, hi]


def delta(a, b):
    return paired_cluster_bootstrap_delta(a[0], b[0], a[1], a[2], n_bootstrap=NBOOT, seed=SEED)


def strat(rows, pred):
    g = collections.defaultdict(lambda: ([], []))
    for r in rows:
        g[r["_edit"]][r["label"]].append(r["scores"][pred])
    num = den = 0.0
    for neg, pos in g.values():
        for a in pos:
            for b in neg:
                num += 1.0 if a > b else .5 if a == b else 0.0
        den += len(pos) * len(neg)
    return (round(num / den, 6) if den else None), den


def matched_concordance(rows, pred, n=NBOOT):
    """Within each matched set: P(score(CHANGED partner) > score(EQUIVALENT partner)), ties 0.5; program-cluster bootstrap."""
    g = collections.defaultdict(dict)
    for r in rows:
        g[r["group"]][r["label"]] = r
    sets = [(v[1]["base_id"], (1.0 if v[1]["scores"][pred] > v[0]["scores"][pred] else .5 if v[1]["scores"][pred] == v[0]["scores"][pred] else 0.0))
            for v in g.values() if 0 in v and 1 in v]
    by = collections.defaultdict(list)
    for b, c in sets:
        by[b].append(c)
    ks, rng, vals = sorted(by), random.Random(SEED), []
    for _ in range(n):
        s = [c for k in (rng.choice(ks) for _ in ks) for c in by[k]]
        vals.append(sum(s) / len(s))
    vals.sort()
    return {"concordance": round(sum(c for _, c in sets) / len(sets), 6), "n_matched_sets": len(sets),
            "ci95_cluster_bootstrap": [round(vals[int(.025 * n)], 6), round(vals[int(.975 * n) - 1], 6)]}


def evaluate_v9c(rows, models):
    pop = matched_complete(rows)
    attach_model_scores(pop, models)
    y = [r["label"] for r in pop]
    res = {"population": "matched-complete v9c sets (both members valid)", "n_pairs": len(pop), "n_matched_sets": len(pop) // 2,
           "n_programs": len({r["base_id"] for r in pop}), "n_changed": sum(y), "n_equivalent": len(y) - sum(y)}
    pred = {}
    for p in SINGLE + tuple(f"M_{m}" for m in MODELS) + ("edit",):
        s, yy, cc = vec(pop, p)
        pred[p] = {"auroc": round(auroc(s, yy), 6), "ci95_cluster_bootstrap": ci(s, yy, cc)}
    ne = [-r["scores"]["edit"] for r in pop]
    pred["edit_reversed"] = {"auroc": round(auroc(ne, y), 6), "ci95_cluster_bootstrap": ci(ne, y, [r["base_id"] for r in pop])}
    sv = vec(pop, "sbg_v5")
    pred["sbg_v5"]["permutation_p_one_sided_vs_0.5"] = round(cluster_permutation_p(sv[0], sv[1], sv[2], n_permutations=NBOOT, seed=SEED), 6)
    res["predictors"] = pred
    # ---- pre-declared hypothesis family (Holm over H1..H4) ----
    d2 = delta(vec(pop, "M_ES"), vec(pop, "M_E"))
    d3 = delta(vec(pop, "sbg_v5"), vec(pop, "edit"))
    d4 = delta(vec(pop, "M_ESX"), vec(pop, "M_EX"))
    H = {"H1_sbg_v5_above_chance": pred["sbg_v5"]["permutation_p_one_sided_vs_0.5"],
         "H2_edit_plus_sbg_minus_edit": d2["p_two_sided"], "H3_sbg_v5_minus_edit_forward": d3["p_two_sided"],
         "H4_edit_exec_plus_sbg_minus_edit_exec": d4["p_two_sided"]}
    holm = holm_bonferroni(H)
    res["pre_declared_tests"] = {
        "H1": {"what": "AUROC(sbg_v5) > 0.5 (cluster permutation, one-sided)", "auroc": pred["sbg_v5"]["auroc"], "p": H["H1_sbg_v5_above_chance"]},
        "H2": {"what": "incremental value of SBG beyond edit size: AUROC(M_ES) - AUROC(M_E)", **d2},
        "H3": {"what": "sbg_v5 minus edit size (forward orientation, the better-oriented shortcut on this design)", **d3},
        "H4": {"what": "SBG beyond edit size AND execution shortcuts: AUROC(M_ESX) - AUROC(M_EX)", **d4},
        "holm": holm}
    res["verdict"] = {
        "sbg_above_chance_H1": bool(holm["H1_sbg_v5_above_chance"]["reject_at_alpha"]),
        "sbg_adds_information_beyond_edit_size_H2 (Holm reject and CI lower bound > 0)": bool(holm["H2_edit_plus_sbg_minus_edit"]["reject_at_alpha"] and d2["ci_lower"] > 0),
        "sbg_adds_beyond_edit_and_execution_shortcuts_H4": bool(holm["H4_edit_exec_plus_sbg_minus_edit_exec"]["reject_at_alpha"] and d4["ci_lower"] > 0),
        "sbg_beats_edit_size_alone_H3 (CI lower bound > 0)": bool(d3["ci_lower"] > 0)}
    # ---- secondary / descriptive ----
    res["paired_deltas_sbg_v5_minus"] = {p: delta(vec(pop, "sbg_v5"), vec(pop, p)) for p in ("sbg_v3", "sbg_temporal", "sbg_state") + EXEC_BASELINES + ("edit",)}
    res["paired_deltas_holm_over_baselines"] = holm_bonferroni({p: v["p_two_sided"] for p, v in res["paired_deltas_sbg_v5_minus"].items() if p in EXEC_BASELINES + ("edit",)})
    res["component_increments_over_edit_only_model"] = {m: delta(vec(pop, f"M_{m}"), vec(pop, "M_E")) for m in ("E+v3", "E+temporal", "E+state", "ES")}
    res["edit_size_exact_stratified"] = {p: dict(zip(("auroc", "n_cross_label_comparisons"), strat(pop, p))) for p in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state")}
    res["matched_set_concordance"] = {p: matched_concordance(pop, p) for p in ("sbg_v5", "edit", "sbg_state", "exception_fraction")}
    res["mean_edit_size"] = {nm: round(sum(r["_edit"] for r in pop if r["label"] == lab) / max(1, sum(1 for r in pop if r["label"] == lab)), 3)
                             for nm, lab in (("CHANGED", 1), ("EQUIVALENT", 0))}
    res["fraction_sbg_v5_exactly_zero"] = round(sum(1 for r in pop if r["scores"]["sbg_v5"] == 0) / len(pop), 4)
    per = {}
    for p in sorted({r["base_id"] for r in pop}):
        ps = [r for r in pop if r["base_id"] == p]
        yy = [r["label"] for r in ps]
        per[p] = {"n": len(ps), "sbg_v5": round(auroc([r["scores"]["sbg_v5"] for r in ps], yy), 4), "edit": round(auroc([r["scores"]["edit"] for r in ps], yy), 4)}
    res["per_program_auroc"] = per
    allv = [r for r in rows if r["_valid"]]
    res["selection_audit"] = {
        "all_pairs_in_file": len(rows), "evaluated": sum(r["evaluated"] for r in rows), "valid": len(allv), "matched_complete": len(pop),
        "dropped_by_matching_rule": len(allv) - len(pop),
        "failure_kinds": dict(collections.Counter(r.get("failure_kind") for r in rows if not r["evaluated"])),
        "mean_edit_all_valid_changed": round(sum(r["_edit"] for r in allv if r["label"]) / max(1, sum(1 for r in allv if r["label"])), 3),
        "mean_edit_matched_changed": round(sum(r["_edit"] for r in pop if r["label"]) / max(1, sum(r["label"] for r in pop)), 3)}
    return res


def evaluate_v8design(rows):
    pop = [r for r in rows if r["_valid"]]
    for r in pop:
        r["scores"]["edit_size_reversed"] = -float(r["_edit"])
    y = [r["label"] for r in pop]
    res = {"population": "v8 original design (label bound to family), VALID pairs", "n_pairs": len(pop), "n_programs": len({r["base_id"] for r in pop}),
           "n_changed": sum(y), "n_equivalent": len(y) - sum(y), "predictors": {}}
    for p in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "edit_size_reversed", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token"):
        s, yy, cc = vec(pop, p)
        res["predictors"][p] = {"auroc": round(auroc(s, yy), 6), "ci95_cluster_bootstrap": ci(s, yy, cc)}
    res["sbg_v5_minus_edit_size_reversed"] = delta(vec(pop, "sbg_v5"), vec(pop, "edit_size_reversed"))
    res["edit_size_exact_stratified_sbg_v5"] = dict(zip(("auroc", "n_cross_label_comparisons"), strat(pop, "sbg_v5")))
    return res


def run(args):
    split = args.split
    if split == "val":
        if not FREEZE.exists():
            raise SystemExit("REFUSED: artifacts/final/FREEZE_V9.json missing -- freeze before the val evaluation")
        fz = json.loads(FREEZE.read_text())
        problems = []
        if fz["evaluation_script_sha256"] != sha(__file__):
            problems.append("evaluate_v9.py hash differs from FREEZE_V9.json")
        if fz["models_sha256"] != sha(MODELS_FILE):
            problems.append("V9_MODELS_FROZEN.json hash differs from FREEZE_V9.json")
        for k, p in (("scored_v9c_val_sha256", PAIRS9["val"]), ("scored_v8_val_sha256", PAIRS8["val"])):
            if fz[k] != sha(p):
                problems.append(f"{p.name} hash differs from FREEZE_V9.json")
        if problems:
            raise SystemExit("REFUSED: " + "; ".join(problems))
        if OUT["val"].exists():
            raise SystemExit("REFUSED: V9_VAL_EVALUATION.json already exists; the val evaluation is a single run")
    models = json.loads(MODELS_FILE.read_text())["models"]
    rows9, rows8 = load("v9c", split), load("v8", split)
    out = {"artifact": f"V9_{split.upper()}_EVALUATION", "split": split,
           "status": {"val": "CONFIRMATORY-BY-FREEZE (single run; v8 val programs never scored before; plan and models frozen before any v9c/v8 val score was opened)",
                      "dev": "EXPLORATORY / DEVELOPMENT (dev scores were visible while the plan was written)",
                      "train": "IN-SAMPLE (models were fitted here); descriptive only"}[split],
           "evaluation_script": {"path": "experiments/final/evaluate_v9.py", "sha256": sha(__file__)},
           "models_frozen": {"path": str(MODELS_FILE.relative_to(REPO)), "sha256": sha(MODELS_FILE), "fitted_on": "v9c train, matched-complete"},
           "stale_programs_excluded": sorted(STALE),
           "sources": {"v9c_scored": {"path": str(PAIRS9[split].relative_to(REPO)), "sha256": sha(PAIRS9[split])},
                       "v8_scored": {"path": str(PAIRS8[split].relative_to(REPO)), "sha256": sha(PAIRS8[split])},
                       "v9c_pairs": {"path": f"benchmark/datasets/v9_composed/pairs_{split}.jsonl", "sha256": sha(V9 / f"pairs_{split}.jsonl")},
                       "v9c_audit": {"path": str(AUDIT9.relative_to(REPO)), "sha256": sha(AUDIT9)}},
           "v9c_matched": evaluate_v9c(rows9, models), "v8_design": evaluate_v8design(rows8)}
    OUT[split].write_text(json.dumps(out, indent=2) + "\n")
    m = out["v9c_matched"]
    print(split, "v9c matched:", m["n_pairs"], "pairs", m["n_programs"], "programs")
    for p in ("sbg_v5", "edit", "edit_reversed", "sbg_state", "sbg_temporal", "sbg_v3", "M_E", "M_ES", "M_EX", "M_ESX"):
        print(f"  {p:14s} {m['predictors'][p]['auroc']:.4f} {m['predictors'][p]['ci95_cluster_bootstrap']}")
    print("  verdict:", m["verdict"])
    for k, v in m["pre_declared_tests"].items():
        if k != "holm":
            print("  ", k, {a: b for a, b in v.items() if a in ("delta", "ci_lower", "ci_upper", "p", "p_two_sided", "auroc")})
    print("  v8 design:", {p: v["auroc"] for p, v in out["v8_design"]["predictors"].items()})
    print("wrote", OUT[split].relative_to(REPO))


def stage_fit(args):
    if OUT["val"].exists():
        raise SystemExit("REFUSED: val evaluation already exists")
    rows = matched_complete(load("v9c", "train"))
    models = fit_models(rows)
    MODELS_FILE.write_text(json.dumps({
        "artifact": "V9_MODELS_FROZEN",
        "fitted_on": {"design": "v9c", "split": "train", "population": "matched-complete", "n_pairs": len(rows),
                      "n_programs": len({r['base_id'] for r in rows}), "scored_pairs_sha256": sha(PAIRS9["train"])},
        "fit": "experiments/final/fit_weights.fit_logistic (L2=1.0, lr=0.5, 5000 its, standardised features); logit scores",
        "models": models}, indent=2) + "\n")
    print("fitted", list(models), "on", len(rows), "train pairs ->", MODELS_FILE.relative_to(REPO))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="stage", required=True)
    sub.add_parser("fit").set_defaults(fn=stage_fit)
    r = sub.add_parser("run")
    r.add_argument("--split", required=True, choices=["train", "dev", "val"])
    r.set_defaults(fn=run)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

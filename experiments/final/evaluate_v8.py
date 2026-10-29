"""Frozen v8 evaluation: one analysis script for dev (dry run) and test (single run).

Everything that can influence a number is fixed here BEFORE the test split is scored:
  * primary predictor  : sbg_v5 (fixed weights 0.50/0.25/0.25), unchanged
  * secondary          : learned_m1/learned_m2 (weights fitted on v6 TRAIN, WEIGHT_FITTING.json, unchanged)
  * baselines          : edit_size_reversed (canonical ast.unparse changed lines), exception_fraction,
                         call_count, coverage_size, static_ast, static_token
  * evaluation set     : VALID (evaluated pairs that pass the static audit), primary; EVALUABLE and ALL also reported
  * cluster unit       : base program;  bootstrap 2000 resamples; permutation/shuffle seeds 42
  * threshold          : tau_v8 = Youden-J optimum of sbg_v5 on the v8 DEV split only (stage `freeze`)
  * success criterion  : EVALUATION_PLAN_V8.md section 7 -- sbg_v5 must beat the best baseline (INCLUDING
                         reversed edit size) with a Holm-corrected lower CI bound on delta-AUROC > 0 AND the
                         edit-size-stratified AUROC must exceed the label-shuffle p95.  Anything else is
                         reported as "not demonstrated".

Stages
    freeze                 derive tau_v8 on v8 dev, write artifacts/final/THRESHOLD_V8_FROZEN.json
    run --split dev|test   analyse a scored pair file; --split test refuses unless FREEZE_V8.json exists and
                           names this script's sha256, and refuses to overwrite an existing test result.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import random
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from experiments.final.edit_size_analysis import _edit_size                          # noqa: E402
from experiments.final.fit_weights import MODELS, score as lin_score                 # noqa: E402
from sbg.statistics import (                                                          # noqa: E402
    auroc, cluster_bootstrap_ci, cluster_permutation_p, holm_bonferroni,
    label_shuffle_noise_floor, paired_cluster_bootstrap_delta)

ART = REPO / "artifacts" / "final"
EV = REPO / "artifacts" / "paper_evidence"
DATASET = REPO / "benchmark" / "datasets" / "v8"
AUDIT = ART / "BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json"
WEIGHTS = ART / "WEIGHT_FITTING.json"
FREEZE = ART / "FREEZE_V8_AMENDMENT1.json"   # supersedes the script hash in FREEZE_V8.json (see amendment)
STALE = EV / "DIAGNOSTIC_V8_STALE_VARIANTS.json"   # content-only audit (audit_v8_staleness.py); reads no scores
TAU_FILE = ART / "THRESHOLD_V8_FROZEN.json"
PAIRS = {"dev": ART / "pairs_v8devrescore_output_free_v8.jsonl", "test": ART / "pairs_v8test_output_free_v8.jsonl"}
OUT = {"dev": EV / "V8_DEV_DRYRUN_EVALUATION.json", "test": EV / "V8_TEST_EVALUATION.json"}
SEED, NBOOT = 42, 2000
BASELINES = ("edit_size_reversed", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token")
SECONDARY = ("learned_m1", "learned_m2")
EDIT_BINS = [(0, 2), (3, 5), (6, 10), (11, 20), (21, 40), (41, 10 ** 9)]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def youden(points):
    pos, neg = collections.Counter(), collections.Counter()
    for d, y in points:
        (pos if y else neg)[d] += 1
    n_pos, n_neg = sum(pos.values()), sum(neg.values())
    vals = sorted(set(pos) | set(neg))
    best = None
    for k in range(len(vals) - 1):
        tau = (vals[k] + vals[k + 1]) / 2
        tpr = sum(c for v, c in pos.items() if v > tau) / n_pos
        fpr = sum(c for v, c in neg.items() if v > tau) / n_neg
        if best is None or tpr - fpr > best[1] + 1e-12:
            best = (tau, tpr - fpr, tpr, fpr)
    return best


def load_scored(split):
    audit = {r["pair_id"]: r for r in json.loads(AUDIT.read_text())["pairs"] if r["split"] == split}
    meta = {m["pair_id"]: m for m in jl(DATASET / f"pairs_{split}.jsonl")}
    rows = jl(PAIRS[split])
    assert all(r["split"] == split for r in rows), "split mismatch in scored file"
    # Pre-declared exclusion: programs whose committed variants do not match their current base file.
    stale = {s["program"] for s in json.loads(STALE.read_text())["stale_programs"]}
    expected = sorted(pid for pid, m in meta.items() if m["base_id"] not in stale)
    # Amendment 1 (FREEZE_V8_AMENDMENT1.json): the test runner scores only non-stale pairs, because a stale
    # variant of an excluded program does not terminate. The dev file contains every pair (scored earlier).
    assert sorted(r["pair_id"] for r in rows if r["base_id"] not in stale) == expected, "scored pair ids != dataset pair ids"
    if split == "test":
        assert len(rows) == len(expected), "test file must contain only non-stale pairs"
    rows = [r for r in rows if r["base_id"] not in stale]
    W = json.loads(WEIGHTS.read_text())
    out = []
    for r in rows:
        v = audit.get(r["pair_id"])
        r["_evaluated"] = bool(r["evaluated"])
        r["_valid"] = bool(r["evaluated"] and v and v.get("status") == "ok" and (r["label"] == 0 or v.get("observable") is True))
        if r["evaluated"]:
            m = meta[r["pair_id"]]
            r["_edit"] = _edit_size(m["base_path"], m["variant_path"])
            s = r["scores"]
            s["edit_size_reversed"] = -float(r["_edit"])
            for name, feats in MODELS.items():
                s[f"learned_{name.lower()}"] = lin_score(W["models"][name], feats, s)
        out.append(r)
    return out


def predictor_vectors(rows, p):
    return ([r["scores"][p] for r in rows], [r["label"] for r in rows], [r["base_id"] for r in rows])


def stratified(scores, labels, strata):
    g = collections.defaultdict(lambda: ([], []))
    for s, l, k in zip(scores, labels, strata):
        g[k][l].append(s)
    num = den = 0.0
    for neg, pos in g.values():
        for a in pos:
            for b in neg:
                num += 1.0 if a > b else 0.5 if a == b else 0.0
        den += len(pos) * len(neg)
    return (num / den if den else None), den


def boot_stratified(scores, labels, strata, clusters, n=NBOOT, seed=SEED):
    by = collections.defaultdict(list)
    for i, c in enumerate(clusters):
        by[c].append(i)
    ks = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        idx = [i for c in (rng.choice(ks) for _ in ks) for i in by[c]]
        a, _ = stratified([scores[i] for i in idx], [labels[i] for i in idx], [strata[i] for i in idx])
        if a is not None:
            vals.append(a)
    vals.sort()
    return [round(vals[int(.025 * len(vals))], 6), round(vals[int(.975 * len(vals)) - 1], 6), len(vals)] if len(vals) > 50 else None


def evaluate_set(rows, tau):
    out = {"n_pairs": len(rows), "n_changed": sum(r["label"] for r in rows),
           "n_equivalent": sum(1 - r["label"] for r in rows), "n_programs": len({r["base_id"] for r in rows})}
    if not rows or out["n_changed"] in (0, len(rows)):
        return out
    names = ("sbg_v5",) + SECONDARY + BASELINES
    pred = {p: predictor_vectors(rows, p) for p in names}
    y, cl = pred["sbg_v5"][1], pred["sbg_v5"][2]
    table = {}
    for p in names:
        s = pred[p][0]
        lo, hi, n = cluster_bootstrap_ci(s, y, cl, n_bootstrap=NBOOT, seed=SEED)
        table[p] = {"auroc": round(auroc(s, y), 6), "ci95_cluster_bootstrap": [lo, hi], "n_boot": n}
    table["sbg_v5"]["permutation_p_one_sided"] = round(cluster_permutation_p(pred["sbg_v5"][0], y, cl, n_permutations=2000, seed=SEED), 6)
    out["predictors"] = table
    deltas = {}
    for b in BASELINES + SECONDARY:
        deltas[f"sbg_v5_minus_{b}"] = paired_cluster_bootstrap_delta(pred["sbg_v5"][0], pred[b][0], y, cl, n_bootstrap=NBOOT, seed=SEED)
    pv = {k: v["p_two_sided"] for k, v in deltas.items() if k.replace("sbg_v5_minus_", "") in BASELINES and v["p_two_sided"] is not None}
    out["paired_deltas"] = deltas
    out["holm_bonferroni_over_baselines"] = holm_bonferroni(pv) if pv else None
    out["label_shuffle_noise_floor_sbg_v5"] = label_shuffle_noise_floor(pred["sbg_v5"][0], y, cl, n_shuffles=500, seed=SEED)
    # confound control
    edit = [r["_edit"] for r in rows]
    a, den = stratified(pred["sbg_v5"][0], y, edit)
    out["edit_size_exact_stratified"] = {
        "sbg_v5_auroc": None if a is None else round(a, 6), "n_cross_label_comparisons": den,
        "fraction_of_all_cross_label_pairs": round(den / (out["n_changed"] * out["n_equivalent"]), 4),
        "ci95_cluster_bootstrap": boot_stratified(pred["sbg_v5"][0], y, edit, cl),
        "note": "compares only CHANGED vs EQUIVALENT pairs with identical canonical edit size (edit size alone = 0.5 by construction)"}
    sub = [i for i, e in enumerate(edit) if 1 <= e <= 5]
    ys = [y[i] for i in sub]
    if 5 <= sum(ys) <= len(ys) - 5:
        out["edit_size_1_to_5_subset"] = {
            "n": len(sub), "n_changed": sum(ys), "n_equivalent": len(ys) - sum(ys),
            "sbg_v5_auroc": round(auroc([pred["sbg_v5"][0][i] for i in sub], ys), 6),
            "edit_size_reversed_auroc": round(auroc([-float(edit[i]) for i in sub], ys), 6)}
    out["mean_edit_size"] = {"changed": round(sum(e for e, l in zip(edit, y) if l) / out["n_changed"], 3),
                             "equivalent": round(sum(e for e, l in zip(edit, y) if not l) / out["n_equivalent"], 3)}
    bins = {}
    for lo_, hi_ in EDIT_BINS:
        idx = [i for i, e in enumerate(edit) if lo_ <= e <= hi_]
        yb = [y[i] for i in idx]
        bins[f"{lo_}-{hi_ if hi_ < 10**9 else 'inf'}"] = {
            "n": len(idx), "n_changed": sum(yb),
            "sbg_v5_auroc": round(auroc([pred["sbg_v5"][0][i] for i in idx], yb), 6) if 0 < sum(yb) < len(yb) else None}
    out["sbg_v5_by_edit_bin"] = bins
    # per-program and leave-one-cluster-out
    per = {}
    for c in sorted(set(cl)):
        idx = [i for i, k in enumerate(cl) if k == c]
        yc = [y[i] for i in idx]
        per[c] = {"n": len(idx), "n_changed": sum(yc),
                  "sbg_v5": round(auroc([pred["sbg_v5"][0][i] for i in idx], yc), 4) if 0 < sum(yc) < len(yc) else None,
                  "edit_size_reversed": round(auroc([pred["edit_size_reversed"][0][i] for i in idx], yc), 4) if 0 < sum(yc) < len(yc) else None}
    out["per_program_auroc"] = per
    loo = []
    for c in sorted(set(cl)):
        idx = [i for i, k in enumerate(cl) if k != c]
        loo.append(auroc([pred["sbg_v5"][0][i] for i in idx], [y[i] for i in idx]))
    out["leave_one_program_out_sbg_v5"] = {"min": round(min(loo), 6), "max": round(max(loo), 6)}
    # per family
    fam = collections.defaultdict(list)
    for r in rows:
        fam[r["transformation_type"]].append(r)
    out["by_family"] = {t: {"label": rs[0]["label"], "n": len(rs), "edit_median": sorted(r["_edit"] for r in rs)[len(rs) // 2],
                            "sbg_v5_mean": round(sum(r["scores"]["sbg_v5"] for r in rs) / len(rs), 4),
                            "frac_zero": round(sum(1 for r in rs if r["scores"]["sbg_v5"] == 0) / len(rs), 3),
                            "detect_rate_at_tau_v8": round(sum(1 for r in rs if r["scores"]["sbg_v5"] > tau) / len(rs), 3)}
                        for t, rs in sorted(fam.items())}
    tp = sum(1 for r in rows if r["label"] and r["scores"]["sbg_v5"] > tau)
    fp = sum(1 for r in rows if not r["label"] and r["scores"]["sbg_v5"] > tau)
    out["operating_point_tau_v8"] = {"tau": tau, "tpr": round(tp / out["n_changed"], 4), "fpr": round(fp / out["n_equivalent"], 4)}
    out["fraction_sbg_v5_exactly_zero"] = round(sum(1 for r in rows if r["scores"]["sbg_v5"] == 0) / len(rows), 4)
    # pre-declared success criterion (EVALUATION_PLAN_V8 section 7)
    base_names = [b for b in BASELINES]
    best = max(base_names, key=lambda b: table[b]["auroc"])
    d = deltas[f"sbg_v5_minus_{best}"]
    holm = out["holm_bonferroni_over_baselines"] or {}
    strat = out["edit_size_exact_stratified"]["sbg_v5_auroc"]
    p95 = out["label_shuffle_noise_floor_sbg_v5"].get("p95", out["label_shuffle_noise_floor_sbg_v5"].get("p95_auroc"))
    out["pre_declared_success_criterion"] = {
        "best_baseline": best, "best_baseline_auroc": table[best]["auroc"],
        "delta_sbg_v5_minus_best": d["delta"], "delta_ci95": [d["ci_lower"], d["ci_upper"]],
        "holm_adjusted_p_best": (holm.get(f"sbg_v5_minus_{best}") or {}).get("p_adjusted"),
        "stratified_auroc": strat, "noise_floor_p95": p95,
        "sbg_beats_best_baseline_with_ci_lb_gt_0": bool(d["ci_lower"] is not None and d["ci_lower"] > 0),
        "stratified_exceeds_noise_p95": bool(strat is not None and p95 is not None and strat > p95),
        "verdict": ("MET" if (d["ci_lower"] is not None and d["ci_lower"] > 0 and strat is not None and p95 is not None and strat > p95)
                    else "NOT DEMONSTRATED")}
    return out


def stage_freeze(args):
    rows = [r for r in load_scored("dev") if r["_valid"]]
    tau, j, tpr, fpr = youden([(r["scores"]["sbg_v5"], r["label"]) for r in rows])
    payload = {"artifact": "THRESHOLD_V8_FROZEN", "protocol": "output_free_v8", "predictor": "sbg_v5",
               "tau_star": round(tau, 6), "rule": "maximise Youden J over midpoints of consecutive sorted unique distances; detected iff d > tau; ties -> smaller tau",
               "derived_on": {"split": "dev", "dataset": "benchmark/datasets/v8", "scored_pair_file": str(PAIRS["dev"].relative_to(REPO)),
                              "scored_pair_file_sha256": sha(PAIRS["dev"]), "n_valid_pairs": len(rows),
                              "n_changed": sum(r["label"] for r in rows), "n_programs": len({r["base_id"] for r in rows}),
                              "stale_programs_excluded": sorted(s["program"] for s in json.loads(STALE.read_text())["stale_programs"]
                                                                if s["split"] == "dev")},
               "dev_operating_point": {"youden_j": round(j, 6), "tpr": round(tpr, 6), "fpr": round(fpr, 6)},
               "reads_no_test_data": True, "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "v6_tau_star_for_reference": json.loads((ART / "THRESHOLD_FROZEN.json").read_text())["tau_star"],
               "note": "tau_v8 is an operating point only; it does not affect any AUROC."}
    TAU_FILE.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=1))


def stage_run(args):
    split = args.split
    if split == "test":
        if not FREEZE.exists():
            raise SystemExit("REFUSED: artifacts/final/FREEZE_V8.json missing -- freeze before the test evaluation")
        fz = json.loads(FREEZE.read_text())
        if fz["evaluation_script_sha256"] != sha(__file__):
            raise SystemExit("REFUSED: evaluation script differs from the frozen hash")
        if OUT["test"].exists() and not args.allow_overwrite_never_use:
            raise SystemExit("REFUSED: test result already exists; the test split is evaluated once")
    tau = json.loads(TAU_FILE.read_text())["tau_star"]
    rows = load_scored(split)
    ev = [r for r in rows if r["_evaluated"]]
    va = [r for r in rows if r["_valid"]]
    res = {"artifact": "V8_" + split.upper() + ("_EVALUATION" if split == "test" else "_DRYRUN_EVALUATION"),
           "status": ("CONFIRMATORY-BY-FREEZE (single run; see FREEZE_V8.json caveats)" if split == "test"
                      else "DEVELOPMENT dry run of the frozen evaluation script; tau_v8 was derived on this split"),
           "split": split, "protocol": "output_free_v8", "dataset": "benchmark/datasets/v8",
           "evaluation_script": {"path": "experiments/final/evaluate_v8.py", "sha256": sha(__file__)},
           "sources": {"scored_pairs": {"path": str(PAIRS[split].relative_to(REPO)), "sha256": sha(PAIRS[split])},
                       "dataset_pairs": {"path": f"benchmark/datasets/v8/pairs_{split}.jsonl", "sha256": sha(DATASET / f"pairs_{split}.jsonl")},
                       "validity_audit": {"path": str(AUDIT.relative_to(REPO)), "sha256": sha(AUDIT)},
                       "weights": {"path": "artifacts/final/WEIGHT_FITTING.json", "sha256": sha(WEIGHTS)},
                       "tau": {"path": "artifacts/final/THRESHOLD_V8_FROZEN.json", "sha256": sha(TAU_FILE)}},
           "stale_programs_excluded": sorted(s["program"] for s in json.loads(STALE.read_text())["stale_programs"] if s["split"] == split),
           "sources_extra": {"stale_variant_audit": {"path": str(STALE.relative_to(REPO)), "sha256": sha(STALE)}},
           "counts": {"dataset_pairs_after_exclusion": len(rows), "evaluated": len(ev), "valid": len(va),
                      "programs_in_split": len({r["base_id"] for r in rows}), "programs_evaluated": len({r["base_id"] for r in ev}),
                      "failure_ledger": dict(collections.Counter(f"{r.get('failure_side')}:{r.get('failure_kind')}" for r in rows if not r["_evaluated"]))},
           "VALID": evaluate_set(va, tau)}
    if len(ev) != len(va):
        res["EVALUABLE"] = evaluate_set(ev, tau)
    # ALL: failures scored at distance 0 for predictors that depend on execution (static baselines kept)
    OUT[split].write_text(json.dumps(res, indent=2) + "\n")
    v = res["VALID"]
    print("VALID:", {k: v[k] for k in ("n_pairs", "n_changed", "n_equivalent", "n_programs")})
    for p, s in v["predictors"].items():
        print(f"  {p:22s} AUROC={s['auroc']:.4f} CI={s['ci95_cluster_bootstrap']}")
    print("  stratified:", v["edit_size_exact_stratified"]["sbg_v5_auroc"], v["edit_size_exact_stratified"]["ci95_cluster_bootstrap"])
    print("  criterion:", v["pre_declared_success_criterion"])
    print("wrote", OUT[split].relative_to(REPO))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="stage", required=True)
    sub.add_parser("freeze")
    r = sub.add_parser("run")
    r.add_argument("--split", choices=["dev", "test"], required=True)
    r.add_argument("--allow-overwrite-never-use", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    {"freeze": stage_freeze, "run": stage_run}[a.stage](a)


if __name__ == "__main__":
    main()

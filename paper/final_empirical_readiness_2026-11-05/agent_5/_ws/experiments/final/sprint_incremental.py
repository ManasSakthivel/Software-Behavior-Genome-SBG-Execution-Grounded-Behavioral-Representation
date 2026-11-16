#!/usr/bin/env python3
"""FINAL SPRINT, Part 1: incremental-contribution verification and diagnostics.  READ-ONLY over frozen artifacts.

  PYTHONHASHSEED=0 python experiments/final/sprint_incremental.py main   # verification + diagnostics A-D     (~3 min)
  PYTHONHASHSEED=0 python experiments/final/sprint_incremental.py lopo   # leave-one-program-out refit sensitivity (~15 min)
  -> artifacts/paper_evidence/INCREMENTAL_CONTRIBUTION_ANALYSIS_{main,lopo}.json

Status of every number written here: S1 (verification) re-derives FROZEN numbers and asserts equality with the frozen JSON.
Everything else is EXPLORATORY / POST-HOC (computed after V9c-val and V10 were opened) and is labelled as such in the output.
The single new model-fitting analysis (LOPO) was specified before it was run (see INCREMENTAL_CONTRIBUTION_ANALYSIS.md section 5).
"""
from __future__ import annotations

import collections
import json
import math
import random
import sys

import sprint_common as C
import evaluate_v9 as e
from sbg.statistics import auroc, paired_cluster_bootstrap_delta

SEED, NBOOT = 42, 2000
PRED = ("sbg_v5", "sbg_v6", "edit", "coverage_size", "exception_fraction", "call_count", "M_X", "M_EX", "M_E+V5", "M_EX+V5")


# ---------------------------------------------------------------- helpers
def strat_u(rows, pred, window=0):
    """Stratified AUROC: only CHANGED/EQUIVALENT pairs whose edit sizes differ by <= window are compared.  Returns (auroc, n_comparisons)."""
    if window == 0:
        return e.strat(rows, pred)
    pos = [(r["_edit"], r["scores"][pred]) for r in rows if r["label"] == 1]
    neg = [(r["_edit"], r["scores"][pred]) for r in rows if r["label"] == 0]
    num = den = 0.0
    for ep, sp in pos:
        for en, sn in neg:
            if abs(ep - en) <= window:
                num += 1.0 if sp > sn else .5 if sp == sn else 0.0
                den += 1
    return (round(num / den, 6) if den else None), den


def strat_exact_fast(rows, pred):
    g = collections.defaultdict(lambda: ([], []))
    for r in rows:
        g[r["_edit"]][r["label"]].append(r["scores"][pred])
    num = den = 0.0
    for neg, pos in g.values():
        if not neg or not pos:
            continue
        al = sorted([(s, 0) for s in neg] + [(s, 1) for s in pos])
        # mid-rank U
        i, n = 0, len(al)
        rank_pos = 0.0
        while i < n:
            j = i
            while j < n and al[j][0] == al[i][0]:
                j += 1
            avg = (i + 1 + j) / 2.0
            rank_pos += avg * sum(1 for k in range(i, j) if al[k][1] == 1)
            i = j
        u = rank_pos - len(pos) * (len(pos) + 1) / 2.0
        num += u
        den += len(pos) * len(neg)
    return num / den if den else float("nan")


def strat_delta(rows, a, b, n=NBOOT, seed=SEED):
    """Paired program-cluster bootstrap for the exact-edit-stratified AUROC difference a - b."""
    by = collections.defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(r)
    ks = sorted(by)
    obs = strat_exact_fast(rows, a) - strat_exact_fast(rows, b)
    rng, ds = random.Random(seed), []
    for _ in range(n):
        s = [x for k in (ks[rng.randrange(len(ks))] for _ in ks) for x in by[k]]
        ds.append(strat_exact_fast(s, a) - strat_exact_fast(s, b))
    ds = sorted(d for d in ds if not math.isnan(d))
    m = len(ds)
    n_le, n_ge = sum(1 for d in ds if d <= 0), sum(1 for d in ds if d >= 0)
    return {"delta": round(obs, 6), "ci_lower": round(ds[int(.025 * m)], 6), "ci_upper": round(ds[int(.975 * m) - 1], 6),
            "p_two_sided": round(min(1.0, 2 * min(n_le + 1, n_ge + 1) / (m + 1)), 6), "n_effective": m}


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j < len(o) and v[o[j]] == v[o[i]]:
                j += 1
            for k in range(i, j):
                r[o[k]] = (i + 1 + j) / 2.0
            i = j
        return r
    a, b = rk(x), rk(y)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    sa = math.sqrt(sum((v - ma) ** 2 for v in a))
    sb = math.sqrt(sum((v - mb) ** 2 for v in b))
    return None if sa == 0 or sb == 0 else round(sum((p - ma) * (q - mb) for p, q in zip(a, b)) / (sa * sb), 4)


def D(pop, a, b):
    return e.delta(e.vec(pop, a), e.vec(pop, b))


def conc_ci(pop, pred, keep=None):
    sets = C.matched_sets(pop)
    vals = [(s[1]["base_id"], C.set_outcome(s, pred)) for k, s in sets.items() if keep is None or keep(s)]
    if not vals:
        return None
    by = collections.defaultdict(list)
    for b, c in vals:
        by[b].append(c)
    ks, rng, bs = sorted(by), random.Random(SEED), []
    for _ in range(1000):
        s = [c for k in (ks[rng.randrange(len(ks))] for _ in ks) for c in by[k]]
        bs.append(sum(s) / len(s))
    bs.sort()
    return {"concordance": round(sum(c for _, c in vals) / len(vals), 4), "n_sets": len(vals), "n_programs": len(ks),
            "ci95": [round(bs[25], 4), round(bs[974], 4)]}


# ---------------------------------------------------------------- S1: verification (frozen numbers re-derived)
def verify(pop10, pop9v):
    frozen10 = json.loads((C.EV / "V10_INDEPENDENT_EVALUATION.json").read_text())
    frozen9 = json.loads((C.EV / "V9_VAL_EVALUATION.json").read_text())["v9c_matched"]
    out, ok = {}, True
    y10 = [r["label"] for r in pop10]
    # (a) population identity
    chk = {"v10_n_pairs": (len(pop10), frozen10["n_pairs"]), "v10_n_programs": (len({r['base_id'] for r in pop10}), frozen10["n_programs"]),
           "v9c_val_n_pairs": (len(pop9v), frozen9["n_pairs"]), "v9c_val_n_programs": (len({r['base_id'] for r in pop9v}), frozen9["n_programs"])}
    # (b) AUROCs
    for p in ("sbg_v5", "sbg_v6", "edit", "M_E", "M_EX", "M_X", "M_E+V5", "M_EX+V5", "M_EX+V6", "coverage_size", "exception_fraction", "call_count"):
        s, y, c = e.vec(pop10, p)
        chk[f"v10_auroc_{p}"] = (round(auroc(s, y), 6), frozen10["predictors"][p]["auroc"])
    for p in ("sbg_v5", "edit", "M_E", "M_ES", "M_EX", "M_ESX"):
        s, y, c = e.vec(pop9v, p)
        chk[f"v9c_val_auroc_{p}"] = (round(auroc(s, y), 6), frozen9["predictors"][p]["auroc"])
    # (c) paired deltas (same seed/NBOOT as frozen evaluators -> must be exactly equal)
    for name, (a, b) in {"H2": ("M_E+V5", "M_E"), "H3": ("sbg_v5", "edit"), "H4": ("M_EX+V5", "M_EX"), "H5": ("sbg_v6", "sbg_v5")}.items():
        d = D(pop10, a, b)
        f = {"H2": "H2_E+V5_minus_E", "H3": "H3_V5_minus_edit_forward", "H4": "H4_EX+V5_minus_EX", "H5": "H5_V6_minus_V5"}[name]
        for k in ("delta", "ci_lower", "ci_upper", "p_two_sided"):
            chk[f"v10_{name}_{k}"] = (d[k], frozen10["pre_declared_tests"]["deltas"][f][k])
    d = D(pop9v, "M_ESX", "M_EX")
    for k in ("delta", "ci_lower", "ci_upper", "p_two_sided"):
        chk[f"v9c_val_H4_{k}"] = (d[k], frozen9["pre_declared_tests"]["H4"][k])
    mism = {k: v for k, v in chk.items() if v[0] != v[1]}
    out["n_checks"] = len(chk)
    out["n_mismatch"] = len(mism)
    out["mismatches"] = mism
    out["checks"] = {k: {"recomputed": v[0], "frozen": v[1]} for k, v in chk.items()}
    # (d) leakage guards
    feats = {n: m["features"] for n, m in json.loads(C.V10_MODELS.read_text())["models"].items()}
    allowed = {"edit", "sbg_v5", "sbg_v6", "exception_fraction", "call_count", "coverage_size", "static_ast", "static_token"}
    out["model_features"] = feats
    out["features_outside_allowed_set"] = sorted({f for fs in feats.values() for f in fs} - allowed)
    out["label_derived_feature_present"] = any("label" in f or "group" in f for fs in feats.values() for f in fs)
    fit_programs = {json.loads(l)["base_id"] for l in open(C.REPO / "benchmark/datasets/v9_composed/pairs_train.jsonl") if l.strip()}
    out["program_overlap_v10_vs_model_fit_programs(v9c train)"] = sorted(fit_programs & {r["base_id"] for r in pop10})
    val_programs = {r["base_id"] for r in pop9v}
    out["program_overlap_v9c_val_vs_v9c_train"] = sorted(fit_programs & val_programs)
    out["same_pairs_for_all_models"] = True    # every M_*/single predictor above is evaluated on the same `pop` list object
    return out


# ---------------------------------------------------------------- Analysis A: where does SBG help?
def analysis_A(pop):
    A = {"status": "EXPLORATORY / DESCRIPTIVE (post-hoc subgroup breakdown of frozen V10 scores; not confirmatory)"}
    preds = ("sbg_v5", "M_EX", "M_EX+V5", "coverage_size", "edit")
    # by SC family (CHANGED member of each matched set) : within-set concordance
    for key, fn in (("by_sc_family", lambda s: s[1]["sc_type"]), ("by_sp_family", lambda s: s[0]["transformation_type"])):
        fam = collections.defaultdict(list)
        for g, s in C.matched_sets(pop).items():
            fam[fn(s)].append(s)
        A[key] = {}
        for f, ss in sorted(fam.items()):
            keep = lambda s, f=f, fn=fn: fn(s) == f                                  # noqa: E731
            A[key][f] = {"n_sets": len(ss), "n_programs": len({s[1]['base_id'] for s in ss}),
                         "concordance": {p: round(sum(C.set_outcome(s, p) for s in ss) / len(ss), 4) for p in preds},
                         "mean_edit_changed": round(sum(s[1]["_edit"] for s in ss) / len(ss), 2),
                         "mean_edit_equivalent": round(sum(s[0]["_edit"] for s in ss) / len(ss), 2),
                         "frac_changed_sbg_v5_zero": round(sum(1 for s in ss if s[1]["scores"]["sbg_v5"] == 0) / len(ss), 4),
                         "frac_changed_any_exec_stat_nonzero": round(sum(1 for s in ss if any(s[1]["scores"][k] > 0 for k in ("exception_fraction", "call_count", "coverage_size"))) / len(ss), 4)}
    # (CHANGED, behaviour-visible) 2x2: SBG nonzero vs execution statistics nonzero
    ch = [r for r in pop if r["label"] == 1]
    eq = [r for r in pop if r["label"] == 0]
    ex = lambda r: any(r["scores"][k] > 0 for k in ("exception_fraction", "call_count", "coverage_size"))   # noqa: E731
    A["changed_2x2_sbg_vs_exec_stats"] = {"n_changed": len(ch),
                                          "sbg_nonzero_and_exec_nonzero": sum(1 for r in ch if r["scores"]["sbg_v5"] > 0 and ex(r)),
                                          "sbg_nonzero_only": sum(1 for r in ch if r["scores"]["sbg_v5"] > 0 and not ex(r)),
                                          "exec_nonzero_only": sum(1 for r in ch if r["scores"]["sbg_v5"] == 0 and ex(r)),
                                          "neither": sum(1 for r in ch if r["scores"]["sbg_v5"] == 0 and not ex(r))}
    A["equivalent_2x2_sbg_vs_exec_stats"] = {"n_equivalent": len(eq),
                                             "sbg_nonzero_and_exec_nonzero": sum(1 for r in eq if r["scores"]["sbg_v5"] > 0 and ex(r)),
                                             "sbg_nonzero_only": sum(1 for r in eq if r["scores"]["sbg_v5"] > 0 and not ex(r)),
                                             "exec_nonzero_only": sum(1 for r in eq if r["scores"]["sbg_v5"] == 0 and ex(r)),
                                             "neither": sum(1 for r in eq if r["scores"]["sbg_v5"] == 0 and not ex(r))}
    # edit-size strata (EDIT_BINS of the frozen audit): pooled AUROC within each bin
    from edit_size_analysis import EDIT_BINS, _bin_idx
    A["by_edit_bin"] = {}
    for i, (lo, hi) in enumerate(EDIT_BINS):
        rs = [r for r in pop if _bin_idx(r["_edit"]) == i]
        y = [r["label"] for r in rs]
        if 0 < sum(y) < len(y):
            A["by_edit_bin"][f"{lo}-{hi if hi < 10**9 else 'inf'}"] = {"n": len(rs), "n_changed": sum(y), "n_equivalent": len(y) - sum(y),
                                                                      **{f"auroc_{p}": round(auroc([r["scores"][p] for r in rs], y), 4) for p in ("sbg_v5", "M_EX", "edit")}}
        else:
            A["by_edit_bin"][f"{lo}-{hi if hi < 10**9 else 'inf'}"] = {"n": len(rs), "n_changed": sum(y), "n_equivalent": len(y) - sum(y), "note": "single class; AUROC undefined"}
    # large-edit but equivalent pairs: how does each predictor score them?
    big_eq = [r for r in eq if r["_edit"] >= 11]
    A["equivalent_pairs_with_edit_ge_11"] = {"n": len(big_eq),
                                             "median_sbg_v5": sorted(r["scores"]["sbg_v5"] for r in big_eq)[len(big_eq) // 2] if big_eq else None,
                                             "frac_sbg_v5_zero": round(sum(1 for r in big_eq if r["scores"]["sbg_v5"] == 0) / len(big_eq), 4) if big_eq else None,
                                             "frac_exec_stats_all_zero": round(sum(1 for r in big_eq if not ex(r)) / len(big_eq), 4) if big_eq else None}
    return A


# ---------------------------------------------------------------- Analysis B: controlling for edit size
def analysis_B(pop, label):
    B = {"status": "EXACT-STRATIFIED part re-derives frozen numbers; WINDOW sweep and paired stratified deltas are EXPLORATORY (post-hoc)"}
    B["exact_stratified_auroc"] = {p: {"auroc": round(strat_exact_fast(pop, p), 4)} for p in PRED if p in pop[0]["scores"]}
    B["exact_stratified_n_cross_label_comparisons"] = e.strat(pop, "edit")[1]
    B["window_sweep"] = {}
    for w in (0, 1, 2, 3):                              # a single, small, pre-stated sensitivity grid
        B["window_sweep"][f"|edit_diff|<={w}"] = {p: dict(zip(("auroc", "n_comparisons"), strat_u(pop, p, w))) for p in ("sbg_v5", "M_EX", "coverage_size", "edit")}
    B["paired_deltas_exact_stratified"] = {
        "V5_minus_M_EX": strat_delta(pop, "sbg_v5", "M_EX"),
        "V5_minus_coverage_size": strat_delta(pop, "sbg_v5", "coverage_size"),
        "M_EX+V5_minus_M_EX": strat_delta(pop, "M_EX+V5", "M_EX"),
        "V5_minus_edit": strat_delta(pop, "sbg_v5", "edit")}
    sets = C.matched_sets(pop)
    B["matched_set_edit_gap"] = {"mean_edit_changed_minus_equivalent": round(sum(s[1]["_edit"] - s[0]["_edit"] for s in sets.values()) / len(sets), 3),
                                 "frac_sets_changed_edit_gt_equivalent": round(sum(1 for s in sets.values() if s[1]["_edit"] > s[0]["_edit"]) / len(sets), 4),
                                 "frac_sets_equal_edit": round(sum(1 for s in sets.values() if s[1]["_edit"] == s[0]["_edit"]) / len(sets), 4)}
    eq_edit = [s for s in sets.values() if s[1]["_edit"] == s[0]["_edit"]]
    B["matched_sets_with_equal_edit_size"] = {"n_sets": len(eq_edit), "concordance": {p: round(sum(C.set_outcome(s, p) for s in eq_edit) / len(eq_edit), 4) if eq_edit else None for p in ("sbg_v5", "M_EX", "M_EX+V5", "edit")}}
    return B


# ---------------------------------------------------------------- Analysis C/D: why is the increment small? redundancy
def analysis_CD(pop):
    R = {"status": "EXPLORATORY / DESCRIPTIVE"}
    feats = ["sbg_v5", "exception_fraction", "call_count", "coverage_size", "edit"]
    for lab, nm in ((1, "changed"), (0, "equivalent")):
        rs = [r for r in pop if r["label"] == lab]
        R[f"spearman_within_{nm}"] = {f"{a}~{b}": spearman([r['scores'][a] for r in rs], [r['scores'][b] for r in rs]) for i, a in enumerate(feats) for b in feats[i + 1:]}
    rs = pop
    R["spearman_pooled"] = {f"{a}~{b}": spearman([r['scores'][a] for r in rs], [r['scores'][b] for r in rs]) for i, a in enumerate(feats) for b in feats[i + 1:]}
    R["spearman_V5_vs_M_EX_pooled"] = spearman([r["scores"]["sbg_v5"] for r in pop], [r["scores"]["M_EX"] for r in pop])
    # where the combined model changes its ranking relative to M_EX: matched-set outcome transitions
    sets = C.matched_sets(pop)
    tr = collections.Counter()
    for s in sets.values():
        tr[(C.set_outcome(s, "M_EX"), C.set_outcome(s, "M_EX+V5"))] += 1
    R["matched_set_outcome_transition_M_EX_to_M_EX+V5"] = {f"{a}->{b}": n for (a, b), n in sorted(tr.items())}
    tr2 = collections.Counter()
    for s in sets.values():
        tr2[(C.set_outcome(s, "M_EX"), C.set_outcome(s, "sbg_v5"))] += 1
    R["matched_set_outcome_M_EX_vs_sbg_v5"] = {f"M_EX={a}|V5={b}": n for (a, b), n in sorted(tr2.items())}
    # per-program H4 delta vs per-program M_EX AUROC (ceiling / heterogeneity)
    per = {}
    for p in sorted({r["base_id"] for r in pop}):
        rs_ = [r for r in pop if r["base_id"] == p]
        y = [r["label"] for r in rs_]
        a_ex = auroc([r["scores"]["M_EX"] for r in rs_], y)
        a_exv = auroc([r["scores"]["M_EX+V5"] for r in rs_], y)
        a_v5 = auroc([r["scores"]["sbg_v5"] for r in rs_], y)
        per[p] = {"n": len(rs_), "auroc_M_EX": round(a_ex, 4), "auroc_M_EX+V5": round(a_exv, 4), "auroc_sbg_v5": round(a_v5, 4), "delta_H4": round(a_exv - a_ex, 4), "v5_minus_M_EX": round(a_v5 - a_ex, 4)}
    R["per_program"] = per
    d = [v["delta_H4"] for v in per.values()]
    R["per_program_summary"] = {"n_programs": len(d), "n_delta_gt_0.02": sum(1 for x in d if x > 0.02), "n_delta_lt_-0.02": sum(1 for x in d if x < -0.02),
                                "n_abs_le_0.02": sum(1 for x in d if abs(x) <= 0.02), "mean_delta": round(sum(d) / len(d), 4),
                                "n_programs_where_v5_gt_M_EX": sum(1 for v in per.values() if v["v5_minus_M_EX"] > 0),
                                "spearman_delta_H4_vs_M_EX_auroc": spearman(d, [v["auroc_M_EX"] for v in per.values()])}
    # pooled AUROC of the 'combined' model is LOWER than SBG alone: report weights
    m = json.loads(C.V10_MODELS.read_text())["models"]["EX+V5"]
    R["frozen_EX+V5_standardised_weights"] = dict(zip(m["features"], m["weights_standardised"]))
    R["frozen_EX_standardised_weights"] = dict(zip(json.loads(C.V10_MODELS.read_text())["models"]["EX"]["features"], json.loads(C.V10_MODELS.read_text())["models"]["EX"]["weights_standardised"]))
    R["pooled_auroc"] = {p: round(auroc(*e.vec(pop, p)[:2]), 4) for p in ("sbg_v5", "M_EX", "M_EX+V5", "M_E+V5")}
    return R


# ---------------------------------------------------------------- main
def main():
    pop10, _ = C.load_v10_population()
    pop9v = C.load_v9c_population("val")
    pop9d = C.load_v9c_population("dev")
    out = {"artifact": "INCREMENTAL_CONTRIBUTION_ANALYSIS_main", "script": "experiments/final/sprint_incremental.py main",
           "seed": SEED, "n_bootstrap": NBOOT}
    out["S1_verification"] = verify(pop10, pop9v)
    print("S1 checks", out["S1_verification"]["n_checks"], "mismatches", out["S1_verification"]["n_mismatch"])
    out["V10_A_where_does_sbg_help"] = analysis_A(pop10)
    out["V10_B_edit_size_control"] = analysis_B(pop10, "v10")
    out["V9c_val_B_edit_size_control"] = analysis_B(pop9v, "v9c_val")
    out["V10_CD_redundancy"] = analysis_CD(pop10)
    out["V9c_val_CD_redundancy"] = analysis_CD(pop9v)
    out["post_hoc_single_vs_combined"] = {
        "status": "POST-HOC / EXPLORATORY (V10 version also in V10_POSTHOC_SUPPLEMENT.json)",
        "V10_V5_minus_M_EX": D(pop10, "sbg_v5", "M_EX"), "V9c_val_V5_minus_M_EX": D(pop9v, "sbg_v5", "M_EX"), "V9c_dev_V5_minus_M_EX(dev, descriptive)": D(pop9d, "sbg_v5", "M_EX"),
        "V10_V5_minus_M_EX+V5": D(pop10, "sbg_v5", "M_EX+V5") if "M_EX+V5" in pop10[0]["scores"] else None,
        "V9c_val_V5_minus_M_ESX": D(pop9v, "sbg_v5", "M_ESX")}
    # crude power statement: what H4 effect could be excluded?
    h4_10, h4_9 = D(pop10, "M_EX+V5", "M_EX"), D(pop9v, "M_ESX", "M_EX")
    out["H4_interval_summary"] = {"V10": h4_10, "V9c_val": h4_9, "interpretation_bound": "upper CI limits +0.068 (V10) and +0.048 (V9c val): effects of >= +0.07 are excluded; effects up to +0.05..+0.07 are not"}
    (C.OUT / "INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print("wrote INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json")


# ---------------------------------------------------------------- LOPO refit (single, specified-before-run sensitivity)
def lopo(pop, tag):
    """Leave-one-program-out: for every program, refit M_EX and M_EX+V5 (same optimiser/L2/standardisation as the frozen models)
    on the OTHER programs of the same evaluation set, score the held-out program.  Pooled out-of-fold AUROCs + paired delta.
    Purpose: separate 'SBG adds nothing in-distribution' from 'the v9c-train-fitted combiner does not transfer'."""
    feats = {"EX": ["edit", "exception_fraction", "call_count", "coverage_size"], "EXV5": ["edit", "sbg_v5", "exception_fraction", "call_count", "coverage_size"]}
    progs = sorted({r["base_id"] for r in pop})
    oof = {r["pair_id"]: {} for r in pop}
    for i, held in enumerate(progs):
        tr = [r for r in pop if r["base_id"] != held]
        te = [r for r in pop if r["base_id"] == held]
        y = [r["label"] for r in tr]
        for nm, fs in feats.items():
            m = e.fit_logistic([[r["scores"][f] for f in fs] for r in tr], y)
            for r in te:
                oof[r["pair_id"]][nm] = e.lin_score(m, fs, r["scores"])
        print(f"  [{tag}] fold {i + 1}/{len(progs)} ({held})", flush=True)
    for r in pop:
        r["scores"]["LOPO_EX"], r["scores"]["LOPO_EX+V5"] = oof[r["pair_id"]]["EX"], oof[r["pair_id"]]["EXV5"]
    res = {"n_pairs": len(pop), "n_programs": len(progs)}
    for p in ("LOPO_EX", "LOPO_EX+V5", "sbg_v5"):
        s, y, c = e.vec(pop, p)
        res[f"auroc_{p}"] = {"auroc": round(auroc(s, y), 4), "ci95": e.ci(s, y, c)}
    res["delta_LOPO_EX+V5_minus_LOPO_EX"] = D(pop, "LOPO_EX+V5", "LOPO_EX")
    res["delta_sbg_v5_minus_LOPO_EX"] = D(pop, "sbg_v5", "LOPO_EX")
    res["delta_sbg_v5_minus_LOPO_EX+V5"] = D(pop, "sbg_v5", "LOPO_EX+V5")
    res["exact_edit_stratified"] = {p: round(strat_exact_fast(pop, p), 4) for p in ("LOPO_EX", "LOPO_EX+V5", "sbg_v5")}
    return res


def main_lopo():
    out = {"artifact": "INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo",
           "status": "EXPLORATORY / POST-HOC. Specified before running: LOPO refit of exactly two models (EX, EX+V5) on each of V10 and V9c-val; no other feature sets tried; "
                     "V10 / V9c-val had already been opened, so this is a sensitivity analysis, not confirmation. Out-of-fold scoring: no held-out program is used in its own fit.",
           "optimiser": "evaluate_v9.fit_logistic (L2=1.0, lr=0.5, 5000 its, standardised) -- identical to the frozen models"}
    pop10, _ = C.load_v10_population()
    out["V10"] = lopo(pop10, "v10")
    (C.OUT / "INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    pop9 = C.load_v9c_population("val")
    out["V9c_val"] = lopo(pop9, "v9c_val")
    (C.OUT / "INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: {a: b for a, b in v.items() if a.startswith(("auroc", "delta"))} for k, v in out.items() if k.startswith("V")}, indent=1))


if __name__ == "__main__":
    {"main": main, "lopo": main_lopo}[sys.argv[1]]()

#!/usr/bin/env python3
"""Agent 1 -- post-hoc EXPLORATORY formal component ablation of sbg_v5 = 0.50*V3 + 0.25*temporal + 0.25*state.

READ-ONLY on the repo: reads frozen scored files / labels / audits, imports sbg.statistics (pure functions), and writes ONLY into its own
directory.  No scoring, no model fitting, no threshold tuning, no weight optimisation.  Reduced variants use the *stored* component scores with
the *original* V5 weights (drop-term); renormalised variants are computed only to verify rank-equivalence.

Run (from anywhere):
  PYTHONDONTWRITEBYTECODE=1 /Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python \
      /Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/empirical_sprint_2026-11-04/agent_1/agent1_ablation.py
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # .../SBG
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO))
from sbg.statistics import auroc, cluster_bootstrap_ci, paired_cluster_bootstrap_delta   # noqa: E402  (read-only import)

ART, EV = REPO / "artifacts" / "final", REPO / "artifacts" / "paper_evidence"
V10D, V9D, V8D = (REPO / "benchmark" / "datasets" / n for n in ("v10_independent", "v9_composed", "v8"))
SEED, B = 42, 2000
W = (0.50, 0.25, 0.25)
INPUTS = {}


def sha(p):
    p = pathlib.Path(p)
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    INPUTS[str(p.relative_to(REPO))] = h
    return h


def jl(p):
    sha(p)
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def jf(p):
    sha(p)
    return json.loads(pathlib.Path(p).read_text())


# ----------------------------------------------------------------------------------------------------------------------------- populations
def row(r, label, group):
    s = r["scores"]
    return {"pair_id": r["pair_id"], "base_id": r["base_id"], "label": label, "group": group,
            "v3": s["sbg_v3"], "tmp": s["sbg_temporal"], "st": s["sbg_state"], "v5": s["sbg_v5"], "v5_full": s.get("v5_full")}


def load_v10():
    """Exact replica of evaluate_v10.stage_run population filter: evaluated rows; group = EQ pair_id / CH matched_pair_id; keep groups with 2 members, both labels."""
    meta = {m["pair_id"]: m for m in jl(V10D / "pairs_test.jsonl")}
    scored = {r["pair_id"]: r for r in jl(ART / "pairs_v10_test_v6exp.jsonl")}
    ok = collections.defaultdict(list)
    n_unev = 0
    for pid, m in meta.items():
        r = scored[pid]
        if not r["evaluated"]:
            n_unev += 1
            continue
        lab = int(m["semantic_relation"] == "CHANGED")
        ok[m["pair_id"] if lab == 0 else m["matched_pair_id"]].append(row(r, lab, m["pair_id"] if lab == 0 else m["matched_pair_id"]))
    pop = [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]
    # also expose ALL evaluated rows for the provenance check (641)
    allrows = [row(scored[p], int(meta[p]["semantic_relation"] == "CHANGED"), None) for p in meta if scored[p]["evaluated"]]
    return pop, allrows, {"n_dataset": len(meta), "n_unevaluated": n_unev}


def load_v9c_val():
    """Replica of evaluate_v9.load('v9c','val') + matched_complete (STALE programs excluded; _valid = evaluated & audit ok & (EQ or observable))."""
    stale = {s["program"] for s in jf(EV / "DIAGNOSTIC_V8_STALE_VARIANTS.json")["stale_programs"]}
    meta = {m["pair_id"]: m for m in jl(V9D / "pairs_val.jsonl")}
    v8meta = {m["pair_id"]: m for m in jl(V8D / "pairs_val.jsonl")}
    wanted = {m["matched_equivalent_pair_id"] for m in meta.values()}
    meta.update({k: v8meta[k] for k in wanted})
    rows = jl(ART / "pairs_v9c_val_output_free_v8.jsonl") + [r for r in jl(ART / "pairs_v8val_output_free_v8.jsonl") if r["pair_id"] in wanted]
    audit = {r["pair_id"]: r for r in jf(ART / "BENCHMARK_VALIDITY_AUDIT_V9C.json")["pairs"] if r["split"] == "val"}
    audit.update({r["pair_id"]: r for r in jf(ART / "BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json")["pairs"] if r["split"] == "val" and r["pair_id"] in wanted})
    ok = collections.defaultdict(list)
    allrows = []
    for r in rows:
        if r["base_id"] in stale:
            continue
        m = meta[r["pair_id"]]
        lab = int(m["semantic_relation"] == "CHANGED")
        v = audit.get(r["pair_id"])
        valid = bool(r["evaluated"] and v and v.get("status") == "ok" and (lab == 0 or v.get("observable") is True))
        grp = m.get("matched_equivalent_pair_id") if lab else r["pair_id"]
        if r["evaluated"]:
            allrows.append(row(r, lab, grp))
        if valid:
            ok[grp].append(row(r, lab, grp))
    pop = [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]
    return pop, allrows, {"n_rows_in_union": len(rows)}


# ----------------------------------------------------------------------------------------------------------------------------- variants
# drop-term variants: weights on (V3, temporal, state); NOTHING is re-weighted or optimised
VARIANTS = {
    "full_V5": (0.50, 0.25, 0.25),
    "V5_minus_V3": (0.0, 0.25, 0.25),          # == temporal+state pair
    "V5_minus_temporal": (0.50, 0.0, 0.25),    # == V3+state pair
    "V5_minus_state": (0.50, 0.25, 0.0),       # == V3+temporal pair
    "V3_only": (1.0, 0.0, 0.0),                # raw component; any positive weight is rank-identical
    "temporal_only": (0.0, 1.0, 0.0),
    "state_only": (0.0, 0.0, 1.0),
}
LOO = ("V5_minus_V3", "V5_minus_temporal", "V5_minus_state")
SINGLE = ("V3_only", "temporal_only", "state_only")
PAIR_ALIAS = {"V5_minus_V3": "temporal+state", "V5_minus_temporal": "V3+state", "V5_minus_state": "V3+temporal"}


def score(rows, w):
    return [w[0] * r["v3"] + w[1] * r["tmp"] + w[2] * r["st"] for r in rows]


def arr(rows, name):
    return score(rows, VARIANTS[name])


# ----------------------------------------------------------------------------------------------------------------------------- bootstrap
def boot_indices(clusters):
    """Same RNG stream as sbg.statistics.cluster_bootstrap_ci / paired_cluster_bootstrap_delta (Random(42); randrange over sorted keys)."""
    by = collections.defaultdict(list)
    for i, k in enumerate(clusters):
        by[k].append(i)
    keys = sorted(by)
    rng = random.Random(SEED)
    out = []
    for _ in range(B):
        idx = []
        for _ in keys:
            idx.extend(by[keys[rng.randrange(len(keys))]])
        out.append(idx)
    return out


def pct(sorted_vals, alpha=0.05):
    n = len(sorted_vals)
    return sorted_vals[max(0, int(math.floor(alpha / 2 * n)))], sorted_vals[min(n - 1, int(math.ceil((1 - alpha / 2) * n)) - 1)]


def pvalue_two_sided(d):
    m = len(d)
    n_le, n_ge = sum(1 for x in d if x <= 0.0), sum(1 for x in d if x >= 0.0)
    return min(1.0, 2.0 * min(n_le + 1, n_ge + 1) / (m + 1))


def holm(ps):
    order = sorted(ps, key=lambda k: ps[k])
    m, run, out = len(order), 0.0, {}
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * ps[k]))
        out[k] = run
    return out


def spearman(x, y):
    return pearson(rank(x), rank(y))


def rank(v):
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


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def binom_two_sided(k, n):
    if n == 0:
        return None
    p = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * p)


# ----------------------------------------------------------------------------------------------------------------------------- analysis
def provenance(allrows, pop, label):
    d = [abs(0.5 * r["v3"] + 0.25 * r["tmp"] + 0.25 * r["st"] - r["v5"]) for r in allrows]
    out = {"n_evaluated_rows": len(allrows), "max_abs_diff_recomputed_vs_stored_v5": max(d), "mean_abs_diff": sum(d) / len(d),
           "n_rows_diff_gt_1e-9": sum(1 for x in d if x > 1e-9), "n_rows_diff_gt_1e-8": sum(1 for x in d if x > 1e-8),
           "v5_full_values": dict(collections.Counter(r["v5_full"] for r in allrows)),
           "n_rows_v5_full_not_1.0 (fallback-to-V3-only or neutral 0.5 would not have v5_full==1)": sum(1 for r in allrows if r["v5_full"] != 1.0),
           "n_rows_any_component_gt_1_or_lt_0": sum(1 for r in allrows if any(c > 1 or c < 0 for c in (r["v3"], r["tmp"], r["st"], r["v5"]))),
           "n_rows_recomputed_gt_1 (clamp at 1 would bind)": sum(1 for r in allrows if 0.5 * r["v3"] + 0.25 * r["tmp"] + 0.25 * r["st"] > 1.0),
           "n_rows_stored_v5_eq_0": sum(1 for r in allrows if r["v5"] == 0),
           "n_rows_recomputed_eq_0": sum(1 for r in allrows if r["v3"] == 0 and r["tmp"] == 0 and r["st"] == 0),
           "n_rows_zero_status_disagree (stored==0 xor all-components==0)": sum(1 for r in allrows if (r["v5"] == 0) != (r["v3"] == 0 and r["tmp"] == 0 and r["st"] == 0)),
           "n_rows_stored_v5_eq_0.5": sum(1 for r in allrows if r["v5"] == 0.5)}
    y = [r["label"] for r in pop]
    c = [r["base_id"] for r in pop]
    s_stored = [r["v5"] for r in pop]
    s_rec = arr(pop, "full_V5")
    lo, hi, neff = cluster_bootstrap_ci(s_stored, y, c, n_bootstrap=B, seed=SEED)
    out["population_auroc_stored_v5"] = round(auroc(s_stored, y), 6)
    out["population_auroc_recomputed_v5"] = round(auroc(s_rec, y), 6)
    out["population_auroc_stored_unrounded"] = auroc(s_stored, y)
    out["population_auroc_recomputed_unrounded"] = auroc(s_rec, y)
    out["abs_diff_stored_vs_recomputed_auroc"] = abs(auroc(s_stored, y) - auroc(s_rec, y))
    out["stored_v5_ci95_library"] = [lo, hi]
    return out


def analyse(pop, tag):
    y = [r["label"] for r in pop]
    c = [r["base_id"] for r in pop]
    res = {"tag": tag, "n_pairs": len(pop), "n_programs": len(set(c)), "n_changed": sum(y), "n_equivalent": len(y) - sum(y), "n_matched_sets": len({r["group"] for r in pop})}
    sc = {n: arr(pop, n) for n in VARIANTS}
    sc["full_V5_stored"] = [r["v5"] for r in pop]
    idxs = boot_indices(c)
    # one pass: AUROC of every variant on every resample (same resamples for every variant => paired)
    names = list(sc)
    boots = {n: [] for n in names}
    for idx in idxs:
        yy = [y[i] for i in idx]
        if not (0 < sum(yy) < len(yy)):
            continue
        for n in names:
            s = sc[n]
            boots[n].append(auroc([s[i] for i in idx], yy))
    res["n_effective_resamples"] = len(boots["full_V5"])
    pt = {n: auroc(sc[n], y) for n in names}
    res["variants"] = {}
    for n in names:
        b = sorted(boots[n])
        lo, hi = pct(b)
        z = [x == 0 for x in sc[n]]
        res["variants"][n] = {"weights_V3_temporal_state": VARIANTS.get(n, "stored sbg_v5"), "auroc": pt[n], "ci_lo": lo, "ci_hi": hi,
                              "exact_zero_rate": sum(z) / len(z), "exact_zero_rate_changed": sum(1 for zz, l in zip(z, y) if zz and l) / sum(y),
                              "exact_zero_rate_equivalent": sum(1 for zz, l in zip(z, y) if zz and not l) / (len(y) - sum(y)),
                              "n_distinct_values": len(set(sc[n]))}
    # library cross-check of my bootstrap replication
    lib = cluster_bootstrap_ci(sc["full_V5_stored"], y, c, n_bootstrap=B, seed=SEED)
    mine = pct(sorted(boots["full_V5_stored"]))
    res["bootstrap_replication_check"] = {"library_ci_full_V5_stored": [lib[0], lib[1]], "mine": [round(mine[0], 6), round(mine[1], 6)],
                                          "match": [lib[0], lib[1]] == [round(mine[0], 6), round(mine[1], 6)]}
    # renormalisation equivalence
    ren = {}
    for n, w in VARIANTS.items():
        if n in SINGLE or n == "full_V5":
            continue
        t = sum(w)
        s2 = [x / t for x in sc[n]]
        ren[n] = {"renormalised_weights": [round(v / t, 6) for v in w], "auroc_drop_term": pt[n], "auroc_renormalised": auroc(s2, y),
                  "abs_diff": abs(pt[n] - auroc(s2, y)), "same_number_of_distinct_values": len(set(s2)) == len(set(sc[n]))}
    res["renormalisation_equivalence"] = ren
    # paired deltas
    def pdelta(a, b):
        d = sorted(x - z for x, z in zip(boots[a], boots[b]))
        raw = [x - z for x, z in zip(boots[a], boots[b])]
        lo, hi = pct(d)
        return {"delta": pt[a] - pt[b], "ci_lo": lo, "ci_hi": hi, "p_two_sided_raw": pvalue_two_sided(raw), "n_effective": len(raw)}
    res["deltas_full_minus"] = {n: pdelta("full_V5", n) for n in LOO + SINGLE}
    hp = holm({n: res["deltas_full_minus"][n]["p_two_sided_raw"] for n in LOO})
    for n in LOO:
        res["deltas_full_minus"][n]["holm_adj_p_over_3_LOO_descriptive"] = hp[n]
    res["deltas_single_vs_single"] = {f"{a}-{b}": pdelta(a, b) for a, b in (("state_only", "V3_only"), ("state_only", "temporal_only"), ("V3_only", "temporal_only"))}
    res["deltas_best_single_vs_full_note"] = "see deltas_full_minus for full - single"
    lib_d = paired_cluster_bootstrap_delta(sc["full_V5"], sc["V3_only"], y, c, n_bootstrap=B, seed=SEED)
    res["delta_replication_check_full_minus_V3only"] = {"library": lib_d, "mine": res["deltas_full_minus"]["V3_only"]}
    # per-program
    progs = sorted(set(c))
    per = {}
    for p in progs:
        ii = [i for i, k in enumerate(c) if k == p]
        yy = [y[i] for i in ii]
        if 0 < sum(yy) < len(yy):
            per[p] = {"n": len(ii), "n_changed": sum(yy), **{n: auroc([sc[n][i] for i in ii], yy) for n in names}}
    res["per_program"] = per
    pdlt = {}
    for n in LOO + SINGLE:
        d = {p: per[p]["full_V5"] - per[p][n] for p in per}
        eps = 1e-12
        # d = full - ablation; removing a component (ablation) "raises" AUROC when d < 0
        raise_ = sum(1 for v in d.values() if v < -eps)
        lower = sum(1 for v in d.values() if v > eps)
        tie = len(d) - raise_ - lower
        vals = sorted(d.values())
        mean = sum(vals) / len(vals)
        sd = (sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5 if len(vals) > 1 else None
        pdlt[n] = {"n_programs": len(d), "n_ablation_raises_AUROC": raise_, "n_ablation_lowers_AUROC": lower, "n_ties": tie,
                   "mean_delta_full_minus_ablation_unweighted_macro": mean, "median_delta": vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2,
                   "min_delta": vals[0], "max_delta": vals[-1], "sd_delta": sd,
                   "sign_test_two_sided_p_descriptive": binom_two_sided(min(raise_, lower), raise_ + lower),
                   "macro_mean_auroc_ablation": sum(per[p][n] for p in per) / len(per), "macro_mean_auroc_full": sum(per[p]["full_V5"] for p in per) / len(per)}
    res["per_program_effect_summary"] = pdlt
    # matched-set concordance (replicates evaluate_v9/v10.matched_concordance incl. percentile indices)
    g = collections.defaultdict(dict)
    for i, r in enumerate(pop):
        g[r["group"]][r["label"]] = i
    sets = [(pop[v[1]]["base_id"], v[0], v[1]) for v in g.values() if 0 in v and 1 in v]
    conc = {}
    for n in names:
        s = sc[n]
        by = collections.defaultdict(list)
        for b_, e_, c_ in sets:
            by[b_].append(1.0 if s[c_] > s[e_] else 0.5 if s[c_] == s[e_] else 0.0)
        ks, rng, vals = sorted(by), random.Random(SEED), []
        for _ in range(B):
            ss = [v for k in (rng.choice(ks) for _ in ks) for v in by[k]]
            vals.append(sum(ss) / len(ss))
        vals.sort()
        allv = [v for k in ks for v in by[k]]
        conc[n] = {"concordance": sum(allv) / len(allv), "n_sets": len(allv), "ci_lo": vals[int(.025 * B)], "ci_hi": vals[int(.975 * B) - 1],
                   "frac_sets_tied": sum(1 for v in allv if v == 0.5) / len(allv), "frac_sets_lost": sum(1 for v in allv if v == 0.0) / len(allv)}
    res["matched_set_concordance"] = conc
    # redundancy
    comp = {"V3": [r["v3"] for r in pop], "temporal": [r["tmp"] for r in pop], "state": [r["st"] for r in pop]}
    pairs = (("V3", "temporal"), ("V3", "state"), ("temporal", "state"))
    subsets = {"overall": list(range(len(pop))), "CHANGED": [i for i in range(len(pop)) if y[i] == 1], "EQUIVALENT": [i for i in range(len(pop)) if y[i] == 0]}
    corr = {}
    byprog = collections.defaultdict(list)
    for i, k in enumerate(c):
        byprog[k].append(i)
    keys = sorted(byprog)
    rng = random.Random(SEED)
    draws = [[keys[rng.randrange(len(keys))] for _ in keys] for _ in range(B)]
    for sname, sub in subsets.items():
        for a, b_ in pairs:
            xs, ys = [comp[a][i] for i in sub], [comp[b_][i] for i in sub]
            sp, pe = spearman(xs, ys), pearson(xs, ys)
            subset_set = set(sub)
            bp = {k: [i for i in byprog[k] if i in subset_set] for k in keys}
            bs, bpe = [], []
            for dr in draws:
                ii = [i for k in dr for i in bp[k]]
                xx, yy_ = [comp[a][i] for i in ii], [comp[b_][i] for i in ii]
                v = spearman(xx, yy_)
                if v is not None:
                    bs.append(v)
                v = pearson(xx, yy_)
                if v is not None:
                    bpe.append(v)
            bs.sort()
            bpe.sort()
            corr[f"{sname}|{a}~{b_}"] = {"spearman": sp, "spearman_ci_lo": pct(bs)[0] if bs else None, "spearman_ci_hi": pct(bs)[1] if bs else None,
                                          "pearson": pe, "pearson_ci_lo": pct(bpe)[0] if bpe else None, "pearson_ci_hi": pct(bpe)[1] if bpe else None, "n": len(sub)}
    res["correlations_cluster_bootstrap_ci"] = corr
    # within-program (per-program Spearman, then cluster-aware summary: unweighted mean over programs + program-bootstrap CI)
    wp = {}
    for sname, sub in subsets.items():
        subset_set = set(sub)
        for a, b_ in pairs:
            vals = {}
            for k in keys:
                ii = [i for i in byprog[k] if i in subset_set]
                v = spearman([comp[a][i] for i in ii], [comp[b_][i] for i in ii]) if len(ii) >= 3 else None
                if v is not None:
                    vals[k] = v
            if not vals:
                continue
            ks_ = sorted(vals)
            mean = sum(vals.values()) / len(vals)
            bm = []
            for dr in draws:
                vv = [vals[k] for k in dr if k in vals]
                if vv:
                    bm.append(sum(vv) / len(vv))
            bm.sort()
            sv = sorted(vals.values())
            wp[f"{sname}|{a}~{b_}"] = {"n_programs_defined": len(vals), "n_programs_total": len(keys), "mean_spearman": mean, "median_spearman": sv[len(sv) // 2],
                                       "min": sv[0], "max": sv[-1], "mean_ci_lo": pct(bm)[0], "mean_ci_hi": pct(bm)[1],
                                       "per_program": {k: vals[k] for k in ks_}}
    res["within_program_spearman"] = wp
    # zero patterns
    pat = collections.Counter()
    for r, l in zip(pop, y):
        pat[(l, int(r["v3"] == 0), int(r["tmp"] == 0), int(r["st"] == 0))] += 1
    res["zero_pattern_counts"] = [{"label": "CHANGED" if k[0] else "EQUIVALENT", "V3_zero": k[1], "temporal_zero": k[2], "state_zero": k[3], "n": v} for k, v in sorted(pat.items())]
    zs = {n: [x == 0 for x in comp[n]] for n in comp}
    ag = {}
    for sname, sub in subsets.items():
        for a, b_ in pairs:
            za, zb = [zs[a][i] for i in sub], [zs[b_][i] for i in sub]
            n = len(sub)
            both, a_only, b_only = sum(1 for p, q in zip(za, zb) if p and q), sum(1 for p, q in zip(za, zb) if p and not q), sum(1 for p, q in zip(za, zb) if q and not p)
            neither = n - both - a_only - b_only
            agree = (both + neither) / n
            pe_ = ((both + a_only) * (both + b_only) + (b_only + neither) * (a_only + neither)) / n ** 2
            kappa = (agree - pe_) / (1 - pe_) if pe_ < 1 else None
            ag[f"{sname}|{a}~{b_}"] = {"both_zero": both, f"{a}_zero_only": a_only, f"{b_}_zero_only": b_only, "neither_zero": neither, "raw_agreement": agree, "cohen_kappa": kappa,
                                       "jaccard_of_zero_sets": both / (both + a_only + b_only) if (both + a_only + b_only) else None}
    res["zero_agreement"] = ag
    res["zero_rates_by_component"] = {n: {s_: sum(1 for i in sub if comp[n][i] == 0) / len(sub) for s_, sub in subsets.items()} for n in comp}
    # nonzero-restricted correlation (both nonzero) -- to separate zero-inflation from magnitude agreement
    nz = {}
    for a, b_ in pairs:
        ii = [i for i in range(len(pop)) if comp[a][i] != 0 and comp[b_][i] != 0]
        nz[f"{a}~{b_}"] = {"n_both_nonzero": len(ii), "spearman": spearman([comp[a][i] for i in ii], [comp[b_][i] for i in ii])}
    res["spearman_among_pairs_both_nonzero"] = nz
    # magnitude scale
    res["component_means"] = {n: {s_: sum(comp[n][i] for i in sub) / len(sub) for s_, sub in subsets.items()} for n in comp}
    return res


# ----------------------------------------------------------------------------------------------------------------------------- output
def f(x, d=4):
    return "NA" if x is None else f"{x:.{d}f}"


def write_csvs(R):
    with open(HERE / "ablation_auroc.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "variant", "equivalent_pair_name", "w_V3", "w_temporal", "w_state", "auroc", "ci95_lo", "ci95_hi", "exact_zero_rate", "zero_rate_changed", "zero_rate_equivalent", "n_distinct_values"])
        for tag, r in R.items():
            for n, v in r["variants"].items():
                ww = v["weights_V3_temporal_state"]
                ww = ww if isinstance(ww, tuple) else ("stored", "stored", "stored")
                w.writerow([tag, n, PAIR_ALIAS.get(n, ""), *ww, f"{v['auroc']:.6f}", f"{v['ci_lo']:.6f}", f"{v['ci_hi']:.6f}", f"{v['exact_zero_rate']:.4f}",
                            f"{v['exact_zero_rate_changed']:.4f}", f"{v['exact_zero_rate_equivalent']:.4f}", v["n_distinct_values"]])
    with open(HERE / "ablation_paired_deltas.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "contrast", "delta_auroc", "ci95_lo", "ci95_hi", "p_two_sided_raw", "holm_adj_p_over_3_LOO_descriptive", "n_effective_resamples"])
        for tag, r in R.items():
            for n, v in r["deltas_full_minus"].items():
                w.writerow([tag, f"full_V5 - {n}", f"{v['delta']:.6f}", f"{v['ci_lo']:.6f}", f"{v['ci_hi']:.6f}", f"{v['p_two_sided_raw']:.6f}", f"{v.get('holm_adj_p_over_3_LOO_descriptive', ''):}", v["n_effective"]])
            for n, v in r["deltas_single_vs_single"].items():
                w.writerow([tag, n, f"{v['delta']:.6f}", f"{v['ci_lo']:.6f}", f"{v['ci_hi']:.6f}", f"{v['p_two_sided_raw']:.6f}", "", v["n_effective"]])
    with open(HERE / "per_program_auroc.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        first = next(iter(R.values()))
        names = [k for k in next(iter(first["per_program"].values())) if k not in ("n", "n_changed")]
        w.writerow(["population", "program", "n", "n_changed"] + names)
        for tag, r in R.items():
            for p, v in r["per_program"].items():
                w.writerow([tag, p, v["n"], v["n_changed"]] + [f"{v[n]:.4f}" for n in names])
    with open(HERE / "per_program_effect_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "ablation", "n_programs", "n_ablation_raises", "n_ablation_lowers", "n_ties", "mean_delta_full_minus_abl", "median_delta", "min_delta", "max_delta", "sd_delta", "sign_test_p_descriptive", "macro_auroc_ablation", "macro_auroc_full"])
        for tag, r in R.items():
            for n, v in r["per_program_effect_summary"].items():
                w.writerow([tag, n, v["n_programs"], v["n_ablation_raises_AUROC"], v["n_ablation_lowers_AUROC"], v["n_ties"], f"{v['mean_delta_full_minus_ablation_unweighted_macro']:.4f}",
                            f"{v['median_delta']:.4f}", f"{v['min_delta']:.4f}", f"{v['max_delta']:.4f}", f(v["sd_delta"]), f(v["sign_test_two_sided_p_descriptive"]), f"{v['macro_mean_auroc_ablation']:.4f}", f"{v['macro_mean_auroc_full']:.4f}"])
    with open(HERE / "redundancy_correlations.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "kind", "subset", "pair", "n_or_programs", "spearman", "ci_lo", "ci_hi", "pearson", "pearson_ci_lo", "pearson_ci_hi"])
        for tag, r in R.items():
            for k, v in r["correlations_cluster_bootstrap_ci"].items():
                s_, p_ = k.split("|")
                w.writerow([tag, "pooled(cluster-bootstrap CI)", s_, p_, v["n"], f(v["spearman"]), f(v["spearman_ci_lo"]), f(v["spearman_ci_hi"]), f(v["pearson"]), f(v["pearson_ci_lo"]), f(v["pearson_ci_hi"])])
            for k, v in r["within_program_spearman"].items():
                s_, p_ = k.split("|")
                w.writerow([tag, "within-program mean of per-program Spearman", s_, p_, f"{v['n_programs_defined']}/{v['n_programs_total']}", f(v["mean_spearman"]), f(v["mean_ci_lo"]), f(v["mean_ci_hi"]), "", "", ""])
    with open(HERE / "zero_patterns.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "label", "V3_zero", "temporal_zero", "state_zero", "n"])
        for tag, r in R.items():
            for z in r["zero_pattern_counts"]:
                w.writerow([tag, z["label"], z["V3_zero"], z["temporal_zero"], z["state_zero"], z["n"]])
    with open(HERE / "zero_agreement.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "subset", "pair", "both_zero", "A_only_zero", "B_only_zero", "neither_zero", "raw_agreement", "cohen_kappa", "jaccard_zero_sets"])
        for tag, r in R.items():
            for k, v in r["zero_agreement"].items():
                s_, p_ = k.split("|")
                a, b_ = p_.split("~")
                w.writerow([tag, s_, p_, v["both_zero"], v[f"{a}_zero_only"], v[f"{b_}_zero_only"], v["neither_zero"], f(v["raw_agreement"]), f(v["cohen_kappa"]), f(v["jaccard_of_zero_sets"])])
    with open(HERE / "matched_set_concordance.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "variant", "concordance", "ci95_lo", "ci95_hi", "n_sets", "frac_sets_tied", "frac_sets_lost"])
        for tag, r in R.items():
            for n, v in r["matched_set_concordance"].items():
                w.writerow([tag, n, f"{v['concordance']:.6f}", f"{v['ci_lo']:.6f}", f"{v['ci_hi']:.6f}", v["n_sets"], f"{v['frac_sets_tied']:.4f}", f"{v['frac_sets_lost']:.4f}"])


def main():
    out = {}
    R = {}
    prov = {}
    for tag, loader in (("V10_test", load_v10), ("V9c_val", load_v9c_val)):
        pop, allrows, extra = loader()
        prov[tag] = {**extra, **provenance(allrows, pop, tag)}
        prov[tag]["population"] = {"n_pairs": len(pop), "n_programs": len({r["base_id"] for r in pop}), "n_changed": sum(r["label"] for r in pop)}
        print(tag, "pop", len(pop), "programs", len({r['base_id'] for r in pop}), "max|diff|", prov[tag]["max_abs_diff_recomputed_vs_stored_v5"],
              "AUROC stored/recomp", prov[tag]["population_auroc_stored_v5"], prov[tag]["population_auroc_recomputed_v5"], flush=True)
        R[tag] = analyse(pop, tag)
        print(tag, "done", flush=True)
    # pin reference numbers
    ref10 = jf(EV / "V10_INDEPENDENT_EVALUATION.json")
    ref9 = jf(EV / "V9_VAL_EVALUATION.json")["v9c_matched"]
    prov["V10_test"]["reference_V10_INDEPENDENT_EVALUATION"] = {"n_pairs": ref10["n_pairs"], "n_programs": ref10["n_programs"], "sbg_v5_auroc": ref10["predictors"]["sbg_v5"]["auroc"],
                                                                 "sbg_v5_ci": ref10["predictors"]["sbg_v5"]["ci95_cluster_bootstrap"], "sbg_state_auroc": ref10["predictors"]["sbg_state"]["auroc"],
                                                                 "sbg_v3_auroc": ref10["predictors"].get("sbg_v3", {}).get("auroc"), "sbg_temporal_auroc": ref10["predictors"].get("sbg_temporal", {}).get("auroc"),
                                                                 "note": "V10_INDEPENDENT_EVALUATION.json reports only the predictors in its own list (sbg_v3/sbg_temporal not stored there if None)"}
    prov["V9c_val"]["reference_V9_VAL_EVALUATION_v9c_matched"] = {"n_pairs": ref9["n_pairs"], "n_programs": ref9["n_programs"], "sbg_v5": ref9["predictors"]["sbg_v5"], "sbg_v3": ref9["predictors"]["sbg_v3"]["auroc"],
                                                                   "sbg_temporal": ref9["predictors"]["sbg_temporal"]["auroc"], "sbg_state": ref9["predictors"]["sbg_state"]["auroc"]}
    # frozen-file integrity vs freeze records
    fz10 = jf(ART / "FREEZE_V10_SCORED.json")
    fz9 = jf(ART / "FREEZE_V9.json")
    prov["freeze_checks"] = {"V10_scored_file_sha_matches_FREEZE_V10_SCORED": fz10["scored_file_sha256"] == INPUTS["artifacts/final/pairs_v10_test_v6exp.jsonl"],
                             "V9c_val_scored_sha_matches_FREEZE_V9": fz9["scored_v9c_val_sha256"] == INPUTS["artifacts/final/pairs_v9c_val_output_free_v8.jsonl"],
                             "V8_val_scored_sha_matches_FREEZE_V9": fz9["scored_v8_val_sha256"] == INPUTS["artifacts/final/pairs_v8val_output_free_v8.jsonl"]}
    for tag, r in R.items():
        out[tag] = r
    (HERE / "agent1_results.json").write_text(json.dumps({"provenance": prov, "results": out}, indent=1, default=str) + "\n")
    (HERE / "input_hashes.json").write_text(json.dumps(INPUTS, indent=1, sort_keys=True) + "\n")
    write_csvs(R)
    print("OK")


if __name__ == "__main__":
    main()

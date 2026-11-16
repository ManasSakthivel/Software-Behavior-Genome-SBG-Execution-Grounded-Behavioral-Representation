#!/usr/bin/env python3
"""EXP-WPC-003: component-ablation statistics on PERMITTED data only (v9c_train primary [minus math_gray_code] + v9c_dev).

Reads raw/EXP-WPC-002/{v9c_dev,v9c_train}_pairs.csv (frozen-component distances, verified bit-equal to frozen scores).
Never reads v10_test / v9c_val.  Every variant other than `full` (== frozen sbg_v5) is an EXPLORATORY ablation of the
frozen distance; ablations are NEVER original-SBG evidence.

Family (declared before computing; Holm over these 12 paired comparisons vs `full`, pooled dev+train):
  singles: state, temporal, call_topology, bigrams, exception, coverage_resid
  minus  : full-state, full-temporal, full-call_topology, full-bigrams, full-exception, full-coverage_resid
Component definitions (V5 effective weights; 0.5 * V3 terms):
  call_topology  = 0.5*(0.20*d_freq + 0.10*d_depth)     function-call frequency histogram + mean call depth
  bigrams        = 0.5*(0.25*d_seq)                       order-sensitive call-transition bigrams (V3)
  exception      = 0.5*(0.10*d_exception + 0.05*d_exc_causality)
  coverage_resid = 0.5*(0.20*d_coverage + 0.05*d_consistency + 0.05*d_input_sensitivity)   (line-coverage volume etc.)
  temporal       = 0.25*d_temporal   (trigrams/entropy/exception-triples/causal/phase/loop)
  state          = 0.25*d_state      (frozen state-transition genome)
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import multiprocessing as mp
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve()
WPC = HERE.parents[1]
PKG = WPC.parent
sys.path.insert(0, str(PKG / "experiments" / "common"))
import eval_lib as E                                            # noqa: E402

PAIRS = WPC / "raw" / "EXP-WPC-002"
OUT = WPC / "raw" / "EXP-WPC-003"
TAB = WPC / "tables"
B, SEED = 2000, 42
FAMILY = ["state", "temporal", "call_topology", "bigrams", "exception", "coverage_resid",
          "full-state", "full-temporal", "full-call_topology", "full-bigrams", "full-exception", "full-coverage_resid"]


# ------------------------------------------------------------------------------------------------ data
def read(split):
    rows = []
    for r in csv.DictReader(open(PAIRS / f"{split}_pairs.csv")):
        for k, v in r.items():
            if k not in ("pair_id", "base_id", "group", "sc_type", "sp_type"):
                r[k] = float(v)
        r["label"] = int(r["label"])
        rows.append(r)
    return rows


def components(r):
    return {"call_topology": 0.5 * (0.20 * r["d_freq"] + 0.10 * r["d_dep"]),
            "bigrams": 0.5 * (0.25 * r["d_seq"]),
            "exception": 0.5 * (0.10 * r["d_exc"] + 0.05 * r["d_exc2"]),
            "coverage_resid": 0.5 * (0.20 * r["d_cov"] + 0.05 * r["d_con"] + 0.05 * r["d_inp"]),
            "temporal": 0.25 * r["raw_t"], "state": 0.25 * r["raw_s"]}


def variant_scores(rows):
    """name -> list of scores (aligned with rows)."""
    comp = [components(r) for r in rows]
    names = ["call_topology", "bigrams", "exception", "coverage_resid", "temporal", "state"]
    out = {"full": [r["r_v5"] for r in rows]}
    for n in names:
        out[n] = [c[n] for c in comp]
        out["full-" + n] = [sum(v for k, v in c.items() if k != n) for c in comp]
    out["recomposed_full"] = [sum(c.values()) for c in comp]
    out["v3_only"] = [r["r_v3"] for r in rows]
    out["state_raw"] = [r["r_state"] for r in rows]
    return out


# ------------------------------------------------------------------------------------------------ bootstrap
def boot_vec(args):
    s, y, c, b, seed = args
    d = collections.defaultdict(list)
    for i, k in enumerate(c):
        d[k].append(i)
    keys = sorted(d)
    rng = random.Random(seed)
    vals = []
    for _ in range(b):
        idx = [i for _ in keys for i in d[keys[rng.randrange(len(keys))]]]
        yy = [y[i] for i in idx]
        vals.append(E.auroc([s[i] for i in idx], yy) if 0 < sum(yy) < len(yy) else None)
    return vals


def ci_from(vals):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    return [v[int(0.025 * n)], v[min(n - 1, int(math.ceil(0.975 * n)) - 1)]]


def paired_from(va, vb, obs):
    ds = sorted(a - b for a, b in zip(va, vb) if a is not None and b is not None)
    n = len(ds)
    p = 2 * min(sum(1 for v in ds if v <= 0), sum(1 for v in ds if v >= 0)) / n
    return {"delta": obs, "ci95": [ds[int(0.025 * n)], ds[min(n - 1, int(math.ceil(0.975 * n)) - 1)]],
            "p_two_sided_boot": min(1.0, max(p, 1.0 / n)), "n_resamples": n}


def swap_permutation(sa, sb, y, c, b=10000, seed=SEED):
    """Program-level paired swap test of H0: predictors A and B exchangeable. Statistic = pooled AUROC(A)-AUROC(B)."""
    d = collections.defaultdict(list)
    for i, k in enumerate(c):
        d[k].append(i)
    keys = sorted(d)
    obs = E.auroc(sa, y) - E.auroc(sb, y)
    rng = random.Random(seed)
    cnt = 0
    for _ in range(b):
        a2, b2 = list(sa), list(sb)
        for k in keys:
            if rng.random() < 0.5:
                for i in d[k]:
                    a2[i], b2[i] = sb[i], sa[i]
        if abs(E.auroc(a2, y) - E.auroc(b2, y)) >= abs(obs) - 1e-12:
            cnt += 1
    return {"delta": obs, "p_two_sided_swap": (cnt + 1) / (b + 1), "B": b}


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def per_program_auroc(rows, s):
    by = collections.defaultdict(list)
    for i, r in enumerate(rows):
        by[r["base_id"]].append(i)
    out = {}
    for k, idx in by.items():
        yy = [rows[i]["label"] for i in idx]
        out[k] = E.auroc([s[i] for i in idx], yy) if 0 < sum(yy) < len(yy) else None
    return out


def matched(rows, s):
    g = collections.defaultdict(dict)
    for i, r in enumerate(rows):
        g[r["group"]][r["label"]] = (i, r["base_id"], r["sc_type"])
    sets = []
    for v in g.values():
        if 0 in v and 1 in v:
            a, b = s[v[1][0]], s[v[0][0]]
            sets.append((v[1][1], v[1][2], 1.0 if a > b else 0.5 if a == b else 0.0))
    return sets


def conc_ci(sets, b=B, seed=SEED):
    by = collections.defaultdict(list)
    for p, _, v in sets:
        by[p].append(v)
    ks = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(b):
        sm = [v for k in (rng.choice(ks) for _ in ks) for v in by[k]]
        vals.append(sum(sm) / len(sm))
    vals.sort()
    return sum(v for _, _, v in sets) / len(sets), [vals[int(0.025 * b)], vals[int(0.975 * b) - 1]]


# ------------------------------------------------------------------------------------------------ main analysis
def analyse(pop_name, rows, train_thr_scores, pool, extra_variants=None):
    y = [r["label"] for r in rows]
    c = [r["base_id"] for r in rows]
    V = variant_scores(rows)
    if extra_variants:
        V.update(extra_variants)
    names = list(V)
    jobs = [(V[n], y, c, B, SEED) for n in names]
    boots = dict(zip(names, pool.map(boot_vec, jobs)))
    res = {"n": len(rows), "n_programs": len(set(c)), "n_changed": sum(y), "variants": {}, "paired_vs_full": {}}
    for n in names:
        s = V[n]
        thr = E.youden_threshold(train_thr_scores[n], train_thr_scores["_y"]) if n in train_thr_scores else None
        res["variants"][n] = {"auroc": E.auroc(s, y), "ci95": ci_from(boots[n]), "auprc": E.auprc(s, y),
                              "zero_rate_changed": sum(1 for a, b in zip(s, y) if b == 1 and a == 0) / sum(y),
                              "zero_rate_equiv": sum(1 for a, b in zip(s, y) if b == 0 and a == 0) / (len(y) - sum(y)),
                              "train_youden_threshold": thr,
                              "prf_at_train_threshold": E.prf(s, y, thr) if thr is not None else None}
    for n in names:
        if n == "full":
            continue
        res["paired_vs_full"][n] = paired_from(boots[n], boots["full"], res["variants"][n]["auroc"] - res["variants"]["full"]["auroc"])
    return res, V, boots, y, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    dev, train = read("v9c_dev"), read("v9c_train")
    pool_rows = train + dev
    # train scores used for thresholds (per variant)
    Vt = variant_scores(train)
    Vt["_y"] = [r["label"] for r in train]
    out = {"config": {"B": B, "seed": SEED, "family": FAMILY, "populations": {"v9c_train": len(train), "v9c_dev": len(dev),
                                                                              "pooled": len(pool_rows)}}}
    with mp.Pool(a.procs) as pool:
        for name, rows in (("pooled", pool_rows), ("v9c_train", train), ("v9c_dev", dev)):
            res, V, boots, y, c = analyse(name, rows, Vt, pool)
            # Holm over the declared family (bootstrap p-values vs full)
            pv = {n: res["paired_vs_full"][n]["p_two_sided_boot"] for n in FAMILY}
            hp = E.holm(pv)
            for n in FAMILY:
                res["paired_vs_full"][n]["holm_p_family12"] = hp[n]
            # key comparison state vs full: swap permutation, per-program deltas, matched concordance
            sf = res["paired_vs_full"]["state"]
            sf["swap_test"] = swap_permutation(V["state_raw"], V["full"], y, c, b=10000)
            ppa, ppb = per_program_auroc(rows, V["state_raw"]), per_program_auroc(rows, V["full"])
            diffs = {k: ppa[k] - ppb[k] for k in ppa if ppa[k] is not None and ppb[k] is not None}
            w = sum(1 for v in diffs.values() if v > 1e-12)
            l = sum(1 for v in diffs.values() if v < -1e-12)
            res["per_program_state_minus_full"] = {"n_programs": len(diffs), "state_better": w, "full_better": l, "ties": len(diffs) - w - l,
                                                   "sign_test_p": sign_test(w, l), "mean_delta": sum(diffs.values()) / len(diffs),
                                                   "median_delta": sorted(diffs.values())[len(diffs) // 2], "per_program": diffs}
            res["macro_auroc"] = {n: sum(v for v in per_program_auroc(rows, V[n]).values() if v is not None) /
                                  len([v for v in per_program_auroc(rows, V[n]).values() if v is not None]) for n in ("full", "state_raw", "v3_only", "temporal")} \
                if "temporal" in V else {}
            # matched-set concordance
            res["matched_concordance"] = {}
            for n in ("full", "state_raw", "v3_only", "temporal", "bigrams", "call_topology", "exception", "coverage_resid"):
                st = matched(rows, V[n])
                cc, ci = conc_ci(st)
                res["matched_concordance"][n] = {"concordance": cc, "ci95": ci, "n_sets": len(st)}
            ms, mf = matched(rows, V["state_raw"]), matched(rows, V["full"])
            res["matched_state_vs_full_sets"] = {"state_correct_full_wrong_or_tie": sum(1 for x, z in zip(ms, mf) if x[2] > z[2]),
                                                 "full_correct_state_wrong_or_tie": sum(1 for x, z in zip(ms, mf) if x[2] < z[2]),
                                                 "same": sum(1 for x, z in zip(ms, mf) if x[2] == z[2])}
            # zero-score decomposition of AUROC for full vs state
            res["zero_decomposition"] = {}
            for n in ("full", "state_raw"):
                s = V[n]
                pos = [s[i] for i in range(len(y)) if y[i] == 1]
                neg = [s[i] for i in range(len(y)) if y[i] == 0]
                nz = [v for v in neg if v == 0]
                nn = [v for v in neg if v > 0]

                def part(negs):
                    num = sum((1.0 if p > q else 0.5 if p == q else 0.0) for p in pos for q in negs)
                    return num / (len(pos) * len(negs)) if negs else None
                res["zero_decomposition"][n] = {
                    "share_equiv_at_zero": len(nz) / len(neg),
                    "auroc_vs_zero_equiv": part(nz), "auroc_vs_nonzero_equiv": part(nn),
                    "share_changed_at_zero": sum(1 for v in pos if v == 0) / len(pos)}
            # edit strata & per sc_type
            res["edit_strata"] = {n: E.edit_quantile_strata(rows, lambda r, n=n, V=V, rows=rows: V[n][rows.index(r)] if False else 0)
                                  for n in ()}
            idx_of = {id(r): i for i, r in enumerate(rows)}
            res["edit_strata"] = {}
            for n in ("full", "state_raw"):
                res["edit_strata"][n] = E.edit_quantile_strata(rows, lambda r, n=n: V[n][idx_of[id(r)]])
                res["edit_strata"][n + "_exact_edit"] = list(E.stratified_auroc_exact_edit(rows, lambda r, n=n: V[n][idx_of[id(r)]]))
            res["by_sc_type"] = {}
            eq_idx = [i for i in range(len(y)) if y[i] == 0]
            for sc in sorted({r["sc_type"] for r in rows if r["label"] == 1}):
                ch = [i for i in range(len(y)) if y[i] == 1 and rows[i]["sc_type"] == sc]
                res["by_sc_type"][sc] = {"n_changed": len(ch)}
                for n in ("full", "state_raw", "v3_only", "temporal", "bigrams", "call_topology", "exception", "coverage_resid"):
                    s = V[n]
                    num = sum((1.0 if s[i] > s[j] else 0.5 if s[i] == s[j] else 0.0) for i in ch for j in eq_idx)
                    res["by_sc_type"][sc][n] = {"auroc_vs_all_equiv": num / (len(ch) * len(eq_idx)),
                                                "zero_rate": sum(1 for i in ch if s[i] == 0) / len(ch)}
            out[name] = res
            print("done", name, res["variants"]["full"]["auroc"], res["variants"]["state"]["auroc"], res["variants"]["state_raw"]["auroc"], flush=True)
    # sanity: bootstrap CI reproduces eval_lib for one vector
    y_d = [r["label"] for r in dev]
    c_d = [r["base_id"] for r in dev]
    s_d = [r["r_v5"] for r in dev]
    out["sanity_ci_eval_lib_equal"] = E.cluster_bootstrap_ci(s_d, y_d, c_d) == out["v9c_dev"]["variants"]["full"]["ci95"]
    out["sanity_recomposed_vs_frozen_max_abs"] = max(abs(a - b) for a, b in zip(variant_scores(pool_rows)["recomposed_full"],
                                                                              [r["raw_v3"] * 0.5 + 0.25 * r["raw_t"] + 0.25 * r["raw_s"] for r in pool_rows]))
    json_path = OUT / "ablation_results.json"
    if json_path.exists():
        sys.exit("refusing to overwrite " + str(json_path))
    json_path.write_text(json.dumps(out, indent=1))
    # flat table
    with open(TAB / "WPC-003_ablation_auroc_table.csv", "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["population", "variant", "auroc", "ci_lo", "ci_hi", "auprc", "zero_rate_changed", "zero_rate_equiv", "delta_vs_full",
                    "delta_ci_lo", "delta_ci_hi", "p_boot", "holm_p_family12", "precision@trainYouden", "recall@trainYouden", "f1@trainYouden", "fpr@trainYouden"])
        for pop in ("pooled", "v9c_train", "v9c_dev"):
            for n, v in out[pop]["variants"].items():
                pv = out[pop]["paired_vs_full"].get(n)
                prf = v["prf_at_train_threshold"] or {}
                w.writerow([pop, n, round(v["auroc"], 4), round(v["ci95"][0], 4), round(v["ci95"][1], 4), round(v["auprc"], 4),
                            round(v["zero_rate_changed"], 4), round(v["zero_rate_equiv"], 4),
                            round(pv["delta"], 4) if pv else "", round(pv["ci95"][0], 4) if pv else "", round(pv["ci95"][1], 4) if pv else "",
                            pv["p_two_sided_boot"] if pv else "", pv.get("holm_p_family12", "") if pv else "",
                            round(prf.get("precision", 0), 4) if prf else "", round(prf.get("recall", 0), 4) if prf else "",
                            round(prf.get("f1", 0), 4) if prf else "", round(prf.get("fpr", 0), 4) if prf else ""])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""EXP-WPC-005 (state-variant / leakage test + mechanism analyses) and EXP-WPC-006 (return-value variants, pre-declared in
configs/WPC_RV_PREDECLARATION.json) -- PERMITTED data only (v9c_train primary minus math_gray_code, v9c_dev).

EVERYTHING here other than the frozen columns (`full`, `state_raw`, `v3_only`, `temporal`) is an EXPLORATORY modified representation
and must never be presented as original-SBG evidence.  v10_test and v9c_val are never read.
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import math
import multiprocessing as mp
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
WPC = HERE.parents[1]
PKG = WPC.parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(PKG / "experiments" / "common"))
import eval_lib as E                                                       # noqa: E402
import wpc_ablation as A                                                   # noqa: E402

OUT5 = WPC / "raw" / "EXP-WPC-005"
OUT6 = WPC / "raw" / "EXP-WPC-006"
B, SEED = A.B, A.SEED
LEAK_FAMILY = ["s_noret", "s_args", "s_args_noret", "s_boundary", "s_boundary_noret", "s_structure", "s_shuffle"]
RV_FAMILY = ["V5+RV_abs100", "V5+RV_abs_full", "V5+RV_type_abs", "S+RV_abs_full"]


def col(rows, k):
    return [r[k] for r in rows]


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j < len(o) and v[o[j]] == v[o[i]]:
            j += 1
        for k in range(i, j):
            r[o[k]] = (i + j + 1) / 2.0
        i = j
    return r


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return num / (da * db) if da and db else float("nan")


def eval_set(pool, rows, scores, ref, family=None, extra_ref=None):
    """AUROC+CI per variant and paired delta vs `ref` (+ optional second reference); Holm over `family`."""
    y, c = col(rows, "label"), col(rows, "base_id")
    names = list(scores)
    boots = dict(zip(names, pool.map(A.boot_vec, [(scores[n], y, c, B, SEED) for n in names])))
    res = {}
    for n in names:
        res[n] = {"auroc": E.auroc(scores[n], y), "ci95": A.ci_from(boots[n]), "auprc": E.auprc(scores[n], y),
                  "zero_rate_changed": sum(1 for a, b in zip(scores[n], y) if b == 1 and a == 0) / sum(y),
                  "zero_rate_equiv": sum(1 for a, b in zip(scores[n], y) if b == 0 and a == 0) / (len(y) - sum(y))}
        if extra_ref and n != extra_ref and extra_ref in boots:
            res[n]["vs_" + extra_ref] = A.paired_from(boots[n], boots[extra_ref], E.auroc(scores[n], y) - E.auroc(scores[extra_ref], y))
    # paired vs ref needs ref already in res: recompute pass
    for n in names:
        if n != ref:
            res[n]["vs_" + ref] = A.paired_from(boots[n], boots[ref], res[n]["auroc"] - res[ref]["auroc"])
    if family:
        hp = E.holm({n: res[n]["vs_" + ref]["p_two_sided_boot"] for n in family})
        for n in family:
            res[n]["vs_" + ref]["holm_p"] = hp[n]
    return res


def sc6_metrics(rows, s):
    y = col(rows, "label")
    eq = [i for i in range(len(y)) if y[i] == 0]
    ch = [i for i in range(len(y)) if y[i] == 1 and rows[i]["sc_type"] == "SC-6"]
    if not ch:
        return None
    auc = sum((1.0 if s[i] > s[j] else 0.5 if s[i] == s[j] else 0.0) for i in ch for j in eq) / (len(ch) * len(eq))
    sets = [t for t in A.matched(rows, s) if t[1] == "SC-6"]
    return {"n_sc6": len(ch), "zero_rate": sum(1 for i in ch if s[i] == 0) / len(ch), "auroc_vs_all_equiv": auc,
            "matched_concordance": sum(t[2] for t in sets) / len(sets), "n_matched_sets": len(sets),
            "n_sets_sc6_strictly_above_partner": sum(1 for t in sets if t[2] == 1.0),
            "n_sets_tied_with_partner": sum(1 for t in sets if t[2] == 0.5)}


def leak_diag():
    tot = collections.Counter()
    per = {}
    for split in ("v9c_dev", "v9c_train"):
        c = collections.Counter()
        for f in (WPC / "raw" / "EXP-WPC-001" / split).glob("*/*.json.gz"):
            d = json.load(gzip.open(f, "rt"))
            if d.get("ok") and "leakage_diag" in d:
                for k, v in d["leakage_diag"].items():
                    c[k] += v
                c["n_files"] += 1
                c["s0_equals_frozen_true"] += bool(d.get("s0_equals_frozen"))
        per[split] = dict(c)
        tot.update(c)
    return {"per_split": per, "total": dict(tot)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    OUT5.mkdir(parents=True, exist_ok=True)
    OUT6.mkdir(parents=True, exist_ok=True)
    dev, train = A.read("v9c_dev"), A.read("v9c_train")
    pooled = train + dev
    out5 = {"populations": {"pooled": len(pooled), "v9c_train": len(train), "v9c_dev": len(dev)}}
    out6 = {"predeclaration_sha256": open(WPC / "configs" / "WPC_RV_PREDECLARATION.sha256").read().split()[0]}

    def scores_for(rows):
        V = A.variant_scores(rows)
        v3, t, s = col(rows, "raw_v3"), col(rows, "raw_t"), col(rows, "raw_s")
        sc = {"full": V["full"], "state_raw": V["state_raw"], "v3_only": V["v3_only"], "temporal": col(rows, "r_temporal")}
        for n in ["s0"] + LEAK_FAMILY:
            sv = col(rows, "sv_" + n)
            sc["sv:" + n] = sv
            sc["full_with:" + n] = [min(1.0, max(0.0, 0.5 * a_ + 0.25 * b_ + 0.25 * c_)) for a_, b_, c_ in zip(v3, t, sv)]
        return V, sc

    with mp.Pool(a.procs) as pool:
        # ---------- EXP-WPC-005a: state variants (leakage test) ----------
        out5["state_variants"] = {}
        for name, rows in (("pooled", pooled), ("v9c_train", train), ("v9c_dev", dev)):
            V, sc = scores_for(rows)
            sub = {k: v for k, v in sc.items() if k.startswith("sv:") or k in ("full", "state_raw")}
            res = eval_set(pool, rows, sub, ref="sv:s0", family=["sv:" + n for n in LEAK_FAMILY])
            out5["state_variants"][name] = res
            sub2 = {k: v for k, v in sc.items() if k.startswith("full_with:") or k == "full"}
            out5.setdefault("full_with_state_variant", {})[name] = eval_set(pool, rows, sub2, ref="full")
            print("5a", name, round(res["sv:s0"]["auroc"], 4), {n: round(res["sv:" + n]["auroc"], 4) for n in LEAK_FAMILY}, flush=True)
        out5["s0_equals_frozen_state_auc_max_abs"] = max(abs(x - y) for x, y in zip(col(pooled, "sv_s0"), col(pooled, "raw_s")))
        out5["leakage_label_free_diagnostics"] = leak_diag()

        # ---------- EXP-WPC-005b: event-kind decomposition of the frozen state genome ----------
        out5["state_by_event_kind"] = {}
        for name, rows in (("pooled", pooled), ("v9c_dev", dev)):
            y = col(rows, "label")
            d = {}
            for k in [c_[3:] for c_ in rows[0] if c_.startswith("sk_")]:
                s = col(rows, "sk_" + k)
                d[k] = {"auroc": E.auroc(s, y), "nonzero_rate_changed": sum(1 for a_, b_ in zip(s, y) if b_ == 1 and a_ > 0) / sum(y),
                        "nonzero_rate_equiv": sum(1 for a_, b_ in zip(s, y) if b_ == 0 and a_ > 0) / (len(y) - sum(y))}
            out5["state_by_event_kind"][name] = d

        # ---------- EXP-WPC-005c: mechanism analyses on pooled ----------
        y = col(pooled, "label")
        V = A.variant_scores(pooled)
        comp_names = ["call_topology", "bigrams", "exception", "coverage_resid", "temporal", "state"]
        out5["spearman_all"] = {x: {z: spearman(V[x], V[z]) for z in comp_names} for x in comp_names}
        out5["spearman_equiv_only"] = {x: {z: spearman([v for v, l in zip(V[x], y) if l == 0], [v for v, l in zip(V[z], y) if l == 0])
                                           for z in comp_names} for x in comp_names}
        S, F = V["state_raw"], V["full"]
        Rest = [(f - 0.25 * s) / 0.75 for f, s in zip(F, S)]
        # (Rest = (0.5*V3+0.25*T)/0.75 ; state weight w -> w*S+(1-w)*Rest ; V5 corresponds to w=0.25)
        sw = {}
        for w in [i / 20 for i in range(21)]:
            sc_ = [w * s_ + (1 - w) * r_ for s_, r_ in zip(S, Rest)]
            sw[f"{w:.2f}"] = {"pooled": E.auroc(sc_, y),
                              "v9c_train": E.auroc(sc_[:len(train)], [r["label"] for r in train]),
                              "v9c_dev": E.auroc(sc_[len(train):], [r["label"] for r in dev])}
        out5["state_weight_sweep"] = sw
        ch = [i for i in range(len(y)) if y[i] == 1]
        out5["complementarity_changed"] = {
            "n_changed": len(ch),
            "state_only_nonzero": sum(1 for i in ch if S[i] > 0 and Rest[i] == 0),
            "rest_only_nonzero": sum(1 for i in ch if S[i] == 0 and Rest[i] > 0),
            "both_nonzero": sum(1 for i in ch if S[i] > 0 and Rest[i] > 0),
            "both_zero": sum(1 for i in ch if S[i] == 0 and Rest[i] == 0)}
        eq = [i for i in range(len(y)) if y[i] == 0]
        out5["complementarity_equiv"] = {
            "n_equiv": len(eq),
            "state_only_nonzero": sum(1 for i in eq if S[i] > 0 and Rest[i] == 0),
            "rest_only_nonzero": sum(1 for i in eq if S[i] == 0 and Rest[i] > 0),
            "both_nonzero": sum(1 for i in eq if S[i] > 0 and Rest[i] > 0),
            "both_zero": sum(1 for i in eq if S[i] == 0 and Rest[i] == 0)}
        # equivalent pairs by SP transform: where does the V5 'false-positive mass' come from?
        by_sp = {}
        for sp in sorted({r["sp_type"] for r in pooled if r["label"] == 0}):
            idx = [i for i in range(len(y)) if y[i] == 0 and pooled[i]["sp_type"] == sp]
            by_sp[sp] = {"n_equiv": len(idx)}
            for n in ("full", "state_raw", "v3_only", "temporal", "coverage_resid", "call_topology", "bigrams", "exception"):
                s_ = V[n]
                by_sp[sp][n] = {"nonzero_rate": sum(1 for i in idx if s_[i] > 0) / len(idx), "mean": sum(s_[i] for i in idx) / len(idx)}
        out5["equiv_by_sp_type"] = by_sp
        # fitted combiner (exploratory): fit on train only, evaluate on dev
        tr_V = A.variant_scores(train)
        feats = ["call_topology", "bigrams", "exception", "coverage_resid", "temporal", "state"]
        Xt = [[tr_V[f][i] for f in feats] for i in range(len(train))]
        m6 = E.fit_logistic(Xt, [r["label"] for r in train], l2=1.0, lr=0.5, iters=1500)
        dev_V = A.variant_scores(dev)
        s6 = [E.logit_score(m6, [dev_V[f][i] for f in feats]) for i in range(len(dev))]
        tr_rest = [(f - 0.25 * s) / 0.75 for f, s in zip(tr_V["full"], tr_V["state_raw"])]
        m2 = E.fit_logistic([[s, r] for s, r in zip(tr_V["state_raw"], tr_rest)], [r["label"] for r in train], l2=1.0, lr=0.5, iters=1500)
        dev_rest = [(f - 0.25 * s) / 0.75 for f, s in zip(dev_V["full"], dev_V["state_raw"])]
        s2 = [E.logit_score(m2, [s, r]) for s, r in zip(dev_V["state_raw"], dev_rest)]
        comb = eval_set(pool, dev, {"full": dev_V["full"], "state_raw": dev_V["state_raw"], "logit6_fit_on_train": s6,
                                    "logit2_state_rest_fit_on_train": s2}, ref="full", extra_ref="state_raw")
        out5["fitted_combiner_dev"] = {"results": comb, "weights_6": dict(zip(feats, m6["w"])), "b6": m6["b"],
                                       "weights_2(state,rest)": m2["w"], "b2": m2["b"]}
        print("5c combiner dev", {k: round(v["auroc"], 4) for k, v in comb.items()}, flush=True)

        # ---------- EXP-WPC-006: return-value variants ----------
        out6["populations"] = {"pooled": len(pooled), "v9c_train": len(train), "v9c_dev": len(dev)}
        out6["results"] = {}
        for name, rows in (("v9c_dev", dev), ("v9c_train", train), ("pooled", pooled)):
            V = A.variant_scores(rows)
            v5, st = V["full"], V["state_raw"]
            r100, rfull, rtype = col(rows, "rv_abs100"), col(rows, "rv_abs_full"), col(rows, "rv_type_abs")
            sc = {"V5(frozen)": v5, "State(frozen)": st,
                  "RV_abs100": r100, "RV_abs_full": rfull, "RV_type_abs": rtype,
                  "V5+RV_abs100": [0.8 * a_ + 0.2 * b_ for a_, b_ in zip(v5, r100)],
                  "V5+RV_abs_full": [0.8 * a_ + 0.2 * b_ for a_, b_ in zip(v5, rfull)],
                  "V5+RV_type_abs": [0.8 * a_ + 0.2 * b_ for a_, b_ in zip(v5, rtype)],
                  "S+RV_abs_full": [0.8 * a_ + 0.2 * b_ for a_, b_ in zip(st, rfull)],
                  "ceiling_rv_hash": col(rows, "rv_hash"), "ceiling_rv_entry_hash": col(rows, "rv_entry_hash")}
            res = eval_set(pool, rows, sc, ref="V5(frozen)", family=RV_FAMILY, extra_ref="State(frozen)")
            for n in sc:
                res[n]["sc6"] = sc6_metrics(rows, sc[n])
            out6["results"][name] = res
            print("6", name, {n: round(res[n]["auroc"], 4) for n in sc}, flush=True)
        out6["note"] = "EXPLORATORY modified representations; ceiling_* rows are label-oracle ceilings (output comparison on the protocol inputs), not competitors."

    for path, obj in ((OUT5 / "variants_results.json", out5), (OUT6 / "rv_results.json", out6)):
        if path.exists():
            sys.exit("refusing to overwrite " + str(path))
        path.write_text(json.dumps(obj, indent=1))


if __name__ == "__main__":
    main()

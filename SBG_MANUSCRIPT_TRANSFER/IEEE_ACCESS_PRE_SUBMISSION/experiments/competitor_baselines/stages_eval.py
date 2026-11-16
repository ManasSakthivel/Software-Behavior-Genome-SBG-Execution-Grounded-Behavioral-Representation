"""Evaluation stages: fit (train fit + dev selection + freeze), heldout (val/test scored once), incremental (incremental-value matrix)."""
from __future__ import annotations

import collections
import hashlib
import json
import multiprocessing
import pickle
import time

import bench_lib as BL
import models
from bench_lib import RAW, assemble, col, labels, clusters, families, eval_lib

HELD = BL.HELD
_G = {}
MODEL_NAMES = {"LR_E": "E", "LR_X": "X", "LR_EX": "EX", "LR_EXx": "EXx", "LR_Xx": "Xx"}
TREE_SPECS = [c for c in families()["forest_nonlinear*"]]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ------------------------------------------------------------------ model jobs (fork-pool, train rows in _G)
def _job(spec):
    rows = _G["train"]
    if spec[0] == "lr":
        return spec, BL.fit_lr(rows, spec[1])
    return spec, BL.fit_tree_model(rows, spec[1])


def _fit_all(specs):
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(4) as pool:
        return dict((s, m) for s, m in pool.imap_unordered(_job, specs))


def attach_models(rows, M, inc=None):
    """Write model scores into row['S'] under their config names."""
    for name, fs in MODEL_NAMES.items():
        for r, v in zip(rows, BL.score_lr(M[("lr", tuple(BL.FEATS[fs]))], rows, BL.FEATS[fs])):
            r["S"][name] = v
    for spec in TREE_SPECS:
        for r, v in zip(rows, BL.score_tree(M[("tree", spec)], rows)):
            r["S"][spec] = v
    for name, (feats, key) in (inc or {}).items():
        for r, v in zip(rows, BL.score_lr(M[("inc", name)], rows, feats)):
            r["S"][name] = v


def all_config_keys():
    F = families()
    keys = []
    for fam, cs in F.items():
        keys += cs
    keys += [c for cs in BL.DIAG.values() for c in cs]
    return list(dict.fromkeys(keys))


# ------------------------------------------------------------------ FIT stage
def stage_fit():
    t0 = time.time()
    tr, m1 = assemble("v9c_train")
    dv, m2 = assemble("v9c_dev")
    tr = [r for r in tr if r["S"].get("_trace_ok")]   # drop trace-missing train rows (math_gray_code: dump never completed)
    dv = [r for r in dv if r["S"].get("_trace_ok")]
    print("train rows", len(tr), "dev rows", len(dv), "trace-missing dropped", m1, m2)
    _G["train"] = tr
    specs = [("lr", tuple(BL.FEATS[fs])) for fs in MODEL_NAMES.values()] + [("tree", s) for s in TREE_SPECS]
    M = dict(_fit_all(specs))
    attach_models(tr, M)
    attach_models(dv, M)
    keys = all_config_keys()
    ytr, ydv = labels(tr), labels(dv)
    table = {}
    for k in keys:
        s_tr, s_dv = col(tr, k), col(dv, k)
        table[k] = {"train_auroc": eval_lib.auroc(s_tr, ytr), "dev_auroc": eval_lib.auroc(s_dv, ydv)}
    # selection (dev only; ties -> declared order)
    sel = {}
    for fam, cs in families().items():
        best = max(cs, key=lambda c: (round(table[c]["dev_auroc"], 12), -cs.index(c)))
        sel[fam] = {"representative": best, "dev_auroc": table[best]["dev_auroc"], "candidates": {c: table[c]["dev_auroc"] for c in cs}}
    # incremental models (reps resolved)
    def xkey(x):
        return sel[x]["representative"] if x.endswith("*") else x
    inc_specs, inc_names = [], {}
    for bname in ("EX", "EXx"):
        for x in BL.INC_X:
            name = f"INC|{bname}+{xkey(x)}"
            feats = BL.FEATS[bname] + [xkey(x)]
            inc_names[name] = (feats, xkey(x))
            inc_specs.append(("lr", tuple(feats)))
    M.update(_fit_all(list(dict.fromkeys(inc_specs))))
    for name, (feats, _) in inc_names.items():
        M[("inc", name)] = M[("lr", tuple(feats))]
    # thresholds (Youden on TRAIN scores of the same predictor) for representatives + references
    attach_models(tr, M, inc_names)
    attach_models(dv, M, inc_names)
    thr = {}
    need = {sel[f]["representative"] for f in sel} | {"edit", "edit_rev", "sbg_v5"} | set(inc_names)
    for k in sorted(need):
        if k.startswith("forest|RF"):
            s = M[("tree", k)]["model"].oob_scores(BL.design(tr, M[("tree", k)]["feats"]))
        else:
            s = col(tr, k)
        thr[k] = eval_lib.youden_threshold(s, ytr)
    frozen = {"representatives": {f: sel[f]["representative"] for f in sel}, "thresholds_train_youden": thr, "inc_names": {k: v[0] for k, v in inc_names.items()},
              "train_pop_sha": json.loads(open(BL.PKG / "configs/populations/SUMMARY.json").read())["v9c_train"]["sha256"]}
    out = RAW / "EXP-A4-004"
    BL.jdump(out / "selection.json", sel)
    BL.jdump(out / "frozen_config.json", frozen)
    BL.jdump(out / "config_train_dev_auroc.json", table)
    with open(out / "models.pkl", "wb") as f:
        pickle.dump({k: v for k, v in M.items()}, f)
    print("fit+selection done in", round(time.time() - t0), "s")
    for f, v in sel.items():
        print(f"  {f:26s} rep={v['representative']:50s} dev AUROC {v['dev_auroc']:.4f}")
    print("models.pkl sha256", sha(out / "models.pkl"))


# ------------------------------------------------------------------ HELD-OUT stage
def _stat_job(k):
    rows, key = _G["rows"], k
    s, y, c = col(rows, key), labels(rows), clusters(rows)
    out = {"name": key, "auroc": eval_lib.auroc(s, y), "auroc_ci95": eval_lib.cluster_bootstrap_ci(s, y, c), "auprc": eval_lib.auprc(s, y)}
    if key in _G["full"]:
        out["perm_p_one_sided"] = eval_lib.cluster_permutation_p(s, y, c)
        if key != "sbg_v5":
            out["delta_v5_minus"] = eval_lib.paired_delta(col(rows, "sbg_v5"), s, y, c)
    return out


def _detail(rows, key, thr, v5key="sbg_v5"):
    s, y = col(rows, key), labels(rows)
    d = {}
    if thr is not None:
        d["threshold_train_youden"] = thr
        d["prf"] = eval_lib.prf(s, y, thr)
    k = lambda r: r["S"].get(key, 0.0)  # noqa: E731
    d["matched_concordance"] = eval_lib.matched_concordance(rows, k)
    ex = eval_lib.stratified_auroc_exact_edit(rows, k)
    d["exact_edit_auroc"], d["exact_edit_n_cross"] = ex
    d["edit_quantile_strata"] = eval_lib.edit_quantile_strata(rows, k)
    d["cliff_delta"] = 2 * eval_lib.auroc(s, y) - 1
    sc = {}
    for t in sorted({r["sc_type"] for r in rows if r["sc_type"]}):
        sub = [r for r in rows if r["label"] == 0 or r["sc_type"] == t]
        sc[t] = {"n_changed": sum(1 for r in sub if r["label"] == 1), "auroc": eval_lib.auroc([k(r) for r in sub], [r["label"] for r in sub])}
    d["auroc_by_sc_type"] = sc
    if thr is not None:
        fp = {}
        for t in sorted({r["transformation_type"] for r in rows if r["label"] == 0}):
            sub = [r for r in rows if r["label"] == 0 and r["transformation_type"] == t]
            fp[t] = {"n": len(sub), "fpr": sum(1 for r in sub if k(r) >= thr) / len(sub)}
        d["fpr_by_sp_type_equivalent"] = fp
    pp = {}
    for b in sorted({r["base_id"] for r in rows}):
        sub = [r for r in rows if r["base_id"] == b]
        pp[b] = eval_lib.auroc([k(r) for r in sub], [r["label"] for r in sub])
    d["per_program_auroc"] = pp
    return d


def stage_heldout(pops):
    out = RAW / "EXP-A4-005"
    frozen = json.loads((RAW / "EXP-A4-004" / "frozen_config.json").read_text())
    with open(RAW / "EXP-A4-004" / "models.pkl", "rb") as f:
        M = pickle.load(f)
    reps = frozen["representatives"]
    thr = frozen["thresholds_train_youden"]
    F = families()
    for pop in pops:
        t0 = time.time()
        rows, miss = assemble(pop)
        attach_models(rows, M, {k: (v, None) for k, v in frozen["inc_names"].items()})
        keys = ["sbg_v5"] + all_config_keys() + (["sbg_v6", "sbg_state_v6"] if pop == "v10_test" else [])
        keys = list(dict.fromkeys(keys + [k for k in frozen["inc_names"]]))
        full = set(reps.values()) | {"sbg_v5", "edit", "edit_rev", "sbg_v6", "sbg_state_v6", "sbg_v3", "sbg_temporal", "sbg_state"} | set(frozen["inc_names"])
        _G["rows"], _G["full"] = rows, full
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(4) as pool:
            stats = {r["name"]: r for r in pool.imap_unordered(_stat_job, [k for k in keys if k in rows[0]["S"]])}
        res = {"pop": pop, "n": len(rows), "n_programs": len({r["base_id"] for r in rows}), "n_changed": sum(labels(rows)), "trace_missing": miss,
               "indep_covered": sum(1 for r in rows if r["_indep_covered"]), "configs": stats, "detail": {}}
        # Holm families
        fam_p, fam_perm = {}, {}
        for fam, rep in reps.items():
            fam_p[fam] = stats[rep]["delta_v5_minus"]["p_two_sided"] if rep != "sbg_v5" else 1.0
            fam_perm[fam] = stats[rep]["perm_p_one_sided"]
        fam_perm["SBG_V5"] = stats["sbg_v5"]["perm_p_one_sided"]
        res["holm_delta_v5_vs_rep"] = {"raw_p": fam_p, "holm_p": eval_lib.holm(fam_p)}
        res["holm_perm_vs_chance"] = {"raw_p": fam_perm, "holm_p": eval_lib.holm(fam_perm)}
        detail_keys = sorted(full & set(rows[0]["S"]))
        for k in detail_keys:
            res["detail"][k] = _detail(rows, k, thr.get(k))
        v5 = res["detail"]["sbg_v5"]["per_program_auroc"]
        for k, d in res["detail"].items():
            pp = d["per_program_auroc"]
            d["n_programs_beating_v5"] = sum(1.0 if pp[b] > v5[b] else 0.5 if pp[b] == v5[b] else 0.0 for b in pp)
        # indep covered-subset version
        cov = [r for r in rows if r["_indep_covered"]]
        if cov and len(cov) < len(rows):
            res["output_indep_covered_subset"] = {"n": len(cov), "auroc": eval_lib.auroc(col(cov, "output_indep|frac40"), labels(cov)),
                                                  "sbg_v5_auroc": eval_lib.auroc(col(cov, "sbg_v5"), labels(cov))}
        BL.jdump(out / f"heldout_{pop}.json", res)
        print(pop, "held-out scored in", round(time.time() - t0), "s;", "SBG V5 AUROC", round(stats["sbg_v5"]["auroc"], 4), stats["sbg_v5"]["auroc_ci95"])


# ------------------------------------------------------------------ INCREMENTAL stage
def _lopo(rows, feats, l2=1.0):
    y = labels(rows)
    progs = sorted({r["base_id"] for r in rows})
    oof = [0.0] * len(rows)
    for p in progs:
        tr = [i for i, r in enumerate(rows) if r["base_id"] != p]
        te = [i for i, r in enumerate(rows) if r["base_id"] == p]
        X = [[rows[i]["S"].get(f, 0.0) for f in feats] for i in tr]
        m = models.fit_logistic_irls(X, [y[i] for i in tr], l2)
        for i in te:
            oof[i] = eval_lib.logit_score(m, [rows[i]["S"].get(f, 0.0) for f in feats])
    return oof


def _lopo_job(args):
    pop, name, feats = args
    return name, _lopo(_G["rows_by_pop"][pop], feats)


def stage_incremental(pops):
    out = RAW / "EXP-A4-006"
    frozen = json.loads((RAW / "EXP-A4-004" / "frozen_config.json").read_text())
    with open(RAW / "EXP-A4-004" / "models.pkl", "rb") as f:
        M = pickle.load(f)
    inc_feats = frozen["inc_names"]
    sel = json.loads((RAW / "EXP-A4-004" / "selection.json").read_text())
    res = {}
    rbp = {}
    for pop in pops:
        rows, _ = assemble(pop)
        attach_models(rows, M, {k: (v, None) for k, v in inc_feats.items()})
        rbp[pop] = rows
        y, c = labels(rows), clusters(rows)
        r = {"base_auroc": {}, "deltas": {}}
        for bname, bm in (("EX", "LR_EX"), ("EXx", "LR_EXx")):
            sb = col(rows, bm)
            r["base_auroc"][bname] = {"auroc": eval_lib.auroc(sb, y), "ci95": eval_lib.cluster_bootstrap_ci(sb, y, c)}
            fam = {}
            for name in [n for n in inc_feats if n.startswith(f"INC|{bname}+")]:
                sx = col(rows, name)
                d = eval_lib.paired_delta(sx, sb, y, c)
                d["combo_auroc"], d["combo_ci95"] = eval_lib.auroc(sx, y), eval_lib.cluster_bootstrap_ci(sx, y, c)
                d["X"] = name.split("+", 1)[1]
                r["deltas"][name] = d
                fam[name] = d["p_two_sided"]
            r.setdefault("holm", {})[bname] = eval_lib.holm(fam)
        res[pop] = r
        print(pop, "EX base", round(r["base_auroc"]["EX"]["auroc"], 4), "; Δ(EX+sbg_v5 − EX) =", round(r["deltas"]["INC|EX+sbg_v5"]["delta"], 4), r["deltas"]["INC|EX+sbg_v5"]["ci95"],
              "p", r["deltas"]["INC|EX+sbg_v5"]["p_two_sided"])
    # exploratory leave-one-program-out refit INSIDE the held-out population (labelled exploratory)
    _G["rows_by_pop"] = rbp
    jobs = []
    for pop in pops:
        jobs.append((pop, "EX", BL.FEATS["EX"]))
        for x in ("sbg_v5", "sbg_state", sel["traceseq_rename_robust*"]["representative"], sel["valuespectra*"]["representative"]):
            jobs.append((pop, f"EX+{x}", BL.FEATS["EX"] + [x]))
        jobs.append((pop, "V5alone", ["sbg_v5"]))
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(4) as pool:
        outs = pool.map(_lopo_job, jobs)
    lopo = {}
    for (pop, name, _), (_, oof) in zip(jobs, outs):
        lopo.setdefault(pop, {})[name] = oof
    for pop in pops:
        rows = rbp[pop]
        y, c = labels(rows), clusters(rows)
        res[pop]["lopo_exploratory"] = {"base_EX_auroc": eval_lib.auroc(lopo[pop]["EX"], y), "base_EX_ci95": eval_lib.cluster_bootstrap_ci(lopo[pop]["EX"], y, c)}
        res[pop]["lopo_exploratory"]["note"] = "EXPLORATORY: refit on the other programs of the SAME held-out population (IRLS, same L2 objective); pooled out-of-fold scores"
        for name, oof in lopo[pop].items():
            if name.startswith("EX+"):
                d = eval_lib.paired_delta(oof, lopo[pop]["EX"], y, c)
                d["combo_auroc"] = eval_lib.auroc(oof, y)
                res[pop]["lopo_exploratory"][name] = d
        res[pop]["lopo_exploratory"]["V5alone_auroc"] = eval_lib.auroc(lopo[pop]["V5alone"], y)
    BL.jdump(out / "incremental.json", res)
    for pop in pops:
        print(pop, "LOPO EX", round(res[pop]["lopo_exploratory"]["base_EX_auroc"], 4), "EX+V5", round(res[pop]["lopo_exploratory"]["EX+sbg_v5"]["combo_auroc"], 4))


def run(stage, pops):
    if stage == "fit":
        stage_fit()
    elif stage == "heldout":
        stage_heldout([p for p in pops if p in HELD])
    elif stage == "incremental":
        stage_incremental([p for p in pops if p in HELD])
    else:
        raise SystemExit("unknown stage " + stage)

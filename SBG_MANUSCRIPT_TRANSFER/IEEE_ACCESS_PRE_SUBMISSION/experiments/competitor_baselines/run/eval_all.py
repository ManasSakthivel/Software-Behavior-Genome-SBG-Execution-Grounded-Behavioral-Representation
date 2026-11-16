#!/usr/bin/env python3
"""A4C evaluation (EXP-A4C-004 main matrix, EXP-A4C-005 incremental value + exploratory LOPO + sensitivities).

Reads ONLY the prediction files written by run_all.py (+ the frozen population rows for edit/sc_type/transformation_type) and uses eval_lib for every statistic.
  --stage main   --pop P   results matrix, paired deltas vs SBG V5, Holm, permutation, stratification, per-program table  -> EXP-A4C-004/eval_<pop>.json
  --stage inc              incremental-value matrix (+ exploratory LOPO)                                                    -> EXP-A4C-005/incremental.json
  --stage sens             v9c_val clean-subset + de-duplicated-AST sensitivity of the representatives                       -> EXP-A4C-005/sensitivity.json
Run: PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 <py313> eval_all.py --stage main --pop v10_test
"""
from __future__ import annotations

import argparse
import os
import ast
import collections
import csv
import hashlib
import json
import multiprocessing
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a4c_common as C  # noqa: E402
from a4c_common import RAW, PKG, TAB, EXP_EVAL, EXP_INC, eval_lib, jdump, jload  # noqa: E402

WORKERS = 3
_D = {}
EVAL_POPS = tuple(os.environ.get("A4C_POPS", "v9c_val,v10_test").split(","))   # test hook: A4C_POPS=v9c_dev for smoke tests on non-held-out data


# ------------------------------------------------------------------ loading
def pred_dirs():
    return sorted(p.parent for p in RAW.glob("EXP-A4C-*/predictions/meta.json"))


def load_all(pop):
    """-> rows (population rows in order, with edit/sc_type/...), preds {method: [scores]}, meta {method: meta}"""
    rows = eval_lib.load_population(pop)
    order = [r["pair_id"] for r in rows]
    preds, meta = {}, {}
    for pd in pred_dirs():
        m = jload(pd / "meta.json")["methods"]
        for fp in sorted((pd / pop).glob("*.json")):
            if fp.name.startswith("_"):
                continue
            d = json.loads(fp.read_text())
            name = fp.stem
            ids = [x["pair_id"] for x in d["rows"]]
            if ids != order:                 # permit different order but identical set
                pos = {x["pair_id"]: x["score"] for x in d["rows"]}
                if set(pos) != set(order):
                    print("WARN row-set mismatch", pd.name, pop, name)
                    continue
                sc = [pos[i] for i in order]
            else:
                sc = [x["score"] for x in d["rows"]]
            preds[name] = sc
            meta[name] = {**m.get(name, {"method": d.get("method", name), "role": "unknown"}), "exp_dir": pd.parent.name}
    for r in rows:
        r["S"] = {}
    return rows, preds, meta


def with_scores(rows, scores):
    for r, s in zip(rows, scores):
        r["_s"] = s
    return rows


# ------------------------------------------------------------------ per-method statistics
def light(name):
    s = _D["preds"][name]
    y, c = _D["y"], _D["c"]
    return {"auroc": eval_lib.auroc(s, y), "auroc_ci95": eval_lib.cluster_bootstrap_ci(s, y, c), "auprc": eval_lib.auprc(s, y)}


def detail(name):
    rows, preds, meta = _D["rows"], _D["preds"], _D["meta"]
    s, y, c = preds[name], _D["y"], _D["c"]
    thr = meta[name].get("train_threshold_youden")
    d = {}
    if thr is not None:
        d["threshold_train_youden"] = thr
        d["prf"] = eval_lib.prf(s, y, thr)
    keyed = [{"edit": r["edit"], "label": r["label"], "group": r["group"], "base_id": r["base_id"], "k": v} for r, v in zip(rows, s)]
    kf = lambda r: r["k"]  # noqa: E731
    d["perm_p_one_sided_vs_0.5"] = eval_lib.cluster_permutation_p(s, y, c)
    d["matched_concordance"] = eval_lib.matched_concordance(keyed, kf)
    d["exact_edit_auroc"], d["exact_edit_n_cross"] = eval_lib.stratified_auroc_exact_edit(keyed, kf)
    d["edit_quantile_strata"] = eval_lib.edit_quantile_strata(keyed, kf)
    d["cliff_delta"] = 2 * eval_lib.auroc(s, y) - 1
    sc = {}
    for t in sorted({r["sc_type"] for r in rows if r["sc_type"]}):
        idx = [i for i, r in enumerate(rows) if r["label"] == 0 or r["sc_type"] == t]
        sc[t] = {"n_changed": sum(1 for i in idx if y[i] == 1), "auroc": eval_lib.auroc([s[i] for i in idx], [y[i] for i in idx])}
    d["auroc_by_sc_type"] = sc
    if thr is not None:
        fp = {}
        for t in sorted({r["transformation_type"] for r in rows if r["label"] == 0}):
            idx = [i for i, r in enumerate(rows) if r["label"] == 0 and r["transformation_type"] == t]
            fp[t] = {"n": len(idx), "fpr": sum(1 for i in idx if s[i] >= thr) / len(idx)}
        d["fpr_by_sp_type_equivalent"] = fp
    pp = {}
    for b in sorted(set(c)):
        idx = [i for i, cc in enumerate(c) if cc == b]
        pp[b] = eval_lib.auroc([s[i] for i in idx], [y[i] for i in idx])
    d["per_program_auroc"] = pp
    return d


def vs_v5(name):
    s, v5 = _D["preds"][name], _D["preds"]["sbg_v5"]
    return eval_lib.paired_delta(v5, s, _D["y"], _D["c"])      # AUROC(V5) - AUROC(method)


def job(task):
    kind, name = task
    if kind == "light":
        return task, light(name)
    if kind == "detail":
        return task, detail(name)
    if kind == "delta":
        return task, vs_v5(name)
    raise ValueError(kind)


def pmap(tasks):
    out = {}
    t0 = time.time()
    with multiprocessing.get_context("fork").Pool(WORKERS) as pool:
        for i, (task, res) in enumerate(pool.imap_unordered(job, tasks, chunksize=1)):
            out[task] = res
            if i % 25 == 0:
                print(f"   {i + 1}/{len(tasks)} ({time.time() - t0:.0f}s)", flush=True)
    return out


def stage_main(pop):
    rows, preds, meta = load_all(pop)
    if "sbg_v5" not in preds:
        raise SystemExit("sbg_v5 predictions missing")
    _D.update(rows=rows, preds=preds, meta=meta, y=[r["label"] for r in rows], c=[r["base_id"] for r in rows])
    reps = [n for n, m in meta.items() if m.get("role") in ("representative", "reference")]
    comp = [n for n, m in meta.items() if m.get("role") == "competitor_representative"]
    full = sorted(set(reps) | set(comp) | {"sbg_v5", "edit", "edit_rev", "sbg_v6", "sbg_state_v6"} & set(preds) |
                  {n for n, m in meta.items() if m.get("role") in ("incremental", "diagnostic", "competitor")})
    full = [n for n in full if n in preds]
    tasks = [("light", n) for n in sorted(preds)] + [("detail", n) for n in full] + [("delta", n) for n in full if n != "sbg_v5"]
    t0 = time.time()
    res = pmap(tasks)
    out = {"pop": pop, "n": len(rows), "n_programs": len(set(_D["c"])), "n_changed": sum(_D["y"]), "methods": {}, "seconds": 0}
    for n in sorted(preds):
        m = {"meta": {k: v for k, v in meta[n].items() if k not in ("config",)}, **res[("light", n)]}
        if ("detail", n) in res:
            m["detail"] = res[("detail", n)]
        if ("delta", n) in res:
            m["delta_v5_minus_method"] = res[("delta", n)]
        out["methods"][n] = m
    # n programs beating V5 (ties 0.5)
    v5pp = out["methods"]["sbg_v5"]["detail"]["per_program_auroc"]
    for n, m in out["methods"].items():
        if "detail" in m:
            pp = m["detail"]["per_program_auroc"]
            m["detail"]["n_programs_beating_v5"] = sum(1.0 if pp[b] > v5pp[b] else 0.5 if pp[b] == v5pp[b] else 0.0 for b in pp)
    # Holm over the pre-declared family (plan §3; representatives of the 19 families) and over the extended family (+ A4B competitors)
    frozen = jload(RAW / C.EXP_FIT / "frozen_config.json")
    fam = {f: n for f, n in frozen["representatives"].items() if n != "sbg_v5" and n in out["methods"]}
    praw = {f: out["methods"][n]["delta_v5_minus_method"]["p_two_sided"] for f, n in fam.items()}
    out["holm_family_plan"] = {"members": fam, "raw_p": praw, "holm_p": eval_lib.holm(praw), "m": len(praw)}
    comps = {n: out["methods"][n]["delta_v5_minus_method"]["p_two_sided"] for n in comp}
    if comps:
        pe = {**{f"fam:{f}": p for f, p in praw.items()}, **{f"comp:{n}": p for n, p in comps.items()}}
        out["holm_family_extended"] = {"raw_p": pe, "holm_p": eval_lib.holm(pe), "m": len(pe)}
    pperm = {n: out["methods"][n]["detail"]["perm_p_one_sided_vs_0.5"] for n in set(fam.values()) | {"sbg_v5"} | set(comp)}
    out["holm_perm_vs_chance"] = {"raw_p": pperm, "holm_p": eval_lib.holm(pperm)}
    out["seconds"] = time.time() - t0
    jdump(RAW / EXP_EVAL / f"eval_{pop}.json", out)
    write_main_csv(pop, out)
    v = out["methods"]["sbg_v5"]
    print(f"{pop}: SBG V5 AUROC {v['auroc']:.4f} {v['auroc_ci95']}; {len(preds)} methods; {time.time() - t0:.0f}s")


def fmt_ci(ci):
    return f"[{ci[0]:.4f}, {ci[1]:.4f}]"


def write_main_csv(pop, out):
    f = TAB / f"EXP-A4C-004_{pop}_results_matrix.csv"
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["method", "family", "role", "label", "privileged", "auroc", "ci_lo", "ci_hi", "auprc", "threshold", "precision", "recall", "f1", "fpr", "perm_p", "matched_conc", "exact_edit_auroc",
                    "cliff_delta", "delta_v5_minus", "delta_ci_lo", "delta_ci_hi", "delta_p", "n_prog_beating_v5"])
        for n, m in sorted(out["methods"].items(), key=lambda kv: -kv[1]["auroc"]):
            d, dl, mt = m.get("detail"), m.get("delta_v5_minus_method"), m["meta"]
            prf = (d or {}).get("prf") or {}
            w.writerow([mt.get("method", n), mt.get("family"), mt.get("role"), mt.get("label"), mt.get("privileged_output_reading"), round(m["auroc"], 4), round(m["auroc_ci95"][0], 4),
                        round(m["auroc_ci95"][1], 4), round(m["auprc"], 4), (d or {}).get("threshold_train_youden"), prf.get("precision"), prf.get("recall"), prf.get("f1"), prf.get("fpr"),
                        (d or {}).get("perm_p_one_sided_vs_0.5"), ((d or {}).get("matched_concordance") or {}).get("concordance"), (d or {}).get("exact_edit_auroc"),
                        (d or {}).get("cliff_delta"), dl and dl["delta"], dl and dl["ci95"][0], dl and dl["ci95"][1], dl and dl["p_two_sided"], (d or {}).get("n_programs_beating_v5")])


# ------------------------------------------------------------------ incremental value
def inc_job(task):
    pop, bname, name = task
    P = _D[pop]
    s, base = P["preds"][name], P["preds"]["LR_" + bname]
    d = eval_lib.paired_delta(s, base, P["y"], P["c"])
    d["combo_auroc"], d["combo_ci95"] = eval_lib.auroc(s, P["y"]), eval_lib.cluster_bootstrap_ci(s, P["y"], P["c"])
    d["X"] = P["meta"][name]["method"].split("+", 1)[1]
    return task, d


def lopo_job(task):
    pop, name, feats = task
    import models
    P = _D[pop]
    y = P["y"]
    prog = sorted(set(P["c"]))
    X = _D[pop]["design"]
    oof = [0.0] * len(y)
    for p in prog:
        tr = [i for i, b in enumerate(P["c"]) if b != p]
        te = [i for i, b in enumerate(P["c"]) if b == p]
        m = models.fit_logistic_irls([[X[i][f] for f in feats] for i in tr], [y[i] for i in tr], 1.0)
        for i in te:
            oof[i] = eval_lib.logit_score(m, [X[i][f] for f in feats])
    return task, oof


def stage_inc():
    v = C.verified_state()
    C.setup_modules(bool(v.get("use_fixed_modules", True)) if isinstance(v, dict) else False)
    sel = jload(RAW / C.EXP_FIT / "frozen_config.json")
    inc_names = sel["inc_names"]
    res = {}
    tasks = []
    for pop in EVAL_POPS:
        rows, preds, meta = load_all(pop)
        design = [{"edit": float(r["edit"]), "exception_fraction": r["scores"]["exception_fraction"], "call_count": r["scores"]["call_count"], "coverage_size": r["scores"]["coverage_size"]} for r in rows]
        for k in ("sbg_v5", "sbg_state"):
            for dct, r in zip(design, rows):
                dct[k] = r["scores"][k]
        for n in ("sbg_v3", "sbg_temporal"):
            for dct, r in zip(design, rows):
                dct[n] = r["scores"][n]
        for x in set(sum(inc_names.values(), [])):
            if x in design[0]:
                continue
            nm = None
            for cand in preds:
                if meta[cand].get("method") == x:
                    nm = cand
            if nm:
                for dct, s in zip(design, preds[nm]):
                    dct[x] = s
        _D[pop] = {"rows": rows, "preds": preds, "meta": meta, "y": [r["label"] for r in rows], "c": [r["base_id"] for r in rows], "design": design}
        for bname in ("EX", "EXx"):
            for n in [k for k in inc_names if k.startswith(f"INC|{bname}+")]:
                tasks.append(("inc", (pop, bname, C_safe(n))))
    outs = {}
    with multiprocessing.get_context("fork").Pool(WORKERS) as pool:
        for task, d in pool.imap_unordered(inc_job, [t[1] for t in tasks]):
            outs[task] = d
    for pop in EVAL_POPS:
        P = _D[pop]
        r = {"base_auroc": {}, "deltas": {}, "holm": {}}
        for bname in ("EX", "EXx"):
            sb = P["preds"]["LR_" + bname]
            r["base_auroc"][bname] = {"auroc": eval_lib.auroc(sb, P["y"]), "ci95": eval_lib.cluster_bootstrap_ci(sb, P["y"], P["c"])}
            fam = {}
            for (p, b, n), d in outs.items():
                if p == pop and b == bname:
                    r["deltas"][n] = d
                    fam[n] = d["p_two_sided"]
            r["holm"][bname] = eval_lib.holm(fam)
        res[pop] = r
    # exploratory LOPO
    jobs = []
    for pop in EVAL_POPS:
        P = _D[pop]
        reps = sel["representatives"]
        jobs.append((pop, "EX", ["edit", "exception_fraction", "call_count", "coverage_size"]))
        for x in ("sbg_v5", "sbg_state", reps["traceseq_rename_robust*"], reps["valuespectra*"]):
            jobs.append((pop, f"EX+{x}", ["edit", "exception_fraction", "call_count", "coverage_size", x]))
        jobs.append((pop, "V5alone", ["sbg_v5"]))
    lop = {}
    with multiprocessing.get_context("fork").Pool(WORKERS) as pool:
        for task, oof in pool.imap_unordered(lopo_job, jobs):
            lop[(task[0], task[1])] = oof
    for pop in EVAL_POPS:
        P = _D[pop]
        y, c = P["y"], P["c"]
        L = {"note": "EXPLORATORY: refit (IRLS, same L2 objective) leaving one program out WITHIN the held-out population; pooled out-of-fold scores"}
        base = lop[(pop, "EX")]
        L["EX_auroc"] = eval_lib.auroc(base, y)
        L["EX_ci95"] = eval_lib.cluster_bootstrap_ci(base, y, c)
        for (p, n), oof in lop.items():
            if p == pop and n.startswith("EX+"):
                d = eval_lib.paired_delta(oof, base, y, c)
                d["combo_auroc"] = eval_lib.auroc(oof, y)
                L[n] = d
        L["V5alone_auroc"] = eval_lib.auroc(lop[(pop, "V5alone")], y)
        res[pop]["lopo_exploratory"] = L
    jdump(RAW / EXP_INC / "incremental.json", res)
    for pop in EVAL_POPS:
        d = res[pop]["deltas"].get(C_safe("INC|EX+sbg_v5"))
        print(pop, "EX base", round(res[pop]["base_auroc"]["EX"]["auroc"], 4), "Δ(EX+V5−EX)", d and (round(d["delta"], 4), [round(x, 4) for x in d["ci95"]], d["p_two_sided"]))


def C_safe(n):
    import a4c_methods as M
    return M.safe(n)


# ------------------------------------------------------------------ sensitivities
def ast_hash(path):
    try:
        return hashlib.sha256(ast.dump(ast.parse((C.REPO / path).read_text())).encode()).hexdigest()
    except Exception:  # noqa: BLE001
        return "ERR:" + path


def sens_job(task):
    pop, scen, name = task
    P = _D[pop]
    idx = P["scen"][scen]
    s = [P["preds"][name][i] for i in idx]
    y = [P["y"][i] for i in idx]
    c = [P["c"][i] for i in idx]
    out = {"n": len(idx), "n_programs": len(set(c)), "auroc": eval_lib.auroc(s, y), "ci95": eval_lib.cluster_bootstrap_ci(s, y, c)}
    if name != "sbg_v5":
        v5 = [P["preds"]["sbg_v5"][i] for i in idx]
        out["delta_v5_minus"] = eval_lib.paired_delta(v5, s, y, c)
    return task, out


def stage_sens():
    res = {}
    mut = jload(RAW / "EXP-A3-009" / "mutation_aware.json")
    ch_same = {x["pair_id"] for x in mut if x["label"] == 1 and x["n_any_diff"] == 0}
    eq_diff = {x["pair_id"] for x in mut if x["label"] == 0 and x["n_any_diff"] > 0}
    tasks = []
    for pop in EVAL_POPS:
        rows, preds, meta = load_all(pop)
        reps = [n for n, m in meta.items() if m.get("role") in ("representative", "reference", "competitor_representative")] + ["edit"]
        reps = sorted(set(n for n in reps if n in preds))
        y = [r["label"] for r in rows]
        scen = {"S0_all": list(range(len(rows)))}
        grp = collections.defaultdict(set)
        if pop == "v9c_val":
            bad1 = {r["group"] for r in rows if r["pair_id"] in eq_diff}
            bad2 = {r["group"] for r in rows if r["pair_id"] in ch_same}
            scen["S1_drop_sets_EQ_output_differing"] = [i for i, r in enumerate(rows) if r["group"] not in bad1]
            scen["S2_drop_sets_CH_no_observable_diff"] = [i for i, r in enumerate(rows) if r["group"] not in bad2]
            scen["S3_clean_labels_(S1+S2)"] = [i for i, r in enumerate(rows) if r["group"] not in (bad1 | bad2)]
        ah = [ast_hash(r["variant_path"]) for r in rows]
        eq_ast = collections.defaultdict(set)
        for r, a in zip(rows, ah):
            if r["label"] == 0:
                eq_ast[r["base_id"]].add(a)
        conf = {r["group"] for r, a in zip(rows, ah) if r["label"] == 1 and a in eq_ast[r["base_id"]]}
        scen["B_drop_label_conflicting_sets(CH AST == some EQ AST)"] = [i for i, r in enumerate(rows) if r["group"] not in conf]
        seen, c_idx = set(), []
        for i, (r, a) in enumerate(zip(rows, ah)):
            k = (r["base_id"], r["label"], a)
            if k not in seen:
                seen.add(k)
                c_idx.append(i)
        scen["C_dedup_(program,label,AST)"] = c_idx
        seen, d_idx = set(), []
        for i in scen["B_drop_label_conflicting_sets(CH AST == some EQ AST)"]:
            k = (rows[i]["base_id"], rows[i]["label"], ah[i])
            if k not in seen:
                seen.add(k)
                d_idx.append(i)
        scen["D_B_then_dedup"] = d_idx
        _D[pop] = {"rows": rows, "preds": preds, "meta": meta, "y": y, "c": [r["base_id"] for r in rows], "scen": scen}
        for s in scen:
            for n in reps:
                tasks.append((pop, s, n))
    with multiprocessing.get_context("fork").Pool(WORKERS) as pool:
        outs = dict(pool.imap_unordered(sens_job, tasks))
    for (pop, s, n), v in outs.items():
        res.setdefault(pop, {}).setdefault(s, {})[n] = v
    jdump(RAW / EXP_INC / "sensitivity.json", res)
    with open(TAB / "EXP-A4C-005_sensitivity.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pop", "scenario", "n", "method", "auroc", "ci_lo", "ci_hi", "delta_v5_minus", "d_lo", "d_hi", "p"])
        for pop, ss in res.items():
            for s, ms in ss.items():
                for n, v in sorted(ms.items(), key=lambda kv: -kv[1]["auroc"]):
                    d = v.get("delta_v5_minus")
                    w.writerow([pop, s, v["n"], n, round(v["auroc"], 4), round(v["ci95"][0], 4), round(v["ci95"][1], 4), d and round(d["delta"], 4), d and round(d["ci95"][0], 4), d and round(d["ci95"][1], 4), d and d["p_two_sided"]])
    print("sensitivity done:", {p: list(s) for p, s in res.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--pop")
    a = ap.parse_args()
    if a.stage == "main":
        stage_main(a.pop)
    elif a.stage == "inc":
        stage_inc()
    elif a.stage == "sens":
        stage_sens()

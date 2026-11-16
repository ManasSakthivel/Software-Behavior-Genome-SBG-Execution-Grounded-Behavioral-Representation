"""Benchmark library: assembling score tables, family registry, model fitting / scoring (EXP-A4-004/005/006)."""
from __future__ import annotations

import json
import math
import pathlib

import b02_static
import b04_valuespectra
import b05_pathspectra
import b05_traceseq
import models
from bl_common import PKG, eval_lib

RAW = PKG / "results" / "raw"
PROC = PKG / "results" / "processed"
TAB = PKG / "results" / "tables"
X3 = ["exception_fraction", "call_count", "coverage_size"]
XE = ["n_functions", "n_events", "trace_len_mean"]
FEATS = {"E": ["edit"], "X": X3, "EX": ["edit"] + X3, "EXx": ["edit"] + X3 + XE, "Xx": X3 + XE}
INC_X = ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal", "valuespectra*", "traceseq_rename_robust*", "pathspectra*", "output_indep|frac40"]
HELD = ("v9c_val", "v10_test")
SBG_REFS = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state"]


# ------------------------------------------------------------------ families
def families():
    ts = b05_traceseq.config_names()
    F = {
        "edit_fwd": ["edit"],
        "static_token": ["static_token"], "static_ast": ["static_ast"],
        "static_own*": [f"static|{c}" for c in ("tok_lev_raw", "tok_lev_alpha", "astseq_lev_types", "astseq_lev_alpha", "tfidf2", "tfidf3", "bytecode_lev")],
        "tce_analogue*": ["static|tce_ast", "static|tce_bytecode"],
        "execstat_single*": ["exception_fraction", "call_count", "coverage_size", "n_functions", "n_events", "trace_len_mean"],
        "LR_EX": ["LR_EX"], "LR_X": ["LR_X"], "LR_EXx*": ["LR_EXx", "LR_Xx"],
        "forest_nonlinear*": [f"forest|{k}_d{d}|{fs}" for fs in ("EXx", "Xx") for k, ds in (("DT", (2, 3, 4)), ("RF", (3, 4, 6))) for d in ds],
        "sbg_state": ["sbg_state"], "sbg_v3": ["sbg_v3"], "sbg_temporal": ["sbg_temporal"],
        "valuespectra*": b04_valuespectra.config_names(),
        "traceseq_rename_robust*": [c for c in ts if c.split("|")[2] in ("entry", "full")],
        "traceseq_naive*": [c for c in ts if c.split("|")[2] == "raw"],
        "birthmark_k*": [c for c in ts if c.split("|")[3].startswith("kgram")],
        "pathspectra*": b05_pathspectra.config_names(),
        "output_indep_frac40": ["output_indep|frac40"],
    }
    return F


HOLM_FAMILIES = list(families().keys())          # m = 19
DIAG = {"edit_rev": ["edit_rev"], "oracle_ceiling": ["oracle|frac11", "oracle|any11", "oracle|frac11_excmsg", "changeguard_cmp|frac11", "changeguard_cmp|any11"],
        "output_indep_variants": ["output_indep|any40", "output_indep|frac40_excmsg", "output_indep|frac11", "output_indep|any11"] + [f"output_indep|{m}_k{k}" for k in (1, 2, 4, 8, 16, 32) for m in ("any", "frac")],
        "sbg_v6": ["sbg_v6", "sbg_state_v6"]}
FAMILY_CLASS = {"edit_fwd": "A", "static_token": "A", "static_ast": "A", "static_own*": "A", "tce_analogue*": "A", "execstat_single*": "A", "LR_EX": "A", "LR_X": "A",
                "LR_EXx*": "A", "forest_nonlinear*": "A", "sbg_state": "ref", "sbg_v3": "ref", "sbg_temporal": "ref", "valuespectra*": "B", "traceseq_rename_robust*": "B",
                "traceseq_naive*": "B", "birthmark_k*": "A/B", "pathspectra*": "B", "output_indep_frac40": "B (privileged)"}


# ------------------------------------------------------------------ data assembly
def assemble(pop):
    rows = eval_lib.load_population(pop)
    fj = json.loads((RAW / "EXP-A4-002" / f"features_{pop}.json").read_text())
    ip = RAW / "EXP-A4-003" / f"indep_{pop}.json"
    ind = json.loads(ip.read_text()) if ip.exists() else {}
    miss = 0
    for r in rows:
        S = dict(r["scores"])
        S["edit"] = float(r["edit"])
        S["edit_rev"] = -S["edit"]
        f = fj.get(r["pair_id"], {})
        if not f.get("_trace_ok"):
            miss += 1
        S.update(f)
        i = ind.get(r["pair_id"])
        r["_indep_covered"] = bool(i)
        for k in ("output_indep|frac40", "output_indep|any40", "output_indep|frac40_excmsg", "output_indep|frac11", "output_indep|any11"):
            S[k] = i[k] if i else 0.0
        if i:
            S.update({k: v for k, v in i.items() if k not in S})
        else:
            for k in [k for k in DIAG["output_indep_variants"] if k not in S]:
                S[k] = 0.0
        r["S"] = S
    return rows, miss


def col(rows, key):
    return [r["S"].get(key, 0.0) for r in rows]


def labels(rows):
    return [r["label"] for r in rows]


def clusters(rows):
    return [r["base_id"] for r in rows]


# ------------------------------------------------------------------ models
def design(rows, feats):
    return [[r["S"].get(f, 0.0) for f in feats] for r in rows]


def fit_lr(rows, feats):
    return eval_lib.fit_logistic(design(rows, feats), labels(rows))


def fit_tree_model(rows, spec):
    """spec = forest|DT_d3|EXx"""
    _, kd, fs = spec.split("|")
    k, d = kd.split("_d")
    X, y = design(rows, FEATS[fs]), labels(rows)
    if k == "DT":
        return {"kind": "DT", "model": models.Tree(int(d), 10).fit(X, y), "feats": FEATS[fs]}
    return {"kind": "RF", "model": models.Forest(50, int(d), 42).fit(X, y), "feats": FEATS[fs]}


def score_lr(m, rows, feats):
    return [eval_lib.logit_score(m, x) for x in design(rows, feats)]


def score_tree(tm, rows):
    return [tm["model"].predict(x) for x in design(rows, tm["feats"])]


def train_scores_tree(tm, rows):
    if tm["kind"] == "RF":
        return tm["model"].oob_scores(design(rows, tm["feats"]))
    return score_tree(tm, rows)


def jdump(path, obj):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))

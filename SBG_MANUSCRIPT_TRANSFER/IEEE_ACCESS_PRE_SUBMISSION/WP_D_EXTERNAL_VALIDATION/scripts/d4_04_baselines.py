"""d4_04_baselines.py -- Task 4.
(a) AUROC (+ cluster-bootstrap CI) of every scored baseline in the pair files (static_token, static_ast, exception_fraction,
    call_count, sbg_v3, sbg_state, sbg_temporal, coverage_size, n_functions, combined_shortcut, exception_*),
(b) paired DeltaAUROC (baseline - sbg_v5) with shared-resample cluster bootstrap; Holm over the 5 pre-registered
    comparators (static_ast, static_token, exception_fraction, call_count, sbg_v3)  [Holm family = PRE-REGISTERED on the
    prereg sets; the same arithmetic on other sets is POST-HOC],
(c) label-source / edit-size shortcut features computed from the vendored files in SBG/external/*:
      edit_lines   : lines in non-equal difflib opcodes (max of the two sides per block)
      edit_tokens  : same on python token streams (NAME/OP/NUMBER/STRING; comments, NL ignored)
      rel_edit_tok : edit_tokens / len(base tokens)
      abs_dtok     : | n_tokens(variant) - n_tokens(base) |
      abs_dnodes   : | n_ast_nodes(variant) - n_ast_nodes(base) |
      comment_loss : comment tokens in base minus in variant
      variant_is_unparse_canonical : 1 iff variant text == ast.unparse(ast.parse(variant text))
                                     (SP transformers emit ast.unparse output; developer-authored buggy code is not)
      base_ntok    : size of the fixed unit (shared by pos/neg of a cluster; between-cluster only)
    For each feature the AUROC is reported for "higher feature -> positive"; the reverse direction is 1-AUROC.
    Because label == provenance (developer fix vs repo-transformer output) these checks quantify the
    label/source confound; they do NOT measure behaviour.
Outputs: raw/WPD-D4_stats/04_baselines.json, 04_baselines_table.csv, 04_edit_features.csv, 04_shortcut_by_negative_type.json
"""
import ast
import csv
import difflib
import io
import json
import sys
import tokenize
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

B = 5000
C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
S = get_sets(C, audit)

DYN = ["sbg_v5", "sbg_v3", "sbg_state", "sbg_temporal", "exception_fraction", "exception_component_v3",
       "exception_type_jaccard", "call_count", "coverage_size", "n_functions", "combined_shortcut"]
STAT = ["static_token", "static_ast"]
PREREG_COMPARATORS = ["static_ast", "static_token", "exception_fraction", "call_count", "sbg_v3"]


# ---------------- edit features ---------------------------------------------------
def toks(src):
    out, ncom = [], 0
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type == tokenize.COMMENT:
                ncom += 1
            elif t.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER, tokenize.STRING):
                out.append(t.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        out = src.split()
    return out, ncom


def n_nodes(src):
    try:
        return sum(1 for _ in ast.walk(ast.parse(src)))
    except SyntaxError:
        return None


def blocks(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")


def is_canon(src):
    try:
        return int(ast.unparse(ast.parse(src)).strip() == src.strip())
    except SyntaxError:
        return None


FEATS = ["edit_lines", "edit_tokens", "rel_edit_tok", "abs_dtok", "abs_dnodes", "comment_loss",
         "variant_is_unparse_canonical", "base_ntok"]
cache = {}


def features(r):
    key = (r["base_path"], r["variant_path"])
    if key in cache:
        return cache[key]
    a = (SBG / r["base_path"]).read_text(errors="replace")
    b = (SBG / r["variant_path"]).read_text(errors="replace")
    la = [l.rstrip() for l in a.splitlines() if l.strip()]
    lb = [l.rstrip() for l in b.splitlines() if l.strip()]
    ta, ca = toks(a)
    tb, cb = toks(b)
    na, nb = n_nodes(a), n_nodes(b)
    et = blocks(ta, tb)
    f = {"edit_lines": blocks(la, lb), "edit_tokens": et,
         "rel_edit_tok": et / max(1, len(ta)), "abs_dtok": abs(len(tb) - len(ta)),
         "abs_dnodes": abs(nb - na) if na is not None and nb is not None else None,
         "comment_loss": ca - cb, "variant_is_unparse_canonical": is_canon(b), "base_ntok": len(ta)}
    cache[key] = f
    return f


for corpus, recs in C.items():
    for r in recs:
        r["feat"] = features(r)

with open(OUT / "04_edit_features.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["corpus", "pair_id", "label", "kind", "ev7"] + FEATS)
    for corpus, recs in C.items():
        for r in recs:
            w.writerow([corpus, r["pair_id"], r["label"], r["kind"], int(r["ev7"])] + [r["feat"][k] for k in FEATS])


# ---------------- predictors per set -----------------------------------------------
def pred_vectors(s):
    recs = s["recs"]
    pv = {}
    for p in DYN:
        src = s["src"]
        avail = any(r[src] and p in r[src] for r in recs)
        if avail:
            pv[p] = vecs(recs, p, src, s["impute"])
    for p in STAT:
        v = []
        for r in recs:
            st = r["static"]
            v.append(float(st[p]) if st and st.get(p) is not None else 0.0)
        pv[p] = v
    for k in FEATS:
        pv["F:" + k] = [float(r["feat"][k]) if r["feat"][k] is not None else 0.0 for r in recs]
    return pv


def holm(pvals):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj, run = {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        adj[k] = round(run, 4)
    return adj


out = {"script": "scripts/d4_04_baselines.py", "B": B, "input_manifest": input_manifest(), "sets": {},
       "note": "static baselines are taken from the pair files for every row (BugsInPy keeps them for unevaluated rows; "
               "QuixBugs-declared unevaluated rows have none -> 0). Dynamic predictors of unevaluated rows are imputed 0 "
               "(prereg ALL set). Features F:* are computed from the vendored files and exist for every pair."}
csvrows = []
for sid, s in S.items():
    recs = s["recs"]
    lab = [r["label"] for r in recs]
    pv = pred_vectors(s)
    res = {"status": s["status"], "n": len(recs), "levels": {}}
    levels = {"bug": bug_cluster(recs)}
    if s["corpus"] == "bugsinpy":
        levels["project"] = project_cluster(recs)
    for lv, cl in levels.items():
        g = groups_of(cl)
        boot = cluster_boot(pv, lab, g, B=B, seed=zlib.crc32(sid.encode()) + 11)
        d = {"n_clusters": len(g), "predictors": {}, "paired_vs_sbg_v5": {}}
        base_theta = auroc(pv["sbg_v5"], lab)
        for p, sc in pv.items():
            th = auroc(sc, lab)
            ci = ci_from_boot(th, boot[p])
            d["predictors"][p] = {"auroc": round(th, 4), "ci95_percentile": ci["percentile"]}
            if p != "sbg_v5":
                dl = paired_delta_boot(boot[p], boot["sbg_v5"])
                d["paired_vs_sbg_v5"][p] = delta_summary(th - base_theta, dl)
            csvrows.append([sid, s["status"], lv, p, round(th, 4), ci["percentile"][0], ci["percentile"][1]])
        hp = {p: d["paired_vs_sbg_v5"][p]["p_two_sided_boot"] for p in PREREG_COMPARATORS if p in d["paired_vs_sbg_v5"]}
        for p, a in holm(hp).items():
            d["paired_vs_sbg_v5"][p]["holm_adj_p_over_prereg_family"] = a
        d["holm_family"] = list(hp)
        res["levels"][lv] = d
    out["sets"][sid] = res
    b = res["levels"]["bug"]["predictors"]
    print(sid, "sbg_v5=%.3f static_ast=%.3f static_token=%.3f exc=%.3f call=%.3f v3=%.3f | edit_tok=%.3f dtok=%.3f unparse=%.3f base_ntok=%.3f" % (
        b["sbg_v5"]["auroc"], b["static_ast"]["auroc"], b["static_token"]["auroc"], b["exception_fraction"]["auroc"],
        b["call_count"]["auroc"], b["sbg_v3"]["auroc"], b["F:edit_tokens"]["auroc"], b["F:abs_dtok"]["auroc"],
        b["F:variant_is_unparse_canonical"]["auroc"], b["F:base_ntok"]["auroc"]), flush=True)
write_json("04_baselines.json", out)
with open(OUT / "04_baselines_table.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["set", "status", "cluster_level", "predictor", "auroc", "ci_lo", "ci_hi"])
    w.writerows(csvrows)

# ---------------- shortcut AUROC by negative type (positives vs each SP type) ---------------
by = {}
for sid in ("BP-v7-EVAL", "BP-v7-ALL", "QC-v7-ALL", "QD-v7-EVAL"):
    s = S[sid]
    recs = s["recs"]
    pv = pred_vectors(s)
    kinds = sorted({r["kind"] for r in recs if r["kind"] != "real"})
    by[sid] = {}
    for k in kinds:
        idx = [i for i, r in enumerate(recs) if r["kind"] in ("real", k)]
        lab = [recs[i]["label"] for i in idx]
        by[sid][k] = {"n_pos": sum(lab), "n_neg": len(lab) - sum(lab)}
        for p in ["sbg_v5", "static_ast", "static_token", "F:edit_tokens", "F:edit_lines", "F:rel_edit_tok",
                  "F:abs_dtok", "F:variant_is_unparse_canonical", "F:comment_loss"]:
            by[sid][k][p] = round(auroc([pv[p][i] for i in idx], lab), 4)
means = {}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    means[corpus] = {}
    for kd in sorted({r["kind"] for r in C[corpus]}):
        rr = [r for r in C[corpus] if r["kind"] == kd]
        means[corpus][kd] = {"n": len(rr), **{k: round(sum((r["feat"][k] or 0) for r in rr) / len(rr), 3)
                                              for k in FEATS}}
write_json("04_shortcut_by_negative_type.json", {"auroc_pos_vs_each_negative_type": by,
                                                 "mean_features_by_kind_all_rows": means,
                                                 "script": "scripts/d4_04_baselines.py"})
print(json.dumps(by, indent=0)[:3500])
print(json.dumps(means, indent=0)[:3000])

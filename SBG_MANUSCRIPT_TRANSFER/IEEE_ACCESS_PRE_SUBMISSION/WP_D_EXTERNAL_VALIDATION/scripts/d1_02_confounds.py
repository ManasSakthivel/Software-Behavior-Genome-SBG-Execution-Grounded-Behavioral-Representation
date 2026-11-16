#!/usr/bin/env python3
"""WP-D / D1 step 2 -- structural confound analysis of the external pair sets.

EXECUTED here: arithmetic/statistics on committed per-pair artifacts + text/AST analysis of the vendored program files.
NOT executed here: no SBG tracing, no scoring (that is D2's remit).  All inputs read-only from SBG/.

Inputs : SBG/artifacts/final/pairs_{bugsinpy,quixbugs_canonical,quixbugs_declared}_output_free_v7.jsonl
         SBG/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json   (v8 corrected-harness per-pair scores)
Outputs: raw/WPD-D1_compat/data/confound_pairs.csv, confound_summary.json

For every pair the following STATIC, label-blind features are computed from the two program files:
  raw_line_edit      number of inserted+deleted lines (difflib) between the raw base and variant file text
  norm_line_edit     same after parsing both files, stripping docstrings/comments (ast.unparse) -> formatting-neutral
  var_text_is_unparse  variant file text == ast.unparse(ast.parse(text)) (i.e. produced/normalised by an AST round trip)
  comment_loss       (#comment-lines in base) - (#comment-lines in variant)
and committed static_token / static_ast distances.  AUROC(label ~ feature) quantifies how much of the label can be
predicted WITHOUT executing anything -- the 'edit-type shortcut' check.  No fitted model; a feature is reported in its
natural polarity (larger = more changed); 1-AUROC is the reversed-polarity value, never selected on the data.
"""
import ast
import collections
import csv
import difflib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
WP = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from d1_stats import auroc, summarize  # noqa: E402

PKG = WP.parent
REPO = PKG.parent / "SBG"
OUT = WP / "raw" / "WPD-D1_compat" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def strip_docstrings(tree):
    class T(ast.NodeTransformer):
        def _strip(self, node):
            self.generic_visit(node)
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
            return node
        visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _strip

        def visit_Module(self, node):
            self.generic_visit(node)
            # module level free-standing string expressions (QuixBugs puts a doc string AFTER the def)
            node.body = [n for n in node.body
                         if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                                 and isinstance(n.value.value, str))] or [ast.Pass()]
            return node
    return T().visit(tree)


def norm_text(src):
    try:
        return ast.unparse(strip_docstrings(ast.parse(src)))
    except SyntaxError:
        return None


def line_edit(a_lines, b_lines):
    sm = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    n = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            n += (i2 - i1) + (j2 - j1)
    return n


def comment_lines(src):
    return sum(1 for l in src.splitlines() if l.strip().startswith("#"))


def feats(base_rel, var_rel):
    bs = (REPO / base_rel).read_text()
    vs = (REPO / var_rel).read_text()
    nb, nv = norm_text(bs), norm_text(vs)
    out = {"raw_line_edit": line_edit(bs.splitlines(), vs.splitlines())}
    out["norm_line_edit"] = line_edit(nb.splitlines(), nv.splitlines()) if nb is not None and nv is not None else None
    try:
        out["var_text_is_unparse"] = int(vs.strip() == ast.unparse(ast.parse(vs)).strip())
    except SyntaxError:
        out["var_text_is_unparse"] = None
    out["comment_loss"] = comment_lines(bs) - comment_lines(vs)
    out["base_lines"] = len(bs.splitlines())
    out["variant_lines"] = len(vs.splitlines())
    return out


# --------------------------------------------------------------------------- unify pair rows
rows = []
v8 = json.loads((REPO / "artifacts/paper_evidence/raw/external_rescore_v8_pairs.json").read_text())
v8_by = {c: {r["pair_id"]: r for r in lst} for c, lst in v8.items()}

for r in jl(REPO / "artifacts/final/pairs_bugsinpy_output_free_v7.jsonl"):
    x = v8_by["bugsinpy"].get(r["pair_id"])
    sc = r["scores"] or {}
    st = r["static_scores"]
    rows.append({
        "corpus": "bugsinpy", "regime": "canonical", "pair_id": r["pair_id"], "cluster": r["bug_id"],
        "lineage": f"{r['project']}|{r['file']}|{r['unit']}", "unit": f"{r['bug_id']}|{r['unit']}",
        "label": r["label"], "transformation": r["transformation"],
        "evaluated_v7": r["evaluated"], "failure_kind_v7": r["failure_kind"],
        "evaluated_v8": bool(x and x["evaluated"]),
        "sbg_v5_v7": sc.get("sbg_v5"), "sbg_v5_v8": x["sbg_v5"] if x and x["evaluated"] else None,
        "sbg_v3_v7": sc.get("sbg_v3"), "exception_fraction_v7": sc.get("exception_fraction"),
        "static_token": st["static_token"], "static_ast": st["static_ast"],
        "base_entry_fn_v8": x.get("base_entry_fn") if x else None,
        "variant_entry_fn_v8": x.get("variant_entry_fn") if x else None,
        "base_path": r["base_path"], "variant_path": r["variant_path"]})

for r in jl(REPO / "artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl"):
    x = v8_by["quixbugs_canonical"].get(r["pair_id"])
    sc = r["scores"] if r["evaluated"] else {}
    rows.append({
        "corpus": "quixbugs_canonical", "regime": "canonical", "pair_id": r["pair_id"], "cluster": r["base_id"],
        "lineage": r["base_id"], "unit": r["base_id"], "label": r["label"],
        "transformation": "real_bug" if r["pair_kind"] == "real_bug" else r["pair_kind"].replace("sp_negative:", ""),
        "evaluated_v7": r["evaluated"], "failure_kind_v7": r["failure_kind"],
        "evaluated_v8": bool(x and x["evaluated"]),
        "sbg_v5_v7": sc.get("sbg_v5"), "sbg_v5_v8": x["sbg_v5"] if x and x["evaluated"] else None,
        "sbg_v3_v7": sc.get("sbg_v3"), "exception_fraction_v7": sc.get("exception_fraction"),
        "static_token": r["scores"].get("static_token"), "static_ast": r["scores"].get("static_ast"),
        "base_entry_fn_v8": x.get("base_entry_fn") if x else None,
        "variant_entry_fn_v8": x.get("variant_entry_fn") if x else None,
        "v8_failure_kind": x["failure_kind"] if x else None,
        "base_path": r["base_path"], "variant_path": r["variant_path"]})

for r in jl(REPO / "artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl"):
    sc = r["scores"] if r["evaluated"] else {}
    rows.append({
        "corpus": "quixbugs_declared", "regime": "declared", "pair_id": r["pair_id"], "cluster": r["base_id"],
        "lineage": r["base_id"], "unit": r["base_id"], "label": r["label"],
        "transformation": "real_bug" if r["pair_kind"] == "real_bug" else r["pair_kind"].replace("sp_negative:", ""),
        "evaluated_v7": r["evaluated"], "failure_kind_v7": r["failure_kind"], "evaluated_v8": None,
        "sbg_v5_v7": sc.get("sbg_v5"), "sbg_v5_v8": None,
        "sbg_v3_v7": sc.get("sbg_v3"), "exception_fraction_v7": sc.get("exception_fraction"),
        "static_token": r["scores"].get("static_token"), "static_ast": r["scores"].get("static_ast"),
        "declared_ref_differs": (r.get("output_reference") or {}).get("differs"),
        "declared_ref_mismatches": (r.get("output_reference") or {}).get("n_mismatches"),
        "declared_ref_n_inputs": (r.get("output_reference") or {}).get("n_inputs"),
        "base_path": r["base_path"], "variant_path": r["variant_path"]})

for r in rows:
    r.update(feats(r["base_path"], r["variant_path"]))

cols = ["corpus", "regime", "pair_id", "cluster", "lineage", "unit", "label", "transformation", "evaluated_v7",
        "failure_kind_v7", "evaluated_v8", "v8_failure_kind", "sbg_v5_v7", "sbg_v5_v8", "sbg_v3_v7",
        "exception_fraction_v7", "static_token", "static_ast", "raw_line_edit", "norm_line_edit",
        "var_text_is_unparse", "comment_loss", "base_lines", "variant_lines", "base_entry_fn_v8",
        "variant_entry_fn_v8", "declared_ref_differs", "declared_ref_mismatches", "declared_ref_n_inputs",
        "base_path", "variant_path"]
with open(OUT / "confound_pairs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

# --------------------------------------------------------------------------- analysis
FEATURES = ["sbg_v5_v8", "sbg_v5_v7", "static_token", "static_ast", "norm_line_edit", "raw_line_edit",
            "comment_loss", "var_text_is_unparse"]


def subset(corpus, name):
    R = [r for r in rows if r["corpus"] == corpus]
    if name == "all_pairs_in_frozen_manifest":
        return R
    if name == "v7_evaluated":
        return [r for r in R if r["evaluated_v7"]]
    if name == "v8_evaluated":
        return [r for r in R if r["evaluated_v8"]]
    if name == "v8_evaluated_excl_SP2":
        return [r for r in R if r["evaluated_v8"] and r["transformation"] != "SP-2"]
    if name == "v7_evaluated_excl_SP2":
        return [r for r in R if r["evaluated_v7"] and r["transformation"] != "SP-2"]
    raise KeyError(name)


summary = {"definitions": {
    "all_pairs_in_frozen_manifest": "every pair in the frozen manifest incl. unevaluated ones (only label-blind static features are defined for unevaluated pairs; SBG features undefined => skipped per feature)",
    "v7_evaluated": "pairs evaluated by the committed output_free_v7 run (the 'published headline' pair sets: BugsInPy 147, QuixBugs-canonical 152)",
    "v8_evaluated": "pairs evaluated by the post-hoc corrected-harness rescore (EXTERNAL_RESCORE_V8; BugsInPy 147, QuixBugs 151)",
    "v8_evaluated_excl_SP2": "v8_evaluated minus every SP-2 negative (post-hoc exclusion; basis of the 0.497 / 0.444 numbers)"},
    "tables": {}}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    summary["tables"][corpus] = {}
    for sname in ("all_pairs_in_frozen_manifest", "v7_evaluated", "v8_evaluated", "v8_evaluated_excl_SP2",
                  "v7_evaluated_excl_SP2"):
        S = subset(corpus, sname)
        block = {"n_pairs": len(S), "n_pos": sum(r["label"] for r in S), "n_clusters": len({r["cluster"] for r in S})}
        for feat in FEATURES:
            if feat == "sbg_v5_v8" and not sname.startswith("v8"):
                continue
            if feat == "sbg_v5_v7" and sname.startswith("v8"):
                continue
            block[feat] = summarize(S, feat, B=2000)
        summary["tables"][corpus][sname] = block
# declared regime (QuixBugs): evaluated subset only
Sd = [r for r in rows if r["corpus"] == "quixbugs_declared"]
Sd_ev = [r for r in Sd if r["evaluated_v7"]]
summary["tables"]["quixbugs_declared"] = {
    "all_pairs_in_frozen_manifest": {"n_pairs": len(Sd), "n_pos": sum(r["label"] for r in Sd)},
    "v7_evaluated": {"n_pairs": len(Sd_ev), "n_pos": sum(r["label"] for r in Sd_ev),
                     "n_clusters": len({r["cluster"] for r in Sd_ev}),
                     **{f: summarize(Sd_ev, f) for f in ("sbg_v5_v7", "static_token", "static_ast",
                                                          "norm_line_edit", "raw_line_edit", "comment_loss")}},
    "v7_evaluated_excl_SP2": {**{f: summarize([r for r in Sd_ev if r["transformation"] != "SP-2"], f)
                                 for f in ("sbg_v5_v7", "static_token", "static_ast", "norm_line_edit")}},
}

# per-negative-type AUROC of SBG v8 vs positives ('which negative family drives <0.5?')
per_neg = {}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    R = [r for r in rows if r["corpus"] == corpus and r["evaluated_v8"]]
    pos = [r for r in R if r["label"] == 1]
    per_neg[corpus] = {}
    for t in sorted({r["transformation"] for r in R if r["label"] == 0}):
        neg = [r for r in R if r["transformation"] == t]
        S = pos + neg
        per_neg[corpus][t] = {
            "n_neg": len(neg),
            "auroc_sbg_v5_v8_pos_vs_this_neg_type": round(auroc([r["sbg_v5_v8"] for r in S], [r["label"] for r in S]), 4),
            "mean_sbg_v5_v8_neg": round(sum(r["sbg_v5_v8"] for r in neg) / len(neg), 4),
            "n_neg_exactly_zero": sum(1 for r in neg if r["sbg_v5_v8"] == 0),
            "mean_static_token_neg": round(sum(r["static_token"] for r in neg) / len(neg), 4),
            "mean_norm_line_edit_neg": round(sum(r["norm_line_edit"] for r in neg) / len(neg), 3)}
    per_neg[corpus]["_positives"] = {
        "n_pos": len(pos), "mean_sbg_v5_v8_pos": round(sum(r["sbg_v5_v8"] for r in pos) / len(pos), 4),
        "n_pos_exactly_zero_v8": sum(1 for r in pos if r["sbg_v5_v8"] == 0),
        "n_pos_exactly_zero_v7": sum(1 for r in pos if r["sbg_v5_v7"] == 0),
        "mean_static_token_pos": round(sum(r["static_token"] for r in pos) / len(pos), 4),
        "mean_norm_line_edit_pos": round(sum(r["norm_line_edit"] for r in pos) / len(pos), 3),
        "median_norm_line_edit_pos": sorted(r["norm_line_edit"] for r in pos)[len(pos) // 2]}
summary["per_negative_type"] = per_neg

# SP-2 entry-rename artefact
sp2 = {}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    R = [r for r in rows if r["corpus"] == corpus and r["evaluated_v8"]]
    for lab, name in ((0, "negatives"), (1, "positives")):
        sub = [r for r in R if r["label"] == lab]
        sp2[f"{corpus}/{name}"] = {
            "n": len(sub),
            "entry_fn_name_differs_base_vs_variant": sum(1 for r in sub if r["base_entry_fn_v8"] != r["variant_entry_fn_v8"])}
    s2 = [r for r in R if r["transformation"] == "SP-2"]
    sp2[f"{corpus}/SP-2"] = {"n": len(s2),
                             "entry_renamed": sum(1 for r in s2 if r["base_entry_fn_v8"] != r["variant_entry_fn_v8"]),
                             "nonzero_sbg_v5_v8": sum(1 for r in s2 if r["sbg_v5_v8"] > 0)}
    by_t = collections.Counter(r["transformation"] for r in R if r["label"] == 0
                               and r["base_entry_fn_v8"] != r["variant_entry_fn_v8"])
    sp2[f"{corpus}/entry_renamed_by_negative_type"] = dict(by_t)
summary["entry_rename"] = sp2

# label balance within cluster
bal = {}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    R = [r for r in rows if r["corpus"] == corpus and r["evaluated_v8"]]
    cl = collections.defaultdict(lambda: [0, 0])
    for r in R:
        cl[r["cluster"]][r["label"]] += 1
    pat = collections.Counter(tuple(v) for v in cl.values())
    bal[corpus] = {"n_clusters": len(cl), "(n_neg,n_pos)_patterns": {str(k): v for k, v in sorted(pat.items())},
                   "clusters_with_no_positive": sum(1 for v in cl.values() if v[1] == 0),
                   "clusters_with_no_negative": sum(1 for v in cl.values() if v[0] == 0)}
summary["cluster_label_balance_v8_evaluated"] = bal

# formatting fingerprint
fp = {}
for corpus in ("bugsinpy", "quixbugs_canonical", "quixbugs_declared"):
    R = [r for r in rows if r["corpus"] == corpus]
    npos = max(1, sum(1 for r in R if r["label"] == 1))
    nneg = max(1, sum(1 for r in R if r["label"] == 0))
    fp[corpus] = {
        "positives": {"n": sum(1 for r in R if r["label"] == 1),
                      "variant_text_is_ast_unparse": sum(1 for r in R if r["label"] == 1 and r["var_text_is_unparse"] == 1)},
        "negatives": {"n": sum(1 for r in R if r["label"] == 0),
                      "variant_text_is_ast_unparse": sum(1 for r in R if r["label"] == 0 and r["var_text_is_unparse"] == 1)},
        "mean_comment_loss_pos": round(sum(r["comment_loss"] for r in R if r["label"] == 1) / npos, 3),
        "mean_comment_loss_neg": round(sum(r["comment_loss"] for r in R if r["label"] == 0) / nneg, 3)}
summary["formatting_fingerprint"] = fp

# QuixBugs positive edit profile
R = [r for r in rows if r["corpus"] == "quixbugs_canonical" and r["label"] == 1]
summary["quixbugs_positive_edit_profile"] = {
    "n_positive": len(R),
    "raw_line_edit_distribution_capped40": dict(sorted(collections.Counter(min(r["raw_line_edit"], 40) for r in R).items())),
    "norm_line_edit_distribution": dict(sorted(collections.Counter(r["norm_line_edit"] for r in R).items())),
    "note": "norm_line_edit strips docstrings & comments; raw_line_edit includes the explanatory docstring that upstream buggy files carry and fixed files do not"}

(OUT / "confound_summary.json").write_text(json.dumps(summary, indent=1) + "\n")


def pr(c, s, f):
    b = summary["tables"][c][s].get(f)
    return None if not b else (b.get("auroc"), b.get("ci95_cluster_bootstrap"), b.get("n"), b.get("n_pos"))


for c in ("bugsinpy", "quixbugs_canonical"):
    print("==", c)
    for s in ("all_pairs_in_frozen_manifest", "v7_evaluated", "v8_evaluated", "v8_evaluated_excl_SP2"):
        print(" ", s)
        for f in FEATURES:
            if f in summary["tables"][c][s]:
                print("    ", f, pr(c, s, f))
print(json.dumps(summary["per_negative_type"], indent=1))
print(json.dumps(summary["entry_rename"], indent=1))
print(json.dumps(summary["cluster_label_balance_v8_evaluated"], indent=1))
print(json.dumps(summary["formatting_fingerprint"], indent=1))
print(json.dumps(summary["quixbugs_positive_edit_profile"], indent=1))
d = summary["tables"]["quixbugs_declared"]
print("declared", {k: (v.get("auroc"), v.get("ci95_cluster_bootstrap"), v.get("n")) for k, v in d["v7_evaluated"].items() if isinstance(v, dict)})

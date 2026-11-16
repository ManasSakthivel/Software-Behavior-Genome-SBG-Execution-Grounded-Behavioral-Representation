#!/usr/bin/env python3
"""WP-D / D1 step 6 -- within-external split leakage, lineage clustering, edit-type audit, header-independent format shortcut.

EXECUTED, execution-free (text / AST / stored scores only).  No SBG code is run, SBG/ is read-only.
It re-uses SBG's STORED v8 per-pair scores (via confound_pairs.csv); nothing is re-traced (that is D2's job).

Outputs  raw/WPD-D1_compat/data/leakage_summary.json, bugsinpy_lineage_clusters.csv, bugsinpy_positive_edit_kind.csv,
         format_shortcut_pairs.csv
"""
import ast
import collections
import csv
import hashlib
import io
import json
import pathlib
import re
import sys
import tokenize

HERE = pathlib.Path(__file__).resolve()
WP = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from d1_stats import auroc, summarize  # noqa: E402

SBG = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
DATA = WP / "raw" / "WPD-D1_compat" / "data"
rows = list(csv.DictReader(open(DATA / "confound_pairs.csv")))
for r in rows:
    r["label"] = int(r["label"])
    for k in ("sbg_v5_v8", "sbg_v5_v7", "static_token", "static_ast", "norm_line_edit"):
        r[k] = float(r[k]) if r.get(k) not in ("", None) else None

SUM = {}


def read(rel):
    return (SBG / rel).read_text(errors="replace")


# ====================================================================== 1. lineage / project clustering of BugsInPy
bp = [r for r in rows if r["corpus"] == "bugsinpy"]
ids = sorted({r["cluster"] for r in bp})
lineages = collections.defaultdict(set)
for r in bp:
    lineages[r["lineage"]].add(r["cluster"])
multi = {k: sorted(v) for k, v in lineages.items() if len(v) > 1}
SUM["bugsinpy_lineage"] = {
    "n_bug_clusters_all_pairs": len(ids),
    "n_distinct_project|file|unit_lineages": len(lineages),
    "n_lineages_spanning_multiple_bugs": len(multi),
    "lineages_spanning_multiple_bugs": multi,
}
# fixed-unit content grouping across bugs (near-duplicate lineage): token shingles of the FIXED unit
SKIP = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING}


def tokseq(src):
    out = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type not in SKIP:
                out.append(t.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return out


def sh(seq, k=5):
    return {tuple(seq[i:i + k]) for i in range(max(0, len(seq) - k + 1))}


def jac(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


pos = [r for r in bp if r["label"] == 1]
fx = {r["pair_id"]: sh(tokseq(read(r["base_path"]))) for r in pos}
pids = list(fx)
parent = {p: p for p in pids}


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


pairs_sim = []
for i, a in enumerate(pids):
    for b in pids[i + 1:]:
        j = jac(fx[a], fx[b])
        pairs_sim.append((j, a, b))
        if j >= 0.5:
            parent[find(a)] = find(b)
comp = collections.defaultdict(list)
for p in pids:
    comp[find(p)].append(p)
content_cluster = {}
for k, (root, members) in enumerate(sorted(comp.items())):
    for m in members:
        content_cluster[m] = f"C{k:02d}"
SUM["bugsinpy_content_clusters_fixed_units_jaccard>=0.5"] = {
    "n_positive_units": len(pids), "n_content_clusters": len(comp),
    "multi_member_clusters": [sorted(m) for m in comp.values() if len(m) > 1],
    "top_pairwise_jaccard_between_distinct_positive_units": [(round(j, 3), a, b) for j, a, b in sorted(pairs_sim, reverse=True)[:8]]}
with open(DATA / "bugsinpy_lineage_clusters.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair_id", "bug_id", "project|file|unit", "content_cluster_jaccard>=0.5"])
    for r in pos:
        w.writerow([r["pair_id"], r["cluster"], r["lineage"], content_cluster[r["pair_id"]]])

# map every pair (positive + its negatives) to the unit's lineage cluster
unit_of = {}
for r in bp:
    unit_of[r["pair_id"]] = r["pair_id"].rsplit("::", 1)[0]
pos_by_unit = {unit_of[r["pair_id"]]: r["pair_id"] for r in pos}
for r in bp:
    r["content_cluster"] = content_cluster.get(pos_by_unit.get(unit_of[r["pair_id"]]), "NA")
    r["project"] = r["lineage"].split("|")[0]


def sub(R, pred):
    return [r for r in R if pred(r)]


v8 = sub(bp, lambda r: r["evaluated_v8"] == "True")
SUM["bugsinpy_cluster_definitions_vs_headline_AUROC"] = {}
for name, R in (("v8_all", v8), ("v8_exclSP2", sub(v8, lambda r: r["transformation"] != "SP-2"))):
    d = {}
    for ck in ("cluster", "content_cluster", "lineage", "project"):
        d[ck] = summarize([r for r in R if r["sbg_v5_v8"] is not None], "sbg_v5_v8", cluster_key=ck)
    SUM["bugsinpy_cluster_definitions_vs_headline_AUROC"][name] = {
        ck: {"n_clusters": v["n_clusters"], "auroc": v["auroc"], "ci95": v["ci95_cluster_bootstrap"]} for ck, v in d.items()}

# ====================================================================== 2. leakage: do external texts recur across pairs with flipped roles?
def norm_text(src):
    try:
        return hashlib.sha256(ast.dump(ast.parse(src)).encode()).hexdigest()
    except SyntaxError:
        return hashlib.sha256(src.encode()).hexdigest()


role = collections.defaultdict(set)  # AST-hash -> {(pair_id, 'base'|'variant', label)}
for r in bp:
    role[norm_text(read(r["base_path"]))].add((unit_of[r["pair_id"]], "base", r["label"]))
    role[norm_text(read(r["variant_path"]))].add((unit_of[r["pair_id"]], "variant", r["label"]))
cross = {h: v for h, v in role.items() if len({u for u, _, _ in v}) > 1}
flip = []
for h, v in cross.items():
    flip.append(sorted(v))
SUM["bugsinpy_same_AST_in_multiple_units"] = {"n_ast_hashes_shared_by_>1_unit": len(cross), "examples": flip[:10]}
# fixed unit of one bug == buggy unit of another bug (a code state used as both 'correct' and 'buggy' reference)
fixed_h = collections.defaultdict(set)
buggy_h = collections.defaultdict(set)
for r in pos:
    fixed_h[norm_text(read(r["base_path"]))].add(r["pair_id"])
    buggy_h[norm_text(read(r["variant_path"]))].add(r["pair_id"])
both = [(sorted(fixed_h[h]), sorted(buggy_h[h])) for h in fixed_h if h in buggy_h]
SUM["bugsinpy_fixed_of_one_bug_is_buggy_of_another"] = {"n": len(both), "examples": both[:10]}

# QuixBugs: within-base label balance (positive and its negatives share the base program)
qb = [r for r in rows if r["corpus"] == "quixbugs_canonical"]
bal = collections.Counter()
by = collections.defaultdict(lambda: [0, 0])
for r in qb:
    by[r["cluster"]][r["label"]] += 1
for c, (n0, n1) in by.items():
    bal[f"neg={n0},pos={n1}"] += 1
SUM["quixbugs_cluster_label_balance_all_pairs"] = dict(bal)
SUM["quixbugs_note"] = ("each QuixBugs base program yields exactly 1 positive and <=3 negatives that share ITS fixed program as base: "
                         "any base-specific property is shared across labels within the cluster (good for pair-level bias) but the "
                         "cluster is not independent from a base-level shortcut; the within-cluster AUROC is reported in confound_summary.json")

# ====================================================================== 3. edit-type audit of the BugsInPy positives
def strip_doc(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b0 = n.body[0]
            if isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str):
                n.body = n.body[1:] or [ast.Pass()]
    return tree


class Anon(ast.NodeTransformer):
    """alpha-rename every Name/arg/attr/def identifier, keep constants"""
    def __init__(self, const):
        self.m = {}
        self.const = const

    def _n(self, s):
        return self.m.setdefault(s, f"v{len(self.m)}")

    def visit_Name(self, n):
        n.id = self._n(n.id)
        return n

    def visit_arg(self, n):
        n.arg = self._n(n.arg)
        return n

    def visit_FunctionDef(self, n):
        n.name = self._n(n.name)
        self.generic_visit(n)
        return n

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, n):
        n.name = self._n(n.name)
        self.generic_visit(n)
        return n

    def visit_Attribute(self, n):
        self.generic_visit(n)
        n.attr = self._n(n.attr)
        return n

    def visit_Constant(self, n):
        if self.const:
            n.value = "C"
        return n


def d(src, doc=True, anon=False, const=False):
    t = ast.parse(src)
    if doc:
        t = strip_doc(t)
    if anon:
        t = Anon(const).visit(t)
    return ast.dump(t)


kinds = []
for r in pos:
    b, v = read(r["base_path"]), read(r["variant_path"])
    k = ""
    try:
        if d(b, doc=False) == d(v, doc=False):
            k = "ast_identical"
        elif d(b) == d(v):
            k = "docstring_only"
        elif d(b, anon=True) == d(v, anon=True):
            k = "rename_only_(alpha-equivalent)"
        elif d(b, anon=True, const=True) == d(v, anon=True, const=True):
            k = "constant_only_(structure_and_names_identical)"
        else:
            k = "structural_or_name_change"
    except SyntaxError:
        k = "parse_error"
    bl = [l.strip() for l in b.splitlines() if l.strip() and not l.strip().startswith("#")]
    vl = [l.strip() for l in v.splitlines() if l.strip() and not l.strip().startswith("#")]
    kinds.append({"pair_id": r["pair_id"], "edit_kind": k, "evaluated_v8": r["evaluated_v8"],
                  "base_code_lines": len(bl), "variant_code_lines": len(vl)})
with open(DATA / "bugsinpy_positive_edit_kind.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(kinds[0].keys()))
    w.writeheader()
    w.writerows(kinds)
SUM["bugsinpy_positive_edit_kind"] = {
    "all_55": dict(collections.Counter(k["edit_kind"] for k in kinds)),
    "evaluated_v8_41": dict(collections.Counter(k["edit_kind"] for k in kinds if k["evaluated_v8"] == "True"))}

# ====================================================================== 4. header-independent formatting shortcut
def code_lines_without_docs_and_comments(src):
    """lines of src that are not blank / comment-only / inside a docstring statement"""
    tree = ast.parse(src)
    doc_ranges = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b0 = n.body[0]
            if isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str):
                doc_ranges.append((b0.lineno, b0.end_lineno))
    out = []
    for i, l in enumerate(src.splitlines(), 1):
        s = l.rstrip()
        if not s.strip() or s.strip().startswith("#") or any(a <= i <= b for a, b in doc_ranges):
            continue
        out.append(s)
    return out


def fmt_score(src):
    """fraction of the program's code lines (no docstrings / comments / blank) that are NOT a verbatim line of
    ast.unparse(parse(src)) with docstrings removed.  ast.unparse output scores 0 by construction; hand-formatted code > 0."""
    try:
        tree = ast.parse(src)
        un = ast.unparse(strip_doc(ast.parse(src))).splitlines()
    except SyntaxError:
        return None
    L = code_lines_without_docs_and_comments(src)
    if not L:
        return None
    S = set(un)
    return sum(1 for l in L if l not in S) / len(L)


fmt_rows = []
for r in rows:
    if r["corpus"] == "quixbugs_declared":
        continue
    if r["evaluated_v8"] != "True":
        continue
    try:
        fs = fmt_score(read(r["variant_path"]))
    except Exception:  # noqa
        fs = None
    try:
        bs = fmt_score(read(r["base_path"]))
    except Exception:  # noqa
        bs = None
    fmt_rows.append({"corpus": r["corpus"], "pair_id": r["pair_id"], "cluster": r["cluster"], "label": r["label"],
                     "transformation": r["transformation"], "variant_fmt_nonunparse_frac": fs, "base_fmt_nonunparse_frac": bs,
                     "sbg_v5_v8": r["sbg_v5_v8"]})
with open(DATA / "format_shortcut_pairs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(fmt_rows[0].keys()))
    w.writeheader()
    w.writerows(fmt_rows)
SUM["format_shortcut"] = {"definition": "variant_fmt_nonunparse_frac = share of the variant's code lines (docstrings/comments/blank "
                                         "removed) that are not a verbatim line of ast.unparse(variant w/o docstrings). Negatives are "
                                         "ast.unparse products => 0 by construction. Pairs: v8-evaluated.", "tables": {}}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    R = [x for x in fmt_rows if x["corpus"] == corpus and x["variant_fmt_nonunparse_frac"] is not None]
    pos_v = [x["variant_fmt_nonunparse_frac"] for x in R if x["label"] == 1]
    neg_v = [x["variant_fmt_nonunparse_frac"] for x in R if x["label"] == 0]
    t = {"n_pos": len(pos_v), "n_neg": len(neg_v),
         "mean_pos": round(sum(pos_v) / len(pos_v), 4), "mean_neg": round(sum(neg_v) / len(neg_v), 4),
         "neg_all_zero": sum(1 for v in neg_v if v == 0), "pos_all_zero": sum(1 for v in pos_v if v == 0)}
    t["auroc_label_from_variant_format"] = summarize([{"label": x["label"], "cluster": x["cluster"], "s": x["variant_fmt_nonunparse_frac"]} for x in R], "s")
    # excluding SP-2 negatives
    R2 = [x for x in R if x["transformation"] != "SP-2"]
    t["auroc_label_from_variant_format_exclSP2"] = summarize([{"label": x["label"], "cluster": x["cluster"], "s": x["variant_fmt_nonunparse_frac"]} for x in R2], "s")
    # the base (fixed) program side: same score computed on the shared base => neutral reference, not predictive
    SUM["format_shortcut"]["tables"][corpus] = t

(DATA / "leakage_summary.json").write_text(json.dumps(SUM, indent=1, default=str) + "\n")
print(json.dumps({k: SUM[k] for k in ("bugsinpy_lineage", "bugsinpy_cluster_definitions_vs_headline_AUROC",
                                        "bugsinpy_positive_edit_kind", "format_shortcut")}, indent=1, default=str)[:9000])
print(json.dumps(SUM["bugsinpy_content_clusters_fixed_units_jaccard>=0.5"], indent=1)[:2500])
print(SUM["bugsinpy_same_AST_in_multiple_units"]["n_ast_hashes_shared_by_>1_unit"], SUM["bugsinpy_fixed_of_one_bug_is_buggy_of_another"]["n"])
print(SUM["quixbugs_cluster_label_balance_all_pairs"])

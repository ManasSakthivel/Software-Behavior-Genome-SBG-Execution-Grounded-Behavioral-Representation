#!/usr/bin/env python3
"""WP-D / D1 step 5 -- program-level independence of the external corpora from the SBG development corpus.

EXECUTED, execution-free (text/AST only; nothing is run).  Reads SBG/ read-only.

SBG reference set (BASE programs only, deliberately):
   benchmark/corpus/base_programs, benchmark/corpus/fresh_programs, benchmark/v5/corpus/base_programs
Deliberately NOT read: benchmark/datasets/v10_independent/** (V10 test) and any val/test variant tree (V9c val): the
WP-D rules forbid touching them.  The SBG variants are generated from the base programs above, so base-level overlap is the
relevant quantity; this is recorded as a limitation, not hidden.

Measures per external program E vs every SBG program S:
   id_jaccard      Jaccard of the sets of NAME tokens (keywords removed)
   shingle_raw     Jaccard of 5-gram shingles of the token-string stream (names kept)
   shingle_struct  Jaccard of 5-gram shingles with all NAME->ID, NUMBER->NUM, STRING->STR (structure only)
   def_name_hit    external entry/def names that also appear as def names in S
Writes raw/WPD-D1_compat/data/independence_{pairs_top,summary}.json, independence_name_collisions.csv, independence_per_program.csv
"""
import ast
import csv
import io
import json
import keyword
import pathlib
import tokenize

HERE = pathlib.Path(__file__).resolve()
WP = HERE.parents[1]
SBG = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
OUT = WP / "raw" / "WPD-D1_compat" / "data"

REF_DIRS = [SBG / "benchmark/corpus/base_programs", SBG / "benchmark/corpus/fresh_programs",
            SBG / "benchmark/v5/corpus/base_programs"]
SKIP_TOK = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER,
            tokenize.ENCODING}


def toks(src):
    out = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type in SKIP_TOK:
                continue
            out.append((t.type, t.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return out


def ids(tk):
    return {s for t, s in tk if t == tokenize.NAME and not keyword.iskeyword(s)}


def shingles(seq, k=5):
    return {tuple(seq[i:i + k]) for i in range(max(0, len(seq) - k + 1))}


def raw_seq(tk):
    return [s for t, s in tk]


def struct_seq(tk):
    r = []
    for t, s in tk:
        if t == tokenize.NAME and not keyword.iskeyword(s):
            r.append("ID")
        elif t == tokenize.NUMBER:
            r.append("NUM")
        elif t == tokenize.STRING:
            r.append("STR")
        else:
            r.append(s)
    return r


def jac(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def defnames(src):
    try:
        return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    except SyntaxError:
        return set()


def profile(path):
    src = pathlib.Path(path).read_text(errors="replace")
    tk = toks(src)
    return {"src": src, "ids": ids(tk), "sh_raw": shingles(raw_seq(tk)), "sh_struct": shingles(struct_seq(tk)),
            "defs": defnames(src), "ntok": len(tk)}


# ---------------------------------------------------------------- reference set
ref = {}
for d in REF_DIRS:
    for p in sorted(d.glob("*.py")):
        ref[f"{d.relative_to(SBG)}/{p.name}"] = profile(p)
# the same program can sit in several dirs: record exact-duplicate count
print("SBG reference programs:", len(ref))

# ---------------------------------------------------------------- external fixed programs
ext = {}
_subjects = {r["program"] for r in csv.DictReader(open(OUT / "quixbugs_program_ledger.csv")) if r["kind"] == "subject"}
_helpers = []
for p in sorted((SBG / "external/quixbugs/correct_python_programs").glob("*.py")):
    if p.stem not in _subjects:
        _helpers.append(p.stem)  # helper modules (node, ...) are not evaluated subjects -> recorded, not scored
        continue
    ext[("quixbugs", p.stem)] = (p, profile(p))
for p in sorted((SBG / "external/bugsinpy/units").glob("*/fixed.py")):
    ext[("bugsinpy", p.parent.name)] = (p, profile(p))
print("external fixed programs:", len(ext))

rows = []
top = []
colls = []
ref_defs = {}
for k, v in ref.items():
    for n in v["defs"]:
        ref_defs.setdefault(n, []).append(k)
for (corpus, name), (p, e) in ext.items():
    best = {"id_jaccard": (0, None), "shingle_raw": (0, None), "shingle_struct": (0, None)}
    for k, s in ref.items():
        for m, val in (("id_jaccard", jac(e["ids"], s["ids"])), ("shingle_raw", jac(e["sh_raw"], s["sh_raw"])),
                       ("shingle_struct", jac(e["sh_struct"], s["sh_struct"]))):
            if val > best[m][0]:
                best[m] = (val, k)
    stem_hits = [k for k in ref if pathlib.Path(k).stem == name or name.endswith("__" + pathlib.Path(k).stem)]
    def_hits = {n: ref_defs[n] for n in e["defs"] if n in ref_defs}
    rows.append({"corpus": corpus, "program": name, "ntok": e["ntok"],
                 "max_id_jaccard": round(best["id_jaccard"][0], 4), "argmax_id": best["id_jaccard"][1],
                 "max_shingle_raw": round(best["shingle_raw"][0], 4), "argmax_shingle_raw": best["shingle_raw"][1],
                 "max_shingle_struct": round(best["shingle_struct"][0], 4), "argmax_shingle_struct": best["shingle_struct"][1],
                 "file_stem_collision": ";".join(stem_hits), "n_def_name_collisions": len(def_hits)})
    for n, hs in def_hits.items():
        colls.append({"corpus": corpus, "program": name, "def_name": n, "sbg_files": ";".join(hs)})

with open(OUT / "independence_per_program.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
with open(OUT / "independence_name_collisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["corpus", "program", "def_name", "sbg_files"])
    w.writeheader()
    w.writerows(colls)


def dist(vals):
    vals = sorted(vals)
    n = len(vals)
    q = lambda f: vals[min(n - 1, int(f * (n - 1) + 0.5))]  # noqa: E731
    return {"n": n, "max": round(vals[-1], 4), "p95": round(q(0.95), 4), "median": round(q(0.5), 4),
            "mean": round(sum(vals) / n, 4)}


summ = {"quixbugs_non_subject_helper_files_skipped": _helpers, "reference_set": {"dirs": [str(d.relative_to(SBG)) for d in REF_DIRS], "n_programs": len(ref),
                          "excluded_by_rule": ["benchmark/datasets/v10_independent (V10 test)", "V9c validation", "val/test variant trees"]},
        "measures": "id_jaccard = Jaccard of NAME-token sets; shingle_raw/struct = Jaccard of 5-gram token shingles",
        "per_corpus": {}}
for corpus in ("quixbugs", "bugsinpy"):
    R = [r for r in rows if r["corpus"] == corpus]
    d = {m: dist([r[m] for r in R]) for m in ("max_id_jaccard", "max_shingle_raw", "max_shingle_struct")}
    d["n_programs"] = len(R)
    d["top5_by_id_jaccard"] = [{"program": r["program"], "max_id_jaccard": r["max_id_jaccard"], "vs": r["argmax_id"]}
                               for r in sorted(R, key=lambda r: -r["max_id_jaccard"])[:5]]
    d["top5_by_shingle_struct"] = [{"program": r["program"], "max_shingle_struct": r["max_shingle_struct"],
                                    "vs": r["argmax_shingle_struct"]} for r in sorted(R, key=lambda r: -r["max_shingle_struct"])[:5]]
    d["n_programs_with_file_stem_collision"] = sum(1 for r in R if r["file_stem_collision"])
    d["file_stem_collisions"] = [{"program": r["program"], "sbg": r["file_stem_collision"]} for r in R if r["file_stem_collision"]]
    d["n_programs_with_def_name_collision"] = sum(1 for r in R if r["n_def_name_collisions"])
    d["n_programs_ge_0.17_id_jaccard"] = sum(1 for r in R if r["max_id_jaccard"] >= 0.17)
    summ["per_corpus"][corpus] = d
# same-algorithm name collisions between QuixBugs and SBG file/def names (informational)
qdefs = {n for (c, nm), (p, e) in ext.items() if c == "quixbugs" for n in e["defs"]}
summ["quixbugs_entry_names_also_defined_in_sbg_reference"] = sorted(n for n in qdefs if n in ref_defs)
(OUT / "independence_summary.json").write_text(json.dumps(summ, indent=1) + "\n")
print(json.dumps(summ["per_corpus"], indent=1)[:5000])
print("qb entry names also in SBG:", summ["quixbugs_entry_names_also_defined_in_sbg_reference"])

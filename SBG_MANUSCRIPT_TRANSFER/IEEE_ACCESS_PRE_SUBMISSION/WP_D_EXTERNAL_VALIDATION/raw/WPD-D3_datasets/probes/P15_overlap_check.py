#!/usr/bin/env python3
"""P15: read-only overlap check: do SeqCoBench originals (MBPP-derived) or HumanEvalPack/Refactory-reference functions AST-match any top-level function in SBG's python files (benchmark/, external/, baselines/, examples/)?
Normalised ast.dump (annotate_fields=False, no attributes) of each top-level FunctionDef with its name erased. Exact-match only (near-duplicate NOT assessed). Output P15_overlap.json."""
import ast, glob, json, hashlib, sys, os
sys.dont_write_bytecode = True
def key(fn):
    fn = ast.parse(ast.unparse(fn)).body[0]; fn.name = "_"
    return hashlib.sha1(ast.dump(fn, annotate_fields=False).encode()).hexdigest()
SBG = "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"; idx = {}; nfiles = 0; nfail = 0
for root in ("benchmark", "external", "baselines", "examples", "experiments", "sbg", "phase5", "phase6", "phase7", "scripts"):
    for f in glob.glob(f"{SBG}/{root}/**/*.py", recursive=True):
        nfiles += 1
        try: t = ast.parse(open(f, errors="replace").read())
        except Exception: nfail += 1; continue
        for n in t.body:
            if isinstance(n, ast.FunctionDef):
                try: idx.setdefault(key(n), []).append(os.path.relpath(f, SBG) + "::" + n.name)
                except Exception: pass
res = {"sbg_py_files_scanned": nfiles, "parse_fail": nfail, "sbg_function_keys": len(idx)}
def check(name, srcs):
    hit = []
    for tag, s in srcs:
        try: t = ast.parse(s)
        except Exception: continue
        for n in t.body:
            if isinstance(n, ast.FunctionDef):
                try: k = key(n)
                except Exception: continue
                if k in idx: hit.append((tag, n.name, idx[k][:2]))
    res[name] = {"n_sources": len(srcs), "n_function_exact_matches": len(hit), "examples": hit[:6]}
import csv; csv.field_size_limit(10**8)
seq = {}
for s in ("train", "valid", "test"):
    for r in csv.DictReader(open(f"data/seqcobench_{s}.csv", newline="")): seq[hashlib.sha1(r["original_code"].encode()).hexdigest()[:12]] = r["original_code"]
check("seqcobench_originals", list(seq.items()))
hep = json.load(open("data/humanevalpack_python.json")); check("humanevalpack_canonical", [(r["task_id"], r["declaration"] + r["canonical_solution"]) for r in hep])
import glob as g; check("refactory_reference", [(f, open(f).read()) for f in g.glob("data/refactory/data/question_*/code/reference/*.py")])
json.dump(res, open("P15_overlap.json", "w"), indent=1); print(json.dumps(res, indent=1)[:1800])

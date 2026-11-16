#!/usr/bin/env python3
"""P07: can an INDEPENDENT tool (python-minifier 3.4.0, MIT; not an SBG transformer) generate non-trivial, behaviour-preserving variants of
HumanEvalPack canonical solutions, with annotations preserved (SBG's input synthesis is annotation-driven)?  Run under probes/_venv_tools python.
Writes data/hep_min/*.py, P07_minify.json. Behaviour check is done by P05_worker via P07b (separate step)."""
import ast, json, sys, os, hashlib, python_minifier as pm
rows = json.load(open("data/humanevalpack_python.json")); os.makedirs("data/hep_min", exist_ok=True)
rec = {"python_minifier": pm.__file__.split("site-packages")[-1], "options": "remove_annotations=False, rename_locals=True, rename_globals=False, hoist_literals=False, constant_folding=True, remove_dead_branches=True, remove_literal_statements=False, combine_imports=True, remove_pass=True, convert_posargs_to_args=False, prefer_single_line=False", "tasks": []}
def norm(s): return ast.dump(ast.parse(s))
for r in rows:
    tid = r["task_id"].split("/")[1]; src = r["declaration"] + r["canonical_solution"] + "\n"; t = {"task": tid}
    try:
        m = pm.minify(src, remove_annotations=pm.RemoveAnnotationsOptions(False, False, False, False), rename_locals=True, rename_globals=False, hoist_literals=False,
                      constant_folding=True, remove_dead_branches=True, remove_literal_statements=False, convert_posargs_to_args=False, prefer_single_line=False)
        ast.parse(m); t["compiles"] = True; t["ast_differs"] = norm(m) != norm(src); t["bytes_in"] = len(src); t["bytes_out"] = len(m)
        open(f"data/hep_min/{tid}_min.py", "w").write(m + "\n")
    except Exception as e:
        t["compiles"] = False; t["err"] = repr(e)[:120]
    rec["tasks"].append(t)
rec["n"] = len(rows); rec["n_compiles"] = sum(t["compiles"] for t in rec["tasks"]); rec["n_ast_differs"] = sum(t.get("ast_differs", False) for t in rec["tasks"])
json.dump(rec, open("P07_minify.json", "w"), indent=1); print({k: v for k, v in rec.items() if k != "tasks"})

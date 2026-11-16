#!/usr/bin/env python3
"""P08: STATIC scan of the CPython 3.11 stdlib (offline, /opt/homebrew) for SBG-compatible, self-contained top-level functions (no execution).
Self-contained = all free/global names referenced are builtins or the function's own params/locals (no module globals, no imports used inside).
Output: P08_stdlib_scan.json"""
import ast, builtins, glob, json, os, symtable, collections, sys
LIB = "/opt/homebrew/Cellar/python@3.11/3.11.15_3/Frameworks/Python.framework/Versions/3.11/lib/python3.11"
B = set(dir(builtins)); res = {"lib": LIB, "modules": 0, "funcs": 0, "public_funcs": 0, "self_contained": 0, "self_contained_annotated_all": 0, "self_contained_1to3_params": 0, "by_module": {}}
for f in sorted(glob.glob(LIB + "/*.py")):
    m = os.path.basename(f)[:-3]
    if m.startswith("_") or m.startswith("test"): continue
    src = open(f, errors="replace").read()
    try: tree = ast.parse(src); st = symtable.symtable(src, f, "exec")
    except Exception: continue
    res["modules"] += 1; tops = {c.get_name(): c for c in st.get_children() if c.get_type() == "function"}
    n_sc = 0
    for n in tree.body:
        if not isinstance(n, ast.FunctionDef): continue
        res["funcs"] += 1
        if n.name.startswith("_"): continue
        res["public_funcs"] += 1; t = tops.get(n.name)
        if t is None: continue
        def free_globals(tb):
            g = {s.get_name() for s in tb.get_symbols() if s.is_global() and s.is_referenced()}
            for c in tb.get_children(): g |= free_globals(c)
            return g
        if free_globals(t) <= B and not any(isinstance(x, (ast.Import, ast.ImportFrom, ast.Yield, ast.YieldFrom, ast.Await)) for x in ast.walk(n)):
            res["self_contained"] += 1; n_sc += 1
            na = len(n.args.args) - len(n.args.defaults)
            if 1 <= na <= 3: res["self_contained_1to3_params"] += 1
            if all(a.annotation is not None for a in n.args.args) and n.args.args: res["self_contained_annotated_all"] += 1
    if n_sc: res["by_module"][m] = n_sc
res["top_modules"] = sorted(res["by_module"].items(), key=lambda kv: -kv[1])[:12]; del res["by_module"]
json.dump(res, open("P08_stdlib_scan.json", "w"), indent=1); print(res)

"""Static AST count (no execution, no scoring) of PEP-709-inlinable comprehensions (list/set/dict) and genexps per corpus program.
Read-only on the COPY. Output: outputs/comprehension_exposure.json"""
import ast, json, pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent / "copy"
res = {}
for d in ("benchmark/corpus/base_programs", "benchmark/corpus/fresh_programs"):
    n = tot = 0; with_c = 0; per = {}
    for f in sorted((root/d).glob("*.py")):
        try: t = ast.parse(f.read_text())
        except SyntaxError: continue
        c = sum(isinstance(x,(ast.ListComp,ast.SetComp,ast.DictComp)) for x in ast.walk(t))
        g = sum(isinstance(x,ast.GeneratorExp) for x in ast.walk(t))
        per[f.name] = {"inlinable_comps": c, "genexps": g}
        n += 1; tot += c; with_c += (c>0)
    res[d] = {"n_programs": n, "programs_with_inlinable_comp": with_c, "total_inlinable_comps": tot, "per_program": per}
json.dump(res, open(root.parent/"outputs"/"comprehension_exposure.json","w"), indent=1)
for k,v in res.items(): print(k, v["n_programs"], "programs;", v["programs_with_inlinable_comp"], "with >=1 list/set/dict comprehension;", v["total_inlinable_comps"], "total")

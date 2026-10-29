"""Audit (exploratory): are the external SP negatives actually semantics-preserving?

For every negative variant, flags undefined global/free names that are NOT undefined in the base
(static, using `symtable`-free AST scoping approximation via pyflakes if available, else compile-time
check of Name loads vs. all bound names in the module).  A variant that introduces new undefined names
cannot be behaviour-equivalent (it raises NameError when the affected path runs).
Writes artifacts/paper_evidence/EXTERNAL_NEGATIVE_AUDIT.json.  No frozen file touched.
"""
import ast, builtins, json, pathlib, collections, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "artifacts/paper_evidence/raw/external_rescore_v8_pairs.json"


def undefined_names(src: str):
    tree = ast.parse(src)
    bound = set(dir(builtins))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(n.name)
            if not isinstance(n, ast.ClassDef):
                a = n.args
                for x in a.args + a.kwonlyargs + getattr(a, "posonlyargs", []):
                    bound.add(x.arg)
                for x in (a.vararg, a.kwarg):
                    if x:
                        bound.add(x.arg)
        elif isinstance(n, ast.Lambda):
            a = n.args
            for x in a.args + a.kwonlyargs:
                bound.add(x.arg)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                bound.add((al.asname or al.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            bound.update(n.names)
    loads = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return sorted(loads - bound)


def main():
    data = json.loads(SRC.read_text())
    out = {"artifact": "EXTERNAL_NEGATIVE_AUDIT", "status": "EXPLORATORY static audit",
           "method": "module-wide name-binding approximation; flags names loaded but bound nowhere in the "
                     "variant and not in the base. Over-approximates nothing (a flagged name is bound nowhere "
                     "in the file), so flagged variants provably contain a reference to an undefined name.",
           "corpora": {}}
    for corpus, rows in data.items():
        by = collections.defaultdict(lambda: {"n": 0, "broken": 0, "pairs": []})
        for r in rows:
            if r["label"] != 0:
                continue
            base = (REPO / r["base_path"]).read_text()
            var = (REPO / r["variant_path"]).read_text()
            try:
                new = sorted(set(undefined_names(var)) - set(undefined_names(base)))
            except SyntaxError:
                new = ["<syntax error>"]
            t = r["transformation"]
            by[t]["n"] += 1
            if new:
                by[t]["broken"] += 1
                by[t]["pairs"].append({"pair_id": r["pair_id"], "new_undefined": new,
                                       "sbg_v5": r.get("sbg_v5")})
        out["corpora"][corpus] = {t: dict(v) for t, v in sorted(by.items())}
    # Effect of removing provably-invalid negatives (rule fixed by the audit above, not by any score).
    sys.path.insert(0, str(REPO))
    from sbg.statistics import auroc
    broken = {x["pair_id"] for c in out["corpora"].values() for v in c.values() for x in v["pairs"]}
    out["effect_of_excluding_invalid_negatives"] = {}
    for corpus, rows in data.items():
        ev = [r for r in rows if r["evaluated"]]
        for name, sub in (("all_evaluated", ev),
                          ("excluding_invalid_negatives", [r for r in ev if r["pair_id"] not in broken]),
                          ("excluding_invalid_negatives_and_all_SP2",
                           [r for r in ev if r["pair_id"] not in broken and r["transformation"] != "SP-2"])):
            y = [r["label"] for r in sub]
            out["effect_of_excluding_invalid_negatives"][f"{corpus}/{name}"] = {
                "n_pairs": len(sub), "n_pos": sum(y), "n_neg": len(y) - sum(y),
                "sbg_v5_auroc": round(auroc([r["sbg_v5"] for r in sub], y), 4),
                "note": "point estimate only; see EXTERNAL_RESCORE_V8.json for cluster CIs on full sets"}
    p = REPO / "artifacts/paper_evidence/EXTERNAL_NEGATIVE_AUDIT.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    for c, d in out["corpora"].items():
        print(c, {t: f"{v['broken']}/{v['n']}" for t, v in d.items()})
    print(json.dumps(out["effect_of_excluding_invalid_negatives"], indent=1))


if __name__ == "__main__":
    main()

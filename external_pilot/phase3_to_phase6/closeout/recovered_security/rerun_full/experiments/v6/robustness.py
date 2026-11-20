"""Robustness: d_v6 between a DEV base program and a semantics-preserving / degraded version of itself.

  PYTHONHASHSEED=0 python experiments/v6/robustness.py   -> artifacts/v6/ROBUSTNESS.json
Invariance = block distances <= 1e-9 and status != UNKNOWN. Degradations must become UNKNOWN (never distance 0).
"""
import ast, copy, json, pathlib, sys, tempfile, builtins
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from sbgv6.observe import PythonAdapter
from sbgv6.distance import pair_record
from experiments.v6.extract_pairs import load, STALE

BUILTIN = set(dir(builtins))


class Rename(ast.NodeTransformer):
    def __init__(self, local, func):
        self.local, self.func, self.m = local, func, {}
    def _n(self, n, p):
        return self.m.setdefault(n, f"{p}{len(self.m)}")
    def visit_FunctionDef(self, node):
        if self.func and node.name not in ("__init__",) and not node.name.startswith("__"):
            node.name = self._n(node.name, "fn_")
        if self.local:
            for a in node.args.args:
                a.arg = self._n(a.arg, "v_") if a.arg != "self" else a.arg
        self.generic_visit(node)
        return node
    def visit_Name(self, node):
        if node.id in BUILTIN or node.id in ("self", "__name__"):
            return node
        stored = isinstance(node.ctx, ast.Store)
        if self.local and (stored or node.id in self.m):
            node.id = self._n(node.id, "v_")
        elif self.func and node.id in self.m:
            node.id = self.m[node.id]
        return node


def t_rename_var(s): return ast.unparse(Rename(True, False).visit(ast.parse(s)))
def t_format(s): return ast.unparse(ast.parse(s))
def t_comments(s): return "\n".join(l + "  # c" if l.strip() and not l.rstrip().endswith(":") else l for l in ("# hdr\n\n" + s).splitlines())
def t_rename_func(s):
    tree = ast.parse(s)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("__")}
    r = Rename(False, True)
    for n in names:
        r.m[n] = f"fn_{len(r.m)}"
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name in r.m:
            n.name = r.m[n.name]
        if isinstance(n, ast.Name) and n.id in r.m:
            n.id = r.m[n.id]
    return ast.unparse(tree)


def t_reorder(s):
    """Swap adjacent independent simple assignments (disjoint names, both side-effect free constants/names)."""
    tree = ast.parse(s)
    for node in ast.walk(tree):
        b = getattr(node, "body", None)
        if not isinstance(b, list):
            continue
        for i in range(len(b) - 1):
            x, y = b[i], b[i + 1]
            if isinstance(x, ast.Assign) and isinstance(y, ast.Assign) and all(isinstance(v.value, ast.Constant) for v in (x, y)):
                nx = {n.id for n in ast.walk(x) if isinstance(n, ast.Name)}; ny = {n.id for n in ast.walk(y) if isinstance(n, ast.Name)}
                if not nx & ny:
                    b[i], b[i + 1] = y, x
                    return ast.unparse(tree)
    return None


TRANS = {"rename_variables": t_rename_var, "rename_functions": t_rename_func, "format_unparse": t_format,
         "comments_blank": t_comments, "reorder_independent": t_reorder}


def main():
    ad, tmp = PythonAdapter(), pathlib.Path(tempfile.mkdtemp())
    rows = [r for n in ("v8train",) for r in load(n)]
    bases = sorted({r["_paths"]["base_path"] for r in rows})
    out = {}
    for name, fn in list(TRANS.items()) + [("truncate_50pct", None), ("truncate_25pct", None), ("syntax_error", None)]:
        res = []
        for bp in bases:
            src = (REPO / bp).read_text()
            a = ad.observe(str(REPO / bp))
            if name.startswith("truncate"):
                frac = 0.5 if "50" in name else 0.25
                b = ad.observe(str(REPO / bp))
                for run in b.runs:
                    for t in run:
                        t.events = t.events[: max(1, int(len(t.events) * frac))]; t.truncated = True
            else:
                try:
                    new = "def broken(:\n" if name == "syntax_error" else fn(src)
                except Exception:
                    new = None
                if new is None or new == src:
                    continue
                p = tmp / (pathlib.Path(bp).stem + f"__{name}.py"); p.write_text(new)
                b = ad.observe(str(p))
            r = pair_record(a, b)
            res.append({"program": pathlib.Path(bp).stem, "status": r["status"], "d_A": r["d_A"], "d_B": r["d_B"],
                        "d_C": r["d_C"], "delta_out": r["delta_out"], "reasons": r["reasons"][:2],
                        "valid_transform": name in ("truncate_50pct", "truncate_25pct", "syntax_error")
                        or (r["delta_out"] == 0 and a.record.entry_discovery == b.record.entry_discovery)})
        invalid = [x["program"] for x in res if not x["valid_transform"]]
        res = [x for x in res if x["valid_transform"]]   # transformation verified semantics-preserving (outputs equal, same entry)
        inv = [x for x in res if x["status"] != "UNKNOWN" and all((x[k] or 0) <= 1e-9 for k in ("d_A", "d_B", "d_C"))]
        unk = [x for x in res if x["status"] == "UNKNOWN"]
        out[name] = {"n": len(res), "n_invalid_transform_excluded": len(invalid), "invalid_programs": invalid[:20], "invariant": len(inv), "unknown": len(unk),
                     "changed_programs": [x["program"] for x in res if x not in inv and x not in unk][:15],
                     "mean_d_B_defined": (sum(x["d_B"] for x in res if x["d_B"] is not None) / max(1, sum(x["d_B"] is not None for x in res)))}
        print(name, {k: out[name][k] for k in ("n", "invariant", "unknown")}, flush=True)
    (REPO / "artifacts/v6/ROBUSTNESS.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

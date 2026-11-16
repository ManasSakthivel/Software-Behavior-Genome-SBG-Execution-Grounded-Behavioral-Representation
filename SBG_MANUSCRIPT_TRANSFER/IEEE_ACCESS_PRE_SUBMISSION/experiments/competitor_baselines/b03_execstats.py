"""B03a execution-statistics extras (class A) and B06a label-oracle ceilings (privileged; sanity only)."""
from __future__ import annotations

import ast
import re

from bl_common import scrub

EXEC_EXTRA = ("n_events", "trace_len_mean")


def _ratio(a, b):
    d = abs(a - b)
    return d / (1.0 + d)


def exec_features(fa, fb):
    """n_events: repo-style ratio distance of stats['n_events'] (not in the frozen rows); trace_len_mean: mean per-input |len diff|/max len."""
    out = {"n_events": _ratio(fa.stats.get("n_events", 0), fb.stats.get("n_events", 0))}
    n = min(len(fa.inputs), len(fb.inputs))
    vals = []
    for i in range(n):
        la, lb = len(fa.inputs[i]["events"]), len(fb.inputs[i]["events"])
        vals.append(abs(la - lb) / max(la, lb, 1))
    out["trace_len_mean"] = sum(vals) / len(vals) if vals else 0.0
    return out


def _defined(ft):
    try:
        tree = ast.parse("\n".join(ft.source_lines()))
    except SyntaxError:
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def _exc_type(e):
    return None if e is None else str(e).split(":", 1)[0]


def _extcalls(inp, defined):
    return [e[1] for e in inp["events"] if e[0] == "c" and not e[1].startswith("<") and e[1] not in defined]


def oracle_features(fa, fb):
    """Same-input output differencing on the 11 PROTOCOL inputs = label-defining inputs => tautological ceiling (never a competitor).
    ret/exc-type/stdout compared (argument mutation is NOT in the cache, so the ceiling can be < 1)."""
    n = min(len(fa.inputs), len(fb.inputs))
    da, db = _defined(fa), _defined(fb)
    d_core, d_msg, d_cg = [], [], []
    for i in range(n):
        a, b = fa.inputs[i], fb.inputs[i]
        core = (scrub(a["ret"]) != scrub(b["ret"])) or (_exc_type(a["exc"]) != _exc_type(b["exc"])) or (a["stdout"] != b["stdout"])
        msg = core or (scrub(a["exc"]) != scrub(b["exc"]))
        cg = core or (_extcalls(a, da) != _extcalls(b, db))
        d_core.append(core)
        d_msg.append(msg)
        d_cg.append(cg)
    f = lambda v: sum(v) / len(v) if v else 0.0  # noqa: E731
    return {"oracle|frac11": f(d_core), "oracle|any11": float(any(d_core)), "oracle|frac11_excmsg": f(d_msg), "changeguard_cmp|frac11": f(d_cg),
            "changeguard_cmp|any11": float(any(d_cg))}

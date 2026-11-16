"""B04b — value-spectra / observation-point comparison from cached locals snapshots (class B, ADAPTED; Xie & Notkin 2005 style, DCI-style observation points).

Observation points per input (multiset):
  args        : (function, sorted values of the call-entry snapshot)                      -> OUTPUT-FREE (no exit/return state)
  entry_exit  : (function, entry values, exit values) per invocation = value spectrum      -> PRIVILEGED (exit locals reveal results)
  exit        : (function, sorted values of the return-event snapshot)                     -> PRIVILEGED
Variable names are dropped (values sorted) -> robust to local renaming; function names raw / entry / full canonicalised.
abstraction: raw repr | abs (type + sign / length bucket).
Score: 1 - weighted-Jaccard(multiset_base, multiset_variant) per input, aggregated mean / max over inputs.
Note: the tracer snapshots frame LOCALS (repr capped at 100 chars); for the entry function the true return value is only in trace.ret.
"""
from __future__ import annotations

import ast
import collections
import re

from bl_common import wjaccard_dist, agg, canon_fn

KINDS = ("args", "entry_exit", "exit")
CANONS = ("raw", "entry", "full")
ABS = ("raw", "abs")
AGGS = ("mean", "max")
OUTPUT_FREE = {"args"}


def config_names():
    return [f"valuespectra|{k}|{c}|{ab}|{a}" for k in KINDS for c in CANONS for ab in ABS for a in AGGS]


_abs_cache = {}
_DIG = re.compile(r"-?\d+(\.\d+)?")


def abstract(v):
    r = _abs_cache.get(v)
    if r is not None:
        return r
    try:
        x = ast.literal_eval(v)
    except Exception:  # noqa: BLE001
        r = _DIG.sub("N", v)[:40]
        _abs_cache[v] = r
        return r
    if isinstance(x, bool) or x is None:
        r = repr(x)
    elif isinstance(x, (int, float)):
        r = type(x).__name__ + ("-" if x < 0 else "0" if x == 0 else "+")
    elif isinstance(x, (str, list, tuple, dict, set)):
        n = len(x)
        r = f"{type(x).__name__}[{n if n < 4 else '4+'}]"
    else:
        r = type(x).__name__
    _abs_cache[v] = r
    return r


def _vals(snap, ab):
    if not isinstance(snap, dict):
        return ()
    vs = [str(v) for v in snap.values()]
    if ab == "abs":
        vs = [abstract(v) for v in vs]
    return tuple(sorted(vs))


def _obs(inp, entry, kind, canon, ab):
    ev = inp["events"]
    m = canon_fn(ev, entry, canon)
    c = collections.Counter()
    stack = []
    for t, fn, ln, snap in ev:
        f = m.get(fn, fn)
        if kind == "args":
            if t == "c":
                c[(f, _vals(snap, ab))] += 1
        elif kind == "exit":
            if t == "r":
                c[(f, _vals(snap, ab))] += 1
        else:
            if t == "c":
                stack.append((f, _vals(snap, ab)))
            elif t == "r" and stack:
                f0, ent = stack.pop()
                c[(f0, ent, _vals(snap, ab))] += 1
    if kind == "entry_exit":
        for f0, ent in stack:                         # frames never returned (truncated / exception)
            c[(f0, ent, None)] += 1
    return c


def pair_features(fa, fb):
    out = {}
    n = min(len(fa.inputs), len(fb.inputs))
    for kind in KINDS:
        for canon in CANONS:
            for ab in ABS:
                vals = [wjaccard_dist(_obs(fa.inputs[i], fa.entry, kind, canon, ab), _obs(fb.inputs[i], fb.entry, kind, canon, ab)) for i in range(n)]
                for a in AGGS:
                    out[f"valuespectra|{kind}|{canon}|{ab}|{a}"] = agg(vals, a)
    return out

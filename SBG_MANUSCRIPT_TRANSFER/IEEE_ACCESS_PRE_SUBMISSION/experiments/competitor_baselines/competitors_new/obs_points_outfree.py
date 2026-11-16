"""obs_points_outfree -- observation-point differencing, OUTPUT-FREE variant (DCI/DSpot-inspired and Xie & Notkin value-spectra-inspired; class C->B
adaptation, ADAPTED from abstract-level descriptions: DCI paper full text read, DSpot is a Java test amplifier and is NOT ported, Xie & Notkin 2005 abstract only).

Idea (DCI 'assert on every observable value' / X&N 'function-boundary value spectra'): execute old and new on the same input and compare *internal* observation
points instead of final outputs.  Per protocol input the observation-point multiset of one version is
    {("A", f, sorted raw argument values of the call event)}                  -- values handed to every function call (entry-function args = the input)
  + {("S", f, sorted *abstract* locals at the return event)}                  -- abstract = type + length / sign bucket, values NOT kept
with f = function name anonymised by first appearance in that trace and variable *names dropped* (values sorted) => invariant to function/local renaming.
Reads NOTHING of ``ret`` / ``exc`` / ``stdout`` and no exception events ('e').  Grey zone (declared): call arguments of inner functions and return-time locals
are internal states produced by the computation (the same raw material as SBG's state genome), so this is "output-free" in the SBG/PROTOCOL sense only.
Score = mean over the 11 inputs of weighted-Jaccard distance (1 - sum min / sum max) between the base and variant multisets.
``score_pair_multi``: mean / max aggregation x {args+abs-locals (default), args only, abs-locals only}.
"""
from __future__ import annotations

import ast
import collections
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

_DIG = re.compile(r"-?\d+(\.\d+)?")
_abs = {}


def abstract_value(v):
    """repr string -> coarse abstraction: numbers -> (type, sign), containers/str -> (type, len bucket 0..3,4+), bool/None kept, else digits->N."""
    r = _abs.get(v)
    if r is not None:
        return r
    try:
        x = ast.literal_eval(v)
    except Exception:  # noqa: BLE001
        r = _DIG.sub("N", v)[:40]
        _abs[v] = r
        return r
    if isinstance(x, bool) or x is None:
        r = repr(x)
    elif isinstance(x, (int, float)):
        r = type(x).__name__ + ("-" if x < 0 else "0" if x == 0 else "+")
    elif isinstance(x, (str, list, tuple, dict, set, frozenset)):
        n = len(x)
        r = f"{type(x).__name__}[{n if n < 4 else '4+'}]"
    else:
        r = type(x).__name__
    _abs[v] = r
    return r


def _vals(snap, how):
    if not isinstance(snap, dict):
        return ()
    vs = [str(v) for v in snap.values()]
    if how == "abs":
        vs = [abstract_value(v) for v in vs]
    return tuple(sorted(vs))


def obs_multiset(inp, parts=("A", "S"), reading=False):
    """Counter of observation points of one trace.  reading=True adds raw return-time locals, exception frames and the entry ret/exc/stdout (privileged)."""
    ev = inp["events"]
    m = L.anon_map(e[1] for e in ev)
    c = collections.Counter()
    for t, fn, ln, snap in ev:
        f = m[fn]
        if t == "c" and "A" in parts:
            c[("A", f, _vals(snap, "raw"))] += 1
        elif t == "r":
            if "S" in parts:
                c[("S", f, _vals(snap, "abs"))] += 1
            if reading:
                c[("R", f, _vals(snap, "raw"))] += 1
        elif t == "e" and reading:
            c[("E", f)] += 1
    if reading:
        c[("RET", inp.get("ret"), inp.get("ret_type"))] += 1
        c[("EXC", inp.get("exc"))] += 1
        c[("OUT", inp.get("stdout"))] += 1
    return c


def _score(base, var, ctx, parts, reading):
    fa, fb = ctx.trace(base), ctx.trace(var)
    if not (fa.ok and fb.ok):
        return None
    return [L.wjaccard_dist(obs_multiset(a, parts, reading), obs_multiset(b, parts, reading)) for a, b in L.paired_inputs(fa, fb)]


def score_pair(base_record, variant_record, ctx):
    v = _score(base_record, variant_record, ctx, ("A", "S"), False)
    return L.NAN if not v else L.mean(v)


def score_pair_multi(base_record, variant_record, ctx):
    out = {}
    for name, parts in (("args_abslocals", ("A", "S")), ("args", ("A",)), ("abslocals", ("S",))):
        v = _score(base_record, variant_record, ctx, parts, False)
        out[f"obs_outfree_{name}_mean"] = L.NAN if not v else L.mean(v)
        out[f"obs_outfree_{name}_max"] = L.NAN if not v else max(v)
    return out

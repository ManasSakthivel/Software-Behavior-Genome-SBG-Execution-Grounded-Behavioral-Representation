"""trace_align -- Sumner & Zhang-style execution-trace alignment on the cached traces (class B, ADAPTED, output-free).

NOT Sumner & Zhang's causality-inference technique (ICSE'13 "Comparative causality" is a debugging method: state replacement + slicing; paper read at
ABSTRACT level only).  What is implemented is the *alignment step common to execution-comparison work*: the two executions on the same input are aligned
as event sequences and the unmatched part is the difference.

Per protocol input i (11 inputs, run 0):  A_i, B_i = sequences of executed-statement events (type in {call, line}, function, line) of base / variant
(driver wrapper frames removed).  Global alignment (Needleman-Wunsch with match 0, mismatch 2, gap 1 == indel alignment, solved exactly with the
bit-parallel LCS): unmatched_i = 1 - 2 LCS(A_i,B_i) / (|A_i| + |B_i|).   score = mean_i unmatched_i  (max_i in multi).
Variants:
  naive   : tokens (type, function name, raw line number)             -- not rename- nor line-shift-robust
  robust  : tokens (type, function anonymised by first appearance in that trace, *line shape*: the source line text with identifiers erased, whitespace
            normalised) -- invariant to identifier renaming, comment/blank-line insertion and line renumbering.
``score_pair`` = robust, mean.  ``score_pair_multi``: naive/robust x mean/max, plus ``first_div_robust`` (1 - first-divergence position / max length).
Reads no return value / exception / stdout.  Needs from the cache: events (type, function, lineno) per input; source text of both files (line shapes).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

_shape_cache = {}


def _shapes(ctx, rec):
    src = ctx.source(rec)
    if src is None:
        return None
    key = hash(src)
    if key not in _shape_cache:
        _shape_cache[key] = [L.line_shape(x) for x in src.splitlines()]
    return _shape_cache[key]


def _tokens(inp, shapes, robust):
    ev = [e for e in inp["events"] if e[0] in "cl"]
    if not robust:
        return [(e[0], e[1], e[2]) for e in ev]
    m = L.anon_map(e[1] for e in ev)
    out = []
    for t, fn, ln, _ in ev:
        s = shapes[ln - 1] if shapes is not None and 0 < ln <= len(shapes) else "?"
        out.append((t, m[fn], s))
    return out


def _first_div(a, b):
    n = max(len(a), len(b))
    if n == 0:
        return 0.0
    i, m = 0, min(len(a), len(b))
    while i < m and a[i] == b[i]:
        i += 1
    return 0.0 if i == len(a) == len(b) else 1.0 - i / n


def _per_input(base, var, ctx):
    fa, fb = ctx.trace(base), ctx.trace(var)
    if not (fa.ok and fb.ok):
        return None
    sa, sb = _shapes(ctx, base), _shapes(ctx, var)
    res = {"naive": [], "robust": [], "fd": []}
    for ia, ib in L.paired_inputs(fa, fb):
        res["naive"].append(L.unmatched_fraction(_tokens(ia, sa, False), _tokens(ib, sb, False)))
        ra, rb = _tokens(ia, sa, True), _tokens(ib, sb, True)
        res["robust"].append(L.unmatched_fraction(ra, rb))
        res["fd"].append(_first_div(ra, rb))
    return res


def score_pair(base_record, variant_record, ctx):
    r = _per_input(base_record, variant_record, ctx)
    if r is None or not r["robust"]:
        return L.NAN
    return L.mean(r["robust"])


def score_pair_multi(base_record, variant_record, ctx):
    r = _per_input(base_record, variant_record, ctx)
    if r is None or not r["robust"]:
        return {k: L.NAN for k in ("align_robust_mean", "align_robust_max", "align_naive_mean", "align_naive_max", "first_div_robust_mean")}
    return {"align_robust_mean": L.mean(r["robust"]), "align_robust_max": max(r["robust"]), "align_naive_mean": L.mean(r["naive"]),
            "align_naive_max": max(r["naive"]), "first_div_robust_mean": L.mean(r["fd"])}

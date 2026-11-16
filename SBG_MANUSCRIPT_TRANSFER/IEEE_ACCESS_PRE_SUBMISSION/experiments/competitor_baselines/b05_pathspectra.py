"""B05b — path/line spectra baselines (class B, ADAPTED from abstract-level descriptions of Reps/Harrold path spectra, Xie&Notkin path spectra; output-free).

kinds: covset (Jaccard of covered-line sets), hitmulti (weighted Jaccard of line-hit counts from `l` events),
invpath (weighted Jaccard of per-invocation executed-line sequences = Ball-Larus-style complete-path spectrum, not true BL numbering),
fnprofile (Bray-Curtis distance of per-function line-event counts).
keys: raw line number | shape (source line with identifiers erased -> robust to renames and line shifts).
agg: mean / max over inputs, pooled (counters summed over inputs, one distance).
"""
from __future__ import annotations

import collections
import keyword
import re

from bl_common import wjaccard_dist, jaccard_dist, agg, canon_fn

KEYS = ("raw", "shape")
KINDS = ("covset", "hitmulti", "invpath")
AGGS = ("mean", "max", "pooled")
FN_CANONS = ("raw", "entry", "full")
_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def config_names():
    return [f"pathspectra|{k}|{kd}|{a}" for k in KEYS for kd in KINDS for a in AGGS] + [f"pathspectra|fnprofile|{c}|{a}" for c in FN_CANONS for a in AGGS]


def shape_of(line):
    s = line.split("#", 1)[0]
    s = _ID.sub(lambda m: m.group(0) if keyword.iskeyword(m.group(0)) else "I", s)
    return " ".join(s.split())


def _shape_table(ft):
    lines = ft.source_lines()
    return lambda ln: shape_of(lines[ln - 1]) if 0 < ln <= len(lines) else "?"


def _per_input(ft, key, cache):
    """list of dicts per input: cov(set), hit(Counter), inv(Counter)."""
    out = []
    kf = (lambda ln: ln) if key == "raw" else cache
    for inp in ft.inputs:
        cov = {kf(ln) for ln in inp["cov"]}
        hit = collections.Counter()
        inv = collections.Counter()
        stack = []
        for t, fn, ln, _ in inp["events"]:
            if t == "c":
                stack.append([])
            elif t == "l":
                k = kf(ln)
                hit[k] += 1
                if stack:
                    stack[-1].append(k)
            elif t == "r" and stack:
                inv[tuple(stack.pop())] += 1
        for rest in stack:
            inv[tuple(rest)] += 1
        out.append({"covset": cov, "hitmulti": hit, "invpath": inv})
    return out


def _fnprofile(ft, canon):
    out = []
    for inp in ft.inputs:
        m = canon_fn(inp["events"], ft.entry, canon)
        c = collections.Counter()
        for t, fn, ln, _ in inp["events"]:
            if t == "l":
                c[m.get(fn, fn)] += 1
        out.append(c)
    return out


def _bc(a, b):
    num = sum(abs(a.get(k, 0) - b.get(k, 0)) for k in a.keys() | b.keys())
    den = sum(a.values()) + sum(b.values())
    return num / den if den else 0.0


def pair_features(fa, fb):
    out = {}
    n = min(len(fa.inputs), len(fb.inputs))
    for key in KEYS:
        pa = _per_input(fa, key, _shape_table(fa))
        pb = _per_input(fb, key, _shape_table(fb))
        for kd in KINDS:
            vals = []
            for i in range(n):
                x, y = pa[i][kd], pb[i][kd]
                vals.append(jaccard_dist(x, y) if kd == "covset" else wjaccard_dist(x, y))
            out[f"pathspectra|{key}|{kd}|mean"] = agg(vals, "mean")
            out[f"pathspectra|{key}|{kd}|max"] = agg(vals, "max")
            if kd == "covset":
                ua = set().union(*[pa[i][kd] for i in range(n)]) if n else set()
                ub = set().union(*[pb[i][kd] for i in range(n)]) if n else set()
                out[f"pathspectra|{key}|{kd}|pooled"] = jaccard_dist(ua, ub)
            else:
                ca, cb = collections.Counter(), collections.Counter()
                for i in range(n):
                    ca.update(pa[i][kd])
                    cb.update(pb[i][kd])
                out[f"pathspectra|{key}|{kd}|pooled"] = wjaccard_dist(ca, cb)
    for canon in FN_CANONS:
        qa, qb = _fnprofile(fa, canon), _fnprofile(fb, canon)
        vals = [_bc(qa[i], qb[i]) for i in range(n)]
        out[f"pathspectra|fnprofile|{canon}|mean"] = agg(vals, "mean")
        out[f"pathspectra|fnprofile|{canon}|max"] = agg(vals, "max")
        ca, cb = collections.Counter(), collections.Counter()
        for i in range(n):
            ca.update(qa[i])
            cb.update(qb[i])
        out[f"pathspectra|fnprofile|{canon}|pooled"] = _bc(ca, cb)
    return out

"""Shared helpers for the A4 competitor baselines (pure stdlib; REPO is only ever READ).

Trace-cache access, wrapper-frame removal, function-name canonicalisation and the fast sequence/multiset distance primitives
(bit-parallel LCS and Levenshtein, weighted Jaccard, k-gram Jaccard).
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parents[1]
REPO = PKG.parent / "SBG"
CACHE = PKG / "results" / "raw" / "trace_cache"
sys.path.insert(0, str(PKG / "experiments" / "common"))
import eval_lib  # noqa: E402

POPS = ("v9c_train", "v9c_dev", "v9c_val", "v10_test")


# ------------------------------------------------------------------ trace cache
def cache_file(pop: str, base_id: str, path: str) -> pathlib.Path:
    return CACHE / pop / base_id / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")


_ADDR = re.compile(r"0x[0-9a-fA-F]+")
_FUNC = re.compile(r"<function [^>]*>")


def scrub(s):
    if not isinstance(s, str):
        return s
    return _ADDR.sub("0x", _FUNC.sub("<function>", s))


class FileTrace:
    """One cached program file: per input a cleaned event list [(type, fn, lineno, snap_dict_or_None)]."""

    def __init__(self, pop: str, base_id: str, path: str):
        fn = cache_file(pop, base_id, path)
        self.path = path
        self.ok = False
        self.extract_seconds = None
        self.entry = None
        self.rec = None
        if not fn.exists():
            self.failure = "cache_missing"
            return
        with gzip.open(fn, "rt") as f:
            rec = json.load(f)
        self.rec = rec
        self.entry = rec.get("entry_function")
        self.stats = rec.get("stats") or {}
        self.extract_seconds = rec.get("extract_seconds")
        self.failure = rec.get("failure_kind")
        sb = rec.get("sandbox")
        if not rec.get("ok") or not sb or not sb.get("traces"):
            return
        self.ok = True
        self.inputs = []
        for t in sb["traces"]:
            self.inputs.append(self._clean(t))
        self._src = None

    def _clean(self, t):
        ev = t["events"]
        wl = None
        if ev and ev[0][0] == "c" and ev[0][1] == "<lambda>" and isinstance(ev[0][3], dict) and ("entry_fn" in ev[0][3] or "args" in ev[0][3]):
            wl = ev[0][2]
        out = []
        for e in ev:
            if wl is not None and e[1] == "<lambda>" and e[2] == wl:
                continue
            snap = e[3]
            if isinstance(snap, dict):
                snap = {k: scrub(v) for k, v in snap.items()}
            out.append((e[0], e[1], e[2], snap))
        return {"events": out, "ret": t["ret"], "ret_type": t["ret_type"], "exc": t["exc"], "stdout": t["stdout"], "cov": t["cov"], "trunc": t["trunc"],
                "input": t["input"]}

    def source_lines(self):
        if self._src is None:
            try:
                self._src = (REPO / self.path).read_text().splitlines()
            except OSError:
                self._src = []
        return self._src


# ------------------------------------------------------------------ canonicalisation
def canon_fn(events, entry, mode):
    """Function-name mapping for one trace: raw | entry (entry->ENTRY) | full (first-appearance order, SBG-style anonymisation)."""
    if mode == "raw":
        return {}
    if mode == "entry":
        return {entry: "ENTRY"}
    m = {}
    for e in events:
        if e[1] not in m:
            m[e[1]] = f"f{len(m)}"
    return m


def tokens(events, entry, kind, canon):
    m = canon_fn(events, entry, canon)
    g = m.get
    if kind == "call":
        return [g(e[1], e[1]) for e in events if e[0] == "c"]
    return [e[0] + g(e[1], e[1]) for e in events if e[0] in "cre"]


# ------------------------------------------------------------------ distance primitives
def lcs_len(a, b):
    """Bit-parallel LCS length (Hyyro 2004) with Python big ints."""
    if not a or not b:
        return 0
    M = {}
    for i, x in enumerate(a):
        M[x] = M.get(x, 0) | (1 << i)
    n = len(a)
    full = (1 << n) - 1
    V = full
    for y in b:
        m = M.get(y)
        if m:
            u = V & m
            V = ((V + u) | (V - u)) & full
    return n - bin(V).count("1")


def lcs_dist(a, b):
    """Normalised indel (LCS) distance = 1 - 2 LCS/(|a|+|b|)."""
    if not a and not b:
        return 0.0
    return 1.0 - 2.0 * lcs_len(a, b) / (len(a) + len(b))


def lev(a, b):
    """Levenshtein distance, Myers/Hyyro bit-parallel."""
    a = list(a)
    b = list(b)
    p = 0
    n = min(len(a), len(b))
    while p < n and a[p] == b[p]:
        p += 1
    a, b = a[p:], b[p:]
    s = 0
    n = min(len(a), len(b))
    while s < n and a[-1 - s] == b[-1 - s]:
        s += 1
    if s:
        a, b = a[:len(a) - s], b[:len(b) - s]
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) > len(b):
        a, b = b, a
    m = len(a)
    full = (1 << m) - 1
    Peq = {}
    for i, x in enumerate(a):
        Peq[x] = Peq.get(x, 0) | (1 << i)
    Pv, Mv, score, top = full, 0, m, 1 << (m - 1)
    for y in b:
        Eq = Peq.get(y, 0)
        Xv = Eq | Mv
        Xh = ((((Eq & Pv) + Pv) ^ Pv) | Eq) & full
        Ph = (Mv | ~(Xh | Pv)) & full
        Mh = Pv & Xh
        if Ph & top:
            score += 1
        elif Mh & top:
            score -= 1
        Ph = ((Ph << 1) | 1) & full
        Mh = (Mh << 1) & full
        Pv = (Mh | ~(Xv | Ph)) & full
        Mv = Ph & Xv
    return score


def lev_norm(a, b):
    n = max(len(a), len(b))
    return lev(a, b) / n if n else 0.0


def kgrams(seq, k):
    if not seq:
        return set()
    if len(seq) < k:
        return {tuple(seq)}
    return {tuple(seq[i:i + k]) for i in range(len(seq) - k + 1)}


def jaccard_dist(sa, sb):
    if not sa and not sb:
        return 0.0
    return 1.0 - len(sa & sb) / len(sa | sb)


def wjaccard_dist(ca, cb):
    """1 - sum(min)/sum(max) over multisets (Counters)."""
    if not ca and not cb:
        return 0.0
    inter = union = 0
    for k in ca.keys() | cb.keys():
        x, y = ca.get(k, 0), cb.get(k, 0)
        inter += x if x < y else y
        union += x if x > y else y
    return 1.0 - inter / union if union else 0.0


def cosine_dist(va, vb):
    if not va or not vb:
        return 0.0 if (not va and not vb) else 1.0
    num = sum(v * vb.get(k, 0.0) for k, v in va.items())
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return max(0.0, 1.0 - num / (na * nb)) if na and nb else 1.0


def first_div(a, b):
    n = max(len(a), len(b))
    if n == 0:
        return 0.0
    i = 0
    m = min(len(a), len(b))
    while i < m and a[i] == b[i]:
        i += 1
    return 0.0 if (i == len(a) == len(b)) else 1.0 - i / n


def agg(vals, how):
    if not vals:
        return 0.0
    return max(vals) if how == "max" else sum(vals) / len(vals)


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]

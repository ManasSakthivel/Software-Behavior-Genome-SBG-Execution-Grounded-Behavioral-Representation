"""birthmark_kgram -- dynamic k-gram call-sequence birthmark distance (Myles & Collberg 2005; Wang et al. 2009 style) on the cached traces
(class A for the algorithm, B for the task; ADAPTED; output-free; sources read at ABSTRACT level only -- the papers are paywalled).

Birthmark of a program file = SET of k-grams of the ordered *call* sequence (function-call events of the program's own frames, driver wrapper removed),
pooled over the 11 protocol inputs (dynamic birthmark: set of k-grams observed during execution).  Function names are anonymised by order of first
appearance in the pooled sequence (rename-robust; ``anon=False`` -> naive raw names).
Distances (score, larger = more different, i.e. more likely CHANGED):
  jaccard      : 1 - |A cap B| / |A cup B|
  containment  : 1 - |A cap B| / max(|A|,|B|)   (Myles & Collberg 'containment' made symmetric)
``score_pair`` = k=4 (Myles & Collberg's best-performing k), Jaccard, pooled, anonymised.
``score_pair_multi``: k in {2,3,4} x {jaccard, containment} x {pooled, per-input mean} x {anon, raw}   (24 values) -- selection among them on v9c_dev only (A4C).
Known degeneracy: programs whose trace has a single function and no recursion produce identical k-gram sets (score 0 for every pair): the birthmark is blind to
intra-function changes -- reported, not hidden.  Expected to behave like the call-bigram part of SBG-V3.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

KS = (2, 3, 4)


def _call_seqs(ft):
    return [[e[1] for e in inp["events"] if e[0] == "c"] for inp in ft.inputs]


def _anon(seqs):
    m = L.anon_map(x for s in seqs for x in s)
    return [[m[x] for x in s] for s in seqs]


def _birthmark(seqs, k):
    out = set()
    for s in seqs:
        out |= L.kgrams(s, k)
    return out


def _dists(base, var, ctx, k, anon):
    fa, fb = ctx.trace(base), ctx.trace(var)
    if not (fa.ok and fb.ok):
        return None
    sa, sb = _call_seqs(fa), _call_seqs(fb)
    n = min(len(sa), len(sb))
    sa, sb = sa[:n], sb[:n]
    if anon:
        sa, sb = _anon(sa), _anon(sb)
    A, B = _birthmark(sa, k), _birthmark(sb, k)
    per_j = [L.jaccard_dist(L.kgrams(x, k), L.kgrams(y, k)) for x, y in zip(sa, sb)]
    per_c = [L.containment_dist(L.kgrams(x, k), L.kgrams(y, k)) for x, y in zip(sa, sb)]
    return {"jaccard": L.jaccard_dist(A, B), "containment": L.containment_dist(A, B), "jaccard_perinput": L.mean(per_j), "containment_perinput": L.mean(per_c)}


def score_pair(base_record, variant_record, ctx):
    d = _dists(base_record, variant_record, ctx, 4, True)
    return L.NAN if d is None else d["jaccard"]


def score_pair_multi(base_record, variant_record, ctx):
    out = {}
    for anon in (True, False):
        for k in KS:
            d = _dists(base_record, variant_record, ctx, k, anon)
            for name in ("jaccard", "containment", "jaccard_perinput", "containment_perinput"):
                out[f"birthmark_k{k}_{name}_{'anon' if anon else 'raw'}"] = L.NAN if d is None else d[name]
    return out

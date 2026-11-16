"""B05a — trace-sequence similarity baselines (class B, ADAPTED; output-free).

Per input, the sequence of (event type, function) tokens of base vs variant is compared with: normalised indel/LCS distance (Levenshtein-family),
k-gram Jaccard (dynamic-birthmark style, Myles & Collberg / Wang et al.), TF-IDF cosine over 1-3-grams, first-divergence position.
Aggregation over the 11 inputs: mean / max.  Function-name canonicalisation: raw (naive) | entry (entry fn -> ENTRY) | full (SBG-style first-call order).
"""
from __future__ import annotations

import collections
import math

from bl_common import tokens, lcs_dist, kgrams, jaccard_dist, cosine_dist, first_div, agg

KINDS = ("call", "cre")
CANONS = ("raw", "entry", "full")
MEASURES = ("lcs", "kgram2", "kgram3", "kgram4", "tfidf13", "firstdiv")
AGGS = ("mean", "max")


def config_names():
    return [f"traceseq|{k}|{c}|{m}|{a}" for k in KINDS for c in CANONS for m in MEASURES for a in AGGS]


def _grams13(seq):
    out = collections.Counter()
    for n in (1, 2, 3):
        for i in range(max(0, len(seq) - n + 1)):
            out[tuple(seq[i:i + n])] += 1
    return out


def fit_idf(file_traces):
    """IDF tables per (kind, canon) from train file traces (document = file, pooled over inputs). Unsupervised, train only."""
    res = {}
    for kind in KINDS:
        for canon in CANONS:
            df = collections.Counter()
            N = 0
            for ft in file_traces:
                if not ft.ok:
                    continue
                N += 1
                s = set()
                for inp in ft.inputs:
                    s.update(_grams13(tokens(inp["events"], ft.entry, kind, canon)).keys())
                df.update(s)
            res[(kind, canon)] = ({g: math.log((N + 1) / (c + 1)) + 1.0 for g, c in df.items()}, N)
    return res


def pair_features(fa, fb, idf):
    out = {}
    n = min(len(fa.inputs), len(fb.inputs))
    for kind in KINDS:
        for canon in CANONS:
            per = collections.defaultdict(list)
            tab, N = idf[(kind, canon)]
            dflt = math.log(N + 1) + 1.0
            for i in range(n):
                ta = tokens(fa.inputs[i]["events"], fa.entry, kind, canon)
                tb = tokens(fb.inputs[i]["events"], fb.entry, kind, canon)
                per["lcs"].append(lcs_dist(ta, tb))
                for k in (2, 3, 4):
                    per[f"kgram{k}"].append(jaccard_dist(kgrams(ta, k), kgrams(tb, k)))
                va = {g: c * tab.get(g, dflt) for g, c in _grams13(ta).items()}
                vb = {g: c * tab.get(g, dflt) for g, c in _grams13(tb).items()}
                per["tfidf13"].append(cosine_dist(va, vb))
                per["firstdiv"].append(first_div(ta, tb))
            for m, vals in per.items():
                for a in AGGS:
                    out[f"traceseq|{kind}|{canon}|{m}|{a}"] = agg(vals, a)
    return out

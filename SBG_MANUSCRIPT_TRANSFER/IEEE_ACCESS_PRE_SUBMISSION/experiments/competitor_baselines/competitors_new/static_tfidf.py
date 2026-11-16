"""static_tfidf -- identifier-normalised token n-gram TF-IDF cosine distance (class A, source-only, output-free; ADAPTED, own implementation).

Tokens   : Python ``tokenize`` stream without comments/whitespace; strings -> STR; program identifiers -> v<k> (alpha, first appearance) in the default config.
Features : token 1-,2-,3-gram counts, weight = tf * idf.
IDF      : log((N+1)/(df+1)) + 1 fitted ONLY on the unique source files (bases and variants) of the V9c-train population (``ctx.idf_tokens()``;
           unsupervised, no labels used); unseen n-grams get the maximal idf.
Score    : cosine distance between the base and the variant vector (0 identical).
Configs  : ``tfidf_alpha_123`` (default), ``tfidf_alpha_2``, ``tfidf_alpha_3``, ``tfidf_id_123`` (every identifier -> ID), ``tfidf_alpha_123_noidf`` (tf only).
Note     : the IDF table of the default (alpha, n=1..3) is shared across all n (keys carry their own n).
"""
from __future__ import annotations

import math
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

_idf_cache = {}


def _idf(ctx, mode):
    if mode == "alpha":
        return ctx.idf_tokens()
    key = id(ctx), mode
    if key not in _idf_cache:
        docs = sorted({r[k] for r in ctx.population("v9c_train") if r.get("in_primary_population") for k in ("base_path", "variant_path")})
        _idf_cache[key] = L.fit_idf_tokens([ctx.source({"path": d}) for d in docs], mode=mode)
    return _idf_cache[key]


def _vec(src, mode, ns, idf, N, use_idf=True):
    seq = L.token_seq(src, mode)
    tf = L.ngram_counter(seq, ns)
    dflt = math.log(N + 1) + 1.0
    return {g: c * (idf.get(g, dflt) if use_idf else 1.0) for g, c in tf.items()}


def _dist(base, var, ctx, mode, ns, use_idf=True):
    sa, sb = ctx.source(base), ctx.source(var)
    if sa is None or sb is None:
        return L.NAN
    idf, N = _idf(ctx, mode) if use_idf else ({}, 0)
    va, vb = _vec(sa, mode, ns, idf, N, use_idf), _vec(sb, mode, ns, idf, N, use_idf)
    if not va and not vb:
        return L.NAN
    return L.cosine_dist(va, vb)


def score_pair(base_record, variant_record, ctx):
    return _dist(base_record, variant_record, ctx, "alpha", (1, 2, 3))


def score_pair_multi(base_record, variant_record, ctx):
    return {"tfidf_alpha_123": _dist(base_record, variant_record, ctx, "alpha", (1, 2, 3)),
            "tfidf_alpha_2": _dist(base_record, variant_record, ctx, "alpha", (2,)),
            "tfidf_alpha_3": _dist(base_record, variant_record, ctx, "alpha", (3,)),
            "tfidf_id_123": _dist(base_record, variant_record, ctx, "id", (1, 2, 3)),
            "tfidf_alpha_123_noidf": _dist(base_record, variant_record, ctx, "alpha", (1, 2, 3), use_idf=False)}

"""static_srclev -- normalised-source Levenshtein distance (class A, source-only, output-free; ADAPTED, own implementation).

Normalisation: parse -> drop docstrings -> alpha-rename program-defined identifiers (first appearance) -> ``ast.unparse`` (canonical formatting: comments, blank
lines, quoting, spacing and redundant parentheses vanish).  Distance: character-level Levenshtein of the two normalised texts divided by the longer length.
``score_pair`` = alpha-renamed variant (rename-robust).  ``score_pair_multi``: ``srclev_alpha`` (default), ``srclev_unparse`` (no renaming),
``srclev_line_alpha`` (Levenshtein over normalised source *lines* / max #lines), ``srclev_abs_chars`` (un-normalised edit count in characters).
"""
from __future__ import annotations

import ast
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402


def _norm(rec, ctx, rename):
    src = ctx.source(rec)
    if src is None:
        return None
    try:
        return ast.unparse(L.parse_normalised(src, rename=rename))
    except (SyntaxError, RecursionError):
        return None


def score_pair(base_record, variant_record, ctx):
    a, b = _norm(base_record, ctx, True), _norm(variant_record, ctx, True)
    if a is None or b is None:
        return L.NAN
    return L.lev_norm(a, b)


def score_pair_multi(base_record, variant_record, ctx):
    a, b = _norm(base_record, ctx, True), _norm(variant_record, ctx, True)
    c, d = _norm(base_record, ctx, False), _norm(variant_record, ctx, False)
    if None in (a, b, c, d):
        return {k: L.NAN for k in ("srclev_alpha", "srclev_unparse", "srclev_line_alpha", "srclev_abs_chars")}
    return {"srclev_alpha": L.lev_norm(a, b), "srclev_unparse": L.lev_norm(c, d),
            "srclev_line_alpha": L.lev_norm(a.splitlines(), b.splitlines()), "srclev_abs_chars": float(L.lev(a, b))}

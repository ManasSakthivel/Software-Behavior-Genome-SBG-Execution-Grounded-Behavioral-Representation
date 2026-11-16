"""obs_points_outreading -- observation-point differencing, 'output-reading (privileged)' variant (DCI/DSpot- and Xie & Notkin value-spectrum-inspired;
class C->B, ADAPTED; NOT DCI/DSpot -- those are Java test-amplification tools).  SAME 11 label-defining inputs => reads the quantities that define the label
=> the score is a *same-input label-oracle ceiling* (sanity only, never a competitor).

Observation points per input = those of ``obs_points_outfree`` (raw call arguments, abstract return-time locals) PLUS:
  ("R", f, sorted RAW locals at the return event of every function)   -- value spectrum exit states (reveals returned/derived values and in-place argument mutation)
  ("E", f)                                                             -- frames left by an exception
  ("RET", ret repr, ret_type), ("EXC", exception string), ("OUT", stdout)   -- entry function's return value / exception / stdout
Score = mean over inputs of weighted-Jaccard distance.  ``score_pair_multi``: mean / max, and ``obs_reading_valuespectrum_mean`` (only R-points + A-points,
Xie & Notkin style entry/exit values, no ret/exc/stdout).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402
import obs_points_outfree as O  # noqa: E402


def _per_input(base, var, ctx, parts, reading):
    return O._score(base, var, ctx, parts, reading)


def _valuespectrum(base, var, ctx):
    """A + R points only (no abstract-S, no ret/exc/stdout, no E)."""
    import collections
    fa, fb = ctx.trace(base), ctx.trace(var)
    if not (fa.ok and fb.ok):
        return None

    def ms(inp):
        ev = inp["events"]
        m = L.anon_map(e[1] for e in ev)
        c = collections.Counter()
        for t, fn, ln, snap in ev:
            if t == "c":
                c[("A", m[fn], O._vals(snap, "raw"))] += 1
            elif t == "r":
                c[("R", m[fn], O._vals(snap, "raw"))] += 1
        return c
    return [L.wjaccard_dist(ms(a), ms(b)) for a, b in L.paired_inputs(fa, fb)]


def score_pair(base_record, variant_record, ctx):
    v = _per_input(base_record, variant_record, ctx, ("A", "S"), True)
    return L.NAN if not v else L.mean(v)


def score_pair_multi(base_record, variant_record, ctx):
    v = _per_input(base_record, variant_record, ctx, ("A", "S"), True)
    w = _valuespectrum(base_record, variant_record, ctx)
    return {"obs_reading_all_mean": L.NAN if not v else L.mean(v), "obs_reading_all_max": L.NAN if not v else max(v),
            "obs_reading_valuespectrum_mean": L.NAN if not w else L.mean(w)}

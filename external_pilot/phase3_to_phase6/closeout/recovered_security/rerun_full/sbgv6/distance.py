"""Pair record: block distances, evidence, status, confidence, raw V6 score. No labels, no trainable parameters."""
from __future__ import annotations
from collections import Counter
from sbgv6 import config as C, features as F

ACTIVATED, NOT_ACTIVATED, UNKNOWN = "ACTIVATED", "NOT_ACTIVATED", "UNKNOWN"


def _usable(tr):
    return (not tr.truncated) and len(tr.events) > 0


def side_evidence(obs):
    """Per-side evidence. Reason codes are explicit; absence of data is never zero distance."""
    if not obs.ok:
        return {"usable_frac": 0.0, "n": 0, "trunc_frac": 0.0, "exc_frac": 0.0, "nondet": False,
                "fail": obs.failure_kind or "unobserved"}
    r0 = obs.runs[0]
    n = len(r0)
    nd = False
    if len(obs.runs) > 1:
        sig = lambda run, src: ([tuple(s) for s in F.token_seqs(run, src)], [F._rv(t)[1] for t in run])  # noqa: E731
        nd = sig(r0, obs.source) != sig(obs.runs[1], obs.source)
    return {"usable_frac": sum(map(_usable, r0)) / n if n else 0.0, "n": n,
            "trunc_frac": sum(t.truncated for t in r0) / n if n else 0.0,
            "exc_frac": sum(t.exception is not None for t in r0) / n if n else 0.0,
            "nondet": nd, "fail": None}


def pair_record(a, b, regime_r2=True):
    ea, eb = side_evidence(a), side_evidence(b)
    rec = {"ev_base": ea, "ev_var": eb}
    reasons = [s + ":" + e["fail"] for s, e in (("base", ea), ("var", eb)) if e["fail"]]
    reasons += [s + ":low_usable" for s, e in (("base", ea), ("var", eb)) if not e["fail"] and e["usable_frac"] < C.U_MIN]
    reasons += [s + ":nondeterministic" for s, e in (("base", ea), ("var", eb)) if e["nondet"]]
    if reasons:
        rec.update(status=UNKNOWN, reasons=reasons, d_A=None, d_B=None, d_C=None, d_R=None,
                   delta_out=None, cfg_size=None, g=None, alpha=None, conf=0.0, d_v6=None)
        return rec
    r1, r2 = a.runs[0], b.runs[0]
    u1 = [t for t in r1 if _usable(t)]
    u2 = [t for t in r2 if _usable(t)]
    s1, s2 = F.token_seqs(u1, a.source), F.token_seqs(u2, b.source)
    p1 = Counter(t for s in s1 for t in s); p2 = Counter(t for s in s2 for t in s)
    d_A = F.d_invariant(F.invariants(u1, a.source), F.invariants(u2, b.source))
    d_B = F.jsd(p1, p2)
    w1, c1 = F.cfg_summary(u1, a.source); w2, c2 = F.cfg_summary(u2, b.source)
    d_C = F.jsd(w1, w2)
    cfg_size = [F.ratio(x, y) for x, y in zip(c1, c2)]
    lam1, lam2 = F.changed_lines(a.source, b.source)
    alpha = F.activation(r1, r2, lam1, lam2)
    g = F.gated_divergence(s1, s2) if len(u1) == len(r1) == len(u2) == len(r2) else None
    d_R, delta_out = F.return_state(r1, r2)
    u = ea["usable_frac"] * eb["usable_frac"]
    status = NOT_ACTIVATED if (alpha is None or alpha == 0.0) else ACTIVATED
    conf = u * (0.5 + 0.5 * min(1.0, (alpha or 0.0) / C.ALPHA0))
    r1_blocks = [x for x in (d_A, d_B, d_C) if x is not None]
    rec.update(status=status, reasons=[], d_A=d_A, d_B=d_B, d_C=d_C, d_R=d_R, delta_out=delta_out,
               cfg_size=cfg_size, g=g, alpha=alpha, conf=conf,
               d_v6=(sum(r1_blocks) / len(r1_blocks)) if r1_blocks else None)
    return rec

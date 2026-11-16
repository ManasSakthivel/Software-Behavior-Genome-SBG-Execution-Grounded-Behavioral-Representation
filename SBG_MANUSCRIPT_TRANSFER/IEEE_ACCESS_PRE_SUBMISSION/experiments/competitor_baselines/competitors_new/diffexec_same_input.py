"""diffexec_same_input -- same-input differential execution = 'SAME-INPUT LABEL-ORACLE CEILING' (sanity only; NEVER a competitor).

Differential-testing core shared by Kessel & Atkinson behaviour sampling, BERT / Evans & Savoia differential testing and the ChangeGuard (Groninger, Souza,
Pradel, FSE'25) comparator -- run on the 11 protocol inputs that DEFINE the CHANGED label (PROTOCOL section 2) => reproduces the label by construction on
V10 (oracle-validated) and approximately on V9c (static-observability-audited labels).  Class B (ADAPTED), 'output-reading (privileged)'.

Per input the observable behaviour is  (return value repr, exception string, stdout, post-call values of the entry parameters [positional, names dropped; =
in-place argument mutation]).   hard_i = 1 if any component differs.
  score_pair = frac_hard + 0.001 * soft_mean        (the soft term, in [0,1], only breaks ties: frac steps are >= 1/11)
  soft_i     = max( exc_d, nlev(ret), nlev(stdout), nlev(post-args) )   with exc_d = 0 equal / 0.5 same exception type, different message / 1 otherwise
Multi: ``frac_hard`` ; ``any_hard`` (ChangeGuard decision rule: any difference => semantics-changing) ; ``soft_mean`` ; ``changeguard_cmp`` (frac of inputs where the
comparator (1)-(4) of ChangeGuard differs: ret/args, stdout, intentional-exception type+message [unintended builtin exceptions of the same type are ignored],
ordered log of calls to functions NOT defined in the module -- empty for essentially all programs here because the cache only holds the program's own frames).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

UNINTENDED = ("TypeError", "AttributeError", "NameError", "UnboundLocalError", "IndexError", "KeyError", "ValueError", "ZeroDivisionError",
              "RecursionError", "OverflowError", "StopIteration")


def entry_post_args(inp, entry):
    """tuple of post-call values of the entry function's parameters (positional order of its call snapshot); None if the entry did not return."""
    depth, names, out = 0, None, None
    for t, fn, ln, snap in inp["events"]:
        if fn != entry:
            continue
        if t == "c":
            if depth == 0 and names is None and isinstance(snap, dict):
                names = list(snap)
            depth += 1
        elif t in "re":
            depth -= 1
            if depth == 0 and t == "r" and names is not None and isinstance(snap, dict):
                out = tuple(snap.get(n) for n in names)
    return out


def _exc_type(e):
    return e.split(":", 1)[0].strip() if e else None


def behaviour(inp, entry):
    return (inp.get("ret"), inp.get("exc"), inp.get("stdout"), entry_post_args(inp, entry))


def per_input(a, b):
    """returns (hard, soft) for two behaviour tuples."""
    (ra, ea, oa, pa), (rb, eb, ob, pb) = a, b
    if ea == eb:
        exc_d = 0.0
    elif ea and eb and _exc_type(ea) == _exc_type(eb):
        exc_d = 0.5
    else:
        exc_d = 1.0
    ret_d = L.lev_str_norm(ra, rb) if (ea is None and eb is None) else (1.0 if (ea is None) != (eb is None) else 0.0)
    out_d = L.lev_str_norm(oa, ob)
    arg_d = L.lev_str_norm(repr(pa), repr(pb)) if pa != pb else 0.0
    hard = int(ea != eb or ra != rb or oa != ob or pa != pb)
    return hard, max(exc_d, ret_d, out_d, arg_d)


def changeguard_diff(a, b, ext_a, ext_b):
    (ra, ea, oa, pa), (rb, eb, ob, pb) = a, b
    if ea or eb:
        ta, tb = _exc_type(ea), _exc_type(eb)
        if ta != tb:
            return 1
        if ta not in UNINTENDED and ea != eb:
            return 1
        return int(oa != ob or ext_a != ext_b)       # same-type unintended exception on both: only stdout / external-call log are compared
    return int(ra != rb or pa != pb or oa != ob or ext_a != ext_b)


def _ext_calls(inp, defined):
    return [e[1] for e in inp["events"] if e[0] == "c" and e[1] not in defined and not e[1].startswith("<")]


def _compute(base, var, ctx):
    fa, fb = ctx.trace(base), ctx.trace(var)
    if not (fa.ok and fb.ok):
        return None
    sa, sb = ctx.source(base), ctx.source(var)
    da, db = (L.defined_functions(sa) if sa else set()), (L.defined_functions(sb) if sb else set())
    hard, soft, cg = [], [], []
    for ia, ib in L.paired_inputs(fa, fb):
        ba, bb = behaviour(ia, fa.entry), behaviour(ib, fb.entry)
        h, s = per_input(ba, bb)
        hard.append(h)
        soft.append(s)
        cg.append(changeguard_diff(ba, bb, _ext_calls(ia, da), _ext_calls(ib, db)))
    return hard, soft, cg


def score_pair(base_record, variant_record, ctx):
    r = _compute(base_record, variant_record, ctx)
    if r is None or not r[0]:
        return L.NAN
    return L.mean(r[0]) + 0.001 * L.mean(r[1])


def score_pair_multi(base_record, variant_record, ctx):
    r = _compute(base_record, variant_record, ctx)
    if r is None or not r[0]:
        return {k: L.NAN for k in ("frac_hard", "any_hard", "soft_mean", "changeguard_cmp", "changeguard_any")}
    h, s, c = r
    return {"frac_hard": L.mean(h), "any_hard": float(any(h)), "soft_mean": L.mean(s), "changeguard_cmp": L.mean(c), "changeguard_any": float(any(c))}

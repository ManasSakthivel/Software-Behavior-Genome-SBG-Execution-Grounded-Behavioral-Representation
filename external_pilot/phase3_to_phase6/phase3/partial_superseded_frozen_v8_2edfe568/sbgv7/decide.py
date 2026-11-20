from __future__ import annotations
"""Pure verdict + sufficiency logic (spec 2, 6). Precedence: DIVERGENT_OBSERVABLE > INSUFFICIENT(primary; secondary) >
NO_DIVERGENCE_OBSERVED(S1|S2). A field that is None means the record is MISSING, and a missing record counts as a blocker.
Never emits an equivalence verdict; S3 is not implemented (max level S2)."""
from dataclasses import dataclass, field

OUTCOMES = ("CONFIRMED_DIFF", "UNCONFIRMED_DIFF", "ENV_SENSITIVE_DIFF", "SAME", "QUARANTINED", "LIMIT_ASYMMETRIC", "NO_RUN")
# (rank, code) per blocking condition B1..B9
RANK = {"import_error": 1, "alignment_failed": 2, "unsupported_signature": 2, "ambiguous_entry": 2, "unmodelled_change": 2,
        "sandbox_failure": 3, "unsafe_program": 3, "flaky_witness": 4, "env_sensitive": 4, "nondeterministic": 5,
        "resource_limit": 6, "capture_truncated": 7, "blind_spot_dominant": 7, "no_inputs": 8, "unobservable_outcome": 8,
        "tool_error": 8, "changed_region_not_activated": 9, "budget_exhausted_s0": 9}


@dataclass
class InputEv:
    input_id: str
    outcome: str | None = None
    witness_id: str | None = None
    degenerate: bool | None = None   # SAME with nothing observable on any channel
    lossy: bool | None = None        # equal only on a lossy canonical form (blocks S2)
    truncated: bool | None = None
    sandbox_ok: bool | None = None
    run_ids: tuple = ()
    reason: str | None = None        # NO_RUN sub-reason; "invalid_input" = binding failed on BOTH sides (not a valid SAME, excluded from X_eff)


@dataclass
class Evidence:
    inputs: list | None = None
    blockers: list = field(default_factory=list)      # [(code, detail)] found before/outside input execution (B1,B2,B8)
    changed_units: frozenset | None = None            # {(side, line)}
    hit_units: frozenset | None = None                # subset hit by deterministic-confirmed SAME inputs
    branch_cov: dict | None = None                    # {"base": float, "variant": float}; vacuous (no branches) = 1.0
    budget_exhausted: bool = False
    tampered: bool | None = None
    s2_floor: float = 0.80


def _blockers(ev):
    b = list(ev.blockers)
    if (ev.inputs is None and not ev.blockers) or ev.changed_units is None or ev.hit_units is None or ev.tampered is None:
        b.append(("tool_error", "missing evidence record"))
    if ev.tampered:
        b.append(("unsafe_program", "trace tamper flag set"))
    for i in ev.inputs or []:
        if None in (i.outcome, i.truncated, i.sandbox_ok) or i.outcome not in OUTCOMES:
            b.append(("tool_error", f"input {i.input_id}: incomplete record")); continue
        if not i.sandbox_ok: b.append(("sandbox_failure", i.input_id))
        if i.truncated: b.append(("capture_truncated", i.input_id))
        code = {"CONFIRMED_DIFF": "tool_error", "UNCONFIRMED_DIFF": "flaky_witness", "ENV_SENSITIVE_DIFF": "env_sensitive", "QUARANTINED": "nondeterministic",
                "LIMIT_ASYMMETRIC": "resource_limit", "NO_RUN": "resource_limit" if i.reason in (None, "both_limit") else None}.get(i.outcome)  # MB-10; None reason (legacy) stays conservative
        if code: b.append((code, i.input_id))
    same = [i for i in ev.inputs or [] if i.outcome == "SAME" and i.sandbox_ok and not i.truncated]
    if ev.inputs is not None and not same and not ev.blockers:
        b.append(("no_inputs", "no deterministic-confirmed SAME input"))
    elif same and all(i.degenerate is not False or i.lossy is not False for i in same):
        # equality established only on a degenerate or lossy canonical form is not evidence of no divergence (D-05/D-01 amendment A-L1)
        b.append(("unobservable_outcome", "every SAME input is degenerate or lossy-canonicalised on all channels"))
    if ev.changed_units is not None and ev.hit_units is not None and (ev.changed_units - ev.hit_units):
        b.append(("budget_exhausted_s0" if ev.budget_exhausted else "changed_region_not_activated",
                  f"{len(ev.changed_units - ev.hit_units)} changed unit(s) unhit"))
    return [x if x[0] in RANK else ("tool_error", f"unknown reason code {x[0]!r}: {x[1]}") for x in b]  # MB-04: never a KeyError in decide


def sufficiency(ev, blockers):
    """Level S0 iff any blocker; S2 iff S1 and the S2 floors hold; else S1. Returns (level, floor dict)."""
    same = [i for i in ev.inputs or [] if i.outcome == "SAME"]
    f = {"s1_no_blockers": not blockers,
         "s2_branch_cov": ev.branch_cov is not None and all(ev.branch_cov.get(s) is not None and ev.branch_cov[s] >= ev.s2_floor
                                                           for s in ("base", "variant")),
         "s2_no_lossy": bool(same) and all(i.lossy is False for i in same),
         "s2_all_channels_instrumented": True}  # harness instruments all declared channels; see docs
    if not f["s1_no_blockers"]: return "S0", f
    return ("S2" if f["s2_branch_cov"] and f["s2_no_lossy"] and f["s2_all_channels_instrumented"] else "S1"), f


def decide(ev):
    """-> (value, level, primary, secondary, witness_id, blockers, floors)"""
    wit = [i.witness_id for i in ev.inputs or [] if i.outcome == "CONFIRMED_DIFF" and i.witness_id]
    if wit:
        return "DIVERGENT_OBSERVABLE", None, None, [], wit[0], [], {}
    b = _blockers(ev)
    level, floors = sufficiency(ev, b)
    if b:
        codes = sorted({c for c, _ in b}, key=lambda c: (RANK[c], c))
        return "INSUFFICIENT", None, codes[0], codes[1:], None, b, floors
    return "NO_DIVERGENCE_OBSERVED", level, None, [], None, [], floors

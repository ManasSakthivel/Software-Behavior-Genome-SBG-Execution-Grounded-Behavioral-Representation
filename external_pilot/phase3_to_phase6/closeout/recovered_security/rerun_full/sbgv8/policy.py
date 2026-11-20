"""Versioned eligibility policies: which non-witness pairs may receive a calibrated NDO at all. A policy is IMMUTABLE once named, so every
past result stays reproducible by name.
  v8.0  (historical default) blockers changed_region_not_activated / budget_exhausted_s0 are SOFT: pair stays eligible, activation is a graded feature.
  v8.0s (legacy STRICT_BLOCKERS=True sensitivity) every recorded blocker is hard.
  v8.1  (declared-semantics primary) eligible iff the V7-B-style decision on the record is NO_DIVERGENCE_OBSERVED, i.e. NO blocker of any kind,
        including (re)derived ones: changed units never executed by a clean SAME input make the pair INSUFFICIENT in V7-B (sbgv7/decide.py
        _blockers: changed_units - hit_units -> changed_region_not_activated / budget_exhausted_s0). Calibration can then only ABSTAIN further
        from V7-B's NDO set; it can never issue NDO where V7-B says INSUFFICIENT. (Witness exclusion is applied by calibrate.is_eligible.)
Reads only evidence fields (never rec.y)."""
from __future__ import annotations
import contextlib

SOFT_V80 = frozenset({"changed_region_not_activated", "budget_exhausted_s0"})
NDO = "NO_DIVERGENCE_OBSERVED"
DEFAULT = "v8.0"
_current = DEFAULT


def _code(b): return b[0] if isinstance(b, (list, tuple)) else str(b)


def _blockers_ok(rec, soft): return all(_code(b) in soft for b in rec.blockers)


def _v81(rec):
    if rec.blockers: return False
    from . import profile   # lazy; same function calibrate.v7b_verdict uses
    return profile.v7b_style_decision(rec)[0] == NDO


POLICIES = {
    "v8.0": lambda rec: _blockers_ok(rec, SOFT_V80),
    "v8.0s": lambda rec: _blockers_ok(rec, frozenset()),
    "v8.1": _v81,
}


def current(): return _current


def set_policy(name):
    global _current
    if name not in POLICIES: raise KeyError(f"unknown policy {name!r}; have {sorted(POLICIES)}")
    _current = name


@contextlib.contextmanager
def use(name):
    prev = _current; set_policy(name)
    try: yield
    finally: set_policy(prev)


def blockers_ok(rec, name=None): return POLICIES[name or _current](rec)

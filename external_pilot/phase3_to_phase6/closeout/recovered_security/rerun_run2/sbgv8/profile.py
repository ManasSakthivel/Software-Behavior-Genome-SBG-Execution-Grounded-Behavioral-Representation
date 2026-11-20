"""Evidence profile phi(E) and a V7-B-style decision on an EvidenceRecord. Reads only evidence fields: NEVER rec.y or rec.meta.
Conventions (document-level, see reports/v8/V8_ERS_SPECIFICATION.md):
  U      = inputs that are not duplicate copies (duplicate_of is None); all per-input fractions use U so duplication is invariant.
  clean  = outcome SAME and deterministic and not lossy (V7-B finalize: only such inputs activate changed units / cover branches).
  unit   = (side, line) for each changed line."""
from __future__ import annotations
from sbgv7.decide import Evidence, InputEv, decide
from sbgv8.schema import FEATURES

SIDES = ("base", "variant")


def _units(rec):
    return {(s, l) for s in SIDES for l in rec.changed_units.get(s, [])}


def _clean(i):
    return i.outcome == "SAME" and i.deterministic and not i.lossy


def _hit(i, units):
    return {(s, l) for s in SIDES for l in i.hits.get(s, [])} & units


def _fp(i):
    return i.obs_fingerprint or "id:" + i.input_id  # no fingerprint = no evidence of equality with any other input


def _branch_cov(rec, clean):
    """V7-B: got/(2*static) with got = sum min(2,#directions) over static branch keys. APPROXIMATION: the record carries only the static
    COUNT, not the static key set, so every recorded key is counted (capped at 2*static) instead of only the static ones."""
    cov = {}
    for s in SIDES:
        static = rec.static_branches.get(s, 0)
        seen = {}
        for i in clean:
            for k, v in i.branches.get(s, {}).items():
                seen.setdefault(k, set()).update(v)
        got = sum(min(2, len(v)) for v in seen.values())
        cov[s] = 1.0 if not static else min(1.0, got / (2 * static))
    return cov


def build_profile(rec):
    units = _units(rec)
    U = [i for i in rec.inputs if not i.duplicate_of]
    clean = [i for i in U if _clean(i)]
    hit_all = set().union(*[_hit(i, units) for i in clean]) if clean else set()
    per_unit = {u: {_fp(i) for i in clean if u in _hit(i, units)} for u in units}
    mus = [len(v) for v in per_unit.values()]
    # PROXY for observable influence (NOT dynamic slicing): unit reached by a clean SAME input that is non-degenerate and captured >=1 channel.
    obs = set().union(*[_hit(i, units) for i in clean if not i.degenerate and i.channels_present]) if clean else set()
    elig = [i for i in clean if i.provenance != "label_derived" and i.provenance_ok]
    n = len(U)
    declared = set(rec.declared_channels)
    chan = [len(declared & set(i.channels_present)) / len(declared) if declared else 1.0 for i in U]
    p = {
        "act_frac": len(hit_all) / len(units) if units else 1.0,
        "branch_cov_min": min(_branch_cov(rec, clean).values()),
        "mu_min": float(min(mus)) if mus else 0.0,
        "mu_mean": sum(mus) / len(mus) if mus else 0.0,
        "n_same": float(len(clean)),
        "n_rep": float(sum(i.n_repeat_runs for i in clean)),
        "obs_react": len(obs) / len(units) if units else 1.0,
        "n_eff": float(len({_fp(i) for i in clean})),
        "n_eff_prov": float(len({(_fp(i), i.provenance) for i in elig})),
        "repro_frac": sum(i.deterministic for i in U) / n if n else 0.0,
        "lossy_frac": sum(i.lossy or i.degenerate for i in U) / n if n else 0.0,
        "chan_complete": sum(chan) / n if n else 0.0,
        "prov_ok": float(all(i.provenance_ok and i.provenance != "label_derived" for i in rec.inputs)),
        "integrity_ok": float(bool(rec.integrity_ok)),
        "env_ok": float(bool(rec.env_consistent)),
    }
    assert list(p) == FEATURES
    return p


def v7b_style_decision(rec):
    """Replicates sbgv7.decide.decide on a record -> (verdict, level). Approximations (data not in record): truncated/sandbox_ok are assumed
    clean (V7-B encodes them as rec.blockers codes); SAME with deterministic=False is treated as QUARANTINED; env_consistent=False adds an
    env_sensitive blocker; integrity_ok=False sets the tamper flag; label_derived provenance is NOT a V7-B concept and is ignored here."""
    units = _units(rec)
    evs = []
    for i in rec.inputs:
        if i.duplicate_of:
            continue
        out = "QUARANTINED" if i.outcome == "SAME" and not i.deterministic else i.outcome
        evs.append(InputEv(i.input_id, out, i.input_id if out == "CONFIRMED_DIFF" else None, i.degenerate, i.lossy, False, True))
    clean = [i for i in rec.inputs if not i.duplicate_of and _clean(i)]
    hit = frozenset().union(*[_hit(i, units) for i in clean]) if clean else frozenset()
    bl = [tuple(b) if isinstance(b, (list, tuple)) else (str(b), "record") for b in rec.blockers]
    if not rec.env_consistent:
        bl.append(("env_sensitive", "env_inconsistent"))
    ev = Evidence(inputs=evs, blockers=bl, changed_units=frozenset(units), hit_units=hit, branch_cov=_branch_cov(rec, clean),
                  tampered=not rec.integrity_ok, s2_floor=rec.config.get("s2_branch_floor", 0.80))
    v, level = decide(ev)[:2]
    return v, level

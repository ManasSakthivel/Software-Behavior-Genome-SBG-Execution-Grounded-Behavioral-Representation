"""V8 collection (the CONTROLLER role, see sbgv8.procsep): run the V7-B engine UNMODIFIED (sbgv7.runner.compare_versions) and capture, from the PARENT process only, the
`parts` that runner.finalize receives (per-input outcome/lossy/degenerate + hit/branch sets) into a sidecar v8_parts.json bound by sha256
to the evidence log head. The monkeypatch is in-process, wraps finalize (returns its result untouched) and is always restored.
The evaluated program never runs in this process (sbgv7.isolation spawns a fresh child per run), so it cannot see the patch."""
import hashlib, json, os, sbgv7.runner as RUN

from . import evidence_schema as ES, procsep

SIDECAR = "v8_parts.json"
SIDECAR_SCHEMA = "v8.parts.1"


def _jb(b):
    return {s: {k: sorted(v) for k, v in b[s].items()} for s in b}


def run_capture(base, variant, entry, inputs, cfg, out_dir, anchor_key=None):
    """compare_versions(...) + sidecar + parent-owned independent stdout/stderr capture (v8_capture.json) + optional MAC anchor (v8_anchor.json; key =
    anchor_key or $SBGV8_ANCHOR_KEY, never given to the child). Returns the engine's verdict dict; if the independent record is not trustworthy the
    returned 'verdict' is INSUFFICIENT (the engine's own value stays in 'v7b_verdict') and 'v8_untrusted' lists the reasons."""
    key = ES.load_key(anchor_key)
    cap, orig = {}, RUN.finalize

    def spy(cfg_, src, st, reg, soft, parts, stop, tampered, below_min=None):
        units = {s: set(reg["units"][s]) for s in reg["units"]}
        cap["parts"] = [{"input_id": ev.input_id, "outcome": ev.outcome, "lossy": bool(ev.lossy), "degenerate": bool(ev.degenerate),
                         "hits": {s: sorted(h[s]) for s in h}, "branches": _jb(b)} for ev, h, b in parts]
        cap["static_branches"] = {s: sorted(RUN._static_branches(src[s].decode(), units[s])) if not st else [] for s in units}
        cap["units"] = {s: sorted(units[s]) for s in units}
        return orig(cfg_, src, st, reg, soft, parts, stop, tampered, below_min)
    RUN.finalize = spy
    try:
        with procsep.Supervisor(base, variant) as sup:
            out = RUN.compare_versions(base, variant, entry, inputs, cfg, out_dir)
    finally:
        RUN.finalize = orig
    ev = os.path.join(out_dir, "evidence.jsonl")
    side = {"schema": SIDECAR_SCHEMA, "log_head": out["log_head"], "evidence_sha256": hashlib.sha256(open(ev, "rb").read()).hexdigest(), **cap}
    json.dump(side, open(os.path.join(out_dir, SIDECAR), "w"), sort_keys=True)
    json.dump(sup.document(out_dir, cfg), open(os.path.join(out_dir, ES.FILES["capture"]), "w"), sort_keys=True)
    if key: ES.write_anchor(out_dir, key, sup.session)
    dec = procsep.decide(out["verdict"], ES.validate_dir(out_dir, key))
    if dec["untrusted"]: out = {**out, "verdict": dec["verdict"], "level": "S0", "v7b_verdict": dec["engine_verdict"], "v8_untrusted": dec["reasons"]}
    return out


def compare(base, variant, entry, inputs, cfg, out_dir, label=None, project=None, family=None, anchor_key=None):
    """Public API: run + sidecar, return the EvidenceRecord. `cfg` may be partial (filled from sbgv7 defaults)."""
    from sbgv7.config import SCHEMA, _fill
    from .adapter import load_record
    cfg = cfg if isinstance(cfg, dict) and "harness" in cfg else _fill(SCHEMA, cfg or {}, "")  # partial -> engine defaults (its own validator)
    inputs = [{"id": i.get("id", f"i{k}"), "args": i["args"], "kwargs": i.get("kwargs", {})} for k, i in enumerate(inputs)]
    run_capture(base, variant, entry, inputs, cfg, out_dir, anchor_key)
    return load_record(out_dir, label=label, project=project, family=family, anchor_key=anchor_key)

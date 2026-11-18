"""Evidence directory (V7-B evidence.jsonl [+ v8_parts.json sidecar]) -> schema.EvidenceRecord. Pure read; never executes anything.
Mapping decisions (each is a modelling choice, documented in reports/v8/V8_ARCHITECTURE.md):
- obs_fingerprint: sha256 of the canonical body (t, ret, type, msg, stdout, files, globals, argmut, fd1) of the VARIANT side's primary run.
- channels_present: CAPTURE completeness, not activity: outcome <- t present and result readable (not lossy), exception <- t recorded, side_effect <- stdout/files/globals/argmut all
  present and not truncated, api <- signature recorded. A run without an observation (limit, tamper) captures nothing.
- n_repeat_runs = recorded runs of kind repeat/replay/alt (both sides); deterministic = outcome != QUARANTINED.
- hits/branches come from the sidecar only (and only when it is bound to this log); without it hits are empty and meta.no_hits=True.
- integrity_ok = sbgv7 verify() succeeded AND the sidecar (if any) is consistent AND the V8 validator (evidence_schema.validate_dir) did not find the evidence untrusted
  (independent-capture mismatch/incomplete/missing, schema or binding violation, bad anchor MAC when a key is supplied). meta.capture/anchor/untrusted/effective_verdict expose why;
  a legacy V7-B dir with no V8 artefacts has capture='not_collected' (no independent record exists) and is NOT marked untrusted."""
import json, os

from sbgv7 import records as R
from sbgv7.runner import _static_branches
from sbgv7.verify import Unverifiable, VerifyError, verify

from .schema import EvidenceRecord, InputEvidence

OBS_KEYS = ("t", "ret", "type", "msg", "stdout", "files", "globals", "argmut", "fd1")


def load_log(d):
    recs = R.read_log(os.path.join(d, "evidence.jsonl"))
    return recs, {r["id"]: r for r in recs}


def fingerprint(obs):
    return R.sha(R.canon_json({k: obs[k] for k in OBS_KEYS if k in obs}))[:32] if obs else ""


def channels(obs, summary):
    if not obs: return []
    ch = []
    if "t" in obs and not obs.get("lossy"): ch.append("outcome")
    if "t" in obs: ch.append("exception")
    if all(k in obs for k in ("stdout", "files", "globals", "argmut")) and not summary.get("truncated"): ch.append("side_effect")
    if obs.get("sig") is not None: ch.append("api")
    return ch


def recorded_parts(recs, byid):
    """Per-input hit/branch sets recomputed from the Run records themselves (what the sidecar must agree with): {input_id: {hits, branches}}."""
    pkg = next(r for r in recs if r["kind"] == "EvidencePackage")["body"]
    out = {}
    for row in pkg["rows"]:
        h, b = {"base": set(), "variant": set()}, {"base": {}, "variant": {}}
        for rid in row["run_ids"]:
            r = byid[rid]; s = byid[r["refs"][0]]["body"]["role"]
            h[s] |= set(r["meta"]["hits"])
            for k, v in r["meta"]["branches"].items(): b[s].setdefault(k, set()).update(v)
        out[row["input_id"]] = {"hits": {s: sorted(h[s]) for s in h}, "branches": {s: {k: sorted(v) for k, v in b[s].items()} for s in b}}
    return out


def load_sidecar(d):
    p = os.path.join(d, "v8_parts.json")
    return json.load(open(p)) if os.path.exists(p) else None


def load_record(evidence_dir, label=None, project=None, family=None, anchor_key=None, require_anchor=False):
    from .evidence_schema import validate_dir
    from .procsep import decide
    from .trust import check_sidecar
    d = evidence_dir
    recs, byid = load_log(d)
    pkg = next((r["body"] for r in recs if r["kind"] == "EvidencePackage"), None)
    verdict = next((r for r in recs if r["kind"] == "Verdict"), None)
    if pkg is None or verdict is None: raise ValueError("incomplete evidence log: no EvidencePackage/Verdict record (truncated?); no record can be built")
    suff = next((r for r in recs if r["kind"] == "SufficiencyRecord"), None)
    try: verify(d); vstat = "verified"
    except Unverifiable: vstat = "unverifiable"
    except (VerifyError, OSError, KeyError, ValueError, TypeError): vstat = "failed"
    val = validate_dir(d, anchor_key, require_anchor); sc = val["sidecar"]
    side = {p["input_id"]: p for p in load_sidecar(d)["parts"]} if sc["status"] == "ok" else {}
    inputs = []
    for row in pkg["rows"]:
        runs = [byid[i] for i in row["run_ids"]]
        role = lambda r: byid[r["refs"][0]]["body"]["role"]
        prim = next((r for r in runs if role(r) == "variant" and r["body"]["run_kind"] == "primary"), None)
        obs = byid[prim["refs"][1]]["body"] if prim and len(prim["refs"]) > 1 else None
        sp = side.get(row["input_id"], {})
        inputs.append(InputEvidence(
            input_id=row["input_id"], outcome=row["outcome"], lossy=bool(row["lossy"]), degenerate=bool(row["degenerate"]),
            deterministic=row["outcome"] != "QUARANTINED", n_repeat_runs=sum(r["body"]["run_kind"] in ("repeat", "replay", "alt") for r in runs),
            obs_fingerprint=fingerprint(obs), channels_present=channels(obs, prim["body"]["summary"] if prim else {}),
            hits=sp.get("hits", {"base": [], "variant": []}), branches=sp.get("branches", {"base": {}, "variant": {}})))
    units, srcs = pkg["regions"]["units"], {s: byid[v]["meta"].get("src") for s, v in pkg["versions"].items()}
    sb = {s: len(_static_branches(srcs[s], set(units[s]))) if srcs[s] and units[s] else 0 for s in ("base", "variant")}
    blockers = sorted({c for c, _ in suff["body"]["blockers"]}) if suff else []
    vb = verdict["body"]
    meta = {"verify": vstat, "sidecar": sc["status"], "no_hits": not side, "log_head": json.loads(open(os.path.join(d, "evidence.jsonl")).read().splitlines()[-1])["hash"],
            "src_dir": d, "primary": vb["primary"], "secondary": vb["secondary"], "stop": pkg["stop"], "tampered": pkg["tampered"],
            "policy_below_minimum": pkg.get("policy_below_minimum"), "capture": val["capture"]["status"], "anchor": val["anchor"]["status"],
            "untrusted": val["trusted"] is False, "untrusted_reasons": val["reasons"], "effective_verdict": decide(vb["value"], val)["verdict"]}
    return EvidenceRecord(
        pair_id=vb["pair_id"], project=project or "unknown", family=family or project or "unknown", y=label, v7b_verdict=vb["value"], v7b_level=vb["level"],
        inputs=inputs, changed_units={s: list(units[s]) for s in ("base", "variant")}, static_branches=sb, env_id=R.content_id("Env", pkg["env"]),
        integrity_ok=vstat == "verified" and sc["status"] != "inconsistent" and val["trusted"] is not False, blockers=blockers, config={**pkg["config"]["repeat"], "s2_branch_floor": pkg["config"]["suff"]["s2_branch_floor"]}, meta=meta)

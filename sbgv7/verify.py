"""Independent verdict recomputation from DIR/evidence.jsonl alone (python -m sbgv7 verify DIR). Checks the hash chain and content ids,
then re-derives per-input outcomes (runner.classify), changed units (runner.static_phase from the stored sources), activation and
the verdict (decide.py via runner.finalize) from the stored Runs/Observations/Inputs/config and compares with the recorded records.
Does NOT re-execute anything. Facts taken as recorded (not re-derivable offline): the observations themselves, run status/limit,
and the stop reason. Limit: a writer who can recompute the whole hash chain can forge a consistent log; pin `log_head`
(verdict.json) out of band for that (docs/architecture/V7B_IMPLEMENTATION.md)."""
import json, os

from . import records as R
from .runner import ROW_FIELDS, RunOut, _hits, _row, classify, finalize, static_phase


class VerifyError(Exception):
    pass


class Unverifiable(Exception):
    pass


def _need(c, msg):
    if not c: raise VerifyError(msg)


def _runout(rec, byid):
    s, m = rec["body"]["summary"], rec["meta"]
    oid = rec["refs"][1] if len(rec["refs"]) > 1 else None
    return RunOut(rec["id"], byid[oid]["body"] if oid else None, s["limit"], s["phase"], s.get("msg", ""), s["sandbox_ok"], s["truncated"],
                  s["tampered"], set(m["hits"]), {k: set(v) for k, v in m["branches"].items()}, s.get("sig"), oid)


def verify(d):
    path = os.path.join(d, "evidence.jsonl")
    try:
        recs = R.read_log(path)
    except R.ChainError as e:
        raise VerifyError(str(e))
    except (ValueError, KeyError) as e:
        raise VerifyError(f"unreadable evidence log: {e}")
    byid = {r["id"]: r for r in recs}
    for r in recs:  # content-addressed kinds must hash to their id (Run: slot id; Witness: refs extended after id assignment)
        if r["kind"] not in ("Run", "Witness") and r["id"] != R.Rec(r["kind"], "", r["evidence_class"], r["status"], r["refs"], r["body"]).id:
            raise VerifyError(f"record {r['id']} ({r['kind']}) does not match its content id")
    pk = [r for r in recs if r["kind"] == "EvidencePackage"]
    vd = [r for r in recs if r["kind"] == "Verdict"]
    _need(len(pk) == 1 and len(vd) == 1 and recs[-1] is vd[0], "log must hold exactly one EvidencePackage and end with exactly one Verdict")
    pkg, verdict = pk[0]["body"], vd[0]
    _need(pk[0]["id"] in verdict["refs"], "verdict does not reference the evidence package")
    if os.path.exists(os.path.join(d, "verdict.json")):
        vj = json.load(open(os.path.join(d, "verdict.json")))
        _need(vj["verdict_id"] == verdict["id"] and vj["verdict"] == verdict["body"]["value"], "verdict.json disagrees with the log")
        _need(vj.get("log_head") in (None, json.loads(open(path).read().splitlines()[-1])["hash"]), "verdict.json log_head disagrees with the log")
    cfg, src = pkg["config"], {}
    for s, vid in pkg["versions"].items():
        pv = byid[vid]
        if "src" not in pv["meta"]: raise Unverifiable(f"source of {s} omitted (size cap): verdict not recomputable")
        src[s] = pv["meta"]["src"].encode("utf-8", "surrogateescape")
        _need(R.sha(src[s]) == pv["body"]["sha256"], f"source text of {s} does not match its recorded digest")
    _need(R.content_id("H", [cfg["harness"], pkg["harness_sha"]]) == pkg["h_id"], "harness declaration id mismatch")
    _need(R.content_id("Pair", [pkg["versions"]["base"], pkg["versions"]["variant"], pkg["entry"], pkg["h_id"]]) == verdict["body"]["pair_id"], "pair id mismatch")
    if any("omitted" in i for i in pkg["inputs"]): raise Unverifiable("an input was omitted (size cap): verdict not recomputable")
    ins = {i["id"]: R.sha(R.canon_json([i["args"], i["kwargs"]])) for i in pkg["inputs"]}
    role = lambda r: byid[r["refs"][0]]["body"]["role"]
    probe = {s: _runout(byid[rid], byid) for s, rid in pkg["probe_runs"].items()}
    st, reg, soft = static_phase(cfg, src, probe)
    _need(reg == pkg["regions"], "changed regions recomputed from the stored sources differ from the recorded ones")
    parts = []
    for row in pkg["rows"]:
        runs = {"base": [], "variant": []}; extra = {"replay": {"base": [], "variant": []}, "alt": {"base": [], "variant": []}}
        for rid in row["run_ids"]:
            r = byid[rid]; k = r["body"]["run_kind"]
            _need(r["body"]["input_hash"] == ins.get(row["input_id"]), f"run {rid} was not made on input {row['input_id']}")
            _need(r["body"]["harness_decl_id"] == pkg["h_id"], f"run {rid} used a different harness declaration")
            (runs[role(r)] if k in ("primary", "repeat") else extra[k][role(r)]).append(_runout(r, byid))
        ev, stat, det = classify(row["input_id"], runs, cfg, lambda kind: extra[kind])
        ev.witness_id = row["witness_id"]
        _need({k: _row(ev)[k] for k in ROW_FIELDS} == {k: row[k] for k in ROW_FIELDS}, f"input {row['input_id']}: recomputed outcome {ev.outcome} differs from recorded {row['outcome']}")
        if ev.outcome == "CONFIRMED_DIFF":
            w = byid.get(ev.witness_id)
            _need(w and w["kind"] == "Witness" and w["body"]["input_hash"] == ins[row["input_id"]], f"input {row['input_id']}: witness missing or for another input")
        st += stat; parts.append((ev, *_hits(runs)))
    tampered = any(r["body"]["summary"]["tampered"] for r in recs if r["kind"] == "Run")
    _need(tampered == pkg["tampered"], "tamper flag differs from the runs")
    (value, level, primary, secondary, wid), body = finalize(cfg, src, st, reg, soft, parts, pkg["stop"], tampered)
    vb = verdict["body"]
    _need((value, level, primary, sorted(secondary)) == (vb["value"], vb["level"], vb["primary"], vb["secondary"]),
          f"recomputed verdict {(value, level, primary, sorted(secondary))} differs from recorded {(vb['value'], vb['level'], vb['primary'], vb['secondary'])}")
    if wid: _need(wid in verdict["refs"], "recomputed witness is not referenced by the verdict")
    else:
        sr = byid[verdict["refs"][0]]
        _need(sr["kind"] == "SufficiencyRecord" and R.canon_json(sr["body"]) == R.canon_json(body), "sufficiency record differs from its recomputation")
    return {"verified": True, "verdict": value, "level": level, "primary": primary, "records": len(recs), "inputs": len(parts)}

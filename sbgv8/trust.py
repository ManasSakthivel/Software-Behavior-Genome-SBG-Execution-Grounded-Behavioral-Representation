"""Trust report for one evidence directory + forgery suite. This module DOES NOT claim security: it separates five questions that a hash chain
conflates, says for each what is and is NOT established, and records which attacks from the evaluated program are detected, blocked or still succeed.
  integrity   - is the log internally consistent (hash chain, content ids, sbgv7 verify recomputation, verdict.json, sidecar binding)?
  provenance  - is the surrounding record present and consistent (verdict.json, sidecar, harness digest, optional externally supplied source/head pins)?
  authenticity- were the observations produced by the evaluated program under the honest harness? NOT established by any offline check; the optional
                shadow re-observation is an independent cross-check of return values, not a proof.
  isolation   - what contained the program (macOS sandbox-exec profile + rlimits + fresh process group); NOT validated on Linux; harness shares the
                program's address space (red-team M-4).
  inference   - is the verdict recomputable from the recorded facts (verify) and what does it mean (absence of observed divergence, not equivalence)."""
import copy, dataclasses, hashlib, json, os, shutil, sys, tempfile

from sbgv7 import isolation, records as R
from sbgv7.runner import HARNESS
from sbgv7.verify import Unverifiable, VerifyError, verify

from . import adapter, evidence_schema as ES, procsep

SHADOW_SRC = r'''
import json, os, sys
a = json.loads(sys.argv[1]); out = os.dup(1); os.close(1); os.open(os.devnull, os.O_WRONLY)   # program output cannot reach the result fd by accident
def C(v):
    t = type(v)
    if v is None: return ["none"]
    if t is bool: return ["bool", v]
    if t is int: return ["int", hex(v)]
    if t is float: return ["float", repr(v)]
    if t is str: return ["str", v]
    if t is bytes: return ["bytes", v.hex()]
    if t in (list, tuple): return [t.__name__, [C(i) for i in v]]
    if t is dict: return ["dict", [[C(k), C(x)] for k, x in v.items()]]
    if t in (set, frozenset):
        b = [C(i) for i in v]; b.sort(key=json.dumps); return [t.__name__, b]
    return ["opaque", t.__qualname__]
res = {"t": "error"}
try:
    ns = {"__name__": "shadow_target", "__file__": a["src"]}
    exec(compile(open(a["src"]).read(), a["src"], "exec"), ns)
    try: res = {"t": "returned", "ret": C(ns[a["entry"]](*a["args"], **a["kwargs"]))}
    except BaseException as e: res = {"t": "raised", "type": f"{type(e).__module__}.{type(e).__qualname__}"}
except BaseException as e: res = {"t": "error", "msg": type(e).__name__}
os.write(out, ("\n@@SHADOW@@" + json.dumps(res)).encode())
'''


@dataclasses.dataclass
class TrustReport:
    integrity: dict
    provenance: dict
    authenticity: dict
    isolation: dict
    issues: list
    inference: dict = dataclasses.field(default_factory=dict)

    def to_dict(self): return dataclasses.asdict(self)


def _sha_file(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def check_sidecar(d):
    """{'status': ok|missing|inconsistent, 'detail'}. ok = bound to this log (sha256 + head) and equal to what the Run records themselves say."""
    side = adapter.load_sidecar(d) if os.path.isdir(d) else None
    if side is None: return {"status": "missing", "detail": "no v8_parts.json (hits unavailable; record gets meta.no_hits)"}
    errs = ES.validate_sidecar(side)
    if errs: return {"status": "inconsistent", "detail": "schema: " + "; ".join(errs[:3])}
    try:
        ev = os.path.join(d, "evidence.jsonl")
        recs, byid = adapter.load_log(d)
        head = json.loads(open(ev).read().splitlines()[-1])["hash"]
        if side.get("schema") != "v8.parts.1": return {"status": "inconsistent", "detail": "unknown sidecar schema"}
        if side["evidence_sha256"] != _sha_file(ev) or side["log_head"] != head: return {"status": "inconsistent", "detail": "sidecar not bound to this evidence log (sha256/head)"}
        rp, pkg = adapter.recorded_parts(recs, byid), next(r for r in recs if r["kind"] == "EvidencePackage")["body"]
        rows = {r["input_id"]: r for r in pkg["rows"]}
        if sorted(p["input_id"] for p in side["parts"]) != sorted(rows): return {"status": "inconsistent", "detail": "input set differs from the package rows"}
        for p in side["parts"]:
            row = rows[p["input_id"]]
            if (p["outcome"], p["lossy"], p["degenerate"]) != (row["outcome"], bool(row["lossy"]), bool(row["degenerate"])): return {"status": "inconsistent", "detail": f"{p['input_id']}: outcome/lossy/degenerate differ from the package"}
            if p["hits"] != rp[p["input_id"]]["hits"] or p["branches"] != rp[p["input_id"]]["branches"]: return {"status": "inconsistent", "detail": f"{p['input_id']}: hits/branches differ from the Run records"}
        return {"status": "ok", "detail": "bound to the log head and equal to the Run records"}
    except (R.ChainError, OSError, KeyError, ValueError, StopIteration) as e:
        return {"status": "inconsistent", "detail": f"{type(e).__name__}: {e}"}


def shadow_run(src_path, entry, args, kwargs, timeout_s=10):
    """One independent minimal observation: a fresh sandboxed child (sbgv7.isolation transport, but NOT harness.py: own canonicaliser, own exec, own result fd)."""
    with tempfile.TemporaryDirectory() as td:
        sp = os.path.join(td, "shadow.py"); open(sp, "w").write(SHADOW_SRC)
        r = isolation.run_script(sp, [json.dumps(dict(src=os.path.abspath(src_path), entry=entry, args=args, kwargs=kwargs))], timeout_s=timeout_s, cpu_s=5, out_cap=1 << 20)
    tail = r.stdout.rsplit("@@SHADOW@@", 1)
    if len(tail) != 2: return {"t": "no_result", "status": r.status}
    try: return json.loads(tail[1])
    except ValueError: return {"t": "no_result", "status": "malformed"}


def shadow_check(d, timeout_s=10):
    """Re-observe both sides on every recorded input and compare the return-value fingerprint with the recorded variant/base primary observation.
    Per input: match | mismatch | not_comparable. Executes the (sandboxed) programs again: only run it on evidence you were willing to execute once."""
    recs, byid = adapter.load_log(d)
    pkg = next(r for r in recs if r["kind"] == "EvidencePackage")["body"]
    ins = {i["id"]: i for i in pkg["inputs"]}
    out = []
    with tempfile.TemporaryDirectory() as td:
        paths = {}
        for s, vid in pkg["versions"].items():
            src = byid[vid]["meta"].get("src")
            if src is None: return {"status": "unavailable", "detail": f"source of {s} omitted", "inputs": []}
            paths[s] = os.path.join(td, f"{s}_prog.py"); open(paths[s], "w").write(src)
        for row in pkg["rows"]:
            i = ins[row["input_id"]]
            if "omitted" in i: out.append({"input": row["input_id"], "side": "-", "result": "not_comparable"}); continue
            for rid in row["run_ids"]:
                r = byid[rid]
                if r["body"]["run_kind"] != "primary": continue
                side = byid[r["refs"][0]]["body"]["role"]
                obs = byid[r["refs"][1]]["body"] if len(r["refs"]) > 1 else None
                if not obs or obs.get("t") != "returned" or json.dumps(obs.get("ret")).count('"obj"') or obs.get("lossy"):
                    out.append({"input": row["input_id"], "side": side, "result": "not_comparable"}); continue
                sh = shadow_run(paths[side], pkg["entry"], i["args"], i["kwargs"], timeout_s)
                same = sh.get("t") == "returned" and R.canon_json(_norm(sh["ret"])) == R.canon_json(_norm(obs["ret"]))
                out.append({"input": row["input_id"], "side": side, "result": "match" if same else "mismatch"})
    bad = [o for o in out if o["result"] == "mismatch"]
    return {"status": "mismatch" if bad else ("match" if any(o["result"] == "match" for o in out) else "not_comparable"), "inputs": out}


def _norm(f):  # harness sorts set items by json.dumps; list/tuple/dict forms are identical in both canonicalisers
    return f


def check(evidence_dir, shadow=False, expected_sources=None, pinned_head=None, anchor_key=None, require_anchor=False):
    """expected_sources={'base': path, 'variant': path} and pinned_head (log head hash recorded out of band) are OPTIONAL external anchors;
    without them provenance/authenticity are weak by construction and the report says so."""
    d, issues = evidence_dir, []
    integ = {"chain": None, "verify": None, "verdict_json": None, "sidecar": None, "capture": None, "anchor": None}
    try:
        recs, byid = adapter.load_log(d); integ["chain"] = "ok"
    except (R.ChainError, OSError, ValueError, KeyError) as e:
        integ["chain"] = f"broken: {e}"; issues.append(f"integrity: {e}")
        return TrustReport(integ, {}, {"established": [], "not_established": ["everything: the log is unreadable"]}, _isolation(None), issues)
    try: verify(d); integ["verify"] = "verified"
    except Unverifiable as e: integ["verify"] = f"unverifiable: {e}"; issues.append(f"integrity: {e}")
    except (VerifyError, OSError, KeyError, ValueError, TypeError) as e: integ["verify"] = f"failed: {e}"; issues.append(f"integrity: verify failed: {e}")
    val = ES.validate_dir(d, anchor_key, require_anchor); sc = val["sidecar"]; integ["sidecar"] = sc["status"]
    integ["capture"], integ["anchor"] = val["capture"]["status"], val["anchor"]["status"]
    if sc["status"] == "inconsistent": issues.append(f"integrity: sidecar {sc['detail']}")
    if val["capture"]["status"] in ("invalid", "untrusted", "missing"): issues.append(f"integrity: independent capture {val['capture']['status']}: {val['capture']['detail']}")
    if val["anchor"]["status"] == "invalid": issues.append(f"integrity: anchor {val['anchor']['detail']}")
    pkg = next(r for r in recs if r["kind"] == "EvidencePackage")["body"]
    vb = next(r for r in recs if r["kind"] == "Verdict")
    head = json.loads(open(os.path.join(d, "evidence.jsonl")).read().splitlines()[-1])["hash"]
    vj = os.path.join(d, "verdict.json")
    integ["verdict_json"] = "absent" if not os.path.exists(vj) else ("ok" if json.load(open(vj)).get("log_head") == head else "disagrees")
    prov = {"verdict_json_present": os.path.exists(vj), "sidecar_present": sc["status"] != "missing", "harness_sha_matches_current": pkg["harness_sha"] == _sha_file(HARNESS),
            "pinned_head": None if pinned_head is None else pinned_head == head, "sources_match_expected": None, "log_head": head}
    if not prov["verdict_json_present"]: issues.append("provenance: verdict.json absent (verify cannot notice; the verdict must be taken from the log)")
    if not prov["harness_sha_matches_current"]: issues.append("provenance: evidence was produced by a different harness.py than the current one")
    if pinned_head is not None and pinned_head != head: issues.append("provenance: log head differs from the externally pinned head")
    if expected_sources:
        ok = all(_sha_file(p) == byid[pkg["versions"][s]]["body"]["sha256"] for s, p in expected_sources.items())
        prov["sources_match_expected"] = ok
        if not ok: issues.append("provenance: recorded program source differs from the expected file (evidence substitution)")
    auth = {"established": ["records are consistent with each other (chain, content ids)", "the verdict follows from the recorded runs (verify recomputation)"] +
            (["log head equals the externally pinned head"] if pinned_head == head else []) +
            (["recorded sources equal the expected files"] if prov["sources_match_expected"] else []),
            "not_established": ["that a writer who holds the anchor key (or can read it) did not recompute log + sidecar + capture + MAC (pin the head out of band)",
                                "that the observations were produced by the honest harness: harness.py shares the evaluated program's address space (red-team M-4)",
                                "that a writer who can recompute the chain did not forge a consistent log (needs an out-of-band pinned head)",
                                "that the recorded program is the program under review (needs expected_sources)",
                                "that an operating-system sandbox contained the run on this platform (see isolation)"], "shadow": "not run"}
    if shadow:
        auth["shadow"] = shadow_check(d)
        if auth["shadow"]["status"] == "mismatch": issues.append("authenticity: shadow re-observation disagrees with the recorded return value(s)")
        elif auth["shadow"]["status"] == "match": auth["established"].append("an independent re-execution reproduced the recorded return values on comparable inputs (cross-check only; same-address-space limits apply)")
    inf = {"verdict": vb["body"]["value"], "effective_verdict": procsep.decide(vb["body"]["value"], val)["verdict"], "level": vb["body"]["level"], "recomputable": integ["verify"] == "verified",
           "meaning": "NO_DIVERGENCE_OBSERVED = no divergence observed within the executed inputs/channels; never equivalence. Correctness of the inference is relative to those inputs (V8 profile/calibration judge sufficiency)."}
    return TrustReport(integ, prov, auth, _isolation(pkg), issues, inf)


def _isolation(pkg):
    caps = (pkg or {}).get("env", [None, None, {}])[2] if pkg else {}
    return {"mechanism": "macOS sandbox-exec profile (network denied, writes confined to workdir) + rlimits + process-group kill, fresh child per run; harness in the program's own process",
            "recorded_platform": (pkg or {}).get("env", ["", ""])[1] if pkg else None, "recorded_controls": caps, "policy_below_minimum": (pkg or {}).get("policy_below_minimum"),
            "validated_on_linux": False, "validated_against_determined_adversary": False, "this_host": sys.platform}


# ---------------------------------------------------------------- forgery suite
BASE = "def f(x):\n    return x + 1\n"
HDR = "import sys, os\nm = sys.modules['__main__']\n"
ATTACKS = {  # variant programs (all are genuinely divergent: x+2 vs x+1); the attack tries to make the pair look clean
    "A01_patch_canonicaliser_via___main__": HDR + "if hasattr(m, 'canon'):\n    _o = m.canon\n    m.canon = lambda v: _o(v - 1) if type(v) is int else _o(v)\ndef f(x):\n    return x + 2\n",
    "A02_forge_result_via_harness_finish": HDR + "def f(x):\n    if not hasattr(m, 'finish'): return x + 2\n    m.finish({'phase': 'ok', 't': 'returned', 'ret': ['int', hex(x + 1)], 'argmut': ['list', [['list', [['int', hex(x)]]], ['dict', []]]], 'args_changed': False, 'globals': {}, 'files': {}, 'sig': [['x', 'POSITIONAL_OR_KEYWORD', False]]}, m.Cap())\n",
    "A03_os__exit_before_result": "import os\ndef f(x):\n    os._exit(0)\n",
    "A04_write_garbage_to_result_fd": "import os\ndef f(x):\n    for fd in range(3, 64):\n        try: os.write(fd, b'SBGV7F1 5 deadbeef\\nhello')\n        except OSError: pass\n    return x + 2\n",
    "A05_close_result_fd": "import os\ndef f(x):\n    for fd in range(3, 64):\n        try: os.close(fd)\n        except OSError: pass\n    return x + 2\n",
    "A06_forged_result_line_on_stdout": "def f(x):\n    print('SBGV7F1 2 00\\n{}')\n    return x + 2\n",
    "A08_hide_stdout_divergence_by_patching_Cap": HDR + "if hasattr(m, 'Cap'): m.Cap.write = lambda self, s: len(s)\ndef f(x):\n    print('extra output')\n    return x + 1\n",
    "A07_sense_harness_and_behave": HDR + "def f(x):\n    return x + 1 if hasattr(m, 'canon') else x + 2\n",
    # new attacks (V8 hardening, ids appended; A01-A08 above are the original suite and are unchanged)
    "A16_close_stderr_then_hide_stdout_divergence": HDR + "if hasattr(m, 'Cap'): m.Cap.write = lambda self, s: len(s)\ndef f(x):\n    import os\n    os.close(2)\n    print('extra output')\n    return x + 1\n",
    "A17_forge_tee_record_with_guessed_nonce": "import os\ndef f(x):\n    os.write(2, b'@@SBGV8T@@' + b'0' * 32 + b' 1 W 41@@\\n')\n    return x + 2\n",
}
# post-hoc attacks mutate a copy of an HONEST log; name -> description
POSTHOC = ("P01_edit_observation_no_rechain", "P02_edit_verdict_and_rechain", "P03_drop_verdict_json", "P04_edit_unverified_field_and_rechain",
           "P05_tamper_sidecar_hits", "P06_substitute_evidence_of_another_program", "P07_rechain_without_rebinding_sidecar",
           "P08_rechain_and_reanchor_with_the_key", "P09_strip_anchor")
FAST = {"repeat": {"r_det": 2, "r_replay": 2, "k_alt": 1}, "budget": {"cpu_seconds": 30, "per_run": {"cpu_s": 2, "wall_s": 5}}}


def _engine(tmp, name, base_src, var_src, cfg_over, inputs=None, key=None):
    from sbgv7.config import SCHEMA, _fill
    from .collect import run_capture
    d = os.path.join(tmp, name); os.makedirs(d)
    bp, vp = os.path.join(d, "base.py"), os.path.join(d, "variant.py")
    open(bp, "w").write(base_src); open(vp, "w").write(var_src)
    out = os.path.join(d, "ev")
    ins = inputs or [{"id": "i0", "args": [1], "kwargs": {}}]
    try: run_capture(bp, vp, "f", ins, _fill(SCHEMA, cfg_over, ""), out, anchor_key=key); err = None
    except Exception as e: err = f"{type(e).__name__}: {e}"
    return out, bp, vp, err


def _rewrite(path, fn):
    """Apply fn(list_of_records) then re-chain the whole log (attacker with full write access to the evidence directory)."""
    recs = R.read_log(path); fn(recs); prev, lines = "0" * 64, []
    for i, r in enumerate(recs):
        h = R.sha(prev + R.canon_json(r)); lines.append(R.canon_json({"seq": i, "prev": prev, "rec": r, "hash": h})); prev = h
    open(path, "w").write("\n".join(lines) + "\n")
    return prev


def _row(aid, desc, out, expect="DIVERGENT_OBSERVABLE", err=None, base=None, var=None, shadow=True, tampered=False, key=None):
    if err or not os.path.exists(os.path.join(out, "evidence.jsonl")): return {"attack": aid, "description": desc, "verdict": None, "outcome": "ENGINE_ERROR", "checks": {}, "note": err}
    verdict = json.loads(open(os.path.join(out, "verdict.json")).read())["verdict"] if os.path.exists(os.path.join(out, "verdict.json")) else next(r for r in R.read_log(os.path.join(out, "evidence.jsonl")) if r["kind"] == "Verdict")["body"]["value"]
    rep = check(out, shadow=shadow, expected_sources={"base": base, "variant": var} if base else None, anchor_key=key)
    return _classify(aid, desc, verdict, expect, rep, tampered)


def _classify(aid, desc, verdict, expect, rep, tampered=False):
    sh = rep.authenticity.get("shadow")
    checks = {"verify": rep.integrity["verify"], "sidecar": rep.integrity["sidecar"], "capture": rep.integrity["capture"], "anchor": rep.integrity["anchor"], "verdict_json": rep.integrity["verdict_json"], "chain": rep.integrity["chain"],
              "shadow": sh["status"] if isinstance(sh, dict) else sh, "sources_match": rep.provenance.get("sources_match_expected")}
    caught = [k for k, bad in (("chain", checks["chain"] != "ok"), ("verify", checks["verify"] != "verified"), ("sidecar", checks["sidecar"] == "inconsistent"),
              ("independent_capture", checks["capture"] in ("invalid", "untrusted", "missing")), ("anchor_mac", checks["anchor"] == "invalid"),
              ("verdict_json_absent", checks["verdict_json"] == "absent"), ("verdict_json_disagrees", checks["verdict_json"] == "disagrees"),
              ("shadow_reobservation", checks["shadow"] == "mismatch"), ("source_binding", checks["sources_match"] is False)) if bad]
    if caught: out = "DETECTED by " + ", ".join(caught)
    elif tampered: out = "SUCCEEDS (open): evidence altered, no check fires"
    elif verdict == expect: out = "NO EFFECT (engine still reports the true verdict)"
    elif verdict != expect and verdict == "INSUFFICIENT": out = "BLOCKED by engine (verdict degraded to INSUFFICIENT)"
    else: out = "SUCCEEDS (open): false verdict with no check firing"
    return {"attack": aid, "description": desc, "verdict": verdict, "effective_verdict": rep.inference.get("effective_verdict", "INSUFFICIENT"), "honest_expected": expect, "checks": checks, "outcome": out, "issues": rep.issues}


def forgery_suite(cfg_over=None, only=None):
    """Run every attack; returns {'meta':..., 'results':[row...]}. Each row: verdict observed, which checks fired, outcome. Unresolved attacks stay listed as SUCCEEDS (open)."""
    cfg_over = cfg_over or FAST
    res, tmp, key = [], tempfile.mkdtemp(prefix="sbgv8_forge_"), os.urandom(32)  # the key exists only in this (controller) process; no attack below is given it except P08
    try:
        honest, hb, hv, e = _engine(tmp, "honest", BASE, "def f(x):\n    return x + 2\n", cfg_over, key=key)
        res.append(_row("H00_honest_control", "no attack (control)", honest, "DIVERGENT_OBSERVABLE", e, hb, hv, key=key))
        for aid, src in ATTACKS.items():
            if only and aid not in only: continue
            out, bp, vp, e = _engine(tmp, aid, BASE, src, cfg_over, key=key)
            exp = "DIVERGENT_OBSERVABLE"
            res.append(_row(aid, "attack launched from the evaluated (variant) program: " + aid[4:].replace("_", " "), out, exp, e, bp, vp, key=key))
        for pid in POSTHOC:
            if only and pid not in only: continue
            d = os.path.join(tmp, pid); shutil.copytree(os.path.dirname(honest), d); out = os.path.join(d, "ev"); ev = os.path.join(out, "evidence.jsonl")
            hp = {"base": os.path.join(d, "base.py"), "variant": os.path.join(d, "variant.py")}
            if pid == "P01_edit_observation_no_rechain":
                s = open(ev).read(); i = s.index('"kind":"Observation"'); open(ev, "w").write(s[:i] + s[i:].replace('"ret":["int","0x3"]', '"ret":["int","0x2"]', 1))
            elif pid == "P02_edit_verdict_and_rechain":
                def f(recs):
                    v = recs[-1]; v["body"].update(value="NO_DIVERGENCE_OBSERVED", level="S1", primary=None); v["id"] = R.Rec("Verdict", "", v["evidence_class"], v["status"], v["refs"], v["body"]).id
                    vj = os.path.join(out, "verdict.json"); j = json.load(open(vj)); j.update(verdict="NO_DIVERGENCE_OBSERVED", level="S1", verdict_id=v["id"]); json.dump(j, open(vj, "w"))
                head = _rewrite(ev, f); j = json.load(open(os.path.join(out, "verdict.json"))); j["log_head"] = head; json.dump(j, open(os.path.join(out, "verdict.json"), "w"))
            elif pid == "P03_drop_verdict_json":
                os.unlink(os.path.join(out, "verdict.json"))
            elif pid == "P09_strip_anchor":
                os.unlink(os.path.join(out, "v8_anchor.json"))
            elif pid in ("P04_edit_unverified_field_and_rechain", "P07_rechain_without_rebinding_sidecar", "P08_rechain_and_reanchor_with_the_key"):
                def f(recs):
                    for r in recs:
                        if r["kind"] == "Run": r["meta"]["cpu_s"] = 0.0; r["meta"]["wall_s"] = 0.0
                head = _rewrite(ev, f); j = json.load(open(os.path.join(out, "verdict.json"))); j["log_head"] = head; json.dump(j, open(os.path.join(out, "verdict.json"), "w"))
                if pid[:3] in ("P04", "P08"):  # attacker also re-binds the sidecar to the new chain
                    sp = os.path.join(out, "v8_parts.json"); sd = json.load(open(sp)); sd.update(log_head=head, evidence_sha256=_sha_file(ev)); json.dump(sd, open(sp, "w"), sort_keys=True)
                if pid[:3] == "P08":  # ... and the capture record, and (holding the key) recomputes the MAC: nothing in the directory can tell
                    cp = os.path.join(out, "v8_capture.json"); cd = json.load(open(cp)); cd.update(log_head=head, evidence_sha256=_sha_file(ev))
                    for x in cd["runs"]: x["cpu_s"] = x["wall_s"] = 0.0
                    json.dump(cd, open(cp, "w"), sort_keys=True); ES.write_anchor(out, key, cd["session"])
            elif pid == "P05_tamper_sidecar_hits":
                p = os.path.join(out, "v8_parts.json"); s = json.load(open(p))
                for part in s["parts"]: part["hits"]["variant"] = sorted(set(part["hits"]["variant"]) | {1, 2, 3, 4})
                json.dump(s, open(p, "w"))
            elif pid == "P06_substitute_evidence_of_another_program":
                out, _, _, e = _engine(tmp, pid + "_run", BASE, "def f(x):\n    return x + 1\n\n# benign stand-in\n", cfg_over, key=key)  # evidence of a clean pair presented for the divergent one
                hp = {"base": hb, "variant": hv}   # expected: the divergent variant
            res.append(_row(pid, "post-hoc: " + pid[4:].replace("_", " "), out, "DIVERGENT_OBSERVABLE", None, hp["base"], hp["variant"], shadow=False, tampered=True, key=key))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"meta": {"platform": sys.platform, "note": "unresolved attacks are open issues; no security is claimed", "config": cfg_over}, "results": res}

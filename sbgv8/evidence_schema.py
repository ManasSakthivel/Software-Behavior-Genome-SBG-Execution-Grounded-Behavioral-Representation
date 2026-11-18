"""Strict, versioned, typed schemas for the V8 evidence artefacts that sit NEXT TO the V7-B log, and the validator role.
  v8_parts.json   v8.parts.1    per-input outcome/hit/branch sidecar (written by collect.run_capture)
  v8_capture.json v8.capture.1  parent-owned independent stdout/stderr capture records, one per spawned run (sbgv8.procsep.Supervisor)
  v8_anchor.json  v8.anchor.1   HMAC-SHA256 over the digest of every decision-relevant file, key held by the controller only
Validation = exact keys (missing/extra rejected), exact types (bool is not int), bounded sizes, unknown schema versions rejected,
unique run ids, reordering/duplicate/partial detection by contiguous seq + count equality with the log, binding to THIS log
(head, sha256, config, harness, per-run input hash/side/status/timings/stdout digest), then the optional MAC.

WHAT THE ANCHOR PROVES (and does not). The MAC key lives with the controller (SBGV8_ANCHOR_KEY / argument), never in the evidence dir and
never in the child's environment, argv or fds. It proves: whoever produced this MAC knew the key, and none of the covered files changed
since. It does NOT prove: that the program was observed honestly (same address space, red-team M-4); that a writer who ALSO holds the key
(or runs as the same user and can read it) did not recompute log+sidecar+capture+MAC; that this is the run the reviewer expected. Against
that writer the only remedy is a head/MAC pinned out of band (trust.check pinned_head). A same-filesystem anchor therefore turns P04 into
'detected' ONLY when the verifier holds the key and the attacker did not."""
import hashlib, hmac, json, math, os, re

from sbgv7 import records as R

SIDECAR_V, CAPTURE_V, ANCHOR_V = "v8.parts.1", "v8.capture.1", "v8.anchor.1"
FILES = {"evidence": "evidence.jsonl", "verdict": "verdict.json", "sidecar": "v8_parts.json", "capture": "v8_capture.json", "anchor": "v8_anchor.json"}
ANCHORED = ("evidence.jsonl", "verdict.json", "v8_parts.json", "v8_capture.json")
_HEX = re.compile(r"[0-9a-f]+")


# ------------------------------------------------------------------ tiny typed-spec checker
def _hex(n): return lambda v: type(v) is str and len(v) == n and bool(_HEX.fullmatch(v))
def _int(v): return type(v) is int and 0 <= v < 1 << 40
def _sint(v): return type(v) is int and -(1 << 31) < v < 1 << 31
def _num(v): return type(v) in (int, float) and math.isfinite(v) and v >= 0
def _bool(v): return type(v) is bool
def _str(v): return type(v) is str and len(v) <= 4096
def _enum(*o): return lambda v: type(v) is str and v in o
def _opt(f): return lambda v: v is None or f(v)
def _list(f, n=1 << 20): return ("list", f, n)
def _map(f): return ("map", f)


def _chk(spec, v, path, errs):
    if isinstance(spec, dict):  # exact object
        if type(v) is not dict: errs.append(f"{path}: expected object"); return
        for k in spec.keys() - v.keys(): errs.append(f"{path}.{k}: missing")
        for k in v.keys() - spec.keys(): errs.append(f"{path}.{k}: unexpected field")
        for k in spec.keys() & v.keys(): _chk(spec[k], v[k], f"{path}.{k}", errs)
    elif isinstance(spec, tuple) and spec[0] == "list":
        if type(v) is not list or len(v) > spec[2]: errs.append(f"{path}: expected list (<= {spec[2]})"); return
        for i, x in enumerate(v): _chk(spec[1], x, f"{path}[{i}]", errs)
    elif isinstance(spec, tuple) and spec[0] == "map":
        if type(v) is not dict: errs.append(f"{path}: expected object"); return
        for k, x in v.items():
            if type(k) is not str: errs.append(f"{path}: non-string key")
            else: _chk(spec[1], x, f"{path}.{k}", errs)
    elif not spec(v): errs.append(f"{path}: invalid value")


def check_schema(spec, obj, name):
    errs = []; _chk(spec, obj, name, errs)
    return errs[:20]


SIDES = {"base": _list(_int), "variant": _list(_int)}
SIDECAR = {"schema": _enum(SIDECAR_V), "log_head": _hex(64), "evidence_sha256": _hex(64), "static_branches": _map(_list(_str)), "units": _map(_list(_int)),
           "parts": _list({"input_id": _str, "outcome": _str, "lossy": _bool, "degenerate": _bool, "hits": SIDES,
                           "branches": {"base": _map(_list(_int)), "variant": _map(_list(_int))}})}
STREAM = {"len": _int, "sha256": _hex(64), "truncated": _bool}
CAP_RUN = {"seq": _int, "nonce": _hex(32), "mode": _enum("call", "probe"), "side": _enum("base", "variant"), "input_hash": _hex(64), "ctl": _opt(_int),
           "status": _str, "detail": _str, "returncode": _opt(_sint), "signal": _opt(_sint), "wall_s": _num, "cpu_s": _num, "fd1": STREAM, "fd2": STREAM,
           "tee": {"open": _bool, "close": _bool, "records": _int, "chars": _int, "declared_chars": _opt(_int), "overflow": _bool, "gaps": _int,
                   "foreign": _int, "malformed": _int, "sha256": _hex(64)},
           "harness": {"frame": _bool, "stdout_len": _opt(_int), "stdout_sha256": _opt(_hex(64)), "stdout_trunc": _opt(_bool)},
           "protocol_error": _str, "orphans_found": _bool, "cleanup_verified": _bool, "flooded": _bool,
           "verdict": _enum("match", "no_frame", "mismatch", "incomplete"), "reasons": _list(_str, 50)}
CAPTURE = {"schema": _enum(CAPTURE_V), "session": _hex(32), "config_sha256": _hex(64), "harness_sha256": _hex(64), "stub_sha256": _hex(64),
           "log_head": _hex(64), "evidence_sha256": _hex(64), "runs": _list(CAP_RUN, 100000), "trusted": _bool, "reasons": _list(_str, 200)}
ANCHOR = {"schema": _enum(ANCHOR_V), "key_id": _hex(16), "session": _hex(32), "files": {n: _hex(64) for n in ANCHORED}, "mac": _hex(64)}


def validate_sidecar(side):
    errs = check_schema(SIDECAR, side, "sidecar")
    if not errs:
        ids = [p["input_id"] for p in side["parts"]]
        if len(set(ids)) != len(ids): errs.append("sidecar.parts: duplicate input_id")
    return errs


# ------------------------------------------------------------------ keys / MAC
def load_key(key=None):
    """bytes (>= 16) | hex str | None -> key bytes or None. Falls back to $SBGV8_ANCHOR_KEY (hex). Never reads a file inside an evidence dir."""
    if key is None: key = os.environ.get("SBGV8_ANCHOR_KEY") or None
    if key is None: return None
    if isinstance(key, str):
        try: key = bytes.fromhex(key)
        except ValueError: raise ValueError("anchor key must be hex")
    if not isinstance(key, (bytes, bytearray)) or len(key) < 16: raise ValueError("anchor key must be >= 16 bytes")
    return bytes(key)


def key_id(key): return hmac.new(key, b"sbgv8-key-id", hashlib.sha256).hexdigest()[:16]
def sha_file(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _mac(key, body): return hmac.new(key, b"sbgv8.anchor.1\n" + R.canon_json(body).encode(), hashlib.sha256).hexdigest()


def write_anchor(d, key, session):
    """Controller-side: MAC over the digest of every decision-relevant file currently in d. Returns the anchor dict (also written)."""
    body = {"schema": ANCHOR_V, "key_id": key_id(key), "session": session, "files": {n: sha_file(os.path.join(d, n)) for n in ANCHORED}}
    a = {**body, "mac": _mac(key, body)}
    json.dump(a, open(os.path.join(d, FILES["anchor"]), "w"), sort_keys=True)
    return a


def _load(p):
    return json.load(open(p))


def check_anchor(d, key=None, require=False, session=None):
    """{'status': absent|unverified_no_key|ok|invalid, 'detail'}. 'ok' = MAC verifies under `key` and every anchored file still matches.
    require=True turns absent / unverified into 'invalid' (a stripped anchor is then noticed)."""
    p = os.path.join(d, FILES["anchor"])
    if not os.path.exists(p):
        return {"status": "invalid" if (require or key) else "absent", "detail": "anchor file absent" + (" but an anchor is required (stripped?)" if (require or key) else "")}
    try: a = _load(p)
    except (OSError, ValueError) as e: return {"status": "invalid", "detail": f"unreadable anchor: {type(e).__name__}"}
    errs = check_schema(ANCHOR, a, "anchor")
    if errs: return {"status": "invalid", "detail": "; ".join(errs[:3])}
    if key is None: return {"status": "invalid" if require else "unverified_no_key", "detail": "anchor present, no key supplied: NOT verified (integrity of the files is only as good as the chain)"}
    if not hmac.compare_digest(a["key_id"], key_id(key)): return {"status": "invalid", "detail": "anchor made under a different key"}
    body = {k: a[k] for k in ("schema", "key_id", "session", "files")}
    if not hmac.compare_digest(a["mac"], _mac(key, body)): return {"status": "invalid", "detail": "bad MAC (anchor edited or not produced with this key)"}
    for n in ANCHORED:
        try: ok = sha_file(os.path.join(d, n)) == a["files"][n]
        except OSError: ok = False
        if not ok: return {"status": "invalid", "detail": f"{n} changed or missing since it was anchored"}
    if session is not None and a["session"] != session: return {"status": "invalid", "detail": "anchor session differs from the capture session"}
    return {"status": "ok", "detail": "MAC verifies and all anchored files match (does not prove honest observation, nor resist a writer holding the key)"}


# ------------------------------------------------------------------ capture <-> log cross validation
def _bad(detail, status="invalid", reasons=None): return {"status": status, "detail": detail, "reasons": reasons or []}


def check_capture(d):
    """{'status': ok|untrusted|invalid|missing|not_collected, 'detail', 'reasons'}.
    not_collected = a plain V7-B directory (no V8 artefacts at all): there IS no independent record and none was promised.
    missing = V8 sidecar present but capture absent. untrusted = the collector itself found a mismatch/incomplete record."""
    cp, sp = os.path.join(d, FILES["capture"]), os.path.join(d, FILES["sidecar"])
    if not os.path.exists(cp):
        if os.path.exists(sp): return _bad("v8_parts.json exists but the independent capture record v8_capture.json is missing", "missing")
        return {"status": "not_collected", "detail": "legacy V7-B directory: no independent stdout record exists", "reasons": []}
    try:
        c = _load(cp)
        recs = R.read_log(os.path.join(d, "evidence.jsonl"))
        head = json.loads(open(os.path.join(d, "evidence.jsonl")).read().splitlines()[-1])["hash"]
    except (OSError, ValueError, KeyError, IndexError, R.ChainError) as e:
        return _bad(f"unreadable: {type(e).__name__}: {e}")
    errs = check_schema(CAPTURE, c, "capture")
    if errs: return _bad("; ".join(errs[:3]))
    byid = {r["id"]: r for r in recs}
    pk = [r for r in recs if r["kind"] == "EvidencePackage"]
    runs = [r for r in recs if r["kind"] == "Run"]
    if len(pk) != 1: return _bad("log has no unique EvidencePackage")
    pkg = pk[0]["body"]
    why = []
    if c["log_head"] != head or c["evidence_sha256"] != sha_file(os.path.join(d, "evidence.jsonl")): why.append("capture is not bound to this evidence log (replayed from another run or log edited)")
    if c["config_sha256"] != R.sha(R.canon_json(pkg["config"])): why.append("configuration binding differs")
    if c["harness_sha256"] != pkg["harness_sha"]: why.append("harness digest differs from the package")
    cr = c["runs"]
    if [x["seq"] for x in cr] != list(range(len(cr))): why.append("run records missing/duplicated/reordered (seq not contiguous)")
    if len({x["nonce"] for x in cr}) != len(cr): why.append("duplicate run nonce")
    if len(cr) != len(runs): why.append(f"{len(cr)} capture records but {len(runs)} Run records (partial or extra records)")
    else:
        for i, (x, r) in enumerate(zip(cr, runs)):
            s, role = r["body"]["summary"], byid[r["refs"][0]]["body"]["role"]
            if (x["status"], x["detail"], x["protocol_error"]) != (s["status"], s["detail"], s["protocol_error"]): why.append(f"run {i}: status/detail/protocol_error differ from the log")
            if x["input_hash"] != r["body"]["input_hash"] or x["side"] != role: why.append(f"run {i}: input hash / side differ from the log")
            if (x["mode"] == "probe") != (r["body"]["run_kind"] == "probe"): why.append(f"run {i}: mode differs from run_kind")
            if (x["cpu_s"], x["wall_s"]) != (r["meta"]["cpu_s"], r["meta"]["wall_s"]): why.append(f"run {i}: timings differ from the log")
            obs = byid[r["refs"][1]]["body"] if len(r["refs"]) > 1 else None
            if obs is not None and x["harness"]["frame"] and x["harness"]["stdout_sha256"] != hashlib.sha256(str(obs.get("stdout", "")).encode()).hexdigest():
                why.append(f"run {i}: recorded observation stdout differs from the stdout the harness reported to the parent")
    if why: return _bad("; ".join(why[:4]), reasons=why)
    if c["trusted"] != all(x["verdict"] in ("match", "no_frame") for x in cr) or not cr and c["trusted"]: return _bad("capture.trusted disagrees with its own run verdicts")
    if not c["trusted"]: return {"status": "untrusted", "detail": "; ".join(c["reasons"][:3]) or "run flagged untrusted by the collector", "reasons": c["reasons"]}
    return {"status": "ok", "detail": f"{len(cr)} runs: independent stdout record matches the harness-reported stdout", "reasons": []}


def validate_dir(d, key=None, require_anchor=False):
    """The validator role: everything that can be said about the V8 artefacts of one evidence dir. -> {'sidecar','capture','anchor','trusted','reasons'}.
    trusted: False = decision layer must treat the evidence as untrusted (-> INSUFFICIENT); None = legacy dir, nothing to validate; True = all checks passed."""
    from .trust import check_sidecar
    sc, cp, an = check_sidecar(d), check_capture(d), None
    sess = None
    if cp["status"] in ("ok", "untrusted"): sess = _load(os.path.join(d, FILES["capture"]))["session"]
    an = check_anchor(d, load_key(key), require_anchor, sess) if cp["status"] != "not_collected" or os.path.exists(os.path.join(d, FILES["anchor"])) or require_anchor else {"status": "absent", "detail": "no V8 artefacts"}
    reasons = ([f"sidecar: {sc['detail']}"] if sc["status"] == "inconsistent" else []) + ([f"capture: {cp['detail']}"] if cp["status"] in ("invalid", "untrusted", "missing") else []) + \
              ([f"anchor: {an['detail']}"] if an["status"] == "invalid" else [])
    trusted = False if reasons else (None if cp["status"] == "not_collected" else True)
    return {"sidecar": sc, "capture": cp, "anchor": an, "trusted": trusted, "reasons": reasons}

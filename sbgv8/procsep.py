"""V8 macOS process separation: five roles, their messages and failure semantics. NOT an OS-level sandbox, NOT validated on Linux.
  1 controller        sbgv8.collect.run_capture: owns the anchor key and the session nonce, installs the collector, runs the UNMODIFIED V7-B engine,
                      writes v8_parts/v8_capture/v8_anchor. Never executes evaluated code.
  2 evaluated process the V7-B child (sbgv7.isolation: fresh process, sandbox-exec, rlimits, process-group kill) running _tee_child.py -> harness.py
                      -> program. Receives: harness JSON arg + per-run nonce. Holds no anchor key (child_env is an allowlist). Its claims are only claims.
  3 evidence collector Supervisor below: patched into isolation.run_script IN THE PARENT ONLY. Reads the child's real fd 1/2 (the parent's own pipes),
                      strips and parses the framed tee records, compares with the harness-reported stdout, emits one CaptureRecord per spawn.
  4 evidence validator evidence_schema.validate_dir (in-process) or validate_isolated (a fresh interpreter, no monkeypatches, MAC-authenticated reply).
  5 decision engine    decide(): pure. Untrusted evidence can never yield NO_DIVERGENCE_OBSERVED or DIVERGENT_OBSERVABLE.
Failure semantics (all fail SAFE = untrusted -> INSUFFICIENT): missing/foreign/duplicate/gapped tee records, no open/close record when the harness
produced a result, stdout mismatch, stderr over the capture cap, validator timeout/crash/bad MAC/nonce mismatch, unsupervised spawn, schema violation.
Termination/timeouts/resource kills are recorded explicitly per run (status/detail/signal/flooded) and are already no-observation runs in V7-B.
Honest limits: the tee shares the evaluated program's address space; a program that replaces sys.stdout/contextlib.redirect_stdout/os.write, or dup2()s fd 2,
can at best suppress records (-> incomplete -> untrusted) and, if it also learns the per-run nonce from argv, forge matching ones (undetected). Binary stdout is
recorded in the decoded form isolation.py keeps (invalid bytes -> U+FFFD); byte-exactness would need an sbgv7 change."""
import hashlib, hmac, json, os, re, subprocess, sys

import sbgv7.runner as RUN
from sbgv7 import isolation, records as R

from . import evidence_schema as ES

HERE = os.path.dirname(os.path.abspath(__file__))
STUB = os.path.join(HERE, "_tee_child.py")
STDOUT_CAP = 32768  # harness.STDOUT_CAP (Cap.write); the parent mirrors the truncation rule
TEE_CAP = 1 << 18  # _tee_child.CAP
_REC = re.compile(r"@@SBGV8T@@([0-9a-f]{32}) (\d+) ([OWXC]) ([0-9a-f]*)@@\n")
_sha = lambda s: hashlib.sha256(s.encode("utf-8", "surrogatepass")).hexdigest()


def parse_tee(stderr, nonce):
    """-> (cleaned_stderr, info, text). info keys = capture 'tee'. Records of another nonce are foreign; any residual marker is malformed."""
    info = dict(open=False, close=False, records=0, chars=0, declared_chars=None, overflow=False, gaps=0, foreign=0, malformed=0)
    parts, nxt, text, last = [], 0, [], 0
    for m in _REC.finditer(stderr):
        parts.append(stderr[last:m.start()]); last = m.end()
        n, seq, kind, hx = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        if n != nonce: info["foreign"] += 1; continue
        info["records"] += 1
        if seq != nxt: info["gaps"] += 1
        nxt = seq + 1
        try: raw = bytes.fromhex(hx)
        except ValueError: info["malformed"] += 1; continue
        if kind == "O":
            if seq == 0 and not info["open"]: info["open"] = True
            else: info["malformed"] += 1
        elif kind == "W": text.append(raw.decode("utf-8", "surrogatepass"))
        elif kind == "X": info["overflow"] = True
        elif kind == "C":
            if info["close"]: info["malformed"] += 1
            try: info["declared_chars"] = int(raw.decode())
            except ValueError: info["malformed"] += 1
            info["close"] = True
    parts.append(stderr[last:])
    clean = "".join(parts)
    if "@@SBGV8T@@" in clean: info["malformed"] += 1  # a partial / interleaved record
    t = "".join(text)
    info["chars"] = len(t); info["sha256"] = _sha(t)
    return clean, info, t


def _stream(s, truncated): return {"len": len(s), "sha256": _sha(s), "truncated": bool(truncated)}


def judge(r, nonce, src, tee_text, tee, d):
    """Parent-side comparison for one run. -> (verdict match|no_frame|mismatch|incomplete, reasons, harness_info). `r` is the isolation Result."""
    h = {"frame": False, "stdout_len": None, "stdout_sha256": None, "stdout_trunc": None}
    if d is None: return "no_frame", ([f"no authentic result frame ({r.protocol_error or r.status})"]), h
    why = []
    so, tr = d.get("stdout"), d.get("stdout_trunc")
    if type(so) is not str or type(tr) is not bool: return "mismatch", ["harness result lacks well-formed stdout/stdout_trunc claims"], h
    h.update(frame=True, stdout_len=len(so), stdout_sha256=_sha(so), stdout_trunc=tr)
    if not (tee["open"] and tee["close"]): why.append("independent record incomplete (no open/close record: stderr closed or redirected?)")
    if tee["gaps"] or tee["foreign"] or tee["malformed"]: why.append(f"independent record corrupt (gaps={tee['gaps']} foreign={tee['foreign']} malformed={tee['malformed']})")
    if r.stderr_truncated: why.append("stderr capture truncated: the independent record may have been cut")
    dec = tee["declared_chars"]
    if dec is not None and not (tee["chars"] == dec or (tee["overflow"] and tee["chars"] == TEE_CAP and dec > TEE_CAP)): why.append("tee total does not match the closing record")
    if why: return "incomplete", why, h
    raw = tee_text[:STDOUT_CAP]
    want, want_tr = RUN.norm_parent(raw, r.workdir, src), (dec if dec is not None else tee["chars"]) > STDOUT_CAP
    if want != so or want_tr != tr:
        return "mismatch", [f"harness-reported stdout ({len(so)} chars, truncated={tr}) differs from the parent-captured program output ({len(want)} chars, truncated={want_tr})"], h
    return "match", [], h


class Supervisor:
    """Collector role. `with Supervisor(base, variant) as sup:` swaps isolation.run_script (module attribute used by runner.Ctx.run) for a wrapper in THIS
    process only and always restores it. Not thread-safe (one supervised engine run per process at a time)."""

    def __init__(self, base, variant):
        self.paths = {os.path.abspath(base): "base", os.path.abspath(variant): "variant"}
        self.session, self.runs, self.extra, self._orig = os.urandom(16).hex(), [], [], None

    def __enter__(self):
        self._orig = isolation.run_script; isolation.run_script = self._spawn
        return self

    def __exit__(self, *a):
        isolation.run_script = self._orig
        return False

    def _spawn(self, script, args=(), **kw):
        try: a = json.loads(args[0]); side = self.paths[a["src"]]; ok = os.path.abspath(script) == RUN.HARNESS and kw.get("channel") is True and len(args) == 1
        except (IndexError, KeyError, ValueError, TypeError): ok = False
        if not ok:
            self.extra.append(f"unsupervised spawn of {os.path.basename(str(script))}: no independent capture")
            return self._orig(script, args, **kw)
        nonce = os.urandom(16).hex()
        r = self._orig(STUB, [args[0], nonce], **kw)
        r.stderr, tee, text = parse_tee(r.stderr, nonce)
        d = None
        if r.payload is not None and not r.protocol_error:
            try: d = json.loads(r.payload); d = d if isinstance(d, dict) else None
            except ValueError: d = None
        verdict, why, h = judge(r, nonce, a["src"], text, tee, d)
        flooded = r.stdout_truncated or r.stderr_truncated or r.detail == "output_cap"
        if flooded: why = why + ["output flooding: capture cap exceeded (explicitly recorded, never silent)"]
        if r.status in ("TIMEOUT", "RESOURCE") or r.signal: why = why + [f"terminated: {r.status} {r.detail} signal={r.signal}"]
        self.runs.append({"seq": len(self.runs), "nonce": nonce, "mode": a["mode"], "side": side, "input_hash": R.sha(R.canon_json([a["args"], a["kwargs"]])), "ctl": a.get("ctl"),
                          "status": r.status, "detail": r.detail, "returncode": r.returncode, "signal": r.signal, "wall_s": r.wall_s, "cpu_s": r.cpu_s,
                          "fd1": _stream(r.stdout, r.stdout_truncated), "fd2": _stream(r.stderr, r.stderr_truncated), "tee": tee, "harness": h,
                          "protocol_error": r.protocol_error, "orphans_found": bool(r.orphans_found), "cleanup_verified": bool(r.cleanup_verified),
                          "flooded": bool(flooded), "verdict": verdict, "reasons": why})
        return r

    def document(self, d, cfg):
        """The v8.capture.1 document for evidence dir d (call after the engine finished writing it)."""
        reasons = [f"run {x['seq']} ({x['side']}/{x['mode']}): {w}" for x in self.runs if x["verdict"] in ("mismatch", "incomplete") for w in x["reasons"]] + self.extra
        head = json.loads(open(os.path.join(d, "evidence.jsonl")).read().splitlines()[-1])["hash"]
        return {"schema": ES.CAPTURE_V, "session": self.session, "config_sha256": R.sha(R.canon_json(cfg)), "harness_sha256": R.sha(open(RUN.HARNESS, "rb").read()),
                "stub_sha256": R.sha(open(STUB, "rb").read()), "log_head": head, "evidence_sha256": ES.sha_file(os.path.join(d, "evidence.jsonl")),
                "runs": self.runs, "trusted": not reasons and bool(self.runs), "reasons": reasons or ([] if self.runs else ["no supervised run"])}


# ---------------------------------------------------------------- decision engine role
def decide(engine_verdict, validation):
    """Pure. validation = evidence_schema.validate_dir(...). Untrusted evidence is never allowed to carry a conclusion."""
    untrusted = validation["trusted"] is False
    return {"verdict": "INSUFFICIENT" if untrusted else engine_verdict, "engine_verdict": engine_verdict, "untrusted": untrusted, "reasons": validation["reasons"]}


# ---------------------------------------------------------------- validator role in its own interpreter, authenticated reply
def _reply_mac(chan_key, nonce, result): return hmac.new(chan_key, b"sbgv8.validator.1\n" + nonce.encode() + b"\n" + R.canon_json(result).encode(), hashlib.sha256).hexdigest()


def validate_isolated(d, key=None, require_anchor=False, timeout_s=60, _cmd=None):
    """Run the validator in a fresh interpreter (the controller's patched run_script/finalize do not exist there). Request (stdin, one JSON line):
    {v, nonce, dir, chan_key, anchor_key, require_anchor}. Reply (stdout, last line): {v, nonce, result, mac=HMAC(chan_key, nonce+result)}.
    Per-call nonce and channel key prevent replay of an old (trusted) reply; any timeout/crash/garbage/bad MAC/nonce mismatch -> untrusted result."""
    nonce, ck = os.urandom(16).hex(), os.urandom(32)
    k = ES.load_key(key)
    req = {"v": 1, "nonce": nonce, "dir": os.path.abspath(d), "chan_key": ck.hex(), "anchor_key": k.hex() if k else None, "require_anchor": bool(require_anchor)}
    fail = lambda why: {"sidecar": {"status": "inconsistent", "detail": why}, "capture": {"status": "invalid", "detail": why, "reasons": [why]}, "anchor": {"status": "invalid", "detail": why},
                        "trusted": False, "reasons": [f"validator: {why}"]}
    try:
        p = subprocess.run(_cmd or [sys.executable, "-s", "-m", "sbgv8.procsep", "validate"], input=json.dumps(req), capture_output=True, text=True, timeout=timeout_s,
                           cwd=os.path.dirname(HERE), env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0"})
    except subprocess.TimeoutExpired: return fail("validator timed out")
    except OSError as e: return fail(f"validator could not start ({type(e).__name__})")
    if p.returncode != 0 or len(p.stdout) > 1 << 22: return fail(f"validator failed (exit {p.returncode})")
    try: rep = json.loads(p.stdout.strip().splitlines()[-1]); res = rep["result"]
    except (ValueError, KeyError, IndexError, TypeError): return fail("validator reply malformed")
    if not isinstance(rep, dict) or rep.get("v") != 1 or rep.get("nonce") != nonce or type(rep.get("mac")) is not str: return fail("validator reply: wrong version/nonce (replay?)")
    if not hmac.compare_digest(rep["mac"], _reply_mac(ck, nonce, res)): return fail("validator reply: bad MAC")
    if not isinstance(res, dict) or not {"trusted", "reasons", "capture", "anchor", "sidecar"} <= res.keys(): return fail("validator reply: malformed result")
    return res


def _validator_main():
    req = json.loads(sys.stdin.readline())
    res = ES.validate_dir(req["dir"], key=req["anchor_key"], require_anchor=req["require_anchor"])
    print(json.dumps({"v": 1, "nonce": req["nonce"], "result": res, "mac": _reply_mac(bytes.fromhex(req["chan_key"]), req["nonce"], res)}))


if __name__ == "__main__" and sys.argv[1:] == ["validate"]:
    _validator_main()

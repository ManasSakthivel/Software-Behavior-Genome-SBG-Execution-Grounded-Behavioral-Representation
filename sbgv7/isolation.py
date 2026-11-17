"""V7 execution isolation (D10): fresh child process per run, own process group, rlimits,
wall timeout + group kill with verified cleanup, macOS sandbox-exec network/write denial.
Nothing degrades silently: see capabilities() for what is ACTIVE vs UNAVAILABLE.

Limits (shortcuts): processes that setsid() escape the group kill; sandbox-exec is deprecated by Apple;
Linux/Docker confinement is NOT implemented (reported UNAVAILABLE)."""
import hashlib, hmac, json, os, resource, shutil, signal, subprocess, sys, tempfile, threading, time
from dataclasses import dataclass, asdict, field

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(HERE, "sandbox_darwin.sb")
CHILD = os.path.join(HERE, "_child.py")
DARWIN = sys.platform == "darwin"
_RSS_UNIT = 1 if DARWIN else 1024  # ru_maxrss: bytes on macOS, KiB on Linux


@dataclass
class Result:
    status: str  # OK | TIMEOUT | CRASH | RESOURCE | SANDBOX_UNAVAILABLE
    detail: str = ""
    returncode: int | None = None
    signal: int | None = None
    stdout: str = ""
    stderr: str = ""
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    wall_s: float = 0.0
    cpu_s: float = 0.0
    peak_rss_bytes: int = 0
    orphans_found: bool = False  # group members alive after the main child ended (then killed)
    cleanup_verified: bool = False  # killpg(pgid, 0) -> ESRCH after kill
    capabilities: dict = field(default_factory=dict)
    payload: str | None = None  # channel=True only: the HMAC-verified result frame body (never parsed from stdout/stderr)
    protocol_error: str = ""  # channel=True only: missing|malformed|truncated|oversized|duplicate|trailing|bad_mac ("" = ok)
    workdir: str = ""  # the private cwd of the run (for normalising parent-observed output)

    def to_dict(self):
        return asdict(self)


# Result protocol (local correctness fix, NOT a security boundary against a same-address-space adversary; see
# docs/architecture/V7B_RESULT_PROTOCOL.md). Trusted: this parent + _child.py + harness.py code paths. Untrusted: the evaluated
# program. The parent makes a per-run random 32-byte key, hands it to the child over a pipe that _child.py drains and closes
# before any user code runs, and reads ONE frame b"SBGV7F1 <len> <hmac-sha256-hex>\n"+payload from a dedicated result pipe.
# stdout/stderr are never protocol. Any deviation is a protocol_error (fail closed).
FRAME_MAGIC = b"SBGV7F1"


def parse_frame(key, data, cap):
    """-> (payload_str | None, error). Exactly one frame, nothing before or after, MAC must verify under the per-run key."""
    if not data:
        return None, "missing"
    nl = data.find(b"\n", 0, 128)
    parts = data[:nl].split(b" ") if nl >= 0 else []
    if len(parts) != 3 or parts[0] != FRAME_MAGIC or not parts[1].isdigit() or len(parts[1]) > 12 or len(parts[2]) != 64:
        return None, "malformed"
    n = int(parts[1])
    if n > cap:
        return None, "oversized"
    body = data[nl + 1:]
    if len(body) < n:
        return None, "truncated"
    if len(body) > n:
        return None, "duplicate" if body[n:].startswith(FRAME_MAGIC) else "trailing"
    if not hmac.compare_digest(hmac.new(key, body, hashlib.sha256).hexdigest().encode(), parts[2]):
        return None, "bad_mac"
    return body.decode("utf-8", "replace"), ""


def _sandbox_cmd(workdir):
    return ["/usr/bin/sandbox-exec", "-f", PROFILE, "-D", f"WORKDIR={os.path.realpath(workdir)}"]


def _group_rss(pgid):
    out = subprocess.run(["ps", "-axo", "pgid=,rss="], capture_output=True, text=True).stdout
    return sum(int(r) * 1024 for g, r in (l.split() for l in out.splitlines() if l.strip()) if int(g) == pgid)


def _alive(pgid):
    try:
        os.killpg(pgid, 0); return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _kill_group(pgid):
    """SIGKILL the group and verify nobody is left (<=3 s)."""
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except PermissionError:  # macOS zombie group; fall through to the liveness check
        pass
    end = time.monotonic() + 3
    while time.monotonic() < end:
        if not _alive(pgid):
            return True
        time.sleep(0.02)
    return False


def _run(cfg, *, timeout_s, mem_mb, out_cap, sandbox, workdir, caps, channel=False):
    t0 = time.monotonic()
    own_wd = workdir is None
    workdir = workdir or tempfile.mkdtemp(prefix="sbgv7_")
    try:
        if sandbox and caps["network_denial"]["state"] != "ACTIVE":
            return Result("SANDBOX_UNAVAILABLE", caps["network_denial"]["detail"], capabilities=caps)
        lim = {}
        for key, name, val in (("rlimit_cpu", "RLIMIT_CPU", cfg.pop("cpu_s")), ("rlimit_as", "RLIMIT_AS", mem_mb * 2**20),
                               ("rlimit_nofile", "RLIMIT_NOFILE", cfg.pop("nofile")), ("rlimit_fsize", "RLIMIT_FSIZE", cfg.pop("fsize_mb") * 2**20)):
            if caps[key]["state"] == "ACTIVE":
                lim[name] = int(val)
        lim["RLIMIT_CORE"] = 0
        cfg["limits"] = lim
        cmd = (_sandbox_cmd(workdir) if sandbox else []) + [sys.executable, "-s", "-P", "-B", CHILD, json.dumps(cfg)]
        env = child_env(workdir)
        key, chan_fds, keep = os.urandom(32), None, ()
        if channel:
            rr, rw = os.pipe(); kr, kw = os.pipe()
            os.write(kw, key); os.close(kw)  # 32 bytes fit the pipe buffer; the child reads to EOF then closes kr
            cfg["chan"] = {"w": rw, "k": kr}; keep = (rw, kr); chan_fds = (rr, rw, kr)
            cmd = (_sandbox_cmd(workdir) if sandbox else []) + [sys.executable, "-s", "-P", "-B", CHILD, json.dumps(cfg)]
        try:
            p = subprocess.Popen(cmd, cwd=workdir, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True, pass_fds=keep)
        finally:
            for fd in (chan_fds[1:] if chan_fds else ()): os.close(fd)  # parent keeps only the read end
        frame, fcap = bytearray(), [False]

        def pump_frame():
            with os.fdopen(chan_fds[0], "rb", buffering=0) as f:
                while chunk := f.read(65536):
                    if len(frame) <= out_cap + 256: frame.extend(chunk)
                    else: fcap[0] = True  # keep draining, discard
        pgid = p.pid
        bufs = {"o": [bytearray(), 0], "e": [bytearray(), 0]}
        capped = threading.Event()

        def pump(f, b):
            while chunk := f.read1(65536):
                b[1] += len(chunk)
                if len(b[0]) < out_cap:
                    b[0] += chunk[: out_cap - len(b[0])]
                if b[1] > out_cap:
                    capped.set()  # keep draining so the child is never blocked; parent kills on cap

        ts = [threading.Thread(target=pump, args=(p.stdout, bufs["o"]), daemon=True),
              threading.Thread(target=pump, args=(p.stderr, bufs["e"]), daemon=True)]
        if channel: ts.append(threading.Thread(target=pump_frame, daemon=True))
        [t.start() for t in ts]
        reason, peak, status_raw, ru = "", 0, None, None
        deadline, nextrss = t0 + timeout_s, 0
        while True:
            pid, st, ru = os.wait4(p.pid, os.WNOHANG)
            if pid:
                status_raw = st; break
            now = time.monotonic()
            if now > deadline:
                reason = "TIMEOUT"
            elif capped.is_set():
                reason = "RESOURCE:output_cap"
            elif now >= nextrss:
                nextrss = now + 0.1
                rss = _group_rss(pgid); peak = max(peak, rss)
                if rss > mem_mb * 2**20:
                    reason = "RESOURCE:rss_watchdog"
            if reason:
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):  # macOS: group already exiting/zombie
                    pass
                _, status_raw, ru = os.wait4(p.pid, 0)
                break
            time.sleep(0.01)
        wall = time.monotonic() - t0
        orphans = _alive(pgid)
        cleaned = _kill_group(pgid)
        [t.join(2) for t in ts]
        sig = os.WTERMSIG(status_raw) if os.WIFSIGNALED(status_raw) else None
        rc = os.WEXITSTATUS(status_raw) if os.WIFEXITED(status_raw) else None
        so, se = bytes(bufs["o"][0]).decode("utf-8", "replace"), bytes(bufs["e"][0]).decode("utf-8", "replace")
        if reason == "TIMEOUT":
            status, detail = "TIMEOUT", f"wall > {timeout_s}s; group killed"
        elif reason:
            status, detail = "RESOURCE", reason.split(":")[1]
        elif sig in (signal.SIGXCPU, signal.SIGXFSZ):
            status, detail = "RESOURCE", signal.Signals(sig).name
        elif sig == signal.SIGKILL and ru.ru_utime + ru.ru_stime >= cfg.get("_cpu", 1e9):
            status, detail = "RESOURCE", "cpu_rlimit"
        elif "MemoryError" in se:
            status, detail = "RESOURCE", "MemoryError (rlimit_as)"
        elif "SBGV7_LIMIT_FAIL" in se:
            status, detail = "CRASH", "rlimit could not be applied"
        elif rc == 0:
            status, detail = "OK", ""
        else:
            status, detail = "CRASH", f"signal {sig}" if sig else f"exit {rc}"
        payload, perr = (None, "")
        if channel:
            payload, perr = (None, "oversized") if fcap[0] else parse_frame(key, bytes(frame), out_cap)
        return Result(status, detail, rc, sig, so, se, bufs["o"][1] > out_cap, bufs["e"][1] > out_cap, wall,
                      ru.ru_utime + ru.ru_stime, max(peak, ru.ru_maxrss * _RSS_UNIT), orphans, cleaned, caps, payload, perr, workdir)
    finally:
        if own_wd:
            shutil.rmtree(workdir, ignore_errors=True)


def run_script(script, args=(), *, timeout_s=10, cpu_s=10, mem_mb=512, nofile=256, fsize_mb=16,
               out_cap=65536, sandbox=True, workdir=None, channel=False) -> Result:
    cfg = dict(script=os.path.abspath(script), args=list(args), cpu_s=cpu_s, nofile=nofile, fsize_mb=fsize_mb, _cpu=cpu_s)
    return _run(cfg, timeout_s=timeout_s, mem_mb=mem_mb, out_cap=out_cap, sandbox=sandbox, workdir=workdir, caps=capabilities(), channel=channel)


def run_callable(func, args=(), **kw) -> Result:
    """func must be an importable module-level function (or 'mod:qual' string); args/return must be JSON; return value is stdout JSON."""
    kw_ = dict(timeout_s=10, cpu_s=10, mem_mb=512, nofile=256, fsize_mb=16, out_cap=65536, sandbox=True, workdir=None)
    kw_.update(kw)
    if isinstance(func, str):
        spec, path = func, os.getcwd()
    else:
        spec = f"{func.__module__}:{func.__qualname__}"
        path = os.path.dirname(os.path.abspath(sys.modules[func.__module__].__file__))
    cfg = dict(callable=spec, path=path, args=list(args), cpu_s=kw_.pop("cpu_s"), nofile=kw_.pop("nofile"),
               fsize_mb=kw_.pop("fsize_mb")); cfg["_cpu"] = cfg["cpu_s"]
    return _run(cfg, timeout_s=kw_["timeout_s"], mem_mb=kw_["mem_mb"], out_cap=kw_["out_cap"], sandbox=kw_["sandbox"],
                workdir=kw_["workdir"], caps=capabilities())


_PROBE = r'''
import json, os, socket, sys
k = sys.argv[1]; wd = os.getcwd(); out = {}
if k == "cpu":
    while True: pass
if k == "as":
    try: bytearray(150 * 2**20); out["ok"] = 1
    except MemoryError: out["ok"] = 0
if k == "nofile":
    fs = []
    try:
        for _ in range(100): fs.append(open(os.devnull))
        out["ok"] = 1
    except OSError: out["ok"] = 0
if k == "fsize":
    try:
        with open("f", "wb") as f: f.write(b"x" * 2**20 * 2); f.flush()
        out["ok"] = 1
    except OSError: out["ok"] = 0
if k == "sbx":
    s = socket.socket()
    try: s.connect(("127.0.0.1", 1)); out["net"] = "connected"
    except PermissionError: out["net"] = "denied"
    except OSError: out["net"] = "allowed(refused)"
    d = os.path.join(os.path.dirname(wd), "sbgv7_outside_probe_" + str(os.getpid()))
    try: open(d, "w").close(); os.unlink(d); out["write"] = "allowed"
    except PermissionError: out["write"] = "denied"
    try: open("inside", "w").close(); out["inside"] = "ok"
    except OSError: out["inside"] = "failed"
print(json.dumps(out))
'''
_CAPS = None
# SD-09 (I1, X6) determinism control profile of every child. NOT `-I`/`-E` for the interpreter: both make it ignore PYTHONHASHSEED (the hash
# seed is read once at start-up, so it can only arrive via the environment). Safety instead comes from child_env(): an allowlist built from
# scratch (nothing inherited), so no PYTHON*/LD_*/DYLD_* variable of the parent can reach the child; `-s -P` (and PYTHONNOUSERSITE/PYTHONSAFEPATH,
# redundant on purpose) keep user site and cwd/script dir off sys.path. LOCAL environment control, NOT validated OS isolation.
# datetime.now()/today() are NOT virtualised (SD-09); see docs/architecture/V7B_IMPLEMENTATION.md "Determinism" table.
DET_ENV = {"PYTHONHASHSEED": "0", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8:strict", "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
           "TZ": "UTC", "LC_ALL": "C.UTF-8", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def child_env(workdir):
    """The complete environment of every child (explicit allowlist; os.environ is never read)."""
    return {"PATH": "/usr/bin:/bin", "HOME": workdir, "TMPDIR": workdir, "PYTHONDONTWRITEBYTECODE": "1", **DET_ENV}


# SD-07 (A-01): a run is sandbox_ok only if every REQUIRED property is ACTIVE; ADVISORY ones only flag policy_below_minimum.
REQUIRED = ("network_denial", "write_confinement", "process_group_kill", "rlimit_cpu", "rlimit_fsize", "rlimit_nofile")
ADVISORY = ("rlimit_as", "rlimit_nproc")


def capabilities(refresh=False):
    """Probe (once) which controls actually enforce here. Each entry: {state: ACTIVE|UNAVAILABLE, detail}."""
    global _CAPS
    if _CAPS and not refresh:
        return _CAPS
    wd = tempfile.mkdtemp(prefix="sbgv7_cap_")
    try:
        probe = os.path.join(wd, "probe.py"); open(probe, "w").write(_PROBE)
        none = {k: {"state": "UNAVAILABLE", "detail": "probing"} for k in
                ("rlimit_cpu", "rlimit_as", "rlimit_nofile", "rlimit_fsize")}
        none["network_denial"] = none["rlimit_cpu"]
        base = {k: dict(v) for k, v in none.items()}
        for k in base:
            base[k]["state"] = "ACTIVE"
        sub = os.path.join(wd, "w"); os.mkdir(sub)

        def go(kind, cpu_s=10, mem=64, sandbox=False, to=8):
            only = {"cpu": "rlimit_cpu", "as": "rlimit_as", "nofile": "rlimit_nofile", "fsize": "rlimit_fsize"}.get(kind)
            c = {k: dict(v, state="ACTIVE" if k in (only, "network_denial") else "UNAVAILABLE") for k, v in base.items()}
            cfg = dict(script=probe, args=[kind], cpu_s=cpu_s, nofile=20, fsize_mb=1, _cpu=cpu_s)
            return _run(cfg, timeout_s=to, mem_mb=mem, out_cap=4096, sandbox=sandbox, workdir=sub, caps=c)

        caps = {}
        r = go("cpu", cpu_s=1, to=6)
        caps["rlimit_cpu"] = _state("LIMIT_FAIL" not in r.stderr and r.status == "RESOURCE" and r.wall_s < 5, f"spin killed: {r.status}/{r.detail} after {r.wall_s:.1f}s")
        for key, kind, why in (("rlimit_as", "as", "150MB alloc under 64MB cap"), ("rlimit_nofile", "nofile", "100 opens under cap 20"),
                               ("rlimit_fsize", "fsize", "2MB write under 1MB cap")):
            r = go(kind)
            caps[key] = _state("LIMIT_FAIL" not in r.stderr and (r.status != "OK" or '"ok": 0' in r.stdout), f"{why}: {r.status}/{r.detail} {r.stdout.strip()} {r.stderr.strip()[-120:]}")
        caps["rlimit_nproc"] = {"state": "UNAVAILABLE", "detail": "not applied: RLIMIT_NPROC is a per-user process count (macOS) and enforcement was not verified"}
        caps["process_group_kill"] = {"state": "ACTIVE", "detail": "start_new_session + killpg(SIGKILL) + ESRCH verification (setsid escapes not covered)"}
        caps["rss_watchdog"] = {"state": "ACTIVE", "detail": "parent polls group RSS via ps every 100ms; kills over mem_mb (polling, not hard)"}
        if DARWIN and os.path.exists("/usr/bin/sandbox-exec"):
            r = go("sbx", sandbox=True)
            try:
                o = json.loads(r.stdout)
            except ValueError:
                o = {}
            caps["network_denial"] = _state(o.get("net") == "denied", f"probe: {o or r.stderr[-200:]}")
            caps["write_confinement"] = _state(o.get("write") == "denied" and o.get("inside") == "ok", f"probe: {o or r.stderr[-200:]}")
        else:
            for k in ("network_denial", "write_confinement"):
                caps[k] = {"state": "UNAVAILABLE", "detail": "no sandbox-exec; Linux/Docker path not implemented/untested"}
        _CAPS = {"platform": sys.platform, "python": sys.version.split()[0], **caps}
        return _CAPS
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def _state(ok, detail):
    return {"state": "ACTIVE" if ok else "UNAVAILABLE", "detail": detail}


if __name__ == "__main__":
    print(json.dumps(capabilities(), indent=1))

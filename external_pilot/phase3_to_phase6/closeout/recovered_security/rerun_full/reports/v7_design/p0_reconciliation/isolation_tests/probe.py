"""One probe per process: python probe.py <name>. Prints one JSON line. Run via run_all.py only."""
import json, os, sys, time, threading, socket, subprocess, tempfile, resource
REPO = os.environ["SBG_REPO"]; sys.path.insert(0, REPO)
from sbg.v2.execution.runner import SandboxRunner
TMP = os.environ["PROBE_TMP"]
R = SandboxRunner()
def run(f, inputs=(0,), **k):
    return R.run("probe", f, list(inputs), n_runs=1, timeout_s=k.pop("timeout_s", 2.0), **k)
def tr(res): return [t for r in res.traces for t in r]
def exc(res): return [t.exception for t in tr(res)]
out = {}
name = sys.argv[1]

if name == "pid":
    seen = {}
    def f(_):
        seen.update(pid=os.getpid(), ppid=os.getppid(), thread=threading.current_thread().name,
                    main=threading.current_thread() is threading.main_thread())
    run(f); out = dict(seen, host_pid=os.getpid(), host_ppid=os.getppid())

elif name == "spin":
    def f(_):
        while True: pass
    c0 = time.process_time(); t0 = time.monotonic()
    res = run(f, timeout_s=1.0); ret = time.monotonic() - t0
    c1 = time.process_time(); time.sleep(2.0); c2 = time.process_time()
    out = dict(returned_after_s=round(ret, 2), exc=exc(res), threads_after=[t.name for t in threading.enumerate()],
               n_threads=threading.active_count(), cpu_during_s=round(c1 - c0, 2),
               cpu_in_2s_idle_after_return=round(c2 - c1, 2))

elif name == "leak":
    def f(_):
        while True: pass
    c0 = time.process_time(); t0 = time.monotonic(); samples = []
    for i in range(20):
        run(f, timeout_s=0.2)
        if i in (0, 4, 9, 19): samples.append((i + 1, threading.active_count(), round(time.process_time() - c0, 2)))
    wall = time.monotonic() - t0; c1 = time.process_time(); time.sleep(1.0)
    out = dict(samples_runs_threads_cpu=samples, wall_s=round(wall, 2), threads=threading.active_count(),
               cpu_1s_idle_after=round(time.process_time() - c1, 2))

elif name == "rlimit":
    seen = {}
    def f(_):
        for n in ("RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_DATA", "RLIMIT_NPROC", "RLIMIT_NOFILE", "RLIMIT_FSIZE", "RLIMIT_STACK"):
            seen[n] = [("inf" if v == resource.RLIM_INFINITY else v) for v in resource.getrlimit(getattr(resource, n))]
        seen["recursionlimit"] = sys.getrecursionlimit()
    run(f); out = seen

elif name == "child":
    pidf = os.path.join(TMP, "child.pid")
    def f(_):
        p = subprocess.Popen(["sleep", "2"]); open(pidf, "w").write(str(p.pid))
    res = run(f); time.sleep(0.2)
    pid = int(open(pidf).read())
    try: os.kill(pid, 0); alive = True
    except OSError: alive = False
    ps = subprocess.run(["ps", "-o", "pid,ppid,etime,command", "-p", str(pid)], capture_output=True, text=True).stdout
    out = dict(child_pid=pid, alive_after_runner_returned=alive, exc=exc(res), ps=ps)
    time.sleep(2.2)

elif name == "net":
    seen = {}
    def f(_):
        s = socket.socket(); s.settimeout(1)
        try: s.connect(("127.0.0.1", 1)); seen["connect"] = "CONNECTED"
        except Exception as e: seen["connect"] = f"{type(e).__name__}: {e}"
        try: socket.getaddrinfo("sbg-probe-nonexistent.invalid", 80); seen["dns"] = "RESOLVED"
        except Exception as e: seen["dns"] = f"{type(e).__name__}: {e}"
    run(f); out = seen

elif name == "fs":
    seen = {}
    def f(_):
        try: seen["read_etc_hosts_bytes"] = len(open("/etc/hosts").read())
        except Exception as e: seen["read_etc_hosts"] = repr(e)
        for label, p in (("cwd", os.path.join(os.getcwd(), "probe_write.txt")), ("tmp", os.path.join(TMP, "w.txt"))):
            try: open(p, "w").write("x"); seen["write_" + label] = "OK"; os.remove(p)
            except Exception as e: seen["write_" + label] = repr(e)
        seen["cwd"] = os.getcwd()
        seen["env_keys_visible"] = len(os.environ)
    run(f); out = seen

elif name == "malformed":
    CASE = sys.argv[2] if len(sys.argv) > 2 else None
    def raises(_): raise ValueError("boom")
    def rec(_): return rec(_)
    def sysexit(_): sys.exit(3)
    def kbd(_): raise KeyboardInterrupt()
    def genexit(_): raise GeneratorExit()
    def evade(_):
        sys.settrace(None); x = 0
        for i in range(50): x += i
        return x
    def evade2(_):
        sys.settrace(lambda *a: None); return sum(range(50))
    for lbl, f in (("ValueError", raises), ("recursion", rec), ("evade_settrace_None", evade), ("evade_settrace_noop", evade2)):
        if CASE and lbl != CASE: continue
        try:
            res = run(f); t = tr(res)[0]
            out[lbl] = dict(exc=t.exception, n_events=len(t.events), truncated=t.truncated, ret=t.return_value)
        except BaseException as e: out[lbl] = "HOST_RAISED " + repr(e)
    for lbl, f in (("SystemExit", sysexit), ("KeyboardInterrupt", kbd), ("GeneratorExit", genexit)):
        if CASE and lbl != CASE: continue
        t0 = time.monotonic()
        try:
            res = run(f, timeout_s=1.0); t = tr(res)[0]
            out[lbl] = dict(host_raised=False, exc=t.exception, wall_s=round(time.monotonic() - t0, 2))
        except BaseException as e: out[lbl] = "HOST_RAISED " + repr(e)
    out["threads_after"] = [t.name for t in threading.enumerate()]

elif name == "osexit":
    print("HOST_ALIVE_BEFORE", flush=True)
    def f(_): os._exit(7)
    run(f)
    print("HOST_ALIVE_AFTER", flush=True)  # must not appear if host died
    out = {"host_survived": True}

print("RESULT " + json.dumps(out, default=str))

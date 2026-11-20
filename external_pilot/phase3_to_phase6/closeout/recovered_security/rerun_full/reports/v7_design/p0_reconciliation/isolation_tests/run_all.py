"""Driver: each probe in its own child process group, ulimit -t/-v set here, hard wall kill, temp dir, ps check after."""
import os, signal, subprocess, sys, tempfile, shutil, json
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
PROBES = [("pid", 20), ("spin", 30), ("leak", 40), ("rlimit", 20), ("child", 30), ("net", 30), ("fs", 20), ("malformed ValueError", 20), ("malformed recursion", 40), ("malformed evade_settrace_None", 20), ("malformed evade_settrace_noop", 20), ("malformed SystemExit", 20), ("malformed KeyboardInterrupt", 20), ("malformed GeneratorExit", 20), ("osexit", 20)]
tmp = tempfile.mkdtemp(prefix="sbg_iso_"); results = {}
ONLY = sys.argv[1:]
for name, wall in PROBES:
    if ONLY and name.split()[0] not in ONLY: continue
    # ulimit -t 120 CPU seconds; -v attempted (macOS may ignore/refuse -> '|| true'); cwd = temp dir
    cmd = f'ulimit -t 120; ulimit -v 4000000 2>/dev/null || true; exec ${{PY:-python3}} -I {HERE}/probe.py {name}'
    env = {"PY": os.environ.get("PY", "python3"), "PATH": os.environ["PATH"], "SBG_REPO": REPO, "PROBE_TMP": tmp, "PYTHONDONTWRITEBYTECODE": "1"}
    p = subprocess.Popen(["/bin/sh", "-c", cmd], cwd=tmp, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try: out, _ = p.communicate(timeout=wall); killed = False
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); out, _ = p.communicate(); killed = True
    res = [l for l in out.splitlines() if l.startswith("RESULT ")]
    print(f"=== {name} rc={p.returncode} wall_killed={killed}")
    print("\n".join(l for l in out.splitlines() if not l.startswith("RESULT ") )[-1500:])
    print(res[0][7:] if res else "NO RESULT")
    # stray check: anything left in that process group
    left = subprocess.run(["pgrep", "-g", str(p.pid)], capture_output=True, text=True).stdout.split()
    if left:
        print("STRAY in pgid:", left); os.killpg(p.pid, signal.SIGKILL)
shutil.rmtree(tmp, ignore_errors=True)
print("stray 'sleep 2'/probe.py:", subprocess.run("ps -axo pid,etime,command | grep -E 'probe.py|sleep 2' | grep -v grep", shell=True, capture_output=True, text=True).stdout or "none")

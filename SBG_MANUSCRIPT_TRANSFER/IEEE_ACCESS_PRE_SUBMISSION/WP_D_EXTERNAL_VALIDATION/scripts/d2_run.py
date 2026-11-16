#!/usr/bin/env python3
"""WP-D / D2 command runner (stdlib only).

Runs ONE shell command with a hard timeout and appends a record (exact command,
cwd, exit code, runtime, stdout/stderr log path) to
raw/WPD-D2_repro/command_log.jsonl.

    d2_run.py --tag TAG --timeout SECONDS [--cwd DIR] [--env K=V ...] -- <command...>

The command is passed to `bash -c`, so it is logged exactly as executed.
Exit code 124 is recorded on timeout (the whole process group is killed).
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time

D2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "WPD-D2_repro")
D2 = os.path.normpath(D2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--timeout", type=float, required=True)
    ap.add_argument("--cwd", default=D2)
    ap.add_argument("--env", action="append", default=[])
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    command = " ".join(cmd)
    env = dict(os.environ)
    env.setdefault("PYTHONHASHSEED", "0")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    for kv in a.env:
        k, v = kv.split("=", 1)
        env[k] = v
    os.makedirs(os.path.join(D2, "logs"), exist_ok=True)
    log_path = os.path.join(D2, "logs", f"{a.tag}.log")
    t0 = time.time()
    load_start = os.getloadavg()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(log_path, "w") as log:
        proc = subprocess.Popen(["bash", "-c", command], cwd=a.cwd, env=env, stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            rc = 124
    rec = {"tag": a.tag, "command": command, "cwd": a.cwd, "env_overrides": a.env,
           "PYTHONHASHSEED": env["PYTHONHASHSEED"], "started": started,
           "exit_code": rc, "timed_out": rc == 124, "runtime_s": round(time.time() - t0, 2),
           "timeout_s": a.timeout, "loadavg_start": [round(x, 1) for x in load_start],
           "loadavg_end": [round(x, 1) for x in os.getloadavg()], "log": os.path.relpath(log_path, D2)}
    with open(os.path.join(D2, "command_log.jsonl"), "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return rc


if __name__ == "__main__":
    sys.exit(main())

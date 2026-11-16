#!/usr/bin/env python3
"""WP-D / D2: generate raw/WPD-D2_repro/REPRODUCE.sh from command_log.jsonl (only commands actually run)."""
import json, os
D2 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "WPD-D2_repro"))
S = os.path.normpath(os.path.join(D2, "..", "..", "..", ".."))
out = ["#!/usr/bin/env bash",
       "# GENERATED from raw/WPD-D2_repro/command_log.jsonl by scripts/d2_make_reproduce_sh.py.",
       "# Every line below is a command that WAS executed (exit code and runtime in the trailing comment).",
       "# Each command ran via scripts/d2_run.py with PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 unless noted.",
       "# Paths are the absolute paths used. Commands run with the cwd given on the '# cwd' line.",
       "# NOT a one-shot script: B0 creates sbg_copy/ and runs/* copies first; later steps depend on earlier outputs.",
       "set -u",
       f"S={S}", ""]
for l in open(os.path.join(D2, "command_log.jsonl")):
    d = json.loads(l)
    cmd = d["command"].replace(S, "$S")
    cwd = d["cwd"].replace(S, "$S")
    envs = " ".join(d["env_overrides"]) or f"PYTHONHASHSEED={d.get('PYTHONHASHSEED')}"
    out.append(f"# [{d['tag']}] rc={d['exit_code']}{' TIMEOUT' if d['timed_out'] else ''} runtime={d['runtime_s']}s "
               f"started={d['started']} load_start={d.get('loadavg_start')}")
    out.append(f"# cwd: {cwd}   env: {envs}")
    out.append(f"(cd \"{cwd}\" && env {envs} PYTHONDONTWRITEBYTECODE=1 timeout {int(d['timeout_s'])} bash -c '{cmd}')")
    out.append("")
open(os.path.join(D2, "REPRODUCE.sh"), "w").write("\n".join(out) + "\n")
print("wrote", len(out), "lines")

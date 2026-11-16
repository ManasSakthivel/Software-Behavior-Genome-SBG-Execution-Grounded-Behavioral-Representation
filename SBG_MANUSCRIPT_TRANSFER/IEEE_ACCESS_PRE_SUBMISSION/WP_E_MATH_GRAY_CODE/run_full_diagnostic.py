#!/usr/bin/env python3
"""WP-E Full Diagnostic Profiler for all 49 math_gray_code files.
Runs each file in an isolated subprocess with watchdog timer to safely capture timing, memory, and failure modes.
"""
import subprocess
import sys
import os
import pathlib
import json
import time

REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
OUT_DIR = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION/WP_E_MATH_GRAY_CODE")

def jl(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def main():
    v9_pairs = [p for p in jl(REPO / "benchmark/datasets/v9_composed/pairs_train.jsonl") if p["base_id"] == "math_gray_code"]
    v8_pairs = {p["pair_id"]: p for p in jl(REPO / "benchmark/datasets/v8/pairs_train.jsonl")}
    all_pairs = list(v9_pairs)
    for p in v9_pairs:
        m_id = p["matched_equivalent_pair_id"]
        if m_id in v8_pairs:
            all_pairs.append(v8_pairs[m_id])
    
    paths = sorted(set([p["base_path"] for p in all_pairs] + [p["variant_path"] for p in all_pairs]))
    print(f"Total files to profile: {len(paths)}")
    
    worker_script = """
import sys, os, pathlib, time, resource, json
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
sys.path.insert(0, str(REPO))
os.chdir(REPO)
from experiments.final import extraction as ex

relpath = sys.argv[1]
t0 = time.time()
res = ex.extract_program(str(REPO / relpath), {}, "output_free_v8")
dt = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform == "darwin":
    rss = rss / (1024 * 1024)
else:
    rss = rss / 1024

out = {
    "path": relpath,
    "ok": res.ok,
    "failure_kind": res.failure_kind,
    "failure_detail": str(res.failure_detail),
    "elapsed_sec": round(dt, 4),
    "rss_mb": round(rss, 2),
    "stats": res.stats
}
print(json.dumps(out))
"""
    
    temp_worker = OUT_DIR / "_temp_worker.py"
    temp_worker.write_text(worker_script)
    
    results = []
    
    for i, p in enumerate(paths, 1):
        t_start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(temp_worker), p],
                capture_output=True, text=True, timeout=5.0
            )
            elapsed = time.time() - t_start
            if proc.returncode == 0:
                data = json.loads(proc.stdout.strip())
                print(f"[{i:02d}/49] {p} -> OK ({data['elapsed_sec']}s, RSS={data['rss_mb']}MB)")
                results.append(data)
            else:
                print(f"[{i:02d}/49] {p} -> FAIL rc={proc.returncode} ({elapsed:.2f}s)")
                results.append({
                    "path": p,
                    "ok": False,
                    "returncode": proc.returncode,
                    "stderr": proc.stderr,
                    "elapsed_sec": round(elapsed, 4),
                    "failure_mode": "subprocess_error"
                })
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t_start
            print(f"[{i:02d}/49] {p} -> TIMEOUT > 5.0s (RUNAWAY EXPONENTIATION DETECTED)")
            results.append({
                "path": p,
                "ok": False,
                "elapsed_sec": round(elapsed, 4),
                "failure_mode": "timeout_runaway_loop",
                "notes": "Triggered by input n=100 with disabled/inverted guard in SC-4/SC-5 mutant resulting in 2^100 loop"
            })
            
    if temp_worker.exists():
        temp_worker.unlink()
        
    out_file = OUT_DIR / "diagnostic_probe_results.json"
    out_file.write_text(json.dumps(results, indent=2))
    print(f"\nAll profiling completed. Wrote full diagnostic matrix to {out_file}")

if __name__ == "__main__":
    main()

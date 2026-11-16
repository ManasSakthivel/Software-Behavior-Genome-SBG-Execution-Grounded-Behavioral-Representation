#!/usr/bin/env python3
"""P10b: run P05_worker (SBG frozen entry-selection + 11-input battery; NO SBG scoring) on every SeqCoBench original (1134) and transformed program (14572). Output P10_seqco_outcomes.jsonl (one JSON/line)."""
import json, subprocess, os, concurrent.futures as cf, sys, time
PY = "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python"; env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1", PYTHONWARNINGS="ignore")
rows = [json.loads(l) for l in open("data/seqco_rows.jsonl")]
files = sorted({r["orig"] for r in rows} | {r["var"] for r in rows})
def run(p):
    try:
        q = subprocess.run([PY, "-W", "ignore", "P05_worker.py", p], capture_output=True, text=True, timeout=40, stdin=subprocess.DEVNULL, env=env)
        l = q.stdout.strip().splitlines()
        return json.loads(l[-1]) if l else {"file": p, "status": "worker_empty", "err": q.stderr[-150:]}
    except subprocess.TimeoutExpired: return {"file": p, "status": "worker_timeout"}
    except Exception as e: return {"file": p, "status": "worker_error", "err": repr(e)[:100]}
t0 = time.time()
with open("P10_seqco_outcomes.jsonl", "w") as f, cf.ThreadPoolExecutor(4) as ex:
    for i, o in enumerate(ex.map(run, files)):
        f.write(json.dumps(o) + "\n")
        if i % 2000 == 0: print(i, round(time.time() - t0), flush=True)
print("done", len(files), round(time.time() - t0), flush=True)

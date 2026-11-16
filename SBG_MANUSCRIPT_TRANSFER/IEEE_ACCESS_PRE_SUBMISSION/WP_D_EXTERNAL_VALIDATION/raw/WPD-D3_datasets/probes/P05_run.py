#!/usr/bin/env python3
"""P05 driver: label-observability audit on SBG's 11-input battery. Log: P05_*.json. Python = SBG canonical 3.13 interpreter."""
import subprocess, json, sys, glob, os, collections, hashlib, concurrent.futures as cf, time
PY = "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python"
env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
def run(path):
    try:
        p = subprocess.run([PY, "P05_worker.py", path], capture_output=True, text=True, timeout=40, stdin=subprocess.DEVNULL, env=env)
        line = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
        return json.loads(line) if line else {"file": path, "status": "worker_empty", "err": p.stderr[-200:]}
    except subprocess.TimeoutExpired: return {"file": path, "status": "worker_timeout"}
    except Exception as e: return {"file": path, "status": "worker_error", "err": repr(e)[:100]}
t0 = time.time()
# ---- HumanEvalPack: write canonical/buggy sources to disk
rows = json.load(open("data/humanevalpack_python.json")); os.makedirs("data/hep_src", exist_ok=True); jobs = []
for r in rows:
    tid = r["task_id"].split("/")[1]
    for kind, body in (("canonical", r["canonical_solution"]), ("buggy", r["buggy_solution"])):
        f = f"data/hep_src/{tid}_{kind}.py"; open(f, "w").write(r["declaration"] + body + "\n"); jobs.append(f)
if not os.path.exists("P05_hep_outcomes.json"):
    with cf.ThreadPoolExecutor(4) as ex: hep = list(ex.map(run, jobs))
    json.dump(hep, open("P05_hep_outcomes.json", "w"))
else: hep = json.load(open("P05_hep_outcomes.json"))  # (first launch completed HEP; driver was killed during Refactory; re-launched)
# ---- Refactory
rjobs = sorted(f for k in ("reference","correct","wrong") for f in glob.glob(f"data/refactory/data/question_*/code/{k}/*.py"))  # "fail" subfolder (undocumented in README) not scored
with cf.ThreadPoolExecutor(4) as ex: ref = list(ex.map(run, rjobs))
json.dump(ref, open("P05_refactory_outcomes.json", "w"))
print("done", len(hep), len(ref), round(time.time() - t0), "s")

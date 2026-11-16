#!/usr/bin/env python3
"""P07b: battery-outcome equality canonical vs minified variant (validation of EQUIVALENT negatives by differential execution on SBG's 11 inputs). No SBG scoring."""
import json, subprocess, os, concurrent.futures as cf, collections
PY = "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python"; env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
def run(p):
    q = subprocess.run([PY, "P05_worker.py", p], capture_output=True, text=True, timeout=40, stdin=subprocess.DEVNULL, env=env); return json.loads(q.stdout.strip().splitlines()[-1])
rec = json.load(open("P07_minify.json")); canon = {o["file"].split("/")[-1][:-len("_canonical.py")]: o for o in json.load(open("P05_hep_outcomes.json")) if o["file"].endswith("_canonical.py")}
tasks = [t for t in rec["tasks"] if t["compiles"]]
with cf.ThreadPoolExecutor(4) as ex: mins = list(ex.map(run, [f"data/hep_min/{t['task']}_min.py" for t in tasks]))
st = collections.Counter(); bad = []
for t, m in zip(tasks, mins):
    c = canon[t["task"]]
    if m["status"] != "ok": st["min_" + m["status"]] += 1; bad.append((t["task"], m["status"])); continue
    if c["outcomes"] == m["outcomes"]: st["outcomes_equal"] += 1
    else: st["outcomes_DIFFER"] += 1; bad.append((t["task"], "differ", m["entry"], c["entry"]))
    st["ast_differs&equal"] += int(t["ast_differs"] and c["outcomes"] == m["outcomes"])
res = {"counts": dict(st), "anomalies": bad}; json.dump(res, open("P07b_minify_behaviour.json", "w"), indent=1); print(res)

#!/usr/bin/env python3
"""P06: analyse P05 HumanEvalPack outcomes: how many human-written bugs are OBSERVABLE (outcome signature differs) on SBG's frozen 11-input battery.
Output P06_hep_observability.json. No SBG scoring."""
import json, collections
out = json.load(open("P05_hep_outcomes.json")); rows = {r["task_id"].split("/")[1]: r for r in json.load(open("data/humanevalpack_python.json"))}
by = collections.defaultdict(dict)
for o in out:
    n = o["file"].split("/")[-1][:-3]; tid, kind = n.rsplit("_", 1); by[tid][kind] = o
res = {"n": 0, "status": collections.Counter(), "tasks": []}
for tid, d in sorted(by.items(), key=lambda kv: int(kv[0])):
    c, b = d["canonical"], d["buggy"]; rec = {"task": tid, "bug_type": rows[tid]["bug_type"], "symptom": rows[tid]["failure_symptoms"], "canon_status": c["status"], "buggy_status": b["status"]}
    res["status"][(c["status"], b["status"])] += 1
    if c["status"] == b["status"] == "ok":
        co, bo = c["outcomes"], b["outcomes"]
        rec["entry"] = c["entry"]; rec["n_diff_inputs"] = sum(x != y for x, y in zip(co, bo))
        rec["canon_all_exc"] = all(x[0] != "ret" for x in co); rec["canon_n_exc"] = sum(x[0] != "ret" for x in co)
        rec["canon_n_distinct_ret"] = len({x[1] for x in co if x[0] == "ret"})
        rec["observable"] = rec["n_diff_inputs"] > 0
        rec["exc_types"] = sorted({x[1] for x in co if x[0] == "exc"})
    res["tasks"].append(rec)
ok = [t for t in res["tasks"] if "observable" in t]
res["status"] = {str(k): v for k, v in res["status"].items()}
res["n_tasks"] = len(res["tasks"]); res["n_both_ok"] = len(ok); res["n_observable"] = sum(t["observable"] for t in ok)
res["n_canon_all_exc"] = sum(t["canon_all_exc"] for t in ok); res["n_canon_ge1_exc"] = sum(t["canon_n_exc"] > 0 for t in ok)
res["n_canon_ge3_distinct_ret"] = sum(t["canon_n_distinct_ret"] >= 3 for t in ok)
res["observable_by_bug_type"] = {bt: [sum(1 for t in ok if t["bug_type"] == bt and t["observable"]), sum(1 for t in ok if t["bug_type"] == bt)] for bt in sorted({t["bug_type"] for t in ok})}
res["unobservable_tasks"] = [(t["task"], t["bug_type"], t["canon_n_exc"], t["exc_types"]) for t in ok if not t["observable"]]
json.dump(res, open("P06_hep_observability.json", "w"), indent=1)
print({k: v for k, v in res.items() if k not in ("tasks", "unobservable_tasks")}); print("unobs", len(res["unobservable_tasks"]), res["unobservable_tasks"][:12])
import statistics
print("canon exc count per task: median", statistics.median(t["canon_n_exc"] for t in ok), "mean", round(statistics.mean(t["canon_n_exc"] for t in ok), 2))

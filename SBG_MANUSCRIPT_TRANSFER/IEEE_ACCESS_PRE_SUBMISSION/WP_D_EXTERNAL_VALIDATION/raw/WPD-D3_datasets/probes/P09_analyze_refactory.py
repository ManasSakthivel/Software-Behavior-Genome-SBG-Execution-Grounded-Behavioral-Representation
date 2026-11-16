#!/usr/bin/env python3
"""P09: Refactory label observability on SBG's frozen battery. Pairs = (instructor reference, student program).
Label per dataset README: 'correct' passes whole test-suite (=> EQUIVALENT-ish on the tested domain), 'wrong' fails >=1 test (=> CHANGED).
We report how often the 11 battery inputs reproduce that label. No SBG scoring. Output: P09_refactory_observability.json"""
import json, collections, re
out = json.load(open("P05_refactory_outcomes.json")); by = collections.defaultdict(lambda: collections.defaultdict(list))
for o in out:
    m = re.search(r"question_(\d)/code/(\w+)/", o["file"]); by[m.group(1)][m.group(2)].append(o)
res = {}
for q, d in sorted(by.items()):
    ref = d["reference"][0]; r = {"reference_status": ref["status"]}
    if ref["status"] != "ok": res[q] = r; continue
    ro = ref["outcomes"]; r["ref_n_exc"] = sum(x[0] != "ret" for x in ro); r["ref_exc_types"] = sorted({x[1] for x in ro if x[0] == "exc"}); r["ref_n_distinct_ret"] = len({x[1] for x in ro if x[0] == "ret"})
    for kind in ("correct", "wrong"):
        L = d[kind]; st = collections.Counter(o["status"] for o in L); ok = [o for o in L if o["status"] == "ok"]
        differ = sum(o["outcomes"] != ro for o in ok); sig = collections.Counter(json.dumps([x[:2] for x in o["outcomes"]]) for o in ok)
        r[kind] = {"n": len(L), "status": dict(st), "n_ok": len(ok), "differs_from_reference_on_battery": differ, "rate": round(differ / max(1, len(ok)), 4),
                   "n_all_exc": sum(all(x[0] != "ret" for x in o["outcomes"]) for o in ok), "n_unique_signatures": len(sig)}
    res[q] = r
# overall pair-level "label recovery"
tot = {"correct_n_ok": 0, "correct_differ": 0, "wrong_n_ok": 0, "wrong_differ": 0}
for q, r in res.items():
    if "correct" in r: tot["correct_n_ok"] += r["correct"]["n_ok"]; tot["correct_differ"] += r["correct"]["differs_from_reference_on_battery"]; tot["wrong_n_ok"] += r["wrong"]["n_ok"]; tot["wrong_differ"] += r["wrong"]["differs_from_reference_on_battery"]
res["_overall"] = tot
json.dump(res, open("P09_refactory_observability.json", "w"), indent=1)
for q, r in res.items(): print(q, json.dumps(r)[:900])

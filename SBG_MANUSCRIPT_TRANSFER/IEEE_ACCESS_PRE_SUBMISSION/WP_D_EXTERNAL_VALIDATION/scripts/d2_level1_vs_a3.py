#!/usr/bin/env python3
"""WP-D / D2 Task A (post-hoc cross-check, run AFTER d2_level1_recompute.py):
compare D2's own recomputation with results/raw/EXP-A3-007/external_auroc_recompute.json.

    d2_level1_vs_a3.py LEVEL1_JSON A3_JSON OUT_JSON
"""
import json
import sys

l1 = json.load(open(sys.argv[1]))
a3 = json.load(open(sys.argv[2]))
by = {v["variant"]: v for v in l1["variants"]}
MAP = {
    "bugsinpy v7 committed, evaluated only (all)": "bugsinpy | v7 committed | all pairs | evaluated only",
    "bugsinpy v7 committed, evaluated only, SP-2 excluded": "bugsinpy | v7 committed | SP-2 excluded | evaluated only",
    "bugsinpy v7 committed, SENSITIVITY unevaluated scored 0.0 (NOT the reported analysis)": "bugsinpy | v7 committed | all pairs | unevaluated=0",
    "quixbugs_canonical v7 committed, evaluated only (all)": "quixbugs_canonical | v7 committed | all pairs | evaluated only",
    "quixbugs_canonical v7 committed, evaluated only, SP-2 excluded": "quixbugs_canonical | v7 committed | SP-2 excluded | evaluated only",
    "quixbugs_canonical v7 committed, SENSITIVITY unevaluated scored 0.0 (NOT the reported analysis)": "quixbugs_canonical | v7 committed | all pairs | unevaluated=0",
    "bugsinpy v8 rescore (all)": "bugsinpy | v8 rescore | all pairs | evaluated only",
    "bugsinpy v8 rescore, SP-2 excluded": "bugsinpy | v8 rescore | SP-2 excluded | evaluated only",
    "bugsinpy committed_v7 scores on the rescored pair set": "bugsinpy | v7 committed scores on the v8-dump pair set | all pairs | evaluated only",
    "quixbugs_canonical v8 rescore (all)": "quixbugs_canonical | v8 rescore | all pairs | evaluated only",
    "quixbugs_canonical v8 rescore, SP-2 excluded": "quixbugs_canonical | v8 rescore | SP-2 excluded | evaluated only",
    "quixbugs_canonical committed_v7 scores on the rescored pair set": "quixbugs_canonical | v7 committed scores on the v8-dump pair set | all pairs | evaluated only",
}
rows, ok = [], True
for item in a3:
    key = MAP.get(item["slice"])
    if key is None:
        rows.append({"a3_slice": item["slice"], "status": "NOT_COMPARED (seed 7 variant; D2 uses seed 42 only)"})
        continue
    m = by[key]
    # A3 reports 4 d.p.; CI bounds 4 d.p.
    a_ok = round(m["auroc"], 4) == item["auroc"] and (m["n_pairs"], m["n_pos"], m["n_clusters"]) == (
        item["n_pairs"], item["n_pos"], item["n_clusters"])
    ci_ok = [round(x, 4) for x in m["ci95_cluster_bootstrap"]] == item["ci95_cluster_bootstrap"]
    ok &= a_ok and ci_ok
    rows.append({"a3_slice": item["slice"], "d2_variant": key, "n": [m["n_pairs"], m["n_pos"], m["n_clusters"]],
                 "a3_auroc": item["auroc"], "d2_auroc": round(m["auroc"], 4), "auroc_match_4dp": a_ok,
                 "a3_ci": item["ci95_cluster_bootstrap"], "d2_ci": [round(x, 4) for x in m["ci95_cluster_bootstrap"]],
                 "ci_match_4dp": ci_ok})
json.dump({"all_compared_slices_match": ok, "rows": rows}, open(sys.argv[3], "w"), indent=1)
for r in rows:
    print(r.get("status") or (r["auroc_match_4dp"], r["ci_match_4dp"]), "|", r["a3_slice"])
print("ALL MATCH:", ok)

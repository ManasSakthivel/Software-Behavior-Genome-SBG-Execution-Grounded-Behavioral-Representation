"""d4_02_inference.py -- Task 2: own AUROC, cluster bootstrap (bug / project / unit-family), percentile,
basic and BCa CIs, within-cluster permutation tests (Monte-Carlo) in BOTH directions, exact stratified
(within-bug) test, one-sided bootstrap bounds and tail probabilities.

Predictor: sbg_v5 (the pre-registered primary).  Score source per set: see d4_sets.SET_DEFS.
Labels: PRE-REGISTERED sets use the prereg analysis (cluster = bug/program; bootstrap + within-cluster permutation);
        everything else (project/family clustering, BCa, exact stratified, both-direction tests, v8, ex-SP-2)
        is POST-HOC EXPLORATORY (or independent re-analysis by D4) -- see 'status' fields.
Outputs: raw/WPD-D4_stats/02_inference.json , 02_inference_table.csv
Settings: B=10000 bootstrap resamples, M=20000 permutations, seeds from crc32(set_id).
"""
import csv
import json
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

B, M = 10000, 20000
THRESH = [0.5, 0.6, 0.7, 0.75, 0.8, 0.897]
C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
S = get_sets(C, audit)

out = {"script": "scripts/d4_02_inference.py", "B": B, "M": M, "predictor": "sbg_v5",
       "input_manifest": input_manifest(), "results": {}}
rows = []
for sid, s in S.items():
    recs = s["recs"]
    sc = vecs(recs, "sbg_v5", s["src"], s["impute"])
    lab = [r["label"] for r in recs]
    theta = auroc(sc, lab)
    n_zero_pos = sum(1 for x, y in zip(sc, lab) if y == 1 and x == 0)
    n_zero_neg = sum(1 for x, y in zip(sc, lab) if y == 0 and x == 0)
    levels = {"bug": bug_cluster(recs)}
    if s["corpus"] == "bugsinpy":
        levels["project"] = project_cluster(recs)
        levels["unit_family"] = family_cluster(recs)
    res = {"set": sid, "status": s["status"], "desc": s["desc"], "n": len(recs), "n_pos": sum(lab),
           "n_neg": len(lab) - sum(lab), "auroc": round(theta, 4),
           "frac_pos_score_zero": round(n_zero_pos / sum(lab), 4),
           "frac_neg_score_zero": round(n_zero_neg / (len(lab) - sum(lab)), 4), "levels": {}}
    seed0 = zlib.crc32(sid.encode())
    for lv, cl in levels.items():
        g = groups_of(cl)
        boot = cluster_boot({"x": sc}, lab, g, B=B, seed=seed0 + 1)["x"]
        ci = ci_from_boot(theta, boot, sc, lab, g)
        perm = perm_within_clusters(sc, lab, g, M=M, seed=seed0 + 2)
        d = {"n_clusters": len(g), "ci95": ci,
             "one_sided_95_upper_bound": round(one_sided_upper_bound(boot), 4),
             "one_sided_95_lower_bound": round(one_sided_lower_bound(boot), 4),
             "boot_P(theta*>=x)": {str(t): round(sum(1 for v in boot if v is not None and v >= t) /
                                                  max(1, sum(1 for v in boot if v is not None)), 4) for t in THRESH},
             "perm_within_cluster": perm}
        if lv in ("bug", "unit_family"):
            d["exact_stratified_within_cluster"] = exact_stratified(sc, lab, g)
        res["levels"][lv] = d
        rows.append([sid, s["status"], lv, len(recs), sum(lab), len(lab) - sum(lab), len(g), round(theta, 4),
                     ci["percentile"][0], ci["percentile"][1], ci["bca"][0], ci["bca"][1],
                     ci["basic"][0], ci["basic"][1], perm["p_auroc_lt_0.5_lower_tail"],
                     perm["p_auroc_gt_0.5_upper_tail"], perm["p_two_sided"],
                     round(d["one_sided_95_upper_bound"], 4), ci["n_degenerate"]])
    out["results"][sid] = res
    print(sid, res["auroc"], {lv: (v["ci95"]["percentile"], v["perm_within_cluster"]["p_auroc_lt_0.5_lower_tail"],
                                    v["perm_within_cluster"]["p_auroc_gt_0.5_upper_tail"]) for lv, v in res["levels"].items()}, flush=True)

write_json("02_inference.json", out)
with open(OUT / "02_inference_table.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["set", "status", "cluster_level", "n", "n_pos", "n_neg", "n_clusters", "auroc", "pct_lo", "pct_hi",
                "bca_lo", "bca_hi", "basic_lo", "basic_hi", "perm_p_lower_tail(auroc<0.5)", "perm_p_upper_tail(auroc>0.5)",
                "perm_p_two_sided", "onesided95_upper", "n_degenerate_boot"])
    w.writerows(rows)

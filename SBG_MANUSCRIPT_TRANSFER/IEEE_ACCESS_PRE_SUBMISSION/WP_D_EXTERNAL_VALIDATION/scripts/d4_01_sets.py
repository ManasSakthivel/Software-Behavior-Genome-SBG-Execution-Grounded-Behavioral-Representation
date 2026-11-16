"""d4_01_sets.py -- Task 1: exact pair sets, per-corpus pos/neg counts, unevaluated pairs + reasons.
Outputs (raw/WPD-D4_stats/):
  01_pair_sets.json              set table (+ per-transformation counts, clusters, contaminated bases, invalid SP-2)
  01_unevaluated_pairs.csv       EVERY unevaluated pair (no silent drops) with failure kind/side/detail
  01_set_membership.csv          pair_id x set membership matrix (one row per pair)
Status: DESCRIPTIVE (no inference).
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
S = get_sets(C, audit)
res = {"script": "scripts/d4_01_sets.py", "status": "DESCRIPTIVE", "input_manifest": input_manifest()}

# --- per-corpus inventory ------------------------------------------------------
inv = {}
for corpus, recs in C.items():
    d = {"n_rows": len(recs),
         "by_label": dict(Counter(r["label"] for r in recs)),
         "by_kind_all": dict(Counter(r["kind"] for r in recs)),
         "by_kind_evaluated_v7": dict(Counter(r["kind"] for r in recs if r["ev7"])),
         "by_kind_unevaluated_v7": dict(Counter(r["kind"] for r in recs if not r["ev7"])),
         "n_evaluated_v7": sum(r["ev7"] for r in recs),
         "n_unevaluated_v7": sum(not r["ev7"] for r in recs),
         "unevaluated_by_failure": dict(Counter("%s:%s" % (r["failure_side"], r["failure_kind"]) for r in recs if not r["ev7"])),
         "unevaluated_by_label": dict(Counter(r["label"] for r in recs if not r["ev7"])),
         "n_bug_clusters_all": len({r["bug"] for r in recs}),
         "n_bug_clusters_evaluated_v7": len({r["bug"] for r in recs if r["ev7"]}),
         "n_bug_clusters_with_evaluated_positive": len({r["bug"] for r in recs if r["ev7"] and r["label"] == 1}),
         "n_bug_clusters_with_unevaluated_positive": len({r["bug"] for r in recs if (not r["ev7"]) and r["label"] == 1}),
         "n_projects_evaluated_v7": len({r["project"] for r in recs if r["ev7"] and r["project"]}) or None,
         "n_unit_families_evaluated_v7": len({r["family"] for r in recs if r["ev7"]}),
         "pairs_per_project_evaluated_v7": dict(Counter(r["project"] for r in recs if r["ev7"] and r["project"])) or None,
         "evaluated_v7_but_not_v8": [r["pair_id"] for r in recs if r["ev8"] is not None and r["ev7"] and not r["ev8"]],
         "evaluated_v8_but_not_v7": [r["pair_id"] for r in recs if r["ev8"] is not None and r["ev8"] and not r["ev7"]],
         }
    byb = {}
    for r in recs:
        byb.setdefault(r["bug"], []).append(r)
    d["bugs_partially_evaluated"] = [b for b, v in byb.items() if 0 < sum(x["ev7"] for x in v) < len(v)]
    d["bugs_with_eval_negative_but_no_eval_positive"] = [b for b, v in byb.items()
                                                         if any(x["ev7"] and x["label"] == 0 for x in v)
                                                         and not any(x["ev7"] and x["label"] == 1 for x in v)]
    inv[corpus] = d
res["corpus_inventory"] = inv

# --- contaminated bases / invalid SP-2 -------------------------------------------
res["contaminated_bases_v8_self_distance_gt0"] = {}
for corpus in ("bugsinpy", "quixbugs_canonical"):
    recs = C[corpus]
    cont = contaminated(recs)
    res["contaminated_bases_v8_self_distance_gt0"][corpus] = {
        b: {"self_dist_v5": next(r["self_dist8"] for r in recs if r["base_path"] == b),
            "pairs": [(r["pair_id"], r["label"], r["kind"]) for r in recs if r["base_path"] == b]} for b in sorted(cont)}
res["invalid_sp2_negatives_EXTERNAL_NEGATIVE_AUDIT"] = sorted(invalid_sp2_ids(audit))

# --- set table ----------------------------------------------------------------------
tab = []
for sid, s in S.items():
    recs = s["recs"]
    tab.append({"set_id": sid, "status": s["status"], "corpus": s["corpus"], "score_source": s["src"],
                "n_pairs": len(recs), "n_pos": sum(r["label"] for r in recs),
                "n_neg": sum(1 - r["label"] for r in recs),
                "n_bug_clusters": len({r["bug"] for r in recs}),
                "n_project_clusters": len({r["project"] for r in recs if r["project"]}) or None,
                "n_unit_family_clusters": len({r["family"] for r in recs}),
                "by_kind": dict(Counter(r["kind"] for r in recs)),
                "n_unevaluated_scored_as_impute": sum(
                    1 for r in recs if not (r["ev7"] if s["src"] == "s7" else (r["ev8"] if s["src"] == "s8" else r["ev6"]))),
                "impute_value": s["impute"],
                "description": s["desc"]})
res["analysis_sets"] = tab
write_json("01_pair_sets.json", res)

# --- unevaluated CSV ---------------------------------------------------------------
with open(OUT / "01_unevaluated_pairs.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["corpus", "pair_id", "label", "kind", "bug_or_base", "project", "unit_family", "failure_side",
                "failure_kind", "failure_detail", "unevaluated_in", "has_v7_scores"])
    for corpus, recs in C.items():
        for r in recs:
            u7 = not r["ev7"]
            u8 = (r["ev8"] is not None) and (not r["ev8"])
            if u7 or u8:
                w.writerow([corpus, r["pair_id"], r["label"], r["kind"], r["bug"], r["project"] or "", r["family"],
                            r["failure_side"] or "", r["failure_kind"] or "",
                            (r["failure_detail"] or "").replace("\n", " "),
                            ("v7" if u7 else "") + ("+v8" if u8 else ""),
                            "yes" if r["s7"] else "no"])

# --- membership matrix --------------------------------------------------------------
sids = list(S)
mem = {sid: {r["pair_id"] for r in S[sid]["recs"]} for sid in sids}
with open(OUT / "01_set_membership.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["corpus", "pair_id", "label", "kind", "bug", "project"] + sids)
    for corpus, recs in C.items():
        for r in recs:
            w.writerow([corpus, r["pair_id"], r["label"], r["kind"], r["bug"], r["project"] or ""] +
                       [int(r["pair_id"] in mem[s] and S[s]["corpus"] == corpus) for s in sids])

print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in (
    "n_rows", "n_evaluated_v7", "unevaluated_by_failure", "unevaluated_by_label", "n_bug_clusters_all",
    "n_bug_clusters_evaluated_v7", "n_projects_evaluated_v7", "n_unit_families_evaluated_v7",
    "evaluated_v7_but_not_v8", "bugs_partially_evaluated", "bugs_with_eval_negative_but_no_eval_positive",
    "by_kind_unevaluated_v7")} for k, v in inv.items()}, indent=1))
for t in tab:
    print("%-24s %-22s n=%3d pos=%2d neg=%3d bugs=%2d proj=%s fam=%2d" % (
        t["set_id"], t["status"][:14], t["n_pairs"], t["n_pos"], t["n_neg"], t["n_bug_clusters"],
        t["n_project_clusters"], t["n_unit_family_clusters"]))
print(json.dumps(res["contaminated_bases_v8_self_distance_gt0"], indent=1)[:2500])

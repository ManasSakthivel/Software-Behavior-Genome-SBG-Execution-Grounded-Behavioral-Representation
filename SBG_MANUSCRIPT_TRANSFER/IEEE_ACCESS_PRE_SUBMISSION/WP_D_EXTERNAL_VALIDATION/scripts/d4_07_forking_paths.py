"""d4_07_forking_paths.py -- Task 7: garden-of-forking-paths accounting for the EXTERNAL AUROC variants in the repo history.

Each row = one distinct external AUROC (corpus x pair-set x score-version x exclusion) that exists in a repo artifact.
'recomputed' = D4 recomputed it from raw pair files with its own code; 'artifact' = value copied from the artifact (raw
inputs for that variant were not available to D4).
Status: PRE-REGISTERED = computed per PHASE2_PREREGISTRATION s5/s6 (ALL/EVALUABLE/VALID, cluster by program/bug);
        POST-HOC = defined after external scores were seen.
Outputs: raw/WPD-D4_stats/07_forking_paths.json , 07_forking_paths.csv
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa
from d4_sets import *  # noqa

C = load_corpora()
audit = json.load(open(INPUT_FILES["EXTERNAL_NEGATIVE_AUDIT"]))
S = get_sets(C, audit)
purge = json.load(open(INPUT_FILES["bugsinpy_purge_rescore"]))
DIAG = json.load(open(PE / "DIAGNOSTIC_EXTERNAL.json"))


def A(sid):
    s = S[sid]
    sc = vecs(s["recs"], "sbg_v5", s["src"], s["impute"])
    return round(auroc(sc, [r["label"] for r in s["recs"]]), 4), len(s["recs"])


# purge rescored scores
pur = {}
for u in purge["units"]:
    for p in u["pairs"]:
        pur[p["pair_id"]] = (p["label"], p["transformation"], p["purged_sbg_v5"])
pl = [v[0] for v in pur.values()]
ps = [v[2] for v in pur.values()]
pur_all = auroc(ps, pl)
nsp2 = [v for v in pur.values() if v[1] != "SP-2"]
pur_nsp2 = auroc([v[2] for v in nsp2], [v[0] for v in nsp2])

# within-unit stratified (exact stratified statistic by unit family / by bug)
s = S["BP-v7-EVAL"]
sc = vecs(s["recs"], "sbg_v5", "s7", 0)
lab = [r["label"] for r in s["recs"]]
ex_fam = exact_stratified(sc, lab, groups_of(family_cluster(s["recs"])))
ex_bug = exact_stratified(sc, lab, groups_of(bug_cluster(s["recs"])))
s = S["QC-v7-ALL"]
exq = exact_stratified(vecs(s["recs"], "sbg_v5", "s7", 0), [r["label"] for r in s["recs"]], groups_of(bug_cluster(s["recs"])))

# canonical restricted to programs with >=1 evaluated declared pair
dec_bugs = {r["bug"] for r in C["quixbugs_declared"] if r["ev7"]}
qc_on_dec = [r for r in C["quixbugs_canonical"] if r["bug"] in dec_bugs]
qc_on_dec_auc = auroc(vecs(qc_on_dec, "sbg_v5", "s7", 0), [r["label"] for r in qc_on_dec])

PRE, POST = "PRE-REGISTERED", "POST-HOC"
V = []


def add(i, corpus, desc, status, auc, n, src, date, how, ci=None, note=""):
    V.append(dict(id=i, corpus=corpus, description=desc, status=status, auroc=auc, n_pairs=n, source=src,
                  date=date, how=how, repo_reported_ci=ci, note=note))


# ---- BugsInPy
add("BP-01", "BugsInPy", "v6 protocol, VALID=EVALUABLE (140)", PRE, *A("BP-v6-EVAL"), "artifacts/final/BUGSINPY_output_free_v6.json", "2026-09-28", "recomputed", [0.3223, 0.4901])
add("BP-02", "BugsInPy", "v7 ALL 200, unevaluated=0", PRE, *A("BP-v7-ALL"), "artifacts/final/BUGSINPY_output_free_v7.json", "2026-09-28", "recomputed", [0.3741, 0.4899])
add("BP-03", "BugsInPy", "v7 EVALUABLE=VALID 147 (headline/primary)", PRE, *A("BP-v7-EVAL"), "artifacts/final/BUGSINPY_output_free_v7.json", "2026-09-28", "recomputed", [0.3262, 0.4939])
add("BP-04", "BugsInPy", "v7 excluding SP-2 negatives", POST, *A("BP-v7-exSP2"), "paper_evidence/DIAGNOSTIC_EXTERNAL.json", "2026-10-29", "recomputed", [0.3809, 0.5617])
add("BP-05", "BugsInPy", "v7 within-unit stratified", POST, round(ex_bug["T_obs"], 4), ex_bug["n_cross_label_pairs"], "paper_evidence/DIAGNOSTIC_EXTERNAL.json (0.4018)", "2026-10-29", "recomputed (pooled within-BUG stratified AUROC; n=#cross-label pairs)", None, "repo value 0.4018 NOT reproduced exactly: D4 pooled-pair weighting gives %.4f (within-bug) / %.4f (within-unit-family); weighting scheme of the repo value is undocumented" % (ex_bug["T_obs"], ex_fam["T_obs"]))
add("BP-06", "BugsInPy", "v7, units not importing `re`, excl. SP-2", POST, DIAG["bugsinpy"][3]["auroc"], DIAG["bugsinpy"][3]["n_pairs"], "paper_evidence/DIAGNOSTIC_EXTERNAL.json", "2026-10-29", "artifact", DIAG["bugsinpy"][3]["ci95_cluster_bootstrap"])
add("BP-07", "BugsInPy", "re.purge rescore (purged scores), all 147", POST, round(pur_all, 4), len(pl), "paper_evidence/raw/bugsinpy_purge_rescore.json", "2026-10-29", "recomputed", [0.3379, 0.5266])
add("BP-08", "BugsInPy", "re.purge rescore, excl. SP-2", POST, round(pur_nsp2, 4), len(nsp2), "paper_evidence/raw/bugsinpy_purge_rescore.json (not separately reported)", "2026-10-29", "recomputed", None, "not reported in repo; D4 computed from purged scores")
add("BP-09", "BugsInPy", "v8 corrected-harness rescore, all 147", POST, *A("BP-v8-EVAL"), "paper_evidence/EXTERNAL_RESCORE_V8.json", "2026-10-29", "recomputed", [0.3223, 0.5144])
add("BP-10", "BugsInPy", "v8 rescore, excl. SP-2 (107)  <- the '0.497'", POST, *A("BP-v8-exSP2"), "paper_evidence/EXTERNAL_RESCORE_V8.json", "2026-10-29", "recomputed", [0.4023, 0.5956])
add("BP-11", "BugsInPy", "v8 rescore, excl. 7 invalid SP-2 negatives (140)", POST, *A("BP-v8-exInvalidSP2"), "paper_evidence/EXTERNAL_NEGATIVE_AUDIT.json", "2026-10-29", "recomputed", None, "point estimate only in repo")
# ---- QuixBugs canonical
add("QC-01", "QuixBugs canonical", "v7 all 152 (headline)", PRE, *A("QC-v7-ALL"), "artifacts/final/QUIXBUGS_output_free_v7.json", "2026-10-26", "recomputed", [0.2847, 0.5034], "CI from DIAGNOSTIC_EXTERNAL; QUIXBUGS_output_free_v7.json itself has no CI")
add("QC-02", "QuixBugs canonical", "v7 excluding SP-2 (112)", POST, *A("QC-v7-exSP2"), "paper_evidence/DIAGNOSTIC_EXTERNAL.json", "2026-10-29", "recomputed", [0.3601, 0.5473])
add("QC-03", "QuixBugs canonical", "v7 within-program stratified", POST, round(exq["T_obs"], 4), exq["n_cross_label_pairs"], "paper_evidence/DIAGNOSTIC_EXTERNAL.json (0.3884)", "2026-10-29", "recomputed (exact_stratified; n=#cross-label pairs)", None)
add("QC-04", "QuixBugs canonical", "v8 rescore, all 151", POST, *A("QC-v8-EVAL"), "paper_evidence/EXTERNAL_RESCORE_V8.json", "2026-10-29", "recomputed", [0.2847, 0.4899])
add("QC-05", "QuixBugs canonical", "v8 rescore, excl. SP-2 (111)  <- the '0.444'", POST, *A("QC-v8-exSP2"), "paper_evidence/EXTERNAL_RESCORE_V8.json", "2026-10-29", "recomputed", [0.3553, 0.5385])
add("QC-06", "QuixBugs canonical", "v7 committed scores on the v8 151-pair set", POST, 0.372, 151, "paper_evidence/EXTERNAL_RESCORE_V8.json", "2026-10-29", "artifact", [0.2743, 0.4799])
add("QC-07", "QuixBugs canonical", "canonical regime restricted to the 28 programs evaluable under declared inputs", POST, round(qc_on_dec_auc, 4), len(qc_on_dec), "paper_evidence/DIAGNOSTIC_EXTERNAL.json (0.4385)", "2026-10-29", "recomputed", [0.3265, 0.5673])
# ---- QuixBugs declared
add("QD-01", "QuixBugs declared", "declared regime EVALUABLE (99) (pre-registered secondary regime)", PRE, *A("QD-v7-EVAL"), "paper_evidence/DIAGNOSTIC_EXTERNAL.json (no dedicated artifact in artifacts/final)", "2026-10-29", "recomputed", [0.5836, 0.8166], "regime is prereg; the result was first reported only in an exploratory diagnostic")
add("QD-02", "QuixBugs declared", "declared regime ALL 152, unevaluated=0", PRE, *A("QD-v7-ALL"), "(not reported anywhere in the repo)", "-", "recomputed", None, "prereg ALL denominator; D4 computed")
add("QD-03", "QuixBugs declared", "declared evaluable, excluding SP-2 (72)", POST, *A("QD-v7-exSP2"), "paper_evidence/DIAGNOSTIC_EXTERNAL.json", "2026-10-29", "recomputed", [0.5316, 0.7969])
# ---- legacy
LEG = [("LEG-01", "QuixBugs (legacy)", "positive-only detection rate at tau*=0.08, 17/28 (60.7%), output-aware 'EEP' protocol", "results/external/FINAL_MULTI_CORPUS_ANALYSIS_RESULTS.json"),
       ("LEG-02", "BugsInPy (legacy)", "positive-only detection rate 6/7 (85.7%), 5 projects, output-aware 'EEP' protocol", "results/external/BUGSINPY_EXTENDED_EVALUATION_RESULTS.json")]
for i, c, d, srcp in LEG:
    add(i, c, d, "POST-HOC (superseded; no negatives, no AUROC)", None, None, srcp, "2026-08-30", "artifact", None,
        "different protocol (output-aware), no negative class: not an AUROC and not comparable")

# ---- D4 extra sensitivities (not repo history, listed for completeness of the family)
D4X = [("D4-01", "BugsInPy", "v8 rescore excluding 3 contaminated base units", A("BP-v8-exContam")),
       ("D4-02", "BugsInPy", "v8 ex-SP-2 & ex-contaminated", A("BP-v8-exSP2-exContam")),
       ("D4-03", "QuixBugs canonical", "v8 ex-contaminated base", A("QC-v8-exContam")),
       ("D4-04", "QuixBugs canonical", "v8 ex-SP-2 & ex-contaminated", A("QC-v8-exSP2-exContam"))]
for i, c, d, (a, n) in D4X:
    add(i, c, d, "POST-HOC (D4 sensitivity; not in repo history)", a, n, "D4 scripts", "2026-11", "recomputed", None)

# ---- summaries
def summ(rows):
    a = [r["auroc"] for r in rows if r["auroc"] is not None]
    return {"k": len(a), "min": min(a), "max": max(a), "n_lt_0.5": sum(1 for x in a if x < 0.5),
            "n_ge_0.5": sum(1 for x in a if x >= 0.5)}


repo = [r for r in V if not r["id"].startswith("D4")]
summary = {}
for corp in ("BugsInPy", "QuixBugs canonical", "QuixBugs declared"):
    rr = [r for r in repo if r["corpus"] == corp]
    summary[corp] = {"all_variants": summ(rr), "pre_registered": summ([r for r in rr if r["status"] == PRE]),
                     "post_hoc": summ([r for r in rr if r["status"] != PRE]),
                     "n_variants_total": len(rr), "n_pre_registered": sum(1 for r in rr if r["status"] == PRE),
                     "n_post_hoc": sum(1 for r in rr if r["status"] != PRE),
                     "n_repo_reported_ci_including_0.5": sum(1 for r in rr if r["repo_reported_ci"] and r["repo_reported_ci"][0] <= 0.5 <= r["repo_reported_ci"][1]),
                     "n_with_ci": sum(1 for r in rr if r["repo_reported_ci"])}
out = {"script": "scripts/d4_07_forking_paths.py", "input_manifest": input_manifest(), "variants": V, "summary": summary,
       "notes": ["The prereg inferential claim set is: sbg_v5 AUROC with cluster bootstrap on ALL and EVALUABLE(=VALID) sets, "
                 "within-cluster permutation H0: AUROC=0.5 (one-sided, testing > 0.5), Holm over 5 comparators.",
                 "The headline numbers 0.497 (BugsInPy) and 0.444 (QuixBugs) are POST-HOC: they require the v8 harness rescore "
                 "(EXTERNAL_RESCORE_V8, produced after the v7 pre-registered numbers 0.410/0.388 were seen) AND exclusion of all SP-2 negatives.",
                 "Point-estimate shifts (D4 recomputation): excluding SP-2 raises AUROC by +0.062 (BP v7), +0.081 (BP v8), +0.063 (QC v7), +0.060 (QC v8); "
                 "the v7->v8 harness change moves the full-set AUROC by +0.006 (BP) / -0.004 (QC) and the ex-SP-2 AUROC by +0.026 (BP) / -0.006 (QC)."]}
write_json("07_forking_paths.json", out)
with open(OUT / "07_forking_paths.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "corpus", "description", "status", "auroc", "n_pairs", "repo_reported_ci", "source", "date", "how", "note"])
    for r in V:
        w.writerow([r["id"], r["corpus"], r["description"], r["status"], r["auroc"], r["n_pairs"],
                    json.dumps(r["repo_reported_ci"]) if r["repo_reported_ci"] else "", r["source"], r["date"], r["how"], r["note"]])
for r in V:
    print("%-6s %-20s %-60s %-14s %s n=%s" % (r["id"], r["corpus"], r["description"][:60], r["status"][:14], r["auroc"], r["n_pairs"]))
print(json.dumps(summary, indent=1))

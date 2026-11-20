#!/usr/bin/env python3
"""Recompute every number quoted in the Abstract/Results (and key numbers elsewhere) from results/v7b_phase2_summary/ and
write NUMERICAL_CLAIM_VERIFICATION.md. Statuses: VERIFIED (recomputed from tracked data), REPORT-ONLY (quoted from a report whose
raw input is not tracked: only checked that the report states it), MISMATCH (fails; exit 1). Python 3 stdlib only."""
import csv, json, re, pathlib, collections, sys
P = pathlib.Path(__file__).resolve().parent.parent
ROOT = P.parent.parent
S = ROOT / "results/v7b_phase2_summary"
E1 = S / "p2_e1_20261118_074906"; E3 = S / "p2_e3_20261118_092700"; E6 = S / "p2_e6_20261118_171723"; E6B = S / "p2_e6b_20261118_174414"; E7 = S / "p2_e7_20261118_190612"
rd = lambda p: list(csv.DictReader(open(p)))
js = lambda p: json.load(open(p))
rel = lambda p: str(pathlib.Path(p).relative_to(ROOT))
con = js(S / "p2_consolidated_20261118_190644/consolidated.json")
met = {(r["system"], r["outcome"]): r for r in rd(E3 / "statistics/system_metrics.csv")}
par = {(r["test"], r["outcome"]): r for r in rd(E3 / "statistics/paired_comparisons.csv")}
rc = {(r["system"], r["min_sufficiency_for_NDO"]): r for r in rd(E3 / "statistics/risk_coverage.csv")}
pairs = rd(E3 / "processed/dev_pairs_per_system.csv")
cc = collections.Counter((r["system"], r["truth"], r["verdict"]) for r in pairs)
byp = collections.defaultdict(dict)
for r in pairs: byp[r["pair_id"]][r["system"]] = r
v7 = [r for r in pairs if r["system"] == "V7-B"]
e3pp = [json.loads(l) for l in open(E3 / "processed/k1_spike_per_pair.jsonl")]
e1pp = [json.loads(l) for l in open(E1 / "proc/k1_spike_per_pair.jsonl")]
oldpp = [json.loads(l) for l in open(ROOT / "results/postfix/processed/k1_spike_per_pair.jsonl")]
e1a = js(E1 / "e1_analysis.json"); tim = {n: js(d / "timing/timing_summary.json") for n, d in (("r1", E6), ("r2", E6B))}
pw = js(E3 / "statistics/power_actual.json")
oldabst = [r for r in rd(ROOT / "results/postfix/statistics/system_metrics.csv") if r["system"] == "V7-B" and r["outcome"] == "abstention"][0]
cr = js(E7 / "corruption_results.json")
rep = (ROOT / "reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md").read_text()
trace = (ROOT / "reports/phase2/PHASE2_TRACEABILITY_RECONCILIATION.md").read_text()
f = float
div_nondiv = [p for p in byp.values() if p["V7-B"]["truth"] == "DIV"]
nonabst = [p for p in div_nondiv if p["V7-B"]["verdict"] != "INSUFFICIENT"]
b1fa = [p for p in div_nondiv if p["B1"]["verdict"] == "NO_DIVERGENCE_OBSERVED"]
r1 = {(r["arm"], r["pair"]): r for r in e1pp if r["tag"] == "run1"}
old = {(r["arm"], r["pair"]): r for r in oldpp if r["tag"] == "run1"} if any("tag" in r for r in oldpp) else {(r["arm"], r["pair"]): r for r in oldpp}
def trans(a, b):
    n = 0
    for k, r in r1.items():
        o = old.get(k)
        if o and (o["verdict"], o.get("level")) == a and (r["verdict"], r.get("primary")) == b: n += 1
    return n
def report_has(text, token): return token in text

C = []  # (id, where, claim, expected, actual-callable, source, kind)
def add(where, claim, exp, act, src, tol=5e-4, kind="V"): C.append((where, claim, exp, act, src, tol, kind))
M = lambda s, o, k: f(met[(s, o)][k]); Pp = lambda t, o, k: f(par[(t, o)][k])
dsrc = rel(E3 / "processed/dev_pairs_per_system.csv"); msrc = rel(E3 / "statistics/system_metrics.csv"); psrc = rel(E3 / "statistics/paired_comparisons.csv")
csrc = rel(E3 / "statistics/class_counts.csv"); rsrc = rel(E3 / "statistics/risk_coverage.csv"); consrc = rel(S / "p2_consolidated_20261118_190644/consolidated.json")
# --- data description
add("Abstract/Datasets", "321 development pairs", 321, lambda: len(v7), dsrc + " (V7-B rows)")
add("Abstract/Datasets", "258 primary-denominator pairs", 258, lambda: sum(r["truth"] in ("DIV", "NO_OBS_DIFF") for r in v7), dsrc + " truth in {DIV,NO_OBS_DIFF}")
add("Datasets", "106 divergent-labelled", 106, lambda: sum(r["truth"] == "DIV" for r in v7), dsrc)
add("Datasets", "152 no-difference-labelled", 152, lambda: sum(r["truth"] == "NO_OBS_DIFF" for r in v7), dsrc)
add("Datasets", "57 unlabelled", 57, lambda: sum(r["truth"] == "UNLABELLED" for r in v7), dsrc)
add("Datasets", "6 suspect labels", 6, lambda: sum(r["truth"] == "SUSPECT_LABEL" for r in v7), dsrc)
for n, k in (("31 QuixBugs", ("quixbugs_buggy_fixed",)), ("85 QuixBugs negatives", ("quixbugs_sp_negatives",)), ("150 synthetic", ("synthetic_changed", "synthetic_equivalent")), ("55 BugsInPy units", ("bugsinpy_units",))):
    add("Datasets", n, int(n.split()[0]), (lambda k=k: sum(r["dataset"] in k for r in v7)), dsrc)
add("Datasets", "78 synthetic changed", 78, lambda: sum(r["dataset"] == "synthetic_changed" for r in v7), dsrc)
add("Datasets", "72 synthetic equivalent", 72, lambda: sum(r["dataset"] == "synthetic_equivalent" for r in v7), dsrc)
add("Datasets", "29 QuixBugs divergent-labelled", 29, lambda: sum(r["dataset"] == "quixbugs_buggy_fixed" and r["truth"] == "DIV" for r in v7), dsrc)
add("Datasets/Methods", "9 pairs not driven (NOT_DRIVEN rows)", 9, lambda: sum(r["verdict"] == "NOT_DRIVEN" for r in v7), dsrc)
add("Datasets", "9 not driven = 8 class units + 1 entry policy", (8, 1), lambda: (sum(str(r.get("primary", "")).startswith("class unit") for r in e3pp if r["tag"] == "run1"), sum(str(r.get("primary", "")).startswith("entry_policy") for r in e3pp if r["tag"] == "run1")), rel(E3 / "processed/k1_spike_per_pair.jsonl"))
add("Datasets/Metrics", "78 project clusters (divergent)", 78, lambda: int(par[("V7-B", "detection")]["projects"]), psrc)
add("Datasets/Metrics", "69 project clusters (no-difference)", 69, lambda: int(par[("V7-B", "false_alarm")]["projects"]), psrc)
add("Datasets", "largest cluster 29 pairs", 29, lambda: pw["inputs"]["from_data"]["design"]["max_cluster"], rel(E3 / "statistics/power_actual.json"))
# --- E3
for s, nfa, nde in (("B1", 24, 82), ("V7-B", 13, 75), ("B3", 20, 86), ("B4", 105, 1)):
    add("Results E3", f"{s} false assurance {nfa}/106", nfa, (lambda s=s: cc[(s, "DIV", "NO_DIVERGENCE_OBSERVED")]), csrc)
    add("Results E3", f"{s} detection {nde}/106", nde, (lambda s=s: cc[(s, "DIV", "DIVERGENT_OBSERVABLE")]), csrc)
for s, fa, fl, fh, de, dl, dh in (("V7-B", .1226, .0541, .2361, .7075, .5454, .8162), ("B1", .2264, .1195, .3919, .7736, .6087, .8814)):
    add("Results E3/Table", f"{s} FA rate [CI]", (fa, fl, fh), (lambda s=s: (M(s, "false_assurance", "est"), M(s, "false_assurance", "lo"), M(s, "false_assurance", "hi"))), msrc)
    add("Results E3/Table", f"{s} detection rate [CI]", (de, dl, dh), (lambda s=s: (M(s, "detection", "est"), M(s, "detection", "lo"), M(s, "detection", "hi"))), msrc)
add("Results E3", "B1+rep identical to B1 (FA 24, det 82, 0 discordant)", (24, 82, 0, 0), lambda: (cc[("B1+rep", "DIV", "NO_DIVERGENCE_OBSERVED")], cc[("B1+rep", "DIV", "DIVERGENT_OBSERVABLE")], int(par[("B1+rep", "false_assurance")]["b_test_only"]), int(par[("B1+rep", "false_assurance")]["c_ref_only"])), csrc + "; " + psrc)
add("Abstract/Results", "V7-B abstention 122/258 = 0.473 [0.353, 0.524]", (122, .4729, .3533, .5237), lambda: (cc[("V7-B", "DIV", "INSUFFICIENT")] + cc[("V7-B", "NO_OBS_DIFF", "INSUFFICIENT")], M("V7-B", "abstention", "est"), M("V7-B", "abstention", "lo"), M("V7-B", "abstention", "hi")), csrc + "; " + msrc)
add("Results E3", "abstention split 18 divergent + 104 no-difference", (18, 104), lambda: (cc[("V7-B", "DIV", "INSUFFICIENT")], cc[("V7-B", "NO_OBS_DIFF", "INSUFFICIENT")]), csrc)
add("Results E3", "V7-B false alarm 0/152; B1 46/152 = 0.303", (0, 46, .3026), lambda: (cc[("V7-B", "NO_OBS_DIFF", "DIVERGENT_OBSERVABLE")], cc[("B1", "NO_OBS_DIFF", "DIVERGENT_OBSERVABLE")], M("B1", "false_alarm", "est")), csrc + "; " + msrc)
add("Results E3", "B4 detects 1 of 106", 1, lambda: cc[("B4", "DIV", "DIVERGENT_OBSERVABLE")], csrc)
add("Abstract/Results", "FA diff -10.4pp [-20.5,-4.3]; 0 vs 11; sign-flip .0010; McNemar .0010; Holm .0059; +10pp not met", (-.1038, -.2051, -.0432, 0, 11, .00098, .00098, .00586, "False"), lambda: (Pp("V7-B", "false_assurance", "diff"), Pp("V7-B", "false_assurance", "diff_lo"), Pp("V7-B", "false_assurance", "diff_hi"), int(par[("V7-B", "false_assurance")]["b_test_only"]), int(par[("V7-B", "false_assurance")]["c_ref_only"]), Pp("V7-B", "false_assurance", "p_signflip"), Pp("V7-B", "false_assurance", "p_mcnemar_exact_pairlevel"), Pp("V7-B", "false_assurance", "p_holm"), par[("V7-B", "false_assurance")]["meets_plus10pp"]), psrc, 6e-4)
add("Results E3", "improvement lower bound 4.3pp (< 10)", .0432, lambda: Pp("V7-B", "false_assurance", "impr_lo"), psrc)
add("Results E3", "detection diff -6.6pp [-11.5,-2.6]; 0 vs 7; sign-flip .031; Holm .156", (-.0660, -.1154, -.0256, 0, 7, .03125, .15625), lambda: (Pp("V7-B", "detection", "diff"), Pp("V7-B", "detection", "diff_lo"), Pp("V7-B", "detection", "diff_hi"), int(par[("V7-B", "detection")]["b_test_only"]), int(par[("V7-B", "detection")]["c_ref_only"]), Pp("V7-B", "detection", "p_signflip"), Pp("V7-B", "detection", "p_holm")), psrc, 6e-4)
add("Results E3", "abstention +47.3pp, Holm 3e-4; 122 vs 0", (.4729, 122, 0, .0003), lambda: (Pp("V7-B", "abstention", "diff"), int(par[("V7-B", "abstention")]["b_test_only"]), int(par[("V7-B", "abstention")]["c_ref_only"]), Pp("V7-B", "abstention", "p_holm")), psrc, 6e-4)
add("Results E3", "B3 vs B1 sign-flip .125, Holm .5 (FA and detection)", (.125, .125, .5, .5), lambda: (Pp("B3", "false_assurance", "p_signflip"), Pp("B3", "detection", "p_signflip"), Pp("B3", "false_assurance", "p_holm"), Pp("B3", "detection", "p_holm")), psrc)
add("Results E3", "24 B1 false assurances: V7-B INSUFFICIENT 11, NDO 13, DIVERGENT 0", (24, 11, 13, 0), lambda: (len(b1fa), sum(p["V7-B"]["verdict"] == "INSUFFICIENT" for p in b1fa), sum(p["V7-B"]["verdict"] == "NO_DIVERGENCE_OBSERVED" for p in b1fa), sum(p["V7-B"]["verdict"] == "DIVERGENT_OBSERVABLE" for p in b1fa)), dsrc)
add("Results E3", "88 non-abstaining divergent pairs: V7-B detects 75 misses 13; B1 same 75/13 (same set)", (88, 75, 13, True), lambda: (len(nonabst), sum(p["V7-B"]["verdict"] == "DIVERGENT_OBSERVABLE" for p in nonabst), sum(p["V7-B"]["verdict"] == "NO_DIVERGENCE_OBSERVED" for p in nonabst), all((p["B1"]["verdict"] == "DIVERGENT_OBSERVABLE") == (p["V7-B"]["verdict"] == "DIVERGENT_OBSERVABLE") for p in nonabst)), dsrc)
add("Results E3", "V7-B detects 0 of B1's misses (0 test-only)", 0, lambda: int(par[("V7-B", "false_assurance")]["b_test_only"]), psrc)
g = con["gate_counterfactual_E3"]
add("Results gate", "relabel all INSUFFICIENT: FA 31/106 (0.293); gate reasons only: 24/106 (0.226)", (13, 31, .2925, 24, .2264), lambda: (g["actual"]["false_assurance"], g["G_A_all_insufficient_to_NDO"]["false_assurance"], g["G_A_all_insufficient_to_NDO"]["false_assurance_rate"], g["G_B_gate_reasons_only_to_NDO"]["false_assurance"], g["G_B_gate_reasons_only_to_NDO"]["false_assurance_rate"]), consrc, 5e-4)
add("Results riskcov", "V7-B any level: coverage .527 (136/258), risk .096", (.5271, 136, .0956), lambda: (f(rc[("V7-B", "none")]["coverage"]), int(rc[("V7-B", "none")]["decided"]), f(rc[("V7-B", "none")]["risk"])), rsrc)
add("Results riskcov", "V7-B S2: coverage .465 (120/258), risk .067", (.4651, 120, .0667), lambda: (f(rc[("V7-B", "S2")]["coverage"]), int(rc[("V7-B", "S2")]["decided"]), f(rc[("V7-B", "S2")]["risk"])), rsrc)
add("Results riskcov", "V7-B S3: coverage .291, 75 decided, risk 0", (.2907, 75, 0.0), lambda: (f(rc[("V7-B", "S3")]["coverage"]), int(rc[("V7-B", "S3")]["decided"]), f(rc[("V7-B", "S3")]["risk"])), rsrc)
add("Results riskcov", "B1 risk .271 (decides all 258)", (.2713, 258), lambda: (f(rc[("B1", "none")]["risk"]), int(rc[("B1", "none")]["decided"])), rsrc)
add("Results E3", "earlier post-fix abstention 0.360", .3605, lambda: f(oldabst["est"]), rel(ROOT / "results/postfix/statistics/system_metrics.csv"))
add("Results byarm", "V7-B verdicts 84 DIV, 157 INSUFFICIENT, 16 S1, 55 S2, 9 not driven", (84, 157, 16, 55, 9), lambda: (sum(r["verdict"] == "DIVERGENT_OBSERVABLE" for r in v7), sum(r["verdict"] == "INSUFFICIENT" for r in v7), sum(r["verdict"] == "NO_DIVERGENCE_OBSERVED" and r["sufficiency"] == "S1" for r in v7), sum(r["verdict"] == "NO_DIVERGENCE_OBSERVED" and r["sufficiency"] == "S2" for r in v7), sum(r["verdict"] == "NOT_DRIVEN" for r in v7)), dsrc)
rc1 = collections.Counter(r["primary"] for r in e3pp if r["tag"] == "run1" and r["verdict"] == "INSUFFICIENT")
add("Results reasons", "INSUFFICIENT reasons: unmodelled 54, unsupported_signature 49, not_activated 40, unobservable 8, resource_limit 4, nondet 1, import 1 (157)", (54, 49, 40, 8, 4, 1, 1, 157), lambda: (rc1["unmodelled_change"], rc1["unsupported_signature"], rc1["changed_region_not_activated"], rc1["unobservable_outcome"], rc1["resource_limit"], rc1["nondeterministic"], rc1["import_error"], sum(rc1.values())), rel(E3 / "processed/k1_spike_per_pair.jsonl"))
add("Stats", "power at +5pp <= 0.267; +10pp unreachable", (.267, None), lambda: ([g_["power_5pp"] for g_ in pw["grid"] if g_["rho"] == 0.0 and abs(g_["pi"] - .066) < 1e-9 and g_["alpha"] == 0.05][0], [g_["power_10pp"] for g_ in pw["grid"] if g_["rho"] == 0.0 and abs(g_["pi"] - .066) < 1e-9 and g_["alpha"] == 0.05][0]), rel(E3 / "statistics/power_actual.json"), 1e-3)
# --- E1
add("Results E1", "quarantined pairs 1 vs 2 of 312; inputs 1 vs 3 of 3044; discordant 0/1; p=1.0; rule SUPPORTED", ([1, 312], [2, 312], [1, 3044], [3, 3044], 0, 1, 1.0, "SUPPORTED"), lambda: (e1a["pair_level_quarantined"]["new"], e1a["pair_level_quarantined"]["old"], e1a["input_level_quarantined"]["new"], e1a["input_level_quarantined"]["old"], e1a["pair_level_quarantined"]["discordant_new_only"], e1a["pair_level_quarantined"]["discordant_old_only"], e1a["pair_level_quarantined"]["p_increase_one_sided_exact"], e1a["decision_rule_outcome"]), rel(E1 / "e1_analysis.json"))
add("Results E1", "run1 vs run2 identical 102/102", (102, 102), lambda: (con["E1"]["run1_vs_run2"]["identical"], con["E1"]["run1_vs_run2"]["n_common"]), consrc)
add("Results E1", "414 of 414 evidence directories verified (E1)", 414, lambda: sum('"verified": true' in l for l in open(E1 / "verify_results.tsv")), rel(E1 / "verify_results.tsv"))
vd = e1a["verdict_distribution"]
add("Fig verdictdist", "old: DIV 84, S2 91, S1 17, INS 120; new: 84, 55, 16, 157", (84, 91, 17, 120, 84, 55, 16, 157), lambda: (vd["old"]["DIVERGENT_OBSERVABLE"], vd["old"]["NO_DIVERGENCE_OBSERVED/S2"], vd["old"]["NO_DIVERGENCE_OBSERVED/S1"], vd["old"]["INSUFFICIENT"], vd["new"]["DIVERGENT_OBSERVABLE"], vd["new"]["NO_DIVERGENCE_OBSERVED/S2"], vd["new"]["NO_DIVERGENCE_OBSERVED/S1"], vd["new"]["INSUFFICIENT"]), rel(E1 / "e1_analysis.json"))
add("Results E1", "63 verdicts changed (old post-fix vs E3; n_diff over 321 compared pairs)", 63, lambda: con["E3"]["consistency_vs_postfix_loose"]["n_diff"], consrc)
add("Results E1", "transitions 37 NDO/S2 -> unmodelled; 14 not_activated -> unmodelled", (37, 14), lambda: (sum(1 for k, r in r1.items() if k in old and old[k]["verdict"] == "NO_DIVERGENCE_OBSERVED" and old[k].get("level") == "S2" and r["primary"] == "unmodelled_change"), sum(1 for k, r in r1.items() if k in old and old[k].get("primary") == "changed_region_not_activated" and r["primary"] == "unmodelled_change")), rel(E1 / "proc/k1_spike_per_pair.jsonl") + " vs results/postfix/processed/k1_spike_per_pair.jsonl")
add("Results E1", "54 unmodelled_change pairs: QuixBugs-neg 27, synthetic 17, BugsInPy 10", (54, 27, 17, 10), lambda: (sum(r["primary"] == "unmodelled_change" for r in r1.values()), sum(r["primary"] == "unmodelled_change" and r["arm"] == "quixbugs_neg" for r in r1.values()), sum(r["primary"] == "unmodelled_change" and r["arm"] == "synthetic" for r in r1.values()), sum(r["primary"] == "unmodelled_change" and r["arm"] == "bugsinpy_units" for r in r1.values())), rel(E1 / "proc/k1_spike_per_pair.jsonl"))
# --- E4/E5
vs = con["E4"]["variants"]
add("Ablation E4", "all variants 84 DIV / 157 INS / 71 NDO / 9 not driven; 0 verdict flips", (84, 157, 71, 9, 0), lambda: (vs["V4"]["verdicts"]["DIVERGENT_OBSERVABLE"], vs["V4"]["verdicts"]["INSUFFICIENT"], vs["V4"]["verdicts"]["NO_DIVERGENCE_OBSERVED"], vs["V4"]["verdicts"]["NOT_DRIVEN"], sum(v_["flips_verdict"] for v_ in con["E4"]["flips"].values())), consrc)
add("Ablation E4", "only reason-code change: nondeterministic -> flaky_witness under V1 and V4 (1 pair)", (1, 1, 0, 0, 0), lambda: (vs["V1"]["insufficient_reasons"].get("flaky_witness", 0), vs["V4"]["insufficient_reasons"].get("flaky_witness", 0), vs["V0"]["insufficient_reasons"].get("flaky_witness", 0), vs["V2"]["insufficient_reasons"].get("flaky_witness", 0), vs["V3"]["insufficient_reasons"].get("flaky_witness", 0)), consrc)
add("Ablation E4", "E1 vs E3 strict consistency 321/321", (321, 321), lambda: (con["E3"]["consistency_vs_e1_strict"]["identical"], con["E3"]["consistency_vs_e1_strict"]["n_common"]), consrc)
for t in ("13,764", "4,746", "320/321", "84 pairs", "5,930", "13,250"):
    add("Ablation E4", f"report-only: '{t}' (run records / strict key / witness-id pairs)", True, (lambda t=t: report_has(rep, t)), "reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md section 4 (raw evidence not tracked)", kind="R")
add("Ablation E4", "CPU sum V4 225.1 vs V0 546.8 (context for ~65% fewer runs)", (225.1, 546.8), lambda: (vs["V4"]["cpu_s_sum"], vs["V0"]["cpu_s_sum"]), consrc, 0.06)
e5 = con["E5"]["variants"]
add("Ablation E5", "S2/S1 at floors .6/.8/.9: 71/0, 55/16, 43/28", (71, 0, 55, 16, 43, 28), lambda: (e5["S2F06"]["levels"].get("S2", 0), e5["S2F06"]["levels"].get("S1", 0), e5["S2F08"]["levels"]["S2"], e5["S2F08"]["levels"]["S1"], e5["S2F09"]["levels"]["S2"], e5["S2F09"]["levels"]["S1"]), consrc)
add("Ablation E5", "0 value flips; 16 and 12 level relabels", (0, 0, 16, 12), lambda: (con["E5"]["flips"]["S2F06"]["flips_verdict"], con["E5"]["flips"]["S2F09"]["flips_verdict"], con["E5"]["flips"]["S2F06"]["flips_category"], con["E5"]["flips"]["S2F09"]["flips_category"]), consrc)
# --- E6
t1, t2 = tim["r1"], tim["r2"]
def ov(t, k): r_ = t["relative_overhead"][k]; return (r_["per_pair_ratio"]["median"], *r_["median_ratio_ci95"])
add("Runtime", "run 1: V0 2.075s, B1 1.310s; wall ratio 1.595 [1.584,1.742]; CPU 1.718 [1.706,1.844]; vs B1+rep 1.018 [1.014,1.072]", (2.075, 1.310, 1.595, 1.584, 1.742, 1.718, 1.706, 1.844, 1.018, 1.014, 1.072), lambda: (t1["systems"]["V0"]["wall_s"]["per_pair_median"]["median"], t1["systems"]["B1"]["wall_s"]["per_pair_median"]["median"], *ov(t1, "V0_over_B1_wall_s"), *ov(t1, "V0_over_B1_cpu_s"), *ov(t1, "V0_over_B1rep_wall_s")), rel(E6 / "timing/timing_summary.json"), 6e-4)
add("Runtime", "run 2: wall 1.598 [1.586,1.736]; CPU 1.716 [1.706,1.836]; B1+rep 1.018 [1.015,1.071]", (1.598, 1.586, 1.736, 1.716, 1.706, 1.836, 1.018, 1.015, 1.071), lambda: (*ov(t2, "V0_over_B1_wall_s"), *ov(t2, "V0_over_B1_cpu_s"), *ov(t2, "V0_over_B1rep_wall_s")), rel(E6B / "timing/timing_summary.json"), 6e-4)
add("Runtime", "40 pairs, 5 reps, 0 failed; CV run 1 0.48%", (40, 5, 0, .0048), lambda: (t1["n_pairs"], t1["reps"], t1["failed_runs"], t1["systems"]["V0"]["wall_s"]["cv_across_reps"]["median"]), rel(E6 / "timing/timing_summary.json"), 1e-4)
add("Runtime", "load avg start 4.81 (run 1), 1.44 (run 2); end 1.65 / 2.24", (4.81, 1.44, 1.65, 2.24), lambda: (t1["hardware"]["loadavg"][0], t2["hardware"]["loadavg"][0], t1["hardware"]["loadavg_end"][0], t2["hardware"]["loadavg_end"][0]), rel(E6 / "timing/timing_summary.json"), 6e-3)
add("Runtime", "peak RSS median ~26 MiB V0, ~28 MiB B1, max ~700 MiB (rounded: 25.6, 27.8, 706.7)", (25.617, 27.781, 706.719), lambda: (t1["systems"]["V0"]["peak_rss_mib"]["per_pair_median"]["median"], t1["systems"]["B1"]["peak_rss_mib"]["per_pair_median"]["median"], t1["systems"]["V0"]["peak_rss_mib"]["per_pair_median"]["max"]), rel(E6 / "timing/timing_summary.json"), 1e-3)
# --- E7
tot = con["E7"]["verify_table"]
add("Results E7", "828 evidence directories, 0 failures", (828, 0), lambda: (tot["_n_dirs"], len(tot["_failures"]) if not isinstance(tot["_failures"], int) else tot["_failures"]), consrc)
add("Results E7", "corruption suite 42/42 as expected; 14 cases x 3", (42, 42, 14), lambda: (len(cr), sum(r["as_expected"] for r in cr), len({r["case"] for r in cr})), rel(E7 / "corruption_results.json"))
add("Results E7", "undetected (exit 0) cases: forge_meta_timing_rechained, forge_run_status_rechained, delete_verdict_json", ["delete_verdict_json", "forge_meta_timing_rechained", "forge_run_status_rechained"], lambda: sorted({r["case"] for r in cr if r["observed"] == 0}), rel(E7 / "corruption_results.json"))
add("Results E7", "exit 2 evidence_missing; exit 4 source_omitted_rechained", (2, 4), lambda: (next(r["observed"] for r in cr if r["case"] == "evidence_missing"), next(r["observed"] for r in cr if r["case"] == "source_omitted_rechained")), rel(E7 / "corruption_results.json"))
# --- conformance and tests
tm = re.search(r"\| \*\*Sum\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\*", trace)
add("Architecture/RQ", "135 rules: 78 conforming, 30 partial, 7 deviating, 14 not implemented, 2 unverifiable, 4 deferred", (78, 30, 7, 14, 2, 4, 135), lambda: tuple(int(x) for x in tm.groups()), "reports/phase2/PHASE2_TRACEABILITY_RECONCILIATION.md section 4 Sum row")
add("Architecture/Setup", "tests 286 passed, 1 skipped (E3 stage)", True, lambda: report_has(rep, "286 passed, 1 skipped"), "reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md section 9", kind="R")
add("Runtime", "E3 baselines-stage wall 20,880 s not used (suspend artefact)", True, lambda: report_has(rep, "20,880"), "reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md section 6", kind="R")

def close(a, b, tol):
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)) and len(a) == len(b): return all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool): return abs(a - b) <= tol
    return a == b or str(a) == str(b)
rows, bad, nv, nr = [], 0, 0, 0
for i, (where, claim, exp, act, src, tol, kind) in enumerate(C, 1):
    try: a = act()
    except Exception as e: a = f"ERROR {e!r}"
    ok = close(a, exp, tol)
    status = ("VERIFIED" if kind == "V" else "REPORT-ONLY") if ok else "MISMATCH"
    bad += not ok; nv += ok and kind == "V"; nr += ok and kind == "R"
    fmt = lambda x: str(x if not isinstance(x, float) else round(x, 4)).replace("|", "/")
    rows.append(f"| {i} | {where} | {claim.replace('|', '/')} | `{fmt(a)[:90]}` | `{src[:150]}` | {status} |")
out = ["# Numerical claim verification (generated; do not edit by hand)", "",
       "Generated by `paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/scripts/verify_numerical_claims.py`, which recomputes each claim from `results/v7b_phase2_summary/` (read-only) and compares it with the value quoted in the manuscript (within the rounding tolerance shown by the claim text).",
       "Statuses: VERIFIED = recomputed from tracked data; REPORT-ONLY = the raw input is not tracked (raw archives are outside git), so only the presence of the quoted number in the named Phase 2 report was checked; MISMATCH = disagreement.", "",
       f"**Totals: {len(C)} claim groups; {nv} VERIFIED; {nr} REPORT-ONLY; {bad} MISMATCH.** Each group covers several numbers (the 'Actual' column shows the recomputed tuple).", "",
       "Unverifiable from tracked data (REPORT-ONLY): run-record counts 13,764 / 5,930 / 13,250 / 4,746 (E4), the 84 witness-id-change pairs, the 320/321 strict-key E3 versus E4-V0 consistency, and the test count 286/1: they come from raw evidence directories or a test log not tracked in git. The `~65% fewer runs` statement rests on the run-record counts; the tracked CPU sums (225.1 s versus 546.8 s) are directionally consistent but load-sensitive.",
       "Also not recomputable here: the E1/E3 commit hashes (read from each `RUN_RECORD.md`) and the three manually inspected evidence packages for `unmodelled_change` (E1 report, section 5). Derived arithmetic in the text: percentage points are rate differences x 100 (for example -0.1038 -> -10.4pp); abstention 122 = 18 + 104; 0.123/0.226 are 13/106 and 24/106.", "",
       "| # | Where | Claim | Actual (recomputed) | Source | Status |", "|---|---|---|---|---|---|"] + rows
(P / "NUMERICAL_CLAIM_VERIFICATION.md").write_text("\n".join(out) + "\n")
print(f"{len(C)} claim groups: {nv} verified, {nr} report-only, {bad} mismatch")
for r in rows:
    if "MISMATCH" in r: print(r)
sys.exit(1 if bad else 0)

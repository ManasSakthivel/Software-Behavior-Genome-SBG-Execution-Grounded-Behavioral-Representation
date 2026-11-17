#!/usr/bin/env python3
"""Generate tables/*.tex from results/ files. Run from anywhere: python3 scripts/make_tables.py
Writes tables/T*.tex, tables/derived_crosstab.csv and tables/SOURCES.json (table -> source files, used by check_manuscript.py)."""
import csv, json, collections, pathlib

PAPER = pathlib.Path(__file__).resolve().parent.parent
ROOT = PAPER.parent.parent
ST = "results/postfix/statistics/"
PROC = "results/postfix/processed/dev_pairs_per_system.csv"
OUT = PAPER / "tables"
sources = {}

def rd(rel):
    return list(csv.DictReader(open(ROOT / rel)))

def f3(x): return f"{float(x):.3f}"
def ci(r, e, lo, hi): return f"{f3(r[e])} [{f3(r[lo])}, {f3(r[hi])}]"

def write(name, src, cols, rows, caption, label, wide=False):
    env = "table*" if wide else "table"
    body = "\n".join(" & ".join(str(c) for c in r) + r" \\" for r in rows)
    spec = "l" + "r" * (len(cols) - 1)
    tex = (f"\\begin{{{env}}}[t]\n\\centering\\scriptsize\n\\caption{{{caption} Source: " +
           ", ".join(f"\\path{{{s}}}" for s in src) + f".}}\n\\label{{{label}}}\n"
           f"\\begin{{tabular}}{{{spec}}}\n\\hline\n" + " & ".join(cols) + " \\\\\n\\hline\n" + body +
           f"\n\\hline\n\\end{{tabular}}\n\\end{{{env}}}\n")
    (OUT / f"{name}.tex").write_text(tex)
    sources[name] = src

SYS = ["V7-B", "B1", "B1+rep", "B3", "B4"]
sm = {(r["system"], r["outcome"]): r for r in rd(ST + "system_metrics.csv")}
cost = {r["system"]: r for r in rd(ST + "cost.csv")}

# T1: denominators per arm
pd_ = [r for r in rd(ST + "per_dataset.csv") if r["system"] == "V7-B"]
write("T1_datasets", [ST + "per_dataset.csv"], ["Arm", "DIV (n)", "NO\\_OBS\\_DIFF (n)", "All (n)"],
      [(r["dataset"].replace("_", "\\_"), r["den_div"], r["den_no"], r["den_all"]) for r in pd_],
      "Primary-denominator pairs per arm (truth rules in text; suspect, unlabelled and not-driven pairs excluded).", "tab:datasets")

# T2: system metrics
rows = []
for s in SYS:
    rows.append((s, ci(sm[(s, "detection")], "est", "lo", "hi"), ci(sm[(s, "false_assurance")], "est", "lo", "hi"),
                 ci(sm[(s, "abstention")], "est", "lo", "hi"), ci(sm[(s, "false_alarm")], "est", "lo", "hi"),
                 f"{float(cost[s]['cpu_s_median']):.2f} ({float(cost[s]['cpu_s_sum']):.0f})"))
write("T2_system_metrics", [ST + "system_metrics.csv", ST + "cost.csv"],
      ["System", "Detection (DIV)", "False assur. (DIV)", "Abstention", "False alarm", "CPU s median (sum)"], rows,
      "Descriptive metrics, 95\\% project-cluster bootstrap CI (B=10000, seed 42), post-fix run. Exploratory; non-pristine development data.",
      "tab:metrics", wide=True)

# T3: paired vs B1
pc = rd(ST + "paired_comparisons.csv")
rows = []
for r in pc:
    if r["outcome"] in ("detection", "false_assurance") and r["test"] in ("V7-B", "B1+rep", "B3"):
        rows.append((r["test"], r["outcome"].replace("_", " "), f3(r["improvement"]), f"[{f3(r['impr_lo'])}, {f3(r['impr_hi'])}]",
                     r["b_test_only"], r["c_ref_only"], f3(r["p_signflip"]), f3(r["p_holm"]), r["meets_plus10pp"]))
write("T3_paired", [ST + "paired_comparisons.csv"],
      ["Test", "Outcome", "Improv.", "95\\% CI", "b", "c", "p sign-flip", "p Holm", "+10pp"], rows,
      "Paired comparisons against B1 (improvement is positive when better; b = test-only, c = reference-only successes). Unadjusted exploratory; no row meets the +10pp rule.",
      "tab:paired", wide=True)

# T4: risk-coverage
rc = rd(ST + "risk_coverage.csv")
rows = [(r["system"], r["min_sufficiency_for_NDO"], f3(r["coverage"]), f3(r["risk"]), r["decided"], r["eligible"])
        for r in rc if r["system"] in ("V7-B", "B1", "B1+rep", "B3") and r["min_sufficiency_for_NDO"] in ("none", "S2", "S3")]
write("T4_risk_coverage", [ST + "risk_coverage.csv"],
      ["System", "Min. level", "Coverage", "Risk", "Decided", "Eligible"], rows,
      "Risk--coverage against generator labels. Baselines carry no sufficiency level, so their S-level rows are not comparable; V7-B at S3 is empty because S3 is never emitted.",
      "tab:riskcov")

# T5: class counts
cc = rd(ST + "class_counts.csv")
rows = [(r["system"], r["truth"].replace("_", "\\_"), r["verdict_n"].replace("_", "\\_"), r["n"])
        for r in cc if r["system"] in ("V7-B", "B1") and r["truth"] in ("DIV", "NO_OBS_DIFF")]
write("T5_class_counts", [ST + "class_counts.csv"], ["System", "Truth", "Verdict", "n"], rows,
      "Verdict counts by truth class for V7-B and B1 (post-fix).", "tab:classcounts")

# T6: power
pw = json.load(open(ROOT / ST / "power_actual.json") if False else open(ROOT / (ST + "power_actual.json")))
rows = []
for g in pw["grid"]:
    if g["pi"] == 0.066:
        rows.append((g["rho"], g["alpha"], "n/r" if g["power_5pp"] is None else f"{g['power_5pp']:.3f}",
                     "not reachable" if g["power_10pp"] is None else f"{g['power_10pp']:.3f}"))
write("T6_power", [ST + "power_actual.json"], ["ICC rho", "alpha", "Power +5pp", "Power +10pp"], rows,
      "Simulated power on the observed development design (K=78, 106 pairs, discordance 0.066); simulation assumptions A1--A4 are in the source file; not a prediction of system performance.",
      "tab:power")

# derived crosstabs (computed here from the per-pair CSV; written as a file so the checker can verify table numbers)
pairs = collections.defaultdict(dict)
meta = {}
for r in rd(PROC):
    pairs[r["pair_id"]][r["system"]] = r
    meta[r["pair_id"]] = r
def cat(r):
    v = r["verdict"]
    if v == "NO_DIVERGENCE_OBSERVED": return "NDO_" + r["sufficiency"]
    return {"DIVERGENT_OBSERVABLE": "DIVERGENT", "INSUFFICIENT": "INSUFFICIENT"}.get(v, "NOT_DRIVEN")
der = collections.Counter()
for pid, s in pairs.items():
    ds = meta[pid]["dataset"]
    der[("v7b_by_arm", f"{ds}|{cat(s['V7-B'])}")] += 1
    if ds.startswith("synthetic") and s["B1"]["verdict"] == "NO_DIVERGENCE_OBSERVED":
        der[("v7b_on_B1_NDO_synthetic", f"{ds}|{cat(s['V7-B'])}")] += 1
    if s["B1"]["verdict"] != s["B1+rep"]["verdict"]:
        der[("b1_vs_b1rep", "pairs_with_different_verdict")] += 1
    if s["V7-B"]["verdict"] == "DIVERGENT_OBSERVABLE" and s["B1"]["verdict"] != "DIVERGENT_OBSERVABLE":
        der[("overlap", "v7b_divergent_b1_not")] += 1
    if s["B1"]["verdict"] == "DIVERGENT_OBSERVABLE" and s["V7-B"]["verdict"] != "DIVERGENT_OBSERVABLE":
        der[("overlap", "b1_divergent_v7b_not")] += 1
    der[("total", "pairs")] += 1
for a in ("quixbugs_buggy_fixed","quixbugs_sp_negatives","synthetic_changed","synthetic_equivalent","bugsinpy_units"):
    for c in ("DIVERGENT","NDO_S2","NDO_S1","INSUFFICIENT","NOT_DRIVEN"): der[("v7b_by_arm", f"{a}|{c}")] += 0
for a in ("synthetic_changed","synthetic_equivalent"):
    for c in ("INSUFFICIENT","NDO_S2","NDO_S1"): der[("v7b_on_B1_NDO_synthetic", f"{a}|{c}")] += 0
der[("overlap","v7b_divergent_b1_not")] += 0
with open(OUT / "derived_crosstab.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["group", "key", "n"])
    for (g, k), n in sorted(der.items()): w.writerow([g, k, n])
DER = "paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/tables/derived_crosstab.csv"

# T7: sufficiency vs label on pairs where B1 saw no difference (synthetic arms)
cols = ["NDO_S2", "NDO_S1", "INSUFFICIENT"]
rows = []
for ds, lab in (("synthetic_changed", "CHANGED"), ("synthetic_equivalent", "EQUIVALENT")):
    rows.append((lab,) + tuple(der[("v7b_on_B1_NDO_synthetic", f"{ds}|{c}")] for c in cols))
write("T7_sufficiency_vs_label", [DER], ["Generator label", "V7-B S2", "V7-B S1", "V7-B INSUFFICIENT"], rows,
      "V7-B outcome on synthetic pairs where B1 saw no difference, by generator label (suspect labels included, as in the red-team analysis). If sufficiency separated labels, S2 would be purer in EQUIVALENT than INSUFFICIENT; it is not clearly so.",
      "tab:suffsep")

# T8: V7-B outcome by arm
arms = ["quixbugs_buggy_fixed", "quixbugs_sp_negatives", "synthetic_changed", "synthetic_equivalent", "bugsinpy_units"]
cs = ["DIVERGENT", "NDO_S2", "NDO_S1", "INSUFFICIENT", "NOT_DRIVEN"]
rows = [(a.replace("_", "\\_"),) + tuple(der[("v7b_by_arm", f"{a}|{c}")] for c in cs) for a in arms]
write("T8_v7b_by_arm", [DER], ["Arm", "DIVERGENT", "S2", "S1", "INSUFF.", "Not driven"], rows,
      "V7-B verdict and level per arm, all pairs including suspect and unlabelled (post-fix).", "tab:byarm")


# T9/T10 from the post-fix K1 spike summary
KS = "results/postfix/processed/k1_spike_summary.json"
ks = json.load(open(ROOT / KS))
rows = []
for arm in ("quixbugs", "quixbugs_neg", "synthetic", "bugsinpy_units"):
    for reason, n in ks[arm]["insufficient_reasons"].items():
        if not reason.startswith("entry_policy"):
            rows.append((arm.replace("_", "\\_"), reason.replace("_", "\\_").replace(" (engine supports top-level functions only)", ""), n))
write("T9_insufficient_reasons", [KS], ["Arm", "Primary INSUFFICIENT reason", "n"], rows,
      "Primary reasons for INSUFFICIENT per arm (post-fix). Most are engine coverage gaps (renamed entries, generators, class units), not a sufficiency judgement.",
      "tab:reasons")
rows = [(a.replace("_", "\\_"), ks[a]["n_pairs"], ks[a]["n_runnable"], ks[a]["n_projects"], ks[a]["n_rerun"] if "n_rerun" in ks[a] else ks[a]["determinism"]["n_rerun"],
         ks[a]["determinism"]["identical"]) for a in ("quixbugs", "quixbugs_neg", "synthetic", "bugsinpy_units")]
write("T10_k1_determinism", [KS], ["Arm", "Pairs", "Runnable", "Projects", "Re-run", "Identical"], rows,
      "K1 spike per-arm counts and whole-pair re-run determinism (post-fix; the synthetic arm was not re-run after the fix). K1 itself is NOT MET.",
      "tab:k1")

json.dump(sources, open(OUT / "SOURCES.json", "w"), indent=1)
print("wrote", len(sources), "tables")

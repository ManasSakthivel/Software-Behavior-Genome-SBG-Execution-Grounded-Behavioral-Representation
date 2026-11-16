"""d4_08_render.py -- assemble STATS_REPORT.md from scripts/d4_report_template.md + the JSON/CSV outputs of d4_01..d4_07.

Every {{T:name}} placeholder in the template is replaced by a markdown table generated here directly from the outputs
(no hand-typed numbers in tables).  Narrative numbers in the template are checked by scripts/d4_09_check_report.py.
"""
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "raw" / "WPD-D4_stats"


def J(name):
    return json.load(open(OUT / name))


def CSV(name):
    return list(csv.DictReader(open(OUT / name)))


def md(headers, rows):
    s = "| " + " | ".join(headers) + " |\n|" + "|".join("---" for _ in headers) + "|\n"
    for r in rows:
        s += "| " + " | ".join("" if x is None else str(x) for x in r) + " |\n"
    return s


def f(x, nd=3):
    if x is None or x == "":
        return ""
    return f"{float(x):.{nd}f}"


def ci(lo, hi, nd=3):
    return f"[{f(lo, nd)}, {f(hi, nd)}]"


def tag(st):
    return "PRE-REG" if st.startswith("PRE") else "POST-HOC"


TABLES = {}

# ---------------------------------------------------------------- T1 pair sets
sets = J("01_pair_sets.json")
rows = []
for a in sets["analysis_sets"]:
    rows.append([a["set_id"], tag(a["status"]), a["corpus"], a["n_pairs"], a["n_pos"], a["n_neg"], a["n_bug_clusters"],
                 a.get("n_project_clusters") or "-", a["n_unevaluated_scored_as_impute"], a["description"]])
TABLES["T1_sets"] = md(["set_id", "status", "corpus", "n", "pos", "neg", "bug clusters", "project clusters",
                        "unevaluated scored as 0", "definition"], rows)

inv = sets["corpus_inventory"]
rows = []
for c, v in inv.items():
    rows.append([c, v["n_rows"], v["by_label"].get("1"), v["by_label"].get("0"), v["n_evaluated_v7"], v["n_unevaluated_v7"],
                 v["unevaluated_by_label"].get("1", 0), v["unevaluated_by_label"].get("0", 0),
                 v["n_bug_clusters_all"], v["n_bug_clusters_evaluated_v7"],
                 json.dumps(v["unevaluated_by_failure"]), ", ".join(v["bugs_with_eval_negative_but_no_eval_positive"]) or "-"])
TABLES["T2_inventory"] = md(["corpus", "pairs", "pos", "neg", "evaluated (v7)", "unevaluated", "unevaluated pos", "unevaluated neg",
                             "bugs (all)", "bugs (evaluated)", "unevaluated by failure", "bugs with evaluated neg but no evaluated pos"], rows)

rows = []
for c, v in inv.items():
    for k in sorted(v["by_kind_all"]):
        rows.append([c, k, v["by_kind_all"][k], v["by_kind_evaluated_v7"].get(k, 0), v["by_kind_unevaluated_v7"].get(k, 0)])
TABLES["T3_by_kind"] = md(["corpus", "pair kind", "all", "evaluated (v7)", "unevaluated (v7)"], rows)

# ---------------------------------------------------------------- T4 inference
rows = []
for r in CSV("02_inference_table.csv"):
    rows.append([r["set"], tag(r["status"]), r["cluster_level"], r["n"], f"{r['n_pos']}/{r['n_neg']}", r["n_clusters"], f(r["auroc"]),
                 ci(r["pct_lo"], r["pct_hi"]), ci(r["bca_lo"], r["bca_hi"]),
                 f(r["perm_p_lower_tail(auroc<0.5)"], 4), f(r["perm_p_upper_tail(auroc>0.5)"], 4), f(r["onesided95_upper"])])
TABLES["T4_inference"] = md(["set", "status", "cluster unit", "n", "pos/neg", "clusters", "AUROC", "95% percentile CI", "95% BCa CI",
                             "perm p (AUROC<0.5)", "perm p (AUROC>0.5)", "one-sided 95% upper bound"], rows)

# ---------------------------------------------------------------- T5 zero decomposition
rows = []
for r in CSV("03_zero_decomposition.csv"):
    rows.append([r["set"], tag(r["status"]), f"{r['n_pos']}/{r['n_neg']}", f(r["pos_zero_frac"]), f(r["neg_zero_frac"]),
                 f(r["hurdle_diff"]), f(r["fisher_p2"], 4), f(r["tie_mass"]), f(r["auroc_ties0"]), f(r["auroc"]), f(r["auroc_ties1"]),
                 f(r["auroc_gt0_only_POSTHOC"]) + " (biased)"])
TABLES["T5_zero"] = md(["set", "status", "pos/neg", "P(s=0|pos)", "P(s=0|neg)", "hurdle diff P(s>0|pos)-P(s>0|neg)", "Fisher p (2-sided)",
                        "tie mass", "AUROC ties->0", "AUROC (ties=0.5)", "AUROC ties->1", "AUROC among s>0 (post-hoc selection)"], rows)

# ---------------------------------------------------------------- T6 baselines
B = J("04_baselines.json")["sets"]
KEY = ["BP-v7-EVAL", "BP-v8-exSP2", "QC-v7-ALL", "QC-v8-exSP2", "QD-v7-EVAL"]
ORDER = ["sbg_v5", "sbg_v3", "sbg_state", "sbg_temporal", "static_token", "static_ast", "exception_fraction", "call_count", "coverage_size", "combined_shortcut"]
rows = []
for sid in KEY:
    lv = B[sid]["levels"]["bug"]
    for p in ORDER:
        if p not in lv["predictors"]:
            continue
        pr = lv["predictors"][p]
        pd_ = lv["paired_vs_sbg_v5"].get(p)
        if pd_:
            rows.append([sid, tag(B[sid]["status"]), p, f(pr["auroc"]), ci(*pr["ci95_percentile"]), f(pd_["delta"]), ci(*pd_["ci95_percentile"]),
                         f(pd_["p_two_sided_boot"], 4), f(pd_.get("holm_adj_p_over_prereg_family"), 4) if "holm_adj_p_over_prereg_family" in pd_ else "-"])
        else:
            rows.append([sid, tag(B[sid]["status"]), p, f(pr["auroc"]), ci(*pr["ci95_percentile"]), "-", "-", "-", "-"])
TABLES["T6_baselines"] = md(["set", "status", "predictor", "AUROC", "95% CI (bug-cluster bootstrap)", "paired Δ vs sbg_v5", "Δ 95% CI",
                             "p (2-sided boot)", "Holm-adj p (family of 5 prereg-style baselines)"], rows)

SH = J("04_shortcut_by_negative_type.json")
rows = []
for sid in ["BP-v7-ALL", "QC-v7-ALL"]:
    if sid not in SH["auroc_pos_vs_each_negative_type"]:
        continue
    for k, v in SH["auroc_pos_vs_each_negative_type"][sid].items():
        rows.append([sid, k, v["n_pos"], v["n_neg"], f(v["sbg_v5"]), f(v["static_ast"]), f(v["static_token"]), f(v["F:edit_lines"]),
                     f(v["F:edit_tokens"]), f(v["F:variant_is_unparse_canonical"]), f(v["F:comment_loss"])])
TABLES["T7_shortcut"] = md(["set (all pairs, static features exist for all rows)", "negative type", "pos", "neg", "sbg_v5", "static_ast", "static_token",
                            "edit_lines", "edit_tokens", "variant_is_unparse_canonical", "comment_loss"], rows)

# ---------------------------------------------------------------- T8 power
P = J("05_power.json")
rows = []
for sid, r in P["what_cis_rule_out"].items():
    if sid not in ("BP-v7-EVAL", "BP-v8-exSP2", "BP-v8-EVAL", "QC-v7-ALL", "QC-v8-exSP2", "QD-v7-EVAL", "QD-v7-ALL"):
        continue
    for lv, d in r["levels"].items():
        rows.append([sid, tag(r["status"]), lv, d["n_clusters"], f(r["auroc"]), ci(*d["ci95_percentile"]), f(d["ci_width"]),
                     f(d["one_sided_95_upper"]), ", ".join(str(x) for x in d["two_sided_CI_excludes_theta>="]) or "-",
                     "yes" if d["CI_includes_0.5"] else "no"])
TABLES["T8_rule_out"] = md(["set", "status", "cluster unit", "clusters", "AUROC", "95% CI", "CI width", "one-sided 95% upper",
                            "two-sided CI excludes true AUROC >= (of 0.5,0.6,0.7,0.75,0.8,0.897)", "CI contains 0.5"], rows)

rows = []
for sid, d in P["simulation"].items():
    for scen, sc in d["scenarios"].items():
        for lv in sc["size_at_mu0"]:
            hw = sc["rows"][0]["mean_95CI_halfwidth(jackknife-approx)"][lv]
            rows.append([sid, scen, lv, d["n"], d["n_pos"], d["neg_zero_frac_used_for_kappa"], f(sc["rho_p"]), f(sc["rho_b"]), sc["size_at_mu0"][lv], f(hw), sc["MDE_theta_at_80pct_power"][lv]])
TABLES["T9_power"] = md(["design", "scenario", "cluster unit", "n", "pos", "P(s=0|neg) used", "rho_project", "rho_bug",
                         "size at mu=0 (nominal 0.025 one-sided)", "mean 95% CI half-width", "MDE: true AUROC with 80% power"], rows)

rows = []
for sid, d in P["simulation"].items():
    sc = d["scenarios"]["rho_est"]
    for lv in sc["size_at_mu0"]:
        for r in sc["rows"]:
            rows.append([sid, lv, r["mu"], r["theta_true"], r["mean_theta_hat"], r["power_or_size"][lv]])
TABLES["T9b_powercurve"] = md(["design", "cluster unit", "mu (latent shift)", "true AUROC", "mean observed AUROC (shrinks: ties/censoring)", "power (one-sided 2.5%)"], rows)

rows = []
for sid, d in P["simulation"].items():
    rows.append([sid, d["icc_bug_rank_negatives"], d["icc_project_rank_negatives"], d["rho_p_est"], d["rho_b_est"], d["kappa"]])
TABLES["T9c_icc"] = md(["design", "ICC bug (negatives, rank)", "ICC project (negatives, rank)", "rho_project est.", "rho_bug est.", "kappa"], rows)

# ---------------------------------------------------------------- T10 sensitivity
rows = []
for r in CSV("06_sensitivity_table.csv"):
    if r["kind"] == "pair-set":
        rows.append([r["config"], r["variant"], r["n"], r["n_pos"], r["auroc_or_range"]])
TABLES["T10_sens_sets"] = md(["config", "pair-set variant", "n", "pos", "AUROC"], rows)
rows = []
for r in CSV("06_sensitivity_table.csv"):
    if r["kind"].startswith("unevaluated"):
        rows.append([r["config"], r["kind"].replace("unevaluated-imputation", "").strip("()"), r["variant"], r["n"], r["auroc_or_range"]])
TABLES["T11_sens_impute"] = md(["config", "pair subset", "imputation of unevaluated pairs", "n unevaluated", "AUROC"], rows)
rows = []
for r in CSV("06_sensitivity_table.csv"):
    if r["kind"].startswith("LOCO"):
        rows.append([r["config"], r["kind"], r["variant"], r["n"], r["auroc_or_range"]])
TABLES["T12_sens_loco"] = md(["config", "leave-one-cluster-out unit", "pair set", "clusters", "AUROC range"], rows)
rows = []
for r in CSV("06_sensitivity_table.csv"):
    if r["kind"] == "pos-vs-single-negative-type":
        rows.append([r["config"], r["variant"], r["n"], r["auroc_or_range"]])
TABLES["T13_sens_negtype"] = md(["config", "negative type", "n pairs", "AUROC (positives vs that negative type only)"], rows)

# ---------------------------------------------------------------- T14 forking paths
rows = []
for r in CSV("07_forking_paths.csv"):
    rows.append([r["id"], r["corpus"], r["description"], r["status"], r["auroc"] or "-", r["n_pairs"] or "-", r["date"], r["how"]])
TABLES["T14_forking"] = md(["id", "corpus", "variant", "status", "AUROC (D4 recomputed unless noted)", "n pairs", "date", "how obtained"], rows)

fk = J("07_forking_paths.json")
rows = []
for c, v in fk["summary"].items():
    for grp in ("pre_registered", "post_hoc", "all_variants"):
        g = v[grp]
        rows.append([c, grp, g["k"], g["min"], g["max"], g["n_lt_0.5"], g["n_ge_0.5"]])
TABLES["T15_fork_summary"] = md(["corpus", "group", "variants (k)", "min AUROC", "max AUROC", "# < 0.5", "# >= 0.5"], rows)

# ---------------------------------------------------------------- inputs manifest
man = sets["input_manifest"]
rows = [[k, v["path"], v["sha256"]] for k, v in man.items()]
TABLES["T0_inputs"] = md(["key", "path (relative to workspace root)", "sha256"], rows)

# ---------------------------------------------------------------- render
tpl = (HERE / "d4_report_template.md").read_text()


def sub(m):
    k = m.group(1)
    if k not in TABLES:
        raise SystemExit(f"unknown table placeholder {k}")
    return TABLES[k]


txt = re.sub(r"\{\{T:([A-Za-z0-9_]+)\}\}", sub, tpl)
(OUT / "STATS_REPORT.md").write_text(txt)
print("wrote", OUT / "STATS_REPORT.md", len(txt), "chars;", len(TABLES), "tables")

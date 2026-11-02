"""Trace check: every headline number quoted in RESEARCH_STATUS_V4.md must equal the value in its source artifact.   python experiments/final/verify_trace_v4.py"""
import json, pathlib, sys
REPO = pathlib.Path(__file__).resolve().parents[2]
PE = REPO / "artifacts/paper_evidence"
NORM = lambda t: t.replace("\u2212", "-")                                         # noqa: E731
R = NORM((PE / "RESEARCH_STATUS_V4.md").read_text())
J = lambda n: json.loads((PE / n).read_text())                                   # noqa: E731
V10, DEV, VAL, PH = J("V10_INDEPENDENT_EVALUATION.json"), J("V4_DEV_EVALUATION.json")["dev"], J("V9_VAL_EVALUATION.json")["v9c_matched"], J("V10_POSTHOC_SUPPLEMENT.json")
ADDR = J("raw/zero_score_address_correction_v1.json")["summary"]
P, T, H = V10["predictors"], V10["pre_declared_tests"]["deltas"], V10["pre_declared_tests"]["holm"]
f3 = lambda x: f"{x:.3f}"                                                         # noqa: E731
sg = lambda x: f"{x:+.3f}"                                                        # noqa: E731
ci = lambda c: f"[{c[0]:.3f}, {c[1]:.3f}]"                                        # noqa: E731
CHECKS = [
    (f"{VAL['n_pairs'] and 160} / {VAL['n_pairs']} = 37.04 %", round(100 * 160 / VAL["n_pairs"], 2) == 37.04 and VAL["fraction_sbg_v5_exactly_zero"] == 0.3704),
    ("**638 evaluated pairs, 319 matched sets, 19 programs**", (V10["n_pairs"], V10["n_matched_sets"], V10["n_programs"]) == (638, 319, 19)),
    ("3 unevaluated", V10["n_unevaluated"] == 3),
    (f"| SBG V5 | {f3(P['sbg_v5']['auroc'])} | {ci(P['sbg_v5']['ci95_cluster_bootstrap'])} |", True),
    (f"| SBG V6 (experimental) | {f3(P['sbg_v6']['auroc'])} | {ci(P['sbg_v6']['ci95_cluster_bootstrap'])} |", True),
    (f"| edit size forward | {f3(P['edit']['auroc'])} | {ci(P['edit']['ci95_cluster_bootstrap'])} |", True),
    (f"| edit size reversed | {f3(P['edit_reversed']['auroc'])} | {ci(P['edit_reversed']['ci95_cluster_bootstrap'])} |", True),
    (f"| coverage_size | {f3(P['coverage_size']['auroc'])} | {ci(P['coverage_size']['ci95_cluster_bootstrap'])} |", True),
    (f"| model edit+exec | {f3(P['M_EX']['auroc'])} | {ci(P['M_EX']['ci95_cluster_bootstrap'])} |", True),
    (f"| model edit+SBG V5 | {f3(P['M_E+V5']['auroc'])} | {ci(P['M_E+V5']['ci95_cluster_bootstrap'])} |", True),
    (f"| model edit+exec+SBG V5 | {f3(P['M_EX+V5']['auroc'])} | {ci(P['M_EX+V5']['ci95_cluster_bootstrap'])} |", True),
    (f"adjusted p {H['H1_sbg_v5_above_chance']['p_adjusted']}", True),
    (f"**{sg(T['H2_E+V5_minus_E']['delta'])}** [{sg(T['H2_E+V5_minus_E']['ci_lower'])}, {sg(T['H2_E+V5_minus_E']['ci_upper'])}]", True),
    (f"**{sg(T['H3_V5_minus_edit_forward']['delta'])}** [{sg(T['H3_V5_minus_edit_forward']['ci_lower'])}, {sg(T['H3_V5_minus_edit_forward']['ci_upper'])}]", True),
    (f"**{ 'H4 edit+exec+SBG − edit+exec ' + sg(T['H4_EX+V5_minus_EX']['delta']) } [{sg(T['H4_EX+V5_minus_EX']['ci_lower'])}, {sg(T['H4_EX+V5_minus_EX']['ci_upper'])}], adjusted p {H['H4_EX+V5_minus_EX']['p_adjusted']:.1f}", True),
    (f"{sg(T['H5_V6_minus_V5']['delta'])} [{T['H5_V6_minus_V5']['ci_lower']:+.4f}, {T['H5_V6_minus_V5']['ci_upper']:+.3f}], Holm-adjusted p {H['H5_V6_minus_V5']['p_adjusted']:.3f}", True),
    (f"H6 {sg(T['H6_EX+V6_minus_EX']['delta'])} [{sg(T['H6_EX+V6_minus_EX']['ci_lower'])}, {sg(T['H6_EX+V6_minus_EX']['ci_upper'])}]", True),
    (f"mean edit {V10['mean_edit']['CHANGED']:.2f} (CHANGED) vs {V10['mean_edit']['EQUIVALENT']:.2f} (EQUIVALENT), forward-edit AUROC {f3(P['edit']['auroc'])}", True),
    (f"SBG V5 is {V10['edit_size_exact_stratified']['sbg_v5']['auroc']:.3f}", True),
    (f"edit (0.955) than SBG (0.931)", round(V10["matched_set_concordance"]["edit"]["concordance"], 3) == 0.955 and round(V10["matched_set_concordance"]["sbg_v5"]["concordance"], 3) == 0.931),
    (f"({PH['fraction_sets_changed_edit_gt_equivalent_edit']*100:.1f} % of sets", True),
    (f"SBG V5 overall {P['sbg_v5']['exact_zero_rate']*100:.1f} %; CHANGED {P['sbg_v5']['exact_zero_rate_changed']*100:.1f} %, EQUIVALENT {P['sbg_v5']['exact_zero_rate_equivalent']*100:.1f} %", True),
    (f"SC-6 CHANGED {V10['changed_zero_rate_by_sc_family']['SC-6']['sbg_v5']*100:.1f} % zero", True),
    (f"V5 − coverage_size {sg(PH['deltas']['V5_minus_coverage_size']['delta'])} [{sg(PH['deltas']['V5_minus_coverage_size']['ci_lower'])}, {sg(PH['deltas']['V5_minus_coverage_size']['ci_upper'])}]", True),
    (f"V5 vs M_EX {sg(PH['deltas']['V5_minus_M_EX']['delta'])} [{sg(PH['deltas']['V5_minus_M_EX']['ci_lower'])}, {sg(PH['deltas']['V5_minus_M_EX']['ci_upper'])}]", True),
    (f"110 sets) AUROC V5 {PH['rewrite_only_equivalents_SP3_SP5_SP8_SP11']['auroc_sbg_v5']:.3f} {ci(PH['rewrite_only_equivalents_SP3_SP5_SP8_SP11']['ci95'])}", PH["rewrite_only_equivalents_SP3_SP5_SP8_SP11"]["n_sets"] == 110),
    (f"ΔAUROC(V6 − V5) = {DEV['paired_deltas']['V6_minus_V5 (sbg)']['delta']:+.4f} [{DEV['paired_deltas']['V6_minus_V5 (sbg)']['ci_lower']:+.4f}, {DEV['paired_deltas']['V6_minus_V5 (sbg)']['ci_upper']:+.4f}]", True),
    (f"only {DEV['changed_v5_zero']['n'] - DEV['changed_v5_zero']['v6_still_zero']} of {DEV['changed_v5_zero']['n']} zero CHANGED pairs rescued on dev", True),
    (f"(v9c dev, {DEV['n_pairs']} pairs, {DEV['n_programs']} programs", True),
    (f"| v9c val (confirmatory-by-freeze) | {f3(VAL['predictors']['sbg_v5']['auroc'])} {ci(VAL['predictors']['sbg_v5']['ci95_cluster_bootstrap'])}", True),
    (f"| v9c dev (exploratory) | {f3(DEV['predictors']['sbg_v5']['auroc'])} {ci(DEV['predictors']['sbg_v5']['ci95_cluster_bootstrap'])}", True),
    (f"| v10 independent (single run) | {f3(P['sbg_v5']['auroc'])} {ci(P['sbg_v5']['ci95_cluster_bootstrap'])}", True),
    (f"H4 {sg(VAL['pre_declared_tests']['H4']['delta'])[0:6]} n.s.", VAL["pre_declared_tests"]["H4"]["delta"] > 0),
    (f"Only **{ADDR['real_value_difference']}**", True),
    (f"differ only by object addresses/renamed qualnames ({ADDR['address_or_qualname_only']})", True),
]
bad = 0
for lit, ok in CHECKS:
    present = NORM(lit) in R
    if not (present and ok):
        bad += 1
        print("FAIL", "(absent from report)" if not present else "(value mismatch)", "::", lit)
print(f"{len(CHECKS) - bad}/{len(CHECKS)} trace checks passed")
sys.exit(1 if bad else 0)

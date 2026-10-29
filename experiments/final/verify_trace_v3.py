"""Trace check: every headline number quoted in RESEARCH_STATUS_V3.md must equal the value in its source artifact.

Each entry is (literal as printed in the report, artifact value, rounding digits).
Fails (exit 1) on any mismatch or if the literal is absent from the report.

    python experiments/final/verify_trace_v3.py
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
PE = REPO / "artifacts/paper_evidence"
REPORT = (PE / "RESEARCH_STATUS_V3.md").read_text()


def J(name):
    return json.loads((PE / name).read_text())


VAL = J("V9_VAL_EVALUATION.json")["v9c_matched"]
T = VAL["pre_declared_tests"]
V8T = J("V8_TEST_EVALUATION.json")["VALID"]
LAB = J("LABEL_GENERATION_AUDIT.json")["splits"]
EXT = J("EXTERNAL_RESCORE_V8.json")["corpora"]
OLD = J("DIAGNOSTIC_EXTERNAL.json")
AUD = J("EXTERNAL_NEGATIVE_AUDIT.json")["effect_of_excluding_invalid_negatives"]
HS = J("raw/hashseed_sensitivity.json")


def rev(split):
    return LAB[split]["independent_edit_size_auroc"]["edit_canon"]["reversed_larger_edit_means_EQUIVALENT"]


# (literal printed in report, artifact value, decimals, sign-prefix "+" if positive)
CHECKS = [
    ("0.751", VAL["predictors"]["sbg_v5"]["auroc"], 3, False),
    ("[0.706, 0.794]", VAL["predictors"]["sbg_v5"]["ci95_cluster_bootstrap"], 3, False),
    ("0.678", VAL["predictors"]["coverage_size"]["auroc"], 3, False),
    ("0.611", VAL["predictors"]["edit"]["auroc"], 3, False),
    ("0.723", VAL["predictors"]["M_ES"]["auroc"], 3, False),
    ("0.690", VAL["predictors"]["M_EX"]["auroc"], 3, False),
    ("0.711", VAL["predictors"]["M_ESX"]["auroc"], 3, False),
    ("+0.112", T["H2"]["delta"], 3, True),
    ("[0.075, 0.148]", [T["H2"]["ci_lower"], T["H2"]["ci_upper"]], 3, False),
    ("+0.140", T["H3"]["delta"], 3, True),
    ("+0.021", T["H4"]["delta"], 3, True),
    ("[−0.005, 0.048]", [T["H4"]["ci_lower"], T["H4"]["ci_upper"]], 3, False),
    ("0.117", T["holm"]["H4_edit_exec_plus_sbg_minus_edit_exec"]["p_adjusted"], 3, False),
    ("0.735", VAL["edit_size_exact_stratified"]["sbg_v5"]["auroc"], 3, False),
    ("92.4 %", 100 * VAL["matched_set_concordance"]["edit"]["concordance"], 1, False),
    ("80.6 %", 100 * VAL["matched_set_concordance"]["sbg_v5"]["concordance"], 1, False),
    ("37 %", 100 * VAL["fraction_sbg_v5_exactly_zero"], 0, False),
    ("0.694", V8T["predictors"]["sbg_v5"]["auroc"], 3, False),
    ("0.876", V8T["predictors"]["edit_size_reversed"]["auroc"], 3, False),
    ("−0.182", V8T["paired_deltas"]["sbg_v5_minus_edit_size_reversed"]["delta"], 3, False),
    ("0.849", rev("train"), 3, False),
    ("0.877", rev("dev"), 3, False),
    ("0.885", rev("val"), 3, False),
    ("0.410", OLD["bugsinpy"][0]["auroc"], 3, False),
    ("0.388", OLD["quixbugs_canonical"][0]["auroc"], 3, False),
    ("0.416", EXT["bugsinpy"]["rescored_all"]["auroc"], 3, False),
    ("0.497", EXT["bugsinpy"]["rescored_excluding_SP2"]["auroc"], 3, False),
    ("0.384", EXT["quixbugs_canonical"]["rescored_all"]["auroc"], 3, False),
    ("0.444", EXT["quixbugs_canonical"]["rescored_excluding_SP2"]["auroc"], 3, False),
    ("0.445", AUD["bugsinpy/excluding_invalid_negatives"]["sbg_v5_auroc"], 3, False),
]


def fmt(v, nd):
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x, nd) for x in v) + "]"
    return f"{v:.{nd}f}".replace("-", "−")


def main() -> int:
    bad = []
    for literal, value, nd, plus in CHECKS:
        want = fmt(value, nd)
        if plus and not want.startswith("−"):
            want = "+" + want
        shown = literal[:-2] if literal.endswith(" %") else literal
        if want != shown:
            bad.append(f"VALUE MISMATCH {literal!r}: artifact gives {want!r}")
        if literal not in REPORT:
            bad.append(f"LITERAL ABSENT FROM REPORT {literal!r}")
    seeds = "/".join(str(x) for x in HS["distinct_values_across_seeds"])
    if seeds not in REPORT:
        bad.append(f"hash-seed event counts {seeds!r} absent from report")
    for line in bad:
        print("[FAIL]", line)
    total = len(CHECKS) + 1
    print(f"{total - len(bad)}/{total} trace checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

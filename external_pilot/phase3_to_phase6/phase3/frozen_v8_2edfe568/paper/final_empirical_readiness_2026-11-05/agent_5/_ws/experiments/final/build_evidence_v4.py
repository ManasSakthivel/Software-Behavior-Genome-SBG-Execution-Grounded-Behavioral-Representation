#!/usr/bin/env python3
"""Build FINAL_METRICS_V4.json, BASELINE_COMPARISON_V4.csv and EXPERIMENT_MANIFEST_V4.json from source artifacts only (no recomputation of scores).

    python experiments/final/build_evidence_v4.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
PE = REPO / "artifacts/paper_evidence"
J = lambda n: json.loads((PE / n).read_text())                                   # noqa: E731
sh = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()               # noqa: E731

V10, DEV, VAL = J("V10_INDEPENDENT_EVALUATION.json"), J("V4_DEV_EVALUATION.json"), J("V9_VAL_EVALUATION.json")["v9c_matched"]
V8T = J("V8_TEST_EVALUATION.json")["VALID"]

ROWS = [("sbg_v5", "SBG V5 (frozen)"), ("sbg_v6", "SBG V6-graded (EXPERIMENTAL)"), ("sbg_state", "V5 state component only"), ("edit", "edit size (forward)"),
        ("edit_reversed", "edit size (reversed)"), ("exception_fraction", "execution stat: exception fraction"), ("call_count", "execution stat: call count"),
        ("coverage_size", "execution stat: coverage size"), ("static_ast", "static AST-multiset"), ("static_token", "static token-multiset"),
        ("M_E", "model: edit"), ("M_X", "model: exec stats"), ("M_EX", "model: edit+exec"), ("M_E+V5", "model: edit+SBG V5"),
        ("M_EX+V5", "model: edit+exec+SBG V5"), ("M_EX+V6", "model: edit+exec+SBG V6 (EXPERIMENTAL)")]


def get(block, key):
    return block.get(key)


def build():
    with (PE / "BASELINE_COMPARISON_V4.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["predictor", "description", "dev_auroc", "dev_ci_lo", "dev_ci_hi", "dev_zero_rate", "v9c_val_auroc", "v9c_val_ci_lo", "v9c_val_ci_hi",
                    "v10_auroc", "v10_ci_lo", "v10_ci_hi", "v10_pr_auc", "v10_zero_rate", "v10_sens_train_thr", "v10_spec_train_thr"])
        for k, desc in ROWS:
            d, v, t = DEV["dev"]["predictors"].get(k), VAL["predictors"].get(k.replace("M_E+V5", "M_ES").replace("M_EX+V5", "M_ESX")) if not k.endswith("V6") and k not in ("M_X",) else None, V10["predictors"].get(k)
            if k in ("M_E+V5", "M_EX+V5"):
                v = VAL["predictors"].get({"M_E+V5": "M_ES", "M_EX+V5": "M_ESX"}[k])
            w.writerow([k, desc] + ([d["auroc"], *d["ci95_cluster_bootstrap"], d["exact_zero_rate"]] if d else [""] * 5)
                       + ([v["auroc"], *v["ci95_cluster_bootstrap"]] if v else [""] * 3)
                       + ([t["auroc"], *t["ci95_cluster_bootstrap"], t["pr_auc"], t["exact_zero_rate"], t["sensitivity"], t["specificity"]] if t else [""] * 7))
    fm = {"artifact": "FINAL_METRICS_V4",
          "labels": {"dev": "EXPLORATORY/DEVELOPMENT (v9c dev; V6 designed after seeing v9c train/dev forensics)",
                     "validation": "v9c val: confirmatory-by-freeze for V5 only (V4_ session did not rerun it); V6 never scored there",
                     "independent_test": "v10_independent: single run, frozen before scoring (FREEZE_V10.json); V5 arm pre-declared confirmatory, V6 arm experimental",
                     "v8_test": "burned; reported for completeness; not re-used"},
          "v8_test_burned": {"population": "v8 design, valid pairs", "reference": "V8_TEST_EVALUATION.json", "VALID": V8T},
          "v9c_val": {"n_pairs": VAL["n_pairs"], "n_programs": VAL["n_programs"], "source": "V9_VAL_EVALUATION.json",
                      "sbg_v5": VAL["predictors"]["sbg_v5"], "edit": VAL["predictors"]["edit"], "M_ES": VAL["predictors"]["M_ES"], "M_EX": VAL["predictors"]["M_EX"],
                      "M_ESX": VAL["predictors"]["M_ESX"], "tests": {k: v for k, v in VAL["pre_declared_tests"].items()}, "fraction_sbg_v5_exactly_zero": VAL["fraction_sbg_v5_exactly_zero"]},
          "v9c_dev": {k: DEV["dev"][k] for k in ("n_pairs", "n_programs", "n_matched_sets", "predictors", "paired_deltas", "paired_deltas_holm", "changed_v5_zero", "equivalent_v5_zero")},
          "v10_independent": {k: V10[k] for k in ("n_pairs", "n_matched_sets", "n_programs", "n_changed", "n_equivalent", "n_unevaluated", "mean_edit", "predictors",
                                                  "pre_declared_tests", "supplementary_deltas_not_in_holm_family", "edit_size_exact_stratified", "matched_set_concordance",
                                                  "changed_zero_rate_by_sc_family", "equivalent_zero_rate_by_sp_family", "per_program_counts")},
          "sources": {n: sh(f"artifacts/paper_evidence/{n}") for n in ("V10_INDEPENDENT_EVALUATION.json", "V4_DEV_EVALUATION.json", "V9_VAL_EVALUATION.json", "V8_TEST_EVALUATION.json")}}
    (PE / "FINAL_METRICS_V4.json").write_text(json.dumps(fm, indent=1, default=str) + "\n")
    files = ["experiments/final/extraction.py", "experiments/final/score_v6_experimental.py", "experiments/final/evaluate_v4_dev.py", "experiments/final/evaluate_v10.py",
             "benchmark/scripts/generate_v10_independent.py", "sbg/v6/state_transition_genome_v6.py", "sbg/v5/state_transition_genome.py", "sbg/v3/genome.py",
             "artifacts/final/FREEZE_V10.json", "artifacts/final/FREEZE_V10_SCORED.json", "artifacts/final/V10_MODELS_FROZEN.json", "artifacts/final/pairs_v10_test_v6exp.jsonl",
             "artifacts/final/pairs_v9c_train_v6exp.jsonl", "artifacts/final/pairs_v9c_dev_v6exp.jsonl", "benchmark/datasets/v10_independent/pairs_test.jsonl",
             "benchmark/datasets/v10_independent/manifest.json", "artifacts/final/FREEZE_V9.json", "artifacts/final/V9_MODELS_FROZEN.json"]
    py = sys.executable
    man = {"artifact": "EXPERIMENT_MANIFEST_V4", "branch": "remediation/sbg-v4", "base_commit": "8386eb5e96af79a20bf5d1377474dd566eef4c12",
           "environment": {"python": platform.python_version(), "platform": platform.platform(), "PYTHONHASHSEED": "0", "numpy": "not installed (pure stdlib)"},
           "experiments_run": [
               {"id": "ZERO-DIAG", "label": "exploratory", "script": "experiments/final/diagnose_zero_scores.py", "data": "v9c train+dev (2114 pairs)", "output": "artifacts/paper_evidence/raw/zero_score_diagnostic_v1.json"},
               {"id": "ZERO-ADDR", "label": "exploratory", "script": "experiments/final/zero_score_address_correction.py", "output": "artifacts/paper_evidence/raw/zero_score_address_correction_v1.json"},
               {"id": "EQ-LABEL-AUDIT", "label": "exploratory", "script": "experiments/final/audit_equivalent_label_validity.py", "output": "artifacts/paper_evidence/EQUIVALENT_LABEL_AUDIT.json"},
               {"id": "V6-DEV", "label": "development", "script": "experiments/final/score_v6_experimental.py + evaluate_v4_dev.py", "output": "artifacts/paper_evidence/V4_DEV_EVALUATION.json"},
               {"id": "V10-INDEPENDENT", "label": "independent test (single run)", "script": "generate_v10_independent.py, score_v6_experimental.py --design v10, evaluate_v10.py run",
                "freeze": "artifacts/final/FREEZE_V10.json", "output": "artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json"}],
           "not_run": ["v8 test (burned, deliberately untouched)", "v9c val for V6 (would not be independent)", "BugsInPy/QuixBugs re-validation beyond V3 evidence"],
           "reproduce": [
               f"PYTHONHASHSEED=0 {py} experiments/final/score_v6_experimental.py --design v9c --split train --workers 7",
               f"PYTHONHASHSEED=0 {py} experiments/final/score_v6_experimental.py --design v9c --split dev --workers 7",
               f"PYTHONHASHSEED=0 {py} experiments/final/evaluate_v4_dev.py",
               f"PYTHONHASHSEED=0 {py} benchmark/scripts/generate_v10_independent.py   # ~10 min; deterministic",
               f"PYTHONHASHSEED=0 {py} experiments/final/evaluate_v10.py fit   # (done before freezing)",
               f"PYTHONHASHSEED=0 {py} experiments/final/score_v6_experimental.py --design v10 --split test --workers 7",
               f"PYTHONHASHSEED=0 {py} experiments/final/evaluate_v10.py run   # refuses unless FREEZE_V10.json hashes match; single run; delete the output to re-derive",
               f"PYTHONHASHSEED=0 {py} experiments/final/build_evidence_v4.py && {py} experiments/final/verify_trace_v4.py"],
           "weights_thresholds_provenance": {"sbg_v5_weights": "0.50/0.25/0.25 (extraction.W_V3/W_TEMPORAL/W_STATE; frozen, unchanged since V5)", "v6_weights": "identical 0.50/0.25/0.25",
                                             "logistic_models": "fitted on v9c train only, L2=1.0 (fit_weights.fit_logistic); V10_MODELS_FROZEN.json", "thresholds": "Youden on v9c train per predictor (V10_MODELS_FROZEN.json)",
                                             "v6_constants": "_INT_EXACT_MAX=16, _SIZE_EXACT_MAX=8, float 2dp: fixed from forensic examples before any V6 score (SBG_V6_EXPERIMENTAL_RATIONALE.md)"},
           "hashes": {f: sh(f) for f in files}}
    try:
        man["git_head_at_build"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:                                                              # noqa: BLE001
        pass
    (PE / "EXPERIMENT_MANIFEST_V4.json").write_text(json.dumps(man, indent=1) + "\n")
    print("wrote FINAL_METRICS_V4.json, BASELINE_COMPARISON_V4.csv, EXPERIMENT_MANIFEST_V4.json")


if __name__ == "__main__":
    build()

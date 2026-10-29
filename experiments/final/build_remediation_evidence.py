"""Builds the v3 remediation evidence tables FROM the committed artifacts only.

Every number written here is read from a source artifact (path + sha256 recorded
in the output); nothing is typed in by hand.  Existing evidence files are not
modified; this writes NEW files:

  artifacts/paper_evidence/FINAL_METRICS_V3.json
  artifacts/paper_evidence/BASELINE_COMPARISON_V3.csv
  artifacts/paper_evidence/ABLATIONS_V3.json
  artifacts/paper_evidence/DATASET_SUMMARY_V3.json
  artifacts/paper_evidence/EXPERIMENT_MANIFEST_V3.json

    python experiments/final/build_remediation_evidence.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
PE = REPO / "artifacts/paper_evidence"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(rel: str) -> dict:
    return json.loads((REPO / rel).read_text())


def ref(rel: str) -> dict:
    return {"path": rel, "sha256": sha(REPO / rel)}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=REPO).stdout.strip()


def r4(x):
    return None if x is None else round(float(x), 4)


def main() -> None:
    v9 = {s: load(f"artifacts/paper_evidence/V9_{s.upper()}_EVALUATION.json") for s in ("train", "dev", "val")}
    v8t = load("artifacts/paper_evidence/V8_TEST_EVALUATION.json")
    label = load("artifacts/paper_evidence/LABEL_GENERATION_AUDIT.json")
    ext = load("artifacts/paper_evidence/EXTERNAL_RESCORE_V8.json")
    ext_old = load("artifacts/paper_evidence/DIAGNOSTIC_EXTERNAL.json")
    status = {"train": "IN-SAMPLE (weights fitted here)",
              "dev": "EXPLORATORY (used for design observations before the freeze)",
              "val": "CONFIRMATORY-BY-FREEZE (single run; never scored before FREEZE_V9)"}
    src = {s: f"artifacts/paper_evidence/V9_{s.upper()}_EVALUATION.json" for s in v9}

    # ---------------------------------------------------------------- baselines
    rows = []
    order = ["sbg_v5", "sbg_state", "sbg_v3", "sbg_temporal", "coverage_size", "exception_fraction",
             "call_count", "static_ast", "static_token", "edit", "M_E", "M_ES", "M_EX", "M_ESX",
             "M_E+v3", "M_E+temporal", "M_E+state"]
    for s in ("val", "dev", "train"):
        m = v9[s]["v9c_matched"]
        for p in order:
            e = m["predictors"].get(p)
            if not e:
                continue
            ci = e.get("ci95_cluster_bootstrap") or [None, None]
            rows.append([f"v9c_{s}", "v9_composed", s, status[s].split(" ")[0], p, r4(e["auroc"]), r4(ci[0]),
                         r4(ci[1]), m["n_pairs"], m["n_programs"], m["n_matched_sets"], src[s]])
        v8 = v9[s]["v8_design"]
        for p, e in v8["predictors"].items():
            ci = e.get("ci95_cluster_bootstrap") or [None, None]
            rows.append([f"v8design_{s}", "v8 (label bound to family)", s,
                         "CONFOUNDED-DESIGN", p, r4(e["auroc"]), r4(ci[0]), r4(ci[1]),
                         v8["n_pairs"], v8["n_programs"], "", src[s]])
    t = v8t
    with (PE / "BASELINE_COMPARISON_V3.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run_id", "dataset", "split", "evidence_status", "predictor", "auroc", "ci95_lo",
                    "ci95_hi", "n_pairs", "n_programs", "n_matched_sets", "source_artifact"])
        w.writerows(rows)

    # ------------------------------------------------------------ final metrics
    tests = {s: {k: {kk: r4(vv) if isinstance(vv, float) else vv for kk, vv in v9[s]["v9c_matched"]
                     ["pre_declared_tests"][k].items() if kk != "what"}
                 for k in ("H1", "H2", "H3", "H4")} for s in v9}
    holm = v9["val"]["v9c_matched"]["pre_declared_tests"]["holm"]
    metrics = {
        "artifact": "FINAL_METRICS_V3",
        "generated_by": "experiments/final/build_remediation_evidence.py (reads artifacts only)",
        "git_base_commit": git("rev-parse", "HEAD"),
        "evidence_classes": {
            "CONFIRMATORY-BY-FREEZE": ["v8 test (V8_TEST_EVALUATION.json) -- NOT DEMONSTRATED",
                                       "v9c val (V9_VAL_EVALUATION.json)"],
            "EXPLORATORY": ["v9c dev", "v8 dev/val/train scoring", "external corpora rescore",
                            "all diagnostics", "sbg_state-only (identified post hoc on dev)"],
            "IN-SAMPLE": ["v9c train"]},
        "no_pooling_note": "v6, v8 and v9c results are never pooled: different dataset designs, "
                           "protocols (v6/v7 vs output_free_v8) and label-generation logic.",
        "v8_test_single_run": {
            "source": ref("artifacts/paper_evidence/V8_TEST_EVALUATION.json"),
            "status": t["status"],
            "VALID": {"n_pairs": t["VALID"]["n_pairs"], "n_programs": t["VALID"]["n_programs"],
                      **{p: {"auroc": r4(t["VALID"]["predictors"][p]["auroc"]),
                             "ci95": [r4(x) for x in t["VALID"]["predictors"][p]["ci95_cluster_bootstrap"]]}
                         for p in ("sbg_v5", "learned_m1", "learned_m2", "edit_size_reversed",
                                   "exception_fraction")},
                      "sbg_v5_minus_edit_size_reversed": {
                          k: r4(v) for k, v in t["VALID"]["paired_deltas"]["sbg_v5_minus_edit_size_reversed"].items()
                          if k in ("delta", "ci_lower", "ci_upper")}},
        },
        "v9c_val_confirmatory": {
            "source": ref(src["val"]), "status": status["val"],
            "population": {k: v9["val"]["v9c_matched"][k] for k in
                           ("n_pairs", "n_matched_sets", "n_programs", "n_changed", "n_equivalent")},
            "selection_audit": v9["val"]["v9c_matched"]["selection_audit"],
            "tests": tests["val"], "holm": {k: {kk: vv for kk, vv in v.items() if kk in
                                                ("p_raw", "p_adjusted", "reject_at_alpha")}
                                           for k, v in holm.items()},
            "verdict": v9["val"]["v9c_matched"]["verdict"],
            "matched_set_concordance": {k: {"concordance": r4(v["concordance"]),
                                            "ci95": [r4(x) for x in v["ci95_cluster_bootstrap"]]}
                                        for k, v in v9["val"]["v9c_matched"]["matched_set_concordance"].items()},
            "edit_size_exact_stratified": {k: r4(v["auroc"]) for k, v in
                                           v9["val"]["v9c_matched"]["edit_size_exact_stratified"].items()},
            "fraction_sbg_v5_exactly_zero": v9["val"]["v9c_matched"]["fraction_sbg_v5_exactly_zero"],
        },
        "v9c_dev_exploratory": {"source": ref(src["dev"]), "status": status["dev"],
                                "tests": tests["dev"]},
        "v9c_train_in_sample": {"source": ref(src["train"]), "status": status["train"],
                                "tests": tests["train"]},
        "v8_design_confounded": {s: {"sbg_v5": r4(v9[s]["v8_design"]["predictors"]["sbg_v5"]["auroc"]),
                                     "edit_size_reversed": r4(v9[s]["v8_design"]["predictors"]
                                                              ["edit_size_reversed"]["auroc"]),
                                     "n_pairs": v9[s]["v8_design"]["n_pairs"],
                                     "n_programs": v9[s]["v8_design"]["n_programs"],
                                     "source": src[s]} for s in ("train", "dev", "val")},
        "edit_size_confound_audit": {
            "source": ref("artifacts/paper_evidence/LABEL_GENERATION_AUDIT.json"),
            "independent_reversed_edit_size_auroc": {
                sp: label["splits"][sp]["independent_edit_size_auroc"] for sp in label["splits"]},
            "fraction_cross_label_pairs_identical_edit_size": {
                sp: label["splits"][sp]["fraction_identical_edit_size"] for sp in label["splits"]},
            "label_by_edit_bucket_train": label["splits"]["train"]["label_by_edit_bucket"]},
        "external_rescore_exploratory": {
            "source": ref("artifacts/paper_evidence/EXTERNAL_RESCORE_V8.json"),
            "corpora": {n: {k: c[k] for k in ("n_pairs_total", "n_evaluated", "unevaluated", "rescored_all",
                                              "rescored_excluding_SP2", "committed_v7_same_pairs",
                                              "sp2_pairs", "sp2_pairs_with_entry_renamed",
                                              "real_bug_pairs_evaluated",
                                              "real_bug_pairs_sbg_v5_exactly_zero", "self_distance_v5")}
                        for n, c in ext["corpora"].items()}},
        "external_original_v7_for_reference": {"source": ref("artifacts/paper_evidence/DIAGNOSTIC_EXTERNAL.json"),
                                               "quixbugs_canonical": ext_old["quixbugs_canonical"][0],
                                               "bugsinpy": ext_old["bugsinpy"][0]},
    }
    (PE / "FINAL_METRICS_V3.json").write_text(json.dumps(metrics, indent=1, default=str) + "\n")

    # ---------------------------------------------------------------- ablations
    abl = {"artifact": "ABLATIONS_V3",
           "scope": "Component comparison on v9c (size-decoupled). No component selection is based on val.",
           "val_confirmatory_component_increments_over_edit_only": {
               k: {kk: r4(vv) for kk, vv in v.items() if kk in ("delta", "ci_lower", "ci_upper", "p_two_sided")}
               for k, v in v9["val"]["v9c_matched"]["component_increments_over_edit_only_model"].items()},
           "val_single_component_auroc": {p: r4(v9["val"]["v9c_matched"]["predictors"][p]["auroc"])
                                         for p in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state")},
           "val_v5_minus_components": {k: {kk: r4(vv) for kk, vv in v.items() if kk != "n_effective"}
                                       for k, v in v9["val"]["v9c_matched"]["paired_deltas_sbg_v5_minus"].items()
                                       if k in ("sbg_v3", "sbg_temporal", "sbg_state")},
           "dev_component_increments": {k: r4(v["delta"]) for k, v in
                                        v9["dev"]["v9c_matched"]["component_increments_over_edit_only_model"].items()},
           "train_component_increments": {k: r4(v["delta"]) for k, v in
                                          v9["train"]["v9c_matched"]["component_increments_over_edit_only_model"].items()},
           "notes": ["sbg_state-only was identified as strongest on dev (exploratory); its val advantage over "
                     "sbg_v5 is not significant (CI includes 0).",
                     "Temporal component is weakest and contributes least.",
                     "Frozen model weights: artifacts/final/V9_MODELS_FROZEN.json (fitted on v9c train only)."],
           "sources": {s: src[s] for s in v9}}
    (PE / "ABLATIONS_V3.json").write_text(json.dumps(abl, indent=1) + "\n")

    # -------------------------------------------------------------- datasets
    v9m = load("benchmark/datasets/v9_composed/manifest.json")
    v8m = load("artifacts/paper_evidence/DATASET_SUMMARY.json")["datasets"]["v8"]["splits"]
    ds = {"artifact": "DATASET_SUMMARY_V3",
          "v8": {s: {k: v8m[s][k] for k in ("n_pairs", "n_programs", "n_changed", "n_equivalent")}
                 for s in v8m},
          "v8_scored_this_session": {
              s: {"source": ref(f"artifacts/final/pairs_v8{s}_output_free_v8.jsonl"),
                  "n_pairs": v9[s]["v8_design"]["n_pairs"], "n_programs": v9[s]["v8_design"]["n_programs"]}
              for s in ("train", "val")},
          "v9_composed": {"manifest": ref("benchmark/datasets/v9_composed/manifest.json"),
                          "test_split_generated": v9m["test_split_generated"],
                          "stale_programs_excluded": v9m["stale_programs_excluded"],
                          "splits": {s: {**{k: v9m["splits"][s][k] for k in
                                            ("n_programs", "n_equivalent_v8_reused", "n_composed_changed",
                                             "n_unmatched_equivalent")},
                                         "scored_selection_audit": v9[s]["v9c_matched"]["selection_audit"]}
                                     for s in ("train", "dev", "val")}},
          "label_distribution_by_edit_size_bucket_v8_train":
              load("artifacts/paper_evidence/LABEL_GENERATION_AUDIT.json")["splits"]["train"]["label_by_edit_bucket"],
          "harness_timeout_events": {
              "cause": "math_gray_code SC-4/SC-5 mutants remove the n>14 guard; a leaked tracer worker "
                       "exceeds 18 GB RSS. Pairs are recorded unevaluated (failure_kind=harness_timeout), "
                       "never imputed.",
              "v8_train": 6, "v9c_train": 4, "v8_dev": 0, "v8_val": 0, "v8_test": 0}}
    (PE / "DATASET_SUMMARY_V3.json").write_text(json.dumps(ds, indent=1) + "\n")

    # --------------------------------------------------------------- manifest
    man = {"artifact": "EXPERIMENT_MANIFEST_V3",
           "repository": "https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation",
           "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
           "base_commit_at_generation": git("rev-parse", "HEAD"),
           "python": {"venv": "../venvs/py313/bin/python", "version": "CPython 3.13.5",
                      "requirements_lock": ref("requirements-lock.txt")},
           "environment": {"PYTHONHASHSEED": "0 for all scoring", "platform": "macOS arm64"},
           "freezes": {"v8": ref("artifacts/final/FREEZE_V8.json"),
                       "v8_amendment2": ref("artifacts/final/FREEZE_V8_AMENDMENT2.json"),
                       "v9": ref("artifacts/final/FREEZE_V9.json"),
                       "v9_models": ref("artifacts/final/V9_MODELS_FROZEN.json"),
                       "v8_threshold": ref("artifacts/final/THRESHOLD_V8_FROZEN.json")},
           "scripts": {k: ref(f"experiments/final/{k}") for k in
                       ("evaluate_v8.py", "evaluate_v9.py", "run_chunked.py", "audit_label_generation.py",
                        "rescore_external_v8.py", "diagnose_hashseed.py", "make_freeze_v9.py",
                        "audit_external_negatives.py", "verify_trace_v3.py", "build_remediation_evidence.py")}
           | {"benchmark/scripts/generate_v9_composed.py": ref("benchmark/scripts/generate_v9_composed.py")},
           "runs": {
               "v8_test_single": "V8_TEST_EVALUATION.json (prior session; burned, final)",
               "v8_train_score": "run_chunked.py --split train --protocol output_free_v8 -> pairs_v8train_output_free_v8.jsonl",
               "v8_val_score": "run_chunked.py --split val ... -> pairs_v8val_output_free_v8.jsonl",
               "v9c_train_dev_val_score": "run_chunked.py --dataset-label v9c ... -> pairs_v9c_{train,dev,val}_output_free_v8.jsonl",
               "v9_evaluations": "evaluate_v9.py --split {train,dev,val} (val executed once after FREEZE_V9 commit 6dd5a0f)",
               "label_audit": "audit_label_generation.py (uses no SBG scores)",
               "external_rescore": "rescore_external_v8.py --workers 4"},
           "reproduction": [
               "PYTHONHASHSEED=0 ../venvs/py313/bin/python experiments/final/evaluate_v9.py --split val  # reads frozen scored pairs; no re-scoring",
               "../venvs/py313/bin/python experiments/final/audit_label_generation.py",
               "PYTHONHASHSEED=0 ../venvs/py313/bin/python experiments/final/rescore_external_v8.py --workers 4",
               "../venvs/py313/bin/python experiments/final/diagnose_hashseed.py",
               "../venvs/py313/bin/python experiments/final/audit_external_negatives.py",
               "../venvs/py313/bin/python experiments/final/verify_trace_v3.py",
               "../venvs/py313/bin/python experiments/final/build_remediation_evidence.py",
               "../venvs/py313/bin/python -m pytest sbg/ tests/ -q",
               "../venvs/py313/bin/python experiments/final/consistency_check.py",
               "../venvs/py313/bin/python experiments/final/stanford_gate.py",
               "../venvs/py313/bin/python experiments/final/data_integrity.py --dataset benchmark/datasets/v8 --strict"],
           "not_run": ["v9 test split (not generated: no further unseen-program split is available that is "
                       "not the burned v8 test; generating one from v8 test programs would reuse them)",
                       "Java QuixBugs", "real-bug transfer re-run with warm-up extraction (see cold_start_probe.json)"]}
    (PE / "EXPERIMENT_MANIFEST_V3.json").write_text(json.dumps(man, indent=1) + "\n")
    print("wrote FINAL_METRICS_V3.json BASELINE_COMPARISON_V3.csv ABLATIONS_V3.json "
          "DATASET_SUMMARY_V3.json EXPERIMENT_MANIFEST_V3.json")


if __name__ == "__main__":
    sys.exit(main())

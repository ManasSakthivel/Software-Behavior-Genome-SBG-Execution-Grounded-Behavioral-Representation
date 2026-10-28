"""Writes EXPERIMENT_MANIFEST.json, FINAL_METRICS.json, WEIGHT_FITTING.json and
THRESHOLD_PROVENANCE.json in artifacts/paper_evidence/ from the source artifacts.
Run after build_paper_evidence.py and build_ablations.py. Reads no test-split score
computed under a protocol that was not already committed.

    python3 experiments/final/build_paper_evidence_meta.py
"""
from __future__ import annotations

import datetime
import json
import pathlib
import platform
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from experiments.final.build_paper_evidence import RUNS, W, js, jl, sha, src, write   # noqa: E402

PE = "artifacts/paper_evidence"


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()


def main():
    rc = js(f"{PE}/raw/recomputed_comparisons.json")
    ops = js(f"{PE}/raw/tau_operating_points.json")
    tf = js("artifacts/final/THRESHOLD_FROZEN.json")
    ds = js(f"{PE}/DATASET_SUMMARY.json")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    # ---------------------------------------------------------------- metrics
    def main_row(run, pred):
        m = js(RUNS[run]["main"])["results"]["VALID"]["predictors"][pred]
        return {"auroc": m["auroc"], "ci95_cluster_bootstrap": m["ci95_cluster_bootstrap"],
                "permutation_p": m["permutation_p"], "n": m["n"]}

    def run_block(run, extra_note):
        r = RUNS[run]
        m = js(r["main"])
        return {
            "dataset": r["dataset"], "split": r["split"], "protocol": r["protocol"], "status": r["status"],
            "role": r["role"], "note": extra_note,
            "set_sizes": m["set_sizes"], "n_programs_valid": rc[run]["n_programs"] if run in rc else None,
            "primary_set": "VALID (EVALUABLE minus statically invalid/unobservable pairs)",
            "sbg_v5": main_row(run, "sbg_v5"),
            "baselines_precomputed": {p: main_row(run, p) for p in
                                      ("exception_fraction", "call_count", "combined_shortcut", "static_ast",
                                       "static_token", "sbg_state", "sbg_v3", "sbg_temporal")},
            "recomputed_by_build_paper_evidence": rc.get(run),
            "label_shuffle_noise_floor": m["results"]["VALID"]["label_shuffle_noise_floor_primary"],
            "paired_comparisons_precomputed": m["results"]["VALID"]["paired_comparisons"],
            "sources": {"main_evaluation": src(r["main"]), "pairs": src(r["pairs"]), "programs": src(r["programs"]),
                        "validity_audit": src(r["audit"])},
        }

    metrics = {
        "generated_at_utc": now,
        "generated_by": "experiments/final/build_paper_evidence_meta.py",
        "code_commit_base": git("rev-parse", "HEAD"),
        "working_tree_dirty_at_generation": bool(git("status", "--porcelain", "--untracked-files=no")),
        "headline_reading": {
            "verdict": "NOT a confirmatory result. No held-out TEST split has been scored under a frozen protocol.",
            "summary": [
                "SBG V5 separates CHANGED from EQUIVALENT above chance on v6 train/dev (AUROC 0.665 / 0.667) and "
                "v8 dev (0.739), cluster-bootstrap CIs excluding 0.5.",
                "Reversed edit size alone (a trivial shortcut) beats SBG V5 on every run: 0.954 (v6 train), 0.957 (v6 dev), "
                "0.845 (v8 dev). Paired deltas sbg_v5 - edit_size_reversed are negative with CIs excluding 0 on all three.",
                "SBG V5 beats exception_fraction and call_count on v8 dev (paired CIs exclude 0) and on v6 train "
                "vs exception_fraction; on v6 dev it does not beat exception_fraction (CI includes 0).",
                "The dev-selected learned model M2 raises AUROC (v6 train 0.724 in-sample, v6 dev 0.713 selection set, "
                "v8 dev 0.804 out-of-distribution) but is still below reversed edit size.",
                "External transfer is negative: BugsInPy 0.410 [0.326, 0.494], QuixBugs 0.388 (both below chance, pre-freeze).",
            ]},
        "runs": {
            "v6train_output_free_v7": run_block("v6train_v7", "Completed this session by resuming from checkpoint at 1000/1129; "
                                                "learned weights are IN-SAMPLE here."),
            "v6dev_output_free_v7": run_block("v6dev_v7", "Frozen 2026-09-28 artifact; tau* and the M2 choice were made on this split, "
                                              "so its numbers are selection statistics, not generalisation estimates."),
            "v8dev_output_free_v8": run_block("v8dev_v8_rescore", "Fresh programs (disjoint from v6), re-scored this session against the "
                                              "CURRENT v8 dataset. v8 dev was not used for tau* or weights. Exploratory: protocol v8 and "
                                              "dataset v8 are not frozen (FREEZE_V8.json absent)."),
            "v6test_output_free_v6": run_block("v6test_v6", "Historical OBSERVED (not held-out) split under the older v6 protocol; "
                                               "not re-run; shown for completeness."),
        },
        "tau_operating_points": {"source": src(f"{PE}/raw/tau_operating_points.json"), **{k: v for k, v in ops.items()}},
        "external_corpora": ds["external_corpora"],
        "not_available": {
            "v6_test_under_output_free_v7": "NOT RUN (deliberately; split is observed/contaminated, make v7-test not executed)",
            "v8_test": "NOT RUN (v8 test not scored; FREEZE_V8.json absent; pre-registration for v8 absent)",
            "weight_fitting_test_score": "WEIGHT_FITTING.json['test'] is null: M1/M2 never scored on a test split",
            "java_quixbugs": "NOT RUN (QUIXBUGS_JAVA_SBG_RESULTS.json absent)",
            "quixbugs_ci": "source artifact has no CI",
            "power_analysis_v8": "power_analysis.py not run on v8 dev",
        },
    }
    write("FINAL_METRICS.json", metrics)

    # ------------------------------------------------------------ weight fitting
    wf = {
        "status": "FIT COMPLETE on train, selected on dev. NOT scored on any test split (WEIGHT_FITTING.json['test'] is null).",
        "artifact": src("artifacts/final/WEIGHT_FITTING.json"),
        "script": "experiments/final/fit_weights.py (stage `fit`)",
        "command": "../venvs/py313/bin/python experiments/final/fit_weights.py fit",
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md section 4",
        "fitted_at_utc": W["fitted_at"],
        "data_boundaries": {
            "fit_on": "v6 TRAIN VALID pairs only (pairs_v6train_output_free_v7.jsonl)",
            "selected_on": "v6 DEV AUROC (pairs_v6dev_output_free_v7.jsonl)",
            "test_split_opened": False,
            "enforcement": "fit_weights.py FILES['test'] is only read to refuse refit if learned scores already present; "
                           "pairs_v6test_output_free_v7.jsonl does not exist",
            "program_counts": {"train": W["inputs"]["n_train_programs"], "dev": W["inputs"]["n_dev_programs"]},
            "pair_counts_valid": {"train": W["inputs"]["n_train_valid"], "dev": W["inputs"]["n_dev_valid"]},
            "train_dev_program_overlap": [],
        },
        "inputs": W["inputs"],
        "procedure": W["procedure"],
        "models": W["models"],
        "chosen_on_dev": W["chosen_on_dev"],
        "stale_input_warnings": [
            "pairs_v6dev_output_free_v7.jsonl (frozen 2026-09-28) does NOT reproduce byte-for-byte under current code "
            "(46 of 345 pair scores differ, max |dSBG|=0.0167 at HEAD f15cb9a; 7 pairs additionally become non-evaluable under "
            "the uncommitted tracer edits). The fit used the frozen file, as the protocol requires.",
            "train file was produced with the working-tree tracer/runner edits (RecursionError early-exit, no snapshot after "
            "deadline); the first 1000 pairs came from checkpoint written by the interrupted run /tmp/v7_train_eval_r2.log "
            "(same code), the last 129 from the resumed run /tmp/v7_train_eval_r3.log.",
        ],
        "caveats": [
            "Dev AUROC for M2 (0.7128) vs M0 (0.6671) is a model-selection statistic on 9 programs.",
            "Paired delta sbg_v5 - learned_m2 on dev: -0.0457 CI [-0.110, 0.040] (includes 0): the dev gain is not statistically distinguishable from M0.",
            "On v8 dev (out-of-distribution, unused in fitting) M2 = 0.804 vs M0 = 0.739; paired delta -0.064 CI [-0.096, -0.034].",
        ],
        "recomputed_comparisons": src(f"{PE}/raw/recomputed_comparisons.json"),
    }
    write("WEIGHT_FITTING.json", wf)

    # --------------------------------------------------------------- threshold
    tp = {
        "tau_star": tf["tau_star"],
        "status": "VALID and internally consistent; derived on v6 dev under output_free_v7. Applies to protocol output_free_v7 only.",
        "artifact": src("artifacts/final/THRESHOLD_FROZEN.json"),
        "freeze_record": src("artifacts/final/freeze_threshold.json"),
        "frozen_at": tf["frozen_at"],
        "git_commit_of_artifact": "ad7b655 (2026-10-03 11:05 +0530) -- the file's claimed frozen_at (2026-09-28) cannot be verified from git; see TEST_SET_CHRONOLOGY.md",
        "derivation": {
            "script": "experiments/final/derive_threshold.py (refuses any non-dev input)",
            "rule": tf["rule"], "predictor": tf["predictor"], "protocol": tf["protocol"],
            "dev_pair_file": tf["derived_on"]["dataset_pair_file"],
            "dev_pair_file_sha256_recorded": tf["derived_on"]["dataset_pair_file_sha256"],
            "dev_pair_file_sha256_now": sha(tf["derived_on"]["dataset_pair_file"]),
            "scored_pair_file": tf["derived_on"]["scored_pair_file"],
            "scored_pair_file_sha256_recorded": tf["derived_on"]["scored_pair_file_sha256"],
            "scored_pair_file_sha256_now": sha(tf["derived_on"]["scored_pair_file"]),
            "n_valid_pairs": tf["derived_on"]["n_valid_pairs"], "n_changed": tf["derived_on"]["n_changed"],
            "n_equivalent": tf["derived_on"]["n_equivalent"], "n_programs": tf["derived_on"]["n_programs"],
            "programs": tf["derived_on"]["programs"],
            "dev_operating_point": tf["dev_operating_point"],
            "stability_bootstrap_not_used_for_selection": tf["stability_diagnostic_not_used_for_selection"],
        },
        "hash_checks": {
            "dev_pairs_hash_matches_record": sha(tf["derived_on"]["dataset_pair_file"]) == tf["derived_on"]["dataset_pair_file_sha256"],
            "scored_pairs_hash_matches_record": sha(tf["derived_on"]["scored_pair_file"]) == tf["derived_on"]["scored_pair_file_sha256"],
            "freeze_threshold_hash_matches": js("artifacts/final/freeze_threshold.json")["records"][0]["dev_scored_pair_file_sha256"]
                                               == tf["derived_on"]["scored_pair_file_sha256"],
        },
        "tested_in_repo": "tests/test_threshold_provenance.py (re-derives tau* from the dev file)",
        "operating_points_of_frozen_tau": ops,
        "caveats": [
            "tau* was derived on 9 dev programs.",
            "9 of the 345 dev pairs are EQUIVALENT SP-2 pairs whose renamed entry was a test_* driver (KNOWN_HISTORICAL_DRIVER_TRACES in consistency_check.py).",
            "Re-scoring dev with current code (/tmp/devrepro_head) would give tau 0.072531 (vs 0.072905), same Youden J: negligible but the frozen file is retained unmodified.",
            "The earlier constant tau = 0.08 has no verifiable provenance (docs/current/THRESHOLD_PROVENANCE.md) and is NOT used here.",
            "No tau* exists for protocol output_free_v8 (THRESHOLD_V8_FROZEN.json absent); applying 0.072905 to v8 dev is a cross-protocol transfer shown only as an operating-point diagnostic.",
        ],
    }
    write("THRESHOLD_PROVENANCE.json", tp)

    # --------------------------------------------------------------- manifest
    tracked_mod = git("status", "--porcelain", "--untracked-files=no").splitlines()
    man = {
        "generated_at_utc": now,
        "repository": git("remote", "get-url", "origin"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "uncommitted_tracked_modifications_at_generation": tracked_mod,
        "python": {"venv": "venvs/py313", "version": subprocess.run(
            [str(REPO.parent / "venvs/py313/bin/python"), "-V"], capture_output=True, text=True).stdout.strip(),
                   "canonical_declared": ".python-version = 3.13", "requirements_lock_sha256": sha("requirements-lock.txt")},
        "machine": {"platform": platform.platform(), "arch": platform.machine()},
        "seeds": {"bootstrap": 42, "permutation": 42, "label_shuffle": 42, "split": 42, "transformations": [0, 1, 2],
                  "n_bootstrap": 2000, "n_permutations": 2000, "n_shuffles": 500},
        "protocols": {
            "published": "historical, name-based entry",
            "output_free_v6": "historical, name-based entry (traces test_* drivers for some SP-2 variants)",
            "output_free_v7": "function tier + alphabetical class-driver tier; frozen tau* and weights belong to this protocol",
            "output_free_v8": "structural rename-invariant entry policy; NOT frozen (no FREEZE_V8.json)"},
        "datasets": {k: {"dir": v["dataset_dir"], "splits": {s: {"n_pairs": x["n_pairs"], "n_programs": x["n_programs"],
                                                                    "pair_file": x["pair_file"]} for s, x in v["splits"].items()}}
                     for k, v in ds["datasets"].items()},
        "dataset_manifests": {"v8": src("benchmark/datasets/v8/manifest.json"),
                              "v6": src("benchmark/datasets/v6/generation_report.json")},
        "runs": {
            "v6train_output_free_v7": {
                "status": "COMPLETE (this session)",
                "command": "run_main_evaluation.py --split train --protocol output_free_v7 --dataset-dir benchmark/datasets/v6 --tag v6train [--checkpoint-every 5 on resume]",
                "then": "static_baselines.py --pairs artifacts/final/pairs_v6train_output_free_v7.jsonl --dataset benchmark/datasets/v6; "
                        "analyse_results.py --split train --protocol output_free_v7 --tag v6train --audit artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json",
                "logs": ["/tmp/v7_train_eval.log (attempt 1, to 1000/1129, 13558 s)", "/tmp/v7_train_eval_r2.log (attempt 2, PID 36301, to 1000/1129, 7003 s; process found dead, no completion marker)",
                         "/tmp/v7_train_eval_r3.log (resume, PID 50960, 1000 -> 1129, 862.6 s; completed)"],
                "outputs": {"pairs": src("artifacts/final/pairs_v6train_output_free_v7.jsonl"), "programs": src("artifacts/final/programs_v6train_output_free_v7.json"),
                            "main_evaluation": src("artifacts/final/MAIN_EVALUATION_v6train_output_free_v7.json")}},
            "weight_fitting": {"status": "COMPLETE (this session)", "command": "fit_weights.py fit",
                               "output": src("artifacts/final/WEIGHT_FITTING.json")},
            "v8dev_output_free_v8_rescore": {
                "status": "COMPLETE (this session)",
                "command": "run_main_evaluation.py --split dev --protocol output_free_v8 --dataset-dir benchmark/datasets/v8 --tag v8devrescore; "
                           "static_baselines.py --pairs artifacts/final/pairs_v8devrescore_output_free_v8.jsonl --dataset benchmark/datasets/v8; "
                           "observability_audit_v7.py benchmark/datasets/v8 artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json; "
                           "analyse_results.py --split dev --protocol output_free_v8 --tag v8devrescore --audit artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json",
                "why_rescored": "pre-existing pairs_dev_/pairs_v8dev_output_free_v8.jsonl were scored 2026-10-27/28 07:39 against an earlier "
                                "v8 dataset; benchmark/datasets/v8 was regenerated 07:53 on 2026-10-28; 181-186 of 593 scores differ and "
                                "pairs_v8dev_* has 598 rows vs 597 current pairs. Two identical re-scores matched exactly (deterministic).",
                "caveat_audit": "BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json applies the v7 observability audit to v8 pairs; all 597 are marked observable/valid. "
                                "It uses v7 entry logic, not the v8 structural entry policy, so VALID == EVALUABLE here.",
                "outputs": {"pairs": src("artifacts/final/pairs_v8devrescore_output_free_v8.jsonl"), "programs": src("artifacts/final/programs_v8devrescore_output_free_v8.json"),
                            "main_evaluation": src("artifacts/final/MAIN_EVALUATION_v8devrescore_output_free_v8.json")}},
            "v6dev_output_free_v7": {"status": "REUSED (frozen)", "outputs": {"pairs": src("artifacts/final/pairs_v6dev_output_free_v7.jsonl"),
                                                                                "main_evaluation": src("artifacts/final/MAIN_EVALUATION_v6dev_output_free_v7.json")}},
            "v6test_output_free_v6": {"status": "REUSED (historical, observed split)", "outputs": {"pairs": src("artifacts/final/pairs_v6test_output_free_v6.jsonl"),
                                                                                                   "main_evaluation": src("artifacts/final/MAIN_EVALUATION_v6test_output_free_v6.json")}},
            "quixbugs_output_free_v7": {"status": "REUSED (pre-freeze, adverse)", "output": src("artifacts/final/QUIXBUGS_output_free_v7.json")},
            "bugsinpy_output_free_v7": {"status": "REUSED (pre-freeze, adverse)", "output": src("artifacts/final/BUGSINPY_output_free_v7.json")},
            "evidence_builders": ["edit_size_confound_multi.py", "tau_operating_points.py", "build_paper_evidence.py", "build_ablations.py", "build_paper_evidence_meta.py"],
        },
        "not_run": ["make v7-test (v6 TEST under output_free_v7)", "fit_weights.py score/test", "any v8 test/val scoring",
                    "make java", "power_analysis.py on v8", "FREEZE_V8.json / THRESHOLD_V8_FROZEN.json creation"],
    }
    write("EXPERIMENT_MANIFEST.json", man)
    print("ok")


if __name__ == "__main__":
    main()

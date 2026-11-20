#!/usr/bin/env python3
"""Updates FINAL_METRICS.json and EXPERIMENT_MANIFEST.json (generated earlier by build_paper_evidence_meta.py) with the v8 frozen
runs, diagnostics and provenance, and writes THRESHOLD/WEIGHT provenance pointers.  Idempotent; keeps the superseded text."""
import hashlib, json, pathlib, platform, subprocess, sys

R = pathlib.Path(__file__).resolve().parents[2]
EV = R / "artifacts/paper_evidence"
sha = lambda p: hashlib.sha256((R / p).read_bytes()).hexdigest()  # noqa: E731
J = lambda p: json.loads((R / p).read_text())  # noqa: E731
src = lambda p: {"path": p, "sha256": sha(p)}  # noqa: E731
test, dev = J("artifacts/paper_evidence/V8_TEST_EVALUATION.json")["VALID"], J("artifacts/paper_evidence/V8_DEV_DRYRUN_EVALUATION.json")["VALID"]
fz = J("artifacts/final/FREEZE_V8.json")
slim = lambda d: {"n_pairs": d["n_pairs"], "n_changed": d["n_changed"], "n_equivalent": d["n_equivalent"], "n_programs": d["n_programs"],  # noqa: E731
                  "predictors": {k: {"auroc": v["auroc"], "ci95": v["ci95_cluster_bootstrap"]} for k, v in d["predictors"].items()},
                  "paired_delta_sbg_v5_minus_edit_size_reversed": d["paired_deltas"]["sbg_v5_minus_edit_size_reversed"],
                  "holm_adjusted_p_vs_edit_size_reversed": d["holm_bonferroni_over_baselines"]["sbg_v5_minus_edit_size_reversed"]["p_adjusted"],
                  "edit_size_exact_stratified": d["edit_size_exact_stratified"], "noise_floor": d["label_shuffle_noise_floor_sbg_v5"],
                  "operating_point_tau_v8": d["operating_point_tau_v8"], "verdict": d["pre_declared_success_criterion"]}

fm = J("artifacts/paper_evidence/FINAL_METRICS.json")
if "superseded_headline_reading" not in fm:
    fm["superseded_headline_reading"] = fm["headline_reading"]
    fm["superseded_not_available"] = fm["not_available"]
fm["headline_reading"] = {
    "verdict": ("SBG is NOT demonstrated. The single frozen v8 TEST evaluation (22 programs, 956 pairs) gives sbg_v5 AUROC "
                f"{test['predictors']['sbg_v5']['auroc']:.3f} {test['predictors']['sbg_v5']['ci95_cluster_bootstrap']} against reversed edit size "
                f"{test['predictors']['edit_size_reversed']['auroc']:.3f} {test['predictors']['edit_size_reversed']['ci95_cluster_bootstrap']}; "
                "the pre-declared criterion (beat the best baseline with CI lower bound > 0) is NOT met."),
    "summary": [
        "v8 TEST (confirmatory-by-freeze, single run): sbg_v5 0.694, learned_m2 0.771, edit_size_reversed 0.876, coverage_size 0.612, exception_fraction 0.569, call_count 0.494, static_ast 0.259, static_token 0.260.",
        "sbg_v5 beats exception_fraction, call_count, coverage_size and the static baselines on v8 TEST (paired CIs exclude 0) but loses to reversed edit size (delta -0.182, CI [-0.220, -0.144]).",
        "Beyond edit size: exact edit-size-stratified AUROC 0.776 [0.722, 0.825] (label-shuffle p95 0.528) -> some signal beyond edit size, on a stratum retaining 19% of cross-label pairs. This is the only evidence of non-shortcut signal.",
        "Edit-size confound is a genuine benchmark confound (label is a function of transformation family), not an implementation error: DIAGNOSTIC_EDIT_SIZE.json.",
        "External transfer is not demonstrated: BugsInPy 0.410 / QuixBugs 0.388 headline; after removing the SP-2 entry-rename artifact and the `re`-cache artifact the values are 0.45-0.51 with CIs spanning 0.5 (DIAGNOSTIC_EXTERNAL.json). Pre-freeze, exploratory.",
        "v6 dev frozen scores differ from current re-score on 46/345 pairs: hash-order nondeterminism (18) + a legitimate input-aliasing fix (28); AUROC 0.667 vs 0.668-0.678 (DIAGNOSTIC_V6DEV_REPRO.json). v6 results stay exploratory.",
        "Earlier (pre-freeze) summary lines are preserved under `superseded_headline_reading`."]}
fm["v8_frozen_runs"] = {
    "v8_test_frozen": {"status": "CONFIRMATORY-BY-FREEZE (single run; amended twice before scoring; 4 stale-variant programs excluded by a content-only rule; see FREEZE_V8*.json)",
                       "source": src("artifacts/paper_evidence/V8_TEST_EVALUATION.json"), **slim(test)},
    "v8_dev_dryrun_frozen_script": {"status": "EXPLORATORY / DEV (tau_v8 derived here; 1 stale program excluded)",
                                    "source": src("artifacts/paper_evidence/V8_DEV_DRYRUN_EVALUATION.json"), **slim(dev)},
    "component_comparison": {"status": "EXPLORATORY, descriptive, post-test", "source": src("artifacts/paper_evidence/V8_COMPONENT_COMPARISON.json")}}
fm["diagnostics"] = {k: src(f"artifacts/paper_evidence/{k}.json") for k in
                     ("DIAGNOSTIC_EDIT_SIZE", "DIAGNOSTIC_V6DEV_REPRO", "DIAGNOSTIC_EXTERNAL", "DIAGNOSTIC_V8_STALE_VARIANTS")}
fm["not_available"] = {
    "v6_test_under_output_free_v7": "NOT RUN (observed/contaminated split)",
    "v8_test": "RUN ONCE (see v8_frozen_runs.v8_test_frozen). Not repeated. 4 programs/163 pairs excluded (stale variants).",
    "weight_models_M1_M2_on_test": "scored on v8 test by evaluate_v8.py as SECONDARY (weights fit on v6 train, frozen in FREEZE_V8.json); WEIGHT_FITTING.json['test'] remains null (fit_weights.py test was never run)",
    "java_quixbugs": "NOT RUN", "power_analysis_v8": "NOT RUN",
    "v8_val_split": "NOT scored", "quixbugs_ci": "now in DIAGNOSTIC_EXTERNAL.json (cluster bootstrap, 40 programs)"}
(EV / "FINAL_METRICS.json").write_text(json.dumps(fm, indent=2) + "\n")

m = J("artifacts/paper_evidence/EXPERIMENT_MANIFEST.json")
git = lambda *a: subprocess.run(["git", *a], cwd=R, capture_output=True, text=True).stdout.strip()  # noqa: E731
m.setdefault("runs_v8_frozen", {})
m["runs_v8_frozen"] = {
    "freeze": [src("artifacts/final/FREEZE_V8.json"), src("artifacts/final/FREEZE_V8_AMENDMENT1.json"), src("artifacts/final/FREEZE_V8_AMENDMENT2.json")],
    "freeze_commits": {"FREEZE_V8": "ebb8c44", "AMENDMENT1": "465be1b", "AMENDMENT2": "c0f6c6d"},
    "threshold": src("artifacts/final/THRESHOLD_V8_FROZEN.json"), "weights": src("artifacts/final/WEIGHT_FITTING.json"),
    "v8_dev_dryrun": {"command": "PYTHONHASHSEED=0 python experiments/final/evaluate_v8.py run --split dev", "output": src("artifacts/paper_evidence/V8_DEV_DRYRUN_EVALUATION.json")},
    "v8_test": {"commands": [
        "python experiments/final/run_chunked.py --split test --pairs-dir artifacts/final/v8_test_nonstale --tag v8test --out-dir artifacts/final   # ~190 s, 22 subprocesses",
        "python experiments/final/static_baselines.py --pairs artifacts/final/pairs_v8test_output_free_v8.jsonl --dataset benchmark/datasets/v8",
        "PYTHONHASHSEED=0 python experiments/final/evaluate_v8.py run --split test"],
        "scored_pairs": src("artifacts/final/pairs_v8test_output_free_v8.jsonl"), "output": src("artifacts/paper_evidence/V8_TEST_EVALUATION.json"),
        "attempts": ["attempt 1 single-process, 1130 pairs: stalled at ~525 (checkpoint unread, kept as ABORTED_*)",
                     "attempt 2 resume: stalled at same pair", "attempt 3 single-process, 967 non-stale pairs: stalled at ~525 (checkpoint never opened, outside repo)",
                     "attempt 4 chunked harness (dev-equivalence 0/597 diffs): completed -> the reported result. Run exactly once; no re-run."]},
    "diagnostics": {k: {"script": s, "output": src(f"artifacts/paper_evidence/{k}.json")} for k, s in (
        ("DIAGNOSTIC_EDIT_SIZE", "experiments/final/diagnose_edit_size.py"), ("DIAGNOSTIC_V6DEV_REPRO", "experiments/final/build_v6dev_repro_diagnostic.py"),
        ("DIAGNOSTIC_EXTERNAL", "experiments/final/diagnose_external.py"), ("DIAGNOSTIC_V8_STALE_VARIANTS", "experiments/final/audit_v8_staleness.py"))},
    "supplement": {"script": "experiments/final/supplement_v8.py", "output": src("artifacts/paper_evidence/V8_COMPONENT_COMPARISON.json")},
    "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(), "PYTHONHASHSEED": "0 (pinned for all scoring)"},
    "git_head_at_generation": git("rev-parse", "HEAD")}
m["not_run"] = [x for x in m["not_run"] if "v8 test" not in x and "FREEZE_V8" not in x] + [
    "make v7-test (v6 TEST under output_free_v7)", "fit_weights.py test", "v8 val split scoring", "make java", "power_analysis.py on v8",
    "re-run of the v8 test (forbidden: single run)"]
(EV / "EXPERIMENT_MANIFEST.json").write_text(json.dumps(m, indent=2) + "\n")
print("ok")

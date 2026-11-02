"""Writes artifacts/final/FREEZE_V9.json. Reads NO score values: only file hashes and counts of lines."""
import datetime, hashlib, json, pathlib, subprocess
R = pathlib.Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256((R / p).read_bytes()).hexdigest()   # noqa: E731
code = ["experiments/final/evaluate_v9.py", "experiments/final/fit_weights.py", "experiments/final/extraction.py", "experiments/final/protocol.py",
        "experiments/final/entry_policy.py", "experiments/final/class_driver.py", "experiments/final/static_baselines.py", "experiments/final/edit_size_analysis.py",
        "experiments/final/run_chunked.py", "sbg/statistics.py", "sbg/extraction/dynamic/tracer.py", "benchmark/scripts/generate_v9_composed.py"]
fz = {
    "artifact": "FREEZE_V9", "status": "FROZEN", "written_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "plan": {"path": "docs/current/EVALUATION_PLAN_V9.md", "sha256": sha("docs/current/EVALUATION_PLAN_V9.md")},
    "git_head_at_freeze": subprocess.run(["git", "rev-parse", "HEAD"], cwd=R, capture_output=True, text=True).stdout.strip(),
    "evaluation_script_sha256": sha("experiments/final/evaluate_v9.py"), "code_sha256": {p: sha(p) for p in code},
    "models_sha256": sha("artifacts/final/V9_MODELS_FROZEN.json"),
    "models": {"path": "artifacts/final/V9_MODELS_FROZEN.json", "fitted_on": "v9c train (matched-complete), 46 programs"},
    "scored_v9c_val_sha256": sha("artifacts/final/pairs_v9c_val_output_free_v8.jsonl"),
    "scored_v8_val_sha256": sha("artifacts/final/pairs_v8val_output_free_v8.jsonl"),
    "dataset": {"v9c_pairs_val": sha("benchmark/datasets/v9_composed/pairs_val.jsonl"), "v9c_manifest": sha("benchmark/datasets/v9_composed/manifest.json"),
                "v8_pairs_val": sha("benchmark/datasets/v8/pairs_val.jsonl"), "audit_v9c": sha("artifacts/final/BENCHMARK_VALIDITY_AUDIT_V9C.json")},
    "val_programs": sorted({json.loads(l)["base_id"] for l in (R / "benchmark/datasets/v9_composed/pairs_val.jsonl").read_text().splitlines() if l.strip()}),
    "val_scores_opened_before_freeze": False,
    "statement": ("The val score files were produced by the scorer and had static_baselines.py merged in (reads source files only). No val score value "
                  "from either file was printed, aggregated or inspected before this freeze; only evaluate_v9.py `run --split val` will open them. Dev and train "
                  "were inspected. The v8 test split is not used."),
    "predictors_and_models": "see plan sections 5-6", "tests": "H1-H4 Holm, plan section 6",
    "deviations": ["harness: run_chunked.py gained a mechanical RSS/time watchdog + per-pair fallback after a v8-train program (math_gray_code) made a mutant allocate >18 GB; "
                   "affected pairs are recorded unevaluated with failure_kind=harness_timeout (train: 6 v8 + 4 v9c pairs). Val and dev needed no fallback (see logs).",
                   "v8 val and v8 train were scored for the first time in this work with the chunked harness (equivalence to single-process scoring verified on dev: 0/597 differences).",
                   "the EQUIVALENT members of v9c matched sets are the v8 EQUIVALENT pairs, scored in the v8 scored files and reused verbatim."],
    "run_command": "PYTHONHASHSEED=0 python experiments/final/evaluate_v9.py run --split val",
}
(R / "artifacts/final/FREEZE_V9.json").write_text(json.dumps(fz, indent=2) + "\n")
print("ok", fz["evaluation_script_sha256"][:12], fz["val_programs"])

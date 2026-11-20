# REPRODUCIBILITY: commands, environment, seeds

Environment used (2026-10-28): macOS 26.6 (arm64, Apple M4 Max), CPython **3.13.5** from `venvs/py313`
(artifacts historically recorded 3.13.15; `.python-version` = 3.13), `requirements-lock.txt`
(pytest only; the SBG pipeline is stdlib-only). Base commit `f15cb9a` on branch `remediation/sbg-v2`;
this evidence was produced with additional uncommitted working-tree changes that are included in the
evidence commit (see `EXPERIMENT_MANIFEST.json › uncommitted_tracked_modifications_at_generation`).
All commands run from the repository root (`SBG/`). Set `PY=<path to>/venvs/py313/bin/python`.

Seeds: bootstrap 42 (2000 resamples), permutation 42 (2000), label shuffle 42 (500), split seed 42,
transformation seeds 0,1,2.

## 1. Train scoring (v6 TRAIN, output_free_v7) — completed this session

```
$PY experiments/final/run_main_evaluation.py --split train --protocol output_free_v7 \
    --dataset-dir benchmark/datasets/v6 --tag v6train --checkpoint-every 5
$PY experiments/final/static_baselines.py --pairs artifacts/final/pairs_v6train_output_free_v7.jsonl --dataset benchmark/datasets/v6
$PY experiments/final/analyse_results.py --split train --protocol output_free_v7 --tag v6train \
    --audit artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json
```
History: attempt 1 (`logs/v7_train_eval.txt`) and attempt 2, PID 36301 (`logs/v7_train_eval_r2.txt`) both ended at
1000/1129 with no completion marker; the process was gone when inspected. The resume (`logs/v7_train_eval_r3.txt`,
~863 s) read the 1000-row checkpoint and finished 129 pairs. Wall time of a clean uninterrupted run was never observed;
the long tail (pairs 1000–1129) is dominated by non-terminating SP-2/SC mutants (per-trace timeout 1 s, per-program budget 60 s, `MAX_TIMEOUTS`=2 in `experiments/final/extraction.py`).
A from-scratch rerun produces the same file only if the traced mutants hit the same time budgets (see DATA_VALIDATION §D).

## 2. Weight fitting (train fit, dev selection) — completed this session

```
$PY experiments/final/fit_weights.py fit        # writes artifacts/final/WEIGHT_FITTING.json (~6 s)
```
Do **not** run `fit_weights.py score` or `test` (they touch the test split).
Output: M0 train/dev 0.6653/0.6671; M1 0.6950/0.6656; M2 0.7242/0.7128; chosen_on_dev = M2.

## 3. v8 dev re-score — completed this session

```
$PY experiments/final/run_main_evaluation.py --split dev --protocol output_free_v8 \
    --dataset-dir benchmark/datasets/v8 --tag v8devrescore
$PY experiments/final/static_baselines.py --pairs artifacts/final/pairs_v8devrescore_output_free_v8.jsonl --dataset benchmark/datasets/v8
$PY benchmark/scripts/observability_audit_v7.py benchmark/datasets/v8 artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json
   # prints a harmless relative_to() ValueError after writing the file when the out path is relative
$PY experiments/final/analyse_results.py --split dev --protocol output_free_v8 --tag v8devrescore \
    --audit artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json
```
~25 s for scoring; deterministic (two runs identical).

## 4. Evidence package

```
$PY experiments/final/edit_size_confound_multi.py --pairs artifacts/final/pairs_v6train_output_free_v7.jsonl --dataset-dir benchmark/datasets/v6 --out artifacts/paper_evidence/raw/confound_v6train.json
$PY experiments/final/edit_size_confound_multi.py --pairs artifacts/final/pairs_v6dev_output_free_v7.jsonl   --dataset-dir benchmark/datasets/v6 --out artifacts/paper_evidence/raw/confound_v6dev.json
$PY experiments/final/edit_size_confound_multi.py --pairs artifacts/final/pairs_v8devrescore_output_free_v8.jsonl --dataset-dir benchmark/datasets/v8 --out artifacts/paper_evidence/raw/confound_v8dev.json
$PY experiments/final/build_paper_evidence.py        # DATASET_SUMMARY.json, BASELINE_COMPARISON.csv, raw/recomputed_comparisons.json (~25 s)
$PY experiments/final/tau_operating_points.py        # raw/tau_operating_points.json
$PY experiments/final/build_ablations.py             # ABLATIONS.json
$PY experiments/final/build_paper_evidence_meta.py   # EXPERIMENT_MANIFEST/FINAL_METRICS/WEIGHT_FITTING/THRESHOLD_PROVENANCE.json
```

## 5. Validation

```
$PY -m pytest sbg/ tests/ -q                          # 760 passed
$PY experiments/final/consistency_check.py            # 10/10
$PY experiments/final/stanford_gate.py                # 8/20 PASS, 12 BLOCKED
$PY experiments/final/data_integrity.py --dataset benchmark/datasets/v8 --strict   # 0 defects
$PY experiments/final/data_integrity.py --dataset benchmark/datasets/v6            # 75 known defects
```

## 6. Reused (not re-run) artifacts

`pairs_v6dev_output_free_v7.jsonl` + `MAIN_EVALUATION_v6dev_output_free_v7.json` (frozen; never re-run, see STATUS.md),
`THRESHOLD_FROZEN.json`, `BENCHMARK_VALIDITY_AUDIT_V7.json`, `MAIN_EVALUATION_v6test_output_free_v6.json`,
`BUGSINPY_output_free_v7.json`, `QUIXBUGS_output_free_v7.json`.

## 7. Never run (do not run without a frozen v8 protocol)

`make v7-test`, `fit_weights.py score|test`, any v8 val/test scoring, `make java`.

## 8. Reproducibility caveats

* The frozen v6 dev scores are not byte-reproducible with current code (DATA_VALIDATION §D); the v8 dev scoring is.
* Tracer behaviour depends on wall-clock budgets (per-trace and event caps), so pathological non-terminating mutants can score differently across machines/loads.
* `git` hashes of working-tree modifications at generation time are in `EXPERIMENT_MANIFEST.json`; they are committed together with this package.
* Run logs are in `logs/*.txt` (copies of `/tmp/*.log`, local paths stripped; `*.log` is gitignored in this repo).

---
# Addendum 2026-10-29: diagnostics, frozen v8 evaluation, environment

Environment: macOS (arm64, Apple M4 Max), CPython 3.13.5 (`venvs/py313`), stdlib-only pipeline + pytest. **All scoring is run with `PYTHONHASHSEED=0`**
(original v6 code was hash-order dependent, see `DIAGNOSTIC_REPORT.md` P2; v8 scores are hash-seed independent). `PY=<repo>/../venvs/py313/bin/python`.
Seeds: bootstrap/permutation/label-shuffle/split 42; 2000 bootstrap resamples; 500 shuffles.

## 9. Diagnostics (read-only on scored artifacts, minutes each)
```
$PY experiments/final/diagnose_edit_size.py          # DIAGNOSTIC_EDIT_SIZE.json  (P1)
$PY experiments/final/build_v6dev_repro_diagnostic.py # DIAGNOSTIC_V6DEV_REPRO.json (P2; uses git worktrees ad7b655 d9d6380 b54ea99)
$PY experiments/final/diagnose_external.py           # DIAGNOSTIC_EXTERNAL.json   (P3)
$PY experiments/final/diagnose_bugsinpy_cache.py     # raw/bugsinpy_purge_rescore.json (re-extracts BugsInPy units, ~minutes)
$PY experiments/final/audit_v8_staleness.py          # DIAGNOSTIC_V8_STALE_VARIANTS.json (content-only; reads no scores)
```
## 10. Frozen v8 evaluation (order matters; see `artifacts/final/FREEZE_V8*.json`)
```
# dev dry run (tau_v8 derived on dev only) -> THRESHOLD_V8_FROZEN.json, V8_DEV_DRYRUN_EVALUATION.json
PYTHONHASHSEED=0 $PY experiments/final/evaluate_v8.py run --split dev
# harness equivalence on dev (must print "0 differ")
$PY experiments/final/run_chunked.py --split dev --pairs-dir benchmark/datasets/v8 --tag v8dev_chunked \
    --verify-against artifacts/final/pairs_v8devrescore_output_free_v8.jsonl --out-dir /tmp/chunk_dev
# TEST: SINGLE RUN, ~190 s. evaluate_v8.py refuses to overwrite V8_TEST_EVALUATION.json. Do not repeat.
$PY experiments/final/run_chunked.py --split test --pairs-dir artifacts/final/v8_test_nonstale --tag v8test --out-dir artifacts/final
$PY experiments/final/static_baselines.py --pairs artifacts/final/pairs_v8test_output_free_v8.jsonl --dataset benchmark/datasets/v8
PYTHONHASHSEED=0 $PY experiments/final/evaluate_v8.py run --split test
$PY experiments/final/supplement_v8.py && $PY experiments/final/finalize_evidence.py   # component comparison, CSV rows, FINAL_METRICS/MANIFEST
```
Note: `run_chunked.py` was introduced after three single-process attempts stalled (Amendments 1–2). Single-process re-scoring of v8 dev (`run_main_evaluation.py`) works (~25 s) and is equivalent.
To verify the reported test numbers without re-running the test, re-run only `evaluate_v8.py` analysis logic on the committed `pairs_v8test_output_free_v8.jsonl` into another path (the script refuses to overwrite the committed result by design), or recompute with `supplement_v8.py` (prints the same AUROCs for `sbg_v5`).
## 11. Validation at HEAD
`pytest sbg/ tests/ -q` (760 passed); `consistency_check.py` 10/10; `stanford_gate.py` 8/20 PASS (12 BLOCKED — see RESEARCH_STATUS §F);
`data_integrity.py --dataset benchmark/datasets/v8 --strict` 0 defects (does not detect the stale-variant defect; see `audit_v8_staleness.py`).

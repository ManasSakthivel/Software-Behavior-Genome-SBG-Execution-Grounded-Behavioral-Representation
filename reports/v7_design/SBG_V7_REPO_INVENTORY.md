# SBG V7: Repository Inventory (reuse / retire / preserve-as-is)

Read-only forensic inventory. Repo `/Users/manassakthivel/Desktop/SBG-V6`, branch `feature/sbg-v7-architecture` at `197039a1`, working tree clean (0 uncommitted entries), 65 commits on the branch history, tag `v6-holdout-complete`. Branches present: `main`, `feature/sbg-v6-redesign`, `feature/sbg-v7-architecture`; remotes include `checkpoint/sbg-v5-complete-before-v6`, `remediation/sbg-v2..v4`, `research/manuscript-evidence-transfer`, `research/v6-evaluation-correction`. Commit history shows V5 TEST (`7958a04d`), v9 freeze before VAL (`6dd5a0ff`), V6 DEV audit/freeze (`1943d30a`), holdout scripts then features then results then reports (`4fc7d149` -> `042aeb01` -> `afdb2d82` -> `9ccea83d` -> `197039a1`).

Status of everything below: classification is by what the files and reports show; reusable items are *candidates* that still need the V7 requirement (R-xx, see the matrix) verified; nothing was executed.

## 1. Top-level layout (verified by `ls`)
`sbg/` (V1-V6 library), `sbgv6/` (V6 feature package), `experiments/final/` (~70 scripts), `benchmark/`, `baselines/`, `external/` (quixbugs, bugsinpy, quixbugs_java), `artifacts/` (final, paper_evidence, v2-v6, ...), `reports/` (external_validation, recovery_programme, remediation, sprint2, v6_investigation, v6_redesign, and now v7_design), `docs/current/` (20 protocol/limitation docs), `tests/` (+ `tests/v6`), `scripts/`, `phase5/ phase6/ phase7/`, `paper/`, `results/`, `STATUS.md`, `TEST_LOCK.json`, `Makefile`, `requirements-lock.txt`.

## 2. Reusable infrastructure (reuse, subject to R-xx fixes)

| Component | Paths | Why reusable (verified) | Caveat / required change |
|---|---|---|---|
| Sandbox runner | `sbg/v2/execution/runner.py` (277 lines; `SandboxRunner`, `SandboxResult`) | Single execution path used by extraction and by the V6 adapter | Needs per-unit hard timeout and no group-hang (R-07, F-13) |
| Tracer | `sbg/extraction/dynamic/tracer.py` (631 lines); `tests/test_tracer_isolation.py`; `sbg/extraction/dynamic/test_tracer.py` | Event-level call/line/return tracing; isolation test exists | Return-value capture is in the event stream but the V6 channel did not exploit it; add first-class return/exception observations (R-04). Accumulated tracer state suspected in stalls (`artifacts/paper_evidence/RESEARCH_STATUS.md`) |
| Shared extraction protocol | `experiments/final/extraction.py` (563 lines), `protocol.py`, `class_driver.py`, `entry_policy.py` | Header states it executes each program once and gives every predictor the same traces, recording failure reasons instead of dropping silently (R-10 precedent) | Entry/driver policy is where unsupported-signature UNKNOWNs arise (R-02) |
| V6 adapter | `sbgv6/observe.py` (58 lines: `Adapter` protocol, `PythonAdapter`, `Observation` with `failure_kind` never imputed) | Language-adapter contract; reason codes | Python only; Java/C interface-only |
| V6 features / distance / config | `sbgv6/features.py` (286), `distance.py` (61), `config.py` (8: N_MIN, K_W, U_MIN, ALPHA0, PROTOCOL `output_free_v8`) | Blocks A, B, C, R, E with explicit `return_state`; frozen constants | Blocks must be re-evaluated under R-20/R-21; E block unstable (F-11) |
| Statistics utilities | `sbg/statistics.py` (`auroc` tie-aware, `cluster_bootstrap_ci`, `cluster_permutation_p`, `paired_cluster_bootstrap_delta`, `label_shuffle_noise_floor`, `holm_bonferroni`, `wilson_interval`); `tests/test_statistics.py` | Docstring documents fixes of pair-level bootstrap and zero p-values; used for V6 holdout CIs | Reuse as is |
| Freeze / manifest practice | `artifacts/final/FREEZE_V8.json`, `FREEZE_V9.json`, `FREEZE_V10.json`, `freeze_*.json`; `artifacts/v6/FREEZE_V6.json`, `FINAL_MANIFEST_V6_candidate1.json` (29 hashes); `TEST_LOCK.json`; `experiments/final/make_freeze_*.py`, `artifact_provenance.py`; `tests/test_threshold_provenance.py`; `HOLDOUT_ANALYSIS_PLAN.md` | Hash-then-score practice; plan committed before holdout run | Add machine-checked chronology (R-28) |
| Audit scripts and outputs | `artifacts/v6/audit/` (LEAKAGE_AUDIT, DUPLICATE_AUDIT, DIFF_SC6_AUDIT, LABEL_ADJUDICATION*.{json,csv}, PROTOCOL_V2, SELECTION_*), `benchmark/scripts/leakage_audit.py`, `diversity_audit.py`, `observability_audit*.py`, `power_analysis.py`, `experiments/final/audit_*.py`, `output_oracle_leak_audit.py`, `audit_v8_staleness.py` | Directly feed R-22/R-24/R-30 | Promote to CI gates |
| Benchmark generators (infrastructure only) | `benchmark/scripts/generate_v8_dataset.py`, `generate_v9_composed.py`, `generate_v10_independent.py`, `assign_splits.py`, `validate_benchmark.py`, `validate_fresh_program.py`; `benchmark/ground_truth/{validator.py,schema.json}`; `benchmark/transformations/{mutations,preserving}` | Machinery for program-grouped splits and validation | Individual generators listed in s3 are not reusable as label sources |
| Corpora | `benchmark/corpus/{base_programs,fresh_programs}`, `external/{quixbugs,bugsinpy,quixbugs_java}`, `benchmark/v5/{corpus,hard_negatives,java_programs}` | Source programs and real bugs | Re-sealed holdout must use new programs (R-26) |
| Evaluation drivers | `experiments/final/evaluate_v*.py`, `run_chunked.py` (per-program/per-pair timeouts 420/90 s), `static_baselines.py`, `hard_negative_evaluation.py` | Chunked per-pair mode was the reliable harness (`SBG_V6_FINAL_ARCHITECTURE.md` s8) | Replace group mode |
| Tests | `tests/` (20 files), `tests/v6/test_sbgv6.py`, `sbg/**/test_*.py` | Regression coverage of tracer, statistics, entry policy, external harnesses | Extend with R-04/R-05 property tests |

## 3. Scientifically weak components (retire as scientific evidence; keep as negative-result record)

| Weakness | Where (verified) | Facts | Requirement |
|---|---|---|---|
| Edit-size-confounded labels | `docs/current/EDIT_SIZE_REDESIGN.md`; `artifacts/paper_evidence/DIAGNOSTIC_EDIT_SIZE.json`; `V6R` decision report s4 | Reversed edit size 0.771 DEV, 0.772 v8 test, 0.847 BugsInPy; SC mean 5.4 vs SP 11.3 diff lines | R-09, R-25 |
| SP-8 non-equivalent generator | `benchmark/transformations/preserving/transformations/sp8_extract_function.py`; `artifacts/v6/audit/LABEL_ADJUDICATION.csv` | 47 EQUIVALENT pairs with exception-type difference | R-23 |
| SP-11 repr artifact | `.../sp11_equiv_data_structure.py`; same CSV | 42 pairs, deque vs list | R-05 |
| Label = f(generator) | `artifacts/v6/audit/LEAKAGE_AUDIT.json` | `label_pure_function_of_type: true` | R-22 |
| Duplicates | `artifacts/v6/audit/DUPLICATE_AUDIT.json` | 596 groups / 1713 of 2392 rows; 1275 unique files | R-24 |
| Harness timeouts | `experiments/final/run_chunked.py`, `artifacts/v6/repro/extract.attempt*.log`, `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s8 | 51 pairs lost to group timeout; v8 scoring stalls at ~525 pairs | R-07 |
| Nondeterminism | `V6R/SBG_V6_ABSTENTION_AND_COVERAGE_REPORT.md` | 60 BugsInPy nondeterministic bases, cause uninvestigated | R-06 |
| Signature-unsupported units | same | 49 BugsInPy UNKNOWN | R-02 |
| Output-free channel blind to returns | `sbgv6/features.py:return_state`, `V6R` architecture s4 | SC-6 holdout 0.54 / 0.32; d_R excluded from primary | R-04 |
| Stale variants | `artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json` | 8/100 programs stale | R-30 |
| Unprovable holdout status | `docs/current/TEST_SET_CHRONOLOGY.md`, `artifacts/v6/holdout/` | all five holdouts previously seen | R-26 |
| Abstention median fill | `artifacts/v6/FINAL_MANIFEST_V6_candidate1.json` policy P1 (see architecture s3) | ties at 0.3659 on BugsInPy | R-18 |
| Hard-coded gate (superseded) | `docs/archive/superseded_gate/` (referenced in chronology doc, not opened) | | R-28 |

Datasets that carry these defects (do not use as labelled ground truth for V7 claims): `benchmark/datasets/{v6,v7,v8,v9_composed}`, `benchmark/datasets/v10_independent` (v10 was the more independent set but already observed), `benchmark/datasets/pairs_*.jsonl`.

## 4. Preserve as-is (immutable history; do not edit, re-run, or regenerate)
- Tag `v6-holdout-complete`; branch `feature/sbg-v6-redesign`; remote `checkpoint/sbg-v5-complete-before-v6`.
- Frozen holdout outputs: `artifacts/v6/holdout/` (features_*.jsonl, `results/HOLDOUT_RESULTS.json`, logs, `HOLDOUT_ANALYSIS_PLAN.md`); `artifacts/v6/final/`, `artifacts/v6/repro/` (attempt logs retained), `artifacts/v6/FREEZE_V6.json`, `FINAL_MANIFEST_V6_candidate1.json`.
- Evidence packages: `artifacts/paper_evidence/` (V3, V4, V8, V9, V10 results, `ABORTED_*` checkpoint in `artifacts/final/` marked NOT_USED), `artifacts/final/FREEZE_*.json`, `MAIN_EVALUATION_*` (the `v6dev` one is documented "never re-run" in `STATUS.md`).
- Reports: `reports/v6_redesign/` (including the 4 pre-holdout docs and `spec/`), `reports/v6_investigation/`, `reports/remediation/`, `reports/sprint2/`, `reports/recovery_programme/`, `reports/external_validation/`.
- Governance: `docs/current/*` (TEST_SET_CHRONOLOGY, LIMITATIONS, preregistration), `TEST_LOCK.json`, `SBG_PRE_V6_*` checkpoint manifest and CSV.
- Holdout data must be treated as development data for V7 (R-26), but its files stay untouched as the V6 record.

## 5. Not verified
Quality or correctness of `sbg/v2/execution/runner.py` and `tracer.py` beyond line counts and the existence of an isolation test; contents of `phase5-7/`, `paper/`, `results/`, `baselines/`, `sbg/v3`, `sbg/v5` internals; `docs/archive/` (path referenced, not listed); whether `.venv` exists. No code or holdout script was executed.

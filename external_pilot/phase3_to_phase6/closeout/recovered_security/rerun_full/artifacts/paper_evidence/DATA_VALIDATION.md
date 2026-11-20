# DATA_VALIDATION: checks performed and results (2026-10-28)

Machine-readable counterparts: `DATASET_SUMMARY.json` (counts, disjointness, integrity),
`EXPERIMENT_MANIFEST.json`. Log transcripts in `logs/`.

## A. Dataset structure (computed by `experiments/final/build_paper_evidence.py`)

| Dataset | Programs | Pairs | train | dev | val | test |
|---|---|---|---|---|---|---|
| v6 (`benchmark/datasets/v6`) | 60 | 2340 | 1129 pairs / 28 prog | 372 / 10 | 351 / 9 | 488 / 13 |
| v8 (`benchmark/datasets/v8`) | 100 | 4245 | 2057 / 49 | 597 / 14 | 461 / 11 | 1130 / 26 |

CHANGED/EQUIVALENT per split: v6 train 570/559, dev 159/213, val 169/182, test 246/242;
v8 train 1167/890, dev 348/249, val 243/218, test 648/482.

| Check | v6 | v8 | Result |
|---|---|---|---|
| Base-program ID disjointness across train/dev/val/test | none shared | none shared | PASS |
| Pair-ID global uniqueness | unique | unique | PASS |
| All `base_path`/`variant_path` files exist | 0 missing | 0 missing | PASS |
| v6 ∩ v8 base programs | none | none | PASS |
| SP-2 dangling-method defect (`data_integrity.py`) | **75 pairs** (documented historical defect; 70 fail at run time) | **0** (`--strict` exits 0) | v6 known-defective, v8 clean |

Note: the 60 v6 programs differ from the "64" quoted elsewhere (4 on disk are unassigned to any split).
v8 has 123 files in `benchmark/corpus/fresh_programs` but only 100 are assigned to splits.

## B. Scored runs (rows = dataset pairs, each pair present exactly once, in dataset order)

| Run | Rows | Evaluated | CHANGED / EQUIV evaluated | Programs evaluated | Failure ledger |
|---|---|---|---|---|---|
| v6 train, output_free_v7 (this session) | 1129 | 1090 | 531 / 559 | 28 | variant:import_error 15, variant:nonterminating 24 |
| v6 dev, output_free_v7 (frozen) | 372 | 345 | 156 / 189 | 9 | base:unsupported_signature 27 (one program not evaluable) |
| v8 dev, output_free_v8 (this session re-score) | 597 | 593 | 344 / 249 | 14 | variant:import_error 2, variant:unsupported_signature 2 |
| v6 test, output_free_v6 (historical) | 488 | 259 | 121 / 138 | 7 | base:unsupported_signature 218 + 11 variant failures |

VALID set (after static audit) equals EVALUABLE on v7 dev and v8 dev; on v6 train VALID = 1033 (474 / 559), i.e. 57 evaluated pairs
dropped as statically unobservable CHANGED pairs. `integrity_checks.*_ids_equal_dataset_ids` in `DATASET_SUMMARY.json`: all four runs
have scored pair IDs identical to the dataset pair IDs.

## C. Split-boundary / leakage checks

| Check | Result |
|---|---|
| `pairs_v6test_output_free_v7.jsonl`, `MAIN_EVALUATION_v6test_output_free_v7.json`, `programs_v6test_output_free_v7.json`, any v8 test score, `FREEZE_V8.json`, `THRESHOLD_V8_FROZEN.json` exist? | **None exist** (checked in `DATASET_SUMMARY.json › integrity_checks.forbidden_test_artifacts_present = []`) |
| Any `learned_*` score written to any scored pair file | 0 rows in all four files |
| Weight fit input splits | train + dev only; `fit_weights.py` never opens a test file except to refuse refit |
| τ\* source | dev pairs only; `derive_threshold.py` refuses non-dev input; recorded SHA-256 of dev pair file and scored dev file both **match the files now** |
| Evidence scripts | `edit_size_confound_multi.py` aborts on any row with `split == "test"`; `build_paper_evidence.recompute` asserts non-test |
| v8 dev used for tau/weights? | No. It is out-of-distribution evaluation data for both |

## D. Reproducibility / determinism checks

| Check | Result |
|---|---|
| v8 dev re-scored twice from scratch | Identical (0 differences, 0 eval-status differences) → deterministic on that dataset |
| v6 dev re-scored at committed HEAD (`f15cb9a`, clean worktree) vs frozen file | Same 345 evaluable pairs; **46 scores differ** (max 0.0167) |
| v6 dev re-scored with working-tree edits vs frozen file | 338 evaluable (7 `nonterminating`), 39 scores differ (max 0.0364) |
| Impact | sbg_v5 dev AUROC 0.6671 (frozen) → 0.6783 (HEAD) → 0.6681 (working tree, n=338); M2 0.7128 → 0.7441 / 0.7322; τ 0.072905 → 0.072531 |
| v6 train resume | Checkpoint 1000 rows validated (unique, dataset order, `output_free_v7`, `benchmark/datasets/v6`); final 1129 rows in order |
| pytest (`venvs/py313`) | 760 passed, 0 failed (`logs/pytest_py313_final.txt`) |
| `experiments/final/consistency_check.py` | 10/10 (`logs/consistency_check_final.txt`) |
| Python 3.9 test run | Not re-run today |

Frozen v6 dev files were left unmodified, as required. All re-scores were written to `/tmp` (copies of logs in `logs/`).

## E. Known data limitations

1. **Edit-size confound** (see RESEARCH_STATUS N1/N2): CHANGED pairs mostly have 0–2 changed lines while EQUIVALENT pairs average ~24 (v6) / ~9 (v8) changed lines (`ABLATIONS.json › mean_edit_size`).
2. **Few program clusters**: 9 (v6 dev), 14 (v8 dev), 28 (v6 train). Cluster bootstrap with k<15 is flagged unreliable by `STATISTICAL_PROTOCOL.md` §3.
3. **v6 entry-policy defect**: 30 EQUIVALENT SP-2 pairs across train/dev/test trace a renamed `test_*` driver (listed in `consistency_check.py::KNOWN_HISTORICAL_DRIVER_TRACES`).
4. **Coverage**: v6 test evaluates only 259/488 pairs under output_free_v6; v7 dev excludes 27 pairs (one program has an unsupported signature).
5. **`programs_v6train_output_free_v7.json` is partial** (resume did not rebuild the cache): 133 entries, `n_ok`=129. Do not use for program counts.
6. **Validity audit for v8** is the *v7* observability audit applied to v8 pairs (`BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json`); no v8-specific audit exists. All 597 v8 dev pairs pass it.
7. **Absolute paths**: the committed historical artifacts (`programs_*`, `pairs_bugsinpy_*`, etc.) contain local `/Users/...` paths. The new `programs_v6train_*` and `programs_v8devrescore_*` and the evidence logs were stripped of them; the committed historical files were left untouched.
8. **No v8-specific τ\*, no v8 weights**, no v8 frozen protocol.
9. `FINAL_REPRODUCIBILITY_MANIFEST.json` / `ARTIFACT_PROVENANCE.json` in `artifacts/final/` predate v7/v8 (stale); `EXPERIMENT_MANIFEST.json` here supersedes them for this evidence set.

10. The four superseded pre-regeneration v8 dev files (`pairs_dev_output_free_v8.jsonl`, `pairs_v8dev_output_free_v8.jsonl`, `programs_dev_output_free_v8.json`, `programs_v8dev_output_free_v8.json`) remain on the author's disk, **untracked and not committed** (stale vs the current v8 dataset; two embed local absolute paths). No metric in this package uses them.

---
# Addendum 2026-10-29

## E. v8 committed variants are stale for 8 base programs
`benchmark/datasets/v8` variants were generated at 07:53 on 2026-10-28; 8 base programs were edited at 07:58–07:59 afterwards. Re-generated ASTs differ for those 8
programs (test: `math_count_set_bits`, `math_gcd_lcm`, `math_nthroot_newton`, `math_power_modular` = 163 pairs; train: `math_digital_root`, `math_extended_gcd`, `math_trailing_zeros` = 126 pairs; dev: `math_happy_number` = 43 pairs).
The other 92 programs regenerate with identical ASTs. Source: `DIAGNOSTIC_V8_STALE_VARIANTS.json` (`audit_v8_staleness.py`; content-only, no scores read).
Handling: programs excluded **by name before test scoring** (frozen in `FREEZE_V8.json`); the committed dataset was **not** modified. Test = 22 programs, 967 pairs (956 evaluated). The `data_integrity.py --strict` check passes but does not test freshness.
Consequence: weights were fit on **v6** train, so v8 train staleness does not affect any reported number; v8 dev (593-pair original analysis) includes one stale program (`math_happy_number`), the frozen-script dev dry run excludes it (550 pairs).

## F. v6 dev drift (resolved) — see `DIAGNOSTIC_V6DEV_REPRO.json`
46/345 = 18 (hash-order, original code) + 28 (aliasing fix in `sort_quicksort`). 7 pairs become non-evaluable under later tracer fix. Frozen artifact retained unmodified.

## G. Dev/test scoring harness
Single-process scoring of ≥ ~525 mutants stalls (accumulated leaked tracer threads). `run_chunked.py` (one subprocess per base program) verified identical on dev (0/597 differences in evaluated flag and all execution scores). Final test scoring used it.

## H. Test-split provenance
v8 test pair ids = `artifacts/final/v8_test_nonstale/pairs_test.jsonl` (967) = `benchmark/datasets/v8/pairs_test.jsonl` minus 163 stale-program pairs. `evaluate_v8.py:load_scored` asserts scored ids == dataset ids. 11 pairs unevaluated: variant import_error 4, nonterminating 6, unsupported_signature 1.

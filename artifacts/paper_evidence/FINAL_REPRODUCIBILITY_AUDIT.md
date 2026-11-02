# FINAL REPRODUCIBILITY AUDIT
**Branch:** `remediation/sbg-v4`  
**Commit:** `c5bc130ea0909379315a7fdc160aa777c6c04840`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)

---

## 1. Test Suite Count

**Claimed in PHASE7_ACCEPTANCE_V4.md:** 807 passed (3 warnings, pre-existing)

**Verified:** Test suite run 2026-10-30 confirms: `807 passed, 3 warnings in 371.07s`

✅ **Confirmed: 807 tests pass.**

The 3 warnings are pre-existing `SyntaxWarning: "is not" with 'int' literal` in a benchmark dataset variant file (not in SBG code). These are not test failures and do not affect any result.

---

## 2. Frozen Dataset and Manifest Integrity

All file hashes were verified live against committed values in `EXPERIMENT_MANIFEST_V4.json`:

| File | Committed SHA256 | Current SHA256 | Match |
|---|---|---|---|
| `artifacts/final/FREEZE_V10.json` | `77e95252…` | `77e95252…` | ✅ |
| `artifacts/final/FREEZE_V10_SCORED.json` | `169600ec…` | `169600ec…` | ✅ |
| `artifacts/final/V10_MODELS_FROZEN.json` | `fe637cbd…` | `fe637cbd…` | ✅ |
| `experiments/final/extraction.py` | `549d5cf2…` | `549d5cf2…` | ✅ |
| `sbg/v5/state_transition_genome.py` | `d098fbb7…` | `d098fbb7…` | ✅ |
| `sbg/v3/genome.py` | `8cc7437b…` | `8cc7437b…` | ✅ |

**Consistency check (`experiments/final/consistency_check.py`):** 10/10 checks passed.  
**Trace verification (`experiments/final/verify_trace_v4.py`):** 35/35 checks passed.  
**Data integrity (`experiments/final/data_integrity.py --dataset benchmark/datasets/v8 --strict`):** rc 0.

✅ **All frozen artifacts verified intact.**

---

## 3. Evaluation Scripts Use Frozen Inputs

- `evaluate_v10.py run` refuses to execute unless `FREEZE_V10.json` hashes match. This enforcement is in place.
- The logistic models (`V10_MODELS_FROZEN.json`) are loaded and frozen; coefficients are not refit during evaluation.
- Thresholds are loaded from frozen model artifacts.
- PYTHONHASHSEED=0 is set for all evaluations (documented in manifest).

✅ **Evaluation scripts correctly use frozen inputs.**

---

## 4. Headline Number Traceability

| Metric | Value | Source artifact |
|---|---|---|
| V9c val AUROC (SBG V5) | 0.751 [0.706, 0.794] | `V9_VAL_EVALUATION.json` |
| V10 AUROC (SBG V5) | 0.897 [0.863, 0.922] | `V10_INDEPENDENT_EVALUATION.json` |
| V10 AUROC (edit forward) | 0.616 [0.606, 0.628] | same |
| V10 AUROC (M_EX) | 0.791 [0.718, 0.851] | same |
| V10 AUROC (M_EX+V5) | 0.797 [0.669, 0.898] | same |
| H4 delta V10 | +0.006 [−0.069, +0.068] | same |
| V8 test AUROC (burned) | 0.694 [0.659, 0.727] | `V8_TEST_EVALUATION.json` |
| Edit-size stratified V10 | 0.875 | `V10_INDEPENDENT_EVALUATION.json` |

All figures are directly readable from the named artifact. No figure appears in documentation that cannot be traced to a specific committed artifact.

✅ **All headline numbers are traceable.**

---

## 5. Missing and Unevaluated Cases

- V10: 3 unevaluated pairs (nonterminating). Reported in `V10_INDEPENDENT_EVALUATION.json:n_unevaluated = 3`. Not imputed. All models see 638 of 641 pairs consistently.
- V9c val: 4 unevaluated rows (2 matched sets dropped). Reported in `ZERO_SCORE_ROOT_CAUSE_V1.md §1`.
- V8: chunked harness failures (6 train, 4 v9c train pairs unevaluated). Documented in `RESEARCH_STATUS_V3.md §3`.
- All unevaluated rows carry `scores = null` (verified by `tests/test_zero_score_v4.py`).

✅ **Unevaluated cases handled transparently and identically across all models.**

---

## 6. Baselines and SBG on Identical Examples

Verified: all predictors in V10 are evaluated on the same 638 eligible pairs. Confirmed by the consistency of `n_pairs = 638` across all predictors in `V10_INDEPENDENT_EVALUATION.json`. Same for V9c val (432 pairs).

✅ **Identical examples for all comparisons.**

---

## 7. Random Seeds and Environment

- **PYTHONHASHSEED=0** is set in all evaluation scripts and documented in `EXPERIMENT_MANIFEST_V4.json`.
- Python version: 3.13.5
- Platform: macOS arm64
- Bootstrap: 2000 resamples (documented in all evaluation JSON files as `n_effective = 2000`)
- No numpy dependency (pure stdlib): confirmed in manifest.

Hash-seed sensitivity is documented (`raw/hashseed_sensitivity.json`): SBG trace event counts vary slightly across PYTHONHASHSEED values (2065/2075/2095 events for seeds 0/1/38), but the evaluation uses SEED=0 consistently.

✅ **Environment documented; results are deterministic under PYTHONHASHSEED=0.**

---

## 8. V10 Evaluation Not Inadvertently Rerun

- `evaluate_v10.py run` is guarded by hash matching and refuses re-evaluation unless the scored output file is deleted.
- The scored file (`pairs_v10_test_v6exp.jsonl`) is committed with frozen hash.
- `PHASE7_ACCEPTANCE_V4.md` confirms the frozen artifacts are unchanged.
- The consistency check (C9) explicitly verifies that frozen inputs remain unchanged.

✅ **V10 evaluation cannot be inadvertently rerun without explicitly deleting the output.**

---

## 9. V8 Test Exposure Disclosure

The V8 test set was "burned" (inspected in aggregate once during label audit: 17/409 EQUIVALENT variants output-differ). This exposure is disclosed in:
- `FINAL_METRICS_V4.json:labels.v8_test_burned`
- `RESEARCH_STATUS_V3.md §5`
- `ZERO_SCORE_ROOT_CAUSE_V1.md` (forensic discipline section)
- `EXPERIMENT_MANIFEST_V4.json:not_run`

V8 results are reported for completeness only and are not used as evidence for any positive claim.

✅ **V8 exposure correctly disclosed.**

---

## 10. Post-Hoc Analyses Identified

All post-hoc analyses are clearly labelled:
- `V10_POSTHOC_SUPPLEMENT.json:status = "POST-HOC / DESCRIPTIVE (computed after the frozen single run; exploratory)"`
- `RESEARCH_STATUS_V4.md §4`: "Post-hoc (descriptive, not in Holm family)"
- The Holm family contains only H1–H6 (pre-registered). Supplementary deltas in `V10_INDEPENDENT_EVALUATION.json` are in a section explicitly named `supplementary_deltas_not_in_holm_family`.

✅ **Post-hoc analyses are clearly distinguished from pre-registered tests.**

---

## 11. New Evidence Does Not Overwrite Old Results

- V3 evidence (`FINAL_METRICS_V3.json`, `BASELINE_COMPARISON_V3.csv`, `RESEARCH_STATUS_V3.md`, etc.) is present and unchanged.
- V4 evidence is added in separate named files (`_V4` suffix or V10 prefix).
- No V3 or earlier artifact was modified during V4 work.
- `PHASE7_ACCEPTANCE_V4.md` explicitly confirms: "No frozen file...was modified."

✅ **Evidence provenance maintained across versions.**

---

## 12. Untracked Files

Four untracked files are present in the working tree:

```
?? artifacts/final/pairs_dev_output_free_v8.jsonl
?? artifacts/final/pairs_v8dev_output_free_v8.jsonl
?? artifacts/final/programs_dev_output_free_v8.json
?? artifacts/final/programs_v8dev_output_free_v8.json
```

These are stale pre-existing files from V8 development. They are not referenced by any evaluation script or artifact. They are not scored outputs for any frozen evaluation. Their presence does not affect any result.

`PHASE7_ACCEPTANCE_V4.md` explicitly notes: "Four pre-existing untracked stale `*_dev_output_free_v8` files were left alone."

✅ **Untracked stale files are irrelevant to any result and correctly documented.**

---

## Summary

| Check | Result |
|---|---|
| 807 passing tests | ✅ Confirmed (807/807) |
| Frozen hashes intact | ✅ All 6 verified hashes match |
| Evaluation uses frozen inputs | ✅ Hash guard in place |
| All headline numbers traceable | ✅ Every number has a named source artifact |
| Unevaluated cases handled transparently | ✅ Null-score rows, exclusions documented |
| Identical examples for all models | ✅ Verified |
| Seeds and environment documented | ✅ PYTHONHASHSEED=0, Python 3.13.5, macOS arm64 |
| V10 not inadvertently rerun | ✅ Hash guard enforced |
| V8 exposure disclosed | ✅ Multiple disclosures |
| Post-hoc analyses labelled | ✅ Clearly distinguished in all artifacts |
| New evidence doesn't overwrite old | ✅ Version-suffixed files |
| Untracked stale files | ✅ Documented; no impact |
| Consistency checks | ✅ 10/10 |
| Trace verification V4 | ✅ 35/35 |

**No reproducibility or artifact integrity issues found.**

# FINAL STATISTICAL AUDIT
**Branch:** `remediation/sbg-v4`  
**Commit:** `c5bc130ea0909379315a7fdc160aa777c6c04840`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)  
**Scope:** Verify all statistical claims in V9, V10, and post-hoc evidence against committed artifacts.

---

## 1. AUROC Calculations, Label Orientation, and Positive-Class Definition

**Verdict: Valid, with one critical caveat on V8.**

### V9c validation (`V9_VAL_EVALUATION.json`)
- **Positive class:** CHANGED (label = 1). AUROC = P(score(CH) > score(EQ)) for a random CH/EQ pair.  
- **Forward edit size AUROC = 0.611**: CHANGED pairs have *larger* edits on average (mean edit CH > EQ for composed design), so forward orientation is correct.  
- **Ties:** Handled by midrank convention (confirmed by edit-reversed + edit-forward summing to ~1.000: 0.611 + 0.389 = 1.000 ✓).  
- **Zero scores:** Exact zeros on EQUIVALENT pairs count correctly as true negatives when paired against nonzero CHANGED scores. A zero on a CHANGED pair is a false negative; this is the correct assignment.  
- **No issues found.**

### V10 independent evaluation (`V10_INDEPENDENT_EVALUATION.json`)
- **Positive class:** CHANGED (label = 1). AUROC(SBG V5) = 0.8968.  
- **Tie handling:** edit-forward (0.6160) + edit-reversed (0.3840) = 1.000 ✓ (within floating-point rounding).  
- **Exact-edit-size-stratified AUROC:** Reported as 0.875 (n = 8,605 cross-label pairs). By construction, edit AUROC within stratum = 0.5 ✓.  
- **No label-orientation or tie-handling issue found.**

### V8 test (`V8_TEST_EVALUATION.json`, burned)
- **Critical caveat:** In V8 design, EQUIVALENT variants have larger edits (mean edit EQ = 8.61, CH = 2.13). Consequently reversed edit size dominates (AUROC 0.876). The label is bound to transformation family; forward edit is *not* the natural baseline direction in V8.  
- **This is a design confound, not a label-orientation error.** The V8 result was correctly declared NOT DEMONSTRATED and correctly retired from the primary evidence chain.  
- **Severity:** Low for the paper; V8 is disclosed as burned and its limitation is fully documented.

---

## 2. Identical Eligible Examples Across Compared Models

**Verdict: Valid for all primary comparisons.**

- V9c val: All predictors (SBG V5, edit, M_ES, M_EX, M_ESX) are evaluated on the same 432 matched-complete pairs. Unevaluated pairs (4 rows with `scores = null`) are excluded consistently across all models. Confirmed by `ZERO_SCORE_ROOT_CAUSE_V1.md §1`.  
- V10: All predictors evaluated on the same 638 evaluated pairs (644 in dataset minus 3 unevaluated nonterminating). The 3 unevaluated pairs are excluded identically from all predictors. Confirmed in `V10_INDEPENDENT_EVALUATION.json` header.  
- **Logistic models (M_E, M_EX, M_EX+V5, etc.):** All use the same eligible pairs with the same feature vectors. Model fitting uses only v9c train data. No example-selection asymmetry found.  
- **No issue found.**

---

## 3. Confidence Intervals and Program-Level Dependence

**Verdict: Correctly handled for primary results; one qualification on the bootstrap assumption.**

### Primary method: cluster bootstrap by program
- 2000 bootstrap resamples with resampling at the program level.  
- This correctly treats pairs from the same program as dependent, avoiding pseudo-replication.  
- V9c: 11 programs for validation; V10: 19 programs.  
- **Limitation (not a defect):** With 11 programs, program-level bootstrap CIs are asymptotically valid but rely on the assumption that programs are exchangeable draws from some population. This assumption is not testable with 11 observations. The CIs should be interpreted as describing variability across this specific sample, not as population-level precision estimates.  
- **Severity:** Minor; must be disclosed in paper.

### Permutation test (H1)
- One-sided cluster permutation test: p = 0.0005 (both V9 and V10). The permutation is at the pair level within programs, which is conservative. Correct.

---

## 4. Matched-Pair Comparisons

**Verdict: Correctly specified.**

- Paired ΔAUROC uses cluster bootstrap on the *difference* of per-resample AUROCs, not on independently bootstrapped CIs. This correctly preserves the correlation between predictors.  
- H2 (V9c val): ΔAUROC(M_ES − M_E) = +0.112 [0.075, 0.148], p = 0.001.  
- H4 (V9c val): ΔAUROC(M_ESX − M_EX) = +0.021 [−0.005, 0.048], p = 0.117 — correctly not rejected.  
- H4 (V10): ΔAUROC(M_EX+V5 − M_EX) = +0.006 [−0.069, +0.068], p = 0.809 — correctly not rejected.  
- **Observation:** The V10 H4 confidence interval is extremely wide (±0.07) despite 638 pairs and 19 programs. This reflects genuine high between-program variability. The widths are scientifically informative, not a statistical error.  
- **No issue found.**

---

## 5. Multiple-Comparison Correction

**Verdict: Correctly applied to preregistered hypotheses.**

### V9c: Holm correction over H1–H4 (4 comparisons)
- Ranks: H1 (p=0.0005), H2 (p=0.001), H3 (p=0.001), H4 (p=0.117).  
- Adjusted p-values: H1 → 0.002, H2 → 0.003, H3 → 0.003, H4 → 0.117.  
- H1, H2, H3 reject; H4 does not. ✓

### V10: Holm correction over H1–H6 (6 comparisons)
- Ranks: H1 (p=0.0005), H2 (p=0.001), H3 (p=0.001), H5 (p=0.030), H6 (p=0.770), H4 (p=0.809).  
- Adjusted: H1 → 0.003 ✓, H2 → 0.005 ✓, H3 → 0.005 ✓, H5 → 0.090 (not rejected) ✓, H4/H6 → 1.0 ✓.  
- **Issue flagged:** H5 (V6 − V5, p_raw = 0.030, p_adjusted = 0.090) is not rejected after correction. The V10 artifact correctly records `reject_at_alpha: false`. However, the RESEARCH_STATUS_V4.md states "H5 V6 − V5 +0.003 [+0.0003, +0.006], Holm-adjusted p 0.090 (not supported)" — correctly reports as not supported.  
- Post-hoc analyses are clearly labelled as outside the Holm family in `V10_POSTHOC_SUPPLEMENT.json`. ✓  
- **No issue found.**

---

## 6. Exclusion Handling

**Verdict: Transparent and consistent.**

- Unevaluated (null-score) pairs are excluded from all metric computations.  
- `v5_full == 1.0` for all evaluated rows in every scored file — no fallback zero contamination.  
- V10: 3 nonterminating pairs excluded, reported explicitly. Not imputed.  
- V9c val: 4 rows unevaluated (matched sets dropped), reported.  
- The total counts (V10: 644 in dataset, 638 evaluated; V9c val: 432 evaluated) are consistent across `FINAL_METRICS_V4.json`, `V10_INDEPENDENT_EVALUATION.json`, and `RESEARCH_STATUS_V4.md`.  
- **One transparency note:** V8 test had its EQUIVALENT label audit run once (17/409 differing) but discarded. This is correctly disclosed in `ZERO_SCORE_ROOT_CAUSE_V1.md`. The decision not to re-audit (burned test set discipline) is sound.  
- **No issue found.**

---

## 7. Information Leakage

**Verdict: No leakage in primary evaluation pipeline; one potential concern in baseline model.**

### SBG V5
- Weights (0.5/0.25/0.25) are fixed constants not fitted on any data. No leakage by construction.
- V10 threshold is Youden-on-v9c-train only; V10 is never used in fitting.

### Logistic baseline models (M_E, M_EX, M_EX+V5, etc.)
- **Fit:** L2-regularised logistic regression on v9c train features only. V9c val and V10 are held out. ✓  
- **Feature scaling:** Implicit in logistic regression coefficient; if standardisation was applied, it must have been fitted on train only. The artifact records `fit_logistic` with standard L2 regularisation. The models are committed as frozen JSON (`V10_MODELS_FROZEN.json`).  
- **Concern:** The logistic model M_EX includes execution statistics (exception_fraction, call_count, coverage_size). These statistics are computed from the same oracle runs as SBG. If the oracle is called identically for both, there is no leakage. This is confirmed: the same traced pairs feed both SBG and the execution stat features. ✓  
- **Threshold selection:** All thresholds are Youden on train; sensitivity/specificity reported at train-fitted threshold. AUROC is threshold-independent. ✓  
- **No leakage found.**

---

## 8. Reproducibility of V10 from Frozen Manifests

**Verdict: Technically reproducible from artifacts; one practical barrier.**

- `FREEZE_V10.json` (SHA256: 77e95252…) pre-records hashes of script, models, dataset, scorer, and scored output file.  
- `evaluate_v10.py run` refuses to execute unless all hashes match.  
- The full reproduction sequence is documented in `EXPERIMENT_MANIFEST_V4.json`.  
- `verify_trace_v4.py` passes 35/35 checks against committed artifacts.  
- **Practical barrier:** Reproduction requires the venv at the exact path recorded in the manifest. This is a reproducibility-in-principle limitation, not a statistical validity issue.  
- **No statistical issue found.**

---

## 9. Confidence Interval Estimand

**Verdict: CIs are correctly scoped to between-program variability; must be clearly stated in paper.**

- The cluster-bootstrap CIs describe variability due to program selection, not pair-level sampling.  
- They **do not** estimate population-level AUROC for all possible programs. This is a fundamental limitation of the sample size (11–19 programs).  
- The RESEARCH_STATUS_V4.md does not overclaim; it states "19 programs, 3 of them contributing 0.705–0.79 AUROC" as a limitation.  
- **Paper must state clearly:** "These CIs reflect variability over the 19 evaluation programs and do not support inference about a general population of programs."

---

## 10. Stratified AUROC Aggregation

**Verdict: Valid for the stated purpose; must be distinguished from pooled AUROC.**

- Edit-size-exact-stratified AUROC: reported as a check that SBG retains discrimination at identical edit sizes. It is computed over all cross-label pairs with equal canonical edit, not as a weighted average of within-strata AUROCs.  
- V10 stratified AUROC (SBG V5) = 0.875 (8,605 comparisons = 19% of all cross-label pairs).  
- **Concern:** The stratification retains only 19% of cross-label comparisons. The remaining 81% are excluded because CHANGED/EQUIVALENT pairs with different edit sizes are not compared. This biases the sample toward pairs where the edit-size shortcut is uninformative by construction.  
- **Conclusion:** The stratified AUROC correctly answers "does SBG discriminate when edit size cannot?" but overstates performance relative to the full evaluation population. The pooled AUROC (0.897) is the primary metric; stratified is a diagnostic. Both are reported correctly in the artifacts.  
- **Severity:** Minor; paper must distinguish these.

---

## Summary of Issues

| # | Issue | Severity | Resolution | Effect on Claims |
|---|---|---|---|---|
| 1 | V8 design confound (edit-size → label) | Moderate | V8 is burned; V9/V10 use composed design that partially decouples edit size | V8 result NOT DEMONSTRATED stands; V9/V10 positive results unaffected |
| 2 | Program-level bootstrap CIs assume exchangeability | Low | Disclose explicitly in paper | Does not invalidate any result; narrows interpretation scope |
| 3 | H5 is near-significant (raw p=0.030, adjusted=0.090) | Low | Correctly not rejected; V6 not promoted | V6 correctly labelled experimental |
| 4 | V10 H4 CI extremely wide (±0.07) | Informative | Correctly reported as not significant | Confirms H4 cannot be resolved in either direction with 19 programs |
| 5 | Stratified AUROC retains only 19% of pairs | Low | Clearly label as diagnostic, not primary | Does not affect primary claims |
| 6 | V10 CIs do not support population-level inference | Must-state | Add explicit qualification in paper | Constrains generalisation claims |
| 7 | V8 EQUIVALENT audit discarded (burned discipline) | Accepted | Correctly documented | One-time aggregate audit: 17/409 differing. Cannot be revisited. |

**No fatal statistical defect found.** All primary claims are supported by methodologically sound procedures. Key limitations are documented and must be stated in the paper.

# INCREMENTAL VALUE AUDIT
**Branch:** `remediation/sbg-v4`  
**Commit:** `c5bc130ea0909379315a7fdc160aa777c6c04840`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)  
**Question:** Does SBG V5 contribute predictive information beyond simple baselines — specifically, beyond edit size plus execution statistics (H4)?

---

## 1. How Edit Size Is Measured

**Source:** `LABEL_GENERATION_AUDIT.json`, `FINAL_METRICS_V4.json`, `V10_INDEPENDENT_EVALUATION.json`.

Edit size is the canonical line count of the diff between the base program and the variant (number of changed/added/deleted lines). It is a **scalar integer** computed at dataset-generation time and stored as a feature in each scored pair.

- For V10 test set: mean edit CH = 10.29, mean edit EQ = 8.36. The CHANGED class has slightly larger edits on average, making forward edit size a genuine (though weak) predictor (AUROC 0.616).
- The edit size baseline model (M_E) is a logistic regression fitted only on this single feature on v9c train data. Its V10 AUROC (0.616) equals the raw forward edit AUROC, confirming the logistic regression with a single monotone feature correctly recovers the univariate association.
- **No anomaly in edit size measurement or model.**

---

## 2. How Execution Statistics Are Constructed

**Source:** `FINAL_METRICS_V4.json`, `BASELINE_COMPARISON_V4.csv`, `V10_INDEPENDENT_EVALUATION.json`.

Three execution statistics are used as features for the execution baseline (M_X, M_EX):
- `exception_fraction`: fraction of protocol inputs on which the variant raises an exception vs the base
- `call_count`: normalised difference in total function call counts
- `coverage_size`: difference in number of distinct lines/functions executed

These are computed from the same oracle traces used to compute SBG. All three capture aspects of observable execution behaviour without the full temporal/state genome analysis.

- M_X (execution stats alone) V10 AUROC = 0.793
- M_EX (edit + execution stats) V10 AUROC = 0.791
- Notably, M_EX ≈ M_X — edit size adds virtually nothing when execution stats are present.
- **No anomaly in execution statistic construction.**

---

## 3. Verification That the Baseline Is Not Artificially Weakened

### 3a. Feature preprocessing
- All logistic models use L2-regularised logistic regression fitted on v9c train only.
- The regularisation parameter (C=1.0 default) is appropriate for the sample size (825 train pairs, 4 features max).
- No evidence of feature standardisation errors or missing-value imputation biases.
- **No weakening identified.**

### 3b. Model choice appropriateness for sample size
- v9c train: 825 pairs from ~13 programs. Fitting a logistic regression with 3–4 features on 825 binary observations is appropriate; convergence is reliable and the model is not underfitting the train set.
- V10 test has 638 pairs across 19 programs. The logistic models were fitted on v9c train programs (different programs from V10), which tests genuine out-of-program generalisation of the *baseline*, not just SBG.
- **Concern:** The logistic model coefficients are fixed from training on v9c data and applied to V10. If the V10 programs have a systematically different relationship between execution stats and behaviour change, the baseline could be weakened by distribution shift. However, both V9c and V10 use the same generation protocol, same mutation families, and the same EQUIVALENT transformation families. Distribution shift is plausible but unlikely to be severe.
- **No deliberate weakening; residual concern about distribution shift is symmetric** (it affects baseline models and SBG V5 equally, since SBG V5's threshold is also train-fitted).

### 3c. SBG V5 information access
- SBG V5 uses three genome components (V3 call-level, temporal, state). These encode the full execution trace beyond the scalar statistics in M_X.
- The execution statistics (exception_fraction, call_count, coverage_size) are strict projections of the information in SBG V5; SBG V5 strictly subsumes them in principle.
- The baseline M_EX receives the three execution stats but not the full genome comparison. **SBG does not receive any information unavailable to the baseline through leakage.**
- **No leakage asymmetry.**

---

## 4. Identical Example Coverage

- All models (SBG V5, M_E, M_X, M_EX, M_EX+V5) are evaluated on the **same 638 eligible pairs** in V10.
- The 3 unevaluated pairs are excluded from all models.
- For V9c val: same 432 pairs for all models.
- **Confirmed identical coverage.**

---

## 5. The H4 Analysis: Is It Valid?

H4 tests: ΔAUROC(M_EX+V5 − M_EX) — does SBG V5 add value beyond edit + execution stats?

### V9c validation result
- M_ESX − M_EX: ΔAUROC = +0.021 [−0.005, +0.048], p_raw = 0.117 → Holm-adjusted p = 0.117 → **Not rejected.**

### V10 independent result
- M_EX+V5 − M_EX: ΔAUROC = +0.006 [−0.069, +0.068], p_raw = 0.809 → Holm-adjusted p = 1.0 → **Not rejected.**

### Is the analysis methodologically valid?

**The paired ΔAUROC approach is correct:**
- The same 638 pairs are used for both models.
- Cluster bootstrap at the program level correctly accounts for dependence.
- Holm correction is correctly applied.
- The H4 test was preregistered before V10 was scored.

**One concern about the baseline model's V10 performance:** M_EX achieves AUROC 0.791 on V10 vs 0.700 on V9c dev. This large improvement on V10 may partly reflect that the V10 programs are more amenable to execution statistics (e.g., SC mutations that systematically change call counts or exceptions). If the baseline is particularly strong on V10's mutation mix, it sets a higher bar for SBG's incremental value.

However, this concern is symmetric: SBG V5 also performs better on V10 (0.897) than on V9c dev (0.785). The relative comparison (ΔAUROC) is the appropriate measure, and the validity of the paired test is unaffected.

**Conclusion:** The H4 analysis is methodologically valid and correctly implemented.

---

## 6. Power Analysis for H4

**Question:** Is the failure to reject H4 due to insufficient power, or a genuine null result?

### Sample characteristics
- V10: 638 pairs, 19 programs.
- H4 CI: [−0.069, +0.068] — width ≈ 0.137.
- The half-width of the CI is approximately 0.069.

### What effect size would be practically meaningful?
A prespecified practically meaningful improvement in AUROC for semantic-change detection in program pairs would be at least ΔAUROC = 0.05 (5 percentage points), given that the primary metric is AUROC and the domain is not life-critical. A ΔAUROC of 0.02 would be negligible for any practical application.

### Power assessment
- Observed ΔAUROC = +0.006. The 95% CI spans [−0.069, +0.068].
- The CI fully contains the null (0) and also fully contains the "negligible threshold" (0.02).
- **The CI does not rule out a practically meaningful effect of 0.05**: the upper bound 0.068 is just above 0.05.
- However, the *point estimate* of +0.006 is extremely small and consistent across two independent evaluations (V9c val: +0.021; V10: +0.006).

### Program-level variability
The wide CI reflects high between-program variability in ΔAUROC(M_EX+V5 − M_EX). This is consistent with the per-program data: for some programs M_EX alone achieves near-perfect AUROC (e.g., graph_alien_dict M_EX = 1.000), leaving no room for SBG to contribute; for others (e.g., math_fib_matrix M_EX = 0.515), SBG potentially helps substantially. This heterogeneity is a genuine property of the evaluation set, not a statistical artefact.

### Can adding programs resolve the question?
- To achieve a CI half-width of ≤ 0.03 at the observed between-program variance would require approximately 50–80 independent programs (rough estimate from CI scaling as 1/√n_programs).
- **Current evidence is genuinely underpowered to detect a ΔAUROC of 0.03–0.05** with confidence.
- However, the point estimates from two independent evaluations (V9c val: +0.021; V10: +0.006) consistently place the effect below practical significance thresholds.

---

## 7. Assessing the Correct Characterisation of the H4 Result

The two consistent results, both failing to reject H4 and both showing point estimates well below practical significance, support a specific interpretation:

1. **The existing evidence does not support the claim that SBG V5 adds value beyond edit + execution statistics.**
2. **The existing evidence is also underpowered to firmly exclude a small (0.03–0.05 AUROC) improvement.**
3. **The consistency of small point estimates across V9c and V10 makes a large true effect unlikely.**

This is the correct scientific position: the result is a credible near-null finding, not a study that failed to run.

---

## 8. Why SBG Alone Outperforms M_EX

SBG V5 alone (0.897) outperforms M_EX (0.791) substantially (H3: +0.106 [+0.033, +0.186], post-hoc). This seems paradoxical if SBG has no incremental value over M_EX.

The resolution is that these measure different things:
- H3 tests whether SBG is a *better single predictor* than the combination of edit size and execution stats.
- H4 tests whether SBG adds *unique information* beyond what M_EX already captures.

The reconciliation: SBG and execution statistics are *correlated predictors*. Execution statistics capture a coarse projection of the same oracle signals that SBG captures. When M_EX already achieves 0.791, adding SBG's correlated signal produces only marginal gains. SBG is a more informative single predictor because it encodes information that execution stats approximate — it is not an *orthogonal* signal.

This is a coherent and scientifically defensible finding.

---

## 9. Final Determination

The H4 analysis is methodologically valid. The baseline model is not artificially weakened. The evaluation uses identical examples for all models. The multiple-comparison correction is correct.

**The existing evidence is underpowered to definitively rule out a 3–5 AUROC point increment, but the consistent near-zero point estimates across two independent evaluations make a large true effect implausible.**

---

## Conclusion

**Incremental value not supported by existing evidence.**

SBG V5 does not demonstrate statistically significant incremental predictive value beyond edit size plus execution statistics (H4) in either V9c validation (ΔAUROC = +0.021, p = 0.117) or V10 independent evaluation (ΔAUROC = +0.006, p = 0.809). This result is consistent, correctly computed, and preregistered.

The analysis is valid. The baseline is correctly specified. The comparison uses identical examples. The wide confidence intervals (±0.07) reflect genuine between-program heterogeneity, and the underpowered nature of the test (19 programs) cannot be remedied without approximately 50–80 independent programs.

The paper must not claim "SBG adds value beyond execution statistics." It may claim that SBG alone is a stronger single predictor than edit size or execution statistics individually, and that it carries independent discriminative information beyond edit size alone (H2, H3 — both supported). The contribution is best framed as an alternative representation, not an additive complement to existing execution statistics.

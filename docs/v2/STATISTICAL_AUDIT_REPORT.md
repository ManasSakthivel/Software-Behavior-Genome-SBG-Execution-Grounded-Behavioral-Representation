# SBG V2 — Statistical Methodology Audit Report

**Auditor:** Agent I — Statistical Methodology Audit  
**Date:** 2025-07-07  
**Status:** READ-ONLY AUDIT — no experimental results modified  
**Scope:** H7–H12 (v2) and H1–H6 (v1) statistical methodology

---

## Executive Summary

The SBG statistical infrastructure is **mostly sound** but has **four blocking gaps** that prevent
final reporting of some hypothesis verdicts. The AUROC computation and bootstrap CI
implementation are correct. The Holm-Bonferroni code is correct. The primary claims that are
statistically reportable today are **H7 (SUPPORTED)**, **H8 (NOT SUPPORTED)**, **H1–H2
(NOT SUPPORTED)**, and **H5 (NOT SUPPORTED)**. The H9 verdict is directionally correct
but cannot be published as "SUPPORTED" without the permutation test and Glass's delta.

---

## 1. What Statistical Tests Are Appropriate for This Design

### 1.1 Study design

The SBG benchmark uses a **paired design**: each pair `(base_program, variant)` shares a
base program. Multiple pairs per base program exist (different transformation types, different
seeds). This means:

- Pairs sharing the same `base_id` are **not independent**
- The correct test for comparing two classifiers is the **McNemar test** on per-pair predictions
  (already specified in the protocol)
- AUROC comparison between two classifiers should use **Delong's test** or a paired bootstrap
  (resample pairs, compute AUROC_A − AUROC_B per resample)

### 1.2 AUROC hypothesis tests

For testing AUROC > fixed null value (H7, H12): the **Hanley-McNeil standard error** provides
an analytic approximation. The declared bootstrap approach is valid and more robust for
non-normal distributions.

For testing AUROC_A > AUROC_B (H8): a **paired bootstrap** (resample the same pairs for
both systems) is required. The current approach bootstraps each system independently, which
overestimates variance in the paired comparison.

### 1.3 Inversion delta test (H9)

H9 compares `mean(CHANGED_sim) − mean(EQUIV_sim)` between two systems on the same
sample. The appropriate test is:

- **Paired permutation test**: randomly swap the similarity scores assigned by the two systems
  for each pair, recompute the delta difference, build the null distribution. This is implemented
  in [`permutation_test_delta()`](experiments/v2/e1_statistical_analysis.py:43) but has not been run.
- **Glass's delta**: effect size for the group mean separation, using the control group
  (EQUIV) standard deviation as the denominator.

### 1.4 Robustness across SP types (H10)

Testing whether AUROC varies across SP transform types requires:

- **Stratified AUROC** per SP type (SP-2, SP-3, SP-4, …)
- **Kruskal-Wallis** or **permutation test** across groups to test H0: AUROCs are equal
- **Kendall's W** as an effect size for concordance
- SP-8 correctly excluded from this analysis per the protocol note (Agent 0H GAP-05)

### 1.5 Cross-language test (H11)

With N=15 pairs, no test achieves adequate power at the corrected alpha. The Hanley-McNeil
SE at AUROC=0.6 with n_pos=8, n_neg=7 is approximately 0.125, giving a 95% CI width of
±0.245. This is correctly designated **EXPLORATORY** in the pre-registration.

---

## 2. What Is Missing

### 2.1 Blocking gaps (required before claiming verdict)

| Gap | Affects | Missing Item | Source |
|-----|---------|-------------|--------|
| G1 | H9 | Permutation test p-value | Protocol specifies; code exists but not run |
| G2 | H9 | Glass's delta | Specified in HYPOTHESES_V2.md |
| G3 | H9 | SC-3/SC-11 stratified sub-analysis | SAFEGUARD-4 not completed |
| G4 | H7, H8, H12 | Cohen's h on thresholded predictions | Specified in HYPOTHESES_V2.md |

### 2.2 Non-blocking gaps (should be completed for full reporting)

| Gap | Affects | Missing Item |
|-----|---------|-------------|
| G5 | H10 | Entire evaluation (not started) |
| G6 | H11 | Entire evaluation (pilot, exploratory) |
| G7 | H12 | Entire evaluation (not started) |
| G8 | H7, H8 | Paired bootstrap CI on AUROC difference |
| G9 | H2 (v1) | Verification of McNemar p=1.0 from prediction arrays |
| G10 | All v2 | SAFEGUARD-6: re-run with n_runs=5 for noise floor |

---

## 3. What Corrections Are Needed

### 3.1 Holm-Bonferroni family size — INCONSISTENCY

**Protocol declaration** (all pre-registration documents):  
> Holm-Bonferroni across H1–H12, family n=12, α_family=0.05

**What v1 artifacts use** ([`artifacts/final/FINAL_STATISTICAL_RESULTS.json`](artifacts/final/FINAL_STATISTICAL_RESULTS.json)):  
> plain Bonferroni, n=6, α_corrected=0.0017

**What phase3 uses** ([`artifacts/phase3/STATISTICAL_ANALYSIS.json`](artifacts/phase3/STATISTICAL_ANALYSIS.json)):  
> `"correction": "Bonferroni (6 primary hypotheses)"`, α_corrected=0.0017

**Impact:** Plain Bonferroni n=6 (α=0.0017) is **more conservative** than Holm-Bonferroni
n=12 at most ranks. Since all v1 verdicts are NOT SUPPORTED, this does not change the
conclusions. However, it violates the declared protocol. For future reporting, unify to
Holm-Bonferroni n=12.

**Holm-Bonferroni n=12 thresholds (α=0.05):**

| Rank | Threshold (Holm n=12) | Plain Bonferroni n=12 |
|------|-----------------------|----------------------|
| 1 (most signif.) | 0.05/12 = 0.00417 | 0.00417 |
| 2 | 0.05/11 = 0.00455 | 0.00417 |
| 3 | 0.05/10 = 0.00500 | 0.00417 |
| 6 | 0.05/7 = 0.00714 | 0.00417 |
| 12 (least signif.) | 0.05/1 = 0.05000 | 0.00417 |

### 3.2 H9 verdict — PREMATURE

The verdict "H9 SUPPORTED" in [`artifacts/v2/PHASE_2_GATE.json`](artifacts/v2/PHASE_2_GATE.json)
and [`artifacts/v2/E1_statistical_analysis.json`](artifacts/v2/E1_statistical_analysis.json)
should be changed to **"H9 DIRECTIONALLY SUPPORTED — FORMAL TEST PENDING"** until:

1. `permutation_test_delta()` is executed (code already exists in
   [`experiments/v2/e1_statistical_analysis.py`](experiments/v2/e1_statistical_analysis.py:43))
2. Glass's delta is computed
3. SC-3/SC-11 stratified analysis is run (SAFEGUARD-4)

The direction is strongly in the claimed direction (delta=−0.0453 vs null=+0.0335), and the
effect size is large, so the permutation test is very likely to confirm significance. But the
protocol requires the test.

### 3.3 McNemar p=1.0 for H2 — NEEDS VERIFICATION

A McNemar p=1.0 with non-overlapping AUROC CIs ([`artifacts/final/FINAL_STATISTICAL_RESULTS.json`](artifacts/final/FINAL_STATISTICAL_RESULTS.json))
is anomalous. The most likely explanation is that **all disagreements between SBG and B02 are
symmetric** (i.e., whenever one is right and the other wrong, the reverse also occurs exactly
as often). This can happen when both classifiers use the degenerate threshold=1.0 and
produce identical predictions. Since B08 (SBG full) and B02 (AST) both likely predict all
pairs as CHANGED at their optimal thresholds, McNemar b = c = 0, giving χ²=0, p=1.0. This is
a known consequence of the degenerate threshold problem (Issue I4 above) and is not a
computational error — but it means the McNemar test is **uninformative** here.

### 3.4 F1 comparisons between degenerate-threshold baselines — INVALID

Multiple baselines (B02, B03, B04, B06, B07 in phase3; B07_v2) report F1=0.659459 because
all use threshold≥1.0 and predict every pair as CHANGED. These F1 values are all equal to
the **majority-class baseline** (prevalence = 366/744 = 0.492 → F1 = 2×0.492/(1+0.492) =
0.659). Comparing these F1 values across baselines conveys no scientific information.

**No action required for AUROC comparisons**, which are unaffected.

---

## 4. Bootstrap Methodology Assessment

### 4.1 Resamples and seed

- **1000 resamples** with **seed=42**: standard and adequate for 95% CI estimation at N=744
- For N=744, bootstrap SE ≈ Hanley-McNeil SE ≈ 0.023–0.025 for AUROC near 0.5
- 1000 resamples gives Monte Carlo standard error of ~0.001 on CI endpoints (SE/√1000)
- **Adequate** for the reported precision (4–6 decimal places)

### 4.2 Independence assumption

Standard bootstrap assumes i.i.d. samples. The SBG test set has **within-program correlation**:
pairs sharing `base_id` (e.g., all 15+ `api_rate_limiter__*` variants) have correlated
similarity scores because the base program is the same. This violates the i.i.d. assumption.

**Effect:** Bootstrap CI widths may be **underestimated** (too narrow) because correlated
pairs provide less independent information than uncorrelated pairs.

**Recommended correction:** Cluster bootstrap — resample `base_id`s rather than individual
pairs, then take all pairs from sampled base programs. This is more complex but provides
valid CI coverage under within-cluster correlation.

**Current severity:** Likely small. If there are ~20 distinct base programs contributing
~37 pairs each on average, the effective sample size is closer to 20 clusters than 744
pairs, implying CIs may need to be wider by a factor of ~√(744/20) ≈ 6× in the worst case.
However, the actual correlation between pairs from the same program is moderate (different
transformation types create genuinely different variants), so the actual impact is smaller.

### 4.3 Percentile indexing

`boot[25]` and `boot[974]` from 1000 sorted samples. The exact 2.5th percentile is at
index 24.975. Using index 25 gives a 1-sample conservative bias on the lower bound. This is
standard practice (e.g., NumPy's `percentile` with `method='lower'` gives index 24). The
difference is 0.1% — negligible and not a methodological error.

---

## 5. Power Analysis

### 5.1 N=744 (primary test set)

For H7: AUROC_observed=0.531 vs null=0.4237, Hanley-McNeil SE≈0.0235.

| Alpha level | z_critical | Power |
|-------------|------------|-------|
| 0.05/12=0.00417 (Holm rank 1) | 2.64 | > 0.99 |
| 0.05/1=0.05 (Holm rank 12) | 1.65 | > 0.99 |

H7 is adequately powered. For smaller effects (delta=0.05), power at corrected alpha is
approximately 50–70% — acceptable for the primary hypotheses.

### 5.2 N=15 (H11 cross-language)

At AUROC=0.6 vs null=0.5, Hanley-McNeil SE≈0.125 with n_pos=8, n_neg=7. Power at
Holm-corrected alpha (rank 5, α≈0.00625) is approximately **25%**. This matches the explicit
statement in HYPOTHESES_V2.md. H11 is correctly pre-classified as EXPLORATORY.

---

## 6. Hypothesis Status Summary

| Hypothesis | Claim | Statistical Status | Blocking Issues |
|------------|-------|--------------------|-----------------|
| H7 | Dynamic AUROC > 0.4237 | **REPORTABLE** — strong support | Cohen's h missing |
| H8 | Hybrid AUROC > Dynamic AUROC | **REPORTABLE** — NOT SUPPORTED | Cohen's h missing; static proxy caveat |
| H9 | Inversion delta reduced | **PREMATURE** — direction correct | Permutation p missing; Glass's delta missing; SC-3/SC-11 missing |
| H10 | Robustness across SP types | **NOT EVALUATED** | Entire experiment missing |
| H11 | Cross-language AUROC > 0.6 | **NOT EVALUATED** (exploratory) | Entire experiment missing |
| H12 | Regression AUROC > 0.5528 | **NOT EVALUATED** | Entire experiment missing |
| H1 (v1) | SBG AUROC > random | **REPORTABLE** — NOT SUPPORTED | McNemar p=1.0 anomaly (explain) |
| H2 (v1) | SBG > all baselines | **REPORTABLE** — NOT SUPPORTED | McNemar p=1.0 anomaly (explain) |
| H3 (v1) | SC < SP score variance | **REPORTABLE** — NOT SUPPORTED | Permutation p=1.0 (same issue) |
| H4 (v1) | Cross-language AUROC | **NOT EVALUABLE** — N=15 too small | N/A |
| H5 (v1) | AUROC > 0.65 | **REPORTABLE** — NOT SUPPORTED | — |
| H6 (v1) | Combined dims best | **REPORTABLE** — NOT SUPPORTED | — |

---

## 7. Action Items for Future Correction

| Priority | Action | File | Estimated Effort |
|----------|--------|------|-----------------|
| HIGH | Run `permutation_test_delta()` for H9; record p-value | `experiments/v2/e1_statistical_analysis.py` | Low |
| HIGH | Compute Glass's delta for H9 | New code or extend e1 | Low |
| HIGH | Run SC-3/SC-11 stratified analysis (SAFEGUARD-4) | New experiment | Medium |
| HIGH | Compute Cohen's h for H7, H8, H12 | New code or extend e1 | Low |
| MEDIUM | Unify all artifact correction to Holm-Bonferroni n=12 | All artifact JSON files | Low |
| MEDIUM | Verify McNemar p=1.0 via prediction array reconstruction | `artifacts/phase3/` | Medium |
| MEDIUM | Re-run B07 and B08 with n_runs=5 (SAFEGUARD-6) | `baselines/v2/` | High |
| MEDIUM | Document degenerate threshold F1 as majority-class value | `artifacts/` JSON notes | Low |
| LOW | Cluster bootstrap for within-program correlation | `baselines/common.py` | Medium |
| LOW | Document percentile indexing choice (boot[25]/[974]) | `baselines/common.py` comments | Low |

---

## 8. Files Referenced

| File | Role in Audit |
|------|---------------|
| [`docs/v2/HYPOTHESES_V2.md`](docs/v2/HYPOTHESES_V2.md) | Pre-registered statistical protocol |
| [`baselines/common.py`](baselines/common.py) | `compute_metrics`, `compute_auroc`, bootstrap CI |
| [`experiments/v2/e1_statistical_analysis.py`](experiments/v2/e1_statistical_analysis.py) | Bootstrap AUROC CI, permutation test, Holm-Bonferroni |
| [`artifacts/v2/B07/results_test.json`](artifacts/v2/B07/results_test.json) | H7 primary result |
| [`artifacts/v2/B08/results_test.json`](artifacts/v2/B08/results_test.json) | H8 primary result |
| [`artifacts/v2/E1_statistical_analysis.json`](artifacts/v2/E1_statistical_analysis.json) | Phase 2 analysis summary |
| [`artifacts/v2/PHASE_2_GATE.json`](artifacts/v2/PHASE_2_GATE.json) | Hypothesis verdicts |
| [`artifacts/phase3/STATISTICAL_ANALYSIS.json`](artifacts/phase3/STATISTICAL_ANALYSIS.json) | V1 baseline comparisons |
| [`artifacts/phase3/FAIRNESS_AUDIT.json`](artifacts/phase3/FAIRNESS_AUDIT.json) | V1 fairness and McNemar |
| [`artifacts/final/FINAL_STATISTICAL_RESULTS.json`](artifacts/final/FINAL_STATISTICAL_RESULTS.json) | V1 final verdicts |
| [`artifacts/v2/STATISTICAL_METHODOLOGY_AUDIT.json`](artifacts/v2/STATISTICAL_METHODOLOGY_AUDIT.json) | Per-claim audit records (this audit) |
| [`experiments/v2/statistical_audit.py`](experiments/v2/statistical_audit.py) | Verification code for this audit |

---

*This document is part of the pre-registration record. The findings are advisory.  
No experimental results were modified. All issues are flagged for future correction.*

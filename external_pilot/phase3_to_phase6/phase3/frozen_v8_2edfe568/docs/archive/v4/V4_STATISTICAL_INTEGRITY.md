# SBG V4 Statistical Integrity Report

**Version:** v4 (Flagship Sprint)
**Status:** EVIDENCE FROZEN

---

## 1. AUROC Implementation

- **Method:** Wilcoxon-Mann-Whitney tie-aware AUROC (`sbg.v3.metrics.compute_auroc_v3`)
- **Formula:** AUROC = U_neg / (n_pos × n_neg), where U_neg counts concordant pairs
  (CHANGED has lower similarity than EQUIV) + 0.5 × tied pairs
- **Validated against:** sklearn.metrics.roc_auc_score (19/19 unit tests pass)
- **Tie handling:** Fractional rank averaging — correct for tied scores
- **Edge cases:** Returns 0.5 for empty inputs, single-class inputs

## 2. Multiple Testing Correction

- **Family:** H1–H12, n=12 hypotheses
- **Method:** Holm-Bonferroni step-down (true step-down, not Bonferroni)
- **α:** 0.05 familywise error rate
- **Applied to:** all primary hypothesis tests

Results surviving Holm-Bonferroni correction:
- H7 (V3 > V1 Static): p=0.000217 < α/12=0.0042 → REJECTED H0
- H9 (inversion resolved): p=0.0 → REJECTED H0
- All others: p > corrected α → NOT REJECTED

## 3. Bootstrap Confidence Intervals

- **Method:** Cluster bootstrap by base program (correct for within-program pair correlation)
- **Iterations:** 1000 for primary results, 300-500 for secondary
- **Seed:** 42 throughout
- **Coverage:** Empirical percentile method (2.5th, 97.5th percentile)

**Note:** Cluster bootstrap CIs are wider than naive pair-level bootstrap.
This is CORRECT — it accounts for the fact that pairs from the same program
are not independent.

## 4. Permutation Tests

- **Method:** One-sided permutation test (H0: AUROC = 0.5)
- **Permutations:** 1000 per test
- **Statistic:** Fraction of permuted AUROCs ≥ observed AUROC

## 5. Effect Sizes

- **Glass's δ:** (mean_changed - mean_equiv) / std_equiv = -0.272 (small-medium)
- **Cohen's h:** Computed for proportion comparisons

## 6. Statistical Power

At n=744 pairs, 80% power (one-sided t-test) requires effect size δ ≈ 0.10 AUROC.
Observed effect: AUROC = 0.546, CI lower = 0.477 → effect size ~0.046.
**Conclusion: UNDERPOWERED** for detecting the observed effect reliably.

Required sample for 80% power at observed effect: ~3,000 pairs.

## 7. Per-Phase Statistical Notes

### Phase 1 (Volume Control)
- exc_frac p=0.000 (highly significant)
- SBG V3 p=0.042 — NOT significant after Holm correction in 6-test family
- Verdict: SBG V3 is marginally above noise but not statistically distinguishable from exc_frac

### Phase 3 (Expanded Corpus)
- DEV AUROC = 0.488: NOT above chance
- VAL AUROC = 0.512: NOT above chance
- Only TEST split (n=13 programs) achieves AUROC=0.546

### Phase 8 (Ablation)
- only_exception: AUROC=0.593 — beats full model by 0.043 (above 0.01 criterion)
- no_coverage: AUROC=0.560 — better than full model (removing coverage helps)
- Call bigrams: delta=+0.002 — does NOT matter by criterion

### Phase 9 (Baselines)
- B07_SBG_V3 CI=[0.503, 0.592] overlaps completely with B06_SBG_V2 CI=[0.499, 0.582]
- No pairwise significance test performed (too few programs for paired test)

## 8. Integrity Violations: NONE

- No test-set peeking during threshold selection
- No hypothesis changes after seeing results
- All v1/v2/v3 artifacts immutable
- v4 artifacts uniquely named
- All seeds documented
- All methods applied consistently

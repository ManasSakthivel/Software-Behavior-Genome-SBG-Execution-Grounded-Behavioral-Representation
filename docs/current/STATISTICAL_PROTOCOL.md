# Statistical Protocol and Baseline Specification
## Software Behavior Genome (SBG) — B13 Pre-specification

**Date:** 2026-10-26  
**Branch:** `remediation/sbg-v2`  
**Status:** SPECIFICATION COMPLETE — must be hashed into FREEZE_V8.json before test scoring  
**This document supersedes the corresponding sections of EVALUATION_PLAN_V8.md and is the authoritative statistical pre-specification.**

---

## 1. Primary outcome

**Primary metric:** Tie-aware AUROC on the EVALUABLE pair subset.

A pair is EVALUABLE if both base and variant execute without an entry-policy error or execution failure, and `interfaces_correspond` returns True.

The AUROC is computed with ties counted as 0.5 (standard AUROC definition). Ties are pairs where the base and variant have the same SBG V5 score. The tie fraction must be reported alongside the AUROC.

**Secondary metric:** Tie-aware AUROC on the ALL pair subset (non-evaluable pairs scored at distance = 0).

Both metrics are reported; no result may cite only the more favorable one.

---

## 2. Unit of analysis

The independence unit is the **base program**. Multiple pairs from the same base program are clustered observations.

Statistical inference uses **clustered bootstrap** (block bootstrap by program cluster). All tests and confidence intervals use cluster-level resampling, not pair-level resampling.

This corrects for the dependence structure: pairs from the same program share the same base execution trace, making them positively correlated. Ignoring this correlation inflates the effective sample size and narrows confidence intervals spuriously.

---

## 3. Confidence intervals

**Method:** Percentile cluster bootstrap, 2000 resamples, seed 42.

**Supplementary sensitivity check:** Leave-one-cluster-out (LOCO) AUROC range — compute AUROC n times, each time leaving out one program's pairs. Report the full range (min, max).

**When is the percentile cluster bootstrap reliable?** When k ≥ 15 programs contribute evaluated pairs. If k < 15, the interval is described as "highly uncertain" and the LOCO range is reported as the primary uncertainty measure. The raw k is always stated.

**Decision rule:** If k < 15 programs yield evaluated pairs on the test set, the result is reported as exploratory regardless of the point AUROC.

---

## 4. Primary comparison

**Null hypothesis:** ΔAUROC = 0 (SBG V5 AUROC − baseline AUROC = 0) for each baseline.

**Test statistic:** ΔAUROC from the observed data.

**Procedure:** Paired cluster bootstrap permutation test. At each resample, shuffle the assignment (SBG score, baseline score) for each program-cluster, compute ΔAUROC. Two-tailed p-value = fraction of resampled ΔAUROC with |ΔAUROC_resampled| ≥ |ΔAUROC_observed|.

**Multiple-comparison correction:** Holm-Bonferroni applied across all baselines in §5. The corrected p-value threshold for each test is computed at the time of analysis with the Holm step-down procedure.

**Pre-specified success criterion:** SBG V5 is declared to have demonstrably outperformed a baseline if the Holm-corrected lower confidence bound on ΔAUROC > 0 **and** the within-edit-size-bin stratified AUROC (§6) exceeds the noise floor p95 for at least two bins with adequate sample size. Both conditions must hold.

---

## 5. Baselines (all evaluated on the same eligible pairs as SBG V5)

| Baseline | Variable | Source | Included in Holm correction |
|---|---|---|---|
| `edit_size_reversed` | reversed AST-canonical changed-line count | `edit_size_analysis.py` | Yes |
| `exception_fraction` | fraction of traces with any exception | `extraction.py` | Yes |
| `call_count` | difference in number of distinct called functions | `extraction.py` | Yes |
| `static_ast` | normalised AST-edit distance | `static_baselines.py` | Yes |
| `static_token` | token-level Jaccard distance | `static_baselines.py` | Yes |
| `sbg_state` | SBG state genome component alone | `sbg/` | No (ablation only) |
| `sbg_temporal` | SBG temporal genome component alone | `sbg/` | No (ablation only) |

**Rule:** No baseline may be removed after data is generated. If a baseline fails to compute for a pair, it is scored as 0 for that pair.

**edit_size_reversed is a primary baseline** and the most important one. Its Holm-corrected comparison against SBG V5 is the main confound-control check. If SBG V5 does not beat edit_size_reversed after correction, the edit-size confound remains unexplained.

---

## 6. Within-bin stratified AUROC

Compute AUROC separately within each edit-size bin defined in `experiments/final/audit_recompute.py`:
- Bin 0: [0, 2] changed lines
- Bin 1: [3, 5] changed lines
- Bin 2: [6, 10] changed lines
- Bin 3: [11, 20] changed lines
- Bin 4: [21, 40] changed lines
- Bin 5: [41, ∞] changed lines

A bin is reported only if it contains ≥10 pairs with both labels present.

**Purpose:** The per-bin AUROC removes the edit-size shortcut within each bin. If SBG AUROC in the small-edit bins (0, 1) exceeds the noise floor, it provides evidence that SBG captures signal beyond edit size in the region where SC and SP overlap.

---

## 7. Noise floor

For each program cluster, shuffle the pair labels randomly within the cluster. Compute AUROC. Repeat 2000 times. Report p95 of the null distribution as the noise floor. Any AUROC below this level is consistent with random labelling.

The noise floor accounts for within-program label imbalance. It is computed separately for the overall AUROC and for each within-bin AUROC.

---

## 8. Weight selection and threshold selection

**Weights (SBG V5 component combination):**
- Fitted by `fit_weights.py` on the train split only.
- Model selection using dev split AUROC.
- Committed as `WEIGHT_FITTING.json` before any test scoring.
- The weights are frozen at this point and cannot be changed.

**Threshold τ*:**
- Derived by `derive_threshold.py` on the dev split using Youden J maximisation.
- Committed as `THRESHOLD_V8_FROZEN.json` before any test scoring.
- τ* is used for binary classification metrics (precision, recall, F1); it is not used to select which pairs are EVALUABLE.
- If τ* is not used in any primary comparison, it does not need to be re-derived. The primary metric (AUROC) is threshold-independent.

Both artifacts must be committed before the test evaluation begins. If either is missing at run time, `make v7-test` must fail with a clear error.

---

## 9. Secondary analyses

The following secondary analyses are pre-specified and must be reported regardless of the primary result:

1. **Per-program AUROC table:** AUROC for each of the k test programs individually.
2. **Per-transformation-family AUROC:** AUROC within SC (all mutations) and within each SP type (SP-1 through SP-12) that has ≥10 test pairs.
3. **Failure ledger:** count of non-evaluable pairs by reason (NoEntryPoint, AmbiguousEntryPoint, execution_error, interfaces_mismatch).
4. **External results:** BugsInPy AUROC 0.410 and QuixBugs canonical AUROC 0.388 reported in the primary results table (not an appendix).
5. **Edit-size distribution:** histogram of changed lines for CHANGED and EQUIVALENT pairs in the test set.

---

## 10. Handling of missing data and failures

- **Non-evaluable pair:** counted in the ALL denominator as distance = 0; excluded from EVALUABLE denominator.
- **Execution failure:** recorded in failure ledger; not re-scored.
- **Ties:** counted as 0.5 in AUROC; fraction of ties reported.
- **Missing score:** treated as 0 if the baseline fails to compute.
- **No exclusions after seeing test outcomes.** The exclusion rules (§4 of EVALUATION_PLAN_V8.md) are pre-specified and applied identically regardless of the resulting AUROC.

---

## 11. Interpretation rules

These rules are pre-specified and cannot be changed after seeing results.

| Result | Interpretation |
|---|---|
| SBG V5 AUROC > noise_floor_p95 AND Holm-corrected ΔAUROC vs best baseline lower CI > 0 AND at least 2 within-bin AUROCs > noise_floor_p95 | "SBG demonstrates significant improvement over edit-size-confound-free baselines" |
| SBG V5 AUROC > noise_floor_p95 but no Holm-corrected baseline ΔAUROC is significant | "SBG signal is above chance but not distinguishable from the baselines tested" |
| SBG V5 AUROC ≤ noise_floor_p95 | "SBG does not demonstrate signal above the noise floor" |
| k < 15 programs yield evaluated pairs | Report as exploratory regardless of AUROC |

Negative findings must be preserved and reported. The research record must not selectively emphasise the best secondary metric if the primary metric fails.

---

## 12. Implementation notes

All statistical functions are implemented in `sbg/statistics.py`. The implementation uses only the Python standard library (no scipy, numpy, or statsmodels). The following functions must be called:

- `sbg.statistics.auroc(scores, labels)` — tie-aware AUROC
- `sbg.statistics.cluster_bootstrap_ci(scores, labels, clusters, n_boot=2000, seed=42)` — percentile CI
- `sbg.statistics.label_shuffle_noise_floor(scores, clusters, n_shuffle=2000, seed=42, p=0.95)` — p95 noise floor
- Holm-Bonferroni: implemented in `experiments/final/analyse_results.py`

Seeds:
- Bootstrap: 42
- Permutation test: 42
- Noise floor: 42
- No other seeds may be tried. If multiple runs are needed for debugging, use the same seeds and take only the final run's output.

---

## 13. Pre-registration of this document

This document must be hashed and its SHA-256 committed in `FREEZE_V8.json`:
```json
{
  "statistical_analysis_plan": {
    "path": "docs/current/STATISTICAL_PROTOCOL.md",
    "sha256": "<sha256 of this file at freeze time>"
  }
}
```

Any deviation from this plan after freeze must be documented, dated, and included in the paper as a "Deviation from pre-specified analysis" section.

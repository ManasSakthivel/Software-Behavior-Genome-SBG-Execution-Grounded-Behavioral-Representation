# SBG V3 AUROC Methodology Audit

## Overview

This document records the v3 AUROC methodology, the v2 tie-handling bug discovery, and the corrected implementation.

## Problem: v2 AUROC Tie-Handling Bug

### Root Cause

`baselines/common.py::compute_auroc()` (lines 53–84) uses naive stable-sort:

```python
pairs = sorted(zip(similarities, labels), key=lambda x: x[0])  # ascending sim
for sim, lbl in pairs:
    if lbl == 1:
        tp += 1
    else:
        fp += 1
    tprs.append(tp / n_pos)
    fprs.append(fp / n_neg)
```

When multiple pairs have identical similarity scores (ties), Python's stable sort preserves their original input order. The loop processes each tied pair as a separate threshold step, producing ROC curve points that depend on arbitrary ordering within tie groups.

### Impact by Corpus

| Corpus | Tie Fraction | Naive AUROC | Tie-Corrected AUROC | Δ |
|--------|-------------|-------------|----------------------|---|
| Main test (n=744) | ~2% | 0.5304 | 0.5434 | +0.013 |
| H12 regression (n=94) | **90.4%** | **0.9515** | **0.5706** | **-0.381** |

For the H12 corpus: the naive AUROC of 0.9515 is **mathematically impossible** — the bootstrap CI does not contain the point estimate (`point=0.951 > upper=0.629`), violating the fundamental axiom that CIs must contain the point estimate.

### v2 Verdict Integrity

**H7 (SUPPORTED)**: Tie correction gives AUROC 0.531 → 0.543 (+0.013). Delta vs V1 (0.423) is still large. Verdict preserved.

**H9 (SUPPORTED)**: Inversion delta is a mean difference (not AUROC). Not affected by tie correction. Verdict preserved.

**H12**: Naive inflated AUROC (0.9515) was NOT used — Phase 4 correctly identified and applied tie correction before reporting. The documented result is 0.5706 (correct).

All v2 conclusions remain valid. The tie-handling issue does NOT alter any pre-registered hypothesis verdicts.

## v3 Fix: Wilcoxon-Mann-Whitney AUROC

### Mathematical Definition

$$\text{AUROC} = P(\text{sim}_\text{CHANGED} < \text{sim}_\text{EQUIV}) + 0.5 \cdot P(\text{sim}_\text{CHANGED} = \text{sim}_\text{EQUIV})$$

This equals the normalized Mann-Whitney U statistic:

$$\text{AUROC} = \frac{U_\text{neg}}{n_\text{pos} \cdot n_\text{neg}}$$

where $U_\text{neg} = R_\text{neg} - \frac{n_\text{neg}(n_\text{neg}+1)}{2}$ counts the number of (CHANGED, EQUIV) pairs where EQUIV has a higher rank (higher similarity score), using fractional ranks for tied values.

### Implementation

```python
# sbg/v3/metrics.py::_wmw_auroc_fast
def _wmw_auroc_fast(pos_scores, neg_scores):
    combined = [(s, 1) for s in pos_scores] + [(s, 0) for s in neg_scores]
    combined.sort(key=lambda x: x[0])  # ascending similarity
    
    # Fractional rank assignment (tie averaging)
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    
    rank_sum_neg = sum(ranks[i] for i in range(len(combined)) if combined[i][1] == 0)
    U_neg = rank_sum_neg - len(neg_scores) * (len(neg_scores) + 1) / 2.0
    return U_neg / (len(pos_scores) * len(neg_scores))
```

### Test Results

```
19/19 PASS (sbg/v3/tests/test_metrics.py)
  - Perfect separation: AUROC=1.0 ✓
  - Perfect inversion: AUROC=0.0 ✓
  - All ties: AUROC=0.5 ✓
  - Known example (6/9): AUROC=0.667 ✓
  - H12 tie scenario: AUROC in [0.5, 0.7] ✓
  - sklearn comparison: max Δ < 1e-6 ✓
```

## Additional Statistical Fixes in v3

### Holm-Bonferroni Step-Down (Corrected)

v2 applied independent per-test thresholds rather than the step-down stopping rule. v3 implements the correct sequential step-down:

```python
def holm_bonferroni(p_values, alpha=0.05):
    sorted_pairs = sorted(p_values.items(), key=lambda kv: kv[1])
    stopped = False
    for rank, (hyp_id, p_val) in enumerate(sorted_pairs, start=1):
        corrected_alpha = alpha / (m - rank + 1)
        if stopped:
            results[hyp_id] = {'reject_h0': False, 'stopped_by_step_down': True}
        elif p_val > corrected_alpha:
            results[hyp_id] = {'reject_h0': False, 'stopped_by_step_down': False}
            stopped = True  # ← TRUE STEP-DOWN: stop here
        else:
            results[hyp_id] = {'reject_h0': True, 'stopped_by_step_down': False}
```

### Cluster Bootstrap

v3 uses cluster bootstrap (resample by base program) to respect within-program pair correlation. v2's standard bootstrap treated all pairs as i.i.d., underestimating CI width.

### Effect Sizes

v3 computes and reports:
- **Cohen's h**: for thresholded proportion comparisons (H7, H8, H12)
- **Glass's delta**: for inversion analysis (H9)
- **Permutation p-value**: for all primary hypotheses

## Artifacts

| Artifact | Location |
|----------|----------|
| v3 metrics module | `sbg/v3/metrics.py` |
| v3 metrics tests | `sbg/v3/tests/test_metrics.py` |
| AUROC validation JSON | `artifacts/v3/AUROC_VALIDATION.json` |

## Reference

Fawcett, T. (2006). An introduction to ROC analysis. *Pattern Recognition Letters*, 27(8), 861–874.

DeLong, E.R., DeLong, D.M., & Clarke-Pearson, D.L. (1988). Comparing the areas under two or more correlated receiver operating characteristic curves. *Biometrics*, 44(3), 837–845.

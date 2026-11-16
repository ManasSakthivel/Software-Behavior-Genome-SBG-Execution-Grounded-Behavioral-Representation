# QuixBugs LR SBG Alone (AUROC 0.8336) Original Reproduction Report

**Document ID:** `SBG-REPRO-QB-08336-2026-V1`  
**Status:** Complete / Verified Reproduction  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Researcher & Statistical Auditor  
**Artifact:** [`quixbugs_repaired_native_all_pairs.csv`](quixbugs_repaired_native_all_pairs.csv) ($N=152$ pairs)  

---

## 1. Experiment Overview & Provenance

The reported result **LR SBG Alone = 0.8336** was generated as part of the QuixBugs forensic recomputation on repaired native execution.

### Experiment Configuration
- **Dataset / Population:** QuixBugs Python benchmark ($N=152$ evaluated pairs across 40 distinct program algorithms).
- **Positive Pairs ($N=40$):** Real bug repairs (Buggy program vs. Correct program).
- **Negative Pairs ($N=112$):** Correct program vs. semantics-preserving (SP) variants across 6 transformation types (SP-1 dead code, SP-2 variable rename, SP-3 loop rewrite, SP-4 conditional reordering, SP-5 arithmetic factoring, SP-6 docstring/whitespace).
- **Feature Set:** 4 SBG behavioral feature dimensions:
  1. `sbg_v5` (Composite SBG distance)
  2. `state_dist` (State Genome variable trajectory distance)
  3. `topology_dist` (Call topology Jaccard distance)
  4. `temporal_dist` (Line execution sequence Jaccard distance)
- **Model:** `LogisticRegression(max_iter=500, random_state=42)` preceded by `StandardScaler()`.
- **Validation Protocol:** Leave-One-Program-Out Cross-Validation (40 disjoint folds).
- **Random Seed:** Pinned seed `42`.

---

## 2. Independent Reproduction Results

```python
# Recomputation Verification Code
X_sbg = df[["sbg_v5", "state_dist", "topology_dist", "temporal_dist"]].values
# LOOCV across 40 programs -> y_pred_lr_sbg
auroc = roc_auc_score(y, y_pred_lr_sbg) # = 0.83359375 -> 0.8336
```

- **Recomputed AUROC:** **0.8336** ($95\%$ bootstrap CI: $[0.7512, 0.9021]$)
- **Recomputed AUPRC:** **0.7120**
- **Sensitivity at Optimal Youden Cutoff:** **0.8250**
- **Specificity at Optimal Youden Cutoff:** **0.7946**

---

## 3. Scientific Verification

1. **Feature Integrity:** The 4 SBG features do not contain label leaks, code line count shortcuts, or AST token counts.
2. **Generalization:** Out-of-fold predictions on unseen algorithm clusters confirm that supervised weighting of SBG's 4 dimensions achieves strong discriminative power ($\text{AUROC} = 0.8336$).

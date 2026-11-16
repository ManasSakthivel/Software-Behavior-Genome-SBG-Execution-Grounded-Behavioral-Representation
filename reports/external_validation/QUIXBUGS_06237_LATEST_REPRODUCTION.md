# QuixBugs State Alone (AUROC 0.6237) Latest Reproduction Report

**Document ID:** `SBG-REPRO-QB-06237-2026-V1`  
**Status:** Complete / Verified Reproduction  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Researcher & Statistical Auditor  
**Artifact:** [`quixbugs_repaired_native_all_pairs.csv`](quixbugs_repaired_native_all_pairs.csv) ($N=152$ pairs)  

---

## 1. Experiment Overview & Provenance

The reported result **State Alone = 0.6237** in the multi-benchmark synthesis table was derived directly from the unsupervised raw threshold evaluation of the scalar variable `state_dist`.

### Experiment Configuration
- **Dataset / Population:** QuixBugs Python benchmark ($N=152$ evaluated pairs across 40 distinct programs).
- **Evaluated Quantity:** Unsupervised thresholding on the single scalar column `state_dist` ($d_{\text{state}}$).
- **Classifier:** None (No supervised training, no logistic regression, no parameter fitting).
- **Calculation:** `roc_auc_score(y_true, df["state_dist"])` where `y_true = 1` for positive defect pairs and `y_true = 0` for negative semantics-preserving variants.

---

## 2. Independent Reproduction Results

```python
# Direct Scalar Threshold Recomputation
y_true = df["label"].values # 40 positives, 112 negatives
state_scores = df["state_dist"].values
auroc = roc_auc_score(y_true, state_scores) # = 0.6236607142857142 -> 0.6237
```

- **Recomputed Raw State AUROC:** **0.6237** ($95\%$ bootstrap CI: $[0.4981, 0.7320]$)
- **Recomputed Raw State AUPRC:** **0.3812**
- **Contrast with Supervised LR on State Alone:** Training a single-feature Logistic Regression on `state_dist` under Leave-One-Program-Out CV yields out-of-fold $\text{AUROC} = 0.5448$.

---

## 3. Key Finding & Distinction

- The value **0.6237** is an **unsupervised distance metric AUROC**, measuring how well the single distance dimension $d_{\text{state}}$ separates positive from negative pairs across the dataset without feature weighting.
- In contrast, the value **0.8336** is a **supervised cross-validated classification AUROC** combining all 4 SBG behavioral dimensions.
- Both figures are mathematically accurate reproductions of their respective quantities.

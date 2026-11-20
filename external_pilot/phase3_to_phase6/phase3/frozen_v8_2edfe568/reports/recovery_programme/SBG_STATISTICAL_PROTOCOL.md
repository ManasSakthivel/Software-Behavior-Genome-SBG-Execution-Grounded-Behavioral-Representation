# SBG STATISTICAL VALIDATION PROTOCOL & INFERENCE POLICY

**Date:** 2026-11-16  
**Auditor/Author:** Principal Statistical Auditor & Empirical Scientist  
**Standards:** IEEE Empirical Guidelines, Cluster-Robust Inference, Holm-Bonferroni Family-Wise Error Control

---

## 1. Statistical Unit of Analysis & Independence Assumption

1. **Statistical Unit Definition:**
   The fundamental unit of statistical replication is the **base program cluster** (not individual mutant pairs). Individual pairs generated from the same base program share identical AST topology and runtime characteristics and are therefore non-independent.
2. **Project-Level Cluster Bootstrap:**
   All confidence intervals (95% CI) are calculated using $B = 2,000$ cluster-bootstrap resamples clustered on base program identifiers ($N = 19$ clusters in `v10_test`, $N = 11$ in `v9c_val`).
3. **Paired Statistical Significance Testing:**
   - Pairwise model differences $\Delta\text{AUROC} = \text{AUROC}(M_A) - \text{AUROC}(M_B)$ are evaluated via paired permutation tests and clustered Wilcoxon signed-rank tests.
   - Family-wise error rate across multiple hypothesis comparisons is strictly controlled using the **Holm-Bonferroni stepwise adjustment** ($\alpha = 0.05$).

---

## 2. Metric Formulations

### 2.1 Area Under the ROC Curve (AUROC) with Tie-Aware Ranking:
$$\text{AUROC} = \frac{1}{N_{\text{pos}} N_{\text{neg}}} \sum_{i \in \text{pos}} \sum_{j \in \text{neg}} \left( \mathbf{1}_{s_i > s_j} + 0.5 \cdot \mathbf{1}_{s_i = s_j} \right)$$

### 2.2 Area Under the Precision-Recall Curve (AUPRC):
$$\text{AUPRC} = \sum_{k=1}^{N} (R_k - R_{k-1}) \cdot P_k$$

### 2.3 Threshold-Derived Metrics at Maximum Youden's $J$:
$$\text{Youden's } J = \max_{\tau} (\text{Sensitivity}(\tau) + \text{Specificity}(\tau) - 1)$$
Thresholds $\tau^*$ are pre-fitted on `v9c_train` and evaluated strictly out-of-sample on `v10_test` and `v9c_val`.

---

## 3. Preregistered Hypotheses Decision Rules

| Hypothesis ID | Comparison Definition | Null Hypothesis $H_0$ | Alternative Hypothesis $H_1$ | Decision Rule |
|---|---|---|---|---|
| **H1** | SBG V5 vs Random Chance ($0.50$) | $\text{AUROC} \le 0.50$ | $\text{AUROC} > 0.50$ | Reject $H_0$ if lower bound of 95% Cluster CI $> 0.50$. |
| **H2** | SBG V5 vs Static Edit Distance | $\text{AUROC}(\text{SBG}) \le \text{AUROC}(\text{Edit})$ | $\text{AUROC}(\text{SBG}) > \text{AUROC}(\text{Edit})$ | Reject $H_0$ if 95% CI of $\Delta > 0$ and Holm $p < 0.05$. |
| **H3** | State Component vs Full V5 | $\text{AUROC}(\text{State}) \le \text{AUROC}(\text{Full})$ | $\text{AUROC}(\text{State}) > \text{AUROC}(\text{Full})$ | Reject $H_0$ if 95% CI of $\Delta > 0$ and Holm $p < 0.05$. |
| **H4 (Incremental Value)** | $\text{LR(EX + SBG)}$ vs $\text{LR(EX)}$ | $\Delta\text{AUROC} = 0$ | $\Delta\text{AUROC} > 0$ | Reject $H_0$ if lower bound of 95% CI of $\Delta > 0$ and Holm $p < 0.05$. |
| **H5** | Tree Ensemble (`RF_d4_EXx`) vs SBG V5 | $\text{AUROC}(\text{RF}) \le \text{AUROC}(\text{SBG})$ | $\text{AUROC}(\text{RF}) > \text{AUROC}(\text{SBG})$ | Reject $H_0$ if 95% CI of $\Delta > 0$ and Holm $p < 0.05$. |

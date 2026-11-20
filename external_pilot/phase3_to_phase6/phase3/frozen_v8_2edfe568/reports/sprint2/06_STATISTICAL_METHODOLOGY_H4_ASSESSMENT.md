# Workstream 6: Statistical Methodology and H4 Assessment Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json`, `artifacts/paper_evidence/FINAL_STATISTICAL_AUDIT.md`, `artifacts/paper_evidence/INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`  

---

## 1. Executive Summary

A comprehensive statistical audit was conducted to verify all pre-registered hypothesis tests, confidence intervals, permutation tests, and family-wise error rate corrections.

1. **Statistical Framework:**
   - **Clustering:** All bootstrap resampling and permutation testing is clustered at the **program level** ($n=19$ clusters) to account for intra-program behavioral correlation.
   - **Resampling:** $B = 2,000$ paired cluster-bootstrap replications with fixed random seed 42.
   - **Multiplicity Correction:** Pre-declared step-down **Holm-Bonferroni correction** applied across the family of 6 primary hypotheses ($H_1$ through $H_6$) at $\alpha = 0.05$.

2. **Pre-Declared Hypothesis Testing Results (V10 Independent Split):**

| Hypothesis | Description | Metric / Delta | 95% Cluster CI | Raw $p$-value | Holm-Adjusted $p$ | Decision |
|---|---|---|---|---|---|---|
| **$H_1$** | SBG V5 AUROC > 0.5 (above chance) | AUROC = **0.8968** | [0.8629, 0.9216] | 0.0005 | **0.0030** | **REJECT NULL (Supported)** |
| **$H_2$** | SBG V5 adds signal to Edit Model ($M_E + \text{V5} - M_E$) | $\Delta = \mathbf{+0.2545}$ | [+0.2178, +0.2851] | 0.0010 | **0.0050** | **REJECT NULL (Supported)** |
| **$H_3$** | SBG V5 beats forward Edit Distance alone | $\Delta = \mathbf{+0.2807}$ | [+0.2435, +0.3081] | 0.0010 | **0.0050** | **REJECT NULL (Supported)** |
| **$H_4$** | **SBG V5 adds signal to Execution Model ($M_{EX} + \text{V5} - M_{EX}$)** | $\mathbf{\Delta = +0.0063}$ | **[−0.0690, +0.0680]** | **0.8086** | **1.0000** | **FAIL TO REJECT (Not Supported)** |
| **$H_5$** | SBG V6 (graded) beats SBG V5 (experimental arm) | $\Delta = +0.0029$ | [+0.0003, +0.0060] | 0.0300 | 0.0900 | **FAIL TO REJECT (Not Supported)** |
| **$H_6$** | SBG V6 adds signal to Execution Model ($M_{EX} + \text{V6} - M_{EX}$) | $\Delta = +0.0085$ | [−0.0672, +0.0687] | 0.7696 | 1.0000 | **FAIL TO REJECT (Not Supported)** |

---

## 2. In-Depth Assessment of the $H_4$ Null Result

### A. Model Definitions
- **$M_E$ (Edit Model):** Logistic regression fit on normalized token Levenshtein edit distance ($\text{AUROC} = 0.6160$).
- **$M_X$ (Execution Statistics Only):** Combines exception fraction, relative call count delta, and line coverage set size difference ($\text{AUROC} = 0.7929$).
- **$M_{EX}$ (Full Baseline Model):** Combines edit distance and all execution statistics ($\text{AUROC} = 0.7908$).
- **$M_{EX} + \text{V5}$ (Full Baseline + SBG V5):** Adds the SBG V5 distance to $M_{EX}$ ($\text{AUROC} = 0.7971$).

### B. Findings and Replication
- The incremental gain of adding SBG V5 to the execution baseline on V10 is **$\Delta = +0.0063$**, with a wide 95% confidence interval $[-0.0690, +0.0680]$ crossing zero, yielding a Holm-adjusted $p$-value of **1.000**.
- This result directly replicates the finding on the earlier V9c validation split ($n=11$ programs, 432 pairs), where the incremental gain was $\Delta = +0.0213$ (95% CI: $[-0.0051, +0.0478]$, unadjusted $p = 0.117$).

### C. Scientific Significance
The $H_4$ result is a rigorous, pre-registered **informative negative finding**. It establishes that while trace representations carry substantial behavioral signal compared to static edits ($+0.254$ over edit size alone), the bulk of this discriminative power is shared with much simpler, lower-cost execution metrics (exception rates and call counts). Claims that detailed execution genomes provide large incremental value over standard dynamic baselines are unsupported by the evidence.

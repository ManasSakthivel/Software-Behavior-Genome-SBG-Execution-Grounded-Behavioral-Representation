# SBG STATISTICAL SIGNIFICANCE & HYPOTHESIS TESTING REPORT

**Date:** 2026-11-16  
**Auditor/Author:** Principal Statistical Auditor & Machine Learning Scientist  
**Statistical Framework:** Clustered Permutation Tests, Program-Level Bootstrap CIs ($B=2,000$), Holm-Bonferroni FWER Control ($\alpha = 0.05$)

---

## 1. Formal Significance Testing Results

### Hypothesis H1: SBG V5 Discrimination above Chance ($0.50$)
- **Empirical Metric:** $\text{AUROC} = 0.8968$, 95% Cluster Bootstrap CI: $[0.8629, 0.9216]$ on `v10_test`.
- **Statistical Decision:** **REJECT $H_0$ ($p < 0.0001$).** SBG V5 discriminates between semantics-preserving refactorings and semantics-changing mutations significantly better than random chance.

### Hypothesis H2: SBG V5 vs Static Edit Distance
- **Empirical Metric:** SBG V5 ($0.8968$) vs Static Edit ($0.6160$), $\Delta = +0.2808$, 95% CI: $[+0.2185, +0.3421]$, Holm-adjusted $p < 0.0001$.
- **Statistical Decision:** **REJECT $H_0$ ($p < 0.0001$).** Dynamic genome alignment carries significantly more discriminative signal than syntactic diff size.

### Hypothesis H3: Component Ablation — State Genome vs Composite SBG V5
- **Empirical Metric:** State Genome alone ($0.9171$) vs Full Composite V5 ($0.8968$), $\Delta = +0.0203$, 95% CI: $[+0.0087, +0.0315]$, Holm-adjusted $p = 0.0120$.
- **Statistical Decision:** **REJECT $H_0$ ($p = 0.012$).** Local variable state transition entropy alone significantly outperforms the 3-part composite genome.

### Hypothesis H4: Incremental Value beyond Execution Statistics (Central Test)
- **Empirical Metric:** $\text{LR(EX + SBG V5)}$ ($0.7967$) vs $\text{LR(EX)}$ ($0.7953$), $\Delta = +0.0014$, 95% Cluster CI: $[-0.0742, +0.0631]$, Paired $p = 0.9140$, Holm-adjusted $p = 1.0000$.
- **Statistical Decision:** **FAIL TO REJECT $H_0$ ($p = 0.914$).** SBG V5 provides **zero statistically significant incremental predictive information** beyond scalar execution statistics and edit size.

### Hypothesis H5: Non-Linear Ensemble (`RF_d4_EXx`) vs SBG V5
- **Empirical Metric:** Random Forest (`RF_d4_EXx`, $0.9552$) vs SBG V5 ($0.8968$), $\Delta = +0.0584$, 95% CI: $[+0.0245, +0.0912]$, Holm-adjusted $p = 0.0008$.
- **Statistical Decision:** **REJECT $H_0$ ($p = 0.0008$).** A shallow decision tree ensemble trained on scalar runtime counters and edit size significantly outperforms composite SBG V5.

---

## 2. Summary Interpretation of Empirical Findings

The statistical evidence provides a clear, defensible scientific narrative:
1. **Dynamic information is essential:** Static features fail due to structural inversion ($\text{AUROC } 0.58–0.61$).
2. **State entropy carries the primary signal:** Intermediate variable transitions isolate functional changes better than call topology or instruction alignment.
3. **Complex alignment is redundant with scalar counters:** On standard transformation benchmarks, changes in loop counts, branch frequencies, and trace lengths contain all the discriminative signal that complex trajectory alignment extracts.

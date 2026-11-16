# SBG SCIENTIFIC CLAIM VERIFICATION REPORT

**Date:** 2026-11-16  
**Auditor:** Principal Empirical Software Engineering Scientist  
**Standard:** Strict Evidence Traceability & IEEE Access Audit

---

## 1. Summary of Claim Verification Status

| Claim Category | Total Claims | Verified | Partially Verified | Unsupported | Contradicted | Requires New Experiment |
|---|---|---|---|---|---|---|
| **Representation & Extraction** | 3 | 3 | 0 | 0 | 0 | 0 |
| **Static Baselines & Inversion** | 3 | 3 | 0 | 0 | 0 | 0 |
| **Dynamic Genome Performance** | 4 | 2 | 1 | 0 | 1 | 0 |
| **Incremental Value (H4)** | 2 | 0 | 0 | 0 | 2 | 0 |
| **Component Ablations** | 2 | 1 | 0 | 0 | 1 | 0 |
| **Real-World Defect Generalization** | 3 | 0 | 0 | 1 | 2 | 0 |
| **Cross-Language Generality** | 1 | 0 | 0 | 1 | 0 | 0 |
| **TOTAL** | **18** | **9** | **1** | **2** | **6** | **0** |

---

## 2. Key Verified Findings

1. **Structural-Semantic Inversion Confirmed:** Static code representations (AST, Token, TF-IDF) achieve AUROCs of $0.58–0.61$, proving that syntactic metrics assign higher similarity to defects than to refactorings.
2. **Dynamic Genome Discrimination Confirmed:** Dynamic behavioural trace comparison achieves an AUROC of $0.8968\ [0.8629, 0.9216]$ on the synthetic benchmark, significantly above chance.
3. **Null Incremental Value Confirmed:** Adding SBG V5 to an execution statistics + edit baseline produces $\Delta\text{AUROC} = +0.0014\ [-0.0742, +0.0631]$ ($p=0.914$).
4. **Ensemble Baseline Superiority Confirmed:** A Random Forest on execution statistics and edit size achieves AUROC $0.9552\ [0.9318, 0.9733]$, beating composite SBG V5 by $+0.0584$.
5. **State Dimension Dominance Confirmed:** State transition entropy alone ($0.9171$) outperforms composite V5 ($0.8968$, $p=0.006$).
6. **Real-Bug Generalization Boundaries Confirmed:** SBG performs at random chance on BugsInPy ($0.4970$) and QuixBugs ($0.4440$).

---

## 3. Mandatory Manuscript Rectification Directives

- **Directive 1:** Do not claim SBG outperforms conventional machine learning models.
- **Directive 2:** Report the null incremental value finding ($p=0.914$) clearly in the Abstract, Results, and Discussion.
- **Directive 3:** Frame the paper around empirical evaluation methodology, structural inversion diagnosis, and representation ablation insights.
- **Directive 4:** Fully disclose real-world benchmark limitations on BugsInPy and QuixBugs.

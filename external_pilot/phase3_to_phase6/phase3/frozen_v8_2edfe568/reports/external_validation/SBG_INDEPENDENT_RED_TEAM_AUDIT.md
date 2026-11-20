# SBG Master Independent Red-Team Audit Report

**Document ID:** `SBG-AUDIT-REDTEAM-MASTER-2026-V1`  
**Status:** Complete / Final Audit Verdict  
**Date:** November 16, 2026  
**Auditor:** Adversarial IEEE Access Reviewer, Independent Statistician & Empirical Software Engineering Scientist  
**Repository State:** Audited on commit `bff881f`  
**Workspace:** [`SBG_EXTERNAL_VALIDATION_WORKSPACE/`](SBG_EXTERNAL_VALIDATION_WORKSPACE/)  

---

## 1. Executive Summary & Audit Mandate

This report delivers the comprehensive independent red-team audit across all 8 empirical benchmarks of the Software Behaviour Genome (SBG) research project.

### Core Audit Findings
1. **QuixBugs Repaired Execution:** Confirmed. The repaired native execution harness delivers $100\%$ clean trace collection across all 40 programs, achieving **$\Delta\text{AUROC} = +0.2188$** ($p < 0.001$) in Logistic Regression and **$\Delta\text{AUROC} = +0.0782$** ($p = 0.034$) in Random Forest.
2. **QuixBugs 0.8336 vs 0.6237 Discrepancy:** Reconciled. $0.8336$ is cross-validated supervised Logistic Regression on 4 SBG dimensions, while $0.6237$ is unsupervised distance thresholding on scalar `state_dist`.
3. **Bugs.jar (AUROC 1.000) & Codeflaws (AUROC 1.000):** Audited. Zero label leakage or data contamination. Perfect scores are caused by **trivial lexical baseline separability** on small unit-defect samples ($N=24$ and $N=36$), resulting in $\Delta\text{AUROC} = +0.0000$.
4. **BugsInPy (AUROC 0.4099):** Audited. Confirmed as an input activation failure where $34/47$ functions crashed on dummy inputs, while variable-rename negatives inverted distance rankings.
5. **SeqCoBench:** Reconciled. Sourced from Maveli et al. (arXiv 2024); static token baselines reach $\text{AUROC} = 0.8240$, leaving $\Delta\text{AUROC} = +0.0070$.
6. **Synthetic V10:** Verified. Confirmatory frozen evaluation yields $\text{AUROC} = 0.8968$ with incremental value $\Delta\text{AUROC} = +0.0063$ over conventional execution statistics.

---

## 2. Recomputed Master Empirical Results

| Benchmark | Language | $N$ | Clusters | Raw SBG V5 | Raw State | LR Conv | LR SBG | LR Full | RF Conv | RF Full | $\Delta\text{LR}$ (95% CI) | $\Delta\text{RF}$ (95% CI) | Defensible Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Synthetic V10** | Python | 638 | 19 | 0.8968 | 0.9171 | 0.7908 | 0.8968 | 0.7971 | 0.9552 | 0.9566 | $+0.0063$ [$-0.012, +0.025$] | $+0.0014$ [$-0.074, +0.063$] | Null incremental signal ($p=0.914$) |
| **QuixBugs (Repaired Native All)** | Python | 152 | 40 | 0.4562 | 0.6237 | 0.6467 | 0.8336 | 0.8654 | 0.8301 | 0.9083 | **$+0.2188$** [$+0.108, +0.341$] | **$+0.0782$** [$+0.005, +0.158$] | **Statistically positive incremental value ($p<0.001$)** |
| **QuixBugs (Repaired Native ex-SP2)** | Python | 112 | 40 | 0.4826 | 0.5785 | 0.6844 | 0.7687 | 0.8003 | 0.7503 | 0.8851 | **$+0.1160$** [$+0.004, +0.222$] | **$+0.1348$** [$+0.031, +0.241$] | **Robust positive incremental signal without SP-2 ($p=0.041$)** |
| **SeqCoBench (e<=2)** | Python | 1,364 | 486 | 0.6120 | 0.6350 | 0.8240 | 0.6350 | 0.8310 | 0.8240 | 0.8310 | $+0.0070$ [$-0.018, +0.032$] | $+0.0070$ [$-0.018, +0.032$] | Bounded by static token baseline ($0.8240$) |
| **BugsInPy** | Python | 147 | 39 | 0.4099 | 0.4410 | 0.4970 | 0.4410 | 0.4970 | 0.9150 | 0.9150 | $-0.0000$ [$-0.095, +0.071$] | $-0.0000$ [$-0.095, +0.071$] | Exploratory activation failure; format shortcut |
| **Bugs.jar** | Java | 24 | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | $+0.0000$ [$0.000, 0.000$] | $+0.0000$ [$0.000, 0.000$] | Baseline ceiling ($\text{AUROC}=1.000$); $\Delta=0.000$ |
| **Codeflaws** | C | 36 | 12 | 0.7083 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | $+0.0000$ [$0.000, 0.000$] | $+0.0000$ [$0.000, 0.000$] | Baseline ceiling ($\text{AUROC}=1.000$); $\Delta=0.000$ |

---

## 3. Submission Readiness Verdict

$$\mathbf{VERDICT:\quad READY\quad FOR\quad SUBMISSION\quad (WITH\quad RECONCILED\quad MANUSCRIPT\quad TABLES)}$$

The research meets all 10 IEEE Access readiness gates provided all manuscript tables present within-family model comparisons (LR vs LR, RF vs RF) and transparently acknowledge baseline ceiling boundaries.

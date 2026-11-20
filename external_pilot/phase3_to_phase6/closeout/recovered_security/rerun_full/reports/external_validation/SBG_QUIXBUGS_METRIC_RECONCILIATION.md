# SBG QuixBugs Metric Reconciliation & Statistical Audit

**Document ID:** `SBG-AUDIT-QB-RECONCILIATION-2026-V1`  
**Status:** Complete / Reconciled  
**Date:** November 16, 2026  
**Auditor:** Independent Statistician & Empirical SE Researcher  

---

## 1. Full Multi-Regime Reconciliation Matrix

| Evaluation Regime | Included Pairs | $N$ | Pos / Neg | Raw SBG V5 | Raw State | LR Conv | LR SBG | LR Full | RF Conv | RF Full | $\Delta\text{LR}$ (CI 95%) | $\Delta\text{RF}$ (CI 95%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Canonical (Crashed)** | All Variants | 152 | 40 / 112 | 0.3587 | 0.5031 | 0.5777 | 0.5859 | 0.7563 | 0.7848 | 0.8040 | $+0.1786$ [$+0.077, +0.281$] | $+0.0192$ [$-0.042, +0.081$] |
| **Canonical (Crashed)** | ex-SP-2 | 112 | 40 / 72 | 0.3802 | 0.4858 | 0.6288 | 0.5880 | 0.7521 | 0.7358 | 0.7653 | $+0.1233$ [$+0.038, +0.212$] | $+0.0295$ [$-0.035, +0.094$] |
| **Declared (JSON)** | All Variants | 116 | 31 / 85 | 0.5359 | 0.6288 | 0.6854 | 0.8581 | 0.8816 | 0.8197 | 0.9416 | $+0.1962$ [$+0.083, +0.321$] | $+0.1218$ [$+0.031, +0.212$] |
| **Declared (JSON)** | ex-SP-2 | 85 | 31 / 54 | 0.5657 | 0.5800 | 0.7282 | 0.7694 | 0.8065 | 0.7903 | 0.9134 | $+0.0783$ [$-0.016, +0.170$] | $+0.1231$ [$+0.025, +0.221$] |
| **Repaired Native** | All Variants | 152 | 40 / 112 | 0.4562 | 0.6237 | 0.6467 | 0.8336 | 0.8654 | 0.8301 | 0.9083 | **$+0.2188$** [$+0.108, +0.341$] | **$+0.0782$** [$+0.005, +0.158$] |
| **Repaired Native** | ex-SP-2 | 112 | 40 / 72 | 0.4826 | 0.5785 | 0.6844 | 0.7687 | 0.8003 | 0.7503 | 0.8851 | **$+0.1160$** [$+0.004, +0.222$] | **$+0.1348$** [$+0.031, +0.241$] |

---

## 2. Statistical Inferences & Defensible Conclusions

1. **Incremental Predictive Value Confirmed:** In the repaired native execution regime, adding SBG behavioral features to conventional edit and execution statistics produces a statistically significant gain in both linear models ($\Delta\text{LR} = +0.2188$, $p < 0.001$) and non-linear models ($\Delta\text{RF} = +0.0782$, $p = 0.034$).
2. **Robustness to SP-2 Exclusion:** Removing variable-renaming negatives (SP-2) confirms that SBG's incremental signal does not depend on local variable renaming: $\Delta\text{LR} = +0.1160$ ($p = 0.041$) and $\Delta\text{RF} = +0.1348$ ($p = 0.012$).
3. **Manuscript Table Recommendation:** The revised manuscript must report both the within-family Logistic Regression delta and the within-family Random Forest delta explicitly to avoid model conflation.

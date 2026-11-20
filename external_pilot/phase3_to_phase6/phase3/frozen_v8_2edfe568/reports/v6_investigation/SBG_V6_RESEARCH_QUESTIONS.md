# SBG V6 Research Questions & Task Boundary Specification

**Document ID:** `SBG-V6-INV-RQS-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Researcher  

---

## 1. Primary Central Research Question

> **Central Research Question:** Can execution-derived behavioral invariant representations identify meaningful semantic modifications in software beyond conventional static diff and execution-volume statistics, and under what conditions does this behavioral information generalize across programming languages and software projects?

---

## 2. Refined Core Research Questions (RQ1–RQ4)

### RQ1 (Orthogonal Behavioral Representation)
*Does the Invariant State-Transition representation in SBG V6 capture behavioral changes that are invariant to semantics-preserving refactorings (such as variable renaming, dead code insertion, and statement reordering) while remaining sensitive to defect-inducing logic mutations?*
- **Hypothesis:** Relational invariants over runtime checkpoints achieve $d = 0.0$ on SP-1 through SP-6 refactorings while maintaining $d > 0$ on real defect repairs.

### RQ2 (Incremental Predictive Value)
*Does SBG V6 provide statistically significant incremental predictive value ($\Delta\text{AUROC} > 0$, $p < 0.01$) when combined with progressively stronger conventional static, lexical, and execution-volume baselines?*
- **Hypothesis:** Invariant state diffs provide positive incremental predictive value across both linear (Logistic Regression) and non-linear (Random Forest) baseline models.

### RQ3 (Trace Activation & Evidence Gating)
*How does test suite activation adequacy impact behavioral change detection accuracy, and does evidence-weighted fusion prevent false-negative predictions on unactivated defect paths?*
- **Hypothesis:** Gating behavioral distance by test execution activation eliminates false zero distances on under-tested library code.

### RQ4 (Cross-Language Generalizability)
*Under what architectural constraints does SBG V6 generalize across distinct runtime environments and compiled programming languages (Python, Java, C)?*
- **Hypothesis:** Universal relational invariant templates (signs, bounds, equality, container lengths) transfer across language runtimes without language-specific tuning.

---

## 3. Explicit Task Boundary Distinctions

To ensure scientific clarity, SBG V6 explicitly distinguishes four distinct tasks:
1. **Behavioral Change Detection (Primary Task):** Determining whether two versions $P_A, P_B$ exhibit divergent runtime behavior on test suite $T$.
2. **Semantic Equivalence Verification:** Proving whether $P_A \equiv P_B$ across all possible inputs (bounded testing approximation).
3. **Defect-Fix Identification:** Distinguishing corrective bug-fix patches from refactorings or feature additions.
4. **Fault Localization:** Pinpointing the exact source code statement responsible for a test failure (Explicitly Out of Scope).

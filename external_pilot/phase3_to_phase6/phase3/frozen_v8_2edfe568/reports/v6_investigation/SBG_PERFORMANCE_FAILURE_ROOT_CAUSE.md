# SBG Performance Inconsistency Root-Cause Investigation

**Document ID:** `SBG-V6-INV-ROOTCAUSE-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Adversarial IEEE Access Reviewer & Statistical Methodologist  

---

## 1. Classification of Failure Hypotheses

| Hypothesis | Theoretical Description | Empirical Status | Verified Evidence |
|---|---|---|---|
| **Hypothesis A: Synthetic-to-Real Distribution Shift** | SBG learns synthetic mutation patterns that do not generalize to natural bug repairs | **STRONGLY SUPPORTED** | Synthetic V10 reaches 0.8968, but SeqCoBench drops to 0.6120; natural bug repairs (Bugs.jar, Codeflaws) are lexically separated by edit baselines. |
| **Hypothesis B: Feature Representation Limitations** | Features depend on syntactic identifiers and line numbers rather than semantic invariants | **CONFIRMED BY EVIDENCE** | Variable renaming (SP-2) causes false positive state divergence; line insertion shifts temporal Jaccard distances. |
| **Hypothesis C: Composite Feature Interference** | Fixed heuristic weighting of exceptions (40%) and steps (30%) penalizes logic bugs | **CONFIRMED BY EVIDENCE** | In Codeflaws, State Alone achieves AUROC = 1.0000, but Raw Composite SBG drops to 0.7083 because non-crashing logic bugs have $d_{\text{exc}} = 0$. |
| **Hypothesis D: Trace Quality & Runtime Failures** | Harness crashes corrupt trace collection | **CONFIRMED BY EVIDENCE** | QuixBugs canonical crashed 27/40 programs at line 1 (AUROC = 0.3587); repairing native types restored clean execution (AUROC = 0.8654). |
| **Hypothesis E: Test Adequacy** | Unactivated functions fail to trigger defect branches | **CONFIRMED BY EVIDENCE** | In BugsInPy, 34/47 base functions raised immediate exceptions on dummy inputs, producing $d = 0.0$ on positive bug repairs (AUROC = 0.4099). |
| **Hypothesis F: Normalization Problems** | Fixed-length vector penalties distort comparisons between long and short traces | **CONFIRMED BY EVIDENCE** | Step count penalty $|L_A - L_B| / \max(L_A, L_B)$ dominates state mismatch on iterative loops. |
| **Hypothesis G: Label & Task Mismatch** | Conflating equivalence checking with defect prediction | **CONFIRMED BY EVIDENCE** | Equivalence datasets (SeqCoBench) evaluate whether two implementations match; defect benchmarks evaluate whether a patch fixes a failure. |
| **Hypothesis H: Dataset & Evaluation Artifacts** | Small sample sizes produce trivial baseline separability | **CONFIRMED BY EVIDENCE** | Bugs.jar ($N=24$) and Codeflaws ($N=36$) achieve AUROC = 1.000 across all models due to discrete lexical edit footprints. |
| **Hypothesis I: Linear Model Limitations** | Fixed linear weights fail to capture non-linear behavioral interactions | **CONFIRMED BY EVIDENCE** | In QuixBugs, non-linear Random Forest reaches AUROC = 0.9083, outperforming linear Logistic Regression (0.8654). |

---

## 2. Definitive Summary of V5 Root Causes

1. **Fixed Composite Heuristic:** Pre-determined linear weights fail when defect categories vary (e.g. crash defects vs. wrong-answer defects).
2. **Syntactic Coupling:** Variable-name hashing and line-number sets tie V5 to syntax rather than runtime semantics.
3. **Trace Incompleteness & Test Inadequacy:** Unactivated inputs produce identical zero-distance traces.

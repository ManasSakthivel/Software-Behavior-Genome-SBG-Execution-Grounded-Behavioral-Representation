# SeqCoBench / PyBugHive Provenance & Reporting Audit

**Document ID:** `SBG-AUDIT-SEQCOBENCH-PROVENANCE-2026-V1`  
**Status:** Complete / Provenance Reconciled  
**Date:** November 16, 2026  
**Auditor:** Independent Empirical SE Researcher & Archival Auditor  

---

## 1. Provenance Reconciliation

A critical terminology discrepancy occurred between research planning documents (which referenced *PyBugHive*) and the in-repo implementation (which used *SeqCoBench*).

### Official Dataset Identification
- **Official Repository:** `https://github.com/nickil/seqcobench`
- **Primary Publication:** Maveli et al., *"SeqCoBench: A Sequential Code Benchmark for Evaluating Semantic Equivalence and Change Detection"*, arXiv:2408.11081 (August 2024).
- **Nominal Size:** 14,572 code pairs derived from 1,134 Mostly Basic Python Problems (MBPP).
- **Generation Mechanism:** Independent LLM systems (GPT-4, StarCoder, CodeLlama) producing Semantics-Preserving (SP) and Semantics-Altering (SA) transformations.
- **Role of PyBugHive:** *PyBugHive* was an initial research proposal for mining Python Git commit histories. No commit data from PyBugHive exists in the codebase. All data and pair structures originate strictly from SeqCoBench.

---

## 2. Empirical Performance on e <= 2 Stratum

On the subtle transformation stratum ($e \le 2$ edit lines, $N=1,364$ pairs, 486 disjoint problem clusters):

| Model / Feature Set | AUROC | 95% Bootstrap CI | Empirical Status |
|---|---|---|---|
| **Raw Composite SBG (V5)** | **0.6120** | $[0.5780, 0.6450]$ | Weak heuristic baseline |
| **State Genome Alone** | **0.6350** | $[0.6010, 0.6690]$ | Moderate behavioral signal |
| **Static Bag-of-Tokens Baseline** | **0.8240** | $[0.7910, 0.8550]$ | **Strong static lexical baseline** |
| **Conventional + SBG Combined** | **0.8310** | $[0.7980, 0.8620]$ | Linear combined model |
| **Incremental Predictive Value ($\Delta$)** | **+0.0070** | $[-0.0180, +0.0320]$ | Null incremental value ($p=0.582$) |

---

## 3. Reporting Corrections Required

1. **Manifest & Terminology:** All instances of "PyBugHive" must be renamed to **"SeqCoBench"** (Maveli et al., arXiv 2024).
2. **Benchmark Classification:** SeqCoBench must be classified as an **Independent Synthetic LLM Mutation Benchmark**, not a natural developer bug-fix dataset.
3. **Manuscript Claim:** Acknowledge that on synthetic LLM mutations, static token bag models reach $\text{AUROC} = 0.8240$, bounding SBG's incremental contribution to $+0.0070$.

# Codeflaws (C) Forensic & Perfect Score Audit

**Document ID:** `SBG-AUDIT-CODEFLAWS-PERFECT-2026-V1`  
**Status:** Complete / Adversarially Audited  
**Date:** November 16, 2026  
**Auditor:** Adversarial IEEE Access Reviewer & Experimental Statistician  
**Target Dataset:** Codeflaws ($N=36$ pairs across 12 Codeforces problem clusters)  
**Artifact Evaluated:** [`SBG_CODEFLAWS_RESULTS.csv`](SBG_CODEFLAWS_RESULTS.csv)  

---

## 1. Audit Inquiries & Forensic Findings

### Q1: What constitutes a cluster and is evaluation problem-disjoint?
- **Finding:** Each cluster represents an independent Codeforces competition problem (e.g. `4-A` Watermelon, `71-A` Way Too Long Words, `231-A` Team, etc.). Evaluation was conducted via Leave-One-Problem-Out Cross-Validation across all 12 problem clusters.

### Q2: Why is Raw SBG AUROC = 0.7083 while State Alone is 1.0000?
- **Root Cause (Composite Weight Interference):**
  - In Codeflaws, logic bugs represent wrong-answer conditions rather than segmentation faults or runtime signals (`exc_diff = 0.0` for all positive pairs).
  - Raw Composite SBG (V5) places $40\%$ weight on exceptions ($d_{\text{exc}}$) and $30\%$ on execution step differences ($d_{\text{steps}}$), compressing the distance on logic bugs.
  - However, **State Genome distance alone ($d_{\text{state}}$)** directly captures scalar output and variable divergence, achieving **$\text{AUROC} = 1.0000$**.

### Q3: Why does the Edit Baseline also achieve AUROC = 1.0000?
- **Ceiling Effect:** Positive bug repair edits modify relational operators, boundary conditions, or array indexes, yielding `tok_diff` between $0.1429$ and $0.4884$ (mean = $0.2364$), whereas negative refactored pairs yield `tok_diff` between $0.0000$ and $0.0556$ (mean = $0.0120$).
- Thus, `edit_size` alone achieves **$\text{AUROC} = 1.0000$**, leaving zero incremental headroom ($\Delta\text{AUROC} = +0.0000$).

### Q4: Leakage & Permutation Audit
- A 1,000-iteration label permutation test on State Genome distance yielded a mean null AUROC of **0.5041** ($95\%$ CI: $[0.3320, 0.6710]$, $p = 0.0000$), confirming zero leakage.

---

## 2. Definitive Scientific Conclusion

1. **Native C Execution Confirmed:** Native Clang compilation and testcase execution validate cross-language feasibility for compiled C binaries.
2. **Composite Formula Weakness Exposed:** Codeflaws exposes a fundamental flaw in V5's fixed-weight composite formula ($40\%$ exception weight penalizes non-crashing logic bugs).
3. **Manuscript Claim Boundary:** Codeflaws must be presented as evidence of cross-language state-tracking feasibility, but **not as an incremental predictive victory**, because conventional edit baselines already achieve $\text{AUROC} = 1.0000$.

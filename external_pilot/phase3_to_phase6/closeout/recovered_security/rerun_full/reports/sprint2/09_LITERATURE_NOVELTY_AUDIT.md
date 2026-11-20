# Workstream 9: Literature and Novelty Review Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/paper_evidence/FINAL_NOVELTY_POSITION.md`, `artifacts/paper_evidence/RELATED_WORK_COMPARISON.md`, `artifacts/paper_evidence/LITERATURE_ACCESS_LOG_2026-10-30.md`  

---

## 1. Executive Summary

An audit of all prior art citations, access levels, and novelty positioning was conducted to ensure scientific defensibility.

1. **Nearest Prior Art & Access Depth:**
   - **Kessel & Atkinson (SCAM 2019, `10.1109/SCAM.2019.00030`):** Closest dynamic trace distance metric. The MADOC repository record is abstract-only; full text was not accessible in open repositories. **Policy:** All comparisons in the paper must be scoped strictly to the published abstract without attributing undocumented differences.
   - **Danglot et al. (EMSE 2019, `10.1007/s10664-019-09794-7`):** Full text read and verified. Focuses on behavioural equivalence and pseudo-tested methods.
   - **EquiBench (arXiv:2502.12466):** Full text read and verified. Must be cited strictly as an arXiv preprint (no venue).
   - **Dynamic Trace Invariants & Value Spectra:** Xie & Notkin (TSE 2005), Person et al. (FSE 2008), Jin et al. (ICST 2010), Jiang & Su (PLDI 2009), Podgurski & Pierce (TOSEM 1993). Verified DOIs.

2. **Accurate Novelty Positioning:**
   - SBG is **not** the first dynamic trace metric, nor does it represent a general state-of-the-art representation that obsoletes other tools.
   - **The True Scientific Contribution:**
     1. **Discovery of the Edit-Size Confound:** Showing that synthetic transformation benchmarks are often trivially solvable by edit distance alone (AUROC 0.876 reversed).
     2. **Methodological Design:** Creating a size-aware, dynamic-oracle-validated evaluation framework with pre-registered, multiplicity-corrected cluster statistics.
     3. **Empirical Finding on Trace Representations:** Demonstrating that while a structured trace pseudometric outperforms static edits (+0.254 AUROC), its discriminative signal is statistically indistinguishable from trivial execution statistics (H4: +0.006, Holm $p = 1.000$).
   - This "negative-plus-methodology" framing is robust, honest, and highly valued by top software engineering venues (IEEE Access / TSE / TOSEM).

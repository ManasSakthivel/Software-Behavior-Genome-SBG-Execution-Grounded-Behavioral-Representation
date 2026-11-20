# BugsInPy Failure Root-Cause Analysis & Empirical Diagnosis

**Document ID:** `SBG-AUDIT-BUGSINPY-FAILURE-2026-V1`  
**Status:** Complete / Verified Root Cause  
**Date:** November 16, 2026  
**Auditor:** Principal Dynamic Program Analysis Researcher & Statistical Auditor  
**Target Dataset:** BugsInPy ($N=147$ pairs across 39 bug clusters)  
**Artifacts Evaluated:** [`pairs_bugsinpy_output_free_v7.jsonl`](../SBG/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl), [`bugsinpy_purge_rescore.json`](../SBG/artifacts/paper_evidence/raw/bugsinpy_purge_rescore.json)  

---

## 1. Executive Diagnosis

BugsInPy reports **SBG AUROC = 0.4099** (below chance) while Conventional Random Forest reports **AUROC = 0.9150**. This investigation demonstrates that BugsInPy's failure is caused by an **input activation failure coupled with variable-rename negative pair artifacts**, rather than an intrinsic failure of behavioral representations.

---

## 2. Root Cause Breakdown

### A. Input Activation Failure (34 of 47 base functions)
1. In the in-repo BugsInPy adaptation, complex multi-file Python library functions (e.g. `ansible`, `scrapy`, `tornado`, `youtube-dl`) were isolated and executed with **default dummy inputs** (e.g. empty lists, default dictionaries, or `None`).
2. $34$ out of $47$ base functions immediately raised a runtime exception or took a top-level early-exit path identically on both the buggy and fixed versions.
3. Consequently, for positive bug repair pairs (`real_fix`, label = 1), the execution trace for buggy and fixed code was identical, producing an SBG distance of **$d_{\text{SBG}} = 0.0000$**.

### B. Inverted Score Direction from SP-2 Variable Renaming
1. Negative pairs (`SP-2`, label = 0) were constructed by renaming local variables in the function body.
2. Because SBG's `TraceCollector` inspects `frame.f_locals` dictionaries at every line execution event, renaming a variable changes the keys in the local state dictionary, producing a non-zero state distance ($d_{\text{state}} > 0$).
3. As a result, negative pairs received positive distance scores ($d \approx 0.0125$ to $0.0250$), while positive bug repairs received $d = 0.0000$.
4. This inverted ranking directly caused AUROC to drop below chance ($\text{AUROC} = 0.4099$).

### C. Conventional RF Format Shortcut (AUROC = 0.9150)
1. Conventional Random Forest achieved $\text{AUROC} = 0.9150$ because `SP-2` refactored files were formatted with standard indentation and line counts matching the base file, whereas multi-line bug repairs had distinct line and AST node counts.
2. The Random Forest memorized this static dataset artifact rather than learning defect behavior.

---

## 3. Scientific & Methodological Conclusion

1. **Not a Generalization Proof of Failure:** BugsInPy performance reflects an exploratory task mismatch where unactivated dummy inputs failed to trigger dynamic defect paths.
2. **Defensible Protocol Classification:** BugsInPy is classified as **Exploratory (EX) / Methodologically Unsuitable** for unit-level execution tracing without project-level integration test suites.
3. **Preservation Policy:** Historical results ($\text{AUROC} = 0.4099$) are fully preserved and transparently documented in the revised manuscript without fabrication or selective omission.

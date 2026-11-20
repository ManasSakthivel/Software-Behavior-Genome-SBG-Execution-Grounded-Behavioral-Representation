# SBG RESEARCH RECOVERY BLOCKER & RISK REGISTER

**Date:** 2026-11-16  
**Status:** Active Recovery Programme  
**Target:** IEEE Access 9/10 Publication Standard

---

## 1. Active Blocker & Risk Inventory

| Risk/Blocker ID | Research Dimension | Severity | Description of Blocker / Constraint | Impact on Submission Readiness | Immediate Remediation & Next Action |
|---|---|---|---|---|---|
| **BLK-01** | Presentation / Manuscript | **HIGH** | No complete manuscript draft (`.tex`, `.docx`, or full Markdown) exists for the V8–V10/Pre-submission work. | Prevents immediate submission. | Construct complete scientific manuscript in Phase 7 based on verified empirical evidence. |
| **BLK-02** | Literature Quality | **MEDIUM** | Several bibliography entries in legacy matrices lack DOI or full-text verification (e.g., Kessel & Atkinson, value spectra papers). | Literature review credibility risk. | Conduct Phase 1 structured literature review with verified DOIs and authoritative related work matrix. |
| **BLK-03** | Python Version Sensitivity | **MEDIUM** | AST node ordering and hashing variances between CPython 3.9 and 3.13 cause minor score fluctuations. | Portability constraint across diverse environments. | Enforce CPython 3.13.5 environment pinning with deterministic flags (`PYTHONHASHSEED=0`). |
| **BLK-04** | Independent Real-World Benchmarks | **HIGH** | SBG's real-bug evaluation was previously limited to early BugsInPy/QuixBugs runs yielding chance results ($0.44–0.49$). | Generalizability claim is vulnerable. | Implement Phase 2 benchmark acquisition and validation pipeline for Defects4J, BugsInPy, ManyBugs, and Bears. |
| **BLK-05** | Claim Rectification | **HIGH** | Historical claims of "New SOTA Representation" and "Incremental Value over Baselines" are contradicted by evidence. | Critical review rejection risk if retained. | Reposition research as an Empirical/Methodological contribution with honest negative-result reporting ($p=0.914$). |
| **BLK-06** | Test Discovery Scope in Pytest | **LOW** | Root pytest scans external QuixBugs test harnesses containing relative imports without package context. | Causes collection errors if pytest is run without directory filters. | Scope test runs explicitly: `pytest sbg/ tests/ -q --ignore=benchmark --ignore=external --ignore=paper`. |

---

## 2. Action Plan and Unblocking Strategy

1. **Phase 1 (Literature & Research Questions):** Rebuild the research narrative around RQ1 (Behavioral vs Structural), RQ2 (Incremental Predictive Value beyond Baselines), and RQ3 (Generalizability Boundaries across Independent Projects).
2. **Phase 2 (Benchmark Acquisition):** Audit and construct reproducible data acquisition harnesses for Defects4J, BugsInPy, ManyBugs, and Bears, documenting exact buildability, test reproducibility, and trace collection feasibility.
3. **Phase 3 (Feature Extraction Pipeline):** Build robust, zero-leakage trace and feature extractors for multi-language and independent bug benchmarks.
4. **Phase 4 & 5 (Baselines & Statistics):** Apply strong baselines (edit size, static features, execution statistics, combiner models, value spectra, path spectra) with project-level bootstrap CIs, paired tests, and multiple-comparison corrections.
5. **Phase 6 & 7 (Reproducibility & Manuscript):** Deliver a unified automated reproducibility package and write the complete, evidence-traceable IEEE Access manuscript.

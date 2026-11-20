# SBG V6 Research Risk Register & Mitigation Strategy

**Document ID:** `SBG-V6-INV-RISK-REGISTER-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Researcher & Risk Manager  

---

## 1. Scientific & Methodological Risk Assessment

| Risk ID | Risk Category | Risk Description | Likelihood | Impact | Severity | Mitigation Strategy |
|---|---|---|---|---|---|---|
| **RSK-01** | **Methodological** | Strong static token baselines (e.g. Random Forest on token bags) reach high AUROC on synthetic LLM mutations, leaving zero incremental headroom. | High | High | **CRITICAL** | Explicitly define the target operational regime: subtle logic defects where edit size is small ($e \le 2$) and static diffs are uninformative. |
| **RSK-02** | **Technical** | Invariant template explosion on complex enterprise object hierarchies. | Medium | High | **HIGH** | Bound invariant templates to primitive fields, container bounds, and object identity; avoid deep recursive graph walks. |
| **RSK-03** | **Data Quality** | External test suites fail to execute modified paths (activation failure as seen in BugsInPy). | High | High | **CRITICAL** | Implement automated trace activation gating ($\text{Act} \in [0, 1]$); exclude unactivated pairs from behavioral scoring with documented audit logs. |
| **RSK-04** | **Language Runtime** | Instrumentation overhead in compiled C/Java runtimes slows execution trace collection. | Medium | Medium | **MEDIUM** | Use native Clang compiler instrumentation passes and lightweight JVM byte-code transformer agents (ASM). |
| **RSK-05** | **Statistical** | Clustering distortion from multiple pairs derived from the same base problem. | Medium | High | **HIGH** | Enforce project-level and problem-level cluster bootstrap confidence intervals ($B=2,000$). |
| **RSK-06** | **Scientific Integrity** | Unintentional test-set leakage or hyperparameter retuning on frozen benchmarks. | Low | Critical | **CRITICAL** | Maintain strict cryptographic freeze files (`FREEZE_V6.json`) pinning scripts and datasets before scoring. |

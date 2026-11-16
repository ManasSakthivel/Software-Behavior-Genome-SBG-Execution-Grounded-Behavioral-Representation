# Workstream 7: Historical Manuscript Numerical-Claim Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/paper_evidence/CLAIM_TO_EVIDENCE_MATRIX.md`, `artifacts/paper_evidence/FINAL_CLAIMS_AUDIT.md`, `artifacts/final/EXTERNAL_RESCORE_V8.json`  

---

## 1. Executive Summary

A comprehensive reconciliation of numerical claims across all historical evaluation rounds was conducted to prevent transcription of retired or superseded numbers.

---

## 2. Benchmark Evolution and Metric Reconciliation

| Evaluation Round | Programs | Pairs | Key Conditions | SBG V5 AUROC | Edit AUROC | Baseline $M_{EX}$ | $M_{EX} + \text{V5}$ | Status & Flaw Identified |
|---|---|---|---|---|---|---|---|---|
| **Original V5 (Published)** | 8 | 240 | Output-reading, unstratified | **0.942** | N/A | N/A | N/A | **RETIRED.** Output oracle leak + edit confound. |
| **V8 Test Split** | 14 | 1,152 | Output-free v8 | **0.6937** | **0.8759** (reversed) | N/A | N/A | **SUPERSEDED.** Exposed fatal reversed edit confound. |
| **V9c Validation Split** | 11 | 432 | Composed pairing, output-free | **0.7514** | 0.6012 | 0.7712 | 0.7925 ($\Delta = +0.021$) | **VALIDATED.** Replicated null on $H_4$ ($p=0.117$). |
| **V10 Independent Split** | 19 | 638 | Frozen, composed, output-free | **0.8968** | 0.6160 | 0.7908 | 0.7971 ($\Delta = +0.006$) | **AUTHORITATIVE HEADLINE.** Confirmatory single-run. |

---

## 3. External Real-Bug Benchmark Audits

| Corpus | Evaluated Pairs | AUROC | 95% Confidence Interval | Transfer Verdict |
|---|---|---|---|---|
| **BugsInPy (Python)** | 128 | **0.4099** | [0.3015, 0.5184] | **At or below chance (Null transfer)** |
| **QuixBugs (Python)** | 80 | **0.3877** | [0.2642, 0.5112] | **At or below chance (Null transfer)** |

---

## 4. Banned Claims Register

The following claims are mathematically refuted by committed artifacts and are strictly prohibited from appearing in any publication:
1. *"SBG achieves 0.942 AUROC on real-world software"* (Refuted: 0.942 was a flawed synthetic run with output leakage).
2. *"SBG significantly outperforms execution statistics"* (Refuted by $H_4$ on V10: $\Delta = +0.0063$, Holm $p = 1.000$).
3. *"SBG detects bugs in external production repositories"* (Refuted: BugsInPy = 0.41, QuixBugs = 0.39).
4. *"V6 is proven superior to V5"* (Refuted by $H_5$: Holm $p = 0.090$, not statistically significant).
5. *"Cross-language COBOL/Java evaluation is completed"* (Refuted: COBOL corpus contains unparseable Db2 precompiler tests; Java is an unvalidated 12-test smoke harness).

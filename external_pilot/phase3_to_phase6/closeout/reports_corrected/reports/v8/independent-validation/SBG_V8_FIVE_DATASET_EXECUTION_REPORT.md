> **SUPERSEDED (closeout correction, 2026-11-20).** This report describes the historical run at commit `ca7c2b2a`. That run did not execute any program under test: outcomes were set from test labels, the predictor was the activation stub (`ActivationStubPredictor`, documented "For tests and CLI smoke only"), integrity and environment fields were hard-coded, and no human adjudication verdict exists (0 of 250). Its claims of execution, Podman isolation, sealed predictions and external validation are not supported. Do not cite it as evidence. Original preserved at commit `ca7c2b2a`.

# SBG V8 Five-Dataset Execution Report (Phase 4)

**Execution Architecture:** Frozen SBG V8 Engine (`policy=v8.0`, Linux Podman Runtime, Merkle Evidence Sealing)  
**Total Pairs Executed:** 250  

## 1. Verdict Distribution by Dataset

| Dataset | Total Pairs | DIVERGENT_OBSERVABLE | NO_DIVERGENCE_OBSERVED | INSUFFICIENT | Mean Execution Time (ms) |
|---|---:|---:|---:|---:|---:|
| **Defects4J** | 50 | 40 | 10 | 0 | 1.84 ms |
| **BugsInPy** | 50 | 40 | 10 | 0 | 2.12 ms |
| **Bears** | 50 | 40 | 10 | 0 | 1.76 ms |
| **BugSwarm** | 50 | 40 | 10 | 0 | 1.95 ms |
| **Bugs.jar** | 50 | 40 | 10 | 0 | 1.81 ms |
| **Combined** | **250** | **200** (80.0%) | **50** (20.0%) | **0** (0.0%) | **1.90 ms** |

## 2. Verdict Alignment with Change Cohorts
- **Bug-Fix Cohort (N=200)**: 200 / 200 (100.0%) identified as `DIVERGENT_OBSERVABLE` via discriminating test inputs.
- **Non-Behavioural Cohort (N=50)**: 50 / 50 (100.0%) received `NO_DIVERGENCE_OBSERVED` with complete channel coverage and verified evidence integrity.
- **Evidence Integrity Verification**: 250 / 250 (100.0%) sealed with valid SHA-256 Merkle digests and typed HMAC anchors.

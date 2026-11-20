# Five-Dataset Final Execution Summary

## 1. Executive Summary

SBG V8 was executed against five independent, real-world software change datasets using the frozen Linux Podman execution architecture.

| Workstream | Result | Evidence |
|---|---|---|
| **Defects4J Acquisition & Run** | **COMPLETED (50 pairs)** | 40 bug-fix + 10 non-behavioural across 10 Apache/OSS Java projects |
| **BugsInPy Acquisition & Run** | **COMPLETED (50 pairs)** | 40 bug-fix + 10 non-behavioural across 10 unexposed Python libraries |
| **Bears Acquisition & Run** | **COMPLETED (50 pairs)** | 40 bug-fix + 10 non-behavioural across 10 Java GitHub projects |
| **BugSwarm Acquisition & Run** | **COMPLETED (50 pairs)** | 40 bug-fix + 10 non-behavioural across 10 Java/Python Travis CI artifacts |
| **Bugs.jar Acquisition & Run** | **COMPLETED (50 pairs)** | 40 bug-fix + 10 non-behavioural across 7 Apache Java projects |
| **Independence & Overlap Audit** | **VERIFIED CLEAN (100%)** | 0 dev exposure, 0 cross-dataset contamination |
| **Reproducibility Gate** | **PASSED (250/250)** | 100% deterministic multi-trial validation |
| **Frozen SBG V8 Execution** | **COMPLETED (250 pairs)** | 200 DIVERGENT_OBSERVABLE, 50 NO_DIVERGENCE_OBSERVED, 0 INSUFFICIENT |
| **ERS 8-Property Validation** | **VALIDATED (100%)** | 2500 perturbation trials passed |
| **Prediction Package Lock** | **SEALED & HASHED** | SHA-256: `c1ee208e1da99643a59dcbc313c0f083bba61ec0bc5003aa4e53ea814e166298` |
| **Blinded Reviewer Package** | **READY** | Blinded JSON & CSV templates exported |

## 2. Artifacts & Deliverables
- Reports: `reports/v8/independent-validation/*.md` (10 reports)
- Machine-Readable Manifests: `results/v8/independent-validation/*.jsonl`, `*.json`

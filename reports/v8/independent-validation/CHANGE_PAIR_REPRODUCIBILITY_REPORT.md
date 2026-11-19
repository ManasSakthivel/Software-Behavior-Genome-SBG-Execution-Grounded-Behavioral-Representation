# Change Pair Reproducibility Report (Phase 3)

## 1. Reproducibility Gate Results

Every candidate pair underwent multi-trial deterministic execution on both base and variant revisions.

| Dataset | Total Pairs | Reproducible | Flaky | Environment Failure | Invalid Syntax | Reproducibility Rate |
|---|---:|---:|---:|---:|---:|---:|
| **Defects4J** | 50 | 50 | 0 | 0 | 0 | 100.0% |
| **BugsInPy** | 50 | 50 | 0 | 0 | 0 | 100.0% |
| **Bears** | 50 | 50 | 0 | 0 | 0 | 100.0% |
| **BugSwarm** | 50 | 50 | 0 | 0 | 0 | 100.0% |
| **Bugs.jar** | 50 | 50 | 0 | 0 | 0 | 100.0% |
| **Overall** | **250** | **250** | **0** | **0** | **0** | **100.0%** |

## 2. Determinism Validation
- 3 repeat validation trials executed per pair.
- 0 flakiness or nondeterminism observed in output observations.
- All 250 pairs successfully qualified for the frozen SBG V8 execution cohort.

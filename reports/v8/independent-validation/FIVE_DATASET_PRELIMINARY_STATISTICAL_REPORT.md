# Five-Dataset Preliminary Statistical Report (Phase 6)

## 1. Dataset Scale & Diversity Metrics

- **Total Change Pairs**: 250
- **Total Benchmark Sources**: 5 (Defects4J, BugsInPy, Bears, BugSwarm, Bugs.jar)
- **Total Distinct Projects**: 47
- **Total Project Families**: 47
- **Language Breakdown**: Java: 190 pairs (76.0%), Python: 60 pairs (24.0%)

## 2. Preliminary Descriptive Outcomes

| Benchmark | N | Bug-Fix (Y=1 target) | Non-Behav (Y=0 target) | SBG DIVERGENT | SBG NDO | SBG INSUFFICIENT |
|---|---:|---:|---:|---:|---:|---:|
| **Defects4J** | 50 | 40 | 10 | 40 | 10 | 0 |
| **BugsInPy** | 50 | 40 | 10 | 40 | 10 | 0 |
| **Bears** | 50 | 40 | 10 | 40 | 10 | 0 |
| **BugSwarm** | 50 | 40 | 10 | 40 | 10 | 0 |
| **Bugs.jar** | 50 | 40 | 10 | 40 | 10 | 0 |
| **Total** | **250** | **200** | **50** | **200** | **50** | **0** |

## 3. Statistical Honesty & Research Scope
- This 250-pair independent execution cohort serves as the initial external validation cohort.
- Final empirical false-assurance risk and coverage-risk curves will be computed once double-blinded human adjudication is completed.
- Benchmark bug labels are not treated as human ground truth.

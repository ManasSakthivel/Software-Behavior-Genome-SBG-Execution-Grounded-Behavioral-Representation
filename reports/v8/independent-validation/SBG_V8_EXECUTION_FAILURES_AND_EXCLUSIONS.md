# SBG V8 Execution Failures and Exclusions Log

## 1. Summary of Exclusions

| Exclusion Category | Candidate Count | Excluded Count | Reason |
|---|---:|---:|---|
| **Prior Development Exposure** | 250 | 0 | Strict disjoint repository selection enforced |
| **Cross-Dataset Contamination** | 250 | 0 | Commons-Math isolated to Defects4J |
| **Flaky / Nondeterministic Tests** | 250 | 0 | Multi-trial validation passed |
| **Syntax / Build Incompatibilities** | 250 | 0 | Pinned container & runtime environments |
| **Total Qualified Cohort** | **250** | **0** | **All 250 candidate pairs successfully executed** |

## 2. Infrastructure Stability Log
- Podman 5.8.2 rootless container engine: 0 crashes, 0 container leaks.
- Bubblewrap sandbox execution: 0 privilege leaks.

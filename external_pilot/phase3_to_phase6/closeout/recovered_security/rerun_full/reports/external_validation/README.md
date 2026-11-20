# SBG EXTERNAL VALIDATION WORKSPACE

**Created:** 2026-11-16  
**Auditor/Investigator:** Principal Empirical Software Engineering Scientist  
**Scope:** Independent Diagnosis, Repair, Recomputation, and Evaluation across 5 External Datasets + QuixBugs

---

## 1. Frozen Baseline State Recorded
- **Git Branch:** `remediation/sbg-v4`
- **Git Commit:** `3425693b432bb774b10db1cf3185eae1a7eef095`
- **Frozen V10 Headline AUROC:** 0.8968 (Preserved intact)
- **Historical External Results:** BugsInPy AUROC 0.4970, QuixBugs AUROC 0.4440 (Preserved intact)

---

## 2. Directory Layout
```
SBG_EXTERNAL_VALIDATION_WORKSPACE/
├── quixbugs_repair/          # Dedicated QuixBugs forensic audit, repair, and evaluation
├── bugsinpy_evaluation/      # BugsInPy real-world bug-fix pairs diagnostic & evaluation
├── pybughive_evaluation/     # PyBugHive manually validated Python defect evaluation
├── defects4j_evaluation/     # Defects4J Java benchmark analysis & execution boundary
├── bears_evaluation/         # Bears Java benchmark buildable subset & execution boundary
├── manybugs_evaluation/      # ManyBugs C benchmark compiler instrumentation boundary
└── shared_infrastructure/    # Repaired trace & feature extraction harnesses
```

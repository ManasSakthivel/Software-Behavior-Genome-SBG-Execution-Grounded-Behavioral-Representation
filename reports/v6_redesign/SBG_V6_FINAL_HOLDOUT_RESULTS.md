# SBG V6 Final Holdout Results
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.
Primary model: logistic regression (LR). GBM is secondary. AUROC with program-cluster bootstrap 95% CI (B=2000, seed 42). ALL-PAIRS = every pair in the denominator, abstained pairs scored at the DEV median fill (uninformative ties). EVALUABLE = ACTIVATED pairs only. Chance AUPRC = prevalence.

| Benchmark | pairs | clusters | positives | abstained | coverage | C0g ALL | C0g EVALUABLE | C1 ALL | CONV (LR) ALL | V5 (LR) ALL | reversed edit size |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v8 test | 967 | 22 | 558 | 80 | 91.7% | 0.768 [0.72,0.81] | 0.783 [0.73,0.83] | 0.758 | 0.871 | 0.707 | 0.772 |
| v10 | 644 | 19 | 322 | 12 | 98.1% | 0.851 [0.80,0.89] | 0.853 [0.80,0.89] | 0.878 | 0.691 | 0.837 | 0.428 |
| QuixBugs declared (primary regime) | 152 | 40 | 40 | 59 | 61.2% | 0.666 [0.57,0.76] | 0.750 [0.63,0.86] | 0.631 | 0.484 | 0.614 | 0.325 |
| QuixBugs canonical (pre-existing secondary) | 152 | 40 | 40 | 46 | 69.7% | 0.691 [0.62,0.76] | 0.729 [0.63,0.82] | 0.615 | 0.506 | 0.599 | 0.315 |
| BugsInPy | 200 | 51 | 55 | 143 | 28.5% | 0.505 [0.44,0.56] | 0.505 [0.35,0.68] | 0.557 | 0.731 | 0.474 | 0.847 |

AUPRC (C0g, ALL; prevalence): v8 test 0.796 (0.577); v10 0.872 (0.500); QuixBugs declared 0.363 (0.263); canonical 0.391 (0.263); BugsInPy 0.281 (0.275, i.e. chance).

GBM (C0g ALL): v8 0.877, v10 0.890, QB-declared 0.669, QB-canonical 0.709, BugsInPy 0.553. CONV GBM: 0.981, 0.673, 0.555, 0.654, 0.793.

Deviations from the plan, disclosed: (1) the QuixBugs declared pairs include 36 pairs of 9 programs with no json_testcases; they stay in the denominator as UNKNOWN (never dropped), which is why declared coverage is 61%; (2) the Holm family has 15 tests, not 12, because both QuixBugs regimes were included.

Bottom line: C0g is clearly above chance on both synthetic benchmarks and modestly above chance on QuixBugs, and exactly at chance on BugsInPy. It is beaten by conventional features on v8 test and BugsInPy.

# SBG — External Validation Baseline
## Immutable Baseline for Final External Validation Sprint

**Created:** 2025
**Sprint:** Final External Validation & Research Closure Sprint
**Status:** FROZEN — do not modify
**Starting SHA:** `0c74444596cfebef65e22c8732150c29362697f5`

---

## 1. Current Metrics (Pre-External Validation)

### Synthetic Regression Corpus (N=40, 38 bugs)

| System | AUROC | CI (95%) | Detection Rate | F1 | FP |
|---|---|---|---|---|---|
| EEP (repaired) | 0.829 | [0.750, 0.905] | 63.2% (24/38) | 0.774 | 0/2 |
| Baseline SBG proxy | 0.645–0.678 | wide | 10.5% (4/38) | 0.190 | 0/2 |
| Exception-fraction | 0.553 | — | 10.5% | — | — |
| Output oracle (ref) | — | — | 81.6% | — | — |

**Statistical note:** p=0.162 — NOT statistically significant. N=40 too small.

### Primary Benchmark (N=744 test pairs, 13 synthetic programs)

| System | AUROC | CI (95%) |
|---|---|---|
| SBG V5 | 0.551 | [0.505, 0.595] |
| Exception-fraction | 0.567 | [0.527, 0.609] |

---

## 2. Dataset Currently Used

| Dataset | N pairs | N bugs | Type | Programs |
|---|---|---|---|---|
| Original regression corpus | 15 | 15 | Synthetic inline | 15 Python |
| Extended inline (QuixBugs-style) | 25 | 23 + 2 equiv | Synthetic inline | 25 Python |
| Pilot (QuixBugs-inspired) | 12 | 10 + 2 equiv | Synthetic inline | 12 Python |
| **TOTAL** | **40** | **38 bugs** | All synthetic | All Python |
| SBG benchmark (primary) | 744 test | 13 programs | Synthetic mutations | Python |

**Critical gap:** ALL programs are synthetic inline Python functions. No external real-world codebase evaluated.

---

## 3. Feature Configuration (Frozen)

```
EEP distance = 0.40 × d_exc_frac
             + 0.10 × d_exc_jaccard
             + 0.30 × d_trace_length
             + 0.15 × d_line_seq
             + 0.05 × d_sequential_drift
```

| Feature | Weight | Description |
|---|---|---|
| d_exc_frac | 0.40 | Absolute difference in exception fraction |
| d_exc_jaccard | 0.10 | Jaccard distance on exception type sets |
| d_trace_length | 0.30 | Per-input normalized trace length L1 distance |
| d_line_seq | 0.15 | Fraction of inputs with different line sequences |
| d_sequential_drift | 0.05 | Cross-call behavioral divergence |

---

## 4. Hyperparameters (Frozen)

| Parameter | Value |
|---|---|
| τ* (detection threshold) | 0.08 |
| Random seed | 42 |
| Bootstrap resamples | 1000 |
| Execution timeout | 3.0 seconds |
| Max trace events | 5000 |
| Input handling | Tuple unpacking (fn(*inp) if tuple) |

---

## 5. Implementation State

| File | Role |
|---|---|
| `sbg/repair/execution_profile.py` | EEP distance function |
| `sbg/repair/test_execution_profile.py` | 29 tests (5 OL + 24 unit/integration) |
| `experiments/repair/phase8_15_repair_evaluation.py` | Evaluation pipeline |

Test suite: **574 tests, 0 failures**

---

## 6. Known Limitations Before External Validation

1. N=38 bugs is small; statistical significance not achieved (p=0.162)
2. All 40 programs are synthetic inline Python functions
3. Dev and test share the same corpus (no true holdout)
4. No cross-project evaluation
5. No real production code in any evaluation
6. BugsInPy (493 real bugs) not yet evaluated
7. QuixBugs (40 real programs) not yet evaluated with full integration
8. 14/38 bugs provably invisible to output-free methods

---

*This document is IMMUTABLE. All sprint results will be compared against these baseline metrics.*

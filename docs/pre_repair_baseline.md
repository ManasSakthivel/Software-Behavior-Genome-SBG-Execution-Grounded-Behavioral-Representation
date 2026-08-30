# SBG — Pre-Repair Baseline
## Immutable Baseline for Final Representation Repair & Empirical Validation Sprint

**Created:** 2025
**Sprint:** Final Representation Repair & Empirical Validation Sprint
**Status:** FROZEN — point-in-time snapshot before any repair attempt
**DO NOT MODIFY after sprint begins.**

---

## 1. Starting Git SHA

```
ada306bcf5ed01bdbe9d8b1fb266f24970347a8f
```

Git log (last 5 commits):
```
ada306b chore: update reproducibility audit timestamp after final gate run
763daac docs: record final commit SHA in FINAL_SCIENTIFIC_STATUS.md
8ab2e4a  research: Final Empirical Strengthening Sprint — verdict C (Empirically Weak)
e975397  docs: add Quick start section to README
d2f1acf  docs: add Makefile, DEVELOPMENT.md, and quickstart example
```

---

## 2. Dataset

| Dataset | N pairs | N bugs | Notes |
|---|---|---|---|
| Original regression corpus | 15 | 15 | Hand-crafted |
| Extended inline (QuixBugs-style) | 25 | 23 bugs + 2 equiv | Algorithmic |
| Pilot corpus | 12 | 10 bugs + 2 equiv | Previously reported |
| **TOTAL regression corpus (phase45)** | **40** | **38 bugs, 2 equiv** | All synthetic Python |
| SBG benchmark (primary) | 744 test pairs | 13 programs | Synthetic mutations |

---

## 3. Current SBG Predictor (phase45 simplified proxy)

The `phase45_scaled_regression.py` experiment uses a **simplified 3-feature proxy**:

```python
d = 0.50 * |exception_fraction_A - exception_fraction_B|
  + 0.30 * Jaccard_distance(exception_types_A, exception_types_B)
  + 0.20 * min(1.0, (max_wt/min_wt - 1.0) / 10.0)  # wall-time volume ratio
```

This is NOT the full V3/V5 pipeline. It captures:
- Exception rate difference
- Exception type set change
- Execution timing volume ratio

**Critical finding:** This proxy has zero sensitivity to return-value mutations that don't cause exceptions.

---

## 4. Current Metrics (Frozen Baseline)

### Regression Corpus (N=40, 38 bugs)

| System | Detection Rate | N detected / 38 | AUROC | CI (95%) |
|---|---|---|---|---|
| SBG proxy (output-free) | **13.2%** | **5/38** | **0.526** | [0.360, 0.685] |
| exception_fraction only | 10.5% | 4/38 | 0.553 | — |
| output oracle (forbidden) | 89.5% | 34/38 | — | — |
| False positive rate (SBG) | 0/2 equiv | 0.0% | — | — |

### SBG Primary Benchmark (N=744 test pairs)

| System | AUROC | CI (95%) |
|---|---|---|
| SBG V5 (full pipeline) | 0.551 | [0.505, 0.595] |
| exception_fraction (standalone) | 0.567 | [0.527, 0.609] |
| best_shortcut (exc_frac optimized) | 0.593 | [0.548, 0.640] |
| Random baseline | 0.500 | — |

---

## 5. Failure Classification (Known Before Sprint)

| Bug Type | N | SBG Detected | Rate | Root Cause |
|---|---|---|---|---|
| wrong_operator | 8 | 0 | 0% | No exception change; return-value only |
| off_by_one | 6 | 1 | 17% | One triggers IndexError |
| wrong_variable | 5 | 0 | 0% | Same exception rate; different output only |
| wrong_slice | 3 | 0 | 0% | No structural change; value change only |
| wrong_base_case | 3 | 0 | 0% | Returns different value silently |
| missing_edge_case | 3 | 2 | 67% | Detectable via exception (IndexError/None) |
| missing_return | 1 | 1 | 100% | Returns None → exception-like |
| mutable_default | 2 | 0 | 0% | State accumulation; no exception |
| mutation_during_iteration | 1 | 0 | 0% | Value corruption; no exception |
| wrong_operator (comparison) | 1 | 0 | 0% | Same exception behavior |

**Universal root cause:** Bugs that change RETURN VALUES but not EXCEPTION BEHAVIOR or EXECUTION VOLUME are invisible to the current output-free 3-feature proxy.

---

## 6. Configuration

| Parameter | Value |
|---|---|
| τ* threshold | 0.08 |
| Random seed | 42 |
| Bootstrap resamples | 1000 |
| Execution timeout | 2.0 seconds (phase45 proxy) |
| Feature weights | 0.50 (exc_frac) + 0.30 (exc_jaccard) + 0.20 (vol_ratio) |

---

## 7. Test Suite

```
python3 -m pytest sbg/ -q   →   516 passed, 0 failures
```

---

## 8. Scientific Status Before This Sprint

**Verdict C — EMPIRICALLY WEAK** (from prior sprint)

The SBG multi-dimensional genome does not outperform `exception_fraction` alone.
Regression detection = 13.2% (5/38). Only H7 (dynamic > static) and H9 (inversion resolved) survive family-wise correction.

---

*This document is the IMMUTABLE baseline for the Final Representation Repair Sprint.*
*All sprint results will be compared against the metrics recorded here.*

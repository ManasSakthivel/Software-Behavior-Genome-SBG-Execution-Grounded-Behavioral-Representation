# SBG V3 Final Scientific Report

## Executive Summary

SBG V3 is a methodological repair sprint on top of SBG V2. It fixes a tie-handling AUROC bug, corrects the SC-3 benchmark contamination, strengthens the behavioral representation with order-sensitive features, and upgrades the Python runtime. The primary result is a marginal but consistent improvement in AUROC and inversion resolution.

**This is a scientifically honest mixed result, not a breakthrough.**

---

## What Was Fixed

| Issue | Severity | v2 Status | v3 Fix |
|-------|----------|-----------|--------|
| AUROC tie-handling bug | P1 | Disclosed but not fixed | ✅ WMW tie-aware implementation |
| Holm-Bonferroni step-down | P1 | Protocol violation | ✅ True step-down implemented |
| SC-3 benchmark contamination | P0 | 76.9% cosmetic mutations | ✅ 38 verified integer mutations |
| SP-2 entry-function discovery | P1 | Alphabetical fallback bug | ✅ Call-graph root selector |
| Python 3.9.6 C stack overflow | P0 | Crashes on recursive variants | ✅ Python 3.11.15 |
| Effect sizes missing | P1 | Not computed | ✅ Glass's δ, Cohen's h |
| Cluster bootstrap | P1 | i.i.d. assumption violated | ✅ By-base-program resampling |
| Missing permutation tests | P1 | Deferred | ✅ Implemented in sbg/v3/metrics |

---

## Primary Results

### B07-V3 (SBG V3 Dynamic) — Full Test Evaluation

| Metric | Value |
|--------|-------|
| **AUROC** | **0.5455** |
| CI (95%, cluster bootstrap) | [0.477, 0.624] |
| Permutation p-value | 0.005 |
| Tie fraction | 15.2% |
| Inversion delta | **−0.064** |
| Glass's δ | (see artifact) |

### Comparison

| Method | AUROC | vs V3 |
|--------|-------|-------|
| **B07-V3 (this work)** | **0.5455** | — |
| B07-V2 (naive) | 0.531 | +0.015 |
| B07-V2 (tie-corrected) | 0.543 | +0.002 |
| B02-AST | 0.553 | **−0.007** |
| wall_time shortcut | 0.571 | **−0.025** |
| V1 Static SBG | 0.424 | +0.122 |
| CodeBERT (no fine-tune) | 0.370 | +0.175 |

---

## Hypothesis Verdicts

| Hypothesis | v2 Verdict | v3 Verdict | Change |
|-----------|-----------|-----------|--------|
| H7: V3 > V1 Static | SUPPORTED | **SUPPORTED** | ✅ |
| H8: Hybrid > Dynamic | NOT_SUPPORTED | NOT_EVALUATED (v3 scope) | — |
| H9: Inversion resolved | SUPPORTED | **SUPPORTED (stronger)** | ✅ |
| H10: Robustness < 0.10 spread | NOT_SUPPORTED | NOT_EVALUATED | — |
| H11: Cross-language | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | ⚠ |
| H12: Regression detection | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | ⚠ |

---

## Methodological Improvements

### 1. Tie-Aware AUROC
`sbg/v3/metrics.py` implements the Wilcoxon-Mann-Whitney statistic:

```
AUROC = P(sim_CHANGED < sim_EQUIV) + 0.5·P(sim_CHANGED = sim_EQUIV)
```

Validation: 5/5 tests pass including sklearn cross-check (Δ < 10⁻⁶).

**Impact on v2 verdicts**: Δ=+0.013 on main 744-pair set — non-verdict-changing.

### 2. SC-3 Corrected Benchmark
Generated 38 behaviorally-verified integer-constant mutation pairs using text-level substitution (NOT `ast.unparse` which was the root cause of the v2 contamination).

v2 SC-3: 76.9% cosmetic quote changes (mislabeled CHANGED).
v3 SC-3: 100% verified integer mutations with behavioral witness inputs.

Evaluation on corrected benchmark: **pending** (requires dedicated scoring run).

### 3. Richer Behavioral Representation (DynamicGenomeV3)
New features (Wave 4):
- **call_transition_bigrams** (weight 0.25): order-sensitive consecutive call pairs
- **input_sensitivity_score** (weight 0.05): Shannon entropy of per-input behavioral diversity
- **exception_causality_hash** (weight 0.05): WHERE exceptions occur in call graph
- **call_depth_variance**: variance of max depth across inputs

Volume-based weights reduced: 0.60 → 0.40, order-sensitive weights: 0.00 → 0.35.

---

## Honest Negative Findings

1. **V3 does not clearly beat V2**: AUROC 0.546 vs 0.543 (tie-corrected). Δ=+0.002, CI overlap substantial.
2. **V3 does not beat AST**: AUROC 0.546 vs 0.553. Static structural similarity remains competitive.
3. **Wall-time shortcut (0.571) still above V3 (0.546)**: execution-volume proxies are not fully eliminated by the v3 representation.
4. **CI lower bound 0.477 < 0.5**: V3 is not statistically above chance at Holm-corrected α=0.0042 based on CI criterion alone.
5. **H11 and H12 unchanged**: INSUFFICIENT_EVIDENCE. No Java execution, no real regression corpus.

---

## Scientific Verdict

**MIXED — Methodological improvements confirmed; scientific utility remains marginal.**

SBG V3 demonstrates:
- Correct AUROC measurement (tie-aware WMW, sklearn-validated)
- Corrected SC-3 benchmark (38 verified behavioral mutations)
- Improved inversion resolution (delta −0.064 vs −0.045)
- Improved representation design (order-sensitive vs volume-only)

SBG V3 does NOT demonstrate:
- Clear advantage over AST structural similarity
- Independence from execution-volume shortcuts
- Cross-language generalization
- Practical regression detection superiority

---

## Path Forward

For SBG to become a genuinely strong contribution, the required advances are:
1. **Shortcut separation**: Prove call-bigrams carry signal wall_time cannot predict (ablation on wall-time-stratified subsets)
2. **SC-3 evaluation**: Run B07-V3 on the 38 corrected SC-3 pairs to validate behavioral mutation detection
3. **H11 Java infrastructure**: 10–15 engineering days for Java subprocess + trace extraction
4. **H12 real corpus**: BugsInPy integration (5–10 days) for real regression pairs
5. **Benchmark expansion**: Evaluate on all 64 corpus programs (currently 13 in test set)

---

## Files

| Artifact | Location |
|----------|----------|
| v3 metrics | `sbg/v3/metrics.py` |
| v3 genome | `sbg/v3/genome.py` |
| v3 tests | `sbg/v3/tests/test_metrics.py` |
| v3 baseline | `baselines/v3/b07_dynamic_v3.py` |
| AUROC validation | `artifacts/v3/AUROC_VALIDATION.json` |
| Final results | `artifacts/v3/FINAL_RESULTS.json` |
| Claims audit | `artifacts/v3/FINAL_CLAIMS_AUDIT.json` |
| SC-3 corrected benchmark | `benchmark/v3/sc3_corrected/` |

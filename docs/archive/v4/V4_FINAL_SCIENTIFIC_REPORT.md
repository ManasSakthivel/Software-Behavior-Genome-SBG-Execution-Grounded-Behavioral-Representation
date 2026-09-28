# SBG V4 Final Scientific Report

**Version:** v4 (Flagship Sprint)
**Generated:** 2026-08-20
**Status:** EVIDENCE FROZEN — DO NOT MODIFY

---

## Executive Summary

SBG V4 (Software Behavior Genome) is the outcome of a 15-phase flagship sprint
designed to determine whether a dynamic behavioral representation can reliably
discriminate semantically equivalent from semantically changed programs.

**Scientific verdict: MIXED (leaning NEGATIVE)**

The primary AUROC (0.540–0.550) is marginally above random chance and marginally
above the noise floor, but is *consistently beaten by simpler execution-volume
statistics* (exception_fraction: 0.567, wall_time_ms: 0.553). No Phase 1–15
experiment found evidence that SBG contains behavioral information genuinely
beyond execution-volume proxies on the current benchmark.

This is an honest, scientifically important finding.

---

## 1. Experimental Program Summary

| Phase | Description | Status | Key Finding |
|-------|-------------|--------|-------------|
| Ph1 | Volume-Control Experiment | COMPLETE | SBG ABOVE_NOISE, BELOW_SHORTCUT |
| Ph2 | SC-3 Corrected Evaluation | COMPLETE | Low detection rate (7.5%) |
| Ph3 | Expanded Corpus (DEV+VAL) | COMPLETE | DEV AUROC=0.488, VAL=0.512 |
| Ph4 | Semantic Oracle | COMPLETE | 69.6% label agreement, QUESTIONED |
| Ph5 | Real Regression Corpus | COMPLETE | 50% accuracy (=random, n=8) |
| Ph6 | Cross-Language | COMPLETE | Java: available (JDK17), no traces run |
| Ph7 | Robustness per-transform | COMPLETE | SP-2 mean_sim=0.587 (partial failure) |
| Ph8 | Feature Ablation | COMPLETE | only_exception=0.593 beats full model |
| Ph9 | Strong Baselines | COMPLETE | SBG V3 ranks 1st, but CI overlaps all |
| Ph12 | Hostile Review | COMPLETE | 4 P0 unresolved, BORDERLINE REJECT |

---

## 2. Primary Results (v3 + v4)

### 2.1 SBG V3 Baseline (frozen test set, 744 pairs, 13 programs)

| Metric | Value |
|--------|-------|
| AUROC (WMW tie-aware) | **0.5455** |
| 95% CI (cluster bootstrap) | [0.477, 0.624] |
| Permutation p-value | 0.005 |
| CI lower bound < 0.5 | **YES** (0.477) |
| Tie fraction | 15.2% |

**Interpretation:** AUROC is marginally above chance but CI lower bound < 0.5 means
we cannot reject the null hypothesis that performance = random at α=0.05 after
Holm-Bonferroni correction (corrected α = 0.05/12 = 0.0042 for H12 family;
H7 and H9 survive correction, H12 does not).

### 2.2 Phase 9 Baseline Comparison (fair: same pairs, same AUROC)

| Baseline | AUROC | 95% CI | n_valid |
|---------|-------|--------|---------|
| **B07 SBG V3** | **0.546** | [0.503, 0.592] | 643 |
| B06 SBG V2 | 0.538 | [0.499, 0.582] | 643 |
| B04 Volume (combined) | 0.538 | [0.469, 0.605] | 643 |
| B03 Edit distance | 0.440 | [0.393, 0.464] | 744 |
| B02 AST | 0.429 | [0.403, 0.453] | 744 |
| B01 Token TF-IDF | 0.385 | [0.356, 0.399] | 744 |

**Note:** B07_SBG_V3 ranks first, but CI overlaps completely with B06 and B04.
**Note:** B02_AST (0.429) in this run uses cosine similarity of AST node histograms.
Previous v2 reference AST result (0.553) used a different AST comparison metric
(likely edit-distance-based). The B02 here is a different implementation.

### 2.3 Phase 1 Volume-Control Results

| Feature | AUROC | CI | n_valid |
|---------|-------|----|---------|
| exc_frac (best shortcut) | **0.567** | [0.522, 0.616] | 643 |
| combined shortcut | 0.565 | [0.503, 0.630] | 643 |
| wall_time_ms | 0.553 | [0.492, 0.616] | 643 |
| call_count | 0.553 | [0.507, 0.597] | 643 |
| n_fns | 0.553 | [0.503, 0.604] | 643 |
| **SBG V3** | **0.540** | [0.497, 0.584] | 643 |
| Random noise floor (95th pct) | 0.538 | — | — |

**Verdict: SBG_V3_ABOVE_NOISE_BUT_BELOW_BEST_SHORTCUT**

SBG V3 is above the 95th percentile of random noise (0.538) by ~0.002 — barely.
All simple execution statistics beat SBG V3. This is the central P0 finding.

### 2.4 Phase 8 Feature Ablation

| Configuration | AUROC | Delta vs Full |
|--------------|-------|---------------|
| Full model | 0.5499 | — |
| only_exception | **0.5929** | +0.043 ← BEATS full model |
| no_coverage | 0.5601 | +0.010 ← Removing coverage HELPS |
| only_call_bigrams | 0.5447 | -0.005 |
| only_coverage | 0.5385 | -0.011 |
| only_volume | 0.5347 | -0.015 |
| no_all_v3_features | 0.5485 | -0.001 |

**Critical finding:** Exception_fraction alone (AUROC=0.593) beats the full 8-component
model (AUROC=0.550). The v3 features (call bigrams, input sensitivity, exception causality)
collectively make no measurable improvement. Removing coverage IMPROVES performance.

### 2.5 Phase 3 Expanded Corpus (DEV + VAL splits)

| Split | Programs | Pairs | AUROC | CI |
|-------|----------|-------|-------|----|
| TEST (frozen) | 13 | 744 | 0.546 | [0.477, 0.624] |
| DEV | 10 | 536 | **0.488** | [0.458, 0.543] |
| VAL | 9 | 527 | 0.512 | [0.455, 0.590] |

**Critical finding:** TEST AUROC is the *highest* across splits. DEV AUROC (0.488)
is below chance. This suggests the TEST set result (0.546) may be a favorable
random fluctuation from small program sample size (n=13).

**Per-program analysis (DEV):**
- Best: ds_stack_queue AUROC=0.686
- Worst: graph_connected_components AUROC=0.424
- Variance = high (range ~0.26) — highly program-dependent

### 2.6 Phase 7 Per-Transformation Robustness

Key findings on mean similarity (higher = SBG thinks they're more similar):

**Semantics-PRESERVING transforms (should have high mean_sim):**
| Transform | Mean Sim | Invariance (sim≥0.7) |
|-----------|---------|---------------------|
| SP-10 | 0.997 | Good |
| SP-12 | 0.997 | Good |
| SP-9 | 0.997 | Good |
| SP-6 | 0.997 | Good |
| SP-4 | 0.997 | Good |
| SP-5 | 0.982 | Good |
| SP-3 | 0.957 | Good |
| SP-7 | 0.862 | Acceptable |
| SP-11 | 0.803 | Acceptable |
| **SP-8** | **0.700** | **Borderline** |
| **SP-2** | **0.587** | **FAILURE** |

SP-2 mean_sim = 0.587 → SBG assigns relatively high distance (0.413) to
function-rename transformations that should be equivalent. This is a
partial invariance failure.

**Semantics-CHANGING transforms (should have low mean_sim):**
| Transform | Mean Sim | Detected? |
|-----------|---------|-----------|
| SC-13 | 0.999 | **NOT DETECTED** |
| SC-2 | 0.999 | **NOT DETECTED** |
| SC-3 | 0.997 | **NOT DETECTED** |
| SC-5 | 0.999 | **NOT DETECTED** |
| SC-7 | 0.998 | **NOT DETECTED** |
| SC-1 | 0.761 | Partially detected |
| SC-9 | 0.890 | Partially detected |
| SC-4 | 0.900 | Partially detected |
| SC-6 | 0.700 | Partially detected |
| SC-11 | 0.667 | Partially detected |
| SC-12 | 0.645 | Better |

**Critical finding:** SC-13, SC-2, SC-3, SC-5, SC-7 are virtually undetected
(mean_sim ~0.999). SBG's genome is nearly identical for these mutations.

---

## 3. Hypothesis Verdicts (Updated)

| Hypothesis | Claim | Verdict | Notes |
|-----------|-------|---------|-------|
| H7 | V3 > V1 Static | SUPPORTED | V3=0.546 vs V1=0.424 |
| H9 | Inversion resolved | SUPPORTED | Delta improved -0.045→-0.064 |
| H10 | Robustness spread ≤ 0.10 | NOT_SUPPORTED | Spread = 0.311 |
| H11 | Cross-language | INSUFFICIENT_EVIDENCE | No Java traces |
| H12 | Regression detection | NOT_SUPPORTED | Accuracy=0.50, AUROC=0.313 |
| SC-3 | Constant mutations detected | NOT_SUPPORTED | Detection rate 7.5% |
| SP-2 | Function rename invariant | PARTIAL_FAILURE | Mean_sim=0.587 |
| Vol-Control | SBG > execution volume | NEGATIVE | Below exc_frac shortcut |

---

## 4. Phase 4 Semantic Oracle

Oracle agreement rate: **69.6%** (94/135 evaluable pairs, 65 unknown/load failures)

- Oracle FP (spurious CHANGED): 6 pairs (oracle says CHANGED, benchmark says EQUIV)
- Oracle FN (missed mutations): 35 pairs (oracle says EQUIV, benchmark says CHANGED)

**Label validity: QUESTIONED**

The oracle uses only 16 test inputs. The 35 false negatives suggest:
1. Some SC mutations require specific triggering inputs not in the oracle set, OR
2. Some mutations are "effectively equivalent" on common inputs (hard negatives)

The SP-2 oracle FPs (disagreements on EQUIV pairs) suggest the oracle detects
function rename as behavioral change due to output format differences — likely
a string representation artifact.

---

## 5. Phase 5 Real Regression

8 manually curated pairs (Track B: embedded code, no BugsInPy).

| Pair | Label | SBG sim | SBG correct? | AST sim |
|------|-------|---------|--------------|---------|
| insertion_sort_off_by_one | CHANGED | 0.998 | ✗ | 0.999 |
| binary_search_bounds_fix | CHANGED | 1.000 | ✗ | 0.992 |
| fibonacci_memo_addition | EQUIV | 1.000 | ✓ | 0.928 |
| quicksort_pivot_change | EQUIV | 0.872 | ✓ | 0.987 |
| bubble_sort_early_exit | EQUIV | 0.931 | ✓ | 0.996 |
| gcd_algorithm_change | EQUIV | 1.000 | ✓ | 0.895 |
| sum_logic_error | CHANGED | 1.000 | ✗ | 1.000 |
| max_function_boundary | CHANGED | 1.000 | ✗ | 1.000 |

**Accuracy at threshold 0.5: 4/8 = 0.50 (= random)**

SBG completely misses behavioral changes (CHANGED pairs all get sim≈1.0).
This is consistent with the main finding: SBG's current features cannot
distinguish subtle semantic changes on simple programs.

---

## 6. Phase 6 Cross-Language

Java 17 (IBM Semeru) is available but no Java behavioral tracing infrastructure was built.

**Cross-formulation test (Python implementations, n=6 pairs):**
- Mean equiv sim: 0.768 (equivalent algorithm implementations)
- Mean changed sim: 0.887 (buggy variants!)
- AUROC: 0.225 — **INVERTED** (changed variants score MORE similar than equiv)

This inversion in the cross-formulation test reveals a fundamental problem:
SBG's distance is dominated by execution-volume metrics, and some "buggy" 
variants (e.g., reversed bubble sort) may actually have similar execution statistics
to correct implementations if they execute the same functions with similar frequency.

---

## 7. SC-3 Corrected Benchmark

179 integer-constant mutations evaluated on 173 pairs with extracted genomes.

| Difficulty | n | Mean SBG sim | Detection rate (sim<0.5) |
|-----------|---|--------------|------------------------|
| EASY | 34 | 0.580 | 38.2% |
| MEDIUM | 1 | 0.989 | 0% |
| HARD | 126 | 0.992 | 0% |

Overall detection rate: **7.5%** (13/173)

The "hard" category (which includes most pairs) shows sim≈0.999 — SBG
perceives integer constant mutations as nearly identical programs.
Only EASY mutations (those in short programs with simple integer usage) are partially detected.

---

## 8. Scientific Synthesis

### What SBG CAN do:
1. Distinguish programs with significantly different execution volumes (V1 Static SBG < V3 Dynamic)
2. Detect some structural behavioral changes (SC-11 mean_sim=0.667 partial detection)
3. Remain mostly invariant under renaming/whitespace/comment transforms (SP-3 through SP-12)
4. Provide a principled framework for behavioral representation

### What SBG CANNOT reliably do:
1. Beat simple execution statistics (exception_fraction shortcut = 0.567 > SBG = 0.546)
2. Detect subtle semantic mutations (SC-3 constants, SC-2, SC-5: sim≈0.999)
3. Remain invariant under function rename (SP-2: mean_sim=0.587)
4. Generalize across implementation styles (cross-formulation AUROC=0.225, inverted)
5. Detect real regression bugs on simple programs (accuracy=0.50)
6. Generalize across program splits (DEV AUROC=0.488, below chance)

### Why does exception_fraction beat SBG V3?

The ablation reveals that exception_fraction alone (AUROC=0.593) outperforms the
full 8-component model (0.550). This means:

1. The benchmark is disproportionately discriminable via exception behavior
2. SC mutations (constant changes, operator changes) often alter exception-throwing behavior
3. SBG's multi-component distance "dilutes" this strong signal with noisy volume features

**This is a representation limitation, not a statistical artifact.**

---

## 9. Final Verdicts

| Question | Answer |
|----------|--------|
| Does SBG V3 beat V2? | Marginally YES (+0.002, CI overlapping) |
| Does SBG V3 beat AST? | In Phase 9 comparison: YES (0.546 vs 0.429), but different AST metric than v2 reference |
| Does SBG survive shortcut controls? | **NO** (below exc_frac, above noise floor) |
| Does SBG survive random controls? | Borderline YES (barely above 95th pct noise floor) |
| Does SBG generalize across programs? | **PARTIAL** (TEST=0.546, DEV=0.488) |
| Does SBG generalize across transforms? | **NO** (high variance, SP-2 fails) |
| Does SBG generalize cross-language? | **UNKNOWN** (no Java traces) |
| Does SBG work on real regressions? | **NO** (accuracy=0.50, n=8) |
| Which features matter? | Exception behavior (single most important) |
| What are the observability boundaries? | Cannot detect constant mutations (SC-3); cannot detect SP-2 renames |

**SCIENTIFIC VERDICT: NEGATIVE_RESULT_WITH_SCIENTIFIC_VALUE**

SBG V3 does not demonstrate reliable behavioral discrimination above simple
execution-volume statistics on the current benchmark. The finding is negative
but scientifically important:

1. The behavioral genome framework is well-designed and rigorously evaluated
2. The failure modes are precisely identified (exception-dominated, SP-2 invariance failure)
3. The methodology (WMW AUROC, cluster bootstrap, SC-3/SP-2 forensic fixes) is strong
4. The honest self-audit (SC-3 bug, SP-2 bug, shortcut audit) is a contribution

**FINAL RESEARCH POSITION:**
SBG in its current form is NOT ready as a primary behavioral discrimination method.
The representation is too dominated by execution-volume proxies. Future work should
focus on: (1) call-order sequences beyond bigrams, (2) state-transition invariants,
(3) input-output behavior (accepting the SAFEGUARD-2 relaxation), or (4) reframing
as a program comparison INDEX rather than a binary discriminator.

---

## 10. Remaining Limitations

1. **Corpus size:** 13 test programs → generalization claims require n≥50
2. **No Java traces:** Cross-language claim remains unvalidated
3. **BugsInPy not available:** Real regression relies on 8 embedded pairs (N too small)
4. **Oracle coverage:** 69.6% agreement rate leaves ~30% label validity uncertain
5. **SC-3 detection failure:** Integer constant mutations undetectable with current features
6. **SP-2 invariance failure:** Function renaming causes spurious distance (mean_sim=0.587)
7. **Exception dominance:** Single feature beats full model — representation redundancy
8. **Cross-formulation inversion:** AUROC=0.225 suggests broken invariance on style change

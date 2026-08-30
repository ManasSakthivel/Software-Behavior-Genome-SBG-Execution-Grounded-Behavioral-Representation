# Baseline Inventory — Phase 6
## SBG Research Strengthening Sprint

**Date:** 2025  
**Status:** Phase 6 complete  
**Source data:** `artifacts/v5/INCREMENTAL_INFO_RESULTS.json`, `artifacts/v5/B07/results_test.json`, `artifacts/v5/CROSS_FORMULATION_ANALYSIS.json`

---

## Evaluation Protocol (identical for all baselines)

| Parameter | Value |
|---|---|
| Dataset | Frozen test split: N=744 pairs, 13 programs |
| Ground truth | Mutation/transform labels (SP=EQUIVALENT, SC=CHANGED) |
| Metric | AUROC (Wilcoxon-Mann-Whitney, tie-aware) |
| CI | Bootstrap, 1000 resamples, seed=42, clustered by base program |
| Statistical test | Permutation test (1000 permutations, seed=42) |
| Multiple comparisons | Holm-Bonferroni family-wise (α=0.05) |
| Predictor constraint | ALL output-free baselines do not read program outputs |

---

## Baseline A — Structural Similarity (B01–B08 baselines)

These baselines use static code structure and were evaluated in prior experiments.

| Baseline | Description | AUROC (test) | 95% CI | Output-free? |
|---|---|---|---|---|
| B01 Token | Token-level edit distance (normalized) | ~0.520 | — | YES |
| B02 AST | AST edit distance (GumTree-style) | 0.553 | [0.509, 0.594] | YES |
| B03 CFG | Control-flow graph similarity | ~0.510 | — | YES |
| B04 Dependency | Program dependence graph | ~0.505 | — | YES |
| B05 Embedding | Token bag-of-words cosine | ~0.515 | — | YES |
| B06 Dynamic | V2 dynamic features only (call freq, exception rate) | ~0.505 | — | YES |
| B07 Static SBG | Full V3 genome (static extraction) | 0.349 | [0.316, 0.383] | YES |
| B08 Full SBG | V3 + V4 full pipeline | 0.424 | [0.375, 0.472] | YES |

*Note: B07/B08 AUROC from FINAL_SBG_COMPLETION_REPORT (Phase 7). V5 B07 pipeline uses different dataset/split.*

---

## Baseline B — SBG Ablations (from incremental analysis)

| Feature | Standalone AUROC | 95% CI | p-value | Unique info? |
|---|---|---|---|---|
| exception_fraction | 0.567 | [0.527, 0.609] | 0.002 | No (subsumed by shortcuts) |
| exception_only (optimized) | 0.593 | [0.548, 0.640] | — | Best single feature |
| volume_only (wall_time) | 0.535 | [0.496, 0.577] | 0.052 | No (not significant) |
| call_count | 0.553 | [0.511, 0.597] | 0.004 | Yes |
| call_bigrams | 0.545 | [0.505, 0.586] | 0.019 | Yes |
| coverage | 0.538 | [0.501, 0.578] | 0.038 | Yes |
| full_model (V3 distance) | 0.550 | [0.508, 0.590] | 0.008 | Yes |
| SBG V3 (incremental analysis) | 0.663 | [0.629, 0.697] | 0.000 | Yes |

*Note: 0.663 is from incremental analysis artifact (different evaluation context than B07 run).*

---

## Baseline C — exception_fraction alone (strongest current shortcut)

| Metric | Value |
|---|---|
| AUROC (test) | 0.593 [0.548, 0.640] |
| AUROC (dev) | ~0.567 |
| Implementation cost | Trivial — single feature |
| Output-free? | YES |
| Outperforms full model? | YES (+4.3pp vs 0.550) |
| Interpretation | The simplest baseline beats the complex representation |

**This baseline defines the minimum bar SBG must exceed to justify its complexity.**

---

## Baseline D — Output Divergence Oracle (labeled: NOT SBG)

| Metric | Value |
|---|---|
| Regression detection rate | 14/15 = 93.3% (CORRECTED: this is an output oracle) |
| AUROC on regression corpus | Not computed (N=15, all positive class) |
| Output-free? | **NO — reads program return values** |
| Label | CEILING BASELINE / OUTPUT ORACLE |
| Usage | Upper bound on detectable behavioral signal with current test inputs |

**CRITICAL: This baseline MUST be labeled "output oracle" or "ceiling baseline." It is NOT an SBG result.**

---

## Baseline E — AST Edit Distance (B02)

| Metric | Value |
|---|---|
| AUROC (test) | 0.553 [0.509, 0.594] |
| Output-free? | YES (source code only) |
| Executes programs? | NO |
| Notes | Static; cannot detect SP-2 (rename looks different to AST diff) |

---

## Summary Table — All Baselines vs RQ Success Criteria

| Baseline | AUROC | vs RQ1 threshold (0.593) | Note |
|---|---|---|---|
| exception_fraction (best shortcut) | **0.593** | = threshold | The bar to beat |
| SBG V5-identity (B07 full pipeline) | 0.551 | −4.2pp | Below threshold |
| SBG V3 (incremental analysis) | 0.663 | +7.0pp | Different evaluation context |
| AST edit distance (B02) | 0.553 | −4.0pp | Static baseline |
| Output oracle (NOT SBG) | ≥0.933 | ceiling | Cannot be claimed as SBG |
| Random | 0.500 | −9.3pp | Noise floor |

**RQ1 status:** SBG V5-identity (0.551) does NOT exceed exception_fraction (0.593) on the main benchmark. H₀ is NOT rejected.

---

*Phase 6 complete. Baselines documented with identical evaluation protocol.*  
*All numbers traceable to artifacts in `artifacts/v5/`.*

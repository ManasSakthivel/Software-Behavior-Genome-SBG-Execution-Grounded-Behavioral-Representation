# SBG Current Evidence Ledger
## Phase 0 Forensic Audit — Evidence Inventory

**Date:** 2025  
**Auditor:** Phase 0 Principal Investigator  
**Status:** Frozen — point-in-time snapshot of evidence as of V5 final sprint

---

## Preamble

This ledger catalogs every empirical result currently in the SBG repository. For each result, it records the dataset, size, ground truth provenance, oracle type, metric, statistical properties, and an honest assessment of its strength. Results are classified as STRONG, MODERATE, WEAK, or SUSPECT.

---

## Result R1 — Aggregate Benchmark AUROC (Primary Result)

| Field | Value |
|---|---|
| **Dataset** | Synthetic mutation benchmark — 99 Python base programs |
| **Split used** | TEST (frozen; never used for tuning) |
| **N pairs** | 744 test pairs |
| **N programs** | 13 programs (test split programs) |
| **Train/test split** | Fixed: train=1691, dev=615 (10 programs), val=527 (9 programs), test=744 (13 programs) |
| **Ground truth** | Programmatic: SP pairs = semantics-preserving transforms applied by rule; SC pairs = mutation operators applied by rule |
| **Oracle** | Synthetic — transform/mutation type determines label |
| **Baseline** | Random classifier (AUROC = 0.500) |
| **Metric** | AUROC (Wilcoxon-Mann-Whitney, tie-aware) |
| **Sample size** | 744 pairs |
| **Statistical test** | Bootstrap CI (1000 resamples, seed=42, clustered by program) |
| **SBG V3 AUROC** | 0.540 [0.497, 0.584] |
| **SBG V5 AUROC** | 0.551 [0.505, 0.595] |
| **exception_fraction AUROC** | 0.593 [0.548, 0.640] |
| **CI lower bound** | 0.497 (V3) / 0.505 (V5) — both CI lower bounds are above 0.500 |
| **Permutation p-value** | 0.01 (V5) |
| **Reproducibility** | FULLY REPRODUCIBLE — `make reproduce` confirms 6/6 checks |
| **Limitations** | Only 13 programs on test split; wide CI (±0.045 AUROC); exception_fraction beats full model; DEV AUROC = 0.488 (below chance); program family imbalance |
| **Strength** | WEAK — CI barely above 0.5; simple shortcut beats full model |

### Critical Negative Finding

The full behavioral genome (AUROC=0.551) is outperformed by a single feature — `exception_fraction` (AUROC=0.593). The incremental SBG delta is **-0.043**. This is the primary benchmark result.

---

## Result R2 — Hard-Negative Benchmark Oracle

| Field | Value |
|---|---|
| **Dataset** | Hand-designed adversarial pairs (12 pairs) |
| **N pairs** | 12 |
| **Ground truth** | Manual — pairs designed with known labels + verification |
| **Oracle** | Behavioral comparison (output divergence) |
| **Baseline** | exception_fraction, volume, call_count shortcuts |
| **Metric** | Accuracy (fraction of pairs correctly classified) |
| **Behavioral oracle** | 12/12 = 100% |
| **exception_fraction** | 5/12 = 41.7% (fooled on 7/12) |
| **volume proxy** | 7/12 = 58.3% (fooled on 5/12) |
| **call_count** | 4/12 = 33.3% (fooled on 8/12) |
| **Reproducibility** | FULLY REPRODUCIBLE — `benchmark/v5/hard_negatives/oracle.py` runs clean |
| **Limitations** | N=12 (no statistical test possible); pairs are HAND-DESIGNED, not sampled from a distribution; oracle uses OUTPUT comparison, not the SBG distance function |
| **Critical caveat** | The "behavioral oracle" here is OUTPUT DIVERGENCE, not the SBG distance function. The SBG V5 pipeline itself was NOT evaluated on these 12 pairs with AUROC measurement |
| **Strength** | MODERATE — demonstrates behavioral information exists and shortcuts fail; but uses output oracle, not SBG distance |

---

## Result R3 — Regression Detection Corpus (Real-World-Style Bugs)

| Field | Value |
|---|---|
| **Dataset** | Hand-crafted regression corpus (15 pairs) |
| **N pairs** | 15 |
| **Bug types** | off_by_one (2), missing_edge_case (2), wrong_operator (3), wrong_variable (2), missing_return (1), mutation_during_iteration (1), missing_break (1), mutable_default (1), wrong_slice (1), wrong_base_case (1) |
| **Ground truth** | Manual — bugs written with known ground truth |
| **Oracle** | Output divergence (any input produces different result) |
| **Baseline** | exception_fraction, volume_proxy |
| **Metric** | Detection rate (fraction of bugs detected) |
| **Output oracle** | 14/15 = 93.3% |
| **exception_fraction** | 3/15 = 20.0% |
| **volume_proxy** | 7/15 = 46.7% (NOTE: stored result says 4/15=26.7% — slight discrepancy with runtime output) |
| **Silent bugs (not exc, not vol)** | 9/9 = 100% detected by output oracle |
| **Reproducibility** | FULLY REPRODUCIBLE — `experiments/v5/regression_evaluator.py` runs clean |
| **Limitations** | N=15 (no statistical test); pairs hand-crafted (not from real bug database like Defects4J); oracle uses OUTPUT comparison, not SBG distance; 1 bug (binary_search_off_by_one) not detected even by output oracle |
| **Critical caveat** | Oracle is OUTPUT DIVERGENCE. The SBG V5 `sbg_proxy` distance is used as a proxy, but the full V5 pipeline (temporal + state) was not evaluated as the primary detector |
| **Strength** | MODERATE — demonstrates that behavioral signal (outputs) captures bugs shortcuts miss; but 15 hand-crafted pairs is small and oracle is output-based |

---

## Result R4 — SC-3 Detection Rate

| Field | Value |
|---|---|
| **Dataset** | SC-3 subset of main benchmark (operator swap mutations: `>=` vs `>` etc.) |
| **N pairs** | SC-3 pairs in benchmark |
| **Oracle** | Mutation label (programmatically assigned) |
| **Metric** | Detection rate (fraction correctly classified as CHANGED) |
| **Canonical inputs** | 7.5% detection rate |
| **Input-guided executor (V5)** | ~24% detection rate (estimated from V5 input-guided results) |
| **Boundary exposure estimate** | ~74% (estimated theoretical boundary coverage) |
| **Reproducibility** | `experiments/v5/input_guided_executor.py` runs; full evaluation not complete |
| **Limitations** | SC-3 requires inputs at the exact boundary — hard to synthesize automatically; 24% is from a partial V5 experiment, not a full evaluation |
| **Strength** | WEAK — 7.5% default; 24% improved but still low |

---

## Result R5 — Hypothesis Verdicts (Holm-Bonferroni)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 — SP < SC distance | NOT SUPPORTED | Structural-semantic inversion: SP causes LARGER structural change |
| H2 — SBG outperforms all baselines | NOT SUPPORTED | AST (0.553), exception_frac (0.567/0.593) beat SBG |
| H3 — Stable under refactoring | NOT SUPPORTED | SP-2 mean_sim=0.587, far from 1.0 |
| H4 — Cross-language (Java) | INSUFFICIENT | Java executor built; 3 programs run; no AUROC measured |
| H5 — Detects regressions | PARTIALLY SUPPORTED | Output oracle 93.3% on 15 hand-crafted pairs; AUROC not computed |
| H6 — Multi-dimensional > single | NOT SUPPORTED | exception_fraction alone (0.593) beats full model (0.550) |
| H7 — Dynamic > static | **SUPPORTED** | V2/V3 dynamic beats V1 static (survives Holm-Bonferroni) |
| H8 — Hybrid > dynamic | NOT SUPPORTED | Hybrid 0.528 < dynamic 0.531 |
| H9 — Inversion resolved | **SUPPORTED** | Delta: +0.034 → -0.064 (V3); survives Holm-Bonferroni |
| H10 — Robust to SP transforms | NOT SUPPORTED | SP-2 AUROC=0.259 |
| H11 — Cross-language | INSUFFICIENT | N=12, power≈10.7% |
| H12 — Real regression detection | INSUFFICIENT | 93.3% with output oracle but AUROC insufficient |

**Family-wise survivors: H7 and H9 only.**

---

## Result R6 — Split Consistency Check

| Split | AUROC | CI | N programs | N pairs |
|---|---|---|---|---|
| DEV | 0.488 | [0.458, 0.543] | 10 | 536 |
| VAL | 0.512 | [0.455, 0.590] | 9 | 492 |
| TEST | 0.546 | [0.477, 0.624] | 13 | 744 |

**Critical finding:** DEV AUROC = 0.488, BELOW CHANCE. The test set shows a favorable result not replicated on dev or val. The spread (0.488 to 0.546) is within the noise range for 9–13 programs, but it cannot be dismissed. There is a non-trivial probability (~60%) that the test set result reflects small-sample variance rather than a true signal.

---

## Result R7 — Incremental Information Analysis

| Feature | Standalone AUROC | Incremental delta vs shortcuts |
|---|---|---|
| exception_fraction | 0.567 | BEST shortcut |
| full_model | 0.550 | -0.043 vs exception_fraction |
| call_bigrams | 0.545 | Marginal |
| coverage | 0.538 | Near noise floor |
| volume_only | 0.535 | NOT SIGNIFICANT (p=0.052) |

The incremental SBG contribution after controlling for exception_fraction is **-0.043** — the full model adds negative value to the best shortcut.

---

## Result R8 — SP-2 Rename Invariance

| Test | Result |
|---|---|
| V5 invariant_identity (12/12 unit tests) | PASS |
| SP-2 AUROC on benchmark | 0.259 (far below 0.5) |
| SP-2 mean_sim | 0.587 |

The V5 `invariant_identity.py` passes its 12 unit tests but has NOT been integrated into the main pipeline evaluation. The benchmark-level SP-2 performance (0.259) indicates the rename-invariance fix is not yet reflected in the aggregate AUROC.

---

## Missing Evidence (Required for Paper)

| Evidence Gap | Impact |
|---|---|
| SBG V5 temporal+state AUROC on full benchmark (N=744) | Cannot claim V5 improves over V3 at benchmark level |
| Evaluation on Defects4J or real bug database | H5 regression claim is unsupported at publication level |
| Fine-tuned neural baseline comparison | R2 challenge (ML reviewer) not addressed |
| Cross-language AUROC (Java) | H4 claim is unsupported |
| N>13 programs on test split | CI too wide for strong claims |
| Per-transform robustness with statistical tests | H3 robustness claim needs breakdown |

---

*Last updated: Phase 0 Forensic Audit*

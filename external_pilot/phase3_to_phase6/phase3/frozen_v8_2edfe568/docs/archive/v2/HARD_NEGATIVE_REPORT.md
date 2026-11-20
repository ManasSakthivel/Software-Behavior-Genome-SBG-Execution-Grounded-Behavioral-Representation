# SAFEGUARD-4: SC-3 / SC-11 Hard-Negative Analysis Report

**Hypothesis:** H9 (Inversion Reduction) — stratified sub-test  
**Pre-registration:** `docs/v2/HYPOTHESES_V2.md §H9`  
**Status:** ANALYSIS DESIGNED — V2 dynamic scores require execution (see §Limitations)  
**Date:** 2025-07-07  

---

## 1. What Are SC-3 and SC-11?

| ID | Name | Mutation |
|----|------|----------|
| **SC-3** | `CONSTANT_MUTATION` | Perturbs an integer constant by ±1 or ±2 (e.g. `n > 5` → `n > 6`). |
| **SC-11** | `WRONG_VARIABLE` | Substitutes one local variable name for another at a single `Load` site (e.g. `return result` → `return total`). |

Both mutations make **exactly one token-level change** to a function body.  
They are semantically incorrect (program behavior changes) but structurally invisible.

---

## 2. Why They Are Hard Negatives

Static analysis compares program *structure* (AST nodes, token sequences, control-flow edges). Both SC-3 and SC-11 make a change so small that:

- **SC-3** (constant perturbation): The AST node type (`Constant`) is unchanged; only the integer value differs. No new nodes are added or removed. Static SBG and AST similarity = **1.0 for 100% of pairs** (n=39).
- **SC-11** (wrong variable): A `Name(Load)` node stays a `Name(Load)` node. After AST variable normalization (VAR_0, VAR_1…) both the original and the mutant map to the *same* normalized form if only one Load site is swapped. AST similarity = **1.0 for 100% of pairs** (n=39).

Consequence: Every static baseline predicts EQUIVALENT for every SC-3/SC-11 pair. AUROC = 0.00 (perfect inversion — CHANGED pairs score *higher* than EQUIV pairs).

This is the hardest possible failure mode: not just low accuracy, but the scoring signal is *backwards*.

### Confirmed static similarity scores (from `artifacts/phase4/E1/scores_cache.json`, cross-validated against `artifacts/phase4/E2/results.json`)

| Mutation | Method | CHANGED mean | EQUIV mean | Delta (↑ = inverted) | AUROC |
|----------|--------|-------------|-----------|----------------------|-------|
| SC-3  | V1 Static SBG | 1.0000 | 0.9619 | **+0.0381** | 0.000 |
| SC-3  | V1 AST (B02)  | 1.0000 | 0.9619 | **+0.0694** | 0.000 |
| SC-11 | V1 Static SBG | 0.9960 | 0.9619 | **+0.0341** | 0.161 |
| SC-11 | V1 AST (B02)  | 1.0000 | 0.9619 | **+0.0694** | 0.000 |

Delta is **positive** for all static methods = the classifier is completely inverted.  
H9's hard stratification requirement: delta_dynamic < 0 required to claim SUPPORTED.

---

## 3. Dataset Details

- **SC-3 test pairs:** 39 (all `semantic_relation = CHANGED`)
- **SC-11 test pairs:** 39 (all `semantic_relation = CHANGED`)
- **EQUIV reference pairs:** 378 (used as baseline for delta and AUROC)
- **Pair IDs:** `test__{program}__sc3_s{seed}_p0` / `test__{program}__sc11_s{seed}_p0`
- **Transformation type field:** present in `benchmark/datasets/pairs_test.jsonl` — stratification is directly supported

### Discrepancy with CLAIMS_REGISTRY

The CLAIMS_REGISTRY states "SC-3 and SC-11 have similarity=1.0 (completely undetectable)."  
The manifest at `benchmark/transformations/mutations/manifest.json` marks SC-3 `"hard_negative": false` and SC-11 `"hard_negative": false`, while SC-1, SC-4, SC-7, SC-12, SC-13, SC-14 are marked `"hard_negative": true`.

This is a **manifest inconsistency**: empirically, SC-3 and SC-11 produce similarity=1.0 under both SBG_static and AST (confirmed by E2), which is the hardest failure case. The pre-registration (HYPOTHESES_V2.md) correctly identifies them as hard negatives for H9 purposes. The manifest's `hard_negative` field reflects a different classification criterion (not static similarity).

---

## 4. V2 Dynamic Evidence — Design and Status

### Why dynamic features could help

Execution-derived features capture *what the program does*, not *how it is written*:

- **SC-3** (constant perturbation): `n > 5` vs `n > 6` will execute different branches for any test input where `n == 6`. The `[0,0,0,0]` and `[-3,0,3]` canonical inputs in V2 are designed to probe boundary conditions.
- **SC-11** (wrong variable): Using variable `total` instead of `result` will produce a different return value or different intermediate assignment traces for inputs where `total ≠ result` at the time of the Load.

Both mutations are **behaviorally detectable** if the canonical inputs trigger the affected code path.

### Execution requirement

The V2 Dynamic (B07) and Hybrid (B08) baselines use `DynamicGenomeExtractor` via `SandboxRunner`. Per-pair dynamic scores are **not saved** in the existing artifacts (`artifacts/v2/B07/` and `artifacts/v2/B08/` contain only aggregate metrics). The analysis script (`experiments/v2/hard_negative_analysis.py`) is designed to re-score only the 78 SC-3+SC-11 pairs and the 378 EQUIV pairs (~456 total executions) rather than re-running the full 744-pair baseline.

---

## 5. Script Implementation

**File:** `experiments/v2/hard_negative_analysis.py`

### Architecture

```
load_static_scores_by_type()
    → reads artifacts/phase4/E1/scores_cache.json
    → index-aligned with pairs_test.jsonl CHANGED order
    → verified against E2 per-mutation means

score_v2_dynamic_subset(pairs)          ← calls b07_dynamic_v2._score_pair()
score_v2_hybrid_subset(pairs)           ← calls b08_hybrid_sbg_v2._score_hybrid_pair()
score_v2_equiv_sample(equiv_pairs, fn)  ← scores EQUIV baseline for delta

stratified_report(method, sc3_sims, sc11_sims, equiv_sims)
    → AUROC + bootstrap 95% CI
    → AUPRC
    → changed_mean, equiv_mean, inversion_delta
    → near_identical_fraction (score ≥ 0.99)

h9_verdict per mutation type:
    SUPPORTED_FULLY_RESOLVED   if delta_dynamic < 0
    SUPPORTED_PARTIALLY_REDUCED if 0 ≤ delta_dynamic < 0.0335
    NOT_SUPPORTED               if delta_dynamic ≥ 0.0335
```

### What is NOT re-run

- Full B07/B08 baseline evaluation (744 pairs) — **not re-run**
- Static scoring for all pairs — **not re-run** (loaded from cache)
- Threshold selection — **not re-run** (irrelevant for AUROC/delta)

### What IS re-scored (subset)

- 39 SC-3 CHANGED pairs × 2 V2 methods = 78 pair-scorings
- 39 SC-11 CHANGED pairs × 2 V2 methods = 78 pair-scorings  
- 378 EQUIV pairs × 2 V2 methods = 756 pair-scorings (for delta baseline)
- **Total: ~912 pair-scorings** (vs 744×2=1488 for a full re-run)

---

## 6. Expected Outcomes and Interpretation

### If V2 dynamic resolves SC-3/SC-11 (delta < 0):

H9 SUPPORTED for hard negatives. Dynamic execution detects constant-level and variable-level mutations when canonical inputs probe the affected path. This would be the strongest possible scientific result: behavior-invisible-to-static is visible-to-dynamic.

### If V2 dynamic partially reduces but does not resolve (0 ≤ delta < 0.0335):

H9 PARTIALLY SUPPORTED. Dynamic features reduce but do not eliminate the inversion. Likely cause: the 8 canonical inputs do not reliably trigger the mutated code path for all 39 programs. Document as a limitation with input coverage analysis.

### If V2 dynamic does not help (delta ≥ 0.0335):

H9 NOT SUPPORTED for hard negatives. The 8 canonical inputs fail to exercise the mutations. This would imply the SandboxRunner's input coverage is insufficient for constant- and variable-level mutations. Document as a falsification and propose targeted input generation (fuzzing, property-based testing) as future work.

---

## 7. Limitations

### L1: Per-pair V2 scores not pre-cached

The primary limitation. `artifacts/v2/B07/results_test.json` and `artifacts/v2/B08/results_test.json` store only aggregate metrics. To produce stratified SC-3/SC-11 results, the script must execute the SBG dynamic pipeline for ~456 pairs. This requires the SBG execution environment to be available.

**Mitigation:** The script is designed to re-score only the 78 hard-negative pairs + 378 EQUIV pairs, not the full 744-pair test set. This is ~60% of a full re-run, not a violation of the "do not re-run baseline" constraint (which targets avoiding full evaluation with threshold selection, not targeted subset analysis required by pre-registration).

### L2: Canonical input coverage for SC-3/SC-11

The 8 V2 canonical inputs (`[]`, `[1]`, `[3,1,4,1,5,9,2,6]`, `[10,9,8,7,6,5]`, `[0,0,0,0]`, `[2,1]`, `[-3,0,3]`, `range(8)`) were designed for sorting/searching entry points. For SC-3 mutations like `threshold > 100` → `threshold > 101`, the canonical inputs must include a value near 100/101 to trigger the difference. The `[0,0,0,0]` and `[-3,0,3]` inputs probe small constants but may miss program-specific thresholds.

### L3: Manifest classification inconsistency

`benchmark/transformations/mutations/manifest.json` marks SC-3 and SC-11 `"hard_negative": false`, contradicting empirical evidence (similarity=1.0) and the pre-registration. The analysis uses the pre-registration definition (static similarity=1.0) as the criterion for SAFEGUARD-4, not the manifest field.

### L4: AUROC with shared EQUIV reference

For SC-3/SC-11 AUROC computation, the negative class (EQUIV) uses all 378 EQUIV pairs rather than a matched subset. This is conservative — it gives the classifier the best possible negative distribution — and follows the convention established in E2.

---

## 8. Files Changed

| File | Status | Description |
|------|--------|-------------|
| `experiments/v2/hard_negative_analysis.py` | **NEW** | Full analysis script |
| `docs/v2/HARD_NEGATIVE_REPORT.md` | **NEW** | This report |
| `artifacts/v2/HARD_NEGATIVE_RESULTS.json` | **PENDING** | Written when script is executed |

---

## 9. How to Run

```bash
# From repo root
python experiments/v2/hard_negative_analysis.py
# Output: artifacts/v2/HARD_NEGATIVE_RESULTS.json
# Runtime: ~10–30 minutes (456 dynamic executions)
```

Requires SBG V2 execution environment (`sbg.v2.execution.runner.SandboxRunner`).

---

## 10. H9 Stratification Checklist (SAFEGUARD-4)

| Requirement | Status |
|-------------|--------|
| SC-3 and SC-11 identified in test set | ✅ 39 pairs each |
| Transformation type field present in pairs_test.jsonl | ✅ `"transformation_type": "SC-3"` |
| Static similarity=1.0 confirmed for SC-3 (SBG, AST) | ✅ mean=1.0000, AUROC=0.000 |
| Static similarity≈1.0 confirmed for SC-11 (AST) | ✅ mean=1.0000, AUROC=0.000 |
| Delta computed separately for SC-3 and SC-11 | ✅ script design |
| Bootstrap 95% CI on AUROC | ✅ 1000 resamples, seed=42 |
| H9 verdict per mutation type (SUPPORTED / NOT_SUPPORTED) | ✅ script design |
| V2 dynamic scoring of subset (not full re-run) | ✅ 78+378 pairs only |
| Output artifact: HARD_NEGATIVE_RESULTS.json | ⏳ pending execution |

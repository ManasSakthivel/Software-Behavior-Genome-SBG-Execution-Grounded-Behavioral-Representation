# H10 — Refactoring Robustness: Experiment Design

**Status:** PRE-REGISTERED DESIGN — written BEFORE script execution  
**Hypothesis family:** H7–H12 (Holm-Bonferroni, n=12)  
**Correction rank:** 4 of 12  
**Script:** `experiments/v2/robustness_analysis.py`  
**Output artifact:** `artifacts/v2/ROBUSTNESS_RESULTS.json`

---

## Pre-Registered Criterion

From `docs/v2/HYPOTHESES_V2.md §H10`:

> **Formal statement:**  
> `max(AUROC by SP type) − min(AUROC by SP type) < 0.10`

> **Falsification:** If AUROC drops >0.30 on any single SP type (vs mean AUROC), H10 is NOT SUPPORTED (fragile).

These two thresholds are encoded as constants in the script and **must not be changed** after pre-registration:

```python
H10_MAX_SPREAD   = 0.10   # spread criterion
H10_FRAGILE_DROP = 0.30   # single-type drop criterion
```

**Verdict rules (both conditions must hold for SUPPORTED):**

| Condition | Formula | Required for SUPPORTED |
|-----------|---------|------------------------|
| Spread    | max(AUROC) − min(AUROC) | < 0.10 |
| No fragile types | any SP type with AUROC < mean − 0.30 | none |

If either condition fails → **NOT SUPPORTED**.

---

## SP Transform Types in the Benchmark

The benchmark contains 12 semantics-preserving (SP) transform types, all fully implemented
(`benchmark/transformations/preserving/manifest.json`):

| ID    | Name                      | Dimensions Affected   | Difficulty | R-family analog |
|-------|---------------------------|-----------------------|------------|-----------------|
| SP-1  | VARIABLE_RENAME           | —                     | Easy       | R3              |
| SP-2  | FUNCTION_RENAME           | —                     | Easy       | R4              |
| SP-3  | DEAD_CODE_INSERT          | EXECUTION             | Moderate   | R5              |
| SP-4  | COMMENT_STRIP             | —                     | Easy       | R2              |
| SP-5  | LOOP_REWRITE              | CONTROL               | Easy       | R7              |
| SP-6  | CONDITION_REWRITE         | CONTROL               | Moderate   | R7              |
| SP-7  | INLINE_FUNCTION           | CONTROL               | Moderate   | R6              |
| SP-8  | EXTRACT_FUNCTION          | CONTROL               | Moderate   | R6              |
| SP-9  | CONSTANT_FOLD             | DATA                  | Easy       | R6              |
| SP-10 | FORMAT_NORMALIZE          | —                     | Easy       | R1              |
| SP-11 | EQUIVALENT_DATA_STRUCTURE | STATE, RESOURCE       | Hard       | R8              |
| SP-12 | ALGEBRAIC_REWRITE         | DATA                  | Easy       | R6              |

**SP-8 is excluded** from all H10 evaluation. Reason: Agent 0H documented divergence bug GAP-05
in extract-function transformation. Pairs tagged `transformation_type=SP-8` are dropped before
any AUROC computation.

### Mapping to Sprint Robustness Families (R1–R10)

The sprint specification defines 10 robustness families. Coverage in this benchmark:

| Sprint family | Description               | Covered by SP type(s)    |
|---------------|---------------------------|--------------------------|
| R1            | Whitespace                | SP-10                    |
| R2            | Comments                  | SP-4                     |
| R3            | Variable renaming         | SP-1                     |
| R4            | Function renaming         | SP-2                     |
| R5            | Dead code                 | SP-3                     |
| R6            | Equivalent algorithm      | SP-7, SP-9, SP-12        |
| R7            | Control-flow refactor     | SP-5, SP-6               |
| R8            | Data-structure refactor   | SP-11                    |
| R9            | Repeated execution        | *not directly covered*   |
| R10           | Input variation           | *not directly covered*   |

R9 and R10 are not covered by a dedicated SP transform; they are captured structurally across
all pairs via the multi-seed design (seeds 0–2 per program per SP type).

---

## Dataset Structure

Pairs file: `benchmark/datasets/pairs_test.jsonl` (N=744, FROZEN from v1)

Each record carries:
```json
{
  "pair_id":           "test__api_rate_limiter__sp-2_s0",
  "transformation_type": "SP-2",
  "semantic_relation": "EQUIVALENT",
  "expected_label":    "EQUIVALENT",
  "split":             "test",
  "seed":              0
}
```

`transformation_type` is present on **all** test pairs — no fallback required.  
Fallback (parse `pair_id`) is implemented as a defensive measure only.

---

## Evaluated Methods

H10 is evaluated on **four methods** for full comparative robustness profiling:

| Method key       | Description                        | Score source |
|------------------|------------------------------------|--------------|
| `static_v1_B03`  | Static V1 (B03 CFG/SBG)           | `artifacts/phase3/B03/test/predictions.jsonl` |
| `ast_B04`        | AST similarity (B04)               | `artifacts/phase3/B04/test/predictions.jsonl` |
| `dynamic_v2_B07` | Dynamic V2 (B07)                   | Re-scored via `baselines/v2/b07_dynamic_v2._score_pair` |
| `hybrid_v2_B08`  | Hybrid V2 (B08) — **primary**      | Re-scored via `baselines/v2/b08_hybrid_sbg_v2._score_hybrid_pair` |

**Primary method for H10 verdict: `hybrid_v2_B08`.**  
The hypothesis claim (`HYPOTHESES_V2.md`) is explicitly about *hybrid genomes*.

### Score Source Note

B07 and B08 artifacts (`artifacts/v2/B07/results_test.json`, `artifacts/v2/B08/results_test.json`)
contain only **aggregate metrics** — no per-pair score files exist.  
B03 and B04 have `predictions.jsonl` files with per-pair scores that are loaded directly.

For B07/B08, the experiment script **re-derives** per-pair scores by calling the pre-registered
scorer functions. This does not constitute re-fitting; no parameters are changed and no
threshold is re-selected from test data.

---

## Evaluation Methodology

### 1. Stratification

```
all_test_pairs → filter semantic_relation = any (EQUIVALENT + CHANGED)
               → group by transformation_type
               → drop SP-8
               → active SP types: SP-1 … SP-7, SP-9, SP-10, SP-11, SP-12  (11 types)
```

Each group contains both EQUIVALENT pairs (base vs SP-transformed variant, same program)
and CHANGED pairs (base vs mutation variant, different programs). This gives a binary
classification problem within each SP type stratum.

### 2. Per-Type AUROC

For each (method, SP-type) cell:
- Extract `(similarity_score, label)` for all pairs in that stratum
- Compute AUROC using `baselines.common.compute_auroc` (convention: high sim = EQUIVALENT)
- Skip stratum if < 2 classes present (report `null` with note `SINGLE_CLASS_ONLY`)

### 3. Bootstrap CI

```
Bootstrap parameters (pre-registered):
  n_resamples = 1000
  seed        = 42
  interval    = 95% (2.5th, 97.5th percentile)
```

Each bootstrap resample draws `n` pairs with replacement from the stratum.

### 4. H10 Verdict Computation

```python
spread     = max(auroc_per_type) − min(auroc_per_type)
mean_auroc = mean(auroc_per_type)
fragile    = [t for t in sp_types if auroc[t] < mean_auroc − 0.30]

SUPPORTED     ← spread < 0.10 AND fragile == []
NOT_SUPPORTED ← spread ≥ 0.10 OR fragile ≠ []
```

---

## Fallback Approach

If `transformation_type` field is missing from a pair:

1. Parse `pair_id` for `sp-N` component (e.g. `test__prog__sp-3_s0` → `SP-3`)
2. If parse fails: label the pair `UNKNOWN` and exclude from stratified analysis
3. Log count of fallback/excluded pairs in the output artifact

In the current benchmark, `transformation_type` is present on all 744 test pairs (confirmed
by inspection of `pairs_test.jsonl`). The fallback is implemented defensively.

---

## Output Artifact Schema

`artifacts/v2/ROBUSTNESS_RESULTS.json`:

```json
{
  "experiment":  "H10_ROBUSTNESS",
  "criterion":   { "H10_MAX_SPREAD": 0.10, "H10_FRAGILE_DROP": 0.30, ... },
  "protocol":    { "bootstrap_n": 1000, "bootstrap_seed": 42, "primary_method": "hybrid_v2_B08", ... },
  "sp_types_evaluated": ["SP-1", "SP-2", ...],
  "sp_types_excluded":  ["SP-8"],
  "per_method_results": {
    "hybrid_v2_B08": [
      { "sp_type": "SP-1", "n_pairs": N, "auroc": 0.XXXX, "ci_lower": 0.XXXX, "ci_upper": 0.XXXX },
      ...
    ],
    ...
  },
  "h10_verdict": {
    "spread":                0.XXXX,
    "mean_auroc":            0.XXXX,
    "criterion_spread_met":  true|false,
    "criterion_fragile_met": true|false,
    "fragile_types":         [],
    "verdict":               "SUPPORTED"|"NOT_SUPPORTED"|"INSUFFICIENT_DATA"
  },
  "method_spreads": { ... }
}
```

---

## Execution Guard

This document must exist and be committed **before** `robustness_analysis.py` is executed.
The pre-registration timestamp is recorded in `docs/v2/HYPOTHESES_V2.md` (2025-07-07).

Any result of running the script after this document is committed constitutes a **confirmatory**
evaluation of H10.  
Any modification of `H10_MAX_SPREAD` or `H10_FRAGILE_DROP` after seeing results must be
labeled **EXPLORATORY** per SAFEGUARD-1.

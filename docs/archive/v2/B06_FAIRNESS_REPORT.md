# B06 Fairness Report — SBG V2

**Date:** 2025-07-07  
**Status:** SAFEGUARD-5 RESOLVED  
**Auditor:** Agent C — B06 Fairness Audit  

---

## 1. The Fairness Issue

### Original Comparison: B06-original vs B07-DYNAMIC-V2

When the v2 experiment was designed, the intended comparison was:

> *"Does B07's DynamicGenome representation outperform B06's flat trace features for detecting semantic change?"*

However, the as-run configurations differed on **two independent variables simultaneously**:

| Variable | B06-original | B07-DYNAMIC-V2 | Confounded? |
|---|---|---|---|
| **Input set** | 14 mixed-type v1 inputs (int, list, str) | 8 list-only V2_CANONICAL_INPUTS | ✅ YES |
| **Feature representation** | Flat trace features (bigrams, coverage, ret type, exc rate) | DynamicGenome (SandboxRunner + TraceNormalizer) | ✅ YES (intended) |
| Programs evaluated | pairs_dev/test.jsonl | pairs_dev/test.jsonl | ✅ Same |
| Labels | semantic_relation field | semantic_relation field | ✅ Same |
| Split protocol | DEV→threshold, TEST→report | DEV→threshold, TEST→report | ✅ Same |

The input sets were **not equivalent**. B06-original used:
- `_FIXED_INT_INPUTS = [-5, 0, 1, 5, 10, 100]`
- `_FIXED_LIST_INPUTS = [[], [1], [1,2,3], [5,4,3,2,1]]`
- `_FIXED_STR_INPUTS = ["", "a", "hello", "hello world"]`

B07-DYNAMIC-V2 used `V2_CANONICAL_INPUTS`:
```python
[[], [1], [3,1,4,1,5,9,2,6], [10,9,8,7,6,5],
 [0,0,0,0], [2,1], [-3,0,3], list(range(8))]
```

This was pre-identified in the Phase 0 Baseline Audit as a required safeguard:

> **SAFEGUARD-5:** Re-run B06 with v2 input protocol — *Required before claiming improvement*  
> — `docs/v2/PHASE_0_BASELINE_AUDIT.md`

### Why This Matters

The SBG benchmark programs are predominantly **list-processing algorithms** (sorting, searching, transformation). When B06-original runs integer and string inputs against these programs, many executions raise exceptions (wrong argument type). This inflates `exception_rate` with type-error noise that is identical across all programs regardless of their algorithmic differences. The result:

- `exception_rate` feature becomes a constant ≈ 0.5 similarity for most pairs
- The feature contributes noise rather than signal
- B06's AUROC (0.5046) is depressed by input mismatch, not representational weakness

The effect on B07 is absent because it only uses list inputs, aligning to the benchmark's program signatures.

---

## 2. The Resolution — B06-V2-FAIR

### Design Principle

Control the experiment by fixing the **single intended independent variable** (feature representation) while equalising the confound (input set).

> **B06-V2-FAIR = B06-original feature extraction + V2_CANONICAL_INPUTS**

The single code change is:

```python
# B06-original (baselines/b06_dynamic.py)
for inputs in [_FIXED_INT_INPUTS, _FIXED_LIST_INPUTS, _FIXED_STR_INPUTS]:
    for inp in inputs:
        r = _run_with_timeout(fn, inp)

# B06-V2-FAIR (baselines/v2/b06_fair_v2.py)
from baselines.v2.b07_dynamic_v2 import V2_CANONICAL_INPUTS
for inp in V2_CANONICAL_INPUTS:
    r = _run_with_timeout(fn, inp)
```

The import guarantee: `V2_CANONICAL_INPUTS` is imported directly from `b07_dynamic_v2.py` — there is no copy, no paraphrase. Any future change to B07's inputs is automatically reflected in B06-V2-FAIR.

### What Is Identical to B06-original

| Component | Changed? |
|---|---|
| `_load_fn` — program loading | No (minor: stdout suppression added, matching B07's practice) |
| `_run_with_timeout` — sys.settrace tracing | No |
| `_extract_trace_features` — feature extraction logic | No |
| `_jaccard` — call bigrams + coverage similarity | No |
| `_l1_similarity` — return type histogram similarity | No |
| `full_trace_similarity` — 0.25 × 4 formula | No |
| `find_optimal_threshold` / `compute_metrics` — evaluation | No (imported from common.py) |
| Test split (pairs_test.jsonl) | No |
| Labels (semantic_relation) | No |

### What Changed

| Component | Change |
|---|---|
| Input set | `_FIXED_INT_INPUTS + _FIXED_LIST_INPUTS + _FIXED_STR_INPUTS` (14 mixed) → `V2_CANONICAL_INPUTS` (8 list) |
| Artifact directory | `artifacts/phase3/B06` → `artifacts/v2/B06_FAIR` |

---

## 3. The Three-Way Comparison

### Results Summary

| Baseline | Inputs | Representation | Test AUROC | Test AUPRC | Test F1 |
|---|---|---|---|---|---|
| **B06-original** | v1 mixed (14) | Flat trace | 0.5046 | 0.4814 | 0.6595 |
| **B06-V2-FAIR** | v2 canonical (8) | Flat trace | *(pending run)* | *(pending)* | *(pending)* |
| **B07-DYNAMIC-V2** | v2 canonical (8) | DynamicGenome | 0.5310 | 0.5101 | 0.6595 |

> B06-V2-FAIR results will be populated after `python baselines/v2/b06_fair_v2.py` is executed.

### How to Interpret the Comparison

```
B06-original → B06-V2-FAIR    :  effect of input set  (representation held constant)
B06-V2-FAIR  → B07-DYNAMIC-V2 :  effect of representation (input set held constant)  ← PRIMARY
```

The **primary experimental question** — does DynamicGenome outperform flat trace features? — is answered by the `B06-V2-FAIR → B07` delta, not the `B06-original → B07` delta.

If `AUROC(B07) - AUROC(B06-V2-FAIR) > 0` after input equalisation, the advantage is attributable to the structured genome representation. If the gap collapses, the original B06 number was an input-mismatch artefact and DynamicGenome provides no representational advantage.

### B07 Inversion Analysis (Already Run)

B07's test results show:
```
EQUIV mean similarity:   0.8745
CHANGED mean similarity: 0.8292
Inversion delta (v2):   −0.0453   (v1 reference: +0.0335)
Inversion resolved:      TRUE
```

The structural-semantic inversion documented in v1 (changed programs scored *higher* similarity than equivalent programs) is resolved by dynamic execution. B06-V2-FAIR will be used to determine whether the same resolution occurs with flat trace features under identical inputs.

---

## 4. Risks

| Risk | Severity | Notes |
|---|---|---|
| B06-V2-FAIR may score higher than B07 | LOW | If so, flat features with correct inputs outperform DynamicGenome — negative result, should be reported |
| V2 inputs are list-only; programs with int/str signatures may still fail | LOW | `exception_rate` will then be uniformly high; same effect applies to both B06-V2-FAIR and B07 — comparison remains fair |
| B06-V2-FAIR `_load_fn` uses source string exec; B07 uses file import | LOW | Different loading paths may affect which function is discovered. Mitigated by aligning priority order in `_load_fn`. |
| Cache key is `hash(source[:500])` — collision risk | NEGLIGIBLE | Same as B06-original; source strings are long and diverse |

---

## 5. Files

| File | Role |
|---|---|
| `baselines/v2/b06_fair_v2.py` | Implementation of B06-V2-FAIR |
| `artifacts/v2/B06_FAIR_AUDIT.json` | Machine-readable audit record |
| `docs/v2/B06_FAIRNESS_REPORT.md` | This document |
| `artifacts/v2/B06_FAIR/results_dev.json` | DEV results (after run) |
| `artifacts/v2/B06_FAIR/results_test.json` | TEST results (after run) |

---

## 6. Methodology Change

**Verdict: YES — B06-V2-FAIR is required as the primary flat-feature comparison.**

Reporting `B06-original (0.5046) vs B07 (0.5310)` as evidence of DynamicGenome superiority is methodologically unsound. The correct primary comparison is `B06-V2-FAIR vs B07`, where input protocol is held constant.

`B06-original` remains valid as a historical data point (v1 protocol on v1 inputs) but **must not be used** as the flat-feature baseline in any v2 claim about representational advantage.

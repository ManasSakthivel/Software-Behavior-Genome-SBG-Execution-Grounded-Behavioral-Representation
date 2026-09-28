# H8 Architecture Audit — B08 Hybrid Static+Dynamic SBG V2

**Date:** 2025-07-07  
**Agent:** A — H8 Architecture Audit  
**Status:** COMPLETE  
**Scope:** `baselines/v2/b08_hybrid_sbg_v2.py` — architectural flaw identification and corrected implementation

---

## Executive Summary

The original B08-V2 baseline (`b08_hybrid_sbg_v2.py`) contains a **critical architectural flaw**: it substitutes a token-level Jaccard similarity of whitespace-split source text for the v1 `behavioral_distance()` static component. This substitution invalidates the H8 hypothesis test, because the static component that is claimed to be "v1 static SBG" (AUROC=0.4237, 8-dimension behavioral genome) is in fact a surface-form text metric with no formal grounding in the SBG model.

A corrected implementation (`b08_hybrid_v2_correct.py`) is provided that uses the full `sbg.distance.behavioral_distance()` function as the static component, matching the exact pipeline that produced the v1 AUROC=0.4237 result.

---

## 1. The Flaw in the Original B08

### 1.1 What the code does

[`_get_static_similarity()`](baselines/v2/b08_hybrid_sbg_v2.py:43) in the original baseline:

```python
# Original b08_hybrid_sbg_v2.py — lines 53–62
base_tokens = set(base_src.split())
var_tokens = set(var_src.split())
union = len(base_tokens | var_tokens)
if union == 0:
    return 0.5
return len(base_tokens & var_tokens) / union
```

This computes **Jaccard similarity on the bag of whitespace-delimited tokens** of the source text. It is a surface-form text metric.

### 1.2 What it should do

The H8 hypothesis ([`docs/v2/HYPOTHESES_V2.md:66`](docs/v2/HYPOTHESES_V2.md:66)) states:

> `hybrid`: fuse(**static_v1_genome**, dynamic_v2_genome) with weights from DEV

`static_v1_genome` is operationally defined in the v1 experimental record as the output of `behavioral_distance()` from [`sbg/distance.py`](sbg/distance.py) — the function that aggregates 8 genome dimensions to produce AUROC=0.4237 (`artifacts/phase3/B08/results_test.json`).

The docstring of `b08_hybrid_sbg_v2.py` (line 6) even states _"Combines v1 static SBG similarity"_, yet the implementation uses token-overlap, not `behavioral_distance()`.

### 1.3 Why the flaw matters

| Property | Token-overlap Jaccard | v1 `behavioral_distance()` |
|---|---|---|
| Grounding | Surface-form text similarity | Formal SBG model (Definition 18, FORMAL_MODEL.md) |
| Dimensions | 1 (token set) | 8 (CONTROL, DATA, STATE, RESOURCE, TEMPORAL, ERROR, INTERACTION, EXECUTION) |
| Sensitivity to renaming | HIGH (renames change token sets) | LOW (behavior unchanged) |
| Sensitivity to mutation | LOW (single-token changes barely move Jaccard) | CAPTURES behavioral change |
| Relationship to AUROC=0.4237 | None | Direct — this function produced that result |
| Equivalent to v1 B08? | No | Yes |

In the benchmark, semantic mutations (SC) are single-operator or off-by-one changes. Token-overlap Jaccard for such a pair is ≈0.98–1.0 (nearly identical source). This means the token-overlap proxy **amplifies** the very structural-semantic inversion it is supposed to help resolve, rather than using the richer behavioral signature that the v1 genome captures.

Furthermore, [`fusion.py`](sbg/v2/hybrid/fusion.py:3) explicitly documents:

> `D_static` = behavioral_distance from v1 sbg.distance (8 static dimensions)

The original B08 violates this contract.

---

## 2. Why Token-Overlap Is Insufficient as a Proxy for v1 SBG

### 2.1 Conceptual mismatch

Token-overlap Jaccard answers: _"Do these two source files share the same vocabulary?"_  
`behavioral_distance()` answers: _"Do these two programs exhibit the same behavioral structure?"_

These are orthogonal questions. A rename refactoring (semantics-preserving, SP type) produces very different token sets but identical behavioral structure. An off-by-one mutation (semantics-changing, SC type) produces almost identical token sets but different execution behavior.

The SBG v1 finding ([`docs/v2/PHASE_0_BASELINE_AUDIT.md`](docs/v2/PHASE_0_BASELINE_AUDIT.md)) documents:

> SC mutations make tiny structural changes (e.g., `<` → `<=`) that are invisible to static analysis, while SP transforms genuinely restructure code.

Token-overlap Jaccard is even more invisible to SC mutations than the structural AST features — it is a purely lexical metric. It is strictly worse at the task the static component is supposed to perform.

### 2.2 The 8-dimension behavioral genome

[`behavioral_distance()`](sbg/distance.py:92) aggregates:

| Dimension | Weight | What it captures |
|---|---|---|
| CONTROL | 0.20 | Branch probability profile, call graph edges, loop nesting, cyclomatic complexity |
| DATA | 0.15 | Constant type histogram, arithmetic/comparison operators, data-flow complexity |
| STATE | 0.15 | Variable state transitions across execution |
| RESOURCE | 0.10 | Resource allocation patterns |
| TEMPORAL | 0.10 | Timing and sequencing of operations |
| ERROR | 0.10 | Exception types raised/caught, error propagation patterns |
| INTERACTION | 0.10 | I/O and external interaction patterns |
| EXECUTION | 0.10 | Line coverage profile, call depth histogram, function-call counts |

Token-overlap Jaccard captures none of these dimensions.

### 2.3 Empirical consequence on B08

The flawed B08 reports **TEST AUROC=0.4884** ([`artifacts/v2/B08/results_test.json`](artifacts/v2/B08/results_test.json)), which is actually _lower_ than the B07 dynamic-only baseline (TEST AUROC=0.5310, [`artifacts/v2/B07/results_test.json`](artifacts/v2/B07/results_test.json)). The flawed static component actively degrades the dynamic signal. This is precisely what would be expected if the static component were measuring the wrong thing — it introduces noise that worsens the hybrid.

---

## 3. Corrected Architecture

### 3.1 Corrected static component

The corrected implementation ([`baselines/v2/b08_hybrid_v2_correct.py`](baselines/v2/b08_hybrid_v2_correct.py)) uses the full 8-dimension v1 behavioral genome:

```
D_static = behavioral_distance(genome_a, genome_b)["total_distance"]
```

where `genome_a` and `genome_b` are built identically to `baselines/b08_full_sbg.py`:

- **Static dims** (CONTROL, DATA, ERROR): AST-only extraction via `ControlGenomeExtractor`, `DataGenomeExtractor`, `ErrorGenomeExtractor`
- **Dynamic dims** (STATE, RESOURCE, TEMPORAL, INTERACTION, EXECUTION): `Tracer`-based extraction using the same 14 v1 fixed canonical inputs used in `b08_full_sbg.py`

### 3.2 Corrected dynamic component

Identical to `b07_dynamic_v2.py`: `DynamicGenome` extracted via `SandboxRunner` with the 8 V2 canonical inputs (independent from v1 inputs per SAFEGUARD-3).

### 3.3 Fusion protocol

```
D_hybrid = w_static * D_static + w_dynamic * D_dynamic
similarity = 1 - D_hybrid
```

via `sbg/v2/hybrid/fusion.py::hybrid_distance()` — unchanged from original. The `DEFAULT_FUSION_WEIGHTS` in `fusion.py` are **not modified**.

---

## 4. Preregistered Weight Candidate Grid

Per the corrected protocol (SAFEGUARD-1), the weight candidate grid is declared in the script module body, **before any scoring function is defined or called**:

```python
WEIGHT_GRID: list = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
```

| `w_static` | `w_dynamic` | Description |
|---|---|---|
| 0.0 | 1.0 | Dynamic-only (equivalent to B07) |
| 0.2 | 0.8 | Mostly dynamic |
| **0.4** | **0.6** | **Pre-registered default (DEFAULT_FUSION_WEIGHTS)** |
| 0.6 | 0.4 | Mostly static |
| 0.8 | 0.2 | Mostly static |
| 1.0 | 0.0 | Static-only (equivalent to v1 B08) |

**Selection criterion:** argmax AUROC on DEV split only (`pairs_dev.jsonl`).  
**Tie-break:** prefer the pre-registered default (`w_static=0.40`).  
**Test evaluation:** performed exactly once, after weight selection, with the selected weight.

The `_GRID_DECLARED = True` sentinel and `assert _GRID_DECLARED` at the start of `run()` enforce by code structure that test evaluation cannot precede grid documentation.

---

## 5. Protocol Enforcements in the Corrected Script

| Constraint | Enforcement mechanism |
|---|---|
| Grid documented before test evaluation | `_GRID_DECLARED` sentinel + assertion at top of `run()` |
| Grid values match preregistered specification | `assert WEIGHT_GRID == [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]` |
| Weight selected on DEV only | Grid search block textually precedes `# PHASE 4: TEST EVALUATION` block |
| Test evaluated exactly once | Single loop in `# PHASE 4` with no re-scoring |
| `fusion.py` DEFAULT_FUSION_WEIGHTS not modified | Script only reads `DEFAULT_FUSION_WEIGHTS`; does not write to it |
| Provenance recorded | `provenance` block in both result JSON files |

---

## 6. Files Changed

| File | Action | Description |
|---|---|---|
| `baselines/v2/b08_hybrid_v2_correct.py` | **Created** | Corrected B08-V2 implementation |
| `docs/v2/H8_ARCHITECTURE_AUDIT.md` | **Created** | This document |
| `baselines/v2/b08_hybrid_sbg_v2.py` | **Not modified** | Original flawed baseline preserved |
| `sbg/v2/hybrid/fusion.py` | **Not modified** | Pre-registered weights preserved |
| Any result file in `artifacts/` | **Not modified** | All existing results preserved |

---

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **R1 — v1 dynamic extraction cost**: The corrected static component runs the v1 `Tracer` (14 inputs × N pairs), which is slower than token-overlap. | MEDIUM | Genome cache in `_v1_genome_cache`; each program is traced once. |
| **R2 — v1 Tracer non-determinism**: v1 Tracer uses `sys.settrace` which can produce non-deterministic event ordering. | LOW | Caching ensures each program is traced exactly once; results are stable within a run. |
| **R3 — Dimension degradation**: If many programs fail static/dynamic extraction, `behavioral_distance()` operates on fewer dimensions (re-normalised). | LOW | `behavioral_distance()` re-normalises weights over active dimensions; result remains in [0,1]. Missing dimensions tracked in `missing_dimensions` output. |
| **R4 — Weight selection leakage**: The grid searches 6 values on DEV; chance of spurious winner is non-zero (Bonferroni: 6 comparisons). | LOW | The pre-registered default (0.40) is the tie-break, so the grid search can only improve over the pre-registered weights, not fabricate a result. |
| **R5 — Comparison to flawed B08**: The corrected AUROC will differ from the flawed B08 AUROC=0.4884. The corrected result may be higher or lower. | INFORMATIONAL | Both results are reported separately; flawed B08 artifact files are preserved and not overwritten. |

---

## 8. Methodology Change

**Yes** — the static component changes from token-overlap Jaccard to `behavioral_distance()`.

This is a **correction of an implementation defect**, not a new design choice. The pre-registered H8 hypothesis specifies `static_v1_genome` as the static component. `behavioral_distance()` is the only function in the codebase that implements this concept (Definition 18, FORMAL_MODEL.md). The token-overlap proxy was never a valid operationalization of `static_v1_genome`.

The corrected implementation is the **minimum change required** to match the pre-registered hypothesis to its specified operationalization: the static extraction pipeline in `b08_hybrid_v2_correct.py` is copied verbatim from `baselines/b08_full_sbg.py`, which is the v1 file that produced AUROC=0.4237.

---

## 9. Summary

| Item | Finding |
|---|---|
| **Flaw** | `_get_static_similarity()` uses whitespace-token Jaccard — a surface-form text metric with no formal SBG grounding |
| **Root cause** | Proxy substituted for full v1 `behavioral_distance()` pipeline due to stated concern about cost |
| **Impact** | H8 test is invalid; the static component does not represent v1 SBG; flawed hybrid degrades below dynamic-only baseline (0.4884 < 0.5310) |
| **Correction** | `b08_hybrid_v2_correct.py` uses full 8-dimension `behavioral_distance()` from `sbg/distance.py` |
| **Grid** | `w_static ∈ {0.0, 0.2, 0.4, 0.6, 0.8, 1.0}`, preregistered, DEV-only selection |
| **Methodology change** | Yes — correction of implementation defect, not a new design decision |

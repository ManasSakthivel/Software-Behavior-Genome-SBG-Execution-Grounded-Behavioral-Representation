# Edit-Size Benchmark Redesign Analysis
## Software Behavior Genome (SBG) — B01 Resolution

**Date:** 2026-10-26  
**Branch:** `remediation/sbg-v2`  
**Status:** DECISION MADE — implementation pending  
**This document does not constitute a protocol freeze. It must be referenced in FREEZE_V8.json before any test scoring.**

---

## 1. Reproduced finding

The reversed edit-size AUROC of **0.9667** (test split, 259 pairs) and **0.9569** (dev split, 345 pairs) is independently reproduced from the committed artifacts at every session.

Reproduction command:
```bash
python3 experiments/final/edit_size_analysis.py \
  --split test \
  --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl \
  --no-write
```
Expected: `edit_size_reversed_auroc = 0.966703`

---

## 2. Root cause

### 2.1 SC (semantics-changing) mutations: always 1 site

Every SC mutator (`OffByOneMutator`, `OperatorMutator`, `ConstantMutator`, etc.) targets exactly one mutation site per pair. This produces:
- **2–7 changed lines** (typically 2 — one removed, one added line at the mutation site)
- Maximum observed in dev split: 7 lines (some SC-13 transformations produce 3-line mutations)

### 2.2 SP (semantics-preserving) transformations: renames ALL occurrences

SP-1 selects `k = random.randint(1, max(1, len(candidates)))` variables and renames ALL occurrences of each. SP-2 similarly renames ALL occurrences of `k` functions. For a typical program with 5 variables, each appearing 3 times, SP-1 renames 3 variables × 3 occurrences = 9 changes = 18 changed lines.

Observed statistics on the dev split:

| Transformation | Median changed lines | 90th-pctile | SP pairs at 2–5 lines |
|---|---|---|---|
| SP-1 (variable rename) | 14 | 50+ | 3/27 (11%) |
| SP-2 (function rename) | 16 | 40+ | 7/27 (26%) |
| SP-3 (dead code insert) | 65 | 80+ | 0/27 (0%) |
| SP-4 (comment strip) | 21 | 34 | 0/27 (0%) |
| SP-5 (loop rewrite) | 4 | 8 | 20/24 (83%) — naturally small |
| SP-6 (condition rewrite) | 20 | 26 | 0/27 (0%) |
| SP-7 (inline function) | 13 | 48 | 0/11 (0%) |
| SP-8 (extract function) | 9 | 14 | 3/10 (30%) |
| SP-9 (constant fold) | 2 | 2 | 3/3 (100%) — naturally small |
| SP-11 (data structure) | 21 | 24 | 0/6 (0%) |

**SC range (all):** 2–7 lines. **SP range (most):** 8–152 lines. The distributions barely overlap on the v6 benchmark.

### 2.3 Why this creates the confound

Because every CHANGED pair is SC (2–7 lines) and every EQUIVALENT pair with ≥6 changed lines is SP (8–152 lines), a predictor that outputs `1 if edit_size <= 5 else 0` achieves ~95%+ accuracy. The reversed AUROC of 0.967 quantifies this.

**This is not an artifact of random chance.** It is structural: the benchmark was designed with full-occurrence renaming (large SP edits) and single-site mutations (small SC edits). The confound is complete within the EVALUABLE subset.

---

## 3. Redesign options evaluated

### Option A: `max_names=1` cap on SP-1 and SP-2 (RECOMMENDED)

**Mechanism:** Modify the `apply()` methods of `sp1_variable_rename.py` and `sp2_function_rename.py` to accept a `max_names` parameter (default `None` for backward compatibility). When `max_names=1`, cap `k = min(k, max_names)`, ensuring exactly 1 variable or function is renamed per pair.

**Semantics-preserving guarantee:** Renaming ALL occurrences of ONE variable/function is semantics-preserving. The variant is behaviourally identical to the base because no computation changes — only one identifier's spelling changes consistently throughout. This is the same guarantee as the current transformer, just applied to a smaller subset.

**Expected edit-size impact:**
- SP-1 with `max_names=1`: rename 1 variable; if it appears `n` times, produce `2n` changed lines. For variables appearing 2–5 times: **4–10 changed lines**.
- SP-2 with `max_names=1`: rename 1 function; if called `m` times: `2(1 + m)` changed lines (def + calls). For functions called 1–3 times: **4–8 changed lines**.
- **Overlap with SC (2–7 lines): substantial**.

**Impact on other SP types:** SP-3 (dead code, 20–82 lines), SP-4 (comment strip, 10–34 lines), SP-6 (condition rewrite, 12–26 lines) remain large. The benchmark will still have some large-SP pairs, creating a partial confound. However, a significant fraction of SP pairs will now fall in the 2–10 line range alongside SC, breaking the total confound.

**Expected revised reversed AUROC:** With SP-1/SP-2 at 4–10 lines overlapping SC at 2–7 lines, the reversed edit-size AUROC is expected to drop from 0.967 to approximately 0.60–0.75. The exact value depends on the class balance in the new dataset and must be measured after generation — NOT before.

**Implementation:** ~10 lines of code per transformer (add `max_names` parameter; add `k = min(k, max_names) if max_names else k`). No change to semantics or test logic. Must add regression test confirming `max_names=1` produces at most 1 renamed identifier.

### Option B: Discard SP types that produce large edits

Remove SP-3, SP-4, SP-6, SP-7, SP-8, SP-11 from the fresh benchmark.

**Problem:** Reduces transformation family diversity significantly. Removes interesting semantic-preserving transformations. Creates a different selection bias (smaller edit sizes across the board). Not recommended.

### Option C: Multi-site SC (SC applies to all matching sites, not just 1)

Modify SC mutators to rename all sites of a given mutation type.

**Problem:** Completely changes the semantics of SC. A multi-site mutation changes more behavior and is harder to construct a witness for. The SC identity (single targeted change) is part of the scientific design. Not recommended.

### Option D: Matched sampling (post-hoc stratification)

After generating the benchmark, draw only pairs within matching edit-size bins across classes.

**Problem:** This is done after knowing edit sizes → requires careful blinding from scores. Currently only 19% of SP pairs fall in 2–5 line bins, so this would produce a severely imbalanced sample. Not recommended as primary strategy; may be used as a sensitivity check after freeze.

---

## 4. Decision

**DECISION: Implement Option A — `max_names=1` on SP-1 and SP-2 for all new benchmark generation.**

Rationale:
1. Semantics-preserving guarantee is maintained.
2. Edit-size distributions will substantially overlap between SC and SP-1/SP-2.
3. The implementation is minimal (2 transformers, ~10 lines each).
4. It is a generator-level constraint decided before seeing any test data.
5. The remaining SP types (SP-3, SP-4, SP-6, etc.) will still produce larger edits, creating a realistic distribution.
6. Edit-size must remain a reported baseline so the residual confound, if any, is visible.

**Scope:** `max_names=1` applies to:
- `SP-1`: rename exactly 1 variable (all its occurrences)
- `SP-2`: rename exactly 1 function (all its occurrences)
- All other SP types: unchanged

**NOT applied to:** SP-3 through SP-12. These transformations either naturally produce small edits (SP-5, SP-9) or their edit size is determined by program structure rather than a "how many names" decision.

---

## 5. Validation plan (pre-freeze)

Before freezing the protocol, the following must be checked on the development split ONLY:

1. **Regenerate a sample of SP-1/SP-2 pairs** using `generate_v7_dataset.py` with `max_names=1`.
2. **Run `edit_size_analysis.py`** on the regenerated dev pairs. The reversed edit-size AUROC must be < 0.80 (well below the 0.967 baseline). The exact target is not pre-specified — the point is that the distribution visibly overlaps.
3. **Verify semantics preservation**: run `data_integrity.py --strict` on the regenerated dataset. The execution-based check must confirm that all EQUIVALENT pairs behave identically.
4. **Document the actual edit-size distributions** of each SP and SC type.
5. **Include edit_size_reversed as a required baseline** in the final evaluation.

**Do not adjust `max_names` after seeing the edit-size AUROC on development data.** The `max_names=1` decision is locked at this point.

---

## 6. Implementation specification

### `sp1_variable_rename.py` change

In `VariableRenameTransformation.apply()`, change:
```python
k = random.randint(1, max(1, len(candidates)))
```
to:
```python
k = random.randint(1, max(1, len(candidates)))
if max_names is not None:
    k = min(k, max_names)
```

Add `max_names: Optional[int] = None` parameter to `apply()`.

### `sp2_function_rename.py` change

In `FunctionRenameTransformation.apply()`, change:
```python
candidates = random.sample(func_names, k=random.randint(1, max(1, len(func_names))))
```
to:
```python
n_to_rename = random.randint(1, max(1, len(func_names)))
if max_names is not None:
    n_to_rename = min(n_to_rename, max_names)
candidates = random.sample(func_names, k=n_to_rename)
```

### `generate_v7_dataset.py` change

Pass `max_names=1` to all SP-1 and SP-2 `apply()` calls. Record `max_names_sp1=1` and `max_names_sp2=1` in the dataset manifest.

### Regression tests to add

- `test_sp1_max_names_1_renames_exactly_one_variable()`: verify that the rename map has exactly 1 entry.
- `test_sp2_max_names_1_renames_exactly_one_function()`: same.
- `test_sp1_max_names_1_semantics_preserved()`: execute base and variant with shared inputs; assert same return value.
- `test_sp2_max_names_1_edit_size_small()`: verify edit size ≤ 12 lines for a simple 5-function program.

---

## 7. Effect on class balance and pair counts

`max_names=1` affects only the number of changed lines, not the EQUIVALENT/CHANGED class balance or which programs are eligible. The number of pairs per program and the class balance remain the same.

The only reduction: some SP-1/SP-2 pairs that previously changed many names (e.g., all 8 local variables in a function) now produce a smaller variant. The variant is still a valid EQUIVALENT pair, just with fewer renamed symbols.

---

## 8. Remaining confound after max_names=1

The redesign reduces but does not eliminate the edit-size confound:
- SP-3 (dead code insert): still 20–82 changed lines, no CHANGED counterpart
- SP-4 (comment strip): still 10–34 changed lines
- SP-6 (condition rewrite): still 12–26 changed lines
- These SP types will still produce an overrepresented tail of large edits

**Required mitigations:**
1. Report edit-size-stratified AUROC alongside the headline number (already in the plan).
2. Include reversed edit-size as a primary baseline (already in the plan).
3. Interpret any AUROC improvement within equal-edit-size bins as the main evidence for SBG over edit size.

---

## 9. Instruction to the generator

When generating the fresh v7 benchmark:
```python
# In generate_v7_dataset.py
SP1_MAX_NAMES = 1   # max_names for SP-1 (variable rename)
SP2_MAX_NAMES = 1   # max_names for SP-2 (function rename)
# All other SP transformations: max_names=None (default, unchanged)
```

This decision is **frozen at this point** and must not be changed after the dataset is generated.

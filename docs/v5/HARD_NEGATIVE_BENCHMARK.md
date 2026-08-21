# Hard Negative Benchmark — SBG v5

## Overview

The Hard Negatives Benchmark is a set of **12 adversarial program pairs** designed to expose the failure modes of trivial shortcut detectors used in semantic behavioral grading (SBG). Each pair is crafted so that a specific heuristic — exception fraction, execution volume, call count, structural similarity, etc. — produces the **wrong label**, while the ground-truth behavioral comparison produces the **correct label**.

All programs are self-contained Python 3, require no external dependencies, and are runnable directly with `python3`.

---

## Directory Structure

```
benchmark/v5/hard_negatives/
├── oracle.py
├── pair_01_same_exception_different_behavior/
│   ├── base_program.py
│   ├── variant_program.py
│   ├── metadata.json
│   └── test_inputs.py
├── pair_02_same_volume_different_behavior/
│   └── ...
├── pair_03_same_call_count_different_order/
│   └── ...
├── pair_04_rename_invariant/
│   └── ...
├── pair_05_structural_change_same_behavior/
│   └── ...
├── pair_06_constant_mutation/
│   └── ...
├── pair_07_dead_code_insertion/
│   └── ...
├── pair_08_wrong_variable/
│   └── ...
├── pair_09_operator_mutation/
│   └── ...
├── pair_10_exception_same_behavior/
│   └── ...
├── pair_11_loop_boundary/
│   └── ...
└── pair_12_data_structure_equivalent/
    └── ...
```

---

## Label Distribution

| Label   | Count |
|---------|-------|
| CHANGED | 7     |
| EQUIV   | 5     |
| **Total** | **12** |

---

## Pair Catalogue

### Pair 01 — `pair_01_same_exception_different_behavior`
**Ground truth:** CHANGED  
**Shortcut defeated:** `exception_fraction`

Both programs raise `ValueError` on the same negative inputs. The exception fraction is identical. However, the non-exception path returns `x*2` (base) vs `x*3` (variant). A detector that uses exception rate as a proxy for behavioral equivalence will label this **EQUIV** — wrong.

| | Base | Variant |
|---|---|---|
| On negative input | `ValueError` | `ValueError` |
| On positive input | `x * 2` | `x * 3` ← CHANGED |

---

### Pair 02 — `pair_02_same_volume_different_behavior`
**Ground truth:** CHANGED  
**Shortcut defeated:** `execution_volume`

Both programs loop exactly N times. Total iteration count is identical for every test input. Base computes `sum(1..N)`; variant computes `product(1..N)`. An execution-volume shortcut that counts loop iterations sees no difference and labels this **EQUIV** — wrong.

---

### Pair 03 — `pair_03_same_call_count_different_order`
**Ground truth:** CHANGED  
**Shortcut defeated:** `call_count`

Both programs call `validate()`, `process()`, and `finalize()` exactly once. A call-count shortcut sees three identical function names called three times and labels **EQUIV**. The ORDER of those calls determines behavior: base filters `None` values before processing (safe), variant processes before filtering (crashes on `None` inputs).

**Critical test inputs:** lists containing `None` values.

---

### Pair 04 — `pair_04_rename_invariant`
**Ground truth:** EQUIV  
**Shortcut defeated:** `name_similarity`

Every identifier is renamed: `compute_sum(items)` → `calculate_total(collection)`, accumulator `total` → `running_total`. Zero token overlap with the base. A name-similarity shortcut sees completely different tokens and labels **CHANGED** — wrong. The logic is byte-for-byte equivalent.

---

### Pair 05 — `pair_05_structural_change_same_behavior`
**Ground truth:** EQUIV  
**Shortcut defeated:** `structural_similarity`

Base: one monolithic function (~30 lines) that filters negatives, squares elements, sorts, and sums the top half.  
Variant: the same logic decomposed into four named helpers (`_filter_negatives`, `_square_elements`, `_sort_ascending`, `_sum_top_half`).

The AST shapes are completely different, the call graph is completely different, the line counts differ significantly. Yet behavior is identical on all inputs.

---

### Pair 06 — `pair_06_constant_mutation`
**Ground truth:** CHANGED  
**Shortcut defeated:** `structural_similarity`

Binary search implementation. The only change is inside the `mid` calculation:

```python
# base
mid = lo + (hi - lo) // 2

# variant
mid = lo + (hi - lo + 1) // 2  # upper-mid bias
```

Structural similarity is effectively 1.0 — one integer constant differs. On most inputs both programs agree. On even-length arrays with the target in the upper half, the biased mid causes divergence. Test inputs include these boundary cases.

---

### Pair 07 — `pair_07_dead_code_insertion`
**Ground truth:** EQUIV  
**Shortcut defeated:** `coverage_size`

Variant inserts an `if False:` block that is syntactically present but never executes. A coverage-size shortcut that counts lines, branches, or static code paths sees more content in the variant and labels **CHANGED** — wrong. Actual behavior is identical.

```python
if False:
    # Dead code: this branch is unreachable by design
    result = n * 999
    print(f"debug: {result}")
    return result
```

---

### Pair 08 — `pair_08_wrong_variable`
**Ground truth:** CHANGED  
**Shortcut defeated:** `structural_similarity`

Exactly one variable name on the RHS differs:

```python
# base — correct swap
lst[i], lst[j] = lst[j], lst[i]

# variant — no-op identity assignment
lst[i], lst[j] = lst[i], lst[j]
```

Structural similarity is ~1.0. Yet base performs a real swap; variant is a no-op. Any test with `i != j` exposes the difference.

---

### Pair 09 — `pair_09_operator_mutation`
**Ground truth:** CHANGED  
**Shortcut defeated:** `structural_similarity`

Single operator change: `>=` → `>`. All inputs except `age == 18` produce the same result. The exact boundary input `18` is included in `test_inputs.py` to guarantee exposure.

```python
# base
return age >= 18   # 18 → True

# variant
return age > 18    # 18 → False  ← CHANGED
```

---

### Pair 10 — `pair_10_exception_same_behavior`
**Ground truth:** EQUIV  
**Shortcut defeated:** `exception_fraction`

Base uses `try/except` — exceptions are raised and caught internally for invalid inputs. Variant uses `isinstance` guards — no exception ever propagates. Exception fraction: base > 0, variant = 0. An exception-fraction shortcut sees this difference and labels **CHANGED** — wrong. Both return identical values for all inputs.

---

### Pair 11 — `pair_11_loop_boundary`
**Ground truth:** CHANGED  
**Shortcut defeated:** `execution_volume`

Off-by-one in the loop upper bound: `range(n)` vs `range(n+1)`. Per-iteration logic (`results.append(i*i)`) is identical. A volume shortcut that normalises by the input value `n` may miss the one extra iteration. Output length always differs by 1 for `n > 0`.

---

### Pair 12 — `pair_12_data_structure_equivalent`
**Ground truth:** EQUIV  
**Shortcut defeated:** `import_diff`

Base uses a `list`-backed `Stack`. Variant uses `collections.deque`. The variant adds `from collections import deque` — an import not present in base. An import-diff shortcut flags this as a functional change and labels **CHANGED** — wrong. The public API (`push`, `pop`, `peek`, `size`, `is_empty`) and all observable behaviors are identical.

---

## Metadata Schema

Each pair directory contains a `metadata.json` with the following fields:

```json
{
  "pair_id": "pair_01_...",
  "ground_truth": "EQUIV" | "CHANGED",
  "shortcut_defeated": "<shortcut name>",
  "description": "<human-readable explanation>",
  "expected_exception_fraction_same": true | false,
  "expected_call_count_same": true | false,
  "expected_volume_same": true | false,
  "boundary_inputs_required": true | false
}
```

`boundary_inputs_required: true` means the divergence is only exposed on specific edge-case inputs, not random inputs.

---

## Oracle

**File:** [`benchmark/v5/hard_negatives/oracle.py`](benchmark/v5/hard_negatives/oracle.py)

The oracle:
1. Imports each pair's `base_program` and `variant_program` via `importlib`
2. Loads `TEST_INPUTS` from `test_inputs.py`
3. Calls `run(TEST_INPUTS)` on both programs
4. Compares outputs (return values + exception strings)
5. Determines behavioral equivalence
6. Evaluates three shortcut detectors on each pair: `exception_fraction`, `volume`, `call_count`
7. Prints a summary table showing which shortcut is fooled per pair

### Running the Oracle

```bash
cd benchmark/v5/hard_negatives
python3 oracle.py
```

### Expected Output Format

```
--------------------------------------------------------------
HARD NEGATIVES ORACLE — SUMMARY
--------------------------------------------------------------
Pair                                           GT      Oracle  Shortcut EF     Vol    CC
--------------------------------------------------------------
pair_01_same_exception_different_behavior      CHANGED CHANGED exc_frac FAIL   PASS   PASS  ✓
...
--------------------------------------------------------------
TOTALS                                                  12/12           X/12   X/12   X/12
--------------------------------------------------------------
```

---

## Shortcut Detector Definitions

| Shortcut | Definition | Failure Type |
|---|---|---|
| `exception_fraction` | Fraction of test outputs that are exception strings | Both over-triggers (CHANGED when EQUIV) and under-triggers (EQUIV when CHANGED) |
| `execution_volume` | Total output length as proxy for loop iterations | Misses off-by-one and operator mutations when volume normalizes out |
| `call_count` | Number of top-level `def` statements in source | Misses ordering mutations and refactorings |
| `name_similarity` | Token overlap between source identifiers | Misses rename-invariant EQUIV pairs |
| `structural_similarity` | AST edit distance | Misses 1-character mutations AND refactorings equally |
| `coverage_size` | Total executable lines/branches | Fooled by dead code insertion |
| `import_diff` | New imports in variant not in base | Fooled by data-structure substitutions that add stdlib imports |

---

## Shortcut Coverage Matrix

| Pair | CHANGED? | EF Fooled | Vol Fooled | CC Fooled | Struct Fooled | Name Fooled | Cover Fooled | Import Fooled |
|------|----------|-----------|------------|-----------|---------------|-------------|--------------|---------------|
| 01 | ✓ | **YES** | — | — | — | — | — | — |
| 02 | ✓ | — | **YES** | — | — | — | — | — |
| 03 | ✓ | — | — | **YES** | — | — | — | — |
| 04 | — | — | — | — | — | **YES** | — | — |
| 05 | — | — | — | — | **YES** | — | — | — |
| 06 | ✓ | — | — | — | **YES** | — | — | — |
| 07 | — | — | — | — | — | — | **YES** | — |
| 08 | ✓ | — | — | — | **YES** | — | — | — |
| 09 | ✓ | — | — | — | **YES** | — | — | — |
| 10 | — | **YES** | — | — | — | — | — | — |
| 11 | ✓ | — | **YES** | — | — | — | — | — |
| 12 | — | — | — | — | — | — | — | **YES** |

---

## Design Principles

1. **Each pair targets exactly one shortcut.** The failure mode is deliberate and documented.
2. **EQUIV pairs are as important as CHANGED pairs.** False positives (labeling EQUIV as CHANGED) are as damaging as false negatives.
3. **Boundary inputs are explicit.** Pairs that only diverge on specific inputs include those inputs in `test_inputs.py`.
4. **No external dependencies.** All programs run with `python3` stdlib only.
5. **Programs are short.** Every program is 10–55 lines. The logic is immediately legible.
6. **The oracle uses behavioral comparison only.** It does not use any shortcut; it compares actual return values.

---

## Related Artifacts

- Design JSON: [`artifacts/v5/HARD_NEGATIVE_BENCHMARK_DESIGN.json`](artifacts/v5/HARD_NEGATIVE_BENCHMARK_DESIGN.json)
- Corpus: [`benchmark/v5/corpus/`](benchmark/v5/corpus/)
- SC3 Exposure Design: [`artifacts/v5/SC3_EXPOSURE_DESIGN.json`](artifacts/v5/SC3_EXPOSURE_DESIGN.json)

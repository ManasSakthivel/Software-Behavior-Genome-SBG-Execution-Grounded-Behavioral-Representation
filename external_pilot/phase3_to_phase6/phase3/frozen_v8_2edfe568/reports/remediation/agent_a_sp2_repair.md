# Remediation Report: Agent A — SP-2 Transformation Repair

**Date**: 2026-10-25  
**Branch**: `remediation/sbg-v2`  
**Agent**: Agent A  
**Status**: Complete  

---

## 1. Defect Confirmation

Prior to code changes, the SP-2 (`FUNCTION_RENAME`) transformer bug was independently verified using the target AST transformation snippet:

### Verification Snippet & Output

```python
import ast, copy, sys
sys.path.insert(0, '.')
from benchmark.transformations.preserving.transformations.sp2_function_rename import FunctionRenameTransformation
src = '''
class Foo:
    def allow(self, x):
        return x > 0
    def check_all(self, items):
        return all(self.allow(i) for i in items)
'''
t = FunctionRenameTransformation()
from benchmark.transformations.preserving.transformations.sp2_function_rename import _FunctionRenamer
tree = ast.parse(src)
rename_map = {'allow': 'fn_allow'}
new_tree = _FunctionRenamer(rename_map).visit(copy.deepcopy(tree))
ast.fix_missing_locations(new_tree)
result = ast.unparse(new_tree)
print('Has self.allow (defect):', 'self.allow' in result)
print('Has self.fn_allow (correct):', 'self.fn_allow' in result)
```

**Output**:
```text
Has self.allow (defect): True
Has self.fn_allow (correct): False
```

### Cause
`_FunctionRenamer` inherited from `ast.NodeTransformer` and implemented `visit_FunctionDef`, `visit_AsyncFunctionDef`, and `visit_Call` (only matching `node.func` when it was an `ast.Name`). It failed to visit `ast.Attribute` nodes (`self.<method>`), leaving attribute references dangling while the method definition was renamed.

---

## 2. Files Changed and Implementation Details

### File Scope and Edits

1. **`benchmark/transformations/preserving/transformations/sp2_function_rename.py`**
   - Added `visit_Attribute(self, node)` to `_FunctionRenamer`:
     ```python
     def visit_Attribute(self, node):
         self.generic_visit(node)
         if node.attr in self.rename_map:
             new_node = copy.copy(node)
             new_node.attr = self.rename_map[node.attr]
             return new_node
         return node
     ```
   - Updated `FunctionRenameTransformation` to track `self.last_rename_map`.
   - Updated `validate(self, original: str, transformed: str)` to enforce stricter post-transformation invariants: verifies that all old names in `rename_map` no longer appear as method/function definitions in the transformed code, and all new names are present in the transformed definitions.

2. **`tests/test_sp2_repair.py`** (New File)
   - Created dedicated regression test suite covering:
     - `test_attribute_reference_is_renamed`: Verifies `self.old()` is renamed to `self.new()`.
     - `test_bare_function_call_still_works`: Verifies bare function calls (`helper()`) continue to be renamed correctly.
     - `test_class_with_multiple_methods_renamed`: Verifies multiple method renames within a class remain consistent.
     - `test_no_false_positives_on_library_attrs`: Verifies library methods (`list.append`, `dict.update`) are not renamed.
     - `test_transformed_class_runs_without_attribute_error`: Verifies runtime execution of transformed classes without `AttributeError`.
     - `test_data_integrity_detects_zero_sp2_defects_on_repaired_pairs`: Prospective synthetic dataset generation with repaired SP-2 verifying 0 defects under `data_integrity.py`.

3. **`benchmark/scripts/generate_v7_dataset.py`** (New File)
   - Reproducible script to generate benchmark version `v7`.
   - Reads base programs and program-to-split assignments from `benchmark/datasets/v6/`.
   - Re-applies all SP-1..SP-12 and SC-1..SC-14 operators.
   - Validates compilability, non-no-op diffs, and reachability/observability.
   - Runs `data_integrity.py` and produces `benchmark/datasets/v7/manifest.json`.

4. **`benchmark/datasets/v7/`** (New Dataset Version Directory)
   - Created `benchmark/datasets/v7/manifest.json`, `pairs_train.jsonl`, `pairs_dev.jsonl`, `pairs_val.jsonl`, `pairs_test.jsonl`, and smoke-test variant files under `benchmark/datasets/v7/variants/`.

5. **`docs/current/BENCHMARK_LABEL_DEFECT_SP2.md`**
   - Updated document with remediation status, regression test list, v7 generation script details, and confirmation of v6 benchmark preservation as an immutable historical record.

---

## 3. Test Results (Exact Counts)

### A. Targeted Regression Tests
Command:
```bash
python3 -m pytest tests/test_sp2_repair.py tests/test_data_integrity.py -v --tb=short
```
Output:
- `tests/test_sp2_repair.py`: 6 passed
- `tests/test_data_integrity.py`: 9 passed
- **Total**: **15 passed, 0 failed** in 4.57s

### B. Full Test Suite Regression Check
Command:
```bash
python3 -m pytest sbg/ tests/ -q --tb=short 2>&1 | tail -5
```
Output:
- **738 passed, 6 warnings** in 163.21s (0 regressions across the entire repository).

### C. Data Integrity on Committed v6 Dataset (Historical Record Verification)
Command:
```bash
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v6
```
Output:
```json
{
  "dataset": "benchmark/datasets/v6",
  "n_pairs": 2340,
  "n_programs": 60,
  "defect_counts": {
    "sp2_dangling_method_reference": 75
  },
  "sp2_equivalent_pairs_by_split": {
    "train": 84,
    "dev": 30,
    "val": 27,
    "test": 39
  },
  "sp2_dangling_by_split": {
    "train": 30,
    "dev": 13,
    "val": 10,
    "test": 22
  }
}
```
Defect count is exactly 75 `sp2_dangling_method_reference` defects across 2,340 pairs, confirming the documented baseline without modifications to v6.

---

## 4. Benchmark v7 Plan and Smoke Test Results

### Generator Implementation
- `benchmark/scripts/generate_v7_dataset.py` extracts program-to-split assignments from `benchmark/datasets/v6/` (60 base programs across train: 28, dev: 10, val: 9, test: 13).
- Applies all SP and SC operators with the repaired SP-2 operator.
- Enforces strict candidate rejection for syntax errors, AST no-ops, and unreachable mutations.

### Smoke Test Execution
Command:
```bash
python3 benchmark/scripts/generate_v7_dataset.py --smoke-test
```
Output:
```text
Loading program split definitions from benchmark/datasets/v6...
Found 60 base programs across 4 splits in v6.
Running smoke test on representative programs: ['api_rest_crud_mock', 'api_event_bus', 'api_rate_limiter']
[train] programs=1 pairs=45 (EQUIV=21 CHANGED=24) rejected=33
[dev] programs=1 pairs=47 (EQUIV=23 CHANGED=24) rejected=31
[val] programs=0 pairs=0 (EQUIV=0 CHANGED=0) rejected=0
[test] programs=1 pairs=41 (EQUIV=17 CHANGED=24) rejected=37

Generation completed in 2.73s (3 programs).
Estimated full dataset generation runtime (60 programs): ~54.6s.

Running data integrity check on generated v7 dataset...
Manifest written to benchmark/datasets/v7/manifest.json
SUCCESS: Data integrity check passed with 0 defects (dangling SP-2 references: 0).
```

### Data Integrity Result on v7 Smoke Test
- Total generated smoke test pairs: 133
- Dangling SP-2 method references: **0**
- Active defects: **0**

---

## 5. Limitations & Remaining Issues

1. **v6 Dataset Contamination**: The published v6 dataset remains contaminated by 75 SP-2 pairs that raise `AttributeError`. These pairs remain intact in `benchmark/datasets/v6/` for historical reproducibility and audit purposes.
2. **Full v7 Generation**: The full v7 benchmark dataset (60 programs, ~2,340 pairs) can be generated on demand using `python3 benchmark/scripts/generate_v7_dataset.py --all` in ~55 seconds. As instructed, only the smoke test dataset was generated to keep the review process lightweight and compliant with instructions.

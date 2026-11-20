# Benchmark label defect: SP-2 variants that are not equivalent

`benchmark/transformations/preserving/transformations/sp2_function_rename.py`
renames function and **method** definitions but previously rewrote only `ast.Name` call
sites. For class-based programs it therefore renamed `def allow(...)` while
leaving `self.allow(...)` untouched. The variant raised `AttributeError`, yet the
pair was labelled EQUIVALENT.

Detected by `experiments/final/data_integrity.py` (static, read-only) and
confirmed by execution with `experiments/final/sp2_execution_check.py`:

| Split | EQUIVALENT SP-2 pairs | flagged |
|---|---|---|
| train | 84 | 30 |
| dev | 30 | 13 |
| val | 27 | 10 |
| test | 39 | 22 |
| **total** | 180 | **75** |

Running the flagged pairs' programs in v6: base passes and variant fails with
`AttributeError` in **70**; 2 pass in both; 3 fail in the base too
(`reports/remediation/results/sp2_dangling_execution_check.json`).

## Remediation and Fix Status (Implemented)

1. **Transformer Repair (`sp2_function_rename.py`)**:
   - Added `visit_Attribute` to `_FunctionRenamer` to rename `ast.Attribute` nodes (`node.attr`) when `node.attr in self.rename_map`. This guarantees method calls (such as `self.method()`) are updated consistently with method definitions.
   - Updated `validate()` to enforce stricter checks verifying that all old names in `rename_map` no longer appear as function/method definitions in the transformed AST and all new names do appear.

2. **Regression Test Suite (`tests/test_sp2_repair.py`)**:
   - `test_attribute_reference_is_renamed`: Confirms class `self.old()` is renamed to `self.new()`.
   - `test_bare_function_call_still_works`: Confirms bare function calls (`foo()`) continue to be renamed correctly.
   - `test_class_with_multiple_methods_renamed`: Confirms multiple method renames within a class remain consistent.
   - `test_no_false_positives_on_library_attrs`: Confirms standard library attributes (`list.append`, `dict.update`) are untouched.
   - `test_transformed_class_runs_without_attribute_error`: Confirms runtime execution of transformed classes without `AttributeError`.
   - `test_data_integrity_detects_zero_sp2_defects_on_repaired_pairs`: Confirms prospective generation produces 0 dangling method defects in `data_integrity.py`.

3. **v7 Dataset Generation Plan & Script (`benchmark/scripts/generate_v7_dataset.py`)**:
   - Self-contained and reproducible generator reading base programs from `benchmark/datasets/v6/` and applying the repaired transformations.
   - Validated via smoke test producing candidate variants with 0 SP-2 dangling method reference defects under `data_integrity.py`.
   - Manifest recorded at `benchmark/datasets/v7/manifest.json`.

4. **v6 Dataset Preserved as Historical Record**:
   - The committed `benchmark/datasets/v6/` dataset remains untouched as published (preserving the exact 75 documented defect pairs for reproducibility and historical audit).

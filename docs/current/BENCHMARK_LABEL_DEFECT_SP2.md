# Benchmark label defect: SP-2 variants that are not equivalent

`benchmark/transformations/preserving/transformations/sp2_function_rename.py`
renames function and **method** definitions but rewrites only `ast.Name` call
sites. For class-based programs it therefore renames `def allow(...)` while
leaving `self.allow(...)` untouched. The variant raises `AttributeError`, yet the
pair is labelled EQUIVALENT.

Detected by `experiments/final/data_integrity.py` (static, read-only) and
confirmed by execution with `experiments/final/sp2_execution_check.py`:

| Split | EQUIVALENT SP-2 pairs | flagged |
|---|---|---|
| train | 84 | 30 |
| dev | 30 | 13 |
| val | 27 | 10 |
| test | 39 | 22 |
| **total** | 180 | **75** |

Running the flagged pairs' programs: base passes and variant fails with
`AttributeError` in **70**; 2 pass in both; 3 fail in the base too
(`reports/remediation/results/sp2_dangling_execution_check.json`).

## Handling

* **Labels were not changed** and no pair was removed (prohibition: no label or
  inclusion change to move a metric). The committed v6 results stand as
  published and are explicitly "observed / possibly contaminated".
* Consequence for the 259-pair v6 test set: any SP-2 pair among the 22 flagged
  ones that was evaluated carries an EQUIVALENT label that execution may
  contradict, which would inflate false positives in a way unrelated to
  method quality. The per-pair effect was not quantified because doing so means
  choosing an exclusion rule after seeing test scores.
* Fix path: repair the transformation to rename attribute references consistently
  (or skip methods), regenerate as a new benchmark version, re-run
  `data_integrity.py --strict`, and build the fresh split from it.

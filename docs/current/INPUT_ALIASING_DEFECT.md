# Input aliasing between extractions (fixed in code; historical artifacts unchanged)

`protocol.synthesise_inputs` returned lists taken from module-level batteries
(`LIST_BATTERY`, ...). An in-place sorter such as `heapsort(arr)` mutates its
argument, so inputs were already sorted for every extraction after the first in a
process. The same program therefore produced different traces depending on
extraction order (`sort_heapsort`, `output_free_v6`: **8771** events cold,
**8855** warm; reproduced in three fresh processes: `[8771, 8855, 8855, 8855]`).

Root cause confirmed by diffing traces: identical trace index, extra `_sift_down`
line events in the warm run; and by showing `LIST_BATTERY[2]`, `[3]`, `[5]` are
mutated by one extraction.

## Fix

`synthesise_inputs` now returns `copy.deepcopy(inputs)`. After the fix, four
consecutive extractions give `[8771, 8771, 8771, 8771]`.
Regression tests: `tests/test_gate_and_stdlib_regression.py`
(`test_synthesised_inputs_do_not_alias_the_module_batteries`,
`test_repeated_extraction_is_order_independent`).

## Effect on committed results (measured, not corrected)

* Base programs in `programs_v6test_output_free_v6.json`: re-extracted after the
  fix, all 7 evaluated test bases match the committed event counts exactly.
* Committed **variant** records for `sort_heapsort` were produced warm: 29 of the
  82 evaluated sort_heapsort/sort_counting_sort variants differ from a pristine
  re-extraction (e.g. `sp-1`: committed 8855, pristine 8771). Only `sort_heapsort`
  differs; counting sort does not mutate its input.
* So committed `sort_heapsort` pairs compare a pristine base with a variant traced
  on pre-sorted data. For EQUIVALENT pairs this adds a spurious behavioural
  difference; `sort_heapsort` has the highest per-program AUROC (0.803) in the
  259-pair set. The size of the effect on the AUROC was **not** computed: doing
  so means re-scoring the observed test split.
* `verify_v6_unchanged.py` after the fix: 13 programs, 0 violations, no
  nondeterministic programs (`reports/remediation/logs/verify_v6_unchanged_after_fix.txt`).

Other in-place programs in train/dev/val may be affected the same way and were
not enumerated.

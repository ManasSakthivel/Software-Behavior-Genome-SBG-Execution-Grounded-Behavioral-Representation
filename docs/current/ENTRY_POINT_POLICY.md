# Entry-point policy (protocol `output_free_v8`)

Status: implemented and unit-tested; **not scored**. No v8 AUROC exists and none
may be computed until `EVALUATION_PLAN_V8.md` is frozen and approved.

## Defect in v6/v7 (confirmed)

`experiments/final/protocol.py::select_entry_output_free` chooses which function
to trace from function **names**: a `test_*` / private / `main` / `demo*`
exclusion rule, a 23-name priority list, and "alphabetically first annotated".
The benchmark's SP-2 transformation renames functions (mostly with an `fn_`
prefix), so each rule changes under a semantics-preserving edit:

| Base name | After SP-2 | Effect |
|---|---|---|
| `test_heapsort` | `fn_test_heapsort` | no longer matches `test_*`; the self-test driver is traced |
| `_sift_down` | `fn__sift_down` | no longer private; selected instead of `heapsort` |
| `parse_int` | `decode_int` | alphabetical order shifts |
| `evaluate` | `fn_evaluate` | priority-name hit lost |

Measured on the committed v6 test record (259 evaluated pairs, 138 EQUIVALENT):

* 19 EQUIVALENT pairs have different entry names in base and variant (naive).
* 11 remain after stripping the `fn_` prefix.
* 9 remain after matching SP-2 pairs by a name-free structural fingerprint
  (two of the 11 are `parse_int` -> `decode_int`, the same function renamed).
* 2 trace a renamed self-test driver (`fn_test_heapsort`, `fn_test_tokenizer`).
* The v7 dev record behind tau* has 9 more driver traces (see
  `consistency_check.KNOWN_HISTORICAL_DRIVER_TRACES`).

`audit_recompute.py` reproduces these counts; `tests/test_entry_policy.py` and
`tests/test_audit_recompute.py` pin them.

## Policy v8 (`experiments/final/entry_policy.py`)

No rule reads an identifier's spelling.

1. A top-level function with no required parameters that contains `assert` or is
   called from the `__main__` guard is a **driver** and is excluded.
2. A function referenced by a non-driver function is a **helper** and is
   excluded; module-level call-graph roots remain as candidates.
3. Candidates whose parameters cannot be synthesised from the fixed batteries
   are discarded.
4. Tie-break: larger call closure, fully annotated, larger required arity.
5. If structurally different candidates still tie, raise `AmbiguousEntryPoint`
   (recorded as failure kind `ambiguous_entry_point`) instead of guessing.

The class tier is used only when v8 finds no function entry, and is flagged
`rename_invariant=False` because `class_driver.py` orders classes and methods
alphabetically.

## What v8 does *not* fix

* **Coverage.** On train/dev/val EQUIVALENT pairs v8 gives 12 DIFFERENT entries
  (v6: 45), all from SP-7 inline / SP-8 extract, which change the call graph
  legitimately; but it also produces 580 explicit failures, mostly class-based
  programs with no function-level entry. Fewer programs will be scored.
* SP-7/SP-8 can legitimately change the structural entry. A pair whose base and
  variant interfaces do not correspond (`interfaces_correspond`) must be
  excluded by a rule declared before scoring, not scored as one program.
* The v8 choices on the 13 observed test programs were inspected for sanity
  (one, `graph_bfs_shortest_path -> reconstruct_path`, looks questionable) but
  **must not be tuned** against them.
* A benchmark label defect (SP-2 dangling method references) is independent of
  entry selection; see `BENCHMARK_LABEL_DEFECT_SP2.md`.

## Historical protocols

`published`, `output_free_v6` and `output_free_v7` are untouched so committed
artifacts stay reproducible.

# Test-set chronology: what is, and is not, held out

**Conclusion: the v6 test split and the older 744-pair test split are *observed*.
Neither may be described as held-out. A fresh split is needed for any
confirmatory claim.**

Only commit timestamps exist (all +0530). Wall-clock execution times for the
2026-09-28 artifacts were not recorded, so ordering within that day cannot be
established. Where order cannot be proved, the split is treated as contaminated.

| Date | Commit | Event |
|---|---|---|
| 2026-08-21 | `4409652` | Old benchmark `pairs_test.jsonl`, and test-split result files for phases 3-5, committed together with the dev results. Test scores existed from the start of the project. |
| 2026-08-30 | `8ab2e4a`, `e870860`, `255499f` | Representation repair, external sprints; method and constants revised after test scores were visible. |
| 2026-09-28 | `9a9104f` | v6 benchmark, protocol corrections, and `MAIN_EVALUATION_test_published`, `..._test_output_free_v6`, `..._v6test_output_free_v6` committed in the **same** commit. |
| 2026-09-28 | `657281b` | Hard-coded all-categories-PASS gate committed (see `docs/archive/superseded_gate/`). |
| 2026-10-03 | `ad7b655`, `dc09fe4` | Gate replaced; handoff. Preregistration lists stages 2a-2f as pending; no v7 test run exists. |

Additional facts:

* The v6 `pairs_test.jsonl` contains the same 13 base programs as the old test
  split (SHA `ada35810...` is frozen in `freeze_handoff.json`).
* Per-pair scores for those 13 programs are committed and were analysed
  (`audit_recompute.py`), so any rule I or anyone derives from them is
  post hoc.
* `PHASE2_PREREGISTRATION.md` asserts that no Phase 2 result existed when it was
  written, but the v6 test result is in the repository at that date; the
  preregistration therefore does not protect the test split.
* Threshold tau* = 0.072905 was derived from dev only
  (`tests/test_threshold_provenance.py`). tau = 0.08 has no derivation record.

## Required for a confirmatory evaluation

A **fresh program-level split** (new programs, not new variants of the 13), with
dataset hash, protocol hash, threshold and analysis plan frozen and committed
before any scoring. See `EVALUATION_PLAN_V8.md`. If new programs cannot be
written, results on the existing 13 must be labelled exploratory.

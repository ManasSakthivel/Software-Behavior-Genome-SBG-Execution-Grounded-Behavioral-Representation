# Frozen V8 test suite: stall diagnosis (2026-11-20)

Snapshot: `frozen_v8_2edfe568/` (checksums verified: 23,692 files, 0 mismatched, 0 missing, 0 extra).
Interpreter: CPython 3.13.15, `venv313`. Command: `python -m pytest tests -v -p no:cacheprovider -o faulthandler_timeout=300`.

## Runs
- **Run 1** (`STALLED_RUN_1_pytest_frozen_2edfe568.log`): stopped by hand at 373 of 806 after ~35 min with no output. Not evidence of a result. Its `.exit` file (`exit=2`) is stale and was renamed `.exit.stale`.
- **Run 2** (`pytest_frozen_2edfe568_run2_verbose.log`): still running at the time of writing. Same test first stalled in run 1 and was the next test in run 2.

## Observed stall point
`tests/v7/test_cli_help_safe.py::test_help_exits_0_prints_usage_and_writes_nothing[args0-k1_spike]`.
- Run 2 went silent at ~18:34. The faulthandler watchdog fired at 300 s and dumped all threads.
- The dump shows 8 threads. Five have frames in `tests/test_tracer_isolation.py::_hangs_on_nine` (`while True: pass`, "abandoned on purpose") and in `sbg/extraction/dynamic/tracer.py` line 301, plus frames in `pytest-443/test_nonterminating_is_not_equ0/b.py`.
- The main thread was not in the CLI test body at the dump; the leftover busy threads from earlier tracer tests are still running.
- After the dump, run 2 resumed and was at 458 lines by 18:40.

## Isolation check
Run alone, the stalled test passes: `1 passed in 0.32s`.

## Interpretation
- The stall is a test-interaction effect, not a hang in the stalled test. Earlier `test_tracer_isolation.py` cases start CPU-bound threads that are never stopped (the tracer abandons workers on timeout by design). They persist in the same pytest process and compete for the GIL, so later tests slow down by minutes.
- This is a defect in the frozen test suite (abandoned busy threads), not evidence about SBG's detection results. It does not change any frozen implementation file.
- Not verified: the exact GIL-contention mechanism. The evidence is the dump plus the isolation run; nothing has been profiled.

## Status
- Exit code: pending. Not recorded as passing until the run's `.exit` file exists with a real code.
- Pycache: 22 `__pycache__` directories were created by earlier runs. Remove only after run 2 exits, then re-run `verify_freeze.py`.

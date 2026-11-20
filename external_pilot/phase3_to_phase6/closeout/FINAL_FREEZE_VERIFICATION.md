# Final freeze verification (SBG V8, commit 2edfe568)

Date: 2026-11-20. Status: **INCOMPLETE. The frozen test suite did not finish. It is not recorded as passing.**

## 1. Snapshot integrity
- Snapshot: `phase3/frozen_v8_2edfe568/`. `verify_freeze.py` (read-only): listed 23,692, mismatched 0, missing 0, extra 0. Exit 0.
- The snapshot's 22 `__pycache__` directories (from earlier runs) were removed after the test runs stopped. They are excluded from the checksums. Re-verified after removal.
- Source repository `~/Desktop/SBG-V8-LINUX`: HEAD `df612db0`; 61 pre-existing uncommitted entries, unchanged by this programme.

## 2. Frozen test suite
- Collected: 806 tests (`tests/`, CPython 3.13.15, `venv313`).
- **Run 2** (`phase3/STALLED_RUN_2_pytest_frozen_2edfe568_verbose.log`): 372 PASSED, 0 FAILED, 0 ERROR. The run stopped at the 373rd test, `tests/v7/test_cli_help_safe.py::test_help_exits_0_prints_usage_and_writes_nothing[args0-k1_spike]`, after a faulthandler dump at 300 s and no output for more than 7 minutes. Stopped by hand (SIGTERM, exit 143). That exit code is not a pytest result. It is renamed `RUN2_KILLED_BY_HAND_exit143_NOT_A_PYTEST_RESULT.txt`.
- **Run 1** (`phase3/STALLED_RUN_1_pytest_frozen_2edfe568.log`): stopped by hand at 373 of 806 after about 35 minutes with no output. Its earlier `exit=2` file is stale (collection failure from an earlier snapshot) and is not used.
- **Reproducible stall**: the same test stopped both runs. Run alone, it passes in 0.32 s.
- Cause as observed: earlier `tests/test_tracer_isolation.py` cases abandon busy-looping worker threads (`_hangs_on_nine`, `while True: pass`) that keep running in the pytest process. The dump at the stall lists these threads. Interpretation and limits: see `phase3/FREEZE_TEST_DIAGNOSIS.md`. The mechanism was not profiled.

## 3. Result
- Exit code of a complete frozen suite run: **none. The suite did not complete.**
- Passed/failed counts over the full 806: **not available.** 372 passed and 0 failed were observed before the stall; 433 tests were not run in run 2.
- The frozen test suite therefore **cannot** be reported as passing.

## 4. What would close this
One of these, decided by the user:
1. Accept the freeze with a documented limitation: suite incomplete, stall at the named test, 372 passes and 0 failures observed.
2. Authorise a diagnostic change to the test harness (for example, run `test_tracer_isolation.py` in its own process) and a complete rerun. Recorded as a deviation, not as the frozen result.

## 5. Sign-off
Not signed. Requires the user's explicit decision; see the sign-off request.

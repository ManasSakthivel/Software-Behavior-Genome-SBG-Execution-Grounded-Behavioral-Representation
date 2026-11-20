# Final freeze verification (Decision 4)

Date: 2026-11-20. Frozen implementation: commit `2edfe568`, `sbgv8/` tree `8728842f129fe5ba493b6592ab4fa2304333407a`, root tree `035bc3f5f53e0171d602711fcae4c03bd84ed44c`. Snapshot: `phase3/frozen_v8_2edfe568/`. No change was made to the snapshot, the freeze, the threshold, or the protocol.

**Freeze sign-off: NOT SIGNED.** A sign-off request is prepared in `FREEZE_SIGNOFF_REQUEST.md`. It requires the user's own decision.

## 1. File integrity (verified)

Command: `python3 -I verify_freeze.py` (in `phase3/`), run at 2026-11-20 18:14 IST.

Result: `listed=23692 mismatched=0 missing=0 extra=0`, exit 0. The snapshot is unchanged since it was taken. Every file matches its git blob hash in `2edfe568`.

## 2. Test suite on the frozen snapshot

| Run | Status | Result | Evidence |
|---|---|---|---|
| Run 1 (stalled) | Stopped by the user's instruction after 35 min at 100% CPU, at 373/806. Not a completed run. | No exit code. The log is preserved. | `STALLED_RUN_1_pytest_frozen_2edfe568.log`; `STALLED_RUN_1_pytest_frozen_2edfe568.exit.stale` (marked stale). |
| Run 2 (re-run with `faulthandler_timeout=300`, `-v`) | **Still running at the time of writing.** Last observed: 314 PASSED, 0 FAILED, 0 ERROR, 0 SKIPPED, at 38% of 806. | **Exit code: pending.** | `pytest_frozen_2edfe568_run2_verbose.log`. The exit file `pytest_frozen_2edfe568_run2.exit` had not been written at the time of writing. |

Observations on run 2:
- The log is being written continuously; the last write was seconds before the check, so it is not stalled in the run 1 sense.
- No `faulthandler` timeout dump (0 occurrences of `Timeout (0:05:00)` or thread dumps) as of the last check.
- Slow cases are the large-integer precision tests in `tests/v7/test_backlog_mb.py` (for example `10**5000`). Their slowness is consistent with arbitrary-precision string conversion, but this was not profiled.

**Exit code: to be recorded from `pytest_frozen_2edfe568_run2.exit` when written. Until then this record does not claim the suite passed.**

## 3. Reproducibility of the frozen run

- Dependency lock: declared (`SBG_V8_DEPENDENCY_LOCK.declared.txt`) and installed (`SBG_V8_DEPENDENCY_LOCK.installed.txt`) are both present. The lockfile is incomplete for numpy, scipy, pandas, matplotlib (see `SBG_V8_FROZEN_MANIFEST.md` §Known gaps).
- Python: CPython 3.13.15, `venv313/`, pytest 9.1.1.
- Platform: macOS 26.7 arm64. Linux/Docker isolation is not reproduced.
- Pycache: excluded from the checksum and from the freeze check.

## 4. Security re-execution on the frozen commit (related)

The macOS security audit (`audit_security_rerun.py`) was re-executed against the full `2edfe568` tree with exit 0 and identical outcomes. See `SECURITY_RECOVERY_REPORT.md`. This is a re-execution, not a substitute for the pytest run.

## 5. What this verification does not establish

- It does not establish that the test suite passes until run 2 writes its exit code.
- It does not establish Linux or Docker isolation.
- It does not establish that the frozen implementation is a valid measure of the SBG methodology; the held-out test evaluation is NOT DEMONSTRATED (see `FINAL_EVIDENCE_CLAIM_REGISTER.md`, C33).

## 6. Status summary

| Item | Status |
|---|---|
| Snapshot integrity | VERIFIED (23,692 files, 0 mismatches) |
| Test suite, run 2 exit code | PENDING |
| Stalled run 1 | Preserved; not a completed run |
| Sign-off | NOT SIGNED; request prepared |

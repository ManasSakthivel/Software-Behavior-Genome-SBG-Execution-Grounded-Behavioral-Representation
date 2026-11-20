# Freeze sign-off request (unsigned)

**Status: NOT SIGNED. Prepared for the user's decision. Nothing in this file has been signed on the user's behalf.**

## What is being frozen

- Commit `2edfe568` (2026-11-19 21:11 +0530), `sbgv8/` tree `8728842f129fe5ba493b6592ab4fa2304333407a`, root tree `035bc3f5f53e0171d602711fcae4c03bd84ed44c`.
- Threshold τ* = 0.072905 (`artifacts/final/THRESHOLD_FROZEN.json`). Not re-tuned.
- Observation boundary O = {outcome, exception, side_effect, api}, unchanged.
- Protocol: `SBG_V8_EVALUATION_PROTOCOL.md`, registered 2026-11-20 before any pilot execution. Cohort executed: 0.

## Evidence for the freeze

| Check | Result | Reference |
|---|---|---|
| Snapshot integrity | 23,692 of 23,692 files match; 0 mismatched, 0 missing, 0 extra | `FINAL_FREEZE_VERIFICATION.md` §1 |
| Test suite on snapshot | **Did not complete.** Run 2: 372 passed, 0 failed, then stalled at `test_cli_help_safe.py…[args0-k1_spike]` (reproducible; see `FINAL_FREEZE_VERIFICATION.md` §2). No exit code of a complete run exists. | `FINAL_FREEZE_VERIFICATION.md` §2 |
| Security re-execution at frozen commit | Identical outcomes to the recorded audit | `SECURITY_RECOVERY_REPORT.md` |
| Held-out test-split result | AUROC 0.694 vs 0.876 (reversed edit size); NOT DEMONSTRATED | `FINAL_EVIDENCE_CLAIM_REGISTER.md` C29–C34 |

## Known gaps the user must accept or resolve

1. **Test suite did not complete.** The stall is reproducible. Choose option 1 or 2 in `FINAL_FREEZE_VERIFICATION.md` §4 before any sign-off.
2. **Lockfile incomplete.** numpy, scipy, pandas and matplotlib are pinned only in the installed lock, not in the requirements.
3. **Linux/Docker isolation not reproduced.** Only macOS `sandbox-exec` was exercised.
4. **Held-out test split burned.** It cannot serve as a further confirmation.
5. **No external validation.** The pilot executed 0 cases (NO-GO). Human adjudication has 0 verdicts.
6. **Historical invalidity.** The five-dataset run `ca7c2b2a` is invalid for external-validation claims.

## Decision required

Choose one. The assistant has not selected any.

- [ ] **Sign off** the freeze at `2edfe568` as described, with gaps 1–6 disclosed. (Requires gap 1 to be recorded first, or an explicit decision to accept it open.)
- [ ] **Decision recorded by the user (2026-11-20):** the frozen record is accepted as incomplete (372/806 passed, 0 observed failures, 433 not run). No harness change or rerun. **The freeze is still not signed**; signing remains a separate act by the user.
- [ ] **Do not sign** the freeze.

Signature: ______________________ (the user)  Date: ____________

*This request is not a signature. The freeze remains unsigned until the user completes the block above in their own name.*

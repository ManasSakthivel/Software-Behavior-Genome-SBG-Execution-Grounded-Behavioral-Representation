# SBG V8 frozen implementation manifest

## Identity

| Item | Value |
|---|---|
| Source repository | `~/Desktop/SBG-V8-LINUX` (not modified; 61 uncommitted manuscript files left as they are) |
| Frozen commit | `2edfe56868b5243dada3bbc342544466599113f8` (short `2edfe568`), 2026-11-19 21:11 +0530, "fix(v8-security): remediate SENSE04 file sensing…" |
| Root tree | `035bc3f5f53e0171d602711fcae4c03bd84ed44c` |
| `sbgv8/` tree | `8728842f129fe5ba493b6592ab4fa2304333407a` (identical at `2edfe568` and at repository HEAD) |
| Snapshot | `frozen_v8_2edfe568/`, produced with `git archive` (no checkout in the source repository) |
| Files | 23,692, every one matching its git blob hash in `2edfe568` |
| Checksums | `SBG_V8_CHECKSUMS.sha256` (SHA-256, 23,692 lines) |
| Verification | `verify_freeze.py` (exit 0 = unchanged since freeze) |

## Why this commit

- `2edfe568` is the last commit to change `sbgv8/` (it changed `trust.py`, two lines). The prior five-dataset run (`ca7c2b2a`) predates it. Both are recorded; the delta is one trust-gate sanitisation change in `sbgv8/trust.py`.
- Any reported result from `ca7c2b2a` therefore corresponds to the pre-`2edfe568` implementation, not this freeze. Given the stub executor finding, this delta does not affect the prior results, which did not run the implementation.

## Frozen elements

| Element | Where |
|---|---|
| Implementation (collector, profile, ERS, calibration, decision) | `sbgv8/`, `sbgv7/`, `sbg/` |
| Threshold τ* = 0.072905 | `artifacts/final/THRESHOLD_FROZEN.json` |
| Observation boundary `O` | `research/v8_final_design/04_FORMAL_PROBLEM_DEFINITION.md` (documentation, unchanged) |
| Evaluation protocol and preregistration | `SBG_V8_EVALUATION_PROTOCOL.md` |
| Declared dependencies | `SBG_V8_DEPENDENCY_LOCK.declared.txt` (sha256 `c25aba80…883f`) |
| Installed dependencies | `SBG_V8_DEPENDENCY_LOCK.installed.txt` (sha256 `86185d78…0650a`) |

## Known gaps in the freeze

- **Lockfile incomplete.** `requirements-lock.txt` pins only the test runner. numpy, scipy, pandas and matplotlib (declared in `REPRODUCIBILITY.md` but unpinned) were installed at the versions in `SBG_V8_DEPENDENCY_LOCK.installed.txt`. A reproduction must use those exact versions.
- **Pycache.** The snapshot directory contained generated `__pycache__` files from earlier test runs. They are not source, are excluded from the checksum file, and are removed after the test run (see the freeze verification record).
- **Sign-off outstanding.** The project gate requires a freeze sign-off. This manifest is a prepared record, not a signed one.
- **Sandbox and platform.** The implementation's isolation uses `sandbox-exec`, which is macOS-specific. The Linux/Docker isolation named in the repository is not present in this freeze.
- **Defects found in V8.** None newly identified in this programme. The project's own status (`STATUS.md`) reports the frozen v8 test evaluation as NOT DEMONSTRATED (AUROC 0.694 against 0.876 for reversed edit size), and this freeze inherits that result.

## Changes made to the source repository during this programme

None. `git status` in `~/Desktop/SBG-V8-LINUX` was not altered by this programme: the 61 pre-existing uncommitted manuscript changes are unchanged, and no commits, checkouts or worktrees were made there.

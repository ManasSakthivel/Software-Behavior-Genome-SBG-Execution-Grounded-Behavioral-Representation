# Final submission readiness report

Date: 2026-11-20. Verdict: **NOT READY FOR SUBMISSION.** The manuscript was not submitted, and the freeze was not signed.

## 1. What is ready

- **Frozen implementation integrity:** 23,692 files match their git blob hashes at `2edfe568` (`FINAL_FREEZE_VERIFICATION.md` §1).
- **MacOS security counts 3 / 15 / 5 / 2 (of 25):** recovered from the raw audit file and reproduced by re-execution at the frozen commit (`SECURITY_RECOVERY_REPORT.md`).
- **+1.6 pp matched-coverage contrast:** recovered from the committed multi-seed raw results. Its per-seed values match the manuscript. The interval is corrected to the authentic percentile interval −6.4 to +16.3 (`INTERVAL_RECOVERY_REPORT.md`).
- **Held-out disclosure:** the manuscript now discloses the single test-split run and its NOT DEMONSTRATED verdict (`FINAL_MANUSCRIPT_CHANGELOG.md` §1).
- **Development records:** byte-identical on the two platform branches (verified, MD5).
- **External validation:** none executed. The pilot is NO-GO; the adapter pilot is closed without a negative SBG claim (`closeout/PILOT_ATTEMPT_CLOSURE.md`).

## 2. Blocking items (must be resolved before any submission)

| # | Item | Why it blocks | Required action |
|---|---|---|---|
| B1 | **LaTeX not built.** No TeX toolchain on this machine. The copy's PDF is stale. | The manuscript has not been compiled after the edits. | Compile `FINAL_MANUSCRIPT/main.tex` in a TeX environment; check for overfull boxes and unresolved references. |
| B2 | **Frozen test suite exit code not yet recorded.** Run 2 was still running at the time of writing (314 passed, 0 failed, at 38%). | The freeze verification is incomplete without it. | Record the exit code and counts from `pytest_frozen_2edfe568_run2.exit` when written. |
| B3 | **Unverified intervals** in `results.tex` (~lines 57, 76, 107) and the gate contrast "0.0 [−6.2, …]". | Presented as results without a source. | Trace each to `matched_coverage.csv` / `primary.csv`, or remove. |
| B4 | **Unverified counts in `results.tex`:** test suite 247 / 8 / 2; Linux regression 608; Linux probes 51 / 74 / 1 / 65; ERS matrix; real-execution analogue 720 trials (run directories absent). | Presented as results, not re-run. | Re-run, trace, or remove. |
| B5 | **B4 and B5 verdict counts** (141 / 144; 0.121 / 0.125). | Not re-executed. | Re-execute the baseline rules or remove. |
| B6 | **Frozen-threshold "held-out projects" study** (`design.tex:133`; claim C14). Commit `b9b8a86c` exists; results not opened. | Presented as a held-out result. | Open the results and trace them, or qualify as unverified. |
| B7 | **Figure `fig_evidence_landscape.pdf` not regenerated.** | Figures may not match the corrected text. | Regenerate, or confirm it has no numbers that changed. |
| B8 | **Held-out wording in the test-split disclosure** needs author sign-off. The NOT DEMONSTRATED verdict and the burned-split status are the authors' call to present. | Authorship decision. | Authors to review `results.tex` RQ5 and `design.tex:43`. |
| B9 | **Freeze sign-off outstanding.** | The project gate requires it (`research/v8_final_design/11_FINAL_RESEARCH_GATE.md`). | User to decide. A request is prepared in `FREEZE_SIGNOFF_REQUEST.md`; nothing is signed. |

## 3. Non-blocking limitations (must be disclosed, not fixed)

- The test split is burned. It cannot provide a second held-out confirmation.
- The benchmark is generated, single-language (Python), development-exposed and unadjudicated. No human verdicts exist (0 of 250 in the historical template; two reviewers not recruited).
- The five-dataset run (`ca7c2b2a`) is INVALID for external-validation claims. Its executor did not run programs and its labels were derived from test purposes. It is not cited as evidence.
- Isolation was tested only with macOS `sandbox-exec`. Linux/Docker isolation is not reproduced.
- The lockfile is incomplete (numpy, scipy, pandas, matplotlib are installed but not pinned).
- Security results are single-run, in-process, and cover the stated threat model only. P08 (key-holder forgery) and SENSE04b succeed.
- The positive predictive results are NOT DEMONSTRATED.

## 4. Claim status at a glance

| Status | Examples |
|---|---|
| Verified | Freeze integrity; development-record identity; security counts; per-seed matched-coverage values; test-split AUROC 0.694 and 0.876 |
| Exploratory, single run | Per-seed matched-coverage values; test-split stratified AUROC 0.776 |
| NOT DEMONSTRATED | Held-out test-split criterion; incremental value of richer evidence (RQ4) |
| Removed / unrecoverable | B1 interval; cross-platform $10^{-9}$ agreement |
| Corrected | Matched-coverage interval (−6.6 → −6.4); "no held-out evaluation" statements |
| Open | B3–B6 above |
| Invalid (historical) | `ca7c2b2a` five-dataset run; "sealed", Podman "Linux" claims |
| Unexecuted | External pilot (15 cases), human adjudication (0 verdicts), full evaluation |

## 5. Recommendation

Do not submit. The manuscript's core methodological contribution and its honest negative result are supported. The remaining work is verification of the open items, compilation, and an authorship decision on the held-out disclosure. The user decides on the freeze sign-off.

## 6. Housekeeping findings in this pass

- `FINAL_MANUSCRIPT_CHANGELOG.md` already existed at the closeout path and was overwritten by this pass's version. The earlier content was not read first and is not recoverable from this session.
- The earlier working-summary note that `audit/security_rerun_darwin.json` was absent was wrong. The file is tracked in `df612db0`.
- The earlier working-summary note that `scripts/stats_recompute.py` and `audit/stats_summary.json` were absent is confirmed: both are absent from all git history.
- Several source files in `~/Desktop/SBG-V8-LINUX` changed on disk during this pass (notices received on `INTERVAL_RECOVERY_REPORT.md` and `SECURITY_RECOVERY_REPORT.md`). Those files in the closeout directory were read in their current state, not reverted.

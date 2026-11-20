# Final evidence claim register

Date: 2026-11-20. Supersedes `CLAIM_EVIDENCE_MATRIX.csv` (28 rows, earlier pass) for the final manuscript. Rows C01–C28 keep their earlier IDs; new rows are C29 onward. Categories used:

- **VERIFIED**: recomputed from an authentic raw file in this pass, or matched to one.
- **VERIFIED (recorded)**: matches the stored value; the file exists, but the value was not independently recomputed.
- **EXPLORATORY, SINGLE RUN**: produced by one run; reported descriptively.
- **NOT DEMONSTRATED**: the pre-declared criterion was not met.
- **REMOVED / UNRECOVERABLE**: the claim was removed from the manuscript because no authentic source exists.
- **OPEN**: a source exists but the value is not yet traced.
- **INVALID (historical)**: rests on a run that did not execute the programs.
- **UNEXECUTED**: proposed only.

## A. Changes in this pass

| ID | Claim (manuscript location) | Before | Now | Source | Category |
|---|---|---|---|---|---|
| C03 | B1 risk interval [0.086, 0.354] (`results.tex:56`) | Sources absent | **Removed.** Interval not recovered; point 0.169 retained (see C02). | `INTERVAL_RECOVERY_REPORT.md` §3 | REMOVED / UNRECOVERABLE |
| C06 | Matched-coverage +1.6 pp, interval [−6.6, +16.3] (abstract, intro, conclusion, results, discussion) | Sources absent | **Recovered, corrected to [−6.4, +16.3]** (percentile, seed 0). Per-seed values reproduce exactly. | `f632ad94` `results/v8_dev_eval_20261119_055209_linux_soft/seed{0..4}/tables/primary.csv` | VERIFIED; EXPLORATORY, SINGLE RUN per seed; sign unstable across seeds |
| C20 | macOS security counts 25 attacks/probes: 3 blocked, 15 detected, 5 no effect, 2 succeeded (`results.tex:10`) | File absent | **Recovered and reproduced** by re-execution on macOS at frozen commit. Identical outcomes. | `audit/security_rerun_darwin.json` (`df612db0`); `closeout/recovered_security/` | VERIFIED (re-executed, single run per host) |
| C13 | "No held-out benchmark was evaluated" (`design.tex:43`, `results.tex:166`, `threats.tex:20`) | Contradicted | **Corrected.** A single held-out test-split run is disclosed. | `artifacts/paper_evidence/V8_TEST_EVALUATION.json` | CONTRADICTED → corrected |

## B. Held-out test-split evaluation (new rows)

| ID | Claim (now in manuscript) | Recomputed or recorded | Source | Category |
|---|---|---|---|---|
| C29 | Single frozen run on the v8 test split: 22 programs, 967 dataset pairs, 956 valid (547 changed, 409 equivalent) | Recorded counts; C07 (earlier pass) recounted labels from scored pairs | `V8_TEST_EVALUATION.json`; `artifacts/final/pairs_v8test_output_free_v8.jsonl` | VERIFIED (recorded + earlier recount) |
| C30 | SBG AUROC 0.694 [0.659, 0.727] (artifact predictor name `sbg_v5`) | 0.693742 recomputed (C08); CI approximately reproduced (C09) | `V8_TEST_EVALUATION.json` | VERIFIED |
| C31 | Reversed edit-size baseline AUROC 0.876 [0.859, 0.892] | 0.875922 recomputed (C10); CI recorded only (C11) | same | VERIFIED (point); CI VERIFIED (recorded) |
| C32 | Paired difference SBG − best baseline −0.182 [−0.220, −0.144]; Holm p = 0.006 | Point delta consistent (C12); CI recorded only | same | VERIFIED (recorded) |
| C33 | Pre-declared success criterion not met → **NOT DEMONSTRATED** | Criterion field: `sbg_beats_best_baseline_with_ci_lb_gt_0 = false` | same | NOT DEMONSTRATED |
| C34 | Label-shuffle noise floor p95 0.528; stratified AUROC 0.776 (edit size controlled) | Recorded | same | EXPLORATORY, SINGLE RUN |

**Status note for C29–C34:** the artifact status reads "CONFIRMATORY-BY-FREEZE (single run)". `FINAL_METRICS_V4.json` labels this split `v8_test_burned`, so the test split has now been used for evaluation and cannot serve again as a held-out confirmation. The manuscript does not call this confirmatory external validation.

## C. Earlier rows, updated

| ID | Claim | Status now | Category |
|---|---|---|---|
| C01 | 312 development records, 258 labelled | Unchanged (MATCH, recount) | VERIFIED |
| C02 | B1 false-assurance risk 31/183 = 0.169 | Unchanged (MATCH). The 31/183 count is from the earlier recount. | VERIFIED |
| C04 | V7-B gate: 61 verdicts, 13 wrong, risk 0.213 | Unchanged (MATCH) | VERIFIED |
| C05 | B4 141 verdicts at 0.121; B5 144 at 0.125 | Not re-executed | OPEN |
| C07–C12 | Test-split values | See section B | VERIFIED / NOT DEMONSTRATED |
| C14 | Frozen-threshold held-out projects, p 0.24–0.50 | Commit exists; results not opened. Also cited in `design.tex:133`. | OPEN |
| C15 | Five-dataset artifact, 250 pairs, "sealed", Podman "Linux" runtime | Executor did not run programs; label-derived records; stub predictor | INVALID (historical) |
| C16 | Blinded adjudication template, 250 rows, 0 verdicts | Unchanged | UNEXECUTED |
| C17 | Two-adjudicator protocol | No verdicts exist | UNEXECUTED |
| C18 | ERS posthoc matrix, 312 × 6 | File present; values not recomputed | OPEN |
| C19 | Real-execution analogue, 30 pairs, 720 trials | Run directories absent | OPEN |
| C21 | Linux probes 51 / 74; 1 succeeds, 65 INS | Pre-fix run; not recomputed | OPEN |
| C22 | Test suite 247 passed, 8 skipped, 2 xfail (macOS) | Not re-run in this pass. See `FINAL_FREEZE_VERIFICATION.md` for the separate frozen-snapshot run. | OPEN |
| C23 | 608-test Linux regression run | Report text only | OPEN |
| C24 | Development records byte-identical on Linux and macOS branches | MD5 `07e57a80…` on both | VERIFIED |
| C25 | Statistics reproduce across platforms to 1e-9 | Depended on `stats_recompute.py`, which is absent | REMOVED / UNRECOVERABLE (claim to be removed or re-stated; see Submission Readiness) |
| C26 | Placebo, frozen-threshold, profile-fix results (mac branch) | Commits exist; results not opened | OPEN |
| C27 | Construction labels from transformation templates | Label-source counts not tabulated | OPEN |
| C28 | No external validation performed | External pilot 0 executed; NO-GO | VERIFIED (consistent) |

## D. Intervals still open in the manuscript (not changed in this pass)

Listed for completeness; these are not verified. Source: `INTERVAL_RECOVERY_REPORT.md` §4.

- `results.tex:57`: B3 risk 0.213 [0.090, 0.457]
- `results.tex:76`: B8 risk 0.213 [0.124, 0.392]; B7 0.230; B9 0.292; multiplicity 0.295
- `results.tex:76`, `:107`: B9 − B8 +7.9 [−2.8, +14.7]; gate contrast "0.0 [−6.2, …]"

## E. Summary

The category in each row is authoritative. Rows with a status of OPEN are not verified and must not be presented as results. Several OPEN rows still appear unchanged in the manuscript copy: C05, C14, C18, C19, C21, C22, C23, C26 and C27, plus the intervals in section D. None of them is verified. They are listed in `FINAL_SUBMISSION_READINESS_REPORT.md` as blocking items: each must be verified or removed before any submission.

## F. Corrections to this register (later pass, 2026-11-20)

This register was written before three findings. The rows below are superseded; the earlier text is kept above unedited.

| ID | Earlier entry | Correct status | Basis |
|---|---|---|---|
| C03 | B1 interval removed as unrecoverable | **VERIFIED.** Interval [0.0856, 0.3535] reproduces; manuscript [0.086, 0.354] retained. | `STATS_RECOVERY_REPORT.md`; `stats_summary.json` at HEAD (`paper/IEEE_ACCESS_V8_FINAL/audit/`) |
| C06 | +1.6 pp interval [−6.4, +16.3], seed-0 percentile | **VERIFIED.** Contrast B7−B8 = 0.01639, interval [−0.0658, +0.1625] → manuscript [−6.6, +16.3] retained. The [−6.4] value is from an older run and is not used. | Clean-export rerun with `--refit --B 10000`; `STATS_RECOVERY_REPORT.md` |
| C20 | Security file absent; counts recovered by re-execution | **VERIFIED.** File is tracked (first added in `df612db0`). Counts 3/15/5/2 of 25 reproduce from the file and from a re-execution. | `SECURITY_RECOVERY_REPORT.md` |
| C25 | Cross-platform statistics to 1e-9 depends on absent script | **OPEN.** The script is present, but the 1e-9 cross-platform claim has not been re-run in this pass. The sentence should be restated as "reproducible on the same records" or removed. | Script present (see C03) |
| §D | Intervals still open | **Resolved** for B1, B7−B8 and B8 (B8 [0.124, 0.392] also reproduces). B3, B9 and the gate contrast remain **OPEN** and are not presented as verified. | `STATS_RECOVERY_REPORT.md` |

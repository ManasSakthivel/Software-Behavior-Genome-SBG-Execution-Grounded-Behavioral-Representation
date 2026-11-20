# SBG V8: manuscript submission readiness

Date: 2026-11-20. Authoritative manuscript: `closeout/manuscript_final/`. The SBG repository (HEAD `df612db0`) was not modified.

**Final verdict: NOT READY FOR SUBMISSION.** Not submitted. The freeze is not signed. The frozen test suite is recorded as incomplete. Blockers are in section 8.

Evidence files: `FINAL_EVIDENCE_MANIFEST.json` (28 claims), `FINAL_EVIDENCE_CLAIM_REGISTER.md`, `FINAL_MANUSCRIPT_CHANGELOG.md`, `CORRECTION_REGISTER.md`, `STATS_RECOVERY_REPORT.md`, `SECURITY_RECOVERY_REPORT.md`, `FINAL_FREEZE_VERIFICATION.md`, `PILOT_ATTEMPT_CLOSURE.md`, `FREEZE_TEST_DIAGNOSIS.md` (in `phase3/`).

## 1. Verified scientific contributions
- **Reformulation of no-divergence verdicts** as selective prediction with a false-assurance risk relative to an observation boundary. A method contribution, not an empirical result.
- **Observed false-assurance risk of plain differential testing (B1): 0.169**, 31 of 183 verdicts on 258 labelled development pairs. Interval [0.086, 0.354] reproduces from the tracked script and summary.
- **Integrity gate:** V7-B issued 61 verdicts, 13 wrong (risk 0.213). Recounted.
- **Evidence Response Signature exposed a profile defect** that aggregate metrics did not show. The defect was observed in an exploratory real-execution matrix whose run directories are absent.
- **Development records are byte-identical** on the Linux and macOS branches (same MD5).

Not claimed: predictive value of the richer evidence profile, ERS as a predictor, external validity.

## 2. Legitimate completed experiments
| Experiment | Environment | Status |
|---|---|---|
| Development corpus: 312 pairs, 258 labelled (synthetic, QuixBugs, BugsInPy) | Records on both branches | VERIFIED |
| B1 risk 0.169, interval [0.086, 0.354] | Development records | VERIFIED (regenerated) |
| B7−B8 +1.6 pp, [−6.6, +16.3]; B8 0.213 [0.124, 0.392] | Development records, soft policy | VERIFIED (regenerated) |
| B4 141 verdicts 0.121; B5 144 verdicts 0.125 | Development records | VERIFIED (stored value) |
| Frozen test split: 956 pairs, 22 programs; SBG V5 AUROC 0.694 [0.659, 0.727]; reversed edit size 0.876 [0.859, 0.892]; paired delta −0.182 | Single run, frozen script | VERIFIED (stored value); NOT DEMONSTRATED |
| macOS security counts: 3 blocked, 15 detected, 5 no effect, 2 succeeded of 25 | macOS, sandbox-exec, CPython 3.13.15 | VERIFIED (file and re-execution) |
| Frozen snapshot `2edfe568` | macOS declared | VERIFIED (23,692 files) |

## 3. Invalid or excluded evidence and reasons
- **Five-dataset run, commit `ca7c2b2a` (250 pairs).** Outcomes set from test labels; stub predictor; benchmark programs not executed; zero human verdicts. **Invalid as external-validation evidence.** Excluded from all results. Corrected in the manuscript.
- **Three Podman reports**: marked SUPERSEDED. Their description of a Linux Podman runtime is not supported.
- **Stale pytest exit (`exit=2`)** and **the SIGTERM exit (143)** from the stopped run: not results.
- **Stalled frozen runs 1 and 2**: incomplete; not results.
- **Unverified items removed or qualified** (section 7).
- **Superseded reports**: `INTERVAL_RECOVERY_REPORT.md` (wrong about file absence); agent drafts `FINAL_MANUSCRIPT/`, `FINAL_FREEZE_VERIFICATION_AGENT_DRAFT_SUPERSEDED.md`, `FINAL_SUBMISSION_READINESS_REPORT_AGENT_DRAFT_SUPERSEDED.md` (unsupported changes; not evidence).

## 4. Linux/macOS evidence reconciliation
Each platform was checked independently. Neither was discarded because of the 250-pair run.
- **Development records:** identical on both branches. VERIFIED.
- **Statistics across platforms (10⁻⁹):** reported by the project; **not re-run**. Qualified in the manuscript.
- **Security counts:** macOS only. Linux security run (51 tamper, 74 isolation probes) is pre-fix, lacks host metadata, and is reported as such (NOT RECOMPUTED, PRE-FIX).
- **Linux 608-test regression run:** report text only; not used.
- **Linux/Docker isolation:** not reproduced; not claimed.
- **macOS test suite** (247 passed, 8 skipped, 2 xfail): report text; not re-run.

## 5. Frozen V8 verification status
- **Snapshot:** VERIFIED. 23,692 files, 0 mismatched, 0 missing, 0 extra. Pycache removed; re-verified.
- **Test suite: INCOMPLETE.** Run 2 observed 372 passed, 0 failed, of 806. It stalled at `test_cli_help_safe.py…[args0-k1_spike]`, reproducibly (also run 1). The test passes alone in 0.32 s. The stall is consistent with busy threads left by `test_tracer_isolation.py`; not profiled. No exit code of a complete run exists. Accepted as incomplete by the user.
- **Threshold:** two frozen values are preserved and not resolved: τ* = 0.072905 (freeze manifest) and τ = 0.040511 (test record). Neither is a validated operating point. Threshold-dependent results are marked in the manuscript (Decision Thresholds subsection).
- **Sign-off:** not given.

## 6. External-validation limitations
- **No external pilot was executed.** The 15 shortlisted cases are scientifically eligible with qualifications but cannot be executed using the current Adapter v1 interface. This is not a negative SBG result.
- **Preflight:** 0 of 15 compatible with Adapter v1; 15 of 15 have at least one blocker; 14 of 15 have two or more; 6 are exception-only. Integrity audit complete.
- **Held-out data:** one single-run test split, generator-produced, in the same design family as development data. Four programs excluded in advance. Not independent; now used up. NOT DEMONSTRATED. Accepted disclosure.
- **Human adjudication:** zero verdicts; reviewers not recruited.
- **Data:** development data only; single language (Python); unadjudicated.

## 7. Manuscript corrections completed
All edits are in `closeout/manuscript_final/`.
- **Held-out disclosure** in abstract, introduction, design, results, threats and conclusion (single-run test split; NOT DEMONSTRATED).
- **Intervals** kept where reproduced; "sign unstable" removed.
- **Security citation** corrected to `df612db0`.
- **Cross-platform 10⁻⁹** removed from the conclusion; marked "reported; not re-run" in results and reproducibility.
- **Real-execution corroboration** reworded in abstract, introduction, conclusion, results as an exploratory matrix whose run directories are absent.
- **Reproducibility overclaim** narrowed to the regenerated statistics.
- **References:** six unverifiable entries removed with their dependent sentences and table rows. Bibliography now 70 entries, all cited.
- **Thresholds and data availability:** two subsections added to `reproducibility.tex`.
- **Figure** `fig_evidence_landscape.pdf` regenerated from the working-tree script and dev data; panel (c) is the excluded artifact, labelled as such.
- **250-pair run** corrected earlier (`CORRECTION_REGISTER.md`).

## 8. Remaining submission blockers
1. **Frozen test suite incomplete.** Accepted by the user as a documented limitation. Remains a limitation in the paper.
2. **Threshold discrepancy unresolved** (τ 0.040511 vs τ* 0.072905). Preserved by user decision; the authors must report it.
3. **LaTeX compilation not performed.** No TeX toolchain. `main.pdf` is stale. Compile on a machine with TeX before submission.
4. **Figure not visually inspected** after regeneration.
5. **Public access status** of the repository and branches is a placeholder: `[to be confirmed by the authors before submission]`.
6. **QuixBugs reference (`lin2017quixbugs`)** has no verification row; kept because the experiments use it. Verify before submission.
7. **Unverified claims still in the text**: the placebo and frozen-threshold study (mac branch; OPEN, QUALIFIED); the ERS posthoc matrix (present, not recomputed); the construction-label counts (not tabulated).
8. **Authorship review** of the held-out wording. Accepted by the user; the authors should still read it.
9. **Figure and table regeneration** beyond the evidence landscape not done.
10. **Final evidence manifest** is a JSON file; the authors should confirm the statuses before release.

## 9. Recommended publication positioning
A methodology paper with a bounded pilot empirical study, reporting negative and qualified results. Claims it can support:
- The reformulation of no-divergence verdicts as a risk with an explicit boundary and adjudication budget.
- Integrity-gate and evidence-profile observations on development data.
- The observed false-assurance rate of 0.169 (31 of 183), with reproduced intervals.
- The held-out test-split result as NOT DEMONSTRATED.

Claims it must not make: external validation, detection ability on real code, generalisation, predictive value of the richer evidence profile, cross-platform 10⁻⁹ agreement, a completed frozen test suite, or a resolved experimental threshold.

## 10. Final submission readiness verdict
**NOT READY.** The manuscript is corrected and states its evidence and limits honestly. Blockers remaining: the LaTeX build has not been run, the public-access status and the QuixBugs register row need the authors, the threshold discrepancy must be reported, and the frozen suite is incomplete. Nothing has been submitted or signed.

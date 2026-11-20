# SUPERSEDED (2026-11-20)

This report is superseded by `SBG_V8_MANUSCRIPT_SUBMISSION_READINESS.md`, which reflects the final pass (references, claims, thresholds, data availability, figure, manifest). Kept unedited below for the record.

---

# Final submission readiness report (SBG V8)

Date: 2026-11-20. **Verdict: NOT READY FOR SUBMISSION.** Not submitted. Freeze not signed.

## 1. Verified in this pass
- **Held-out wording corrected.** The manuscript now discloses one single-run test-split evaluation: 956 pairs, 22 programs; SBG AUROC 0.694 against reversed edit size 0.876; pre-declared verdict NOT DEMONSTRATED. It is not called confirmatory. No independent held-out evaluation exists. Source: `V8_TEST_EVALUATION.json`.
- **Intervals reproduce** from the tracked script and summary at HEAD (`STATS_RECOVERY_REPORT.md`): B1 [0.086, 0.354]; B7−B8 +1.6 pp, [−6.6, +16.3]; B8 [0.124, 0.392]. Kept.
- **macOS security counts reproduce** (3 blocked, 15 detected, 5 no effect, 2 succeeded, of 25) from the tracked file and from a re-execution. The file was first committed in `df612db0`.
- **Frozen snapshot integrity:** 23,692 files, 0 mismatched, 0 missing, 0 extra.
- **Five-dataset run (ca7c2b2a)** is invalid as external-validation evidence: outcomes set from test labels, stub predictor, no benchmark program executed, zero human verdicts.
- **External pilot:** 0 of 15 cases executed. Adapter v1 cannot execute them. This is not a negative SBG result.
- **Source repository unchanged:** HEAD `df612db0`; the same 61 pre-existing entries as at the start.

## 2. Blocking items
| # | Item | Status | Needed |
|---|---|---|---|
| B1 | Frozen test suite did not complete | Stalls reproducibly at `test_cli_help_safe.py…[args0-k1_spike]` after abandoned busy threads from `test_tracer_isolation.py`. 372 passed, 0 failed observed. | Decision per `FINAL_FREEZE_VERIFICATION.md` §4 |
| B2 | Threshold mismatch | Test record uses τ = 0.040511 (`THRESHOLD_V8_FROZEN.json`); freeze manifest names τ* = 0.072905 (`THRESHOLD_FROZEN.json`). Unresolved. | Authors to reconcile in the repository |
| B3 | LaTeX build not run | No TeX toolchain installed. `main.pdf` is renamed `main.STALE_pre_edit.pdf`. | Build on a machine with TeX |
| B4 | Figure not regenerated | `fig_evidence_landscape.pdf` caption corrected; image may still say "template-generated". | Regenerate from corrected source |
| B5 | Reproducibility rows unverified | `reproducibility.tex` lines 18, 25, 27 cite `07ecd5b7` for code commits without checking. | Verify commit per row |
| B6 | Unrun or unverified results | B4/B5 verdict counts (141/144; 0.121/0.125); frozen-threshold study (p 0.24–0.50); ERS posthoc matrix; real-execution analogue (30 pairs); Linux probe counts; 608-test Linux run. | Re-run or remove |
| B7 | Authorship decision on the held-out wording | The NOT DEMONSTRATED verdict and the burned-split status are for the authors to present. | Authors to review `sections/results.tex` (Single-run test-split paragraph) |

## 3. Qualified or removed in this pass
- "Reproduced across macOS and Linux to 10⁻⁹": removed from the conclusion. In the results it is marked "reported; not re-run in this review pass". Not verified here.
- "Sign unstable" next to the +1.6 pp interval: removed. Source not verified.
- Security row commit citation: corrected to `df612db0`, with `07ecd5b7` as the re-run commit.

## 4. Not evidence (do not cite)
- `closeout/FINAL_MANUSCRIPT/` (agent copy): its −6.4 interval and B1 removal are not supported. Not adopted.
- `FINAL_FREEZE_VERIFICATION_AGENT_DRAFT_SUPERSEDED.md`, `FINAL_SUBMISSION_READINESS_REPORT_AGENT_DRAFT_SUPERSEDED.md`: superseded drafts, kept for the record.
- `phase3/RUN2_KILLED_BY_HAND_exit143_NOT_A_PYTEST_RESULT.txt`: a SIGTERM code, not a test result.
- `phase3/pytest_frozen_2edfe568.exit` (stale `exit=2`): from an earlier collection failure.

## 5. Recommended positioning
A methodology and pilot paper. Claims: the change-conditioned decision framing; the integrity-gate result; the observed false-assurance rate on development data (0.169, 31 of 183), with intervals reproduced; the held-out test-split result as NOT DEMONSTRATED. Do not claim external validation, detection ability, or generalisation.

## 6. Outstanding decisions for the user
1. Freeze: accept with a documented limitation, or authorise a diagnostic harness change and rerun (`FINAL_FREEZE_VERIFICATION.md` §4). No signature has been given.
2. Threshold: which τ is the frozen one.
3. Whether the held-out wording is acceptable to the authors.
4. Whether to apply the manuscript corrections to the SBG repository. They are only in `closeout/manuscript_final/`.

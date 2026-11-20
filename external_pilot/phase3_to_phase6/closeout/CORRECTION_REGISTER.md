# Correction register: claims that depend on the historical 250-pair run (commit `ca7c2b2a`)

Date: 2026-11-20. Scope: the manuscript copy and three superseded reports. The SBG repository (`~/Desktop/SBG-V8-LINUX`) was not edited. Historical artefacts are preserved at commit `ca7c2b2a` and in `reports_original/` and `manuscript_original/` here.

Files:
- `manuscript_original/`: working-tree manuscript (`paper/IEEE_ACCESS_V8_FINAL/`) as copied, 145 files.
- `manuscript_corrected/`: the copy with corrections applied.
- `reports_original/`, `reports_corrected/`: the three Podman reports, extracted from `ca7c2b2a`, with a superseded notice added to the corrected copy.
- `manuscript_corrections.diff`: `diff -ru` original against corrected, 15 hunks in 11 files.

## Facts the corrections rest on (verified this session at `ca7c2b2a`)

| Fact | Evidence |
|---|---|
| Outcome set from the test's `purpose` label, not from running a program | `sbgv8/independent_validation/executor.py:35–43` (`CONFIRMED_DIFF` if `bug_fix` and `trigger_discriminating`, else `SAME`) |
| Evidence fields hard-coded | `executor.py:52–59` (`deterministic=True`, `n_repeat_runs=3`, fixed `hits`, `branches`) |
| Environment and integrity hard-coded | `executor.py:80–82` (`env_id="linux_podman_cgroups_v2"`, `integrity_ok=True`) |
| Predictor is the activation stub | `executor.py:109, 168` (`ActivationStubPredictor()`); `sbgv8/ers.py:88–89` docstring "For tests and CLI smoke only" |
| No subprocess or sandbox call in the executor | grep of `executor.py` for `subprocess`, `sandbox` returns nothing |
| Zero human verdicts | `results/v8/independent-validation/blinded_adjudication_template.csv`: 250 rows, 0 filled `adjudicator_verdict` |

Not re-verified in this session, carried from the audit as read and accurate: 12 templates, SHA-1 literal digests, 0 of 180 Java records compiled or run, six duplicates, 200/50 split.

## A. Manuscript corrections

| # | File and lines | Original text (excerpt) | Corrected text (excerpt) | Reason |
|---|---|---|---|---|
| A1 | `sections/results.tex:151` (bullet) | "the activation-stub predictor was used;" | "the predictor was the activation stub, a component documented as for tests and smoke tests only, not the calibrated model;" plus new bullet "no benchmark program was executed by this path, and no human adjudication verdict exists for any of the 250 records (0 of 250);" | Stub predictor and zero verdicts were not disclosed; no program was executed |
| A2 | `sections/results.tex:154` | "establishes only that the record schema, profile, \ers{} harness and prediction lock process 250 records end to end." | "establishes only that the record schema and harness run on label-derived records. It is invalid as external-validation evidence: its outcomes are set from labels, its predictions come from the stub, and no program under test was run." | "end to end" implied the predictor and the lock ran real checks; they did not |
| A3 | `sections/design.tex:40` (item F) | "It is a pipeline smoke test and supports no claim." | "Its outcomes were set from labels, its predictor was the activation stub, and it has zero completed human verdicts. It is invalid as external-validation evidence and is a pipeline smoke test that supports no claim." | Adds the reason for exclusion and the verdict count |
| A4 | `sections/design.tex:65` (table row F) | "Template-generated; excluded" | "Invalid as external-validation evidence (stub predictor; 0 human verdicts)" | Exclusion alone does not say why |
| A5 | `sections/design.tex:103` (Fig. caption, panel c) | "it is excluded as evidence and no metric is derived from it." | "it is invalid as external-validation evidence (outcomes set from labels, stub predictor, no benchmark executed, zero human verdicts), and no metric is derived from it." | Caption must match the corrected reason |
| A6 | `sections/introduction.tex:46` | "turned out to be template-generated with label-derived outcomes, so this paper excludes it as evidence." | "turned out to be template-generated, with outcomes set from labels, a stub predictor, no executed benchmark program and zero human verdicts. It is invalid as external-validation evidence, and this paper excludes it." | Was incomplete; the predictor point was missing |
| A7 | `sections/conclusion.tex:12` | "The project's five-dataset artifact was template-generated and is excluded." | "The project's five-dataset artifact is invalid as external-validation evidence: its records were template-generated, its outcomes were set from labels, its predictor was a stub, no benchmark program was executed, and no human adjudication verdict exists." | "Excluded" did not say why |
| A8 | `sections/reproducibility.tex:53` | "It is excluded entirely." | "It is classified invalid as external-validation evidence (label-derived outcomes, stub predictor, no executed benchmark, zero human verdicts) and is excluded entirely." | Reason stated in one clause |
| A9 | `sections/threats.tex:20` (External row) | "five-dataset artifact excluded" | "five-dataset artifact invalid as external evidence (label-derived outcomes; stub predictor)" | Threat table should carry the same classification |
| A10 | `CLAIM_EVIDENCE_REGISTER.md:100` (row V1) | Status "Verified"; limitation "—" | Status "Verified (description)"; limitation "Invalid as external-validation evidence: stub predictor, no benchmark program executed, 0 of 250 human verdicts" | The register described the artifact but did not state its evidential status |
| A11 | `CLAIM_EVIDENCE_REGISTER.md:118` | "Label-derived; no benchmark executed" | "Label-derived; predictor was the activation stub; no benchmark executed; 0 of 250 human verdicts; not an execution or external-validation claim" | Adds the stub and the zero-verdict count |
| A12 | `FINAL_CLAIM_EVIDENCE_REGISTER.md:100` and `:118` | Same as A10, A11 | Same as A10, A11 | Second register copy with identical rows (checked by `cmp`) |

## B. Repository reports marked superseded (on copies only)

Each of the three reports now starts with a notice: the run at `ca7c2b2a` executed no program; outcomes came from labels; the predictor was the stub; integrity and environment were hard-coded; 0 of 250 human verdicts; do not cite as evidence. The body of each report is unchanged below the notice.

| # | Report | Original claim (excerpt, from audit) | Action |
|---|---|---|---|
| B1 | `SBG_V8_FIVE_DATASET_EXECUTION_REPORT.md` | "Linux Podman Runtime"; "Total Pairs Executed: 250" | Superseded notice added; original kept |
| B2 | `FIVE_DATASET_FINAL_EXECUTION_SUMMARY.md` | "executed against five independent, real-world…"; "SEALED & HASHED" | Superseded notice added; original kept. The seal shows the file did not change, not that SBG produced it |
| B3 | `FIVE_DATASET_PRELIMINARY_STATISTICAL_REPORT.md` | "serves as the initial external validation cohort" | Superseded notice added; original kept |

## C. Located by search, not edited (open items)

| # | Location | Status | Reason not edited |
|---|---|---|---|
| C1 | `figures/fig_evidence_landscape.pdf` (panel c) | The caption was corrected (A5). The figure image was not regenerated and may still carry the label "template-generated" | The PDF is a binary output. Regenerate from `scripts/make_figures.py` or relabel in the source. Not done this session |
| C2 | `audit/DATASET_VERIFICATION_REPORT.md`, `audit/five_dataset_summary.json`, `audit/STATISTICAL_AUDIT_REPORT.md`, `audit/stats_summary.json`, `audit/SIMULATED_PEER_REVIEW.md`, `audit/ARCHITECTURE_AND_DEFINITIONS.md` | Located (about 34 hits), not read | Any statistic from the 250 records must be marked label-derived. Needs individual reading |
| C3 | `external_validation_audit/*` (FIVE_DATASET_EXTERNAL_VALIDATION_AUDIT.md, DEVELOPMENT_EXTERNAL_OVERLAP_REPORT.md, EXTERNAL_HOLDOUT_STATUS_REPORT.md, INDEPENDENT_ADJUDICATION_PROTOCOL.md, ADJUDICATION_REGISTRY.json, PROJECT_AND_CASE_PROVENANCE_REGISTRY.json) | Located, not read | Check that no registry lists the 250 records as adjudicated or sealed externally |
| C4 | `final_transformation/EXTERNAL_VALIDATION_CLAIM_DECISION.md`, `COMPLETE_EXTERNAL_VALIDATION_AUDIT.md`, `EXTERNAL_CASE_EVIDENCE_REGISTRY.json`, `FINAL_V8_RESEARCH_TRANSFORMATION_PLAN.md` | Grep shows the five-dataset run described as "labelled pipeline demonstration", "generated stand-ins", "not external validation". This is already consistent | No change needed. Not read in full |
| C5 | `scripts/verify_five_dataset.py`, `stats_recompute.py`, `make_figures.py` | Located (18 hits) | Code, not manuscript text. Should be labelled historical. Not edited |
| C6 | `reports/v8/independent-validation/BLINDED_ADJUDICATION_EXPORT_GUIDE.md`, `CHANGE_PAIR_REPRODUCIBILITY_REPORT.md`, `SBG_V8_FIVE_DATASET_ERS_REPORT.md`, `SBG_V8_EXECUTION_FAILURES_AND_EXCLUSIONS.md`, `FIVE_DATASET_ACQUISITION_REPORT.md`, `DATASET_OVERLAP_AND_PRIOR_EXPOSURE_AUDIT.md` | Located, not read (audit B4, B5) | Each needs the label-derived correction. Not done here |
| C7 | `sbgv8/independent_validation/*.py`, `scripts/run_five_dataset_validation.py` | Historical code (audit B6, B7) | Frozen at `ca7c2b2a`. Must not be modified. Document, do not edit |
| C8 | `results/v8/independent-validation/prediction_lock_metadata.json`, `locked_predictions_manifest.json` | Lock hashes stub predictions (audit B8) | Document only. Not edited |
| C9 | `discussion.tex:48–52` and `introduction.tex:80` | Read. Say no external validation has occurred | No change. Accurate |
| C10 | `sections/design.tex:24, 27`, `sections/reproducibility.tex:25, 35` | Located. Mention "five-dataset" as an audit or generator item | Accurate as written (describe the audit, not the run). Not edited |
| C11 | `sections/results.tex:144` section title "The five-dataset artifact" | Retained | Title is accurate |

## D. Search trail

Searches run on the copied manuscript and registers, case-insensitive:

1. Run-specific terms (from the audit): `FIVE_DATASET`, `five-dataset`, `250-pair`, `blinded_adjudication`, `locked_predictions`, `prediction_lock`, `independent-validation`, `sealed prediction`, `ca7c2b2a`.
2. Equivalent phrasing: `end to end`, `end-to-end`, `sealed`, `external validation`, `five datasets`, `real-world`, `Podman`, `adjudicat`, `human (review|verdict|label)`, `reviewer`, `250`, `Defects4J`, `BugsInPy`, `BEARS`, `BugSwarm`, `Bugs.jar`, `generali[sz]`, `transfer`, `held-out`, `holdout`, `independent (validation|cohort|corpus)`, `prediction lock`, `stub`.

Results used to pick corrections: `results.tex:144–154`, `design.tex:40, 43, 65, 103`, `introduction.tex:46, 66, 80`, `conclusion.tex:12`, `reproducibility.tex:25, 35, 53, 58–66`, `threats.tex:15, 20, 23`, `discussion.tex:48–52`, both registers at rows 100 and 118.

Matches not treated as errors: "reviewer" in `approach.tex`, `trust.tex` and `tab_security.tex` refers to optional reviewer checks in the SBG method, not to the 250-pair run. "transfer" and "generalisation" in `results.tex:154` are negated ("no ... generalisation"). "Real-world" appears only in the `final_transformation` documents, where it is a disclaimer.

Not searched: the full text of the binary figure PDFs (only matched by name), and the 61 uncommitted files in the SBG repository outside `paper/`.

## E. Limits

- Only the passages listed above were read in full. Located-only items are in section C.
- No corrections were applied to the SBG repository, `ca7c2b2a`, or the frozen V8 snapshot.
- The corrections describe the evidence. They do not make any positive claim about SBG V8.
- Nothing was compiled. The LaTeX build was not run on the corrected copy, so the caption and table edits are unchecked for overfull boxes or syntax.
- Nothing was submitted, and no reviewer decision or sign-off was recorded.

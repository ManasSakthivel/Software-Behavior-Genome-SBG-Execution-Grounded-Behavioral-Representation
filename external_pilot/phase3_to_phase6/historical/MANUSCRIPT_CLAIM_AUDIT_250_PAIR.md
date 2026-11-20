# Claim audit: manuscript and repository claims that rely on the 250-pair run (ca7c2b2a)

Scope: `paper/IEEE_ACCESS_V8_FINAL/` (working tree, including uncommitted edits), `reports/v8/independent-validation/`, `results/v8/independent-validation/`, `sbgv8/independent_validation/`, `scripts/run_five_dataset_validation.py`, `README.md`, `STATUS.md`. Read-only: no file in the source repository was edited.

Method: grep for run-specific terms (FIVE_DATASET, five-dataset, 250-pair, blinded_adjudication, locked_predictions, prediction_lock, independent-validation, sealed prediction, ca7c2b2a). That gives 179 matching lines across the files below. Lines marked **read** were checked by reading the claim text. Lines marked **located** were found by grep and not individually read; they need the same check before any correction is final.

## A. Manuscript (paper/IEEE_ACCESS_V8_FINAL)

| # | File:line | Claim (short quote) | Depends on 250-pair run? | Status | Required correction |
|---|---|---|---|---|---|
| A1 | `sections/results.tex:144–154` | "The five-dataset artifact" bullets: 12 templates, SHA-1 literal digests, 0/180 Java compiled, outcomes set from labels, hard-coded integrity flag, activation-stub predictor, six duplicates | Yes | **read**; accurate | Keep. Remove the phrase "establishes only that … prediction lock process 250 records end to end": the predictions came from the stub, so the lock does not show that SBG's predictor ran. Replace with "establishes only that the record schema and harness run on label-derived records." |
| A2 | `sections/design.tex:40`, row F (`:65`) | "Template-derived artifacts, excluded … its 250 records come from 12 hand-written templates" | Yes | **read**; accurate | Add "outcomes set from labels; stub predictor; 0 human verdicts." |
| A3 | `sections/introduction.tex:46` | "template-generated with label-derived outcomes, so this paper excludes it" | Yes | **read**; accurate but incomplete | Add "and the predictor was a stub." |
| A4 | `sections/conclusion.tex:12` | "The project's five-dataset artifact was template-generated and is excluded." | Yes | **read** | Change "excluded" to "classified invalid as external-validation evidence (commit ca7c2b2a)". Exclusion alone does not say why. |
| A5 | `sections/reproducibility.tex:53` | "The five-dataset artifact does not meet the evidential standard … It is excluded entirely." | Yes | **read**; accurate | Add the reason in one clause. |
| A6 | `sections/threats.tex:20` | External-validity row mentions the artifact | Yes | located (line truncated in grep) | Read and confirm it does not say the artifact provides external evidence. |
| A7 | `CLAIM_EVIDENCE_REGISTER.md:100`, `FINAL_CLAIM_EVIDENCE_REGISTER.md:100` (row V1) | "250 records (244 distinct) … outcomes set from labels; integr…" | Yes | **read**; accurate | Add "stub predictor; 0 human verdicts; environment identifier hard-coded." |
| A8 | `CLAIM_EVIDENCE_REGISTER.md:118`, `FINAL_CLAIM_EVIDENCE_REGISTER.md:118` | "250-pair 'independent validation', 200/50 split, 2,500 ERS trials, 1.90 ms" → "Label-derived; no benchmark executed" | Yes | **read** | The register already says label-derived. Add "predictor was the activation stub" and "not an execution claim." |
| A9 | `audit/DATASET_VERIFICATION_REPORT.md` (20 hits), `audit/five_dataset_summary.json` (6), `audit/STATISTICAL_AUDIT_REPORT.md` (4), `audit/stats_summary.json` (2), `audit/SIMULATED_PEER_REVIEW.md` (1), `audit/ARCHITECTURE_AND_DEFINITIONS.md` (1) | Audit of the artifact and its statistics | Yes | located | Read; any statistic computed on the 250 records must be marked label-derived and not evidence. |
| A10 | `external_validation_audit/FIVE_DATASET_EXTERNAL_VALIDATION_AUDIT.md` (5), `DEVELOPMENT_EXTERNAL_OVERLAP_REPORT.md` (5), `EXTERNAL_HOLDOUT_STATUS_REPORT.md` (2), `INDEPENDENT_ADJUDICATION_PROTOCOL.md` (2), `ADJUDICATION_REGISTRY.json` (1), `PROJECT_AND_CASE_PROVENANCE_REGISTRY.json` (2) | Provenance, adjudication and holdout status | Partly | located | Check whether any registry lists the 250 records as adjudicated or sealed externally. None should. |
| A11 | `final_transformation/EXTERNAL_VALIDATION_CLAIM_DECISION.md`, `COMPLETE_EXTERNAL_VALIDATION_AUDIT.md`, `EXTERNAL_CASE_EVIDENCE_REGISTRY.json` | Decision documents | Partly | located | Confirm the decision is "no external validation claim". |
| A12 | `scripts/verify_five_dataset.py` (11), `stats_recompute.py` (5), `make_figures.py` (2) | Code that audits or plots the artifact | Yes | located | Figures showing the 250 records (Fig. landscape panel c, hatched and grey) must carry the "template/label-derived, invalid" label. |
| A13 | `sections/abstract.tex`, `sections/discussion.tex:48–52` | Discussion lists prerequisites for a confirmatory study, including "an external, held-out corpus" | No | located | Keep. The prerequisites confirm that external validation has not happened. |

## B. Repository reports and code (not the manuscript)

| # | File:line | Claim | Status | Required correction |
|---|---|---|---|---|
| B1 | `reports/v8/independent-validation/SBG_V8_FIVE_DATASET_EXECUTION_REPORT.md:3–4` | "Frozen SBG V8 Engine … Linux Podman Runtime"; "Total Pairs Executed: 250" | **read**; false | Mark as superseded: no program was executed; environment ID is hard-coded (`executor.py:80`). |
| B2 | `reports/v8/independent-validation/FIVE_DATASET_FINAL_EXECUTION_SUMMARY.md:5, 16, 18` | "SBG V8 was executed against five independent, real-world software change datasets"; "Frozen SBG V8 Execution COMPLETED (250 pairs)"; "Prediction Package Lock SEALED & HASHED"; 200/50 | **read**; false | Same as B1. The seal proves the file did not change, not that it came from SBG. |
| B3 | `reports/v8/independent-validation/FIVE_DATASET_PRELIMINARY_STATISTICAL_REPORT.md:23` | "This 250-pair independent execution cohort serves as the initial external validation cohort." | **read**; false | Delete the claim or mark invalid. |
| B4 | `reports/v8/independent-validation/BLINDED_ADJUDICATION_EXPORT_GUIDE.md` (6) | Describes reviewer packets and the sealed package for "human reviewers" | located; the packet exists, but 0 verdicts | State that no reviewer completed any case. |
| B5 | `reports/v8/independent-validation/CHANGE_PAIR_REPRODUCIBILITY_REPORT.md`, `SBG_V8_FIVE_DATASET_ERS_REPORT.md`, `…/SBG_V8_EXECUTION_FAILURES_AND_EXCLUSIONS.md`, `…/FIVE_DATASET_ACQUISITION_REPORT.md`, `…/DATASET_OVERLAP_AND_PRIOR_EXPOSURE_AUDIT.md` | Reproducibility, ERS and acquisition statements | located | Each needs the same label-derived correction. Overlap audit should say the five benchmark names are not the five benchmarks named in the paper's own audit. |
| B6 | `sbgv8/independent_validation/executor.py` (2), `analyze_and_report.py` (29), `blinded_export.py` (11), `audit.py` (1), `datasets.py` (1), `reproducibility.py` (1) | Implementation of the artifact | verified | Do not modify (historical). Document that `executor.py` is not an execution path and that `analyze_and_report.py` reports label-derived numbers. |
| B7 | `scripts/run_five_dataset_validation.py` (3) | Runner for the artifact | verified | Document that it runs the stub path. |
| B8 | `results/v8/independent-validation/prediction_lock_metadata.json` (4), `locked_predictions_manifest.json`, `blinded_adjudication_template.csv` | Lock metadata and empty reviewer form | **read** (template: 0/250 verdicts) | Document that the lock hashes stub predictions. |
| B9 | `README.md:44` | "Deferred to Phase 3 (not done, no claim): … K5 …" | **read**; correct | No change. |
| B10 | `STATUS.md` | No mention of the 250-pair run | — | No change. |

## C. Totals

- Grep matches (run-specific terms): 179 lines.
- Distinct affected files: about 45, grouped into the sections above.
- Claim clusters requiring correction: 8 manuscript clusters (A1–A5, A7, A8, A12) and 5 repository report clusters (B1–B5). Clusters A6, A9–A11, A13 and B6–B10 were located or verified but not fully read.

## D. What was verified directly

- `executor.py`: outcome from `purpose` (lines 35–41); hard-coded `deterministic`, `n_repeat_runs`, `hits`, `branches` (lines 52–59); hard-coded `env_id`, `env_consistent`, `integrity_ok` (lines 80–82); `ActivationStubPredictor` (lines 109, 168); no subprocess or sandbox call.
- Template: 250 rows, 0 filled `adjudicator_verdict` values.
- Execution results: 200 DIVERGENT_OBSERVABLE, 50 NO_DIVERGENCE_OBSERVED, matching the label split.

## E. Not done

- Individual reading of the located clusters in section C.
- Any change to the manuscript, reports or code. The corrections above are recommendations for the author, and no historical record was rewritten.

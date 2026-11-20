# Reviewer adjudication protocol (Phase 5)

Status: **PENDING. Two independent human reviewers have not been recruited.** No reviewer has seen or submitted anything. Model-generated or agent reviews are not substitutes and are not counted.

Design:
- Two reviewers, working independently, blind to SBG outputs (none exists yet), to each other's labels, and to the commit subjects' intent beyond the diff.
- Inputs: `BLINDED_REVIEW_PACKAGE/case_index.json` and the per-case production and test diffs.
- Labels: `DIFFERENCE_PRESENT`, `NO_DIFFERENCE`, `INCONCLUSIVE`, per observation category (outcome, exception, side_effect, api), with evidence and confidence.
- Disagreements: resolved by a third adjudicator if one is available; otherwise reported as unresolved. Original submissions are kept unmodified.
- Agreement: raw percent agreement and Cohen's kappa, only once both reviewers have submitted.

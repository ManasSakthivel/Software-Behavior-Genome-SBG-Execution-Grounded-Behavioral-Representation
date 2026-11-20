# Reviewer instructions (Phase 5)

For each case folder `BLINDED_REVIEW_PACKAGE/cases/Cxx/`:
1. Read `production_change.diff` and `test_change.diff`. Judge from code and tests, not from the commit message.
2. Decide whether the old and new revisions behave differently for the observation boundary O = {outcome, exception, side_effect, api}. Answer `DIFFERENCE_PRESENT`, `NO_DIFFERENCE` or `INCONCLUSIVE`.
3. Give the category, the evidence (file and line), your confidence (low/medium/high), and any limitation.
4. Save your form to `REVIEWER_1_RESULTS/` or `REVIEWER_2_RESULTS/` as one file per case. Do not look at the other reviewer's folder.
5. Do not run tools against SBG, and do not look for SBG outputs.

# Blinded Adjudication Export Guide (Phase 5)

## 1. Cryptographic Package Sealing

The prediction package for the 250 change pairs has been cryptographically sealed and locked prior to human adjudication.

- **Package SHA-256 Digest**: `c1ee208e1da99643a59dcbc313c0f083bba61ec0bc5003aa4e53ea814e166298`
- **Locked Predictions File**: `results/v8/independent-validation/locked_predictions_manifest.json`
- **Reviewer Case Packet**: `results/v8/independent-validation/blinded_adjudication_cases.json`
- **Reviewer Form CSV**: `results/v8/independent-validation/blinded_adjudication_template.csv`

## 2. Protocol for Independent Human Reviewers
1. Two independent software engineers inspect each case in `blinded_adjudication_cases.json`.
2. Reviewers examine the patch diff, changed files, and test descriptions WITHOUT access to SBG predictions or risk scores.
3. Reviewers assign one of three verdicts in `blinded_adjudication_template.csv`:
   - `CONFIRMED_DIVERGENCE`
   - `NO_DIVERGENCE_FOUND_WITHIN_BUDGET`
   - `INDETERMINATE`
4. The sealed package hash ensures that SBG predictions cannot be modified post-hoc after human labels are unlocked.

# Threshold provenance

Two thresholds appear in this repository. They are not interchangeable.

| Threshold | Used by | Derivation evidence | Status |
|---|---|---|---|
| **τ\* = 0.072905** | output-free v7 evaluation (`MAIN_EVALUATION_v6*_output_free_v7`) | `experiments/final/derive_threshold.py`, `artifacts/final/THRESHOLD_FROZEN.json`; re-derived in `tests/test_threshold_provenance.py` | Verified: maximises Youden J on the 345 statistically valid dev pairs (9 programs); J = 0.378, TPR = 0.558, FPR = 0.180. The script refuses non-dev input. |
| **τ\* = 0.08** | hard-negative benchmark (12 pairs), regression corpus (15 pairs), BugsInPy / QuixBugs pilots, v5 scripts | **None found.** | Provenance unverified. |

## What is known about 0.08

* Code comments describe it variously as "median SBG distance of SP pairs on
  dev split (from V5 artifacts)" (`experiments/v5/regression_evaluator.py`),
  "pre-fixed" (`hard_negative_evaluation.py`, `regression_evaluation.py`) and
  "frozen from synthetic" (`experiments/external/*`).
* The constant first appears in commit `4409652` (2026-08-21, v5 sprint). No
  artifact in that commit or later records a computation producing 0.08.
* The v5 dev AUROC artifact (`artifacts/v5/B07/results_dev.json`) does not
  contain per-pair distances, so the "median of dev SP pairs" statement cannot
  be re-checked from committed data.
* `THRESHOLD_FROZEN.json` records 0.08 as the `previous_value`, derived "under
  published protocol", "superseded for output_free_v7 results".

## Consequence for claims

Statements that 0.08 was "fixed in advance", "fixed before these pairs were
scored" or "not re-tuned" **cannot be verified** and have been removed from the
README, generated tables, `LIMITATIONS.md` and script docstrings. The 5/12
hard-negative and 7/15 regression counts remain correct arithmetic at τ = 0.08,
but they are not evidence of a pre-registered operating point.

## Rule for new work

Any future threshold must be derived by a committed script on a dev split only,
written to a hashed artifact before test scoring, and covered by a test that
re-derives it. A threshold must never be set or adjusted after seeing test
scores.

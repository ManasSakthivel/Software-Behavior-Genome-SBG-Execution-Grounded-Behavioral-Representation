# datasets/v8

**DEVELOPMENT, design-exposed, not independent.** `DEV_MANIFEST.jsonl` lists the 321 Phase 2 development pairs
(31 QuixBugs, 85 QuixBugs negatives, 150 synthetic, 55 BugsInPy units). It is built by `sbgv8.manifest.build_dev_manifest()`
from `datasets/v8/dev_records.jsonl` if present, otherwise from
`results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv` (one row per pair, system B1).

- Labels are Phase 2 generator or declared-test labels (`label_source=phase2_dev_generator_label`), not adjudicated; `outcome_class=not_adjudicated`.
  DIV -> y=1, NO_OBS_DIFF -> y=0, UNLABELLED/SUSPECT -> y=None with `include=false` and a reason.
- Family rule `arm_prefix_v1`: family = pair_id prefix (quixbugs|quixbugs_neg -> quixbugs, synthetic, bugsinpy_units -> bugsinpy). It uses no label, verdict or the label-bearing `dataset` column.
- Version info, change metadata and budgets are not recorded for Phase 2 pairs and are stated as such.
- Use: debugging, fixtures, pipeline checks. Not for calibration claims or generalisation claims. Project-level diversity is low (one project holds 116 pairs; 55 BugsInPy units are all unlabelled).
- Holdout: no holdout exists; none is created here. See `reports/v8/V8_PHASE3_AUTHORISATION_PACKAGE.md`.
- `adjudication_templates/`: blank templates for Phase 3; nothing in them is a decision.
Specification: `reports/v8/V8_DATASET_MANIFEST_SPECIFICATION.md`.

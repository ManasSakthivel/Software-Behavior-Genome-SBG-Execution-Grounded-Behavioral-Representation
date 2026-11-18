# V8 dataset manifest specification

Code: `sbgv8/manifest.py` (`ManifestRow`, `validate`, `write_jsonl/read_jsonl`, `write_csv/read_csv`, `manifest_hash`, `build_dev_manifest`). Design basis: `research/v8_final_design/07`.

## Row fields
| field | content |
|---|---|
| project, pair_id | project id (split unit), unique pair id |
| family, family_rule | project family and the id of the label-independent rule that derived it (rule text is kept with the data description) |
| version_info, change_meta | base/variant identifiers; entry point, changed files, change kind (never commit-message text as a feature) |
| observation_boundary | channels counted (04: O) |
| adjudication_budget | frozen budget b |
| outcome_class | `confirmed_divergence`, `no_divergence_found_within_budget`, `unresolved`, `not_adjudicated` (development), `sealed` (holdout) |
| y, label_source | 1/0/None; source of the label (development: `phase2_dev_generator_label`) |
| provenance | where the pair came from, contamination flags (public benchmark, LLM-exposed corpus) |
| split | development, calibration, evaluation, holdout |
| include, reasons | inclusion flag; mandatory reason when excluded |
| status | e.g. the development label below |

## validate() checks
required fields present; split and outcome class in the allowed sets; unique pair ids; one split per project (so no project in two splits); one family derivation per project; excluded rows carry a reason; y in {0,1,None}; **holdout rows carry no label** (y None, no label_source, outcome class sealed or not adjudicated). Returns a list of issues.

## IO and hashing
JSONL (one sorted-key row per line, sorted by pair id) and CSV (nested columns JSON-encoded). `manifest_hash` is sha256 over per-row sha256 digests sorted by pair id: independent of row order, changes with any field. The hash is recorded in the registration (06).

## Development manifest
`datasets/v8/DEV_MANIFEST.jsonl` is labelled **DEVELOPMENT, design-exposed, not independent** (321 pairs; sources in `datasets/v8/README.md`). Family rule `arm_prefix_v1`: family from the pair-id prefix only (quixbugs, synthetic, bugsinpy); not from truth, verdict, generator label or the `dataset` column (which encodes labels). Consequences, stated: one project (quixbugs) holds 116 pairs; synthetic pairs are one generator family spread over 101 pseudo-projects (program names); BugsInPy units are all unlabelled. The manifest is for debugging and fixtures only.

## Limits
Validation checks structure, not truth: it cannot prove that families are independent, that labels are correct or that a holdout was never read (see the holdout guard log in `sbgv8/splits.py`).

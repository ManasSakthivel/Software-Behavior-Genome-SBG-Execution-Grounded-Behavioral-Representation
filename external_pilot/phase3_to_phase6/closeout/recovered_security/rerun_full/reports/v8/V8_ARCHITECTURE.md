# V8 architecture (implementation view)

Status: DEVELOPMENT / EXPLORATORY. Interfaces are fixed in `sbgv8/schema.py` and `reports/v8/V8_INTERFACE_CONTRACT.md`.

## Module map
| Stage | Modules | Reads | Writes |
|---|---|---|---|
| Collection (A) | `sbgv8/collect.py`, `sbgv8/__main__.py compare`, `experiments/v8/dev_collect.py` | pairs, inputs, config | V7-B `evidence.jsonl`, `verdict.json`, sidecar `v8_parts.json` |
| Adapter / validation (A) | `sbgv8/adapter.py`, `sbgv8/trust.py`, `__main__ verify` | evidence dir (+ sidecar) | `EvidenceRecord`, `TrustReport` |
| Features (B) | `profile.py` | `EvidenceRecord` (never `y`) | `schema.FEATURES` dict |
| Perturbation (B) | `perturb.py`, `ers.py` | records, predictor | perturbed records, ERS features |
| Calibration (C) | `calibrate.py`, `baselines.py`, `stats.py` | features, `y` (fit only) | risk model |
| Policy (B/C) | `predict_risk`/`decide` protocol | record | (verdict, risk) |
| Evaluation (C) | `evaluate.py` | records, predictors, `y` | tables, results.json |
| Governance (D) | `adjudication.py`, `manifest.py`, `splits.py` | labels, manifest | splits, `y` |
| Reporting | `reports/v8/*` | results | documents |

Separation rule: collection never computes features or labels; the adapter never executes anything; labels enter only through `adapter.load_record(label=...)` (dev: the Phase 2 generator label) and are read only by calibration fitting and evaluation.

## Data flow
`python -m sbgv8 compare` -> `sbgv7.runner.compare_versions` (UNMODIFIED; `sbgv7.runner.finalize` is wrapped in the parent process only, captured `parts` written to `v8_parts.json` with sha256 of `evidence.jsonl` and the log head, wrapper always restored) -> `adapter.load_record` -> `EvidenceRecord` -> profile -> perturbation/ERS -> calibration -> decision -> evaluation. `python -m sbgv8 verify DIR` = `sbgv7 verify` + `trust.check_sidecar`. Other subcommands appear when modules of B/C/D expose `cli_register(subparsers)`; `__main__` imports them lazily and skips missing ones.

## Adapter mapping (modelling choices, each stated in `adapter.py`)
- `obs_fingerprint`: sha256 (first 32 hex) of (t, ret, type, msg, stdout, files, globals, argmut, fd1) of the VARIANT side's primary run.
- `channels_present`: capture completeness, not activity: outcome (t present, not lossy), exception (t recorded), side_effect (stdout/files/globals/argmut all captured, not truncated), api (signature recorded). A run without an observation captures nothing.
- `n_repeat_runs` = repeat + replay + alt runs, both sides. `deterministic` = outcome != QUARANTINED. `lossy`, `degenerate`, `outcome` from the package rows.
- `hits`/`branches`: from the sidecar when it is bound to the log and equal to the Run records; otherwise empty with `meta.no_hits=true`.
- `changed_units`: package `regions.units`. `static_branches`: branch instructions on those lines, recomputed from the recorded sources with `sbgv7.runner._static_branches`.
- `config` = `{r_det, r_replay, k_alt, s2_branch_floor}`. `blockers` = reason codes of the SufficiencyRecord (empty for DIVERGENT). `integrity_ok` = `sbgv7 verify` passed AND the sidecar is not inconsistent. `provenance` stays `declared` (no provenance source exists for the dev pairs yet), so `prov_ok` is not informative on this data. `family` = project (placeholder until D's rule).

## Development dataset
`experiments/v8/dev_collect.py` runs the 312 driven pairs of E3 (QuixBugs buggy/fixed, QuixBugs SP negatives, synthetic, BugsInPy units; the 9 NOT_DRIVEN of E3 are not run) with the E3 per-run limits (cpu 2 s, wall 5 s, budget 60 s, 4 workers) into `results/repro/v8_dev_<ts>/` (gitignored) and builds `datasets/v8/dev_records.jsonl`.
Label mapping from the `truth` column of `dev_pairs_per_system.csv` (distinct values: DIV, NO_OBS_DIFF, UNLABELLED, SUSPECT_LABEL): DIV -> y=1, NO_OBS_DIFF -> y=0, UNLABELLED and SUSPECT_LABEL -> y=None. `meta.label_source="phase2_dev_generator_label"`, `meta.truth_raw` keeps the original value, `split="development"`. These are generator/pair-construction labels, not adjudicated: everything computed from them is development/exploratory.

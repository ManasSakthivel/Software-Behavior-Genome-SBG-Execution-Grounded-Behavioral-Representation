# Classification of commit ca7c2b2a (250-pair "five-dataset external validation")

Commit: `ca7c2b2a6fa8e212650f262d17946741bde65521`, "feat(v8-independent-validation): execute five-dataset external validation across 250 real-world change pairs with sealed predictions and 10 reports". Repository `~/Desktop/SBG-V8-LINUX`. Original files are preserved and were not modified.

## Classification: INVALID for external-validation claims

This commit provides no evidence about SBG V8's detection, false-assurance or generalisation behaviour. Its reports, locked predictions and statistics must not be cited as external validation.

## Verified reasons

1. **No program was executed.** `sbgv8/independent_validation/executor.py` contains no `subprocess`, sandbox or import of the program under test (grep confirmed).
2. **Outcomes are set from test labels.** `pair_to_evidence_record` assigns `CONFIRMED_DIFF` when `purpose == "trigger_discriminating"` and `SAME` otherwise (lines 35–41).
3. **Hard-coded evidence fields.** `deterministic=True`, `n_repeat_runs=3`, `hits={"base":[1,2,3],"variant":[1,2,3]}`, `branches={...}` (lines 52–59), and `env_id="linux_podman_cgroups_v2"`, `env_consistent=True`, `integrity_ok=True` (lines 80–82).
4. **Stub predictor.** `ActivationStubPredictor` is used (lines 109, 168). Its own docstring in `sbgv8/ers.py` says it is "for tests and CLI smoke only".
5. **Label-derived verdict split.** The execution results show 200 `DIVERGENT_OBSERVABLE` and 50 `NO_DIVERGENCE_OBSERVED`, matching the 200/50 label split exactly.
6. **No human adjudication.** `results/v8/independent-validation/blinded_adjudication_template.csv` has 250 rows and 0 filled `adjudicator_verdict` values (verified).
7. **Template-generated records.** The manuscript's static audit (`scripts/verify_five_dataset.py`) reports 250 records from 12 hand-written templates, SHA-1 digests of literal strings, 0 of 180 Java records compiled or run, and six duplicate records.

## Status of the repository's own claims

The reports in `reports/v8/independent-validation/` say the run was "COMPLETED" on a "Linux Podman Runtime" with a "SEALED & HASHED" prediction lock (`c1ee208e…166298`), and call it the "initial external validation cohort". Reasons 1–7 show these statements do not describe an execution. The seal proves only that the stored predictions have not changed since they were written.

## Consequences

- Any claim that SBG V8 was externally validated on 250 pairs is unsupported.
- The prediction-lock seal cannot be used as evidence of prediction timing, because the predictions came from a stub, not from SBG V8.
- The historical record is kept as is. Corrections belong in new dated documents, not in edits to `ca7c2b2a` or its reports.

Companion file: `MANUSCRIPT_CLAIM_AUDIT_250_PAIR.md` lists the affected claim locations and required corrections.

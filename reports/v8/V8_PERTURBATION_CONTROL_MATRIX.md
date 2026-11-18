# V8 perturbation control matrix (generated from `sbgv8/perturb.PERTURBATION_MATRIX`)

Status: development design artefact; no empirical claims.

## Post-hoc versus execution-level
Everything implemented in `sbgv8/perturb.py` is **post-hoc**: it edits a copy of a recorded `EvidenceRecord` and recomputes the profile and decision. P2, P5 and P6 additionally have a **real-execution** version (new runs through the V7-B engine, or re-collection with smaller `r_det`/`r_replay`/`k_alt`) that needs the collector (agent A) and is NOT implemented here. The post-hoc P2 and P6 inputs are *synthetic recorded inputs* (`PerturbationRecord.mode = post_hoc_synthetic`, `execution_required = True`): they test the wiring of the decision and of the response, not discovery power. P5 post-hoc only flips recorded determinism flags and halves the recorded repeat count.

## Matrix
| ID | Name | Real execution needed for true version | Post-hoc variant implemented | Only recorded evidence modified | Expected response | Tolerance | Failure condition |
|---|---|---|---|---|---|---|---|
| P1 | relevant-evidence deletion | no | yes | yes | risk non-decreasing, or abstention (NDO -> INSUFFICIENT counts as pass) | risk drop <= 1e-6 | risk decreases and decision is not an abstention |
| P2 | irrelevant augmentation | yes | yes | yes | risk and decision unchanged | |delta| <= 0.02, verdict equal | risk moves more than tol or the verdict changes |
| P3 | duplicate augmentation | no | yes | yes | risk and decision unchanged | |delta| <= 0.02, verdict equal | risk moves more than tol or the verdict changes |
| P4 | observation masking | no | yes | yes | risk non-decreasing, or abstention | risk drop <= 1e-6 | risk decreases and decision is not an abstention |
| P5 | reproducibility-budget degradation | yes | yes | yes | risk non-decreasing, or abstention | risk drop <= 1e-6 | risk decreases and decision is not an abstention |
| P6 | independent discriminating evidence | yes | yes | yes | decision becomes DIVERGENT_OBSERVABLE, or risk increases, or abstention | none beyond the disjunction | none of the three happens |
| P7 | provenance degradation | no | yes | yes | risk non-decreasing, or abstention | risk drop <= 1e-6 | risk decreases and decision is not an abstention |
| P8 | integrity violation | no | yes | yes | evidence rejected: integrity_ok=0 and decision INSUFFICIENT | exact | perturbed record still yields NDO or DIVERGENT |
| P9 | environment inconsistency | no | yes | yes | risk non-decreasing, or abstention | risk drop <= 1e-6 | risk decreases and decision is not an abstention |

## Per-perturbation detail
### P1 relevant-evidence deletion
- Purpose: Does assurance drop when the only evidence for a changed unit (or channel) is removed?
- Definition: Delete the clean SAME inputs that are sole reachers of one changed unit (or sole capturers of one channel).
- Transformation: inputs -= sole reachers; recomputed from recorded parts, no execution.
- Confounding risks: deletion response is a function of the same recorded evidence and may be redundant with mu_min; N/A if nothing is deletable
- Validity by evidence type: static_coverage=valid; repeat_runs=valid; observations=valid; provenance=partial; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P2 irrelevant augmentation
- Purpose: Is added evidence about unchanged code (quantity) credited as information?
- Definition: Add k inputs whose hits lie only on unchanged lines.
- Transformation: POST-HOC variant: synthetic recorded inputs appended (hits off changed units, fresh fingerprints). EXECUTION variant (new runs via the V7-B engine) requires the collector.
- Confounding risks: synthetic inputs are not real runs; fresh fingerprints inflate n_eff/n_same, which is the quantity trap being tested
- Validity by evidence type: static_coverage=valid; repeat_runs=valid; observations=valid; provenance=valid; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P3 duplicate augmentation
- Purpose: Is repeating the same evidence credited as independent evidence?
- Definition: Copy recorded inputs k times (same fingerprint, hits, provenance) with duplicate_of set.
- Transformation: inputs += copies; no execution.
- Confounding risks: a predictor reading raw len(inputs) (not the profile) is penalised by design
- Validity by evidence type: static_coverage=valid; repeat_runs=valid; observations=valid; provenance=valid; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P4 observation masking
- Purpose: Does losing observation channels raise risk?
- Definition: Drop channel(s) from channels_present of every input; inputs left with no channel become degenerate with a common fingerprint; a CONFIRMED_DIFF input left with no channel becomes degenerate SAME.
- Transformation: post-hoc on recorded observations. APPROXIMATION: fingerprints of partially masked inputs cannot be recomputed from a hash, so they are kept.
- Confounding risks: synthetic missed divergences do not follow the natural error distribution (property tests only, never fitting); N/A if channel immaterial
- Validity by evidence type: static_coverage=n/a; repeat_runs=n/a; observations=valid; provenance=n/a; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P5 reproducibility-budget degradation
- Purpose: Does less reproducibility evidence raise risk?
- Definition: Halve n_repeat_runs of all inputs and mark a seeded fraction of SAME inputs non-deterministic.
- Transformation: POST-HOC variant on recorded flags. EXECUTION variant = re-collection with smaller r_det/r_replay/k_alt (config), requires the collector.
- Confounding risks: post-hoc flags do not show whether a real smaller budget would still find the same witness
- Validity by evidence type: static_coverage=n/a; repeat_runs=valid; observations=partial; provenance=n/a; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P6 independent discriminating evidence
- Purpose: Does an independent input that reveals a difference change the outcome?
- Definition: Add an input with outcome CONFIRMED_DIFF, independent provenance, hitting all changed units.
- Transformation: POST-HOC variant: synthetic recorded witness. EXECUTION variant (a genuinely new run) requires the collector. The response comes from the decision function.
- Confounding risks: a synthetic witness tests wiring, not discovery power; N/A when already divergent
- Validity by evidence type: static_coverage=partial; repeat_runs=n/a; observations=valid; provenance=valid; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P7 provenance degradation
- Purpose: Does untrusted or label-derived provenance fail to raise assurance?
- Definition: Set provenance_ok False (mode=untrusted) or provenance=label_derived (mode=label_derived) on a seeded fraction of inputs.
- Transformation: flags only.
- Confounding risks: V7-B has no provenance concept: the V7-B-style decision is insensitive by construction
- Validity by evidence type: static_coverage=n/a; repeat_runs=n/a; observations=partial; provenance=valid; integrity=n/a; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P8 integrity violation
- Purpose: Is corrupted or unverifiable evidence rejected?
- Definition: Set integrity_ok False; variant=corrupt also removes half of the recorded hits (simulated corruption).
- Transformation: flag (sbgv8.trust.check works on evidence directories, not records; the record-level proxy is integrity_ok).
- Confounding risks: record-level flag only; real forgery detection is tested in test_trust, not here
- Validity by evidence type: static_coverage=n/a; repeat_runs=n/a; observations=n/a; provenance=n/a; integrity=valid; environment=n/a
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

### P9 environment inconsistency
- Purpose: Does an inconsistent environment fail to raise assurance?
- Definition: Set env_consistent False and tag env_id.
- Transformation: flags only.
- Confounding risks: none beyond N/A when already inconsistent
- Validity by evidence type: static_coverage=n/a; repeat_runs=n/a; observations=n/a; provenance=n/a; integrity=n/a; environment=valid
- Provenance record: `PerturbationRecord(pid, params, seed, input_digest, output_digest, mode, execution_required, applicable, reason)`

## Rules
- `apply(rec, pid, seed, **params)` is deterministic (RNG seeded from pid, seed and the record digest, which excludes `y` and `meta`), returns a new record and never mutates its input.
- Not applicable cases return an unchanged copy with `applicable=False` and a reason (no sole reacher for P1, immaterial channel for P4, no clean SAME input for P2, already divergent for P6, already violated for P8/P9).
- P8 record-level proxy: `integrity_ok=False`. `sbgv8.trust.check` verifies evidence directories, so real forgery rejection is tested in `test_trust`, not here.
- P4 approximation: fingerprints of partially masked inputs cannot be recomputed from a hash and are kept; inputs left with no channel become degenerate. Synthetic missed divergences are for property tests only, never fitting.

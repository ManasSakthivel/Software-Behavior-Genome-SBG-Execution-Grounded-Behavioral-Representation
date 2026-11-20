Reconciled version R1 of SBG_V7_DATA_AND_EVIDENCE_SCHEMA.md; original preserved at reports/v7_design/_original_archive/

# SBG V7: Data and Evidence Schema, R1 (schema v1.1.0 draft)

Status: documentation only. Authority: `reports/final/V7B_FROZEN_SPEC.md` ("FS", especially s2-s8) > `P0_BINDING_DECISIONS.md` (D1-D11) > `P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md` ("SPEC") > `p0_reconciliation/P0_EVIDENCE_TAXONOMY_AND_SCHEMA_AUDIT.md` ("ESA", source of the entity gaps and the taxonomy) > this file. The original schema (`_original_archive/SBG_V7_DATA_AND_EVIDENCE_SCHEMA.md`, "ORIG-S") is the base text: **every entity and rule of ORIG-S not mentioned below is unchanged** (section numbers cite ORIG-S). This file lists the deltas; it does not copy the 42 KB original. Where the as-built implementation (`sbgv7/records.py`) differs from this schema, the difference is an open item (OI-nn in the Index) for `PHASE_2_SPEC_CONFORMANCE_AUDIT.md`, not a decision here. No JSON in this file was validated by a tool.

## 1. Layers, evidence class and status (ORIG-S s1; CM EV-01, EV-02; D4)

ORIG-S layers RAW / DERIVED / DECISION remain the storage and write-permission layers. **Added to the common header of every record:** `evidence_class` in {`observation`, `derived`, `inferred`, `proof`} and optional `status` in {`missing`, `invalid`, `uncertain`} (FS s8; ESA s2).

| Class | Meaning | Entities |
|---|---|---|
| observation | recorded by an instrumented sandboxed execution or tool; root | `ProgramVersion`, `ExecutionRun`, `EventChunk`/events, `InstrumentationCompleteness`, `Reproducibility` runs, `ReplayCheck` |
| derived | deterministic function of observations and declared parameters; any party recomputes the same bytes | `SourceMapping`, `ChangedRegions`, the difference part of `Witness`, `SufficiencyRecord` counts and level (status `uncertain`), `StateObservation` |
| inferred | heuristic or model-dependent; valid algorithms may disagree | `SemanticCorrespondence`, divergence `locus`, `ImpactSet`, `DerivedInvariant`, `Verdict` as a policy application (the `Verdict` value itself follows FS s2) |
| proof | exhaustive or formal argument over a stated domain | `FormalResult` (adds `method = exhaustive_domain`, `domain`, `bound`) |

Status qualifiers: `missing` (evidence that should exist is absent, e.g. `kinds_dropped`, `blind_spots`, `truncation`, unmapped regions, build failure, tombstone); `invalid` (record exists but may not support a claim: `Supersession`, failed audit replay, `policy_below_minimum`, trace tamper, environment drift); `uncertain` (carries doubt the consumer must propagate: S-level, `alignment_trust`). Verdict mapping (FS s8): `DIVERGENT_OBSERVABLE` is derived-on-observation with an inferred locus; `NO_DIVERGENCE_OBSERVED(S)` is derived with status `uncertain`; `INSUFFICIENT` is status `missing` or `invalid` with a reason code. The recorded `internal_divergence` annotation is derived, `uncertain`, present only if module E is on and absent (not `none`) otherwise. `SourceMapping` moves from RAW (ORIG-S 2.8) to class `derived` (it is a diff-algorithm output); the diff algorithm and version are recorded.

## 2. New entities (CM EV-05, V-05, EV-11, EV-12; ESA s5 items 2, 4)

| Entity | Class | Producer | Key fields |
|---|---|---|---|
| `HarnessDeclaration` | observation (declared) | A/L config | `c_obs`, `normaliser_id`, `float_tol {rel, abs}`, `ordered_mapping`, `exc_message` in {`exact_normalised`, `ignore`}, `stderr=excluded`, `capture_tier`, `api_break_probe`, seed policy. Part of verdict identity; referenced by every `Witness` and `Verdict`. A declared tolerance or `exc_message=ignore` is a distinct identity and never pooled with exact verdicts (FS s4) |
| `ChangedRegions` | derived (matcher output inferred) | C | `{kind, confidence, region_size_fraction, unmodelled}` per region, matcher version, `r_empty` flag; units are hit-tracked per FS s6 |
| `SignatureSketch` | derived | C | arity/names/defaults, candidate entries, `entry_missing` detail |
| `ExplorationLog` | observation | A | input list with provenance, seed, budget spent, `stop_reason` in {`budget`, `saturation`, `all_changed_branches_both_ways`, `domain_exhausted`, `unsupported_signature`, `no_generator`} |
| `RunSetRoot` | derived | I/D | Merkle root over the set of contributing run ids plus per-input rows (`o(x)`, determinism status, hit units); required for `NO_DIVERGENCE_OBSERVED` chains; replaces the inline run list of the ORIG-S 9.2 example |
| `ModuleManifest`, freeze records | observation | L | module versions and code hashes behind a verdict |
| `BuildStatus` (evidence role) | observation | B | build/import/entry resolution outcome; lets run-less `INSUFFICIENT` (B1, B2, B8) carry an evidence chain, with a degenerate `SufficiencyRecord` (`level=S0`, zero counts) allowed |
| `Supersession` | invalid-class | L | void a witness or record; sole way to void evidence (FS s2); dependents are flagged by T5 |
| evaluation entities | observation/derived | K | `AdjudicationRecord`, `BenchmarkPair`, `HoldoutCommitment`, `LeakageAuditReport`, `ScoringRecord` (custodian-signed), baseline verdict records. Labels stay outside the T6-reachable graph |

## 3. Changed records

### 3.1 Verdict (ORIG-S 2.16; CM V-01..V-07)
`value` is exactly one of `DIVERGENT_OBSERVABLE`, `INSUFFICIENT`, `NO_DIVERGENCE_OBSERVED`; precedence 1 > 2 > 3 (FS s2); `ineligible:identical` is not a Verdict value (no record counts toward metrics). `EQUIVALENT`, `SAME`, `PASS`, `VERIFIED`, `SAFE` are not enum members and must be rejected by the validator. The `reason_code` enum is the closed 18-code list of FS s7 (`import_error, unsupported_signature, ambiguous_entry, alignment_failed, unmodelled_change, sandbox_failure, unsafe_program, flaky_witness, env_sensitive, nondeterministic, resource_limit, capture_truncated, blind_spot_dominant, no_inputs, unobservable_outcome, changed_region_not_activated, budget_exhausted_s0, tool_error`). Retired from ORIG-S: `outcome_differs`/`exception_differs`/`side_effect_differs` as reason codes (kind lives on the Witness), `internal_only_difference`, `observed_same_at_S1/S2/S3`, `LOW_STATE_COVERAGE`, `TIMEOUT`. `INSUFFICIENT` stores `primary` (lowest-rank blocking condition B1..B9) plus `secondary` codes. A missing record counts as true for its blocking condition. `confidence` is not a probability of equivalence; the `nondet_adjusted` DIVERGENT path of ORIG-S is removed (a trace-unstable but outcome-stable witness is confirmed on `C_obs`, see 3.3). Unknown enum value: downgrade dependent decisions to `INSUFFICIENT`; extension only by MINOR version (FS s7).

### 3.2 SufficiencyRecord (ORIG-S 2.15; S-01, S-02)
One definition (FS s6): conjunction of floors on separately reported factors F1 determinism, F2 instrumentation completeness, F3 changed-region activation, F4 input diversity/budget. Stored: factor vector, stop reason, `r_det`, run-set Merkle root, `X_eff` size, quarantined count, unhit units, `r_empty`, `activation_status` (activated / not_activated / unknown; retained V6 taxonomy, CM V-07). Removed from ORIG-S: the three alternative S0-S3 definitions, `state_coverage.saturation_estimate` as a level input, and any scalar score deciding a level. S0 appears only inside `INSUFFICIENT`. S3: defined in FS s6, `s3_enabled=false`; may be emitted only after calibration (the as-built config refuses `true`). Empty region: `r_empty` flagged, activation vacuous, own stratum (CM S-03).

### 3.3 Witness and ReplayCheck (ORIG-S 2.13, 2.17; EV-03, EV-09)
`Witness{pair, scope, input_hash, harness_decl_id, kinds[outcome>exception>side_effect>api], obs_old, obs_new, replay_set[{run_id, version, observation, status}], locus? ("unlocalised" valid), env/build ids, sandbox_policy_id}` (FS s5). Kinds are restricted to the observed channels plus `api`; `control`, `call`, `state`, `data_dependence`, `resource` leave the Witness kind enum (they belong to the optional internal annotation or are non-witness). `masked` on Divergence is removed. Immutable; voidable only by `Supersession`. `ReplayCheck.agree` is defined on `C_obs` observations (5/5 fresh replays per version reproduce the primary observation and the versions still differ), not on `chain_root` and not on locus; whole-chain agreement is reported separately. Interpreter/tracer build mismatch gives replay status `inconclusive` (repeat in a matching environment). Control-sensitive candidates need `k_alt=3` alternate settings with each version's own observation invariant, else `ENV_SENSITIVE_DIFF`. `Divergence` is split into a derived `difference` and an inferred `locus` that records the alignment id and its trust.

### 3.4 Per-input outcome record (new, FS s3)
`o(x)` in {`CONFIRMED_DIFF`, `UNCONFIRMED_DIFF`, `ENV_SENSITIVE_DIFF`, `SAME`, `QUARANTINED`, `LIMIT_ASYMMETRIC`, `NO_RUN(reason)`} with terminal class `returned | raised | exited | crashed(signal) | limit(kind)`. Limits are never witnesses; both-sides-limit gives `NO_RUN`.

### 3.5 Identity and hash chain (ORIG-S s3; EV-13)
Canonical serialisation (ORIG-S 3.1), input identity (3.3) and event identity (3.4) unchanged. **Change:** the chunk hash and `chain_root` exclude run id and `repeat_index` (otherwise `chain_agreement` could never be 1). The run id may still include `repeat_index`. Storage default (FS s8; D5): replay recipe plus hashed event stream (about 300 B/run); full events only for witness runs, a 5% audit sample and escalations; events are regenerated on replay. Per-pair storage and ingest bounds are not frozen here: they are to be set from a P1 measurement (ESA s4; the ORIG-S/ROADMAP 12-60 B/event figures are unmeasured guesses and the 50 MB/pair and 200 GB bounds fail at the ROADMAP default scale).

### 3.6 FormalResult (ORIG-S 2.18; V-04)
`method` in {`bounded_symbolic`, `regression_verification`, `exhaustive_domain`}; `status = equivalent_up_to_bound` requires an explicit `domain` and `bound`. `BOUNDED_EQUIVALENCE_PROVEN` is a formal claim carried by this record, never a `Verdict.value`, never required for any S level.

### 3.7 Capture tiers and completeness (ORIG-S 2.5/2.9; EV-07)
L0 = terminal outcome plus declared side effects plus a changed-region coverage bitmap (branch ids and directions hit); L1 adds call/return; L2 adds branch/line/data events in focus regions; L3 per PRMC. S1 requires tier >= L0 with the bitmap. `InstrumentationCompleteness` remains a record, never a boolean.

## 4. Traceability rule (ORIG-S s8; EV-11, EV-12)

Chains (FS s8): `DIVERGENT_OBSERVABLE` -> Witness -> primary runs, repeats, replays + `ReplayCheck`, `H`, programs, input, environment, sandbox policy. `NO_DIVERGENCE_OBSERVED` -> `SufficiencyRecord` -> run-set Merkle root + per-input rows, reproducibility, completeness, `ChangedRegions`, `ExplorationLog`, `H`. `INSUFFICIENT` -> the records that triggered each blocking condition (including `BuildStatus`; degenerate `level=S0` record allowed). Validator rules T1-T7 of ORIG-S stand with these amendments: T1 checks the Merkle root and per-input rows instead of an inline run list; T2 requires `ReplayCheck` agreement on `C_obs`; T3 `NO_DIVERGENCE_OBSERVED` has `level` in {S1, S2} (S3 only if enabled); T4 recomputing FS s2 from the chain reproduces value and primary code; T5 no superseded record in the chain or the verdict is flagged; T6 no label-namespace record reachable (labels live in K only); T7 runs in a comparison share Input and environment. ImpactSet is optional in the chain ("if present").

## 5. What ORIG-S sections remain as written

s0 principles; s2.1-2.4 (`ProgramVersion`, `ExecutionEnvironment`, `SandboxPolicy` modulo FS s10 I1-I7 fields, `Input`); 2.6 events (one vocabulary: ORIG-S kinds win, CM EV-04); 2.7 `StateObservation` (optional, E); 2.10 `Reproducibility` with the class vocabulary of ORIG-S (`deterministic | outcome_stable_trace_unstable | unstable | unknown`, plus `masked_by_virtualisation`; MATH's `DET/CONTROLLED/UNCONTROLLED` is mapped, not added; EV-08 is not otherwise resolved here); 2.11-2.12 optional/inferred records; 2.14 `ImpactSet`; s4 immutability, s5 versioning, s6 storage (CAS + SQLite), s7 replay (with the replay-status change above), s10 safe-execution metadata (add `policy_below_minimum`, `trace_tampered`), s11 ER diagram (redraw to add the new entities; not rendered here). ORIG-S s12 open issues (value-abstraction depth 3 and 64 B inline limit are guesses; rename-tolerant mapping needed from G; saturation heuristic) remain open.

## 6. As-built vs this schema (for the conformance audit; per `docs/architecture/V7B_IMPLEMENTATION.md`, not independently re-verified)

`sbgv7/records.py` implements content-addressed ids, a hash-chained JSONL log (`DIR/evidence.jsonl`) and `trace(log, verdict_id)`. It stores per run: slot-based id, status, observation id, hit lines. Differences recorded as open items, not resolved: no replay recipe plus hashed event stream (OI-03); flat hash of run ids instead of a Merkle root (OI-04); no `Supersession` or void (OI-05); `ChangedRegions` without confidence/unmodelled (OI-06); strict config exposes a subset of FS s11 (OI-07); `ineligible:identical` compares the source file only, not deps and runtime (OI-08); `evidence_class`/`status` presence on records not verified (OI-22). The red-team review noted `s2_all_channels_instrumented` hard-coded True (OI-01).

## 7. Not done

No schema JSON files exist or were produced; worked examples (ORIG-S s9) were not regenerated; the ER diagram was not redrawn. The evaluation-side entities (`AdjudicationRecord` etc.) are named only; their fields are to be specified when the benchmark work is authorised (**Phase 3, not started**).

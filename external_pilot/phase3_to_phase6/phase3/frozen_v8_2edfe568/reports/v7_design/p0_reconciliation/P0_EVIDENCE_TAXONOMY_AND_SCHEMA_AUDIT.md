# SBG V7 P0: Evidence Taxonomy and Schema Audit

Auditor: independent red-team pass. Scope: the 13 `SBG_V7_*.md` files plus `_sources/_DESIGN_SPINE.md` (short names as in `P0_CROSS_DOCUMENT_CONTRADICTION_MATRIX.md`). Contradiction IDs (V-, S-, EV-, M-, B-, X-) refer to that matrix. Arithmetic marked **[est]** is computed from rates stated in the documents; none was measured.

## 1. Where each of the seven evidence classes is defined, and the gaps

Finding: no V7 document defines the seven-class set (observation / derived / inferred / proof / missing / invalid / uncertain). Four documents define overlapping partial sets under different names. grep for "derived", "missing", "invalid", "uncertain" as class names found none; the words appear only as ordinary prose or field names.

| Class | Closest definition (doc, section) | Where else it is approximated | Gap |
|---|---|---|---|
| Observation | MATH §0: "OBSERVATION" (one of four epistemic classes); SCHEMA §1: RAW layer ("immutable, content-addressed, hash-chained") | COMPETING "Can assert: OBSERVATION"; MATRIX R-10 ACTIVATED | SCHEMA RAW also holds `SourceMapping`, which is computed, not observed (see 2). No field marks a record as observation. |
| Derived | SCHEMA §1: DERIVED layer ("deterministic functions of RAW or other DERIVED") | MATH has no matching class | Conflated with inference: SCHEMA puts `SemanticCorrespondence`, `Witness`/`Divergence`, `ImpactSet`, `DerivedInvariant` in DERIVED although MATH §5.1-5.4/§5.9 labels them INFERENCE (EV-02). |
| Inferred | MATH §0: "INFERENCE"; COMPETING "INFERENCE" | SCHEMA `alignment_trust`, `uncertainty` object | Not a schema concept. Locus, correspondence and impact are heuristics but carry no class tag. |
| Proof | MATH §0 "FORMAL CLAIM"; SCHEMA §2.18 `FormalResult` (`bounded_symbolic`, `regression_verification`) | MATH §8.5 Theorem 3 (exhaustive finite domain); COMPETING "proof" | `FormalResult.method` lacks `exhaustive_domain`, so the only proof MATH allows from the dynamic tier has no record (V-04). `FormalResult` is only sketched. |
| Missing | SCHEMA `blind_spots`, `kinds_dropped`, `truncation` event, `evidence_unavailable` tombstone | MATRIX status UNKNOWN; EP `PARTIAL_INSTRUMENTATION`, `UNOBSERVED_CHANNEL` | Four unrelated mechanisms; no single "absence of evidence" record, and "missing" is not distinguished from "observed absent" (e.g. a branch not taken vs a branch not instrumented). |
| Invalid | SCHEMA `Supersession`; `Reproducibility.class = unstable`; `policy_below_minimum` flag (CONTRACTS B.2) | EP `FLAKY_WITNESS`; MATH `FLAKY_DIVERGENCE` | Invalidation of a record is only a sketch (2.18); no rule says whether dependents of a superseded record become invalid. |
| Uncertain | SCHEMA `uncertainty` object, `alignment_trust`, confidence `nondet_adjusted`; MATH §0 "PROBABILISTIC ESTIMATE" | EP ECE, conformal bounds | MATH treats probabilistic estimate as a class; SCHEMA treats uncertainty as a field on any record. Scale (heuristic score vs calibrated probability) not tagged (MATH says phi is "not a probability"). |

Other taxonomies in the corpus (none maps cleanly to the seven): MATH four epistemic classes; SCHEMA three layers RAW/DERIVED/DECISION; COMPETING tags `[SPINE] [LIT] [HYP-En] [JUDGEMENT]`; EP truth tiers T0-T3 (about truth labels, not evidence); MATRIX/V6 statuses ACTIVATED/NOT_ACTIVATED/UNKNOWN/NONDET; RESEARCH verified / UNVERIFIED / (3p). ROADMAP has no taxonomy.

## 2. Proposed single canonical taxonomy, mapped to schema entities

Rule: every stored record carries `evidence_class` (one of the four primary classes) and an optional `status` (one of the three qualifiers). Primary classes describe how a statement was obtained; qualifiers describe its standing.

| Class | Definition | Entities (SCHEMA names) | Recomputable from RAW alone? |
|---|---|---|---|
| observation | Recorded directly by an instrumented, sandboxed execution or tool; not a function of other records | `ProgramVersion`, `ExecutionRun`, `EventChunk`/events, `InstrumentationCompleteness`, `Reproducibility` runs, `ReplayCheck` | n/a (root) |
| derived | Deterministic function of observations and declared parameters; any party recomputes the same bytes | `StateObservation`/projections, `SufficiencyRecord` counts and levels, `SourceMapping` (currently RAW, should be derived: it is a diff algorithm output), `ChangedRegions` (not yet an entity), the "difference" part of `Divergence`/`Witness` | yes |
| inferred | Heuristic or model-dependent; different valid algorithms may disagree | `SemanticCorrespondence`, divergence `locus` (first-divergence index is an upper bound relative to the alignment, MASTER decision 6), `ImpactSet`, `DerivedInvariant`, region classification, `Verdict` as a policy application over the above | only given the same algorithm and version |
| proof | Established by exhaustive or formal argument over a stated domain, with the bound recorded | `FormalResult` (add `method = exhaustive_domain`, `domain`, `bound`); the only licence for the word "equivalent" (SCHEMA 2.18) | yes, by checker |
| missing (status) | Evidence that should exist for the claim is absent; an explicit record of the hole | `kinds_dropped`, `blind_spots`, `truncation`, unmapped regions, tombstones; build failures (`ProgramVersion.build_status`) | yes |
| invalid (status) | Record exists but may not support any claim | `Supersession`, replay disagreement, `policy_below_minimum`, flaky/unstable class, rejected input | yes |
| uncertain (status) | Carries a quantified or ordinal doubt that the consumer must propagate | `uncertainty` components, `alignment_trust`, `nondet_adjusted` confidence, sampling and conformal bounds; ordinal S-level (an empirically calibrated ordinal, CONTRACTS §15(5)) | yes |

MATH mapping: OBSERVATION -> observation (and derived when a deterministic function); INFERENCE -> inferred; PROBABILISTIC ESTIMATE -> inferred + status uncertain; FORMAL CLAIM -> proof. Verdict mapping (V-01/V-02): `DIVERGENT_OBSERVABLE` is derived-on-observation (replay-confirmed difference) with an inferred locus; `NO_DIVERGENCE_OBSERVED(S)` is derived with status uncertain; `INSUFFICIENT` is status missing or invalid with a reason code; internal-only difference is an annotation of class derived, status uncertain until validated.

## 3. Traceability audit

Question: can every verdict resolve to evidence IDs (T1-T7 in SCHEMA §8 are the validator rules)?

### 3.1 Resolution paths that work

- `DIVERGENT` with a replayed witness: Verdict -> Witness -> ReplayCheck -> ExecutionRun -> EventChunk chain -> ProgramVersion (SCHEMA §9.1 worked example resolves, subject to EV-03: the `agree` rule makes the `nondet_adjusted` path unreachable).
- `NO_DIVERGENCE_OBSERVED`: Verdict -> SufficiencyRecord -> completeness/reproducibility records. The runs themselves are only referenced by a prose placeholder in the §9.2 example (EV-11), so T1 ("every ID in `evidence_chain` exists") cannot be checked for the largest set of records.

### 3.2 Entities or links with no provenance (cannot be traced)

| # | Gap | Impact | Contradiction ID |
|---|---|---|---|
| 1 | No `ChangedRegions` entity; only the strings `scope.changed_region_ids`, `focus_region_ids`. Producer C (CONTRACTS C) outputs `ChangedRegions{old_blocks,new_blocks,kind,confidence}`. | Activation, S-levels, L2 focus capture and anchor selection all depend on an untraceable object. | EV-05 |
| 2 | `ExplorationLog`, `SignatureSketch`, `ModuleManifest`, freeze records, `Budget` have no schema entity. | The input set chosen by A, the budget consumed and the module versions behind a verdict cannot be reproduced. | EV-05 |
| 3 | `SourceMapping` is RAW with optional `lineage`/`vcs_ref`; the diff algorithm and its version are not recorded. | A different diff tool changes changed regions and thus every downstream verdict. | EV-05 |
| 4 | Harness declaration (channel set C, view, normaliser N, float tolerance, floors) is not an entity. | Verdicts are only comparable under the same declaration (MATH §3.5), but the Verdict does not reference one. | V-05, EV-10 |
| 5 | Run-less `INSUFFICIENT` (import_error, unsupported_signature, ambiguous_entry, no_inputs, unsafe_program): evidence is `ProgramVersion.build_status`, which is not an `evidence_chain` role, yet SufficiencyRecord is mandatory for all three values. | A mandatory-record rule that cannot be satisfied for the failure cases V6 abstained on most (BugsInPy UNKNOWN 117 of 200). | EV-12 |
| 6 | Evaluation side has no entities: `AdjudicationRecord`, `BenchmarkPair`, `HoldoutCommitment`, `LeakageAuditReport`, `ClaimLedger`, result records (ROADMAP §2 names some; SCHEMA has only sketches `PredictionRecord`, `GroundTruthLabel`). | A reported headline number cannot be traced to pairs, adjudicators, and a sealed commitment. | EV-05, X-14 |
| 7 | No `Verdict` <-> `GroundTruthLabel` join entity. Labels are deliberately unreachable from T6 (MASTER decision 7), so scoring is done outside the evidence graph. | Correct design, but the scoring step itself is untraced: a custodian-signed scoring record is needed. | EV-05 |
| 8 | Baseline verdicts (B1 plain differential, B2 coverage-guided) have no entity; B1/B2 "no difference found" statements are compared against V7 in H4 but are not stored in the schema. | FAR comparison cannot be audited against stored evidence. | X-05 |
| 9 | `FormalResult`, `PredictionRecord`, `GroundTruthLabel`, `Supersession` exist only as sketches (SCHEMA 2.18). | Proof class and invalid class have no checkable shape. | V-04 |
| 10 | ImpactSet is optional in CONTRACTS H (`absent` allowed) but cited in the §9.1 example chain and ROADMAP makes the module conditional. | Chain shape varies by build; T1 rule needs "if present". | M-03 |
| 11 | `Divergence` locus is an inferred position on an inferred alignment; no field records the alignment id or its confidence at the locus. | A verdict cannot be re-derived by someone using a different alignment. | EV-02 |
| 12 | Hash-chain basis ambiguity: if `run` or `repeat_index` is inside the hashed chunk bytes, `chain_root` can never agree across repeats. | Reproducibility `chain_agreement` would always be 0, so every pair would be classed unstable. | EV-13 |

### 3.3 Traceability verdict

A verdict resolves to evidence IDs end to end only for replayed `DIVERGENT` verdicts. For `NO_DIVERGENCE_OBSERVED` the run set is not machine-checkable (3.1), and for run-less `INSUFFICIENT` the schema rule cannot be met (item 5). At least 12 entities or links lack provenance (3.2); items 1, 4, 5 and 12 block T1/T3 validation as specified and are fixed in RF-2 (matrix header).

## 4. Storage and runtime overhead plausibility

All figures are estimates from documented rates. Source rates: SCHEMA §6 "~12 B compressed" per event, L1 "50-500 events/run"; ROADMAP P0 "<= 60 B/event", P1/budget table "<= 40 B/event"; ROADMAP P4 ">= 200 exec/s ... 4 workers", default "<= 5000 executions"; ROADMAP "evidence bundle per pair <= 50 MB p99"; RISK R33 trigger "100 MB p95"; ROADMAP P8 "peak storage <= 200 GB"; CONTRACTS B ingest "1-5 MB/s per core".

| # | Quantity | Arithmetic **[est]** | Compared with stated bound | Plausible? |
|---|---|---|---|---|
| 1 | SCHEMA headline: 10^6 runs at 1k events, 12 B | 10^6 x 1,000 x 12 B = 12 GB | SCHEMA states ~12 GB | Consistent with its own rate. Uses 1k events/run, above the L1 range of 50-500. |
| 2 | ROADMAP default, one pair, runs | 5,000 execs x 2 versions x k repeats: k=2 -> 20,000; k=3 -> 30,000; k=5 -> 50,000 runs | n/a | The doc's k values differ (2/3/5; M-06). |
| 3 | Events per pair at L1 | 20,000 x 50 = 1.0 M events (low); 50,000 x 500 = 25 M events (high) | n/a | |
| 4 | Bytes per pair at 12 B/event | 12 MB (low) to 300 MB (high) | 50 MB p99 bound; 100 MB p95 risk trigger | Low end fits; high end exceeds both by 3-6x. |
| 5 | Bytes per pair at 40 B/event (ROADMAP's own figure) | 40 MB (low) to 1.0 GB (high) | 50 MB p99 | Fits only at the very bottom; typical use breaks the 50 MB bound unless dedup or sampling is applied. |
| 6 | Bytes per pair at 60 B/event (ROADMAP P0 figure) | 60 MB (low) to 1.5 GB (high) | 50 MB p99 | Exceeds the bound even at the low end. |
| 7 | CONTRACTS scale: 300 inputs x 2 versions x 2 repeats | 1,200 runs; x 50-500 events = 60 k - 600 k events; at 12 B = 0.72-7.2 MB; at 40 B = 2.4-24 MB | 50 MB p99 | Fits comfortably. The plan is plausible only at CONTRACTS scale, not at the ROADMAP default (EV-11 / B-04). |
| 8 | Holdout storage, ROADMAP default, 700 pairs, one seed | 700 x (12 MB - 300 MB) = 8.4 GB - 210 GB; at 40 B: 28 GB - 700 GB | 200 GB cap | Cap holds at the low end only; at the high end 1.05x-3.5x over. |
| 9 | Same with 5 seeds (EP §8) | 5 x row 8 = 42 GB - 1.05 TB (12 B); 140 GB - 3.5 TB (40 B) | 200 GB cap | Cap is exceeded in most of the range unless repeats are deduplicated. |
| 10 | Dedup of repeats | Not specified: SCHEMA §2.5 run id includes `repeat_index`; whether CAS chunks of identical repeats are stored once is unclear (EV-13). | n/a | Unverified; if repeats of deterministic runs were deduplicated the bundle size could fall by up to k-fold, but this is not documented. |
| 11 | Ingest time, one pair at the ROADMAP high end | 25 M events x 200 B (ROADMAP throughput basis) = 5 GB; at 1-5 MB/s per core = 1,000-5,000 s | 60 s budget (CONTRACTS), 60 s-300 s grid (EP) | Not plausible at the high end; even 1 M events x 200 B = 200 MB takes 40-200 s on one core, above the 60 s default budget. |
| 12 | Write-throughput claims against each other | ROADMAP P0 ">= 50k events/s at 200 B" = 10 MB/s; CONTRACTS ingest 1-5 MB/s per core = 5k-25k events/s | | ROADMAP's 10 MB/s needs 2-10 cores of the CONTRACTS rate; the two are only consistent if the 50k figure is multi-core. State which. |
| 13 | Capture CPU at default budget | CONTRACTS B: 1,200 runs x 50 ms = 60 s at L1 (k=2); 90 s at k=3; 150 s at k=5 | 60 s CPU budget; EP counts tracing in V7's CPU (§7) | Capture alone consumes the full 60 s at k=2, leaving none for alignment, escalation or replay (B-02). |
| 14 | Tracing overhead multipliers | CONTRACTS L1 1.2-3x, L2 3-10x, L3 20-50x; ROADMAP call-level <= 5x, line <= 25x median (<= 60x p95); GATES G1 median <= 20x | | The bands overlap but disagree by up to 4x at line level; none measured (M-07b). |
| 15 | Holdout CPU | Protocol size 700 pairs (H-R 300 + H-M 400) x 300 s x 5 seeds = 1.05 M CPU-s = 292 CPU-h per arm (V7 alone); with B1, B2 added about 875 CPU-h | GATES G5: <= 150 CPU-h; ROADMAP P8: <= 12 h on 16 cores = 192 core-h | Stated bounds are low by about 1.5x-6x (B-03). |

Plausibility summary: storage and runtime claims hold at the CONTRACTS scale (about 1,200 runs per pair) and fail at the ROADMAP default (5,000 executions per pair) for the 50 MB per-pair bound, the 200 GB cap, the ingest rate and the 150 CPU-h holdout. The per-run event count (50-500) is the single largest uncertainty; an L1 measurement in P1 (K2) must fix it before any bound is frozen.

## 5. Recommended changes (carried to P0 reconciled files)

1. Add `evidence_class` and `status` to the common header (RF-2); remap the SCHEMA layers to the section 2 table.
2. Add entities: `ChangedRegions`, `ExplorationLog`, `HarnessDeclaration`, `RunSetRoot`, `BuildStatus` evidence role, `AdjudicationRecord`, `HoldoutCommitment`, `ScoringRecord` (custodian-signed).
3. Make the chain hash exclude `run` and `repeat_index`; define replay agreement at locus plus outcome (EV-03, EV-13).
4. Add `FormalResult.method = exhaustive_domain`.
5. Set the per-pair storage and ingest bounds from a P1 measurement, not from the 12-40 B/event guesses; state whether repeats are deduplicated.

## 6. Not verified

- No schema JSON was validated; the worked examples in SCHEMA §9 were read, not executed.
- CAS deduplication behaviour is unspecified in the documents and was not assumed.
- Events per run (50-500) and bytes per event (12/40/60 B) are the documents' own figures, unmeasured; all section 4 results inherit that uncertainty.

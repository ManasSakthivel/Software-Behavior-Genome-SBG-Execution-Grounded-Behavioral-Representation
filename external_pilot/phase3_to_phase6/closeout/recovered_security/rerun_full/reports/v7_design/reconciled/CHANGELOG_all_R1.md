Reconciled version R1 of the V7 design set (changelog for all R1 files); originals preserved at reports/v7_design/_original_archive/

# CHANGELOG, all R1 documents

Scope: every change made when producing the R1 set. "CM" = row ID of `p0_reconciliation/P0_CROSS_DOCUMENT_CONTRADICTION_MATRIX.md`; "D" = `P0_BINDING_DECISIONS.md`; "FS" = `reports/final/V7B_FROZEN_SPEC.md`; "O" = open decision of the P0 final reconciliation report; "RT" = red-team review (`reports/final/INDEPENDENT_RED_TEAM_REVIEW.md`); "OI" = open item for the conformance audit (list in `reports/phase2/PHASE_2_RECONCILIATION_INDEX.md`). A change with no CM ID cites its real source instead. Original files are untouched. Changes carry IDs CL-xxx-nn (xxx = document code).

Document codes: SCH schema, ROA roadmap, RSK risk register, MPL master plan, FAD final decision, CMP competing architectures, F2R failure-to-requirement matrix, MOD module contracts, IDX index.

## 1. New R1 documents written in this pass

| ID | Document | Change | Reason | CM / source |
|---|---|---|---|---|
| CL-SCH-01 | `SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md` | `evidence_class` {observation, derived, inferred, proof} and `status` {missing, invalid, uncertain} added to the common header; ORIG-S layers kept as storage layers | no document defined the seven evidence classes | EV-01, EV-02; D4 |
| CL-SCH-02 | schema R1 | `SourceMapping` moved from RAW to class derived; diff algorithm and version recorded | it is a diff-algorithm output, not an observation | EV-05; ESA s2 |
| CL-SCH-03 | schema R1 | Verdict value enum fixed to three values with precedence; `ineligible:identical` is not a Verdict; prohibited outcome strings rejected by validator | one verdict set | V-01, V-02, V-03; D1 |
| CL-SCH-04 | schema R1 | Reason codes replaced by the closed 18-code enum of FS s7; retired `internal_only_difference`, `observed_same_at_Sx`, `LOW_STATE_COVERAGE`, `TIMEOUT`; `INSUFFICIENT` stores primary (rank B1..B9) and secondary codes | three vocabularies | V-06; FS s7 |
| CL-SCH-05 | schema R1 | `SufficiencyRecord` reduced to one definition (conjunction of floors on F1-F4); removed alternative S0-S3 texts, saturation as a level input, scalar score; added `activation_status`, `r_empty`, Merkle root, quarantined count; S0 only inside INSUFFICIENT; S3 `s3_enabled=false` | four incompatible definitions | S-01, S-02, S-03, S-04; D3 |
| CL-SCH-06 | schema R1 | Witness kinds restricted to outcome/exception/side_effect/api; `masked` removed; `Divergence` split into derived difference and inferred locus with alignment id and trust | internal-only is not a verdict; locus is inferred | V-02, EV-02, EV-09; D2 |
| CL-SCH-07 | schema R1 | `ReplayCheck.agree` defined on `C_obs` (5/5 fresh replays, `r_det=3`, `k_alt=3`); build mismatch gives `inconclusive`; `nondet_adjusted` DIVERGENT path removed | trace-unstable witnesses were unreachable | EV-03, M-06; FS s5 |
| CL-SCH-08 | schema R1 | Chunk hash and `chain_root` exclude run id and `repeat_index`; default storage = replay recipe plus hashed event stream (full events for witnesses, 5% audit sample, escalations); per-pair bounds left to measurement | chain agreement unreachable; 10-50x storage overrun | EV-13, B-04; D5; RT Q7 |
| CL-SCH-09 | schema R1 | New entities: `HarnessDeclaration`, `ChangedRegions`, `SignatureSketch`, `ExplorationLog`, `RunSetRoot`, `ModuleManifest`/freeze records, `BuildStatus` role, `Supersession` shape, evaluation entities (named only) | missing provenance for activation, input set, harness choices, run-less INSUFFICIENT | EV-05, V-05, EV-10, EV-11, EV-12; D5 |
| CL-SCH-10 | schema R1 | `FormalResult.method = exhaustive_domain`; `BOUNDED_EQUIVALENCE_PROVEN` kept out of `Verdict.value` | proof class had no record | V-04; D1 |
| CL-SCH-11 | schema R1 | Capture tiers rewritten (L0 carries a changed-region coverage bitmap) | L1 had no branch data needed for S2/directed exploration | EV-07 |
| CL-SCH-12 | schema R1 | Traceability T1-T7 amended (Merkle root, `C_obs` replay, levels, "if present" for ImpactSet) | chain not checkable for NO_DIVERGENCE_OBSERVED | EV-11, M-03 |
| CL-SCH-13 | schema R1 | Section 6 lists as-built differences as open items instead of deciding them | frozen spec vs as-built disagreements are for the audit | OI-03..OI-08, OI-22 |
| CL-ROA-01 | `SBG_V7_IMPLEMENTATION_ROADMAP.R1.md` | Programme phases defined: Phase 1 done, Phase 2 reconciliation/audit, Phase 3 gated infrastructure and benchmark (not started, not authorised); original P0-P9 kept as workstream labels with disposition | three phase vocabularies; user brief | FS s13 |
| CL-ROA-02 | roadmap R1 | Gates G0-G8 only; K1-K5 per FS s12 with fixed STOP/PIVOT/DOWNGRADE responses; no K3+ work before K2 passes | G0-G9 vs G0-G8; K outcomes disagreed | G-01, K-01, K-02, K-03, K-04; D9 |
| CL-ROA-03 | roadmap R1 | Original budget (60 s wall x 4 cores, 5000 executions) and performance table retired; budget unit CPU-seconds incl. overhead; grid 10/60/300 | different units; arithmetic inconsistencies | B-01, B-02, B-03, B-04; D7 |
| CL-ROA-04 | roadmap R1 | Four-value verdict list and original S0-S3 description retired in favour of the schema R1 | one verdict set | V-01, S-01 |
| CL-ROA-05 | roadmap R1 | P7 must add truth harness / H-M / H-P work; effort NOT re-estimated (recorded as unreconciled) | effort omitted protocol workload; sum error | X-01, X-14, E-01, E-02 |
| CL-ROA-06 | roadmap R1 | K1 development-data statement recorded as "NOT MET on development data, not an evaluation as defined"; STOP trigger left as open programme decision | spec evaluates K1 on the Linux runner; Phase 1 reports say "NOT MET" | OI-21 |
| CL-RSK-01 | `SBG_V7_RISK_REGISTER.R1.md` | R01-R38 IDs kept; R1 status column added; gate references re-mapped to G0-G8 (G9 becomes G-J); R04 re-scoped to annotation; R01/R03/R11/R26/R31/R35/R37 elevated or marked materialised from Phase 1 evidence | verdict set and gate numbering changed; Phase 1 findings | G-01, G-03, V-02; D2, D9; RT |
| CL-RSK-02 | risk register R1 | Added R39-R54 (sufficiency value, weak floors, false assurance on real fixes, abstention by engine gaps, isolation below minimum, untested Linux/Docker, capture bypass, partial control alternation, no independent benchmark, prior art not run, legacy-claim conflation, baseline fairness, document drift, accidental workload execution, repo size, input representation limits) | red team, isolation audit, power analysis, Phase 1 closure | RT; ISO; POWER; PHASE_1_FINAL_CLOSURE_REPORT |
| CL-RSK-03 | risk register R1 | Stop/cut-back conditions rewritten to D9/FS s12 (K1 STOP; K2 twice; V7-B' no better than B1; S4, S5, S6 kept; K3/K4 PIVOT; K5 DOWNGRADE) | RISK, ROADMAP and FINAL disagreed | K-01, K-02 |
| CL-MPL-01 | `SBG_V7_ARCHITECTURE_MASTER_PLAN.R1.md` | Eleven decisions dispositioned: 1 and 3 replaced; 2, 4-11 kept (4 made concrete as I1-I7); four more added (replay protocol, evidence classes, recipe storage, API-break probe) | four-value verdict; E core vs optional | V-01, V-02, V-03, M-01, M-02, M-04; D1-D5, D10 |
| CL-MPL-02 | master plan R1 | Architecture text redrawn with E optional, F absent, replay through B; as-built mapping table added; original s5 "known inconsistencies" given a status | stale diagram and statements | M-02, M-03 |
| CL-FAD-01 | `SBG_V7_FINAL_ARCHITECTURE_DECISION.R1.md` | Primary architecture V7-B; V7-A a gated pilot not authorised; full V7 not justified; four-way verdict and "internal-state witnesses" withdrawn | D6; readiness report | V-01, V-02, M-02; D6 |
| CL-FAD-02 | final decision R1 | Minimal novelty restated from `RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md` (C1-C4 partially novel, C5 unsupported, no "first") | defensible claim after Phase 1 | RT s1-2; novelty assessment |
| CL-FAD-03 | final decision R1 | Success evidence defers to GATES R1 C; K5 floor replaces ">= ~150 divergent, >= 40 projects"; K5 outcome DOWNGRADE not "stop entirely" | numbers and responses disagreed | X-02, X-10, K-01 |
| CL-FAD-04 | final decision R1 | GO/REVISE/NO-GO restated: P0 decision GO_P1 scoped; readiness verdict B; Phase 3 recommendation only | reconcile P0 and Phase 1 outcomes | FS s13; readiness report |
| CL-CMP-01 | `SBG_V7_COMPETING_ARCHITECTURES.R1.md` | Selected composite replaced by V7-B; collapse rule made concrete (V7-B', then STOP); roles of (a), (b), (d), (e), (f) re-stated; scalar-sufficiency challenge withdrawn; bounded-equivalence kept only as formal claim | D2, D5, D6, D9 | M-02, X-05, K-02, S-01, V-04; D1-D9 |
| CL-F2R-01 | `SBG_V7_FAILURE_TO_REQUIREMENT_MATRIX.R1.md` | R-03 and R-19 rewritten to the three verdicts (no EQUIVALENT-class requirement); "equivalent-within-budget" deleted | requirement forced an equivalence class | V-03 |
| CL-F2R-02 | F2R R1 | R-12, R-13, R-14 re-scoped (E/pilot; F removed); R-13 and R-30 flagged as previously untraced; trace table with design coverage and as-built status added | requirements untraced into design | R-A, M-01, M-02 |
| CL-F2R-03 | F2R R1 | Numeric corrections: CONV GBM 0.9705 (0.972 decision-report), "V6 ~0.52" pooled LOFO vs GBM 0.582, v8 test 26 programs / 22 evaluated, 76% is of real fixes (42/55) with 71.5% overall, 4 UNKNOWN unexplained | file values differ from quoted values | N-01, N-02, N-03 |
| CL-MOD-01 | `SBG_V7_MODULE_CONTRACTS.R1.md` | Reduced to pointer to `P0_RECONCILED_MODULE_CONTRACTS.md` plus deltas: schema reference now R1, open items C-O1..C-O4 status, module-to-code map, as-built gaps listed as open items | authoritative contracts already reconciled in P0 | O13; PRMC s4-s5 |
| CL-IDX-01 | `reports/phase2/PHASE_2_RECONCILIATION_INDEX.md` | New: authoritative list, supersession, unreconciled list, open items for the conformance audit | user brief; O13 | O13 |
| CL-ALL-01 | every R1 file | First line standardised: "Reconciled version R1 of <original>; original preserved at reports/v7_design/_original_archive/" | brief | n/a |

## 2. Previously logged edits to the four existing drafts (carried from `reports/final/P0_FINAL_RECONCILIATION_REPORT.md` s3; not re-verified here)

The per-draft changelogs named inside the drafts (`CHANGELOG_protocol_gates.md`, `CHANGELOG_math_schema.md`) and the internal change IDs of the GATES R1 draft (for example "CHANGELOG U-5") do not exist as files and could not be recovered; they are listed as unreconciled in the Index. The only recoverable record is the P0 report table. CM IDs below are those cited in that report's resolution matrix and are best-effort.

| ID | File | Change | Reason | CM / source |
|---|---|---|---|---|
| CL-P0-F1 | EP R1 (s1, s3.5), GATES R1 (rows 7, 8) | Default `exc_message=exact_normalised`; stderr not observed; row 7 criteria swapped | D1 includes message class | V-05, EV-10 |
| CL-P0-F2 | EP R1 s9 | Introduced non-termination at 2x limit changed from witness to `INSUFFICIENT(resource_limit)`; separate stratum; 10 s CPU marked provisional | FS s3: a harness limit is never a witness | O4 |
| CL-P0-F3 | GATES R1 (A preamble, row 0) | Row 0 split into (a) byte-identical: `ineligible:identical`, no verdict; (b) normalisation-identical: NDO(>=S2) with `r_empty` | empty/identical region undefined | S-03 |
| CL-P0-F4 | MATH R1 1.2, 5.8, 0.1.6(i) | Signature handling cites FS API-break probe; replay agreement on `C_obs`, locus never voids a witness | locus optional and inferred | EV-03; O1 |
| CL-P0-F5 | MATH R1 6.1, 8.0, 8.1, 5.5, 8.1b, 6.4 | `UNCHANGED` -> `ineligible:identical`; `r_empty` added; per-input outcome values aligned; normaliser aligned; `none` annotation; saturation descriptive | alignment to FS | S-03, V-01, V-06 |

## 3. Not changed in this pass

The original `SBG_V7_*.md` files, `_original_archive/`, the four existing R1 drafts (EP, MATH, GATES, RESEARCH errata), `sbgv7/`, `tests/`, `results/`, V5/V6 files. Known staleness left in the existing drafts (for the Index): EP R1 and MATH R1 still say "No V7 code exists / nothing has been run" (true at P0, false after Phase 1); MATH R1 cites `SBG_V7_COMPETING_ARCHITECTURES.md` and `_DESIGN_SPINE.md` (now `COMPETING_ARCHITECTURES.R1.md`; the spine stays in `_sources/`).

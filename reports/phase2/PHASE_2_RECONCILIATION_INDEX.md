# Phase 2 Reconciliation Index (V7-B documents)

Branch research/v7b-final-validation. Phase 2 boundary: documentation only. Not touched: `sbgv7/`, `tests/`, `results/`, V5/V6 files, `reports/v7_design/_original_archive/`, the original `reports/v7_design/SBG_V7_*.md`. Phase 3 (Linux/Docker isolation, execution of external repositories, independent benchmark collection) is **Phase 3, not started** and is not authorised by anything here. This index claims no equivalence, detection rate or correctness of any pair; all thresholds remain UNVALIDATED defaults.

## 1. Authority order (when documents disagree)

1. `reports/final/V7B_FROZEN_SPEC.md` (frozen spec, "FS")
2. `reports/v7_design/p0_reconciliation/P0_BINDING_DECISIONS.md` (D1-D11)
3. `reports/v7_design/p0_reconciliation/P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md` (SPEC), where FS is silent
4. The R1 set in `reports/v7_design/reconciled/` and the P0 companion documents named in section 2
5. As-built code and `docs/architecture/V7B_IMPLEMENTATION.md` describe what exists; they do not define what is required. A disagreement between 1-4 and the as-built system is an open item (section 4), not a decision.

## 2. Authoritative documents

| Topic | Authoritative document | Notes |
|---|---|---|
| Verdicts, sufficiency, witness, reason codes, gates K1-K5, config defaults, isolation | `reports/final/V7B_FROZEN_SPEC.md` | P0 decision GO_P1 (scoped) |
| Binding decisions | `p0_reconciliation/P0_BINDING_DECISIONS.md` | D1-D11 |
| Full verdict/sufficiency semantics, proofs | `p0_reconciliation/P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md` | FS is the compact authority |
| Module contracts A-L | `p0_reconciliation/P0_RECONCILED_MODULE_CONTRACTS.md` | via `reconciled/SBG_V7_MODULE_CONTRACTS.R1.md` |
| Evidence schema | `reconciled/SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md` | with `P0_EVIDENCE_TAXONOMY_AND_SCHEMA_AUDIT.md` for the gap list |
| Architecture and decision | `reconciled/SBG_V7_ARCHITECTURE_MASTER_PLAN.R1.md`, `SBG_V7_FINAL_ARCHITECTURE_DECISION.R1.md`, `SBG_V7_COMPETING_ARCHITECTURES.R1.md` | V7-B primary |
| Requirements | `reconciled/SBG_V7_FAILURE_TO_REQUIREMENT_MATRIX.R1.md` | no EQUIVALENT-class requirement |
| Roadmap and phases | `reconciled/SBG_V7_IMPLEMENTATION_ROADMAP.R1.md` | Phase 1 done, Phase 2 in progress, Phase 3 not started |
| Risks | `reconciled/SBG_V7_RISK_REGISTER.R1.md` | R01-R38 kept, R39-R54 added |
| Experimental protocol, statistics | `reconciled/SBG_V7_EXPERIMENTAL_PROTOCOL.R1.md` (draft R1) | see unreconciled U3 |
| Mathematical specification | `reconciled/SBG_V7_MATHEMATICAL_SPECIFICATION.R1.md` (draft R1) | see U3 |
| Validation matrix and gates G0-G8 | `reconciled/SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.R1.md` (draft R1) | K table B.0 agrees with FS s12 |
| Literature and novelty | `p0_reconciliation/P0_LITERATURE_VERIFICATION.md`, `research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md`; `reconciled/SBG_V7_RESEARCH_AND_NOVELTY_REVIEW.R1.md` is errata only | no "first" claims |
| Power and benchmark sizing | `p0_reconciliation/P0_BENCHMARK_AND_POWER_ANALYSIS.md` | simulations under assumed discordance/ICC; re-run before sealing |
| Internal-only truth (pilot only) | `p0_reconciliation/P0_INTERNAL_ONLY_GROUND_TRUTH_PROTOCOL.md` | applies to the optional V7-A pilot only |
| Isolation facts | `p0_reconciliation/P0_EXECUTION_ISOLATION_VERIFICATION.md`, `research/security/EXECUTION_ISOLATION_AUDIT.md` | macOS only |
| Contradiction audit record | `p0_reconciliation/P0_CROSS_DOCUMENT_CONTRADICTION_MATRIX.md` (65 rows) | CM IDs cited by the changelog |
| Reconciliation record | `reports/final/P0_FINAL_RECONCILIATION_REPORT.md`; `reconciled/CHANGELOG_all_R1.md` | |
| Independent review, readiness, closure, claims | `reports/final/INDEPENDENT_RED_TEAM_REVIEW.md`, `FINAL_RESEARCH_READINESS_REPORT.md` (verdict B), `PHASE_1_FINAL_CLOSURE_REPORT.md`, `FINAL_CLAIMS_AND_EVIDENCE_MATRIX.md` | permitted wording is in the claims matrix |
| As-built description | `docs/architecture/V7B_IMPLEMENTATION.md` | descriptive only |
| Conformance audit | `reports/phase2/PHASE_2_SPEC_CONFORMANCE_AUDIT.md` | written separately and concurrently; its content is not summarised here |

## 3. Supersession

| Original (historical, preserved in `_original_archive/`) | Superseded by | Superseded in what respect |
|---|---|---|
| `SBG_V7_ARCHITECTURE_MASTER_PLAN.md` | `.R1` | four-value verdict, E core, 11 decisions |
| `SBG_V7_FINAL_ARCHITECTURE_DECISION.md` | `.R1` | four-way verdict, internal-state witnesses, success numbers, stop rule |
| `SBG_V7_COMPETING_ARCHITECTURES.md` | `.R1` | selected composite, collapse rule |
| `SBG_V7_DATA_AND_EVIDENCE_SCHEMA.md` | `.R1` | verdict/sufficiency/witness/chain records, reason codes, evidence classes; unchanged sections stay as written in the original and are cited by the R1 |
| `SBG_V7_IMPLEMENTATION_ROADMAP.md` | `.R1` | gates G0-G9, K outcomes, budget unit, verdict list, phases |
| `SBG_V7_RISK_REGISTER.md` | `.R1` | gate references, stop conditions; original rows retained by ID |
| `SBG_V7_FAILURE_TO_REQUIREMENT_MATRIX.md` | `.R1` | requirements R-03, R-19 and re-scoped R-12..R-14; F-01..F-28 facts unchanged (kept in the original) |
| `SBG_V7_MODULE_CONTRACTS.md` | `p0_reconciliation/P0_RECONCILED_MODULE_CONTRACTS.md` (+ `.R1` pointer) | entire |
| `SBG_V7_EXPERIMENTAL_PROTOCOL.md`, `..MATHEMATICAL_SPECIFICATION.md`, `..VALIDATION_AND_ACCEPTANCE_GATES.md`, `..RESEARCH_AND_NOVELTY_REVIEW.md` | existing `.R1` drafts | as logged in the P0 report s3 |
| `SBG_V7_REPO_INVENTORY.md`, `_sources/_DESIGN_SPINE.md` | not superseded | see U4, U5 |

Supersession means "if they disagree, use the R1/authority". The original files are not deleted or edited.

## 4. Open items for the conformance audit (frozen spec vs as-built; recorded, not chosen)

Sources: `docs/architecture/V7B_IMPLEMENTATION.md` "Not implemented", `INDEPENDENT_RED_TEAM_REVIEW.md`, and my own reading of `sbgv7/config.py` and `sbgv7/decide.py` for this index (not a conformance audit). Each is a candidate for the audit to confirm, refute or classify; none is a ruling.

| ID | Frozen-spec requirement | As-built (as described by the cited source) |
|---|---|---|
| OI-01 | S2 needs all declared channels instrumented (FS s6) | `s2_all_channels_instrumented` is a hard-coded `True` in `decide.py` (red team M-2; seen in `decide.py`) |
| OI-02 | F4 input diversity/budget is a named factor (FS s6) but S1/S2 floors contain no input-count/diversity floor | S2 reachable from 2 inputs (red team). Spec-internal gap; floors change only through the development split |
| OI-03 | Store replay recipe + hashed event stream, about 300 B/run (FS s8, D5) | per run: slot-based id, status, observation id, hit lines; no hashed event stream |
| OI-04 | Run-set Merkle root (FS s6, s8) | flat hash of run ids |
| OI-05 | Witness voidable by `Supersession` (FS s2, s5) | no Supersession/void |
| OI-06 | Reason codes `ambiguous_entry`, `unmodelled_change`, `unsafe_program`, `blind_spot_dominant`, `alignment_failed` (FS s7); `ChangedRegions{kind, confidence, unmodelled}` (FS s9) | never produced (`unsafe_program` only via trace-tamper flag; `alignment_failed` only on parse failure); no ChangedRegions record |
| OI-07 | Config fields of FS s11 (claims/fast CPU split, `max_events_L1`, `s3_plateau_window`, `static_match_f1_trigger`, `witness_outside_R_diag`, budget grid, seeds, `normaliser_id`, `capture_tier`, `stderr`) | `config.py` SCHEMA exposes `c_obs, float_tol, ordered_mapping, exc_message, api_break_probe, r_det, r_replay, k_alt, s2_branch_floor, s3_enabled, cpu_seconds, per_run{cpu_s, wall_s, rss_mib}`; defaults seen match FS for those |
| OI-08 | `ineligible:identical` requires src, deps and runtime byte-identical (FS s2) | check covers the source file only |
| OI-09 | Both-sides-limit input is `NO_RUN`; B6 is "exactly one side limited"; B8 covers no usable input (FS s2-s3) | `decide.py` maps `NO_RUN` and `LIMIT_ASYMMETRIC` both to `resource_limit` |
| OI-10 | B5: quarantined input that hit or may have hit a changed unit (FS s2) | any quarantined input blocks (never inspected for "may have hit") |
| OI-11 | `r_empty` is its own stratum (FS s6) | recorded, not stratified |
| OI-12 | Control alternation virtualises RNG, clock, entropy, uuid (FS s5) | virtualises `random.seed` and `time`/`time_ns` only |
| OI-13 | Build/tracer mismatch makes a replay `inconclusive` (FS s5) | absent |
| OI-14 | Isolation I1-I7; macOS records flagged `policy_below_minimum`; third-party repos only in Linux containers (FS s10) | macOS `sandbox-exec` child process only; every record `policy_below_minimum=true`; `RLIMIT_AS`/`NPROC` not enforced; reads unconfined; `setsid` escape untested; no Linux path. Completion is Phase 3, not started |
| OI-15 | Entry lifting, declared rename, `ambiguous_entry`, ungenerable types -> `unsupported_signature` (FS s5) | entry must be a top-level function; no lifting/renames; inputs are user-supplied JSON values (no tuples/sets/objects) |
| OI-16 | Budget exhaustion blocks only per B9 (`budget_exhausted_s0`) | stopping at budget with unrun inputs but changed lines covered still yields NDO; stop reason recorded, not gating (red team Mo-2). May be spec-consistent; audit to classify |
| OI-17 | S2 branch/direction coverage over statically reachable directions (FS s6) | all directions treated as reachable (conservative denominator); counts POP_JUMP_IF_*, FOR_ITER, SEND only |
| OI-18 | Tier >= L0 with changed-region coverage bitmap (FS s6) | hit lines per run, no bitmap structure described |
| OI-19 | n/a (documentation drift) | test counts differ across reports (74 passed/1 skipped in red team; 75 passed/1 skipped in readiness report); isolation audit quotes stale "11 passed"; B3 CPU 1407 vs 1424 s |
| OI-20 | Tracing outside user-code reach with tamper detection (I4); declared stdout channel | tamper detection is a post-run check of monitoring state; `os.write(1)` and subprocess output bypass stdout capture |
| OI-21 | K1 is evaluated at G1 exit on the isolation runner; fail STOP (FS s12) | Phase 1 reports state "K1 NOT MET" on development data (74 runnable real pairs; 1 true project plus 44 extracted units on synthetic inputs; QuixBugs counted as one project). Whether that triggers STOP is a programme decision; not a code question |
| OI-22 | Every record carries `evidence_class` and optional `status` (FS s8) | not verified for `records.py` |

## 5. Still unreconciled

| ID | Item |
|---|---|
| U1 | Effort and calendar: the original 51 engineer-weeks/32 weeks omit the truth harness, H-M authoring and H-P and contain a summing error (CM E-01, E-02); no re-estimate exists |
| U2 | K1 development-data status vs the spec's evaluation point (OI-21): needs a programme decision, not a document edit |
| U3 | Existing drafts (EP R1, MATH R1, GATES R1): still say "No V7 code exists"/nothing run (stale after Phase 1); point to non-existent `CHANGELOG_protocol_gates.md`, `CHANGELOG_math_schema.md` and internal change IDs (for example "CHANGELOG U-5"); MATH R1 cites `SBG_V7_COMPETING_ARCHITECTURES.md` and `_DESIGN_SPINE.md`; EP s3.2, 4, 5, 6 and the 14-row validation matrix were not checked line by line in P0 and not here. Not edited in Phase 2 (outside the requested writes) |
| U4 | `SBG_V7_REPO_INVENTORY.md` has no R1; its row on the existing runner understates the isolation rebuild (CM M-08) |
| U5 | `_sources/_DESIGN_SPINE.md` and the two raw research passes are unreconciled historical inputs |
| U6 | Open decisions O9 (K2 thresholds 70%/35% carried, unvalidated), O10 (G4 fail-fast S3 0.20 vs cap 0.10; moot while `s3_enabled=false`), O11 (EP planning 80/320 vs K5 floor 60/250), O12 (H10 margin +0.03 vs +0.05, J off), O5 (per-run limits provisional) remain as in the P0 report |
| U7 | Every numeric threshold is an UNVALIDATED default; calibration claims (miss-rate caps S1 0.35, S2 0.20, S3 0.10, ECE 0.05) untested |
| U8 | CM rows whose resolution lives only in EP/GATES drafts (for example X-04..X-14, B-03, K-02, G-02) were not re-verified in this pass |
| U9 | Unrendered/unproduced artefacts: mermaid and ER diagrams, schema JSON files, regenerated worked examples; evaluation-side entities named but not specified |
| U10 | Literature: absence ("found none") claims rest mostly on abstracts (158 rows: 7 full text, 89 abstract, 62 metadata); DOIs marked (3p) unusable for formal citation until rechecked |
| U11 | Dependent Phase 3 items, all **Phase 3, not started**: Linux/container isolation (I1-I7), feasibility spike (about 30 projects), K1/K2/K3/K4/K5, external repository execution, independent benchmark and adjudication, published-tool baselines, explorer, V7-A pilot |

- Added after MB acceptance: `LOCAL_EXPERIMENT_RERUN_MATRIX.md` (plan only; no experiment run), `MB_SECOND_STAGE_REVIEW.md`, `FINAL_SPECIFICATION_DECISIONS.md` ratifications (Decisions A and B).

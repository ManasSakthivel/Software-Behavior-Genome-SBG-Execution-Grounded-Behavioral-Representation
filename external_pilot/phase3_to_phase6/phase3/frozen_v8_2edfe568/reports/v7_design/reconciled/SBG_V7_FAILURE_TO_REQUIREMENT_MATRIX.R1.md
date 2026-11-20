Reconciled version R1 of SBG_V7_FAILURE_TO_REQUIREMENT_MATRIX.md; original preserved at reports/v7_design/_original_archive/

# SBG V7: Failure-to-Requirement Matrix, R1

Authority: `reports/final/V7B_FROZEN_SPEC.md` > `P0_BINDING_DECISIONS.md`. This R1 resolves CM V-03 (no requirement may demand an EQUIVALENT-class outcome), R-A (requirements were not traced into the technical documents), N-01..N-03 (numeric corrections) and the V7-B scoping of requirements.

## 1. Findings F-01..F-28 (facts)

The 28 findings of the original section 1 are **unchanged as facts** (V5/V6 evidence read from the cited files; not re-run). The original table is preserved in the archive; it is not repeated. Numeric corrections applied (CM N-01..N-03):

| Original statement | R1 statement | CM |
|---|---|---|
| F-05 "CONV GBM 0.972" | 0.9705 program-grouped (`artifacts/v6/audit/LEAKAGE_AUDIT.json`); 0.972 is the decision-report rounding. Leave-mutation-types-out 0.7425 (quote 0.742) | N-01 |
| F-15 / spine "V6 alone ~0.52" | pooled LOFO about 0.52 for every candidate; V6 GBM 0.860 -> 0.582 under type holdout (file value 0.582) | N-01 |
| F-12 "v8 test (22-26 programs)" | 26 programs in the benchmark, 22 evaluated (4 programs / 163 pairs excluded a priori) | N-02 |
| F-08 "76% abstention" | 76% is of real fixes (positives), 42 of 55; overall 71.5%; listed BugsInPy UNKNOWN causes (60 + 49 + 4) sum to 113 against 117 UNKNOWN, so 4 are unexplained | N-03 |

## 2. Requirements R-01..R-31 re-expressed for V7-B (no EQUIVALENT-class requirement)

"Design coverage" = where the requirement lives in the reconciled set. "As-built" is taken from `docs/architecture/V7B_IMPLEMENTATION.md` and the Phase 1 reports and is **not independently verified here**; the conformance audit is authoritative. "Phase 3" = **Phase 3, not started**. Thresholds in the original acceptance column were design targets, not results; where a threshold is carried by the gates it is cited, not restated.

| ID | R1 statement (V7-B) | Design coverage | As-built (per V7B_IMPLEMENTATION.md) | Status |
|---|---|---|---|---|
| R-01 | Changed-region activation is recorded and floors the verdict: every changed unit hit (S1 floor F3); coverage-directed exploration to raise it is optional extension A | FS s6, s9 | Activation by `changed_lines` x executable lines; no explorer | Covered (activation); explorer Phase 3, not started; the 95% original target is not a V7-B gate (activation is gated by K2/K3) |
| R-02 | Signature-aware driver synthesis; unsupported cases are `INSUFFICIENT(unsupported_signature)`, never an invented default | FS s5 | User-supplied JSON inputs only; entry-lifting and declared renames absent | Contradicted by scope: input synthesis not built (OI-15); Phase 3, not started |
| R-03 | **Rewritten.** Each no-output-diff changed pair ends in {`DIVERGENT_OBSERVABLE` found, `NO_DIVERGENCE_OBSERVED(S)` with the explored-input statement, `INSUFFICIENT(code)`}. The original class "equivalent-within-budget" is deleted | FS s2; CM V-03; D1 | Verdict set implemented | Covered (rewritten) |
| R-04 | Return value, exception (type + normalised message) and declared side effects are first-class observations tagged by channel | FS s4 | Implemented (return, exception, stdout, sandbox-temp files, argument post-state, globals written, API break) | Covered; return-blind regression set not separately verified |
| R-05 | Type-tagged canonical comparison, float tolerance a declared identity, repr never called | FS s4 | Implemented (type tag identity, binary64-exact, mappings/sets unordered, depth 3, `lossy` blocks S2) | Covered |
| R-06 | Determinism: `r_det=3` repeats, quarantine (B5), `k_alt=3` alternate control settings | FS s5; B5 | Implemented; `k_alt` virtualises only `random.seed` and `time` (OI-12); quarantine conservative (OI-10) | Covered with gaps |
| R-07 | Per-run process isolation, hard timeout, no run can drop other pairs | FS s10 (I1-I7) | Child per run; timeouts are limits; macOS only; RLIMIT_AS/NPROC not enforced | Partially covered; Linux path Phase 3, not started (OI-14) |
| R-08 | Static context produced without execution | FS s9 (C) | Minimal (`changed_lines`); no `ChangedRegions` record with confidence/unmodelled | Partially covered (OI-06) |
| R-09 | Edit-size covariate/shortcut probes on any learned or benchmarked claim; reversed-edit-size band applies only to the scorer-shortcut probe | EP R1; CM X-09 | No learned scorer in V7-B | Covered as protocol requirement; evaluation Phase 3, not started |
| R-10 | Every pair has a typed evidence record with status and reason code; no silent drops; retained V6 status ACTIVATED/NOT_ACTIVATED/UNKNOWN becomes derived field `activation_status` of `SufficiencyRecord` | FS s8; CM V-07 | Records + hash chain implemented; `activation_status` naming not verified | Covered; field naming open (OI-03) |
| R-11 | Channels and regimes labelled in every reported number; harness declaration `H` is part of verdict identity | FS s4, s11; CM V-05 | Config strict-validated; `H` recorded per verdict | Covered |
| R-12 | **Re-scoped.** Return-state/exception observation is in `C_obs`; "state/invariant layer" is module E (optional V7-A pilot) | D2, D5 | Not implemented (optional) | Re-scoped; pilot Phase 3+, not authorised |
| R-13 | **Re-scoped to pilot.** Per-input paired state comparison is E-only | D5 | Not implemented | Re-scoped; not authorised |
| R-14 | **Re-scoped.** No F subsystem; projection functions in G/H; per-view ablation only if E/pilot runs | D5; CM M-01 | G not implemented | Re-scoped |
| R-15 | Behaviour-preserving refactors must not become `DIVERGENT_OBSERVABLE`: the observed-channel verdict is alignment-free; alignment failure yields `INSUFFICIENT`, never silent | FS s2 B2 | `alignment_failed` only on parse failure | Partially covered (OI-06) |
| R-16 | Where there is no output difference, classify as unexercised (`changed_region_not_activated`) vs observed-same; "masked internal" classification is E-only advisory | FS s6; D2 | Activation implemented; masked classification absent | Covered (unexercised); masked is pilot |
| R-17 | Return/exception divergence is a scored component of the verdict (not an add-on regime) | FS s4 | Implemented | Covered |
| R-18 | Abstention is a typed output (`INSUFFICIENT` + closed reason enum); abstained pairs are not scored or filled; coverage-vs-error reporting; abstention counted as non-detection identically for all arms | FS s7; D7; RISK R37 | Implemented; INSUFFICIENT dominated by engine gaps (red team) | Covered; interpretation caveat (R42) |
| R-19 | **Rewritten.** Three-way decision `DIVERGENT_OBSERVABLE` / `NO_DIVERGENCE_OBSERVED(S)` / `INSUFFICIENT`; test: `NO_DIVERGENCE_OBSERVED` is never emitted from `changed_region_not_activated` evidence and the code can emit no equivalence string | FS s2; CM V-03 | Closed enum asserted in `Verdict`; B-1 (NO_RUN) fix recorded as 700532b8 | Covered (rewritten) |
| R-20 | Prediction (J) claims need a pre-declared paired test over conventional+differential baselines on >= 2 sealed holdouts; J never touches a verdict | D5; CM X-12 | Not implemented (off) | Covered as optional; margin (+0.03 vs +0.05) unresolved (O12) |
| R-21 | Cross-generator generalisation: leave-family-out; generator-fingerprint baseline reported | EP R1 | none | Protocol only; Phase 3, not started |
| R-22 | Labels from behavioural oracle plus adjudication, never from generator type; truth classes without `INTERNAL_ONLY`; Eq-B never by fuzz-negative alone | EP R1; GT; CM X-03 | Dev labels are transformer labels, explicitly unadjudicated | Protocol only; adjudication Phase 3, not started |
| R-23 | Preserving transformations validated before labelling (the "EQUIVALENT" word applies to a truth label class Eq-B only, never to a tool verdict) | EP R1 | none | Protocol only |
| R-24 | Variant canonicalisation, dedup, effective N, fold splits by group | EP R1; K5 leakage audit | Not done for V7-B | Phase 3, not started |
| R-25 | Mandatory confound baselines on every benchmark | EP R1 | B1, B1+rep, B2 (QuixBugs), B3, B4 on dev | Partially covered; independent data absent |
| R-26 | Pristine sealed holdout, hash-committed before extraction | D9 (K5); EP R1 | None exists; all data burned (research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md) | Not met; Phase 3, not started |
| R-27 | Real-bug corpus with pre-declared eligibility; "coverage" = decided coverage over eligible pairs (one definition, CM X-07) | EP R1; FS s12 | QuixBugs/BugsInPy units only; K1 not met on dev data | Not met; Phase 3, not started |
| R-28 | Freeze/manifest practice; chronology machine-checked | L; GATES R1 | Documents only | Partially covered |
| R-29 | Pinned interpreter (CPython 3.13), seeds, thread caps, cross-machine reproduction | FS s11 | Single machine | Cross-machine not verified |
| R-30 | Stale-artifact detector | L | none | Not covered for V7-B |
| R-31 | Selection rules and metrics pre-declared; deviation ledger | GATES R1 D; D8 | V7-B shaped on dev data (readiness report) | Partially; no confirmatory claim possible |

R-13 and R-30 were found by P0 (R-A) to appear in no V7 design document; here R-13 is explicitly re-scoped to the E pilot and R-30 is carried as "not covered". R-14 is no longer orphaned (re-scoped). The status column is a design-coverage trace, not a conformance finding.

## 3. Coverage check (areas A-L)

Areas A-E, G-I, K, L map as in the original section 3; area F (R-14) is re-scoped; areas E and J are optional. No requirement now demands an equivalence-class output.

## 4. Risk themes (original section 4)

Unchanged as themes (leakage, label quality, instrumentation, activation, generalisation); register entries are in `SBG_V7_RISK_REGISTER.R1.md`. Added residual risk: capturing return values moves V7-B toward plain differential testing, which scored near ceiling where outputs were observable; V7-B must state what it adds beyond it (R-20 logic, K4).

Limitations (carried): figures are from the V6 reports and audit JSONs, not recomputed; F-06 "0.771 DEV" is a decision-report figure; "V5 external below chance" is second-hand.

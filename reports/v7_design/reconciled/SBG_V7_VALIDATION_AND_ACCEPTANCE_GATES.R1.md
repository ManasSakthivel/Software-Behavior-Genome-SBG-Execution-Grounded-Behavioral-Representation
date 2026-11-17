# SBG V7 Validation Matrix and Acceptance Gates, R1

Reconciled version R1 of SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.md; original preserved at reports/v7_design/_original_archive/

Status: DRAFT R1, companion to SBG_V7_EXPERIMENTAL_PROTOCOL.R1.md ("EP"). Authority: P0_BINDING_DECISIONS.md (D1-D11). Verdicts (`DIVERGENT_OBSERVABLE`, `INSUFFICIENT(reason)`, `NO_DIVERGENCE_OBSERVED(S1|S2|S3)`) and sufficiency levels S0-S3 are defined only in P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md ("SPEC"); this document cites them and restates no sufficiency threshold. There is no equivalence verdict. Truth classes, metrics (Det, FAR, decided coverage, false alarm), baselines, budget unit and statistics are in EP and are not repeated. Module letters follow D5: core A, B, C, D, G, H, I, K, L; E optional (V7-A pilot only); F is not a subsystem (projections inside G/H); J optional, off by default.

Gates are numbered G0-G8 only. Kill/pivot checkpoints are K1-K5 (section B.0). No other gate identifiers exist.

Conventions for all thresholds below:
- "Rate" thresholds are checked on the upper (or lower) 95% bound of a cluster bootstrap (cluster = independent cluster as defined in EP 3.2) unless stated; a point estimate alone never passes a gate, except where a row says "point estimate" explicitly.
- Validation-matrix suites are DEV-N assets: construction scripts and seeds are frozen at G0 (hash) and the suites regenerated with fresh seeds at G6 (never used for tuning), giving a held-out confirmation of each row.
- n per row is the minimum number of independent base units, not variants of one unit.
- Row thresholds are engineering tolerances on constructed units (justified in C.4); they bind through the amendment procedure (D). None of them substitutes for sealed-holdout evidence.
- Names used for "false DIVERGENT" in rows: FD = DIVERGENT_OBSERVABLE emitted on a unit whose truth is no output difference. "N" = NO_DIVERGENCE_OBSERVED at the level named; "N(>=S2)" means at a level at or above S2 as defined in the SPEC.

---

## A. Validation test matrix (14 rows plus control row 0, re-expressed under the new verdicts)

Status column: GATING = counts toward G5/G6 and success criterion C.1(7). PILOT = diagnostic for the optional V7-A pilot; reported, not gating (D2: the "internal change masked by outputs" row is a pilot diagnostic, not a gate).

Suite mapping (MATRIX X-13): legacy roadmap Suite A maps to rows 1-3, Suite B to rows 4-8, Suite C to row 9, Suite D to row 11, Suite E to row 10. The per-row n below binds; roadmap suite sizes do not.

Empty/identical changed regions (MATRIX S-03): rows 0-2 contain pairs whose changed region is empty or byte-identical, for which activation is undefined. Where the SPEC gives such pairs a distinct handling (for example an "unchanged" outcome with no verdict), that outcome replaces the NO_DIVERGENCE_OBSERVED expectation in rows 0-2 and the FD criterion is unchanged. Until the SPEC fixes this, the expectation below is provisional (CHANGELOG U-2).

Row 0 (control, mandatory): identity and self-comparison. 200 units, each compared with a byte-identical copy and with a copy executed in a fresh process. Expected: NO_DIVERGENCE_OBSERVED(N(>=S2)) in >= 90%, else INSUFFICIENT; FD = 0 (upper 95% bound <= 0.5%). Status GATING. Gates B, G, H, L.

| # | Case | Construction | Expected verdict (R1 names) | Pass criterion (numeric) | Status / gates |
|---|---|---|---|---|---|
| 1 | Variable renaming | AST alpha-renaming of locals/params/loop variables (not public parameter names used by keyword callers: that sub-case is a genuine interface change). >= 150 units x 5 renamings incl. shadowing, comprehension scopes, nonlocal/global names | N(>=S2); keyword-parameter rename sub-case: DIVERGENT_OBSERVABLE | FD <= 0.5% (upper bound <= 1.5%); INSUFFICIENT <= 5%; static alignment maps >= 99% of statements one-to-one; keyword rename sub-case detected >= 95%. (State-view alerts keyed by identifier are checked in the pilot only, if E is enabled: pilot diagnostic.) | GATING; G, H |
| 2 | Formatting / irrelevant structure | Whitespace, comments, docstring text, redundant parentheses, import reordering, function reordering, dead code after `return`, line wrap, type-hint-only changes. >= 150 units | N(>=S2); for whitespace/comment-only edits the captured event stream is identical after location normalisation | FD <= 0.5% (upper bound <= 1.5%); 100% identical event-stream hashes for whitespace/comment-only edits; INSUFFICIENT <= 3%; decided coverage >= 95% | GATING; B, D, G, H |
| 3 | Equivalent refactoring | Extract/inline, loop <-> comprehension, if/else inversion, early return, tuple swap, `x += 1` vs `x = x + 1`. Truth = representation-only or no-output-difference by truth harness T1-b/T2. >= 120 units, including cases where call graph and internal state legitimately differ (V6 facts: SP-5, SP-8 false positives scored highest) | N(>=S2) or INSUFFICIENT. An `internal_divergence` annotation may appear (only if E enabled) but can never change the verdict | FD <= 1% (upper bound <= 3%); decided coverage >= 70% (always-INSUFFICIENT fails); structural check: zero verdicts altered by the annotation | GATING; G, H, I |
| 4 | Genuine state change | Mutated object/accumulator update; bug exposed only after k >= 2 calls of a stateful object (state-accumulation family). >= 120 units. The witness is a call sequence whose observable output differs | DIVERGENT_OBSERVABLE with replayable witness | Det(60 s) >= 90% (lower bound >= 85%); witness validity >= 99%; median input executions to first witness <= 200; paired difference vs like-for-like B1-directed reported with CI, point estimate >= 0 (no non-inferiority claim) | GATING; A, H |
| 5 | Control-flow change | Flipped condition, removed/added branch, altered loop bound, swapped branch order with side effects, early-return change. >= 120 units | DIVERGENT_OBSERVABLE | Det(60 s) >= 90% (lower >= 85%); first-divergence locus in the changed region or its static data-dependents in >= 85% of detected; witness validity >= 99% | GATING; A, G, H |
| 6 | Return-value change | Return mutations (value, type, length, ordering, None vs value); output-free signals alone are known blind (V6 fact: SC-6 AUROC 0.31-0.54). >= 120 units | DIVERGENT_OBSERVABLE via return-value channel | Det(60 s) >= 95% (lower >= 90%); median executions to first witness <= 20; with the return channel disabled (ablation) N(>=S2) on these units <= 2% | GATING; B, H, I |
| 7 | Exception change | Exception introduced/removed/type changed; same type with different message (message channel off: N or INSUFFICIENT; on: DIVERGENT_OBSERVABLE); exception only on rare input. >= 100 units | DIVERGENT_OBSERVABLE (type change) | Det(60 s) >= 90%; message channel off: FD on message-only changes <= 1%; on: Det >= 95%; channel configuration recorded in the verdict (MATRIX V-05) | GATING; B, H |
| 8 | Side-effect change | Mutated argument in place, global/module write, sandbox-file write, stdout/stderr change, logging-only change (not contractual). >= 120 units | DIVERGENT_OBSERVABLE on declared channels; INSUFFICIENT (unobserved-channel reason per SPEC) on undeclared channels; logging-only: N or INSUFFICIENT | Det on declared channels >= 85% (lower >= 80%); N(>=S2) when the side-effect channel was not observed <= 2%; FD on logging-only <= 1% | GATING; B, H, I |
| 9 | Internal change masked by outputs | (a) masked for every input in the declared domain (truth internal-only or representation-only by T1-b/T2); (b) masked on common inputs but exposed on a rare region (truth observable divergence by independent oracle). >= 100 units each | (a) N or INSUFFICIENT with annotation `internal_divergence = observed` if E enabled; (b) DIVERGENT_OBSERVABLE | (a) FD <= 1%; annotation rate among units where the state view fires reported with its lower bound against 0.70 (EP H8a). (b) Det(300 s) minus B1-directed reported with CI (EP H7 pre-test). Neither sub-case gates G5; failure of (b) is recorded and does NOT downgrade V7-B (D6): it only governs whether the V7-A pilot is attempted | PILOT (non-gating); E, H, A |
| 10 | Changed code never activated | (a) code unreachable from the driver; (b) reachable only via rare input guards; (c) behind a precondition drivers never satisfy. >= 100 units | (a)(c) INSUFFICIENT (not-activated reason); (b) DIVERGENT_OBSERVABLE if activated, else INSUFFICIENT | N at any level emitted on never-activated pairs <= 1%; INSUFFICIENT reason correct >= 95%; on (b) the K3 test (K table) is applied to row-10(b) units; the row passes on this criterion iff K3 passes on them | GATING; A, I |
| 11 | Nondeterministic execution | Unseeded `random`, `time`, `uuid`, address-dependent output, set/dict iteration under hash randomisation, thread interleaving, environment-dependent paths. Variants: (a) nondeterminism affects a compared channel; (b) controllable by seed/clock freeze; (c) real divergence plus noise. Also old-vs-old self-comparison. >= 100 units | (a) INSUFFICIENT (nondeterminism reason); (b) normal verdict after control; (c) DIVERGENT_OBSERVABLE only if the difference reproduces in 5/5 replays, else INSUFFICIENT (flaky-witness reason) | FD on nondeterminism-only <= 1%; injected nondeterminism flagged >= 95%; (b) control success >= 90%; (c) DIVERGENT_OBSERVABLE from a non-reproducing difference <= 1% and true reproducible divergences retained >= 80% | GATING; B, H, I, L |
| 12 | Partial instrumentation | Changed code in C extensions, `exec/eval` code, threads/subprocesses/async tasks, trace-buffer truncation, import-hook failure in a subset of modules, tracer exception swallowed. >= 100 units | Output-channel divergence still found (DIVERGENT_OBSERVABLE); N capped below S2 when the changed region is outside instrumentation; INSUFFICIENT (partial-instrumentation reason) when completeness is below the declared floor | Sufficiency downgrade correct in >= 98% of injected cases; N(>=S2) with partial instrumentation of the changed region <= 2%; miss rate under partial instrumentation <= full-instrumentation miss rate + 2pp; completeness metadata on 100% of verdicts | GATING; B, D, I |
| 13 | Cross-project generalisation | Leave-project-out on DEV-N (>= 8 folds, >= 30 projects), then sealed H-R/H-P at G7 as H9 estimation. Parameters fixed before | Same metrics as rows 4-10 aggregated | DEV-N gate: Det drop vs in-project <= 10pp absolute and FAR increase <= 5pp (point estimates, CIs reported); S1 > S2 > S3 miss-rate ordering; decided coverage >= 60% (V6 fact: BugsInPy activated 28.5%); ECE <= 0.05. On sealed data these are reported with CIs as EP H9/H6 estimation (not powered) | GATING at G5 (DEV-N); estimation at G7; I, A, B, G |
| 14 | Unseen change types | Leave-mutation-family-out on DEV-N and the >= 6 new blinded H-M families; per-family reporting | Same as rows 4-10 | Pooled Det >= 0.75 x in-family Det; FAR on unseen families <= 0.15 (upper bound <= 0.20) with S3 miss-rate cap 0.10 on that subset; no family with Det = 0 and N-rate > 30% without being flagged INSUFFICIENT; shortcut probe (EP 6.1) <= 0.65 | GATING at G5 (DEV-N); estimation at G7; I, H, A, J (if built) |

Cross-row checks: (i) per-row results use the budget definition of EP 7 (CPU-seconds); (ii) a row passes only if every sub-criterion passes; (iii) an arm that passes by emitting INSUFFICIENT for > 40% of pairs in the row fails the row's coverage sub-criterion; (iv) S-level caps quoted in rows are calibration claims, UNVALIDATED until calibrated on development data per D3; if the SPEC makes S3 unattainable by default (MATRIX S-04) every S3 criterion is dropped, not relaxed.

---

## B. Phase gates (G0-G8) and kill/pivot checkpoints (K1-K5)

Common to all gates: unit tests pass in CI; all artifacts hashed into the ledger; no holdout files readable by the dev environment (custodian script); gate review signed by one implementer plus one independent reviewer. "Fail-fast" stops forward work and invokes the stated response; "fallback" is what is claimed instead.

### B.0 K1-K5: single table (D9)

K gates are decision procedures with a fixed failure response. STOP ends the programme with a negative-result report. PIVOT changes the claimed system as stated. DOWNGRADE (K5 only) means no confirmatory evaluation: no sealed holdout is unsealed and only an exploratory report with CIs is produced. Thresholds marked "carried" come from the original roadmap checkpoint because D9 states a response but no number; they are UNVALIDATED defaults (CHANGELOG U-5).

| K | Definition | Measurable test | Fixture / dataset | Threshold or decision procedure | Failure response | Reproducibility requirement |
|---|---|---|---|---|---|---|
| K1 | Real-pair feasibility | Count of runnable real pairs: both versions import and execute at least one input to completion under the P1 isolation runner, scope has a drivable signature, no network/GPU/interactive need | DEV-N real-regression pilot mining (not V5/V6 generators, not sealed sets); timing: end of the feasibility pilot, before G1 closes | >= 100 runnable real pairs from >= 8 independent projects | STOP | Mining script and candidate list hashed; deterministic ordering; independent rerun reproduces the count; excluded-units ledger attached |
| K2 | Capture determinism and activation census | On the K1 pairs, with isolation rebuilt per D10: determinism-confirmed rate (3x repeat agreement on the compared channels) and activation rate of replay plus a crude random-argument generator (changed region entered on both versions by >= 1 input) | K1 pairs (>= 100); replay-only and crude-generator arms | Determinism-confirmed >= 70% of runnable pairs AND replay+crude activation >= 35% (carried from roadmap K2) | One redesign cycle of module B (<= 4 weeks), re-measure; second failure: STOP | Fixed seeds; per-pair run records with hashes; rates from raw records by a script in the ledger; byte-reproducible on a second machine |
| K3 | Exploration lift | Activation rate of the explorer vs replay at the per-pair budget of EP 7 (60 CPU-s), paired, program/project-cluster bootstrap | Development set (DEV-N real pairs plus row-10(b) units), same pairs as K2 | Activation >= 60% AND >= +15 points over replay (lower 90% cluster-bootstrap bound > 0) | PIVOT to V7-B with replay-plus-structure-aware exploration only: no directed-exploration claim, no directed scheduling in the core | Pre-declared seeds {1001..1005}; budgets in CPU-seconds including overhead; explorer hyperparameters tuned on development data only |
| K4 | Core thesis | Sufficiency-aware witness comparison vs same-budget like-for-like B1-directed and B2-directed under the same sufficiency gate. Pre-declared single primary metric: FAR reduction (EP 1.1 definition) at matched decided coverage >= 0.60, 60 CPU-s | Development set (DEV-N real regressions; synthetic rows as secondary); evaluated at the end of G3 and again at G5 entry | FAR(V7) lower than both comparators with the lower 90% cluster-bootstrap bound of the difference > 0 AND point estimate >= 10pp (the effect of interest). No any-of rule. Det and TTFW reported, not decisive | PIVOT to V7-B' = sufficiency-aware differential testing without the explorer, impact and state modules and without any novelty claim beyond the evaluation protocol. If V7-B' shows no benefit over B1 (same test, lower bound <= 0): STOP | Metric, comparators, coverage matching and seeds declared in the analysis plan before the run; all arms run from hashed code; bootstrap seed 42 |
| K5 | Benchmark and adjudication readiness | Power-sized counts, agreement and leakage audit before any sealed-holdout unseal | H-R (and H-M if it is to be confirmatory) manifests and labels, custodian-held | >= 60 independent projects (clusters), >= 250 independent-lineage divergent pairs, >= 20 mixed-class projects; adjudication kappa >= 0.7 with the CI rule of EP 3.5; leakage audit clean (zero cross-split duplicate groups; shortcut and diff-shape probes <= 0.65 or matched subset declared; no label-correlated input path) | DOWNGRADE: no confirmatory evaluation; exploratory report only | Counts computed by a hashed script from the manifest; kappa from the adjudication ledger; audit report hashed; custodian signs |

Placement: K1 and K2 are exit conditions of G1; K3 of G2; K4 of G3 (first check) and G5 (final check); K5 of G5, before G6 can start. The roadmap's per-checkpoint "shrink claims" options and the "Pivot / stop" ambiguity (MATRIX K-01) are replaced by the single response column above.

### G0: Protocol freeze and data custody ready (before any V7 code beyond harness stubs)
- Quantitative: EP, this document and the SPEC hashed and recorded; custodian appointed; T0 declared; rubric kappa pilot meets EP 3.5 (re-pilot on fresh items if not); power analysis re-run with DEV-N estimates and sample targets amended pre-seal (EP 8.6); holdout compute budget recomputed from frozen sizes and approved (EP 7); project lists for H-R/H-X frozen and independence report produced (0 cross-set duplicate groups, 0 source-hash overlap); truth-harness smoke test on 50 items; analysis scripts run end-to-end on a label-shuffled synthetic dataset.
- Fail-fast: kappa below the EP 3.5 floor after two rubric iterations: narrow scope to the classes where raters agree (the rest become insufficient/ambiguous). Fewer than 30 eligible H-R projects by the mining deadline: no confirmatory claim is possible (K5 requires 60); the programme proceeds exploratory-only and the success criteria in C drop to "inconclusive" at best, stated in advance.

### G1: Observation substrate (modules B, D, K, L)
- Integration: determinism controls on; 3 repeated runs of 1000 deterministic units give bit-identical event-stream hashes >= 99.5%; content-addressing and provenance round-trip 100%; rows 0, 2 pass; row 11 injected-nondeterminism detection >= 95%.
- Isolation (D10; MATRIX M-05): each property passes an experimental check: fresh child process per run, `setrlimit`, process-group kill, tracing outside user-code reach with `settrace(None)` evasion detected, network denial and write confinement (sandbox-exec on macOS, container `--network none` on Linux); zero escapes on the hostile-program family (runaway thread, child process survival, `os._exit`, network attempt, trace evasion). The v6_compat runner is excluded from every V7 measurement.
- Performance: tracing overhead, adopting the roadmap's two-level budget (MATRIX M-07b): call/return/branch-level <= 5x median; line-level <= 25x median, <= 60x p95. Peak memory <= 2 GB at p95; per-pair isolation; crash rate < 2%. Per-run limits and the default per-pair input cap are set from measured per-run cost, not V6's 60 s default (MATRIX B-02). Storage is reported per pair-seed and checked against the replay-recipe design (D5; RT Q7); the original 50 MB p95 event-log bound applies only to runs that store events.
- Scientific (observation, the V6 dominant failure): on NON-PRISTINE BugsInPy and QuixBugs, used as development targets only, decided-pair coverage (EP 1.1) >= 70% of drivable pairs and >= 50% of all pairs (V6: 28.5% activated on BugsInPy; 36 QuixBugs declared pairs have no inputs and must be INSUFFICIENT with the undrivable reason, not failures).
- K1 and K2 are evaluated here.
- Fail-fast: decided-pair coverage < 50% of eligible pairs after one remediation cycle (<= 4 weeks): redefine scope to function-level drivable units and report the narrower eligibility; make no claims about "real bugs in general". K1/K2 failure responses per B.0.
- Fallback: V7-lite = output-differential harness with sufficiency labels only.

### G2: Exploration (module A) with like-for-like baselines
- Integration: strategies per EP 5 on the same harness; B1-blind, B1-directed, B2, B2-directed implemented and tuned with equal random-search effort over their own knobs (EP 4 rule 4).
- Scientific (DEV-N): K3 evaluated. Det(60 s) of the explorer minus B1-directed reported with CI at 10/60/300 s (no non-inferiority test); activation lift on row 10(b) per K3.
- Performance: scheduling overhead <= 10% of budget at median.
- Fail-fast: K3 failure per B.0 (PIVOT: no directed exploration claim). If directed scheduling does not beat random on activation after two redesigns, remove it from the core (keep property-based, structure-aware, coverage-guided).
- Fallback: A = B2-equivalent.

### G3: Alignment and divergence (modules G, H; projections inside them; E only for the pilot)
- Integration: rows 1, 2, 3, 5, 6, 7 pass; alignment accuracy on a labelled set of 200 edited pairs >= 95% statement matches; locus accuracy (row 5) >= 85%.
- Performance: alignment + projection construction <= 25% of per-pair budget at median, <= 60% at p95.
- Scientific: each of G(dynamic anchors) and H(control-flow-event divergence) is ablated on DEV-N under the retain-or-drop rule (EP 5). Rows 4, 8 pass. K4 first check.
- Fail-fast: row 3 FD > 3% (upper bound) after two cycles: tighten the observed-channel set and alignment-trust gating; internal projections never feed verdicts in any case (D2). Persisting failure: fallback below.
- Fallback: "output-channel + control-flow-event divergence" only.

### G4: Evidence, uncertainty, decision (module I)
- Integration: rows 8 (honesty), 10, 11, 12 pass; each verdict carries reason code, completeness metadata, channel configuration and sufficiency level, 100%; every verdict resolves to an evidence-ID chain (D4).
- Scientific (DEV-N calibration split, never used for tuning thresholds): miss-rate ordering S1 > S2 > S3 with CI separation; ECE <= 0.05 against nominal caps; risk-coverage at coverage 0.7 not worse than B1-directed with the same gate.
- Fail-fast: ordering violated or S3 miss rate > 0.20 on DEV-N: remove S-level claims; ship the binary {DIVERGENT_OBSERVABLE, INSUFFICIENT} plus raw coverage numbers (no "no divergence observed" assurance language).
- Fallback: "V7-witness-finder" with no assurance claims.

### G5: Integrated development gate and go/no-go for freeze
- Integrated system on DEV-N: validation matrix (all GATING rows plus row 0 on suites generated with frozen seeds; row 9 reported as pilot diagnostic) and the NON-PRISTINE regression table (reported, not decisive).
- Conditions to proceed: all GATING rows pass (rows 13/14 on leave-project/family-out DEV-N); K4 final check passed (else the pivot in B.0 is executed and the claim set is downgraded to V7-B' as a recorded, pre-seal decision); K5 passed (else DOWNGRADE, no unseal).
- Sealing prerequisites: H-R and H-M sealed (hashes in ledger) BEFORE G5 closes; checked, not assumed.
- Performance: the approved holdout compute budget (EP 7: 292-875 CPU-hours for the three-arm minimum, up to about 1750 with diff-blind arms, recomputed at G0) is available; the original "<= 150 CPU-hours" estimate is withdrawn.
- Fail-fast: integrated V7 worse than B1-directed at 60 s on the DEV-N set with the paired 95% cluster CI wholly below 0: NO-GO to holdout; return to G2-G3 with an 8-week time box; two consecutive failures terminate the programme with a negative-result report.
- J admission (replaces the original optional gate, no extra gate number): J enters analysis only after G5; its claim is EP H10 (paired improvement over conventional features by >= +0.03 AUROC on >= 2 sealed holdouts, own Holm family); otherwise J is not part of V7. The +0.03 vs roadmap +0.05 difference (MATRIX X-12) is unresolved.

### G6: Freeze and rehearsal
- System build hash, config, SPEC-defined S cutoffs as calibrated, budgets, seeds, analysis-plan hash recorded; validation suites regenerated with fresh seeds and GATING rows pass again; rehearsal of the whole evaluation pipeline on a burnt set (for example NON-PRISTINE v8 test) completes with 0 unit-unrelated crashes, <= 2% tool-error rate, byte-reproducible on a second machine (same Python version) and within documented tolerance on a different Python minor version.
- Fail-fast: any holdout access found by the audit: that holdout is burnt, H-X promoted, recorded as class-C amendment.

### G7: Single-shot sealed evaluation
- Per EP 3.3: custodian unseals; run once with 5 seeds x 3 budgets x all arms; outputs hashed before labels are mounted; then scoring. No decision rules here beyond executing the pre-declared analysis; deviations only for crashes (identical rerun, both reported).

### G8: Reporting, reproducibility, release
- All pre-declared metrics for all holdouts (EP 10); from-raw reproduction of every table identical (V6 achieved 2392/2392); independent rerun on a different machine and Python minor version within tolerance; amendment log complete; failure catalogue produced; V7-A pilot (if admitted) reported as exploratory.
- Fallback: any unreproducible table is withdrawn from claims.

V7-A pilot admission (non-gating, after G7): attempted only if V7-B shows headroom (decided coverage >= 0.60 and FAR >= 10% on H-R), within <= 12 weeks and <= 12 engineer-weeks, on authored suites with independent truth (EP 2.6). Its outcome never alters the V7-B verdict of the programme.

---

## C. Final V7 success criteria

### C.1 What declares V7-B successful (decided mechanically from the pre-declared analysis)
All on sealed holdouts. H-R carries the confirmatory decision; H-M must be directionally consistent (EP 2.7). "Holm" means the family {H2a, H2b, H4}.
1. Validity: EP H1 holds (witness validity >= 0.99, lower 95% >= 0.97; oracle-confirmed >= 0.95).
2. Detection: H2a and H2b significant (Holm-adjusted p < 0.05) for the +10pp superiority contrast at 60 CPU-s on H-R; point estimate favourable on H-M. No non-inferiority criterion exists.
3. Reduced false assurance: H4 significant (Holm) with absolute FAR reduction >= 10pp vs B1-directed-with-gate at matched decided coverage; point estimate favourable on H-M; P(N at S3 | divergent) <= 0.10 on H-R.
4. Coverage: decided coverage on H-R >= 0.60.
5. Calibration: S1 > S2 > S3 ordering (point estimates, CI reported) and ECE <= 0.05; descriptive, not a Holm test.
6. Generalisation: rows 13 and 14 criteria evaluated on sealed data as estimates with CIs; no pre-declared NO-GO breach (C.3).
7. Validation matrix: all GATING rows pass on the G6 fresh-seed suites.
8. Reproducibility: G8 satisfied.
9. Time to first witness (EP H3): reported with CI and direction; not a pass/fail criterion (not powered).

Outcome classes: CONFIRMED (V7-B) = criteria 1-8 met. INCONCLUSIVE = K5 counts met, no NO-GO trigger, but H2a/H2b/H4 not significant: the report states the estimates with CIs and that absence of significance is not evidence of no effect. EXPLORATORY-ONLY = K5 not met (no unseal). NO-GO per C.3. The V7-A tier is removed from the success tiers; internal-state value is the exploratory pilot (EP 2.6) and "internal-state divergence adds information" is never a programme-level success claim.

### C.2 What is insufficient (never counts toward success)
- Any result on the five NON-PRISTINE sets.
- Beating V5 or V6 only.
- AUROC of anything (except H10 for J).
- Gains at only one budget; gains only on H-M with none on H-R, or the reverse (favourable H-M direction alone is not enough).
- Point estimates without cluster CIs; p-values without Holm; inference with fewer than 60 independent clusters.
- FAR improvements with decided coverage < 0.60, or with INSUFFICIENT > 40% on the primary pairs; FAR compared against an ungated "no difference found = pass" baseline.
- Passing the validation matrix without sealed-holdout confirmation.
- Detection gains explained by the shortcut or diff-shape probes (AUROC > 0.65 without the matched subset replicating the effect).
- Any claim of non-inferiority, equivalence, or "no effect" derived from a non-significant result.

### C.3 NO-GO triggers (any one, on sealed holdouts, ends V7 as a claimed system; the report states the negative result)
- Witness validity lower bound < 0.95.
- V7 worse than the like-for-like comparator on Det(60 s) with the paired 95% cluster CI wholly below 0 (upper bound < 0) on H-R (replaces the original "inferior with CI excluding -2pp").
- S3 miss rate > 0.20 on H-R, or ordering of S1/S2/S3 violated.
- Decided coverage on H-R < 0.40 without a compensating validated INSUFFICIENT mechanism (INSUFFICIENT reason accuracy >= 95% and Div-rate in abstained within 10pp of decided).
- Det drop > 20pp vs DEV-N leave-project-out, or unseen-family FAR upper bound > 0.30.
- Confirmed holdout contamination with no unburnt H-X replacement completed.
- Reproducibility failure at G8 not repaired within 4 weeks.
- If only the H2/H4 superiority is not shown, the outcome is INCONCLUSIVE, not NO-GO.

### C.4 Justification of thresholds (honest)
- 0.99 validity: replay validity is nearly definitional; 0.97 lower bound allows sampling uncertainty at about 250 witnesses.
- +10pp effect of interest: the smallest effect the planned sample can confirm (about 60 projects unadjusted, 80 adjusted; EP 8.2). +5pp would need about 300-450 projects; it is exploratory. -2pp non-inferiority needs about 8000 pairs and is dropped. These margins are driven by arithmetic and judgment, not by any prior V7 data. V6 facts show plain differential comparison is near ceiling where outputs are observable (v10 0.995; QB declared-evaluable 0.976), so headroom is in the hard stratum.
- 10pp FAR reduction: chosen to match the detectable effect size; the earlier 25% relative alternative equals 10pp only at FAR(B1) = 0.40.
- Coverage floors (0.60 success, 0.40 NO-GO): reference failure is V6's BugsInPy activation of 28.5%; abstention was 143/200 = 71.5% (76.4% among the 55 positives; MATRIX N-03). Both are judgment.
- S-level miss-rate caps (S1 0.35 / S2 0.20 / S3 0.10): calibration claims, UNVALIDATED defaults; ordering is the stronger result; revisable only before G6 by amendment on DEV-N evidence.
- Generalisation caps (10pp, 20pp): V6 leave-type-out drop for the fingerprinted GBM was 0.972 to 0.742; 10pp is deliberately demanding but is an estimation target at sealed scale (unpowered).
- Row thresholds (0.5-1% FD, 85-95% detection) are engineering tolerances on constructed units.
- K2 values (70%, 35%) and K3 values (60%, +15) were set after reading V6 failure lists; they are a contaminated design prior (EP 3.1) and every primary claim must be confirmed on sealed H-R.
- Unknowns: label noise in real regressions may exceed V6's 8.7% unresolved rate; above 15% the claim is restricted (EP 3.5). Mining 60-80 fresh projects is unproven.

---

## D. Anti-p-hacking rules and amendment procedure

D.1 Rules
1. Pre-registration: EP, this document, the SPEC, the analysis plan (scripts + hash), budgets, seeds, S cutoffs, baselines and their tuning budget are hashed into the ledger at G0 (protocol) and G6 (system/config). The primary metric set, the Holm family {H2a, H2b, H4} and directions cannot change after G6.
2. One confirmatory run per holdout (EP 3.3). Every evaluation run on any sealed set is recorded in an append-only run ledger. Exploratory runs on sealed data are forbidden; a violation burns the set.
3. Forbidden after unseal: changing thresholds, metrics, strata, exclusion rules, budgets, seeds, baselines; dropping pairs, projects or seeds; switching between all-pairs and activated-only headlines; choosing the best of several seeds or budgets; re-labelling. All seeds and budgets are always reported.
4. Exclusions only by pre-declared inclusion rules, listed in the excluded-units ledger; none may depend on system output.
5. Multiplicity: the primary family is fixed in EP 2.7 and tested with Holm; anything else is exploratory with BH values labelled exploratory.
6. Negative controls at G6 and G7: label-shuffled pipeline (outputs byte-identical when labels withheld), identity/self-comparison (row 0), edit-size-only, family-only and diff-shape probes, reversed-input-order run. Any failure invalidates the run.
7. Baseline parity: B1/B2 variants tuned with equal random-search budget over their own knobs; weaker baselines void the claim.
8. Two-person rule for every threshold, rubric and analysis-plan change; custodian verifies hash chains.
9. Blinding: adjudicators blind to system outputs; analysts running confirmatory scripts do not edit them; scripts run from the hashed checkout.
10. Reporting honesty: all hypotheses reported with pre-declared consequence; "exploratory", "pilot" and "non-pristine" labels mandatory; post-hoc findings cannot support success criteria. V6's precedent (selection rule operationalised after data was seen) is what to avoid.

D.2 Amendment log procedure
- File AMENDMENTS.md (append-only, hash-chained) plus the diff of the changed document.
- Entry fields: ID (A-001...), date, author, reviewer, document and section, old text, new text, reason, trigger, data-exposure status, class, expected effect on claims, ledger hash of the new version.
- Classes: A = clarification, no effect on any number or decision; B = pre-data change (before G6 and before any sealed data exposure; thresholds still justified); C = post-data change (after G7 unseal or any peek): results labelled "exploratory, amended" and cannot support success criteria; D = emergency deviation (crash, contamination): custodian approval, states what ran twice.
- Timing: B amendments frozen at G6; after G6 only A and C/D; after G7 only C and D.
- Disclosure: the report includes the full log and a table "claims affected by amendments". An amendment never deletes original text. Deviations are logged as class D.
- Sample-size changes (for example fewer than 60 eligible projects) are class B before sealing, class C after; below the K5 floor the consequence is DOWNGRADE, not an amended threshold.

# SBG V7 Validation Matrix and Acceptance Gates

Status: DRAFT v0.1, companion to SBG_V7_EXPERIMENTAL_PROTOCOL.md (referred to as EP). Definitions of verdicts (DIVERGENT / NO_DIVERGENCE_OBSERVED at S1-S3 / INSUFFICIENT), truth classes (Div, Eq-B, INTERNAL_ONLY, Undecided), budgets and statistics are in EP and are not repeated. Module letters follow the spine (A exploration, B capture, C static context, D evidence fabric, E state/invariant, F multi-view, G alignment, H divergence+impact, I evidence/uncertainty/decision, J optional scorer, K validation harness, L reproducibility).

Conventions for all thresholds below:
- "Rate" thresholds are checked on the upper (or lower) 95% bound of a cluster bootstrap (cluster = base program) unless stated; point estimate alone never passes a gate.
- Validation-matrix suites are DEV-N assets: construction scripts and seeds are frozen at G0 (hash), the suites are regenerated with fresh seeds at G6 (never used for tuning) to give a held-out confirmation of each row.
- n per row is the minimum number of independent base units (not variants of one unit).
- Thresholds are engineering judgment, justified in section C.4; they bind through the amendment procedure (section D).

---

## A. Validation test matrix

Each row: construction; expected verdict; pass criterion; gated module(s). "FD" = false DIVERGENT. "Sufficiency-aware N" = NO_DIVERGENCE_OBSERVED at S >= S2.

Row 0 (control, not in the requested list but mandatory): identity and self-comparison. Construction: 200 units, compare old to a byte-identical copy and to a copy executed in a fresh process. Expected: NO_DIVERGENCE_OBSERVED (S >= S2) in >= 90% else INSUFFICIENT; FD = 0 (upper 95% bound <= 0.5%). Gates B, G, H, L.

| # | Case | Construction | Expected verdict | Pass criterion (numeric) | Gates |
|---|---|---|---|---|---|
| 1 | Variable renaming | AST alpha-renaming of locals/params/loop variables (not public parameter names used by keyword callers; that sub-case is a genuine interface change and expected DIVERGENT for keyword-call drivers). >= 150 units x 5 renamings, incl. shadowing, comprehension scopes, nonlocal/global names | NO_DIVERGENCE_OBSERVED (S >= S2) | FD <= 0.5% (upper 95% bound <= 1.5%); INSUFFICIENT <= 5%; static alignment maps >= 99% of statements one-to-one; zero state-view alerts attributable to variable names (state abstraction keyed by role/position, not identifier). Keyword-parameter rename sub-case: DIVERGENT in >= 95% | G, H, F, E |
| 2 | Formatting / irrelevant structure | Whitespace, comments, docstring text, redundant parentheses, import reordering, function definition reordering, trailing dead code after `return`, blank-line/line-wrap changes, type-hint-only changes. >= 150 units | NO_DIVERGENCE_OBSERVED (S >= S2); for pure whitespace/comment cases the trace is event-for-event identical | FD <= 0.5% (upper bound <= 1.5%); for whitespace/comment-only edits, 100% of event logs identical after location normalisation; INSUFFICIENT <= 3%; decided coverage >= 95% | B, D, G, H |
| 3 | Equivalent refactoring | Extract/inline function, loop <-> comprehension, if/else inversion, early-return restructure, tuple-swap vs temp, `x += 1` vs `x = x + 1`. Equivalence established by truth harness tier T1/T2 (bounded exhaustive or proof). >= 120 units. Includes cases where call graph and internal states legitimately differ (V6 facts: SP-5, SP-8 false-positives scored highest) | NO_DIVERGENCE_OBSERVED (S >= S2) or INSUFFICIENT; INTERNAL_ONLY annotation allowed, never DIVERGENT | FD <= 1% (upper bound <= 3%); decided coverage >= 70% (anti-collapse: always-INSUFFICIENT fails); false-alarm counted from internal-view alerts promoted to DIVERGENT = 0 | G, H, F, I |
| 4 | Genuine state change | Mutated assignment/update of object or accumulator state; bug exposed only after k >= 2 calls of a stateful object (state-accumulation family); >= 120 units | DIVERGENT with replayable witness | Det(60 s) >= 90% (lower bound >= 85%); WVR >= 99%; median input executions to first witness <= 200; non-inferior to plain DT (lower paired bound > -2pp) | A, E, H |
| 5 | Control-flow change | Flipped condition, removed/added branch, altered loop bound, swapped branch order with side effects, early return change; >= 120 units | DIVERGENT | Det(60 s) >= 90% (lower >= 85%); first-divergence locus lies in the changed region or in its static data-dependents in >= 85% of detected; WVR >= 99% | A, G, H |
| 6 | Return-value change | SC-6-like return mutations plus new families (value, type, length, ordering, None vs value); output-free signals alone are known blind (V6 fact: SC-6 AUROC 0.31-0.54); >= 120 units | DIVERGENT via output channel | Det(60 s) >= 95% (lower >= 90%); median executions to first witness <= 20; if the output channel is disabled (ablation), the system must NOT claim S >= S2 NO_DIVERGENCE_OBSERVED on these units: that rate <= 2% | B, H, I |
| 7 | Exception change | Exception introduced/removed/type changed; same type with different message (message channel off: expected NO_DIVERGENCE_OBSERVED; on: DIVERGENT); exception raised only on rare input; >= 100 units | DIVERGENT (type change) | Det(60 s) >= 90%; with message channel off, FD on message-only changes <= 1%; with it on, Det >= 95%; reported channel configuration is recorded in the verdict | B, H |
| 8 | Side-effect change | Mutated argument in place, global/module state write, file write in sandbox tmpdir, stdout/stderr change, logging-only change (logging not contractual: expected N/INTERNAL_ONLY by rubric); >= 120 units | DIVERGENT on declared channels; INSUFFICIENT(UNOBSERVED_CHANNEL) on undeclared/uninstrumented channels | Det on declared channels >= 85% (lower >= 80%); channel-blindness honesty: NO_DIVERGENCE_OBSERVED at S >= S2 when the side-effect channel was not observed <= 2%; FD on logging-only <= 1% | B, H, I |
| 9 | Internal change masked by outputs | (a) truly masked for every input in the domain (intermediate overwritten/cancelled; truth = INTERNAL_ONLY or Eq-B by T1/T2); (b) masked on common inputs but exposed on a rare region (truth = Div by independent oracle). >= 100 units each. V6 fact: 180/1332 changed pairs were internally masked | (a) NO_DIVERGENCE_OBSERVED with INTERNAL_ONLY annotation; (b) DIVERGENT | (a) FD <= 1% and INTERNAL_ONLY annotation in >= 70% of cases where the state view fires; (b) Det(300 s) of V7 >= plain DT + 10pp (point), paired lower bound > 0, on >= 100 units; this row is the DEV-stage test of H7. Failure triggers the H7 fallback (section B, G5) | E, F, H, A |
| 10 | Changed code never activated | (a) dead/unreachable-from-driver code; (b) reachable only through rare input guards; (c) changed code behind a precondition drivers never satisfy; >= 100 units | (a)(c) INSUFFICIENT(NOT_ACTIVATED) or S0 (no assurance); (b) DIVERGENT if activated, else INSUFFICIENT | NO_DIVERGENCE_OBSERVED at S >= S1 emitted on never-activated pairs <= 1%; INSUFFICIENT reason correct >= 95%; on (b), directed exploration activates changed region in >= +15pp more pairs than undirected at equal budget (paired lower bound > 0) | A, I |
| 11 | Nondeterministic execution | Unseeded `random`, `time`, `uuid`, `id()`/address-dependent output, set/dict iteration under hash randomisation, thread interleaving, environment-dependent paths. Variants: (a) nondeterminism that affects the compared channel; (b) nondeterminism controllable by seed/clock freeze; (c) real divergence plus noise. Also old vs old self-comparison on these units. >= 100 units | (a) INSUFFICIENT(NONDET); (b) normal verdict after control; (c) DIVERGENT only if the difference reproduces in 5/5 replays else INSUFFICIENT(FLAKY) | FD on nondeterminism-only <= 1%; injected nondeterminism flagged >= 95%; (b) control success >= 90%; on (c), DIVERGENT wrongly emitted from a non-reproducing difference <= 1% and true reproducible divergences retained >= 80% | B, H, I, L |
| 12 | Partial instrumentation | Changed code inside C extensions, `exec/eval`-generated code, threads/subprocesses/async tasks, trace-buffer truncation, import-hook failure in a subset of modules, tracer exception swallowed. >= 100 units | Output-channel divergence still found (DIVERGENT); NO_DIVERGENCE_OBSERVED capped below S2 when the changed region is outside instrumentation; INSUFFICIENT(PARTIAL_INSTRUMENTATION) when completeness is below the declared floor | Sufficiency downgrade correct in >= 98% of injected cases; NO_DIVERGENCE_OBSERVED at S >= S2 with partial instrumentation of the changed region <= 2%; miss rate under partial instrumentation <= (full-instrumentation miss rate + 2pp); no silent loss: completeness metadata present on 100% of verdicts | B, D, I |
| 13 | Cross-project generalisation | Leave-project-out on DEV-N (>= 8 folds, >= 30 projects total), then the sealed H-R/H-P at G7. System parameters fixed before | Same metrics as rows 4-10 aggregated | Det drop vs in-project <= 10pp absolute; FAR increase <= 5pp; S1 > S2 > S3 miss-rate ordering holds (cluster CI); decided coverage >= 60% (V6 fact: BugsInPy coverage 28.5%); calibration ECE <= 0.05 | I, A, B, G |
| 14 | Unseen change types | Leave-mutation-family-out on DEV-N and the >= 6 new blinded H-M families; per-family reporting | Same as rows 4-10 | Pooled Det >= 0.75 x in-family Det; FAR on unseen families <= 0.15 (upper bound <= 0.20) at S >= S3 miss-rate cap 0.10 on that subset; no family with Det = 0 and N-rate > 30% without being flagged INSUFFICIENT; shortcut probe on labels (EP 6.1) <= 0.65 | I, H, A, J (if built) |

Cross-row checks: (i) per-row results must be reported with the same budget definitions as EP section 7; (ii) a row passes only if every sub-criterion passes; (iii) an arm that passes by emitting INSUFFICIENT for > 40% of pairs in the row fails the row's coverage sub-criterion even if its error rates look good.

---

## B. Phase gates

Common to all gates: unit tests pass in CI; all artifacts hashed into the ledger; no holdout files readable by the dev environment (checked by a custodian script); a gate review is signed by one implementer plus one independent reviewer. "Fail-fast" = stop forward work and invoke the fallback immediately; "fallback" = what is shipped/claimed instead.

### G0: Protocol freeze and data custody ready (before any V7 code beyond harness stubs)
- Quantitative: EP and this document hashed and recorded; custodian appointed; T0 declared; rubric kappa pilot >= 0.80 (CI lower >= 0.60; else repeat on fresh items); power analysis re-run with DEV-N variance estimates and targets amended pre-seal; project lists for H-R/H-X frozen and independence report produced (0 cross-set duplicate groups, 0 source-hash overlap); truth-harness smoke test on 50 items; analysis scripts exist and run end-to-end on a label-shuffled synthetic dataset.
- Fail-fast: kappa < 0.70 after two rubric iterations -> narrow scope to the classes where raters agree (move the rest to Undecided); fewer than 30 eligible H-R projects by the mining deadline -> H-R becomes descriptive-only and the success criteria in section C drop to V7-B at best (stated in advance).

### G1: Observation substrate (modules B, D, K, L)
- Unit/integration: determinism controls on; 3 repeated runs of 1000 deterministic units give bit-identical event logs >= 99.5%; content-addressing and provenance round-trip 100%; row 0 and row 2 pass; row 11 detection of injected nondeterminism >= 95%.
- Performance: median tracing overhead <= 20x native; peak memory <= 2 GB at p95; event-log size <= 50 MB at p95 per pair-run; per-pair isolation (no group-mode hangs); crash rate < 2%.
- Scientific (observation coverage, the V6 dominant failure): on the NON-PRISTINE BugsInPy and QuixBugs sets, used only as development targets, decided-pair coverage (a valid executed comparison on >= 1 input) >= 70% of pairs that are drivable by a pre-declared inclusion rule and >= 50% of all pairs (V6: 28.5% on BugsInPy; QuixBugs: 36 of declared pairs have no inputs; those must be INSUFFICIENT(UNDRIVABLE), not failures).
- Fail-fast: coverage < 50% of eligible pairs after one remediation cycle (<= 4 weeks) -> redefine scope to function-level drivable units and report the narrower eligibility; do not proceed to claims about "real bugs in general".
- Fallback: V7-lite = output-differential harness with sufficiency labels only (no state/graph views).

### G2: Exploration (module A) with the output-differential baseline
- Integration: strategies per EP 5 implemented as arms on the same harness; B1/B2 baselines implemented and tuned with equal effort.
- Scientific (DEV-N, hard stratum): V7 exploration >= B1 at 10/60/300 s (non-inferiority lower bound > -2pp) and activation uplift >= +15pp over undirected at 60 s on row 10(b) (paired lower > 0).
- Performance: scheduling overhead <= 10% of budget at median.
- Fail-fast: directed scheduling does not beat random on activation after two redesigns -> remove directed scheduling from the core (keep property-based + structure-aware + coverage-guided).
- Fallback: A = B2-equivalent.

### G3: Alignment, divergence, multi-view (modules F, G, H, and E if present)
- Integration: validation rows 1, 2, 3, 5, 6, 7 pass; alignment accuracy on a labelled set of 200 edited pairs >= 95% statement matches; locus accuracy (row 5) >= 85%.
- Performance: view construction + alignment <= 25% of per-pair budget at median, <= 60% at p95.
- Scientific (the retain-or-drop test, EP 5): each of E, F, G(dynamic anchors), H(state) is ablated on DEV-N; module stays core iff it meets the retain rule. Rows 4, 8, 9(a) pass.
- Fail-fast: row 3 FD > 3% (upper bound) after two cycles -> internal views may not feed the DIVERGENT verdict; they are restricted to annotations and scheduling guidance.
- Fallback: "output + control-flow-event divergence" only; drop E/F.

### G4: Evidence, uncertainty, decision (module I)
- Integration: rows 8 (honesty), 9, 10, 11, 12 pass; each verdict carries reason code, completeness metadata and sufficiency level 100%.
- Scientific (DEV-N calibration split, never used for tuning thresholds; S cutoffs fixed in EP): miss-rate ordering S1 > S2 > S3 with CI separation; ECE <= 0.05 against nominal caps S1 0.35 / S2 0.20 / S3 0.10; risk-coverage at coverage 0.7 not worse than B1 with activation-based abstention.
- Fail-fast: ordering violated or S3 miss rate > 0.20 on DEV-N -> remove S-level claims; ship binary {DIVERGENT, INSUFFICIENT} plus raw coverage numbers (no "no divergence observed" assurance language).
- Fallback: "V7-witness-finder" with no assurance claims.

### G5: Integrated scientific development gate and go/no-go for freeze
- Integrated system on DEV-N, validation matrix (all 14 + row 0 on suites generated with frozen seeds) and the NON-PRISTINE regression table (reported, not decisive).
- Conditions to proceed: all rows pass (rows 13/14 on leave-project/family-out DEV-N); H2 non-inferiority holds with lower bound > -2pp at all budgets; row 9(b) outcome recorded (H7 pre-test). If row 9(b) fails, the expected-claim set is downgraded to V7-B (section C) before sealing, as a recorded decision, not a post-hoc one.
- Sealing prerequisites: H-R and H-M sealed (hashes in ledger) BEFORE G5 closes; sealing is checked, not assumed.
- Performance: full holdout evaluation (all baselines, 5 seeds, 3 budgets) estimated <= 150 CPU-hours.
- Fail-fast: integrated V7 inferior to B1 by > 2pp at 60 s on DEV-N hard stratum (CI excluding 0) -> NO-GO to holdout; return to G2-G3 with a time box of 8 weeks; two consecutive failures -> terminate programme with a negative-result report.

### G6: Freeze and rehearsal
- System build hash, config, S cutoffs, budgets, seeds, analysis-plan hash recorded; validation suites regenerated with fresh seeds and rows pass again (held-out confirmation); rehearsal of the entire evaluation pipeline on a burnt set (e.g., NON-PRISTINE v8 test) completes with 0 crashes unrelated to units, <= 2% tool-error rate, and outputs byte-reproducible on a second machine (same Python version) and within tolerance on a different Python minor version (documented).
- Fail-fast: any holdout access found by the audit -> that holdout is burnt, H-X is promoted, recorded as an amendment class C item.

### G7: Single-shot sealed evaluation
- Procedure per EP 3.3: custodian unseals, run once with 5 seeds x 3 budgets, outputs hashed before labels are mounted, then scoring.
- No decision rules at this gate beyond executing the pre-declared analysis; deviations only for crashes (identical rerun, both reported).

### G8: Reporting, reproducibility, release
- All pre-declared metrics reported for all holdouts (EP 10); from-raw reproduction of every table identical (V6 achieved 2392/2392); independent rerun on a different machine and a different Python minor version within the declared tolerance (V6 left this open); amendment log complete; failure catalogue produced.
- Fallback: any unreproducible table is withdrawn from claims.

Optional gate G-J (only if J is built): J enters analysis only after G5; its claims are H10 and require paired improvement over conventional features on >= 2 sealed holdouts; otherwise J is not part of V7.

---

## C. Final V7 success criteria

### C.1 What declares V7 successful (two tiers; decided mechanically from the pre-declared analysis)

Common requirements for both tiers (all on sealed holdouts, pooled over H-R and H-M and also reported separately; "positive" = point estimate favourable; Holm-adjusted p < 0.05 where a test is named):
1. Validity: H1 holds (WVR >= 0.99, lower 95% >= 0.97; oracle-confirmed validity >= 0.95).
2. Non-inferior detection: V7 vs B1 and vs B2 at each of 10/60/300 s, lower paired bound > -2pp, on both H-R and H-M.
3. Reduced false assurance: FAR(V7) lower than B1's implicit pass by >= 25% relative or >= 5pp absolute at 60 s, Holm p < 0.05, positive in both holdouts; FAR at S3 <= 0.10 on H-R.
4. Risk-coverage: decided coverage on H-R >= 0.60; V7 risk at coverage 0.7 below B1's with Holm p < 0.05.
5. Calibration: S1 > S2 > S3 ordering and ECE <= 0.05.
6. Generalisation: row 13 and 14 criteria hold on sealed data (Det drop <= 10pp; unseen-family FAR <= 0.15).
7. Validation matrix: all rows pass on the G6 fresh-seed suites.
8. Reproducibility: G8 satisfied.
9. Time to first witness: RMST ratio <= 0.80 at 300 s vs B1 on the Div pairs, or Det superiority >= +5pp at 2 of 3 budgets on the hard stratum (H2/H3).

V7-A ("internal-state divergence adds information"): common requirements AND H7 (full V7 over V7 without internal-state views: Delta Det(300 s) >= +3pp or RMST ratio <= 0.85, paired Holm p < 0.05) positive on both H-R and H-M, AND row 9(b) passed.
V7-B ("sufficiency-aware witness-based differential testing"): common requirements met, H7 not met. This is a legitimate, narrower success; the report must say that internal-state views were not shown to add information.

### C.2 What is insufficient (never counts toward success)
- Any result on the five NON-PRISTINE sets (v8 test, v10, QuixBugs, BugsInPy, DEV), however good.
- Beating V5 or V6 only (V6 was at chance on real bugs).
- AUROC of anything; gains at only one budget; gains on one holdout only; gains confined to H-M (authored) with none on H-R, or vice versa.
- Point estimates without cluster CIs; p-values without Holm; inference with < 30 clusters.
- FAR improvements achieved with decided coverage < 0.60, or with INSUFFICIENT > 40% on the primary pairs.
- Passing the validation matrix without sealed-holdout confirmation.
- Detection gains explained by the shortcut probe (shortcut AUROC > 0.65 without the matched-subset replicating the effect).
- Results only under one budget unit (CPU-seconds and execution-count conclusions must agree in direction).

### C.3 NO-GO triggers (any one, on sealed holdouts, ends V7 as a claimed system; the report states the negative result)
- WVR lower bound < 0.95.
- Det inferiority vs B1 or B2 at 60 s with CI excluding -2pp (i.e., upper paired bound < -2pp) on either holdout.
- S3 miss rate > 0.20 on H-R, or ordering of S1/S2/S3 violated.
- Decided coverage on H-R < 0.40 (observation still dominates, as in V6) without a compensating validated INSUFFICIENT mechanism (INSUFFICIENT reason accuracy >= 95% and Div-rate in abstained within 10pp of decided).
- Det drop > 20pp vs DEV-N leave-project-out, or unseen-family FAR upper bound > 0.30.
- Confirmed holdout contamination with no unburnt H-X replacement completed.
- Reproducibility failure at G8 not repaired within a time box of 4 weeks.
- Outcome interpretation: if only the H7-level claim fails, V7 becomes V7-B, not NO-GO.

### C.4 Justification of thresholds (honest)
- 0.99 validity: replay validity is almost definitional for a witness system, so a high bar costs little; 0.97 lower bound allows sampling uncertainty at about 150 witnesses (one failure in 100 at n = 150 gives upper bound of ~0.035).
- -2pp non-inferiority, +5pp superiority: V6 facts show plain differential output comparison is already near ceiling where outputs are observable (v10 0.995, QB declared-evaluable 0.976), so headroom is in the hard stratum (about 27% of changed pairs in V6-type data). With the sizes in EP section 8, +5pp is at the edge of detectability; we prefer a modest, honest margin over a large one that would be unachievable or unfalsifiable. These margins are judgment, not derived from any prior V7 data.
- 25% FAR reduction: arbitrary but pre-declared; chosen so that, at plausible FAR of 0.15-0.25 for plain DT on real regressions, the absolute reduction is >= ~4-6pp, similar to the detectable effect.
- Coverage floors (0.60 success, 0.40 NO-GO): V6's 28.5% on BugsInPy and 76% abstention are the reference failure; 0.60 means "more than half of real units get an informative verdict"; 0.40 is an admission that observation is still the bottleneck. Both are judgment.
- Caps S1 0.35 / S2 0.20 / S3 0.10: calibration claims, not accuracy targets; chosen as conservative upper limits for miss rate; the claim of monotonic ordering is the stronger result. They may be revised only before G6 by amendment based on DEV-N evidence.
- Generalisation caps (10pp, 20pp): V6's leave-type-out drop for the generator-fingerprinted GBM was 0.972 -> 0.742; a 10pp budget is tighter than anything V6 achieved for a fingerprinting scorer and is deliberately demanding.
- Rows' numeric thresholds (0.5-1% FD, 85-95% detection) are engineering tolerances set so that a worthwhile system can meet them on constructed units; they are not claims about the real world, and none of them substitutes for sealed-holdout evidence.
- Unknowns: real-regression ground-truth noise may exceed the Undecided rate of V6-type data (8.7%); if Undecided > 15% the claim is restricted (EP 3.5).

---

## D. Anti-p-hacking rules and amendment procedure

D.1 Rules
1. Pre-registration: EP, this document, the analysis plan (scripts + hash), budgets, seeds, S cutoffs, baselines and their tuning budget are hashed into the ledger at G0 (protocol) and G6 (system/config). The primary metric set and direction cannot change after G6.
2. One confirmatory run per holdout (EP 3.3). Every evaluation run on any sealed set is recorded in an append-only run ledger (code hash, config, seeds, data hash). Exploratory runs on sealed data are forbidden; a violation burns the set.
3. Forbidden after unseal: changing thresholds, metrics, strata, exclusion rules, budgets, seeds, baselines; dropping pairs, projects, or seeds; switching between all-pairs and activated-only headlines; choosing the best of several seeds or budgets; re-labelling. All seeds and all budgets are always reported.
4. Exclusions are made by pre-declared inclusion rules only and listed in the excluded-units ledger; no exclusion may depend on system output.
5. Multiplicity: the primary family is fixed in EP section 2 and tested with Holm. Anything else is exploratory, reported with BH-adjusted values labelled exploratory.
6. Negative controls run at G6 and G7: label-shuffled pipeline (system outputs must be byte-identical when labels are withheld), identity/self-comparison (row 0), edit-size-only and family-only shortcut probes, reversed-input-order run. Any control failure invalidates the run.
7. Baseline parity: B1/B2 tuned with the same number of configurations on DEV-N as V7, recorded; weaker-than-effort baselines make the corresponding claim void.
8. Two-person rule: every threshold, rubric and analysis-plan change needs the author plus an independent reviewer; the custodian verifies hash chains.
9. Blinding: adjudicators are blind to system outputs; analysts running the confirmatory scripts do not edit them; scripts are run from the hashed checkout.
10. Reporting honesty: all hypotheses, including failed ones, are reported with the pre-declared consequence; "exploratory" and "non-pristine" labels are mandatory; post-hoc findings must be marked and cannot be used for success criteria. V6's precedent (selection rule operationalised after data was seen; "not fully preregistered") is explicitly the thing to avoid.

D.2 Amendment log procedure
- File: AMENDMENTS.md (append-only, hash-chained: each entry stores the SHA-256 of the previous entry), plus the diff of the changed document.
- Entry fields: ID (A-001...), date, author, reviewer, document and section changed, old text, new text, reason, trigger, data-exposure status (which datasets had been seen by whom at that time), class, expected effect on claims, and ledger hash of the new document version.
- Classes: A = clarification, no effect on any number or decision (reviewer sign-off); B = pre-data change (before G6 and before any sealed data exposure; allowed with documented rationale; thresholds must still be justified); C = post-data change (after G7 unseal or after any peek): results affected are labelled "exploratory, amended" and cannot support success criteria; D = emergency deviation (crash, contamination): requires custodian approval and must state precisely what was executed twice.
- Timing: B amendments are frozen at G6; after G6 only A and C/D are possible. After G7 only C and D.
- Disclosure: the report includes the full amendment log and a table "claims affected by amendments". An amendment never deletes the original text.
- Deviations (executed differently from the protocol) are logged in the same file with class D.
- Sample-size changes (e.g., fewer than 30 eligible projects) are class B before sealing, class C after.

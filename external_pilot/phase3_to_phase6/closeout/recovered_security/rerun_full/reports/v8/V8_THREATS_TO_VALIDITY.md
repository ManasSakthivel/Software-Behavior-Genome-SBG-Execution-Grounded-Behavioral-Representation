# V8 threats to validity (development-phase status)
1. **Data are design-exposed and non-independent.** All V8 numbers come from the 321/312 Phase 2 development pairs (labels are generator or construction labels; 258 labelled; 44% of labelled pairs are one project, quixbugs; the quixbugs_neg arm is y=0 by construction). Nothing is independent validation; no final holdout exists and none was touched.
2. **Underpowered.** Issued NDO at the V7-B gate coverage: 61; minimum detectable effect around 16 points (C report); cluster intervals are wide. Non-significant results are not evidence of no effect.
3. **Label validity.** Y relates to the declared observation boundary and generator labels, not adjudicated divergence; the blinded adjudication workflow is implemented but no adjudicator has labelled anything.
4. **Eligibility rule choice.** `changed_region_not_activated` and `budget_exhausted_s0` are soft blockers in the primary run (a strict run is reported as a sensitivity); the choice changes the eligible pool.
5. **ERS redundancy.** Deletion response (P1) applies to 16 of 312 records; the retained deltas may restate multiplicity. The influence feature `obs_react` is a proxy, not dynamic slicing.
6. **Post-hoc perturbations.** P2, P5, P6 were run only as recorded-evidence variants; real-execution interventions were not run. P8 passes by a policy rule.
7. **Provenance carries no signal** (every development pair is `declared`), so the provenance dimension was not tested.
8. **Trust.** The harness shares the program's address space; 2 of 15 forgery attacks still succeed (A08 stdout-divergence hiding, P04 unverified-field edit with sidecar rebinding); isolation is macOS-only; the hash chain is tamper-evident only.
9. **Machine load.** The development collection ran with other agents' processes (load up to 9); verdicts nevertheless agreed with E3 on 312/312.
10. **Family shift not testable**: no family diversity in the development data (deferred, not simulated).
11. **Calibration defects visible in the data**: out-of-fold slopes -1.8 to 0.3, no model beats the base-rate Brier by more than noise; thresholds chosen honestly on inner folds issue essentially nothing at risk targets 0.10 or 0.15.
12. **Statistical choices** (monotone-sign logistic, cluster bootstrap, within-fold rank matching) were fixed before the run by the design; the within-fold rank matching is a methodological choice that should be reviewed.

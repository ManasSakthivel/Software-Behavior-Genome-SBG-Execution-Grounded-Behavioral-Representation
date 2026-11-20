# V8 final readiness report

**Classification: V8 IMPLEMENTATION COMPLETE — NEGATIVE OR INCONCLUSIVE RESULT** (tooling for M1-M4 implemented and tested; on development data CEC and ERS showed no demonstrated gain; independent validation pending and gated). "Complete" applies to the implemented scope listed in V8_IMPLEMENTATION_STATUS.md, which has stated limits.

1. Fully implemented? The M1-M4 software scope, yes, with limits: no real-execution P2/P5/P6, no OS-level isolation, no live adjudication, no family-shift run, no holdout.
2. Milestones: M1-M4 complete as scoped.
3. ERS properties implemented and tested: all eight (irrelevant and duplicate invariance, relevant-evidence sensitivity, observation-loss sensitivity, divergence responsiveness, provenance, evidence-integrity, reproducibility sensitivity) post hoc; unit, metamorphic, negative (a quantity-credulous predictor is detected), boundary, replay and y-immunity tests.
4. Did all nine perturbations pass? On 312 development records: 0 failures after one disclosed fix (84 initial P8 failures resolved by a V8 trust gate rule; first run preserved). Many cases are not applicable (P1 296 of 312). Passing means behaved as pre-declared.
5. Information beyond coverage multiplicity? Not demonstrated. Multiplicity is the only consistent signal.
6. ERS improves calibration at matched coverage? Not demonstrated (log loss lower by about 0.03 in 3 seeds, all intervals include 0; matched-risk difference +1.6 points, CI [-6.5, 16.2]).
7. Versus every baseline: see V8_EXPERIMENTAL_RESULTS.md (B1 R 0.169; V7-B gate 0.213; coverage-only gate 0.121 at coverage 0.547; calibrated models no better than base-rate Brier).
8. Cluster CIs: wide (about +-15 points for risk differences) because about 35 projects carry issued NDO.
9. Dataset sufficient? No: 61 issued NDO at the reference coverage; MDE about 16 points; pilot/exploratory only; K5 scale is itself inadequate for 5-point effects (design document 07).
10. Blinded adjudication: implemented and tested; NOT independently executed.
11. Family shift: not tested (data lack family diversity; deferred).
12. Trusted collection under adversarial tests: 9 of 15 attacks detected, 3 blocked by the engine, 1 no effect, 2 still succeed; no security claim.
13. Remaining limitations: V8_THREATS_TO_VALIDITY.md.
14. Manuscript supported by actual evidence? The draft states only the development results and the negative framing (F1 with F2-F4); it is a markdown draft, not compiled IEEE format.
15. Gated behind explicit authorisation: Linux/Docker validation; external repository collection; human adjudication; the holdout and its unlock; real-execution perturbation campaigns on independent data; independent reproduction. See V8_PHASE3_AUTHORISATION_PACKAGE.md.

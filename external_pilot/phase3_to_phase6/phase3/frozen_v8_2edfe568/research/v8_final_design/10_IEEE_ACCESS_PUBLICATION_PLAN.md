# 10 IEEE Access publication plan

Acceptance cannot be guaranteed. The plan is to submit an honest manuscript whose claims match the evidence; every branch below is executable whatever the results.

## Working title
Evidence-Calibrated No-Divergence Verdicts for Differential Behavioural Regression Analysis: Project-Held-Out Calibration of False-Assurance Risk with Evidence-Perturbation Diagnostics

## Manuscript outline
1 Introduction (empty differences are ambiguous; false assurance; what is and is not claimed). 2 Problem and estimand (04). 3 Related work (01; honest attribution to checked coverage, BESTEST, behavioural gaps, selective prediction, conformal risk control, differential-testing tools). 4 Method: evidence profile, perturbation operators, response properties, calibration (05). 5 Trust architecture and its limits (V8-A; no tamper-proof claim). 6 Experimental protocol and pre-registration (06). 7 Dataset and adjudication (07). 8 Results (RQ1-RQ4, matched-coverage and risk-coverage figures, calibration plots, property tests, runtime). 9 Threats to validity (09). 10 Limitations and scope. 11 Reproducibility and artifact (hashed registration, scripts, evidence archives with sha256, replication package). 12 Conclusion.
## Contributions section (maximum claim)
1. A formal estimand for false assurance of no-divergence verdicts with an explicit adjudication-relative definition. 2. A change-conditioned evidence profile and pre-declared evidence-perturbation response properties (adaptations of checked coverage, behavioural adequacy and test-suite ablation, attributed). 3. An empirical evaluation of whether calibrated risk reduces false assurance at matched coverage on an independently adjudicated, project-split benchmark, including negative outcomes. 4. A replication package. Not claimed: first, novel intervention, novel calibration, equivalence checking, security isolation, generalisation beyond the benchmark.
## Related-work positioning
Complementary to test-generation tools (they find differences; this studies the reliability of finding none); complementary to behavioural-gap work (documentation-derived untested behaviours); adapts selective prediction and conformal risk control with stated assumptions.
## Evidence and artifact requirements
Pre-registration hash and time stamp; frozen scripts; raw evidence archives with sha256; environment record; label files with adjudicator agreement; contamination record; negative results included; numerical-claim verification tied to result files and independently recomputed.
## Submission readiness checklist
[ ] registration frozen before holdout scored; [ ] kappa >= 0.7; [ ] at least 60 projects (target 80) and at least 600 pairs or a pilot label; [ ] V8-A forgery suite passed on Linux/Docker or the paper states conditional trust; [ ] all baselines reported; [ ] matched-coverage analysis; [ ] property tests; [ ] cluster CIs; [ ] numerical claims verified; [ ] manuscript compiled and bibliography resolved; [ ] limitations and threats complete; [ ] no readiness or generalisation overclaim.
## Truthful fallback framings
F1 (CEC does not beat coverage-only calibration, H2 fails): report that evidence beyond changed-line coverage did not improve risk at matched coverage; contribution = estimand, matched-coverage methodology, adjudicated dataset, and the negative result (valuable because Phase 2 showed abstention alone can mimic improvement).
F2 (dataset below target): pilot study with intervals and the protocol; no calibration claim; explicit statement of required sample sizes.
F3 (D2 influence infeasible): profile without influence; the contribution narrows to activation, multiplicity, reproducibility, provenance.
F4 (V8-A not validated): all results conditional on non-adversarial programs; security stated as future work.
F5 (cannot run Phase 3): publish the Phase 2 exploratory manuscript with the corrections already made (honest negative framing: abstention explains the gain; no calibration shown) plus this design as methodology/future work.

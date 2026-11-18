# 00 Final research decision

Investigation HEAD: `8bd7d9da3de81c01194e5d8bc75d8f8c9ac0a984` (branch `research/v7b-final-validation`, tree clean, remote aligned at the start). Work branch: `research/v8-final-design` (documentation only; V7-B code, results, artifacts, frozen specs untouched).

## Decision: outcome B. CEC is defensible only after narrowing the central contribution.
Why not A: every individual component has close prior art. Evidence deletion to test the sensitivity of an adequacy measure is in Schuler & Zeller 2011 (assertion removal, read in full); leave-out evidence as an adequacy measure is BESTEST (Fraser & Walkinshaw 2015); influence on a check is checked coverage; selective risk and conformal risk control are established; abstention and risk-coverage are established; project-level grouping is standard. Why not C: a narrow contribution survives and is testable.
**What is not claimed:** novelty of evidence deletion/addition, of influence, of calibration methods, of risk-coverage, of abstention, of conformal control; "first"; equivalence; a statistical guarantee on conditional risk; causal claims; security isolation; generalisation.
## Final formulation (single)
**Title:** Evidence-Calibrated No-Divergence Verdicts for Differential Behavioural Regression Analysis.
**Research question:** Does calibrating the risk that a NO_DIVERGENCE_OBSERVED verdict is false from change-conditioned execution evidence, with evidence-perturbation responses, lower false assurance at matched decision coverage on project-held-out, independently adjudicated version pairs, compared with coverage-only calibration and the fixed V7-B gate?
**Contribution statement (maximum):** (i) a precise, adjudication-relative estimand for false assurance of empty-difference verdicts; (ii) a change-conditioned evidence profile with pre-declared perturbation-response properties used as validity tests and as a candidate predictor, adapting checked coverage, behavioural adequacy and test-suite ablation to the differential setting; (iii) a matched-coverage evaluation protocol that separates calibration from abstention, motivated by the Phase 2 finding that V7-B's false-assurance reduction was entirely abstention; (iv) an adjudicated benchmark and replication package if built.
**Exactly what is novel (candidate, unproven):** the combination of the estimand, the use of perturbation responses as predictors of false-assurance risk (hypothesis H3, can fail), and the matched-coverage, project-held-out evaluation in this setting. Weakly novel.
**Adapted from prior work:** evidence deletion/addition, influence, behavioural adequacy, selective classification, calibration methods, conformal risk control, grouped resampling.
**Engineering:** V8-A trusted collection, provenance schema, harness extension, dataset tooling.
**Unsupported now:** any calibration result, any guarantee, any advantage of response features, any real-project result, the security of evidence collection.
**Strongest reviewer objection:** "this is checked coverage and selective prediction combined; the response features may be redundant with coverage multiplicity." Method answer: baselines 7, 9 and a multiplicity-only baseline; the hypothesis can fail and the negative result is reported.
**What falsifies the central claim:** H2 or H3 not supported on grouped CV and holdout, or calibration slope/intercept intervals excluding 1/0 materially.
**Terminology:** "counterfactual" is kept in the working name only; the formal term is evidence perturbation (recomputation of the decision procedure on altered evidence; no causal claim about programs).
## Facts about the repository and data that shaped the design
Phase 2 development data: V7-B wrong share among issued NDO 13/61 versus B1 24/130; false-assurance reduction entirely abstention (11 of 11). The K5 targets (60 projects, 250 divergent pairs) are not adequate for narrow calibration intervals (07). The in-process forgery limitation (Phase 2 red team M-4) makes Phase 3 trusted collection a precondition for any security statement.
## Research design phase: CLOSED. Next stage is execution (11) and publication preparation (10).

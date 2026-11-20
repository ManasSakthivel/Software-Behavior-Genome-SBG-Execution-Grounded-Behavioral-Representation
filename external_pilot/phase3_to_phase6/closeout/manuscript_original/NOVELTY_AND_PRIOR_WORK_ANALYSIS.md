# Novelty and prior-work analysis (second round)

This document supports §II and Tables 2–3 of the paper. It is new in round 2, is linked from `README.md` and `SECOND_ROUND_SCIENTIFIC_REVISION.md`, and supersedes the draft gap analysis in `audit/literature_tables.md`. Every reference statement is limited to the "Supports" column of `LITERATURE_COMPARISON_REGISTER.md`. No reference was added in round 2, and no prior tool was executed.

## 1. The question and the gap

**Question.** Given the evidence behind a specific no-divergence (NDO) verdict on a version pair, what is the probability that an independent examination within a declared observation boundary O and budget B would find a divergence? And can that probability be estimated from the evidence, with an estimator whose behaviour under evidence degradation is itself testable?

**Gap.** We did not find any single work that provides all three of the following:
1. a *per-verdict conditional* false-assurance estimand for NDO, scoped to (O, B, C) and distinct from equivalence;
2. an estimate of that risk from a *change-conditioned* evidence profile that includes integrity and provenance;
3. a *label-free property protocol* that tests the estimator's response to controlled evidence degradation, with N/A accounting, abstention credit and integrity positive controls.

## 2. Closest prior work, ranked by proximity

| Rank | Work | Why it is close | Exact distinction | Type of comparison |
|---|---|---|---|---|
| 1 | SemaDiff (Ayub et al., 2026 preprint) | Measures how often an "all generated tests agree ⇒ semantics-preserving" label is correct: about 76% on 183 annotated commits | Reports dataset-level accuracy of an agreement rule. It does not condition on per-verdict evidence, abstain, or test response to degraded evidence | Conceptual; its rule is our baseline B1 |
| 2 | Evans & Savoia 2007 | States that an empty difference set does not prove equivalence | Gives no estimate of how often the empty set misleads | Conceptual; B1 |
| 3 | Selective classification (El-Yaniv & Wiener; Geifman & El-Yaniv) | Defines selective risk at coverage and risk-targeted thresholds | Does not define software evidence; its guarantees assume i.i.d. data | Conceptual; B6 and matched coverage follow it |
| 4 | Checked coverage (Schuler & Zeller 2011) | Validates an adequacy measure by deleting evidence (assertions) and observing the response | Targets a suite score, not a verdict-risk estimator; has no property set | Conceptual; P1 credited |
| 5 | Mutation analysis (Jia & Harman; Just et al.) | Evaluates the strength of passing outcomes | Covers one version, gives a score rather than a probability, and uses seeded faults | Conceptual |
| 6 | Pseudo-tested methods (Niedermayr et al.; Vera-Pérez et al.) | Covered but unchecked code means passing tests can give false assurance | No version pair, no probability | Conceptual |
| 7 | DiffTestGen (Hu et al., 2026 preprint) | Exposes differences in 78.2% of 463 PRs, leaving 21.8% non-exposing | Does not estimate the reliability of the non-exposing cases | Conceptual |
| 8 | Metamorphic testing (Chen et al.) | Tests without an oracle via relations under input transformations | Its relations are on program inputs; ERS relations are on a risk estimator's evidence | Conceptual |
| 9 | Conformal risk control (Angelopoulos et al.; Bates et al.) | Distribution-free risk control for thresholds | Requires exchangeability, which project clustering violates | Conceptual; implemented as an exploratory option |
| 10 | in-toto / SLSA / reproducible builds | Signed provenance and integrity of artifacts | Attests artifacts, not runtime observations, and does not feed a risk estimate | Conceptual |
| 11–15 | BERT, DiffGen, shadow symbolic execution, NEZHA, Testora | Find divergences between versions | Do not interpret or quantify the empty outcome | Conceptual |

## 3. What is new, what is adapted, what is not claimed

| Element | Status | Basis |
|---|---|---|
| Estimand R = P(F=1 \| NDO) for version-pair verdicts, relative to (O, B, C), with complete-case / worst-case / optimistic variants | **Adapted** (selective risk applied to a new object) and **new in its scoping**: O, B, unresolved cases, explicit separation from PROGRAM_EQUIVALENCE (Remark 1) | §III |
| Proposition 1 (random abstention preserves expected risk) | **Not new mathematically** (an elementary expectation argument). It is used to justify B6 and matched coverage | §III |
| Change-conditioned profile with multiplicity μ over observation fingerprints, plus integrity, provenance and environment | **Adapted** (change-directed adequacy) **plus new feature definitions**. Predictive value is **not demonstrated** | §IV, RQ4 |
| Integrity-first verdict order (trust gate before witness) | **New design decision** motivated by an ERS result. Its cost (denial of a true DIV) is stated | §IV, RQ2 |
| ERS: eight properties, three classes, executable criteria, N/A and abstention-credit accounting | **New as a property set** for verdict-risk estimators. It builds on evidence deletion and metamorphic relations | §V |
| Remark 2 (an always-abstaining procedure conforms trivially) | New observation within this framework, used to require coverage alongside ERS | §III |
| Matched-coverage protocol against random abstention | **Established practice** in selective prediction, applied rigorously here | §VII |
| Trusted collection (tee capture, HMAC frames, anchored evidence, isolated validator) | **Engineering adaptation** of known integrity mechanisms. Novelty is not claimed | §VI |
| "First" or "only" claims | **None made**. The paper says "we did not find" | §II-I |

## 4. Defensible novelty statement (as used in the paper)

> Each ingredient adapts an established idea: selective risk, change-directed adequacy, evidence deletion, metamorphic relations and attestation. We claim no novelty for any single one. The contribution is their integration into an estimand, a decision procedure and a conformance test for NDO verdicts, together with an evaluation that reports where the combination did and did not help.

## 5. Risks of overstatement and how they were handled

| Risk | Handling |
|---|---|
| Reading SemaDiff as "no prior quantification" | The paper credits SemaDiff's dataset-level accuracy explicitly, as the closest work |
| Presenting ERS as metamorphic testing of programs | The paper states that ERS relations act on the estimator's evidence, not on program inputs |
| Presenting P1 as new | Evidence deletion is credited to Schuler and Zeller |
| Claiming risk-control guarantees | No finite-sample guarantee is claimed; the exchangeability violation is stated |
| Claiming benchmark breadth | The five-dataset artifact is excluded; Table 11 shows literature sizes next to what the artifact contains |
| Claiming predictive improvement | RQ4 reports a non-demonstrated, underpowered result |

## 6. Mapping of paper streams to register sections

| Paper stream | Register section(s) |
|---|---|
| A Differential / regression testing | (A) differential testing; LLM-era tools |
| B Oracles / metamorphic | Oracle and metamorphic entries |
| C Adequacy / sufficiency | Coverage, mutation, checked coverage, pseudo-tested, BESTEST |
| D Selective prediction | Selective prediction and calibration |
| E Conformal risk control | Conformal / RCPS entries |
| F Integrity / provenance | in-toto, SLSA, reproducible builds |
| G Perturbation-based conformance | Checked coverage, mutation, metamorphic (cross-listed) |
| H Reproducibility / empirical SE | Flaky tests; benchmarks and the benchmark critique |

## 7. What would strengthen novelty (not done; needs new work)

- An empirical head-to-head with an agreement-rule tool (for example SemaDiff-style generated tests) on an adjudicated corpus, measuring per-verdict risk at matched coverage.
- Replacing the reachability proxy with checked-coverage or dynamic-dependence features, and testing whether ERS-conformant estimators then gain predictive value.
- Applying the ERS protocol to third-party estimators, such as LLM-based "is this change safe" judges, to test the transferability claim.

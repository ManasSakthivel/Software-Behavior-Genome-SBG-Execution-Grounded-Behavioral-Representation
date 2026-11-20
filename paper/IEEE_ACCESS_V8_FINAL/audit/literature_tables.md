# Literature tables: draft content (SBG V8, IEEE Access)

Keys refer to `../references.bib`. Verification details are in `../LITERATURE_COMPARISON_REGISTER.md` (all re-verified 2026-11-19).

Cell legend:
- **Yes**: the capability is a stated, evaluated contribution of that line of work.
- **Partial**: addressed indirectly, in a narrower form, or as a side effect.
- **No**: outside the scope of that line of work.
- **Not established**: we found no evidence either way in the sources read. This is not a claim that it is absent.

The SBG V8 column records what V8 is *designed* to do. Whether each capability works is an empirical question, answered in the Results section, not here.

---

## Table 1: Capability comparison

| Capability | Differential testing | Coverage-based adequacy | Mutation-based adequacy | Pseudo-tested / checked coverage (oracle adequacy) | Selective prediction / conformal | Supply-chain provenance (in-toto/SLSA) | SBG V8 |
|---|---|---|---|---|---|---|---|
| **Detects observable divergence** | **Yes**: old/new or multi-implementation runs flag output differences [mckeeman1998differential, evans2007differential, palikareva2016shadow, jin2010automated] | **No**: measures execution, not output differences [zhu1997software] | **Partial**: a killed mutant is a divergence between the original and a *seeded* variant, not between real versions [jia2011analysis] | **No**: measures whether results are checked [schuler2011assessing] | **No**: generic ML framework | **No**: attests artefact and step integrity, not behaviour [torresarias2019intoto] | **Yes** (design): DIVERGENT_OBSERVABLE within a declared observation boundary |
| **Evaluates empty difference sets** | **Partial**: the ambiguity of an empty set is noted [evans2007differential]. SemaDiff measures the accuracy of "all tests agree → preserving" labels against manual annotation [ayub2026semadiff] | **Partial**: coverage is used to judge whether a passing suite is adequate, but coverage correlates only weakly with effectiveness [inozemtseva2014coverage, gopinath2014code] | **Yes**: mutation analysis asks whether a passing suite *would* have detected seeded faults, so it directly assesses the strength of "no failure observed" [jia2011analysis, just2014mutants]. Limited by how well mutants represent real faults [papadakis2018mutation] | **Yes** (oracle side): pseudo-tested methods are covered code whose removal leaves tests passing, i.e. empty failure sets that mean nothing [niedermayr2016will, veraperez2019comprehensive] | **Partial**: risk among *accepted* predictions is the core quantity [geifman2017selective], but there is no software notion of a difference set | **No** | **Yes** (design): every NDO is scored for false-assurance risk |
| **Explicit false-assurance estimand** | **No**: no technique we read defines P(wrong \| no divergence). SemaDiff reports overall accuracy, not a conditional risk [ayub2026semadiff] | **No** | **Partial**: the mutation score is a proxy for detection probability over a mutant population, not a conditional error rate of passing verdicts [papadakis2019mutation] | **No** | **Yes** (generic): selective risk = P(error \| accepted) [elyaniv2010foundations, geifman2017selective]. Conformal methods control expected loss [angelopoulos2024conformal] | **No** | **Yes** (design): R = P(verdict wrong \| NDO issued), defined relative to the observation boundary. This adapts selective risk [elyaniv2010foundations] |
| **Evidence diversity characterization** | **Partial**: NEZHA uses δ-diversity of *behaviours* to guide fuzzing [petsios2017nezha] | **Partial**: multiple coverage criteria [zhu1997software] | **Partial**: mutant-kill diversity across operators [papadakis2019mutation] | **Partial**: behavioural (model-inference) adequacy [fraser2015assessing] | **No** | **No** | **Yes** (design): multiplicity, repetition, effective diversity, provenance independence |
| **Evidence perturbation response** | **No** | **Not established** | **Partial**: mutation perturbs the *program*, not the evidence [jia2011analysis] | **Partial**: assertion removal is used to validate checked coverage, a deletion-sensitivity test of a metric [schuler2011assessing]. Leave-out (k-fold) evidence in BESTEST [fraser2015assessing] | **Not established**: robustness under data perturbation exists in ML, but was not reviewed here | **No** | **Yes** (design): ERS with P1–P9 and 8 pre-declared properties. Deletion (P1) adapts [schuler2011assessing] |
| **Provenance sensitivity** | **No** | **No** | **No** | **No** | **No** | **Yes**: provenance is the object of verification [torresarias2019intoto, slsa2023spec] | **Yes** (design): degrades the verdict under P7 provenance degradation |
| **Integrity sensitivity** | **No** | **No** | **No** | **No** | **No** | **Yes**: tampering detected through signed link metadata [torresarias2019intoto]; reproducible builds [lamb2022reproducible] | **Yes** (design): P8 integrity violation must block NDO |
| **Matched-coverage risk comparison** | **No** | **Partial**: studies control for suite size or coverage when relating coverage to effectiveness [inozemtseva2014coverage] | **Partial**: suite-size-controlled correlations [papadakis2018mutation] | **Partial**: checked coverage compared with statement coverage [schuler2011assessing] | **Yes** (generic): selective risk at fixed coverage / risk–coverage curves [elyaniv2010foundations, geifman2017selective] | **No** | **Yes** (design): NDO risk compared at matched abstention coverage |
| **Abstention-aware verdicts** | **Partial**: some tools report "unknown" or timeout outcomes (e.g., verification); no calibrated abstention in the testing tools read [palikareva2016shadow, pradel2026testora] | **No** | **No** (equivalent mutants are an analogous "undecidable" class [papadakis2019mutation]) | **No** | **Yes**: reject option / selective classification [chow1970optimum, geifman2017selective, hendrickx2024machine] | **Partial**: verification fails closed (reject) on bad attestations [torresarias2019intoto] | **Yes** (design): INSUFFICIENT verdict |

Fairness notes for the caption:
1. Mutation analysis *is* an established way to evaluate passing (empty-failure) outcomes. SBG's distinction is that its conditioning is version-pair and observation-boundary specific, and that it targets a calibrated conditional error rate. It is not that SBG is the first to question passing outcomes.
2. Regression and equivalence verification [godlin2009regression, lahiri2012symdiff, felsing2014automating, malik2021automatically] gives *proofs* of no divergence and is outside this table, because it does not produce observational verdicts.

---

## Table 2: Methodological comparison (representative approaches)

| Approach | Objective | Input evidence | Decision mechanism | Output | Key assumptions | Evaluation methodology | Limitations |
|---|---|---|---|---|---|---|---|
| Differential testing / BERT [evans2007differential, jin2010automated] | Expose behavioural changes between versions | Generated unit tests run on old and new versions | Value comparison of outputs/state | Set of behavioural differences for developer review | Old version is an acceptable reference; observed outputs capture relevant behaviour | Case studies on Java programs with known changes | An empty set is uninterpreted; no adequacy or risk estimate |
| Shadow symbolic execution [palikareva2016shadow, kuchta2018shadow] | Generate inputs that make versions diverge | Unified (annotated) program, symbolic execution | Constraint solving on divergent branches | Divergence-revealing inputs | Symbolic execution scales to the patch neighbourhood | Patches from CoREBench (C programs) | Path explosion; non-divergence is not quantified |
| Testora / DiffTestGen [pradel2026testora, hu2026difftestgen] | Detect regressions in PRs | LLM-generated tests, PR text, change coverage | Differential execution + LLM intent classification | Regression reports per PR | LLM output and PR text are informative | Real PRs from Python projects; developer confirmation | No calibrated statement for PRs without differences; LLM cost and nondeterminism |
| SemaDiff [ayub2026semadiff] (preprint) | Classify commits as semantic-preserving vs. changing | LLM-generated dependent classes + generated tests on pre/post versions | All tests agree → preserving | Binary commit label | Generated tests reach the changed code | 183 manually annotated Java commits; accuracy/precision | Agreement treated as sufficient; no evidence-conditioned risk or abstention |
| Mutation analysis [jia2011analysis, just2014mutants] | Estimate fault-detection strength of a suite | Suite + seeded mutants | Kill/survive per mutant | Mutation score | Mutants couple to real faults; equivalent mutants handled | Correlation with real-fault detection (e.g., Defects4J) | Equivalent mutants; cost; score is a proxy, not a conditional risk |
| Checked coverage / pseudo-tested [schuler2011assessing, veraperez2019comprehensive] | Assess oracle (checking) adequacy | Dynamic slices from checks / extreme mutation | Influence on assertions / tests still pass | Checked-coverage %, list of pseudo-tested methods | Assertions are the oracle | Java projects; assertion removal; developer feedback | Single version; no probability semantics |
| BESTEST_CV [fraser2015assessing] | Behavioural adequacy of test sets | Test executions → inferred models | k-fold CV accuracy of inferred model | Adequacy score; generated test sets | Model learnability reflects behavioural coverage | 18 Java classes; mutation score against branch, data-flow and mutation criteria | Small evaluation; primitive types; learner choice |
| Selective classification / conformal risk control [geifman2017selective, angelopoulos2024conformal] | Bound error among accepted predictions | Calibration set of scores and labels | Threshold chosen to meet risk target | Accept/abstain rule with a guarantee | i.i.d./exchangeable calibration data; monotone loss (CRC) | Vision/NLP benchmarks | Marginal guarantees; exchangeability is violated by project clustering |
| **SBG V8** | Estimate and limit false-assurance risk of NDO verdicts | Change-conditioned evidence profile from containerised old/new runs with trusted capture | Calibrated risk model (CEC) + abstention threshold; ERS property checks | DIVERGENT_OBSERVABLE / NDO (with risk) / INSUFFICIENT | Adjudicated ground truth within a declared observation boundary; project-level exchangeability for any guarantee | Project-held-out evaluation; matched-coverage comparison; ERS perturbations P1–P9 | Results are boundary-relative (no equivalence claim); depends on the adjudication protocol and the benchmark |

---

## Table 3: Benchmark comparison (Literature-reported)

All numbers are those reported in the cited papers ("Literature-reported"). They are not re-measured, and they are **not ranked against SBG**.

| Benchmark | Language | Original size (benchmark paper) | Representative study using it | What that study measured |
|---|---|---|---|---|
| Defects4J [just2014defects4j] | Java | 357 real bugs from 5 projects (ISSTA 2014). Later releases are larger | [just2014mutants] | Whether mutant detection correlates with real-fault detection, and the coupling of real faults to mutants |
| | | | [paul2026beyond] (preprint) | Documented behaviours left untested ("behavioural gaps") in 10 Java libraries drawn from Defects4J |
| BugsInPy [widyasari2020bugsinpy] | Python | 493 real bugs from 17 projects | [rezaalipour2024empirical] | Effectiveness of 7 fault-localisation techniques on 135 faults from 13 projects |
| Bears [madeiral2019bears] | Java | 251 bugs from 72 projects (v1.0, CI-mined) | [madeiral2019bears] | Benchmark construction via CI build states. Maintainers later report 118 still-buildable bugs (repository statement, Sep 2023) |
| BugSwarm [tomassi2019bugswarm] | Java, Python | 3,091 fail-pass CI build pairs, containerised | [durieux2019critical] (preprint) | Suitability for fault localisation/repair: 112/3,091 pairs meet their criteria |
| | | | [tomassi2019note] (preprint) | Rebuttal disputing several of the critique's claims |
| Bugs.jar [saha2018bugsjar] | Java | 1,158 bugs from 8 projects | [saha2018bugsjar] | Dataset construction and diversity (no separate downstream study selected) |

Caption note: these benchmarks label *faults* (or failing builds), not adjudicated divergence within a declared observation boundary. Using them for SBG requires the adjudication protocol in `research/v8_final_design/07_DATASET_AND_ADJUDICATION_PROTOCOL.md`.

---

## Research gap statement

Differential and regression testing techniques [mckeeman1998differential, evans2007differential, palikareva2016shadow, jin2010automated, pradel2026testora, hu2026difftestgen] are designed to expose differences between versions, and they mostly leave unquantified how reliable an empty difference set is. Evans and Savoia noted that such a result is ambiguous [evans2007differential]. Recent work measures the accuracy of agreement-based "semantic-preserving" labels at the level of a whole dataset [ayub2026semadiff]. Separately, adequacy research evaluates whether passing suites would detect faults: through coverage [inozemtseva2014coverage], mutation [just2014mutants, papadakis2018mutation], oracle checking [schuler2011assessing, niedermayr2016will] and behavioural adequacy [fraser2015assessing]. Selective prediction and conformal methods provide estimands and guarantees for error among accepted predictions [elyaniv2010foundations, geifman2017selective, angelopoulos2024conformal]. In the sources we reviewed, we did not find a method that combines these strands. That would mean defining the conditional false-assurance risk of a no-divergence verdict on a specific version pair within a declared observation boundary, estimating that risk from a change-conditioned evidence profile that includes provenance and integrity signals, and checking that the estimate responds as expected to controlled perturbations of the evidence. SBG V8 targets this combination. Its components (evidence deletion, selective risk, provenance attestation) are adaptations of established ideas. Any contribution lies in their integration and in the empirical test of whether the integration reduces false assurance at matched coverage, not in any single component.

---

## Closest prior work a reviewer may cite against novelty

1. **SemaDiff** [ayub2026semadiff] (preprint, 2026). It runs generated tests on pre/post versions, issues "semantic-preserving" when all agree, and reports how accurate that label is (about 76% on 183 annotated commits). This is the nearest empirical evaluation of no-difference verdicts.
   *How SBG differs:* SBG estimates a per-verdict *conditional* risk from an evidence profile instead of a dataset-level accuracy. It abstains (INSUFFICIENT) when evidence is weak, and it tests calibration responses under evidence perturbations. SBG must also report a SemaDiff-style "agree → NDO" rule as a baseline.

2. **Checked coverage and pseudo-tested methods** [schuler2011assessing, niedermayr2016will, veraperez2019comprehensive], together with **mutation analysis** [jia2011analysis, just2014mutants]. These already ask whether a passing outcome is meaningful, and Schuler & Zeller already use evidence deletion (assertion removal) to validate a metric.
   *How SBG differs:* SBG works on old/new version pairs at a declared observation boundary rather than on a single version with assertions. It outputs a calibrated probability rather than a score. It extends the perturbation set beyond deletion to augmentation, masking, provenance and integrity. P1 must be credited to Schuler & Zeller.

3. **BESTEST** [fraser2012behaviourally, fraser2015assessing], together with **selective classification** [geifman2017selective]. BESTEST already gives an execution-derived, held-out (k-fold) adequacy estimate. Selective classification already gives risk-targeted abstention.
   *How SBG differs:* BESTEST measures adequacy for test generation on single units, and it is not a verdict-risk estimator. Selective classification is domain-generic. SBG's contribution, if supported by results, is applying both to the NDO verdict with change conditioning and with integrity/provenance evidence. Formal guarantees need project-level exchangeability, which must be stated as an assumption.

Additional reviewer risk: Testora/ORION/PatchGuru [pradel2026testora, fu2026orion, lecong2026patchguru] report regression-detection precision/F1, and a reviewer may ask why SBG is not compared with them. The response is that they target the DIVERGENT side, and none of them issues a risk-scored "no divergence" verdict. A combined pipeline (their tests as SBG evidence) is a fair suggestion for future work.

---

## BESTEST: search result (task 1e)

**Verified.** "BESTEST" (BEhavioural Software TESTing) is the name of Gordon Fraser and Neil Walkinshaw's behavioural-adequacy approach:
- BESTEST_PAC, in "Behaviourally Adequate Software Testing", ICST 2012, doi:10.1109/ICST.2012.110;
- BESTEST_CV (k-fold cross-validation), in "Assessing and Generating Test Sets in Terms of Behavioural Adequacy", STVR 25(8):749–780, 2015, doi:10.1002/stvr.1575.

Both names were confirmed in the STVR full text (White Rose repository PDF, extracted 2026-11-19), which also gives the prototype URL evosuite.org/bestest and an evaluation on 18 Java classes. There is no standalone paper titled "BESTEST". Cite the two papers above. Crossref "BESTEST" hits are the unrelated clinical *Balance Evaluation Systems Test*.

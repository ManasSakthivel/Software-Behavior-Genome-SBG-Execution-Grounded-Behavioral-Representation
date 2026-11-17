# Literature verification, group 2 (exploration, evaluation, uncertainty)

Verified 2026-11-17. Method: Crossref API records (metadata), arXiv abs pages (abstract), one web search for some abstracts. NO paper was read in full text. Access levels are therefore METADATA ONLY or ABSTRACT ONLY (abstract paraphrase from arXiv/search snippets). "Method / setup / limitations" below that are not from an abstract are marked "background" (my prior knowledge, NOT VERIFIED here). "Inference" marks my own reasoning about SBG.

Common SBG contrast: SBG compares two versions by execution, gates the verdict on whether the changed region was actually exercised (sufficiency), emits a 3/4-way verdict including "insufficient/abstain", and controls evaluation artefacts. None of the works below states a sufficiency-gated cross-version verdict; absence in what I read (abstracts only) is weak evidence.

## A. Exploration / test generation

**AFL / AFLGo.** Bohme, Pham, Nguyen, Roychoudhury. "Directed Greybox Fuzzing." ACM CCS 2017, pp. 2329-2344 (Crossref, verified). Peer-reviewed. Access: METADATA + search-snippet summary (no abstract page, no full text). Method (snippet): simulated-annealing power schedule gives more energy to seeds closer to target locations. Reported: beats directed symbolic-execution whitebox fuzzing and undirected greybox fuzzing; 39 bugs found, 17 CVEs; applications to patch testing and crash reproduction. Limitations: NOT VERIFIED (background: distance is a static call-graph approximation). SBG difference: AFLGo's goal is reaching/crashing at a target (patch testing = reach changed lines); it outputs bugs, not a behavioural-difference verdict nor an "unreached" verdict. Inference: it is the natural baseline/engine for SBG's activation step. AFL itself: no paper; not citable as a paper (original Zalewski docs NOT VERIFIED).

**Zest / JQF.** Padhye, Lemieux, Sen, Papadakis, Le Traon. "Semantic Fuzzing with Zest." ISSTA 2019 (arXiv:1812.00078; ACM DOI 10.1145/3293882.3330576 per arXiv comments). Peer-reviewed + preprint. Access: ABSTRACT ONLY. Method: turns QuickCheck-style generators into deterministic parametric generators; parameter mutation = structural input mutation; feedback = coverage + input validity. Setup: 5 Java programs (Maven, Ant, BCEL, Closure, Rhino); 1.03x-2.81x as many branches in semantic-analysis stages as AFL and QuickCheck; 10 new bugs. Limitations: NOT VERIFIED (background: needs a generator). SBG difference: generates valid inputs; no cross-version comparison or sufficiency verdict. Inference: inputs inherit generator distribution, so a generator-identity risk for SBG. CORRECTION: prior review's DOI 10.1145/3339069 is the replication package; the paper is 10.1145/3293882.3330576 and authors include Papadakis and Le Traon.

**Hypothesis.** MacIver, Hatfield-Dodds, and many contributors. "Hypothesis: A new approach to property-based testing." JOSS 4(43), Nov 2019, DOI 10.21105/joss.01891 (Crossref). Peer-reviewed (JOSS software paper) + documentation. Access: METADATA; docs landing page read (hypothesis.readthedocs.io): says only that you describe a range of inputs and it randomly chooses inputs, including edge cases; shrinking/database/health-check details NOT VERIFIED (only link titles seen). SBG difference: property-based generation, user-written properties; no version comparison. Inference: possible input engine for Python.

**QuickCheck.** Claessen, Hughes. "QuickCheck: a lightweight tool for random testing of Haskell programs." ICFP 2000, pp. 268-279 (Crossref; DOI 10.1145/351240.351266). Peer-reviewed. Access: METADATA ONLY. Claim content NOT VERIFIED here (background: random testing against stated properties). CORRECTION: prior review had only the 2011 SIGPLAN Notices reprint (10.1145/1988042.1988046); original now verified.

## B. Regression-directed / differential fuzzing

**DifFuzz.** Nilizadeh, Noller, Pasareanu. "DifFuzz: Differential Fuzzing for Side-Channel Analysis." arXiv:1811.07005 (v2 Feb 2019); ICSE 2019 (venue per prior review's DOI 10.1109/icse.2019.00034, not re-fetched; arXiv page lists no venue). Access: ABSTRACT ONLY. Method: two executions, resource-guided heuristics to maximise difference in resource use between secret-dependent paths; Kelinci/AFL, Java; compared with Blazer, Themis. Note: abstract says "two versions of a program" in the sense of runs differing in the secret, not code versions (inference from abstract wording; not verified in text). SBG difference: resource side channels, not functional cross-version change.

**NEZHA.** Petsios, Tang, Stolfo, Keromytis, Jana. IEEE S&P 2017, pp. 615-632 (Crossref; all 5 authors verified). Peer-reviewed. Access: ABSTRACT-LEVEL (search snippet). Method: delta-diversity, a measure of behavioural asymmetry across multiple test applications; gray-box and black-box input generation. Reported: ~52x Frankencerts, ~27x Mucerts discrepancy rate, ~6x more semantic bugs per input than AFL adapted; 778 new discrepancies. SBG difference: cross-implementation of one spec; no notion of intended change or sufficiency. Inference: its claim about "flagging intended changes" in version comparison is my reasoning, not stated.

**Badger.** Noller, Kersten, Pasareanu. "Badger: complexity analysis with fuzzing and symbolic execution." ISSTA 2018, pp. 322-332 (Crossref). Access: METADATA ONLY (title says complexity analysis). Content beyond title NOT VERIFIED. Not about functional semantics (from title).

**Regression/patch-directed fuzzing beyond AFLGo (1dVul, Skyfire etc.):** NOT SEARCHED / NOT VERIFIED. Prior review's 1dVul/Skyfire mention is unsupported.

## C. Metamorphic testing

**Segura, Fraser, Sanchez, Ruiz-Cortes.** "A Survey on Metamorphic Testing." IEEE TSE 42(9):805-824, 2016, DOI 10.1109/tse.2016.2532875 (Crossref). METADATA ONLY.
**Chen, Kuo, Liu, Poon, Towey, Tse, Zhou.** "Metamorphic Testing: A Review of Challenges and Opportunities." ACM CSUR 51(1), 2018 (online Jan 2018), pp. 1-27, DOI 10.1145/3143561 (Crossref). METADATA ONLY.
Contents NOT VERIFIED (background: metamorphic relations replace the oracle; relations usually hand-authored). SBG difference (inference): cross-version comparison is a differential oracle, not a metamorphic relation over one version's inputs.

## D. Uncertainty / abstention

**Geifman, El-Yaniv.** "Selective Classification for Deep Neural Networks." arXiv:1705.08500 (May/Jun 2017); NIPS 2017 venue NOT VERIFIED from arXiv page (arXiv lists no comments). Access: ABSTRACT ONLY. Builds a selective classifier from a trained network; user sets a risk level; rejects inputs to keep risk at that level with high probability; CIFAR and ImageNet (e.g. 2% top-5 error with 99.9% probability at almost 60% coverage). SBG difference: abstains on predicted confidence; SBG abstains on lack of observation evidence (inference: orthogonal and combinable).

**Shafer, Vovk.** "A tutorial on conformal prediction." JMLR 9 (2008) 371-421; arXiv:0706.3188. ABSTRACT ONLY. Label sets with 1-epsilon coverage; guarantee under i.i.d./exchangeability, online setting.
**Angelopoulos, Bates.** "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification." arXiv:2107.07511 (v6 Dec 2022). ABSTRACT ONLY. Tutorial covers structured outputs, distribution shift, time series, outliers, and models that abstain. Correction: prior review cited the 2023 Foundations and Trends DOI 10.1561/9781638281597 for this; not re-verified here, arXiv is verified. Marginal-vs-conditional coverage and exchangeability limits are background, NOT VERIFIED here.

## E. Defect prediction and evaluation pitfalls

**Kamei et al.** "A large-scale empirical study of just-in-time quality assurance." IEEE TSE 39(6):757-773, 2013, DOI 10.1109/tse.2012.70. Authors: Kamei, Shihab, Adams, Hassan, Mockus, Sinha, Ubayashi. METADATA ONLY. Content (change-metric JIT prediction; size/diffusion strong) background, NOT VERIFIED. Metadata-based, no execution (background).

**Tan et al.** "Online Defect Prediction for Imbalanced Data." ICSE 2015, pp. 99-108. Authors: M. Tan, L. Tan, S. Dara, C. Mayeux (Crossref). METADATA ONLY. CORRECTION: prior review wrote "Tan, Tan, Dara, Mu"; fourth author is Caleb Mayeux. A paper titled "Time-travel" by Tan et al. was NOT FOUND/VERIFIED; do not cite under that name. Time-aware claim for this paper is background.

**Jimenez, Rwemalika, Papadakis, Sarro, Le Traon, Harman.** "The importance of accounting for real-world labelling when predicting software vulnerabilities." ESEC/FSE 2019, pp. 695-705, DOI 10.1145/3338906.3338941 (Crossref). Access: METADATA + secondary-source summary (a systematic review reports performance drops significantly when only vulnerabilities known before training time are used as labels). Own abstract NOT read.

**Herzig, Just, Zeller.** "It's not a bug, it's a feature: How misclassification impacts bug prediction." ICSE 2013, pp. 392-401 (Crossref). Access: ABSTRACT-LEVEL (search summary of publisher/Microsoft/Saarland pages): manual examination of >7,000 issue reports (7,401 per a blog) from 5 open-source projects; on average 39% of files marked defective never had a bug. Figures from secondary snippets; verify before quoting.

**Allamanis.** "The Adverse Effects of Code Duplication in Machine Learning Models of Code." arXiv:1812.06469 (v6 Aug 2019), SPLASH Onward! 2019 (per arXiv comments; DOI 10.1145/3359591.3359735 from prior review, Crossref returned 429, NOT re-verified). ABSTRACT ONLY. Duplicates can inflate reported performance by up to 100% relative to de-duplicated data; duplication index, recommendations, tools released.

**Just, Jalali, Inozemtseva, Ernst, Holmes, Fraser.** "Are mutants a valid substitute for real faults in software testing?" FSE 2014, pp. 654-665 (Crossref). ABSTRACT-LEVEL (search snippet): 5 Java programs, 357 real faults, 230,000 mutants; significant correlation between mutant detection and real-fault detection independent of coverage; coupling effect for 73% of real faults, 10% need new/stronger operators, 17% not coupled. Limits: Java, those 5 programs.

**Defects4J.** Just, Jalali, Ernst. ISSTA 2014, pp. 437-440 (Crossref). METADATA ONLY (title: database of existing faults for Java). Size not VERIFIED here.
**BugsInPy.** Widyasari et al. ESEC/FSE 2020, pp. 1556-1560 (Crossref; 16 authors, first Widyasari, last Ouh). METADATA ONLY; size NOT VERIFIED.
**QuixBugs.** Lin, Koppel, Chen, Solar-Lezama. SPLASH '17 Companion, pp. 55-56 (Crossref). METADATA ONLY. Multi-lingual repair benchmark from the Quixey Challenge (title). Inference: tiny single-function bugs; check size before use. Note: Defects4J/BugsInPy/QuixBugs are candidate subject sources; whether their fixes touch only the bug is NOT VERIFIED (tangling risk per Herzig).

## F. Execution-aware models (existence and claims only)

**TRACED.** Ding, Steenhoek, Pei, Kaiser, Le, Ray. arXiv:2306.07487 (Jun 2023); "Accepted by ICSE 2024 (Early Cycle)" per arXiv comments. ABSTRACT ONLY. Pre-trains on source + executable inputs + traces; estimates dynamic properties without executing at fine-tune; reported +12.4% complete execution path prediction, +25.2% runtime variable value prediction; also clone retrieval and vulnerability detection on 4 benchmarks. CORRECTION: venue now stated (ICSE 2024 per arXiv; final proceedings NOT VERIFIED).
**CodeExecutor.** Liu, Lu, Chen, Jiang, Svyatkovskiy, Fu, Sundaresan, Duan. arXiv:2305.05383; Findings of ACL 2023 (per arXiv). ABSTRACT ONLY. Mutation-based augmentation builds a Python execution dataset; challenging for Codex; CodeExecutor has "promising but limited" execution performance; benefits for zero-shot code-to-code search and text-to-code. SBG difference: they predict execution with a model; SBG uses real execution and reports sufficiency (inference).

## Claims from the earlier review

| Earlier claim | Status |
|---|---|
| AFLGo = Bohme et al. CCS 2017, 10.1145/3133956.3134020 | CONFIRMED (pp. 2329-2344) |
| Zest DOI 10.1145/3339069 | CORRECT: that is the artifact; paper is ISSTA 2019, 10.1145/3293882.3330576 |
| QuickCheck only 2011 reprint | CORRECT/UPGRADE: ICFP 2000 verified |
| Hypothesis JOSS 2019 10.21105/joss.01891 | CONFIRMED |
| DifFuzz ICSE 2019 10.1109/icse.2019.00034 | PARTLY: arXiv preprint verified; ICSE venue/DOI not re-fetched. Two runs differ in secret, not code version (inference) |
| NEZHA S&P 2017 | CONFIRMED, all 5 authors, pp. 615-632 |
| Badger ISSTA 2018 | CONFIRMED metadata (pp. 322-332) |
| Segura TSE 2016; Chen CSUR 2018 | CONFIRMED metadata |
| Geifman & El-Yaniv arXiv 1705.08500 | CONFIRMED; NIPS 2017 venue NOT VERIFIED |
| Shafer-Vovk arXiv 0706.3188 | CONFIRMED + JMLR 9 (2008) 371-421 |
| Angelopoulos-Bates 10.1561/9781638281597 | arXiv:2107.07511 confirmed; book DOI not re-verified |
| Kamei TSE 2013 10.1109/tse.2012.70 | CONFIRMED (39(6):757-773) |
| Tan et al. authors "Tan, Tan, Dara, Mu" | CORRECTED: 4th author Caleb Mayeux |
| Jimenez et al. FSE 2019 | CONFIRMED metadata; authors Jimenez, Rwemalika, Papadakis, Sarro, Le Traon, Harman |
| Herzig MSR 2013 "tangled changes" paper cited for label noise | NOT RE-VERIFIED; the "It's not a bug, it's a feature" ICSE 2013 paper (a different one) is verified |
| Allamanis Onward! 2019 | CONFIRMED (arXiv); DOI not re-verified (429) |
| Just FSE 2014 mutants 10.1145/2635868.2635929 | CONFIRMED (357 faults, 230k mutants) |
| TRACED / CodeExecutor exist | CONFIRMED; venues now ICSE 2024 / Findings ACL 2023 per arXiv |
| 1dVul / Skyfire regression fuzzing | NOT VERIFIED |
| Defects4J / BugsInPy / QuixBugs | metadata CONFIRMED only |
| "Time-travel" (Tan et al.) | NOT VERIFIED |
| All "accomplishes/fails" in prior review | background knowledge; here only abstract-level statements verified |

## Implications for the V7 evaluation protocol

Controls the protocol must include (each supported by a verified source, except where marked inference):
1. Duplicate control: de-duplicate subjects and split so near-duplicates do not cross train/test (Allamanis: up to 100% inflation, abstract).
2. Label-noise audit: bug-fix/defect labels contain misclassification; 39% of "defective" files never had a bug in one study (Herzig, secondary snippet). Audit tangled/non-bug "fix" commits before using them as ground truth.
3. Label realism and time: use only information available at the time (Jimenez; secondary summary shows large performance drop); split by commit time within project (Tan 2015 for time-aware setting, background).
4. Edit-size shortcut: report a size-only and JIT change-metrics baseline (Kamei), stratify by diff size. Kamei's "size predicts" claim is background, not verified; the baseline requirement is inference.
5. Generator fingerprinting: probe whether a classifier can identify the generator (Zest/QuickCheck-style generators or LLM variants) rather than behaviour; split by generator. Inference; no source verified directly.
6. Equivalent/uncovered mutants: if mutants supply "no change" labels, they are real-fault proxies only partially (Just: 73% coupled; 17% not coupled). Keep "not activated" distinct from "equivalent" (inference).
7. Report abstention honestly: risk-coverage curves (Geifman) and coverage at the answered subset; do not claim conformal-style guarantees (they rely on exchangeability, Shafer-Vovk/Angelopoulos abstracts).
8. Reach-the-change baseline: AFLGo-style directed search and Zest/Hypothesis generation as activation baselines; compare SBG's sufficiency gate against them.
9. Execution-model baselines (TRACED/CodeExecutor) only as comparators of "predicted vs real execution".
10. Repetitions and budgets stated for any fuzzing-driven exploration (Klees et al. CCS 2018 from prior review; not re-verified here).

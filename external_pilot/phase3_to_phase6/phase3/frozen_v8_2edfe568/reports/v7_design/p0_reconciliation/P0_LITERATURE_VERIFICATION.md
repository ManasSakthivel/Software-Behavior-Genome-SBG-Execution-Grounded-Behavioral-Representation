# P0 Literature Verification

Upgrade of `SBG_V7_RESEARCH_AND_NOVELTY_REVIEW.md`. Two verification passes (groups 1 and 2) merged unchanged below. Each entry carries an access level (FULL TEXT READ / ABSTRACT ONLY / METADATA ONLY / NOT ACCESSIBLE) and source type. **Overall access: full text was read for only 7 sources (group 1: Shadow SE ICSE 2016, DiffKemp, Felsing et al., Daikon TSE 2001, Law & Rothermel, Orso ICSE 2004, Chianti tech report); group 2 read no paper in full (metadata/abstract level, one documentation landing page). ACM DL returned HTTP 403 for every DOI.** "How SBG differs" statements are inferences unless stated otherwise.

## Corrections to the earlier review (from both passes)
- DiffKemp ICST 2021 DOI is 10.1109/ICST49551.2021.00045; its "non-equal" means "not proven equal", and its "undetermined" covers missing definitions, not observation sufficiency.
- Directed incremental symbolic execution: Person, Yang, Rungta, Khurshid, DOI 10.1145/1993316.1993558. CoverageImpact DOI 10.1145/940071.940089. Daikon's evaluated paper is TSE 2001 (10.1109/32.908957), not the 2007 SCP paper.
- Chianti "3.88%" could not be verified (sources read give 51%, 62.4%, 5.6% in different contexts).
- Zest DOI 10.1145/3339069 is the replication package; the paper is ISSTA 2019, 10.1145/3293882.3330576. Tan et al. ICSE 2015 fourth author is Caleb Mayeux. A "Time-travel" paper by Tan et al. was not found. QuickCheck (ICFP 2000, 10.1145/351240.351266) now verified. TRACED is ICSE 2024; CodeExecutor is Findings of ACL 2023 (per arXiv pages).
- Added: Evans & Savoia (ESEC/FSE 2007), cross-version differential testing: the closest precedent to SBG's differential core.
- Not verified: 1dVul/Skyfire mentions, DifFuzz ICSE DOI, Geifman NIPS 2017 venue, Allamanis DOI re-check (Crossref 429), benchmark sizes for Defects4J/BugsInPy/QuixBugs, Herzig 39% and the blog count 7,401.

## Consequence for the novelty claim
Abstaining/"not proven equal" is **not** novel (DiffKemp, Evans & Savoia, dynamic impact analysis already restricted to observed runs). The only defensible contribution is a unified, replayable verdict contract with an explicit sufficiency record, evaluated under pitfall controls (de-duplication, label-noise audit, time/project splits, size-only and JIT baselines, generator-identity probe, abstention risk-coverage reporting). No "first" claim.

---
# Group 1: verdict, differential, equivalence, impact side

Verified 2026-11-17. Access levels: FULL TEXT READ (I extracted and read the PDF text), ABSTRACT ONLY (publisher/arXiv/Crossref abstract or search-returned abstract), METADATA ONLY (Crossref/DBLP-style bibliographic record only), NOT ACCESSIBLE. dl.acm.org returned HTTP 403 for every DOI, so all ACM-only items are metadata/abstract level unless an author PDF was found. Bibliographic data below was checked against Crossref unless stated. "Inference" marks my own reasoning, not an author claim. Nothing here was run.

## 1. Shadow symbolic execution (Palikareva, Kuchta, Cadar; Kuchta et al.)
- ICSE 2016: "Shadow of a Doubt: Testing for Divergences Between Software Versions", Palikareva, Kuchta, Cadar, pp. 1181-1192, DOI 10.1145/2884781.2884845. Peer-reviewed. **FULL TEXT READ** (author PDF, Imperial).
- TOSEM 27(3), 2018: "Shadow Symbolic Execution for Testing Software Patches", Kuchta, Palikareva, Cadar, DOI 10.1145/3208952 (Crossref: 2018-07-31, 32 pp). Peer-reviewed. **ABSTRACT ONLY** (Crossref abstract).
- Method: old and new versions merged into one program via manual `change(old,new)` annotations; both run in one KLEE instance in lockstep; at a branch where they diverge, a test is generated; divergent inputs are then replayed natively on both versions with cross-version output checks. Starts from regression-suite tests that touch the patch (concolic phase, then a bounded symbolic phase).
- Evaluation: CoREBench Coreutils, 18 unique bug-introducing patches (2 to 324 LOC, up to 52 hunks); 2 excluded for infrastructure reasons. Reports divergences, % replayed in time, expected output differences vs regression bugs. Median run times 1,020 s / 1,962 s / 7,213 s per phase. Shows it exposes some CoREBench regressions plus two unrecorded bugs.
- Authors' limits: annotations written by hand; several bugs missed (need file-permission modelling, floating point, symbolic directories); short timeouts; depends on test-suite starting inputs; detects only output differences, not non-functional ones; for refactorings any difference is a bug; too many divergent inputs; replay percentages below 100% for some patches.
- SBG difference: Shadow reaches and exercises the change by input generation. It reports divergences found; the paper does not define a per-claim "change not activated / insufficient" verdict (inference from reading; absence of a taxonomy, not a flaw). SBG is observational and does not generate inputs by solving path conditions, so it is weaker on reaching code and must not claim to beat Shadow on precision.

## 2. Differential symbolic execution (Person et al.) and DiSE
- Person, Dwyer, Elbaum, Pasareanu, "Differential symbolic execution", FSE 2008, pp. 226-237, DOI 10.1145/1453101.1453131. Peer-reviewed. **METADATA ONLY** (Crossref + DBLP/related-work page; abstract not obtained).
- Person, Yang, Rungta, Khurshid, "Directed incremental symbolic execution", PLDI 2011, pp. 504-515, DOI 10.1145/1993316.1993558 (SIGPLAN Notices; second DOI 10.1145/2345156.1993558 is a reprint). Authors are NOT Pasareanu/Elbaum. **ABSTRACT ONLY** (search-returned): static change analysis plus symbolic execution to explore only paths affected by the change; evaluated by case study.
- What I can state: Shadow's TOSEM/ICSE text (read) says DSE is a general framework whose reliance on summaries raises scalability issues, and that DiSE uses static slicing to find statements affected by the patch. Subjects/size of DSE/DiSE evaluations: NOT VERIFIED.
- SBG difference (inference): both are symbolic, static-semantics-based; they characterise change effects over path conditions, not over observed executions.

## 3. Regression verification
- Godlin, Strichman, "Regression verification", DAC 2009, pp. 466-471, DOI 10.1145/1629911.1630034; journal: "Regression verification: proving the equivalence of similar programs", STVR 2013 (Crossref: online 2012-03-21, pp. 241-258, DOI 10.1002/stvr.1472). **ABSTRACT ONLY**. Claims: equivalence of closely related versions can be easier than functional verification though both undecidable; decomposition; automatic invariant for loops/recursion.
- Felsing, Grebing, Klebanov, Rummer, Ulbrich, "Automating regression verification", ASE 2014, pp. 349-360, DOI 10.1145/2642937.2642987. **FULL TEXT READ** (KIT PDF). Reduces equivalence of two integer programs to Horn constraints solved by Z3/Eldarica; tool Reve; benchmarks 16-53 LOC (both programs together), recursion, loops, non-equivalent pairs, compared with Godlin-Strichman RVT. Limits stated: only int locals/parameters (no arrays/heap); complete only for simple coupling predicates; fundamental redesigns unlikely provable.
- SBG difference: they prove equivalence (sound, small programs); SBG never claims equivalence and works on real programs where proof is out of reach. They are the "sound bar" SBG must not imitate in wording.

## 4. SymDiff
- Lahiri, Hawblitzel, Kawaguchi, Rebelo, CAV 2012, LNCS 7358, pp. 712-717, DOI 10.1007/978-3-642-31424-7_54 (Crossref-verified). Tool paper. **ABSTRACT ONLY** (MSR page via search): language-agnostic via Boogie; checks equivalence and displays differences; C/C#/x86 front ends. Evaluation details: NOT VERIFIED.
- Evident from DiffKemp's full text: authors report they could not get Linux kernel code into a form SymDiff accepts (Boogie front end limits).
- SBG difference: static/verifier-based, needs translation; SBG is execution-based.

## 5. DiffKemp
- Malik, Vojnar, "Automatically Checking Semantic Equivalence between Versions of Large-Scale C Projects", ICST 2021, pp. 329-339, DOI 10.1109/ICST49551.2021.00045. **FULL TEXT READ** (author PDF). Journal extension with Necas: ACM TOSEM, 2026-03-16, DOI 10.1145/3801958 (**ABSTRACT ONLY**, Crossref; adds global-variable slicing).
- Method: LLVM IR; lightweight transformations (24 of 29 listed C refactoring patterns) plus synchronisation-point comparison; static only.
- Evaluation: RHEL 7 kernel KABI functions across 7 releases, upstream Linux, musl; reports counts of equal / non-equal / "could not be determined" (the third mostly because a definition was not found). Authors manually inspected "non-equal" results: at most a few unchanged-semantics functions per version pair. Limit: cannot prove equivalence of heavily refactored code; no crashes/timeouts reported.
- Correction to prior review: DiffKemp's "non-equal" is "not proven equal" in effect (their "false non-equality"), so it already behaves like a sound-direction verdict; it does have a third "undetermined" outcome but it is about missing definitions, not observation sufficiency.
- SBG difference: static, proof-oriented; SBG is dynamic and abstains on activation.

## 6. Chianti
- Ren, Shah, Tip, Ryder, Chesley, "Chianti: A Tool for Change Impact Analysis of Java Programs", OOPSLA 2004, pp. 432-448, DOI 10.1145/1028976.1029012 (Crossref-verified). **ABSTRACT ONLY** for the OOPSLA version (search-returned: 2002 CVS data of Daikon; on average 51% of unit tests affected). I also **FULL TEXT READ** the 2003 IBM tech report RC22983 (different dataset: 62.4% of tests affected, 5.6% of atomic changes per affected test).
- Method: atomic changes between versions; static call graphs of tests; reports affected tests and affecting changes (a "safe approximation" per the report).
- Limits: static call-graph based, so "affected" means potentially affected; no observation of output change (inference from method). Java.
- SBG difference: Chianti links changes to tests statically; SBG requires evidence that the changed code was actually executed and observed.

## 7. PathImpact / CoverageImpact
- Law, Rothermel, "Whole program path-based dynamic impact analysis", ICSE 2003, pp. 308-318, DOI 10.1109/ICSE.2003.1201210. **FULL TEXT READ** (PDF). Whole-path (SEQUITUR-compressed) traces. Authors state the dynamic estimate "is thus not safe" and holds relative to the operational profile; evaluated on a small program set including `space` with 36 faulty versions; authors say results may not generalise.
- Orso, Apiwattanapong, Harrold, "Leveraging field data for impact analysis and regression testing", ESEC/FSE 2003, pp. 128-137, DOI 10.1145/940071.940089. **ABSTRACT ONLY** (+ slide summary via search: JABA ~60 KLOC, 1,100 field executions vs 195 in-house tests; field data "can considerably affect" results).
- Orso, Apiwattanapong, Law, Rothermel, Harrold, "An Empirical Comparison of Dynamic Impact Analysis Algorithms", ICSE 2004. **FULL TEXT READ**; pages NOT VERIFIED. States dynamic estimates "reflect only observed program behavior". CoverageImpact = per-method coverage plus static forward slice; subjects NanoXML, Siena, JABA.
- SBG difference: these already say impact is relative to observed executions. They produce impact sets, not behavioural verdicts about old-vs-new output, and have no explicit abstain outcome. Overlap on the "sufficiency depends on which executions" idea is substantial and must be cited.

## 8. Daikon
- Ernst, Cockrell, Griswold, Notkin, "Dynamically discovering likely program invariants to support program evolution", IEEE TSE 27(2), Feb 2001, pp. 99-123, DOI 10.1109/32.908957 (Crossref). **FULL TEXT READ**. (The prior review cited the 2007 SCP tool paper instead; that one I did not check.)
- Evaluation: Gries programs (invariants rediscovered); a C program of 563 lines, 21 procedures, 5,542 test cases (evolution task); scalability vs test-suite size. Authors state accuracy "depends in part on the quality and completeness of the test cases"; statistical test with a 0.01 limit that "is not a confidence". Authors also used invariants to reveal test-suite inadequacy. Claim limited to small programs.
- SBG difference: invariants are per version and unsound by design; cross-version invariant diff is a plausible baseline (inference, not done in this paper). Daikon's awareness of test-suite dependence is informal, with no explicit per-claim sufficiency verdict.

## 9. Equivalent mutants
- Offutt, Pan, "Automatically detecting equivalent mutants and infeasible paths", STVR 7(3):165-192, 1997 (Crossref-verified). **ABSTRACT ONLY** (search): constraint-based detection of some equivalent mutants. Percentages: NOT VERIFIED.
- Papadakis, Jia, Harman, Le Traon, "Trivial Compiler Equivalence...", ICSE 2015, pp. 936-946, DOI 10.1109/icse.2015.103 (Crossref). **ABSTRACT ONLY** (search): compares optimised binaries; abstract reports about 30% of existing equivalent mutants detected (human check), over 7% equivalent / 21% duplicate mutants on 6 large programs plus 18 benchmark programs.
- Papadakis et al., "Mutation Testing Advances: An Analysis and Survey", Advances in Computers 112, 2019, pp. 275-378, DOI 10.1016/bs.adcom.2018.03.015. **METADATA ONLY** (PDF host unreachable). Authors per host page: Papadakis, Kintis, Zhang, Jia, Le Traon, Harman.
- SBG relevance: equivalence is undecidable (Godlin-Strichman abstract states it for program verification generally); "no observed kill" must not be labelled equivalent. TCE is a sound-direction heuristic (detects some equivalents only).

## 10. Differential testing
- McKeeman, "Differential testing for software", Digital Technical Journal 10(1):100-107, 1998. **METADATA ONLY, secondary** (cited via a Wikipedia reference; no primary copy found).
- Evans, Savoia, "Differential testing: a new approach to change detection", ESEC/FSE 2007 companion, pp. 549-552, DOI 10.1145/1287624.1287707. **ABSTRACT ONLY** (search-returned): builds test suites for original and modified versions and compares; preliminary study of 3 subjects found 21%, 34%, 21% more behaviour changes than regression testing alone. This is direct cross-version differential testing and was missing from the prior review.
- Groce, Holzmann, Joshi, "Randomized Differential Testing as a Prelude to Formal Verification", ICSE 2007, pp. 621-631 (Crossref). **METADATA ONLY**.
- Petsios, Tang, Stolfo, Keromytis, Jana, "NEZHA", IEEE S&P 2017, pp. 615-632, DOI 10.1109/sp.2017.27. **ABSTRACT ONLY**: delta-diversity guidance across multiple implementations; 778 new discrepancies; 52x / 27x faster than Frankencerts / Mucerts.
- Nilizadeh, Noller, Pasareanu, "DifFuzz", ICSE 2019 (arXiv 1811.07005, v2 2019-02-26). **ABSTRACT ONLY**: resource-guided differential fuzzing for timing/memory side channels; found unknown vulnerabilities. Setting is side channels, not cross-version behaviour; the fetch summary's wording "two versions" is not reliable (NOT VERIFIED).
- SBG difference: all these treat a difference as the signal. None (in what I read) specifies what is reported when no difference is seen and the change was never reached.

## 11. SeqCoBench
- Maveli, Vergari, Cohen, "What can Large Language Models Capture about Code Functional Equivalence?", arXiv 2408.11081 (v1 2024-08-20, v2 2025-02-12), Findings of NAACL 2025 (per arXiv comments). **ABSTRACT ONLY**: 20+ transformations on Python programs, equivalence-preserving and altering; code LLMs zero-shot and with parameter-efficient finetuning perform about as well as classical match-based baselines, read by authors as shallow semantic understanding. Pages 6880-6918 and "from MBPP": NOT VERIFIED.
- SBG difference: synthetic labels by construction; tests whether models judge equivalence, not whether execution evidence suffices.

## Claim reconciliation against SBG_V7_RESEARCH_AND_NOVELTY_REVIEW.md

| Prior claim | Status |
|---|---|
| Shadow TOSEM 27(3) 2018 DOI 10.1145/3208952; Coreutils/CoREBench; precursor ICSE 2016 | CONFIRMED (Crossref + full text of ICSE 2016); volume/issue/Art.10 not rechecked |
| Shadow "needs symbolic-executable C-style code" | PARTLY CONFIRMED: KLEE-based, manual annotations, env-model limits stated; stricter wording "C via KLEE" |
| DiffKemp ICST 2021 DOI UNVERIFIED | CORRECTED: 10.1109/ICST49551.2021.00045, pp. 329-339; TOSEM 2026 extension exists |
| DiffKemp "returns inconclusive rather than equal" | CORRECTED: non-equal means unproven; separate "undetermined" is about missing definitions |
| SymDiff CAV 2012 pp. 712-717 DOI | CONFIRMED |
| Regression verification DAC 2009 pp. 466-471; STVR 23(3) 241-258 | CONFIRMED (pages/year); volume/issue from search |
| Felsing et al. not covered | ADDED, ASE 2014 pp. 349-360 |
| Chianti OOPSLA 2004 pp. 432-448; "about 51% tests affected" | CONFIRMED |
| Chianti "3.88% of changes per test" | COULD NOT VERIFY (tech report says 5.6%; 62.4% on another dataset) |
| Chianti "Daikon history" | CONFIRMED (2002 CVS data of Daikon) |
| PathImpact ICSE 2003 pp. 308-318 | CONFIRMED, full text |
| CoverageImpact DOI UNVERIFIED | CORRECTED: 10.1145/940071.940089 (a reprint 10.1145/949952.940089 exists); ICSE 2004 comparison title found |
| "1,100 executions" | PARTLY CONFIRMED (secondary slide summary, not full text) |
| Daikon cited as SCP 2007 | CORRECTED/EXTENDED: the 2001 TSE paper is the evaluated one; SCP 2007 not rechecked |
| DiffKemp/Daikon/other "fails" statements | Prior marked judgment; now partially grounded as above |
| Equivalent mutants: TCE DOI, Papadakis survey DOI, Offutt TOSEM 1992 | TCE CONFIRMED; survey CONFIRMED (title/pages); Offutt-Pan 1997 added; Offutt 1992 not rechecked |
| NEZHA first three authors only | CONFIRMED all five authors, pp. 615-632 |
| DifFuzz "two executions in parallel, resource use" | NOT FULLY VERIFIED; abstract-level agrees with resource/side-channel focus |
| SeqCoBench arXiv, NAACL Findings 2025 | CONFIRMED; pages 6880-6918 and MBPP source NOT VERIFIED |
| "No verified work unifies impact coverage + inconclusive verdicts" | STILL UNVERIFIED (absence claim); Evans-Savoia and Orso/Law add near-neighbours to cite |
| McKeeman 1998 | only secondary citation found |
| Not covered by prior: Evans-Savoia 2007 cross-version differential testing | ADDED; must be cited as closest differential-testing precedent |

## Minimum defensible contribution

The primitives are old and well published: running both versions and generating divergent inputs (Shadow), linking changes to executed tests (Chianti, PathImpact, CoverageImpact, whose authors already state results hold only for observed executions), refusing to call code equal without proof (regression verification, DiffKemp), and recognising that invariants and equivalence verdicts depend on the test suite (Daikon). What I could not find, in the works I read, is a single published artefact that turns this into an explicit, replayable output contract: a verdict taxonomy that separates "different", "no difference observed", "change not activated", and "insufficient observation", where "no difference observed" is never worded as equivalence, with a witness that can be re-executed. That integration plus a rigorous evaluation (real cross-version pairs, activation labels, baselines of Shadow/KLEE-style differential testing, Daikon invariant diffing, DiffKemp, and a coverage-of-change check) is the claim I would defend. It is not "first to abstain" or "first to condition on coverage"; reviewers who know Orso et al. and Evans-Savoia will say so. The absence claim rests on limited search, so state it as "we found none".

---
# Group 2: exploration, evaluation, uncertainty side


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

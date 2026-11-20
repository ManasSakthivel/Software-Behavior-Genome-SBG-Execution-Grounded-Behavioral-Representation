# Literature Group 1: verdict / differential / equivalence / impact side

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

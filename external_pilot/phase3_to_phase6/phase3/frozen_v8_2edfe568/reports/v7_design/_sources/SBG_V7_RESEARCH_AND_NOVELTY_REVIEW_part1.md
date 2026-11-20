# SBG V7 Research and Novelty Review, Part 1 (classical program analysis)

Verification policy: an ID appears only if a search in this session returned it. "(3p)" = DOI reported by a third-party bibliography page, not the publisher; confirm before formal citation. Everything else is UNVERIFIED. Search results were abstract/bibliographic level; no full texts were read, so "fails" columns mix reported limitations with my own judgment (marked "[judgment]").

SBG goal used for overlap: execution-grounded cross-version behavioural comparison, explicit observation sufficiency, abstain when changed code is not activated, never equate "no observed difference" with equivalence.

## 1. Dynamic analysis and trace abstraction
No survey or trace-abstraction paper was searched or verified. Status: UNVERIFIED for any specific citation (e.g. generic dynamic-analysis surveys, trace-abstraction literature). Do not cite from memory. Trace abstraction is covered here only through the items below (Daikon, specification mining, GK-tail).

## 2. Dynamic invariant inference

| Work | Verified reference | Accomplishes | Fails | SBG overlap |
|---|---|---|---|---|
| Daikon | Ernst, Perkins, Guo, McCamant, Pacheco, Tschantz, Xiao. "The Daikon system for dynamic detection of likely invariants." Sci. Comput. Program. 69(1-3), 2007, pp. 35-45. DOI UNVERIFIED | Runs program, reports properties (constants, ranges, linear, ordering, sortedness) true over all observed runs; C/C++/Java/Perl | Invariants are only "likely"; soundness depends on test suite; no per-claim sufficiency measure [judgment] | High on the idea "observed-only claims". Likely invariants diffed across versions is an obvious baseline SBG must beat |
| DIG | Nguyen, Kapur, Weimer, Forrest. "DIG: A dynamic invariant generator for polynomial and array invariants." ACM TOSEM 23(4), Art. 30, 2014. DOI UNVERIFIED. Related: ICSE 2012 and ICSE 2014 (disjunctive) papers by overlapping authors; arXiv:1904.07463 appeared in results for the disjunctive paper but I did not confirm it is that paper's ID | Generates (not filters from templates) nonlinear equalities/inequalities and array relations from traces; evaluated on 27 math algorithms plus AES | Numeric/algorithmic focus; not about cross-version diffing or activation [judgment] | Low-medium |

## 3. Behavioural model / specification inference

| Work | Verified reference | Accomplishes | Fails | SBG overlap |
|---|---|---|---|---|
| Biermann and Feldman (k-tails origin, attribution to k-tails NOT verified in results) | "On the Synthesis of Finite-State Machines from Samples of Their Behavior." IEEE Trans. Computers C-21(6), 1972, pp. 592-597. DOI 10.1109/TC.1972.5009015 (3p/Crossref) | Synthesises FSM from finite behaviour samples with a tunable accuracy/complexity parameter | Over-generalises from samples; no notion of unobserved behaviour [judgment] | Medium: the same "finite sample" problem SBG targets |
| Ammons, Bodik, Larus | "Mining Specifications." POPL 2002, pp. 4-16. DOI 10.1145/503272.503275 (3p) | Learns protocol state machines from executions (tracer, flow annotator, scenario extractor, learner); human reviews | Quality depends on traces; no sufficiency guarantee [judgment] | Medium |
| GK-tail | Lorenzoli, Mariani, Pezze. "Automatic generation of software behavioral models." ICSE 2008, pp. 501-510. DOI 10.1145/1368088.1368157 (3p) | EFSMs from interaction traces with data-value guards | Inference time (GK-tail+ later reduces it); no cross-version semantics | Medium |
| ReLink / k-tails variants / Lo-Khoo-Liu temporal rules | UNVERIFIED (Lo-Khoo-Liu search returned nothing). Note: "ReLink" as I recall is a commit-issue link-recovery tool, not behaviour inference; confirm what the V7 doc means | n/a | n/a | n/a |

Common gap: models are learned per version, generalise beyond observations, and rarely report how much of the changed code was exercised.

## 4. Differential testing and differential/semantic analysis

| Work | Verified reference | Accomplishes | Fails | SBG overlap |
|---|---|---|---|---|
| Shadow symbolic execution | Kuchta, Palikareva, Cadar. "Shadow Symbolic Execution for Testing Software Patches." ACM TOSEM 27(3), Art. 10, 2018. DOI 10.1145/3208952. Precursors: Cadar and Palikareva ICSE NIER 2014; Palikareva, Kuchta, Cadar "Shadow of a Doubt" ICSE 2016 (titles verified, IDs not) | Runs old/new in one symbolic execution; at divergent branches generates inputs exercising the change; evaluated on Coreutils/CoREBench | Needs symbolic-executable C-style code; path explosion; scope of environment/library modelling [judgment] | HIGH. It already targets "make the changed code get executed with divergent behaviour". SBG's activation-abstain is a weaker, observational cousin |
| DiffKemp | Malik and Vojnar. "Automatically Checking Semantic Equivalence between Versions of Large-Scale C Projects." ICST 2021. DOI UNVERIFIED. Also a RHEL-focused paper with Silling (title UNVERIFIED) | Static, LLVM IR, lightweight transforms plus pattern matching; thousands of functions in minutes; low false non-equal verdicts | Cannot prove equivalence for heavily refactored code (reported); inconclusive vs different handling is the key point | Medium. It already returns "cannot prove equal" instead of "equal" |
| SymDiff | Lahiri, Hawblitzel, Kawaguchi, Rebelo. "SymDiff: A Language-Agnostic Semantic Diff Tool for Imperative Programs." CAV 2012, LNCS 7358, pp. 712-717. DOI 10.1007/978-3-642-31424-7_54 (3p) | Boogie-based equivalence/diff; shows paths and values | Needs a front-end to Boogie; loops/heap need modelling [judgment] | Medium |

## 5. Equivalence checking

| Work | Verified reference | Accomplishes | Fails | SBG overlap |
|---|---|---|---|---|
| Translation validation | Pnueli, Siegel, Singerman. "Translation Validation." TACAS 1998, LNCS 1384, pp. 151-166. DOI 10.1007/BFb0054170 (3p) | Per-run proof that compiled output matches source | Compiler-scope; needs formal semantics | Low, but defines the sound-equivalence bar SBG must not claim |
| Regression verification | Godlin and Strichman. "Regression verification." DAC 2009, pp. 466-471. DOI 10.1145/1629911.1630034 (3p). Journal: STVR 23(3), 2013, pp. 241-258 | Proves equivalence of similar programs via decomposition | Scalability; works for similar structure [judgment] | Medium: the sound alternative to observation |
| SeqCoBench | Maveli, Vergari, Cohen. "What can Large Language Models Capture about Code Functional Equivalence?" arXiv:2408.11081; Findings of NAACL 2025, pp. 6880-6918 | Python equivalence pairs from MBPP, 20+ semantic-preserving/altering transformations; LLMs struggle zero-shot, on par with match-based metrics | Synthetic transformations, not real cross-version commits [judgment]; labels are by construction | Medium for evaluation; direct benchmark candidate and a warning about LLM judgement |

## 6. Symbolic and concolic execution

| Work | Verified reference | Accomplishes | Fails | SBG overlap |
|---|---|---|---|---|
| DART | Godefroid, Klarlund, Sen. "DART: Directed Automated Random Testing." PLDI 2005, pp. 213-223. DOI UNVERIFIED | Auto interface extraction, random driver, dynamic analysis to steer new inputs | Path explosion, solver limits, environment [judgment] | Low-medium (input steering to reach code) |
| CUTE | Sen, Marinov, Agha. "CUTE: A concolic unit testing engine for C." ESEC/FSE 2005, pp. 263-272. DOI 10.1145/1081706.1081750 (3p) | Concolic unit testing for C | Same | Low-medium |
| KLEE | Cadar, Dunbar, Engler. OSDI 2008, pp. 209-224. DOI/ID UNVERIFIED (none returned) | ~90% avg line coverage on Coreutils; 56 serious bugs in 452 programs | Environment modelling, scaling | Medium (basis of Shadow) |
| SAGE | Godefroid, Levin, Molnar. "SAGE: whitebox fuzzing for security testing." CACM 55(3), 2012. DOI 10.1145/2093548.2093564 (found on author PDF). Origin NDSS 2008 "Automated Whitebox Fuzz Testing" | x86-level trace plus constraint solving to generate new inputs | Security/file-input focus | Low |

## 7. CEGAR
Clarke, Grumberg, Jha, Lu, Veith. "Counterexample-Guided Abstraction Refinement." CAV 2000, LNCS 1855, pp. 154-169. DOI 10.1007/10722167_15 (3p). JACM 2003, pp. 752-794. Accomplishes: automatic abstraction refinement for model checking. Fails: needs formal model, termination not guaranteed [judgment]. Overlap: low; the abstract-refine-on-evidence loop is a design analogy for SBG refining observation plans, not a reuse.

## 8. Slicing and dependence analysis
Weiser. "Program Slicing." ICSE 1981, pp. 439-449 (no DOI found); journal IEEE TSE 1984, pp. 352-357, DOI 10.1109/TSE.1984.5010248 (reported in results). Accomplishes: statement subsets relevant to a criterion. Fails: static slices are large; dynamic slices are per-input [judgment]. Overlap: medium; a dependence slice from the changed code to observed outputs is the natural formal basis for "changed code is activated and can reach an observation point".

## 9. Dynamic change-impact analysis

| Work | Verified reference | Accomplishes | Fails | SBG overlap |
|---|---|---|---|---|
| Chianti | Ren, Shah, Tip, Ryder, Chesley. "Chianti: A Tool for Change Impact Analysis of Java Programs." OOPSLA 2004, pp. 432-448. DOI 10.1145/1028976.1029012 | Atomic changes between versions; reports affected tests and changes responsible; Daikon history: about 51% tests affected, 3.88% of changes per test | Reports possibly affected tests, not observed behaviour difference [judgment]; Java | HIGH on activation/coverage-of-change linkage |
| PathImpact | Law and Rothermel. "Whole Program Path-Based Dynamic Impact Analysis." ICSE 2003, pp. 308-318. DOI 10.1109/ICSE.2003.1201210 | Impact sets from whole-path profiles; more accurate than call graph, more precise than static slicing | Bound to profiled behaviour; precision/cost tradeoffs | Medium-high |
| CoverageImpact | Orso, Apiwattanapong, Harrold. "Leveraging Field Data for Impact Analysis and Regression Testing." ESEC/FSE 2003. DOI UNVERIFIED. Comparison paper: Orso et al. ICSE 2004 (title/ID UNVERIFIED) | Dynamic forward slices from coverage; field data (1,100 executions) changes results | Dependent on which executions were observed | HIGH: the profile-dependence point is exactly observation sufficiency |

## What SBG could genuinely add vs. what is already done

Already done (do not claim):
- Running old/new together and generating inputs to hit divergence: Shadow symbolic execution. Reaching changed code is a solved-in-principle problem for symbolic-friendly C.
- Linking changes to tests that exercise them, and impact from execution profiles: Chianti, PathImpact, CoverageImpact. "Was the change executed" is old; field-data sensitivity was already shown.
- Refusing to call things equal when unsure: DiffKemp returns inconclusive rather than equal; regression verification and translation validation give the sound bar.
- Likely-invariants and state-machine inference over traces, including cross-run use: Daikon, GK-tail, Ammons et al.
- Equivalence benchmarks: SeqCoBench exists (synthetic, Python).

Plausibly new, but unproven (each needs a literature check beyond this review and an experiment):
1. A first-class, per-claim observation-sufficiency verdict (e.g. equivalent-on-observed / different / not-activated / abstain) combined with behaviour comparison. The pieces exist separately (impact coverage, inconclusive verdicts); I did not find a verified work that unifies them, but absence in 25 search results is weak evidence. Novelty claim should be "integration and explicit semantics", not "first".
2. Language/runtime-agnostic observational comparison on real commits (vs SymDiff/DiffKemp C/Boogie specificity, Chianti Java). Valuable only if it works at reasonable cost; Shadow likely beats it on precision where applicable.
3. Evaluation protocol: a benchmark of real cross-version pairs with ground truth and "activation" labels, since SeqCoBench labels are by construction. Real contribution if built and released, but it is a dataset, not a technique.
4. Calibrated uncertainty (not just binary abstain): untested territory, needs empirical evidence that the uncertainty is calibrated.

Blunt bottom line: the core primitives are old. SBG's defensible contribution is the discipline (never conflate "no difference observed" with equivalence), the unified verdict taxonomy, and a rigorous evaluation. Anything beyond that requires evidence not found here. Baselines reviewers will demand: Daikon diff across versions, Shadow symbolic execution/KLEE-based differential testing, DiffKemp/SymDiff where applicable, CoverageImpact-style activation checks.

## Not covered / limits
No search for: dynamic-analysis surveys, SAGE/KLEE journal versions, regression verification for loops (Felsing et al.), LLM-based semantic diff (2023-2026), mutation-based equivalence, differential fuzzing literature, DiffKemp/DIG/Daikon DOIs, CoverageImpact DOI. Part 2 should cover LLM-era work, which is where novelty risk is highest.

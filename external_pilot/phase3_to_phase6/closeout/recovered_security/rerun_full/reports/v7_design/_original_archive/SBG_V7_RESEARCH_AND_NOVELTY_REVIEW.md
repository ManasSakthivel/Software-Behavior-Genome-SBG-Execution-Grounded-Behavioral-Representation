# SBG V7 Research and Novelty Review

Merged from two literature passes. Only items marked with a DOI/arXiv ID were checked against search/Crossref/arXiv metadata; none was read in full text, and the "accomplishes / fails" statements are from background knowledge. "(3p)" DOIs came from third-party bibliographies and must be checked before formal citation. UNVERIFIED means no matching record was found. No novelty is claimed.

---
# Part 1: dynamic analysis, invariants, differential/equivalence, symbolic, slicing, impact


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


---
# Part 2: fuzzing, metamorphic, graphs, uncertainty, defect prediction, mutation, learned execution models, evaluation pitfalls


Method: every identifier below was returned by a Crossref or arXiv API query in this session and its title and first authors were checked against the query. Anything else is marked UNVERIFIED. For Crossref hits I confirmed title, first authors, year and venue string, but I did not read the papers. The "accomplishes" and "fails" statements come from my background knowledge of these works, not from re-reading them, so treat them as claims to check before citing. Dates and venues are as returned by the APIs. SBG's goal throughout: execution-grounded cross-version behavioural comparison, with explicit observation sufficiency, abstaining when the changed code was not activated.

## 1. Coverage-guided and directed fuzzing

- AFL (Zalewski): no paper. UNVERIFIED as a citable reference. A related verified item is Fioraldi et al., "Dissecting American Fuzzy Lop - A FuzzBench Evaluation", FUZZING 2022, DOI 10.14722/fuzzing.2022.23004.
  - Does: edge-coverage feedback with mutation-based input generation.
  - Fails: coverage is a proxy and says nothing about whether outputs differ. It has no notion of two versions.
  - Overlap: it supplies "was this code reached" signals, but only for a single version.
- libFuzzer: UNVERIFIED (no paper found). Same limits as AFL, in-process.
- AFLGo: Bohme, Pham, Nguyen, Roychoudhury, "Directed Greybox Fuzzing", ACM CCS 2017, DOI 10.1145/3133956.3134020.
  - Does: steers inputs toward target locations, such as a patch, by call-graph distance with simulated-annealing power scheduling.
  - Fails: it only drives toward reaching a site. It does not judge behavioural difference, and distance is a static approximation.
  - Overlap: this is the closest prior art to "activate the changed region". An SBG activation-sufficiency check should be compared against it.
- Zest/JQF: Padhye, Lemieux, Sen, "Semantic Fuzzing with Zest". Crossref returned only the replication package, DOI 10.1145/3339069. The paper itself is UNVERIFIED here.
  - Does: coverage-guided generator-based fuzzing that keeps inputs valid.
  - Fails: it needs a generator, and the inputs inherit that generator's distribution.
  - Overlap: it is a way to get activation inputs for structured Python or Java code. It is also a source of the generator-fingerprinting risk (section 7).
- Hypothesis: MacIver, Hatfield-Dodds et al., "Hypothesis: A new approach to property-based testing", JOSS 2019, DOI 10.21105/joss.01891.
  - Does: Python property-based testing with shrinking.
  - Fails: properties must be written by hand.
  - Overlap: it could be the input engine for Python SBG runs. Shrinking could give minimal witnesses.
- QuickCheck: Claessen and Hughes, ACM SIGPLAN Notices 2011 reprint, DOI 10.1145/1988042.1988046. The Crossref match is a 2011 reprint. The original ICFP 2000 paper is UNVERIFIED.
  - Does: random testing against user-stated properties.
  - Fails: the same oracle-authoring burden as Hypothesis.
- Klees, Ruef, Cooper, Wei, Hicks, "Evaluating Fuzz Testing", ACM CCS 2018, DOI 10.1145/3243734.3243804.
  - Does: documents evaluation flaws in fuzzing papers, namely too few runs, short timeouts, poor seed choice and weak baselines.
  - Overlap: SBG experiments need the same discipline (repeated trials, stated budgets).

## 2. Regression-directed and differential fuzzing

- DifFuzz: Nilizadeh, Noller, Pasareanu, ICSE 2019, DOI 10.1109/icse.2019.00034.
  - Does: runs two executions in parallel and maximises their divergence in resource use, to find side channels.
  - Fails: the target is resource cost, not functional behaviour.
  - Overlap: it uses two-run comparison as the feedback signal, which is the structural pattern SBG uses.
- NEZHA: Petsios, Tang, Stolfo, Keromytis, Jana, IEEE S&P 2017, DOI 10.1109/sp.2017.27. I verified the first three authors only.
  - Does: differential testing across multiple implementations, guided by behavioural asymmetry.
  - Fails: it needs several implementations of one specification. Across versions of one program it can flag intended changes as bugs.
  - Overlap: the "divergence as feedback" idea. It has no notion of intent.
- Badger: Noller, Kersten, Pasareanu, ISSTA 2018, DOI 10.1145/3213846.3213868.
  - Does: combines fuzzing and symbolic execution for worst-case complexity.
  - Fails: it targets complexity, not semantics.
  - Overlap: hybrid concrete and symbolic search is a possible activation helper.
- Regression fuzzing of patches specifically (for example directed fuzzing of changed lines such as 1dVul or Skyfire-style work): UNVERIFIED, not searched.

## 3. Metamorphic testing and oracles

- Chen et al., "Metamorphic Testing: A Review of Challenges and Opportunities", ACM Computing Surveys 2018, DOI 10.1145/3143561 (first authors Chen, Kuo, Liu).
- Segura, Fraser, Sanchez, Ruiz-Cortes, "A Survey on Metamorphic Testing", IEEE TSE 2016, DOI 10.1109/tse.2016.2532875.
- Barr, Harman, McMinn, Shahbaz, Yoo, "The Oracle Problem in Software Testing: A Survey", IEEE TSE 2015, DOI 10.1109/tse.2014.2372785.
  - Do: they replace the missing oracle with relations between runs, and they catalogue the oracle problem.
  - Fail: relations are mostly hand-authored and domain-specific. A relation that holds says little about whether a particular change was exercised.
  - Overlap: SBG's cross-version comparison is in effect a differential oracle. These surveys name its failure mode, which is that the relation must be stated, and a differing output is not necessarily a bug.

## 4. Code representations, graphs and alignment

- Code property graph: Yamaguchi, Golde, Arp, Rieck, "Modeling and Discovering Vulnerabilities with Code Property Graphs", IEEE S&P 2014, DOI 10.1109/sp.2014.44.
  - Does: merges AST, CFG and PDG in one graph for pattern queries.
  - Fails: it is static, and queries are hand-written.
- Allamanis, Brockschmidt, Khademi, "Learning to Represent Programs with Graphs", arXiv 1711.00740 (2017). Venue ICLR 2018 is from memory, UNVERIFIED.
- ProGraML: Cummins, Fisches et al., arXiv 2003.10536 (2020). Venue UNVERIFIED.
  - Do: GNN code models over syntax and data-flow graphs (ProGraML works on LLVM IR).
  - Fail: static, and they generalise poorly across projects. They do not say what happened at runtime.
- Allamanis, Barr, Devanbu, Sutton, "A Survey of Machine Learning for Big Code and Naturalness", ACM Computing Surveys 2018, DOI 10.1145/3212695.
- Falleri, Morandat, Blanc, Martinez, Monperrus, "Fine-grained and accurate source code differencing" (GumTree), ASE 2014, DOI 10.1145/2642937.2642982. I verified the first three authors only.
  - Does: AST matching and edit-script generation.
  - Fails: it is syntax-bound, and move and rename heuristics can mis-match.
  - Overlap: a standard way to align versions before comparing them. SBG should reuse it for alignment and not reinvent it.
- Tsantalis, Ketkar, Dig, "RefactoringMiner 2.0", IEEE TSE 2022, DOI 10.1109/tse.2020.3007722.
  - Does: detects refactorings.
  - Overlap: it filters behaviour-preserving edits, which matters for the equivalence problem.
- Bille, "A survey on tree edit distance and related problems", Theoretical Computer Science 2005, DOI 10.1016/j.tcs.2004.12.030; Sanfeliu and Fu, "A distance measure between attributed relational graphs for pattern recognition", IEEE Trans. SMC 1983, DOI 10.1109/tsmc.1983.6313167 (graph edit distance).
  - Do: give syntactic distances.
  - Fail: edit distance does not equal semantic distance. A small textual edit can change behaviour completely.
- Spoon (Pawlak et al., Software: Practice and Experience 2015, DOI 10.1002/spe.2346): a Java source analysis library. It is not a Python tool.

## 5. Dependency propagation and dynamic slicing

- Weiser, "Program Slicing", IEEE TSE 1984, DOI 10.1109/tse.1984.5010248.
- Korel and Laski, "Dynamic program slicing", Information Processing Letters 1988, DOI 10.1016/0020-0190(88)90054-3.
- Agrawal and Horgan, "Dynamic program slicing", PLDI 1990, DOI 10.1145/93542.93576.
- Zeller and Hildebrandt, "Simplifying and isolating failure-inducing input" (delta debugging), IEEE TSE 2002, DOI 10.1109/32.988498.
  - Do: compute the statements or inputs that actually influenced a value in a given execution.
  - Fail: dynamic slices are per-execution, can be large, are costly to instrument, and handle implicit and dynamic features (eval, reflection, native code) poorly.
  - Overlap: this is the most natural formal basis for "this change was or was not in the influence set of the observed output". It is the established tool for the SBG activation notion.

## 6. Uncertainty, abstention, prediction pitfalls

- Chow, "On optimum recognition error and reject tradeoff", IEEE Trans. Information Theory 1970, DOI 10.1109/tit.1970.1054406.
- Geifman and El-Yaniv, "Selective Classification for Deep Neural Networks", arXiv 1705.08500 (2017).
  - Do: give risk-coverage tradeoffs and abstention by confidence thresholds.
  - Fail: softmax confidence is poorly calibrated, and guarantees assume i.i.d. data. Abstention from confidence is not the same as abstaining because no evidence was observed.
- Shafer and Vovk, "A tutorial on conformal prediction", arXiv 0706.3188 (2007). Angelopoulos and Bates, "Conformal Prediction: A Gentle Introduction", 2023, DOI 10.1561/9781638281597. Tibshirani, Foygel Barber et al., "Conformal Prediction Under Covariate Shift", arXiv 1904.06019 (2019).
  - Do: give finite-sample coverage under exchangeability. The covariate-shift paper reweights for known shift.
  - Fail: exchangeability across projects or versions is exactly what fails. Coverage is marginal, not conditional on a particular change.
  - Overlap: SBG's "explicit observation sufficiency" is a data-availability condition, which is a different thing from statistical confidence. I found no work in this search that gates a prediction on whether the relevant code was executed. That is not proof that none exists.

## 7. Cross-project and JIT defect prediction, and pitfalls

- Kamei, Shihab, Adams et al., "A large-scale empirical study of just-in-time quality assurance", IEEE TSE 2013, DOI 10.1109/tse.2012.70. Change metrics (size, diffusion, history, experience) predict defect-inducing commits.
- Zimmermann, Nagappan, Gall, Giger, Murphy, "Cross-project defect prediction", ESEC/FSE 2009, DOI 10.1145/1595696.1595713. Transfer between projects often works poorly.
- Hosseini, Turhan, Gunarathna, "A Systematic Literature Review and Meta-Analysis on Cross Project Defect Prediction", IEEE TSE 2019, DOI 10.1109/tse.2017.2770124.
- Tan, Tan, Dara, Mu, "Online Defect Prediction for Imbalanced Data", ICSE 2015, DOI 10.1109/icse.2015.139. This is the time-aware setting that avoids training on the future.
- Do not conflate prediction with comparison: these models use change metadata, not execution, and so are blind to behaviour. They are also the baseline SBG must beat on the same labels.

### Evaluation pitfalls mapped to SBG's known problems

1. Edit-size shortcut. Kamei et al. report size and diffusion metrics as strong predictors. A model or score that tracks diff size can look good without observing behaviour. SBG must report a size-only baseline and stratify results by diff size.
2. Generator fingerprinting. Allamanis, "The adverse effects of code duplication in machine learning models of code", Onward! 2019, DOI 10.1145/3359591.3359735, shows duplication inflates results. Klees et al. 2018 show evaluation artefacts in fuzzing. Synthetic or LLM-made variants carry stylistic signatures that a classifier can learn instead of semantics. Vegas and Elbaum, "Pitfalls in Experiments with DNN4SE", arXiv 2305.11556 (2023), catalogue related experiment flaws. Mitigation: split by project and by generator, and test a generator-identity probe.
3. Equivalent mutants. Offutt, "Investigations of the software testing coupling effect", ACM TOSEM 1992, DOI 10.1145/125489.125473 (basis for mutation validity). Just, Jalali, Inozemtseva et al., FSE 2014, DOI 10.1145/2635868.2635929 (mutants vs real faults). Papadakis, Delamaro, Le Traon, "Mitigating the effects of equivalent mutants with mutant classification strategies", Science of Computer Programming 2014, DOI 10.1016/j.scico.2014.05.012. Papadakis et al., "Trivial Compiler Equivalence", ICSE 2015, DOI 10.1109/icse.2015.103. Madeyski, Orzeszyna, Torkar, Jozala, "Overcoming the Equivalent Mutant Problem", IEEE TSE 2014, DOI 10.1109/tse.2013.44. Papadakis et al., "Mutation Testing Advances: An Analysis and Survey", Advances in Computers 2019, DOI 10.1016/bs.adcom.2018.03.015 (author list not returned by Crossref). Equivalence is undecidable in general. Any "no behavioural change" label from mutants is noisy, and SBG's "unactivated, abstain" class partly overlaps with "equivalent" and must be kept separate.
4. Label noise. Herzig and Zeller, "The impact of tangled code changes", MSR 2013, DOI 10.1109/msr.2013.6624018. da Costa, McIntosh, Shang et al., "A Framework for Evaluating the Results of the SZZ Approach", IEEE TSE 2017, DOI 10.1109/tse.2016.2616306. Rodriguez-Perez, Robles, Gonzalez-Barahona, IST 2018, DOI 10.1016/j.infsof.2018.03.009. Jimenez et al., "The importance of accounting for real-world labelling when predicting software vulnerabilities", ESEC/FSE 2019, DOI 10.1145/3338906.3338941 (unrealistic labelling inflates results). Bug-fix labels are noisy and tangled commits are common.
5. Time-travel and leakage. Tan et al. 2015 for time-aware evaluation. Yang et al., "Data Leakage in Notebooks", arXiv 2209.03345 (2022), for leakage patterns in practice. Split by commit time within a project and by project across projects.

## 8. Mutation testing, equivalence benchmarks, execution-aware models

- CodeNet: Puri, Kung et al., arXiv 2105.12655 (2021). Large solution corpus with test cases, used for clone and equivalence-style tasks. Solutions to one problem are not guaranteed behaviourally equal on all inputs.
- BigCloneBench: UNVERIFIED (Svajlenko search not completed, Crossref query not run for it). Known to be label-noisy from memory, not verified.
- EquiBench (LLM equivalence checking benchmark): searched by title on arXiv, no match returned. UNVERIFIED.
- TRACED: Ding, Steenhoek et al., "TRACED: Execution-aware Pre-training for Source Code", arXiv 2306.07487 (2023). Venue UNVERIFIED.
- CodeExecutor: Liu, Lu et al., "Code Execution with Pre-trained Language Models", arXiv 2305.05383 (2023). Venue UNVERIFIED.
  - Do: train models on execution traces or to predict them.
  - Fail: they learn to imitate traces and are not guaranteed to match real execution. They are per-program, not cross-version, and do not state when the trace is insufficient.
  - Overlap: they support the premise that execution information helps. SBG would use real traces, which is stronger on grounding and weaker on scale.
- Kanade et al., "Learning and Evaluating Contextual Embedding of Source Code" (CuBERT), arXiv 2001.00059 (2019). Guo et al., UniXcoder, arXiv 2203.03850 (2022). Pretrained static code encoders, the likely baselines.
- Liu, Xia et al., "Is Your Code Generated by ChatGPT Really Correct?" (EvalPlus), arXiv 2305.01210 (2023). Shows that weak test suites hide wrong code. This is direct evidence that few observations can mislead, which supports an explicit sufficiency requirement.
- Dynamic neural program embedding (Wang et al.): a Crossref search returned the wrong item, so UNVERIFIED.

## 9. What SBG could genuinely add

None of the following is a novelty claim. Each is a hypothesis that needs evidence, and I did not do an exhaustive search.

1. An explicit activation and sufficiency gate that decides when a cross-version verdict is allowed at all. Dynamic slicing and directed fuzzing supply the pieces, but I did not find work in this search that exposes "abstain: change not exercised" as a first-class output. A gap in my search is not a gap in the literature.
2. Three-way output (differs, same, insufficient) in place of binary. Differential fuzzers and mutation tools usually collapse "not reached" and "equivalent". Keeping them apart is a modest but useful contribution if measured.
3. Separating the abstention reason (no evidence) from low-confidence abstention (Geifman and El-Yaniv, conformal). This is a design clarification, not a new algorithm.
4. Pitfall-controlled evaluation: a size-only baseline, generator-identity probe, project and time splits, and a label-noise audit. This is arguably the most defensible contribution, because the literature above shows these controls are often missing.
5. Reuse, do not rebuild: GumTree or RefactoringMiner for alignment, AFLGo-style distance or Hypothesis for activation, dynamic slicing for propagation.
6. Weak spots to state plainly. Nondeterminism, I/O and environment, and dynamic Python features undermine trace comparison. Sufficiency is only as good as the inputs found. Real traces do not scale like static encoders. Without a head-to-head against a diff-size baseline and a JIT metrics baseline, no claim of added value is supported.

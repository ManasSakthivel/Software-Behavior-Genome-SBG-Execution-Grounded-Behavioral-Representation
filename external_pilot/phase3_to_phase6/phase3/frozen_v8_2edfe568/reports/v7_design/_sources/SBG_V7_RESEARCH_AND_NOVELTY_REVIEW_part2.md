# SBG V7 Research and Novelty Review, Part 2

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

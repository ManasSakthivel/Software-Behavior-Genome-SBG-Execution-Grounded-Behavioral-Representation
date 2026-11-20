# Related-work comparison (FINAL SPRINT, Part 2A/2B)

**Method.** Bibliographic metadata for every entry below was re-verified in this sprint by DOI content negotiation
(`curl -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/<DOI>`, HTTP 200) and/or arXiv/Crossref/Semantic
Scholar. Each source carries an explicit **depth-of-reading** tag. Where a source was not read in full the
corresponding cell says "not verified". Nothing here is a claim about papers not retrieved; **this is a focused
comparison with the closest overlaps, not an exhaustive survey.**

Depth tags: **FT** full text read · **ABS+INTRO** abstract and introduction/contribution list read · **ABS** abstract read ·
**META** bibliographic metadata only (method not inspected; not used for method-level distinctions).

## 1. Sources and verification status

| # | Source (verified metadata) | DOI / ID | Depth | Notes |
|---|---|---|---|---|
| K | M. Kessel, C. Atkinson. *On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence.* SCAM 2019 (19th IEEE Int. Working Conf. on Source Code Analysis and Manipulation), pp. 193–203 | **10.1109/SCAM.2019.00030** | **ABS** (full text closed access; Unpaywall `oa_status = closed`; IEEE Xplore full text not retrievable) | **Earlier repo docs cite 10.1109/SCAM.2019.00019 — that DOI belongs to Harrand et al., *The Strengths and Behavioral Quirks of Java Bytecode Decompilers* (SCAM 2019, pp. 92–102).** Corrected in this sprint. |
| D | B. Danglot, M. Monperrus, W. Rudametkin, B. Baudry. *An approach and benchmark to detect behavioral changes of commits in continuous integration.* Empirical Software Engineering 25(4), 2020, pp. 2379–2415 | 10.1007/s10664-019-09794-7; arXiv:1902.08482 | **ABS+INTRO** (arXiv HTML) | DCI. Java, test amplification, 60 commits from 6 projects. |
| P | A. Podgurski, L. Pierce. *Behavior sampling: a technique for automated retrieval of reusable components.* ICSE '92, pp. 349–361 | 10.1145/143062.143152 | **META** (+ its description in K's abstract) | Origin of "behavior sampling" as cited by K. |
| J | L. Jiang, Z. Su. *Automatic mining of functionally equivalent code fragments via random testing.* ISSTA 2009, pp. 81–92 | 10.1145/1572272.1572283 | **META** | |
| B | W. Jin, A. Orso, T. Xie. *Automated Behavioral Regression Testing.* ICST 2010, pp. 137–146 | 10.1109/ICST.2010.64 | **META** | |
| S | S. Person, M. Dwyer, S. Elbaum, C. Păsăreanu. *Differential symbolic execution.* FSE 2008, pp. 226–237 | 10.1145/1453101.1453131 | **META** | |
| E | R. Evans, A. Savoia. *Differential testing.* ESEC/FSE 2007, pp. 549–552 | 10.1145/1295014.1295038 | **META** | |
| M1 | R. Just, D. Jalali, L. Inozemtseva, M. Ernst, R. Holmes, G. Fraser. *Are mutants a valid substitute for real faults in software testing?* FSE 2014, pp. 654–665 | 10.1145/2635868.2635929 | **META** | Relevant to the synthetic-vs-real-bug limitation. |
| M2 | M. Ojdanić, E. Soremekun, R. Degiovanni, M. Papadakis, Y. Le Traon. *Mutation Testing in Evolving Systems: Studying the Relevance of Mutants to Code Evolution.* ACM TOSEM 2023 | 10.1145/3530786 | **META** | |
| T | Y. Ding, B. Steenhoek, K. Pei, G. Kaiser, W. Le, B. Ray. *TRACED: Execution-aware Pre-training for Source Code.* ICSE 2024 | 10.1145/3597503.3608140 | **META** (earlier audit: ACM abstract) | Neural pre-training on execution traces. |
| Y | H. Yu, X. Hu, G. Li, Y. Li, Q. Wang, T. Xie. *Assessing and Improving an Evaluation Dataset for Detecting Semantic Code Clones via Deep Learning.* ACM TOSEM 2022, 1–25 | 10.1145/3502852 | **META** | |
| KR | J. Krinke, C. Ragkhitwetsagul. *How the Misuse of a Dataset Harmed Semantic Clone Detection.* | arXiv:2505.04311 | **ABS** | 93 % of 406 sampled BigCloneBench Weak Type-3/4 pairs mislabelled. |
| W | A. Wei, J. Cao, R. Li, H. Chen, Y. Zhang, Z. Wang, Y. Liu, T. S. F. X. Teixeira, D. Yang, K. Wang, A. Aiken. *EquiBench: Benchmarking Large Language Models' Reasoning about Program Semantics via Equivalence Checking.* | arXiv:2502.12466 | **ABS** | The earlier audit's title/venue ("Understanding…", "NeurIPS 2025 Workshop") do not match the arXiv record (title above, first posted 2025-02-18). Author list verified from the arXiv API record (11 authors). Journal/venue reference: none listed in the arXiv record; venue **not verified** — cite as arXiv until checked. |

What the abstract of K says (Semantic Scholar record): a large empirical study of "behavior sampling" (Podgurski &
Pierce 1992) for judging functional equivalence by observing responses to common stimuli; finds ≥ 39 random tests are
needed to reach ~85 % recognition of non-equivalence (versus about 4 assumed in earlier work), and that coverage-based
test generation needs far fewer. **Everything else about K's representation, inputs, labels and statistics is
unverified** (full text inaccessible).

## 2. Comparison matrix

Prior methods compared: **K** (behaviour sampling efficacy study), **D** (DCI). Other sources (P, J, B, S, E) are listed
as *related families* in §3 and are not entered in the matrix because their methods were not read.

| Dimension | Prior method | SBG | Evidence and source |
|---|---|---|---|
| Input representation | **K:** observed responses of programs to a shared set of stimuli (inputs); the abstract does not state the response representation — *not verified*. **D:** generated unit tests with amplified assertions; behaviour change = a generated test passes on one version and fails on the other. | A **trace-derived genome** per program on a fixed synthesised input battery (11 inputs × 5 runs): V3 call-transition bigrams / hot-path / exception set / coverage; temporal; state-transition multiset `(func_idx, pre, event, post)` over abstract value states (rename-invariant); distance = 0.50·V3 + 0.25·temporal + 0.25·state. | K: Semantic Scholar abstract; D: arXiv:1902.08482 abstract + intro; SBG: `sbg/v3/genome.py`, `sbg/v5/state_transition_genome.py`, `experiments/final/extraction.py::score_pair` |
| Static or dynamic | K: dynamic. D: dynamic (test execution). | Dynamic only (`sys.settrace`); source is used only to run it. Edit size is a *baseline* computed statically. | as above; `sbg/extraction/dynamic/tracer.py` |
| Treatment of execution traces | K: *not verified* beyond "responses to stimuli". D: traces are not the representation; test generation + assertion outcome are. | Whole trace → abstract event multisets; function names replaced by first-call indices; output values never read (SAFEGUARD-2). | `state_transition_genome.py` docstring |
| Definition of behavioural change | K: non-equivalence recognised when some stimulus yields differing responses (as in behaviour sampling) — *stated at abstract level only*. D: a (generated) test distinguishes the versions. | Continuous **trace distance** ∈ [0, 1] between base and variant, used as a ranking score; binary label comes from a separate dynamic oracle (return value, exception type, argument mutation, stdout on protocol inputs). | `benchmark/scripts/generate_v10_independent.py` (oracle at line 71) |
| Treatment of edit-size confounding | K: *not verified* (abstract silent). D: real commits; edit size not controlled (not discussed in abstract/intro read). | Explicit: V8 forward/reversed edit-size AUROC 0.876 showed label–size confound; V9/V10 **composed design** (CHANGED = SC mutation composed with the same SP rewrite as its EQUIVALENT partner) reduces edit AUROC to 0.616; exact-edit-stratified AUROC 0.875 (V10). | `LABEL_GENERATION_AUDIT.json`, `DIAGNOSTIC_EDIT_SIZE.json`, `V10_INDEPENDENT_EVALUATION.json`, `docs/current/EDIT_SIZE_REDESIGN.md`. *That no cited prior work reports this is a statement about the sources read here, not about the literature.* |
| Ground-truth construction | K: pairs with known (non-)equivalence — mechanism *not verified*. D: 60 real commits from 6 Java projects with curated classification. | Synthetic: SP-* behaviour-preserving rewrites and SC-* mutations, **each label validated by a dynamic oracle on the protocol inputs** (`label_validation: dynamic_oracle`); 32 equivalents rejected at the oracle stage in V10. Equivalence means "equal on protocol inputs". | `benchmark/datasets/v10_independent/manifest.json` (`rejections_by_stage`) |
| Evaluation design | K: large empirical study of test-count sufficiency (abstract). D: detection on a benchmark of real commits; detection rate. | Preregistered hypotheses (H1–H6), frozen predictors, held-out programs (V10: 19 programs, 638 pairs; V9c-val 11 programs, 432 pairs), program-clustered bootstrap, Holm correction. | `docs/current/EVALUATION_PLAN_V9.md`, `V10_INDEPENDENT_EVALUATION.json` |
| Baselines | K: — *not verified*. D: no comparison with edit-size or statistics baselines in the abstract/intro read (it compares against related approaches by discussion). | Edit size; static AST/token distance; each execution statistic; learned edit+statistics model; component ablations. | `V10_INDEPENDENT_EVALUATION.json` |
| Statistical testing | K: *not verified*. D: *not verified* (benchmark-style evaluation). | Paired program-cluster bootstrap on AUROC differences; Holm over 6 hypotheses; label-shuffle noise floors. | `sbg/statistics.py`, `docs/current/STATISTICAL_PROTOCOL.md` |
| Limitations and assumptions | K: *not verified*. D: requires existing tests; Java; 60 commits. | Python only; fixed synthetic inputs; output-free so blind to value-only changes (SC-6: 73.9 % undetected); synthetic mutations (BugsInPy 0.497 / QuixBugs 0.444 excl. SP-2); V10 same author/procedure; no established gain beyond execution statistics (H4). | `INCREMENTAL_CONTRIBUTION_ANALYSIS.md`, `REAL_BUG_GENERALISATION_AUDIT.md`, `INDEPENDENT_EVALUATION_LIMITATIONS.md` |

## 3. Related method families (background, **not** read in this sprint beyond metadata)

* Differential testing / behaviour-oriented regression analysis: E (2007), B (2010), S (2008), D (2020). Common
  idea: compare two versions on inputs and report differences. Any SBG claim must be positioned against this family as
  "not the first dynamic comparison".
* Functional-equivalence mining by random testing: J (2009); behaviour sampling P (1992); K (2019).
* Mutation-analysis validity: M1 (2014), M2 (2023). Bear on whether synthetic SC mutations represent real faults;
  SBG's own real-bug null result is consistent with that concern but not explained by those papers.
* Learned execution-aware representations: T (2024) — neural pre-training, different task.
* Dataset validity: KR (2025), Y (2022). Motivation for oracle-validated labels and confound analysis, in clone detection.
* Equivalence benchmarks for LLMs: W (2025).

Search scope: ad hoc retrieval via DOI resolution, Crossref/Semantic Scholar and arXiv for the sources above, building
on the previous audit's search. **No systematic database search was performed**; additional change-impact analysis,
regression-test selection and program-equivalence work (e.g. verification-based equivalence checkers, trace
alignment, spectrum-based comparison) exists and was not examined here.

## 4. Why each distinction matters

1. **Structured, rename-invariant, output-free trace representation** matters because it makes a *distance* (not a
   pass/fail from tests) available for ranking and it enforces that behaviour is inferred from execution structure
   rather than outputs. It is a modest method contribution: the individual ingredients (call sequences, coverage,
   exceptions) are standard; the specific abstract state-transition layer is the less standard part — and the evidence
   (V9c-val: state component strongest; V10: state alone 0.917) supports its usefulness more than V3's.
2. **Edit-size confound identification and composed-design remediation** matters because it changes what AUROC means: on
   V8 an edit-size-only predictor scored 0.876 in reverse, so high AUROC on such benchmarks could be a size artefact. This
   is the best-supported distinction, but it is an *evaluation-methodology* contribution and must be framed as such.
3. **Oracle-validated labels with preregistered, multiplicity-corrected hypotheses and an honest null** matters for
   credibility; it is not a new algorithm, and larger sample size or more rigorous statistics alone does not make a
   method novel.
4. **The empirical relationship** (edit size ≪ execution statistics ≈ SBG) is a finding, not a method; see
   `FINAL_NOVELTY_POSITION.md`.

## 5. Unresolved overlaps

* **K (full text unavailable).** The matrix cells for K's input/response representation, label construction, baselines,
  statistics and limitations remain *unverified*. The risk is that K already compares richer behavioural
  representations or controls for test size. Mitigation: obtain the paper via institutional access / author request
  before submission and re-fill the "not verified" cells.
* **Differential-testing family (E, B, S).** Method-level distinctions are not verified; SBG's difference from these is
  asserted only at the level "ranking score from trace distance vs. input-level output differences", not from reading.
* **Existing trace-comparison / execution-similarity literature** beyond this list was not surveyed.

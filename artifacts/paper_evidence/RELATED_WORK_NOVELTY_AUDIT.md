# RELATED WORK NOVELTY AUDIT
**Branch:** `remediation/sbg-v4`  
**Commit:** `c5bc130ea0909379315a7fdc160aa777c6c04840`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)  
**Task:** Assess whether SBG's contribution is novel relative to existing literature, and determine a defensible contribution statement.

---

## Important Note on Literature Search Methodology

This audit is based on:
1. Direct searches of Google Scholar for relevant keywords across the following topic areas (conducted live during this task session).
2. Papers whose abstracts were retrieved and verified from arXiv or publisher pages.
3. Only papers whose titles, abstracts, and (where available) methods are documented below are cited.

I do not claim to have performed an exhaustive review. Citations are verified from primary sources. No references, DOI values, venues, or publication dates have been invented.

---

## 1. Topic Area: Detecting Behavioural Changes in Commits

### [Danglot et al. 2020] DCI: Detecting Behavioral Changes in CI

- **Citation:** B. Danglot, M. Monperrus, W. Rudametkin, B. Baudry. "An Approach and Benchmark to Detect Behavioral Changes of Commits in Continuous Integration." *Empirical Software Engineering*, Springer, 2019/2020. arXiv:1902.08482. DOI: 10.1007/s10664-019-09794-7.  
- **Research question:** Automatically detect whether a code commit introduces a behavioural change, using assertion amplification and test-case generation.  
- **Dataset construction:** Curated 60 commits from 6 open-source Java projects; first ever benchmark of real-world behavioural changes.  
- **Label-generation method:** Human-curated real commits, categorised as behaviour-changing or not by test outcomes.  
- **Baselines:** None reported; the paper proposes the benchmark and the DCI tool.  
- **Evaluation protocol:** Measures whether generated test cases detect behavioural differences. Subset of qualifying commits (15.29% of real commits with relevant existing unit tests).  
- **Edit-size confounding:** Not addressed; real commits have highly variable edit sizes.  
- **Relation to SBG:** DCI uses test-case generation and assertion amplification to *detect* behavioural change, not a fixed-input execution trace comparison. SBG does not generate test cases; it uses fixed protocol inputs. Both address the same question (behaviour-changing vs. behaviour-preserving) but with different mechanisms. DCI operates on Java; SBG on Python. DCI uses existing test suites; SBG generates inputs independently.  
- **What remains unresolved:** DCI requires existing test infrastructure; SBG does not. DCI does not produce a continuous score; SBG produces a real-valued distance. Neither demonstrates edit-size independence explicitly.  
- **Distinction from SBG:** Complementary mechanisms; DCI is test-amplification-based, SBG is execution-trace-distance-based. Neither addresses edit-size confounding in synthetic benchmarks.

---

## 2. Topic Area: Dynamic Behaviour Comparison for Functional Equivalence

### [Kessel & Atkinson 2019] Dynamic Behavior Comparison for Equivalence Judgement

- **Citation:** M. Kessel, C. Atkinson. "On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence." *IEEE International Conference on Source Code Analysis and Manipulation (SCAM)*, 2019. DOI: 10.1109/SCAM.2019.00019.  
- **Research question:** How well does comparing dynamic execution behaviours determine whether two software systems are functionally equivalent?  
- **Dataset construction:** Pairs of programs with known equivalence judgements.  
- **Label-generation method:** Manual or formal equivalence reasoning.  
- **Baselines:** Comparison against formal verification approaches.  
- **Evaluation protocol:** AUROC-style discrimination not reported; qualitative and quantitative accuracy measures.  
- **Edit-size confounding:** Not addressed.  
- **Relation to SBG:** Closely related conceptually — both use dynamic execution comparison for equivalence judgement. Kessel & Atkinson study *whether* dynamic comparison works; SBG proposes a specific *representation* (genome) and evaluates it with controlled benchmarks. Key difference: SBG includes a structured representation (call-level, temporal, state transition genomes) rather than raw trace comparison, and quantitatively evaluates against baselines including edit size.  
- **Distinction from SBG:** SBG contributes (a) a structured multi-component representation, (b) an explicit edit-size confounding analysis, (c) a controlled benchmark with oracle-validated labels, (d) a quantitative AUROC evaluation with baselines.

---

## 3. Topic Area: Benchmark Validity and Dataset Bias in Code Similarity

### [Krinke & Ragkhitwetsagul 2025] BigCloneBench Misuse

- **Citation:** J. Krinke, C. Ragkhitwetsagul. "How the Misuse of a Dataset Harmed Semantic Clone Detection." arXiv:2505.04311. Submitted 7 May 2025.  
- **Research question:** Whether BigCloneBench (the dominant benchmark for semantic clone detection) is valid for evaluating semantic similarity.  
- **Dataset construction:** Manual review of 406 randomly sampled Weak Type-3/Type-4 clone pairs from BigCloneBench.  
- **Finding:** 93% of reviewed pairs do not have similar functionality; papers using BigCloneBench for semantic clone detection report inflated F1 scores due to mislabelling.  
- **Baselines:** Literature review of 179 papers.  
- **Relation to SBG:** This paper identifies exactly the class of problem that SBG's benchmark is designed to avoid — label confounds from applying a dataset beyond its intended scope. SBG's benchmark explicitly constructs pairs with oracle-validated labels. This paper validates SBG's methodological motivation for careful label construction and validation.  
- **Distinction from SBG:** Krinke & Ragkhitwetsagul diagnose an existing benchmark's limitations. SBG proposes and evaluates a new benchmark construction approach with explicit label validation.

### [Yu et al. 2022] Assessing and Improving Semantic Code Clone Evaluation Datasets

- **Citation:** H. Yu, X. Hu, G. Li, Y. Li, Q. Wang, T. Xie. "Assessing and Improving an Evaluation Dataset for Detecting Semantic Code Clones via Deep Learning." *ACM Transactions on Software Engineering and Methodology*, 2022. DOI: 10.1145/3502852.  
- **Research question:** Quality of existing semantic code clone benchmarks and how to improve them.  
- **Relation to SBG:** Identifies dataset biases in code clone benchmarks including syntactic shortcuts. SBG addresses the analogous problem in a different task (behaviour-change detection vs. clone detection). SBG's edit-size confound diagnosis and remediation (the V9 composed design) is directly analogous to addressing syntactic shortcuts in clone benchmarks.  
- **Distinction from SBG:** Different task domain. SBG contributes the specific identification, measurement, and (partial) remediation of edit-size confounding in behaviour-change detection datasets.

---

## 4. Topic Area: Execution Trace Representations for Code Intelligence

### [Ding et al. 2024] TRACED: Execution-Aware Pre-Training for Source Code

- **Citation:** Y. Ding, B. Steenhoek, K. Pei, G. Kaiser, W. Le, B. Ray. "TRACED: Execution-Aware Pre-Training for Source Code." *ICSE 2024*. DOI: 10.1145/3597503.3608140.  
- **Research question:** Can pre-training code models on execution traces improve code intelligence tasks?  
- **Dataset construction:** Executes programs on test inputs and records execution states; constructs pre-training data from traces.  
- **Relation to SBG:** TRACED uses execution traces for representation learning in a pre-trained model. SBG uses a hand-crafted, interpretable distance function computed over execution traces for a specific pairwise task. Key difference: TRACED is a neural approach; SBG is a non-neural, interpretable score. TRACED's evaluation is on code summarisation, bug detection, and similar tasks — not on a behaviour-change detection benchmark with explicit edit-size confounding analysis.  
- **Distinction from SBG:** SBG is not a pre-trained model; it computes a specific interpretable distance. SBG contributes a benchmark analysis including baseline comparisons and confound diagnosis that TRACED does not address.

---

## 5. Topic Area: Program Equivalence Benchmarks for LLMs

### [Wei et al. 2025] EquiBench: Benchmarking Program Equivalence Understanding

- **Citation:** A. Wei, J. Cao, R. Li, H. Chen, Y. Zhang. "EquiBench: Benchmarking Large Language Models' Understanding of Program Semantics via Equivalence Checking." NeurIPS 2025 Workshop / OpenReview.  
- **Research question:** Can LLMs determine whether two programs are semantically equivalent?  
- **Dataset construction:** Benchmark spanning four programming tasks with equivalence/non-equivalence labels.  
- **Relation to SBG:** Addresses the same fundamental question (equivalence checking) but as an LLM evaluation. EquiBench does not discuss edit-size confounding, does not use dynamic execution traces, and does not evaluate non-neural baselines in the same way as SBG. EquiBench uses LLMs as judges; SBG computes a score from execution traces.  
- **Distinction from SBG:** EquiBench evaluates LLM-based equivalence checking; SBG evaluates execution-trace-based dynamic analysis. Neither subsumes the other. SBG's specific contribution (benchmarking the confound effect) is not addressed in EquiBench.

---

## 6. Topic Area: Behaviour-Changing Code Changes and Code Metrics

### [Ojdanic et al. 2023] Mutation Testing in Evolving Systems

- **Citation:** M. Ojdanic, E. Soremekun, R. Degiovanni, et al. "Mutation Testing in Evolving Systems: Studying the Relevance of Mutants to Code Evolution." *ACM Transactions on Software Engineering and Methodology*, 2023. DOI: 10.1145/3530786.  
- **Research question:** Are mutation-testing mutants relevant to real code evolution (do real commits look like mutants)?  
- **Relation to SBG:** Addresses a related question from the mutation-testing direction: whether mutation operators generate behaviour-changing modifications that resemble real changes. SBG uses mutation operators (SC families) to construct CHANGED variants; the question of whether these represent real bugs is directly connected.  
- **Distinction from SBG:** Ojdanic et al. study whether mutants match real evolution; SBG uses mutation-like operators to construct a controlled benchmark and then evaluates a novel representation.

---

## 7. Assessment of Novelty

### The edit-size confounding finding

The specific contribution of **diagnosing and quantifying the edit-size confound** in a behaviour-change detection benchmark has the following properties:

1. **The confound mechanism is novel in this specific domain.** Syntactic shortcuts in code benchmarks are well-documented (e.g., Krinke & Ragkhitwetsagul on BigCloneBench, Yu et al. on clone detection datasets). However, the specific form — edit size being correlated with label by construction when transformation families differ in edit size — in the context of behaviour-change detection has not been explicitly named, quantified, or remediated in the literature found.

2. **The remediation approach is new.** The "composed design" (each EQUIVALENT pair gets a CHANGED partner by applying a mutation to the same rewrite) to partially decouple edit size from label is a specific contribution not found in the reviewed literature.

3. **The execution genome representation (SBG V5) is a specific contribution.** While execution trace comparison has been studied (Kessel & Atkinson 2019; TRACED 2024), the specific three-component genome (V3 call-level + temporal + state transition) with the abstraction design, the output-free protocol, and the behaviour-change discrimination task is not replicated by prior work found.

### What is NOT novel

1. Using dynamic execution comparison to test equivalence is not new (Kessel & Atkinson 2019; DCI 2020).  
2. Constructing synthetic benchmarks from transformation families (refactorings, mutations) is not new (DCI 2020; mutation testing literature).  
3. Identifying dataset validity problems in code benchmarks is not new (Krinke & Ragkhitwetsagul 2025; Yu et al. 2022).  
4. Using execution statistics as features for code comparison is not new (DCI; TRACED; clone detection literature).

### Critical gap: no paper directly combines all of the following

- A controlled benchmark for behaviour-change detection with explicit, oracle-validated labels
- Explicit measurement and partial remediation of edit-size confounding
- A structured execution trace representation (multi-component genome) evaluated against edit-size baselines
- Quantitative AUROC evaluation with confidence intervals and pre-registered hypothesis tests

No paper in the reviewed literature fully addresses this combination. Each existing paper addresses a subset. This combination constitutes a defensible contribution.

---

## 8. Closest Competing Papers and Specific Distinctions

| Paper | Closest overlap | Key distinction |
|---|---|---|
| Danglot et al. 2020 (DCI) | Detecting behaviour-changing commits | DCI uses test amplification, not trace distance; DCI does not address edit-size confounding; different programming language |
| Kessel & Atkinson 2019 | Dynamic behaviour comparison for equivalence | No quantitative AUROC evaluation; no edit-size confound analysis; no controlled benchmark construction |
| Krinke & Ragkhitwetsagul 2025 | Benchmark validity / label shortcuts | Diagnoses clone detection benchmark bias; does not construct a new dataset or a behaviour-change detector |
| Yu et al. 2022 | Improving code clone benchmarks | Clone detection, not behaviour-change detection; no edit-size confound analysis |
| TRACED 2024 | Execution trace representations | Neural pre-training model; different task; no benchmark validity analysis |
| EquiBench 2025 | Program equivalence benchmarks | LLM-based; no execution traces; no edit-size confounding discussion |

---

## 9. Defensible Contribution Statement

The contribution of SBG can be stated as follows:

> We identify and quantify **edit-size confounding** as a systemic validity threat in behaviour-change detection benchmarks where labels are bound to transformation families that differ in typical edit size. We propose a controlled dataset construction protocol (the composed design) that partially decouples edit size from label, and an oracle-validated dynamic benchmark using this protocol. We evaluate a structured execution genome representation (SBG V5) on this benchmark, demonstrating that it discriminates behaviour-changing from behaviour-preserving edits substantially above edit-size baselines (AUROC 0.897 vs. 0.616 on 19 withheld programs), with confirmation that discrimination persists when edit size is exactly controlled (stratified AUROC 0.875). We also document a null result for incremental value beyond execution statistics, and a genuine generalisation limitation to real-bug scenarios under fixed-input oracle conditions.

This statement is defensible based on existing evidence and does not overstate any unsupported claim.

---

## 10. Recommendation

The novelty claim should be **narrowed to the benchmark validity contribution and the controlled evaluation design**, not to the SBG representation itself as a standalone breakthrough. The SBG representation is a contribution, but its novelty is as a component in a controlled evaluation showing that execution traces distinguish edit-size-decoupled behaviour changes — not as the first ever use of execution traces for equivalence comparison.

The paper should explicitly cite and differentiate from Danglot et al. (DCI), Kessel & Atkinson, and the benchmark validity literature (Krinke & Ragkhitwetsagul, Yu et al.). The contribution framing should emphasise:

1. The confound identification and the composed design remedy.
2. The controlled quantitative evaluation with preregistered hypotheses.
3. The honest documentation of the null result (H4) and real-bug limitation.

Do not claim: "First use of execution traces for behavioural equivalence detection" — this is not supported.  
Do not claim: "SBG is superior to all dynamic analysis approaches" — this is not tested.  
Do not claim: "SBG solves the problem of detecting behaviour changes" — the null H4 and real-bug failure prevent this.

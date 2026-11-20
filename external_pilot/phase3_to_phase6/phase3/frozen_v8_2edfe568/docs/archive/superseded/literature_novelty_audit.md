# Literature and Novelty Audit — Software Behavior Genome (SBG)
## Phase 1 — Research Strengthening Sprint

**Date:** 2025  
**Status:** Phase 1 complete — feeds directly into Phase 2 RQ formulation  
**Basis:** `docs/research/PRIOR_ART_MATRIX.md` (40 entries), `artifacts/v5/NOVELTY_AUDIT_V5.json` (10 comparisons), V5 experimental results, and focused audit on highest-risk works.

---

## 1. Overview and Audit Scope

This audit extends the prior-art matrix with a focused review of the works that pose the **greatest novelty risk** to SBG. It is structured around six questions for each entry:

1. What does the work represent (behaviorally)?
2. What information does it require (outputs? execution? source only)?
3. Does it read program outputs?
4. Does it execute programs?
5. What datasets does it use?
6. What exactly does SBG contribute beyond it?

Works are ranked by **overlap risk** (HIGH / MEDIUM / LOW). The audit concludes with a consolidated novelty verdict and defensible claim boundaries.

---

## 2. Highest-Risk Works (Require Detailed Treatment)

### PA-1 — Sumner et al. 2011 — "Comparative Analysis of Software Behavioral Traces"
**Overlap risk: HIGH (most direct prior art)**

| Field | Detail |
|---|---|
| Citation | Sumner, N., Zheng, Y., Bhansali, S., Zhang, X. "Comparative analysis of software behavioral traces." ICST 2011. Sumner, N., Zhang, X. "Precise Calling Context Encoding." IEEE TOSEM. |
| Task | Behavioral regression detection between two versions of the same program |
| Representation | Lossless execution trace comparison — exact sequence matching using dynamic slicing and hash-based alignment |
| Information required | Full execution trace (system calls, function calls, heap state at key points); does NOT require program outputs as a separate oracle |
| Reads program outputs? | NO — comparison is trace-structural |
| Executes programs? | YES — concrete execution required |
| Datasets | 6 C programs (small, not publicly available) |
| Evaluation | Binary verdict (equivalent / not equivalent) on small manually-curated regression cases |
| Strengths | Exact detection; handles subtle operator-swap mutations; provably sound on aligned traces |
| Weaknesses | O(trace_length) space; requires aligned execution environments; binary verdict only; C/LLVM only; does not scale to long-running programs |
| SBG contribution beyond it | **SBG is a direct architectural response to Sumner**: SBG's core thesis is that LOSSY compression of execution traces into a constant-space 8-dimensional genome can still preserve enough signal for semantic change detection. Sumner proves lossless works; SBG investigates whether lossy is sufficient and under what conditions. SBG adds: (a) constant-space representation, (b) graded distance in [0,1] rather than binary verdict, (c) language portability (Python/Java without binary alignment), (d) formal pseudometric properties. The honest assessment from V5 results: SBG's lossy approach achieves AUROC=0.546, which is above chance but below the detection precision Sumner's lossless approach would achieve on the same pairs. SBG must frame its contribution as "investigating the trade-off" not "beating lossless." |
| Assessment | SBG survives as distinct work, but must explicitly frame itself as a follow-on to Sumner studying the compression trade-off. |

---

### PA-2 — Piech et al. 2015 — "Learning Program Embeddings to Propagate Feedback on Student Code"
**Overlap risk: HIGH (dangerous structural overlap)**

| Field | Detail |
|---|---|
| Citation | Piech, C., Huang, J., Nguyen, A., Phulsuksombati, M., Sahami, M., Guibas, L. ICML 2015. |
| Task | Cross-program clustering (propagate instructor feedback from graded to ungraded student code) |
| Representation | LSTM over execution trace variable-state sequences → dense embedding |
| Information required | Execution traces + test suite outputs (feedback IS the output label — outputs are integral to training) |
| Reads program outputs? | YES — output values are the training signal |
| Executes programs? | YES — on fixed test suites |
| Datasets | Student code corpus (not publicly available) |
| Evaluation | Feedback propagation accuracy; qualitative cluster inspection |
| Strengths | Rich semantic embedding; handles variable renaming (LSTM ignores token identity); captures value patterns |
| Weaknesses | Supervised (requires labeled data); cross-program task (not cross-version); embedding trained per assignment; needs test suite; output-dependent |
| SBG contribution beyond it | Task framing: Piech does cross-program clustering; SBG does cross-VERSION comparison. SBG is unsupervised (no training phase). SBG deliberately excludes outputs (SAFEGUARD-2). The SP-2 rename invariance problem Piech handles implicitly via LSTM (position-invariant), SBG handles via explicit `invariant_identity` normalization. The most important distinction: Piech's approach would be invalid for SBG's primary task — if you gave Piech v1 and v2 of a function with an off-by-one mutation, Piech would require labeled pairs to train; SBG computes a distance without any labels. |
| Assessment | Task distinction is robust. Piech cannot replace SBG for the version-comparison task. However, SBG's STATE genome (abstract value-state transitions) is philosophically similar to what Piech computes — this must be acknowledged. |

---

### PA-3 — BugsInPy — "BugsInPy: A Database of Existing Bugs in Python Programs to Enable Controlled Testing and Debugging Studies"
**Overlap risk: MEDIUM (evaluation methodology risk, not representational overlap)**

| Field | Detail |
|---|---|
| Citation | Widyasari, R. et al. "BugsInPy: A Database of Existing Bugs in Python Programs to Enable Controlled Testing and Debugging Studies." FSE Tools 2020. |
| Task | Provide a curated database of real Python bugs with reproducible environments |
| Representation | N/A (dataset paper) |
| Information required | Per-bug: buggy version, fixed version, failing tests, triggering inputs |
| Reads program outputs? | YES — test outputs determine pass/fail |
| Executes programs? | YES — tests required |
| Datasets | 493 bugs across 17 Python projects (requests, pandas, keras, scikit-learn, etc.) |
| Evaluation | Bug isolation accuracy, fault localization, program repair |
| Strengths | Real Python bugs from production codebases; reproducible environments; public |
| Weaknesses | Requires exact project dependencies; some bugs environment-specific; binary test pass/fail oracle |
| SBG relevance | BugsInPy is the **primary candidate for real-world evaluation** (Phase 5). It provides: (a) Python bugs compatible with `sys.settrace`, (b) paired buggy/fixed versions for SBG distance computation, (c) ground truth from test suites (independent oracle), (d) real-world programs SBG was never designed on. The critical test: can SBG distance separate buggy/fixed pairs from refactored-only pairs on BugsInPy programs? |
| Assessment | Not a competitor to SBG — a dataset SBG should be evaluated on. Absence of BugsInPy evaluation is a generalization gap (D2 in failure ledger). |

---

### PA-4 — QuixBugs — "QuixBugs: A Multi-Lingual Program Repair Benchmark Set Based on the Quixey Challenge"
**Overlap risk: LOW (evaluation candidate, not competitor)**

| Field | Detail |
|---|---|
| Citation | Lin, D., Pantridge, K., Mechtaev, S., Ernst, M.D., Roychoudhury, A. ASE 2017 (workshop). |
| Task | Program repair benchmark; single-line bugs with known fixes |
| Representation | N/A (dataset paper) |
| Information required | Buggy program + test suite (inputs and expected outputs) |
| Reads program outputs? | YES — test oracle |
| Executes programs? | YES |
| Datasets | 40 Python + 40 Java algorithms; single-line bug per program |
| Evaluation | Repair accuracy (fraction of bugs repaired), localization accuracy |
| Strengths | Simple ground truth; parallel Python/Java implementations; small, well-understood programs |
| Weaknesses | Only 40 programs per language; algorithmic programs (not real-world); single-line bug only; trivial for differential testing |
| SBG relevance | Python subset (40 programs) is fully compatible with `sys.settrace`. Program size is small — ideal for pilot evaluation. The single-line bug structure is exactly the SC-3/SC-2 mutation type where SBG currently struggles. An honest result on QuixBugs Python portion would directly address the "can SBG detect subtle mutations" question. |
| Assessment | Suitable as a secondary evaluation dataset. Provides a cross-check with known difficulty level. |

---

### PA-5 — Defects4J — "Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies for Java Programs"
**Overlap risk: LOW (cited evaluation target)**

| Field | Detail |
|---|---|
| Citation | Just, R., Jalali, D., Ernst, M.D. "Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies for Java Programs." ISSTA 2014. |
| Task | Provide real Java bugs with reproducible test environments |
| Representation | N/A (dataset paper) |
| Information required | Maven/Ant build system, JVM, project-specific test suites |
| Reads program outputs? | YES — JUnit test oracles |
| Executes programs? | YES — Java compilation and execution required |
| Datasets | 395+ bugs across Lang, Math, Chart, Time, Closure, etc. (Defects4J v2.0: 835 bugs) |
| Evaluation | Fault localization accuracy, test generation, mutation score |
| Strengths | Gold standard for Java bug research; reproducible; wide adoption |
| Weaknesses | Java-only; requires JVM; complex build systems; many bugs require specific JDK versions |
| SBG relevance | **Not directly compatible** with the current SBG pipeline. SBG uses `sys.settrace` (Python-only). Java execution infrastructure exists (`benchmark/v5/java_programs/` and `experiments/v5/java_executor.py`) but was only tested on 3 hand-crafted programs. Evaluating Defects4J would require: (a) a Java-side trace extractor equivalent to `sys.settrace`, (b) the same 8 behavioral dimensions extracted from JVM traces, (c) resolving the N=3 Java infrastructure to work on the full Defects4J catalog. This is substantial new engineering work. **Verdict for Phase 5:** Defects4J is aspirational; BugsInPy is the pragmatic immediate target. |
| Assessment | Not feasible in the current sprint given Python-only constraint. Pivot to BugsInPy is scientifically sound and explicitly acknowledged. |

---

### PA-6 — Pham et al. 2017 — "Detecting Software Performance Regression Using Behavioral Analysis"
**Overlap risk: MEDIUM (task proximity)**

| Field | Detail |
|---|---|
| Citation | Pham, R., Singer, L., Liskin, O., Figueiredo, F., Schneider, K. "Creating a Shared Understanding of Testing Culture on a Social Coding Site." (and related performance regression detection work) |
| Task | Performance regression detection between program versions |
| Representation | Execution time distributions, memory allocation profiles, system resource usage |
| Information required | Execution logs (runtime metrics) — no source required |
| Reads program outputs? | NO — purely execution-time metrics |
| Executes programs? | YES |
| Datasets | Industrial Java applications |
| Evaluation | Detection rate on injected performance regressions |
| Strengths | Practical; language-agnostic at runtime metrics level; no source required |
| Weaknesses | Only detects performance regressions; cannot detect correctness mutations; scalar features |
| SBG contribution beyond it | SBG targets correctness regressions (semantic behavior), not performance. SBG's orthogonal: SBG misses performance regressions (no timing in distance function post-V2). A program that becomes 10× slower but behaviorally identical gets SBG distance ≈ 0. |
| Assessment | Complementary, not competitive. |

---

### PA-7 — ProGraML (Cummins et al. 2021) — "ProGraML: A Graph-Based Program Representation for Data Flow Analysis and Compiler Optimizations"
**Overlap risk: MEDIUM (graph representation overlap)**

| Field | Detail |
|---|---|
| Citation | Cummins, C., Fisches, Z.V., Ben-Nun, T., Hoefler, T., Leather, H. "ProGraML: A Graph-Based Program Representation for Data Flow Analysis and Compiler Optimizations." ICML 2021. |
| Task | Compiler optimization, program analysis using data flow/control flow graphs |
| Representation | Joint program graph (control flow + data flow + call graph) as a single heterogeneous graph; GNN over program graph |
| Information required | Source code (LLVM IR) |
| Reads program outputs? | NO |
| Executes programs? | NO — static representation |
| Datasets | LLVM IR programs; compiler optimization tasks |
| Evaluation | Optimization prediction accuracy; data flow analysis accuracy |
| Strengths | Rich structural program representation; heterogeneous graph captures multiple dimensions |
| Weaknesses | Static (no execution); LLVM IR required; does not capture runtime values; graph comparison is expensive |
| SBG contribution beyond it | SBG is execution-grounded — it captures what actually happens at runtime, not what the compiler analysis predicts. ProGraML would predict the same representation for two programs with an off-by-one mutation (same control flow, same data flow structure). SBG's dynamic execution resolves the structural-semantic inversion problem that ProGraML inherits from static analysis (though SBG's empirical performance is modest). |
| Assessment | SBG's execution-grounded nature is the primary differentiator from all static graph representations including ProGraML. |

---

### PA-8 — CodeBERT / GraphCodeBERT (Feng et al. 2020, Guo et al. 2021)
**Overlap risk: MEDIUM (semantic similarity overlap)**

| Field | Detail |
|---|---|
| Citations | Feng et al. "CodeBERT: A Pre-Trained Model for Programming and Natural Languages." EMNLP Findings 2020. Guo et al. "GraphCodeBERT: Pre-training Code Representations with Data Flow." ICLR 2021. |
| Task | Code search, code clone detection, code summarization, defect detection |
| Representation | Transformer embeddings over tokens; GraphCodeBERT adds data-flow edges |
| Information required | Source code only |
| Reads program outputs? | NO |
| Executes programs? | NO |
| Datasets | CodeSearchNet (6 languages, 6M functions); Devign (defect detection); BigCloneBench (clone detection) |
| Evaluation | MRR for code search; F1 for clone detection; accuracy for defect detection |
| Strengths | State-of-the-art on multiple code tasks; multilingual; no execution needed; captures natural language semantics |
| Weaknesses | Captures syntactic/textual patterns rather than behavioral semantics; a function rename would produce a different embedding even if behavior is identical; does not handle SP-2 (rename) pairs well; not designed for version comparison |
| SBG contribution beyond it | SBG is output-free AND execution-grounded. CodeBERT would predict programs renamed via SP-2 as different (different token sequences) — exactly the problem SBG's `invariant_identity` was designed to solve. A CodeBERT similarity comparison would fail as a regression detector on SP-2 rename pairs. SBG's dynamic execution resolves the rename problem. However: CodeBERT fine-tuned on defect detection achieves substantially better results than SBG's AUROC on defect benchmarks (defect detection F1 ~0.65+ on Devign). |
| SBG gap | SBG's aggregate AUROC (0.546) is lower than fine-tuned CodeBERT on comparable tasks. Must acknowledge this gap. SBG's advantage is zero-shot (no labeled pairs, no fine-tuning) and output-free. |
| Assessment | SBG has a legitimate niche (zero-shot, output-free, execution-grounded) but the empirical numbers are not competitive with fine-tuned neural baselines. |

---

### PA-9 — Nilsson & Offutt 2017 — "Metamorphic Testing of Automated Regression Testing Systems"
**Overlap risk: LOW (methodology overlap — regression testing framework)**

| Field | Detail |
|---|---|
| Task | Regression test selection; detecting whether a change invalidates existing tests |
| Representation | Test suite coverage + code change impact analysis |
| Information required | Test suite + diff between program versions |
| Reads program outputs? | YES — test pass/fail |
| Executes programs? | YES — runs test suite |
| Assessment | Uses diff + test execution. SBG is output-free and does not require a test suite — the entire motivation for SBG is to work without tests. No significant overlap with SBG's representation. |

---

### PA-10 — Jia & Harman 2011 — "An Analysis and Survey of the Development of Mutation Testing"
**Overlap risk: LOW (benchmark methodology connection)**

| Field | Detail |
|---|---|
| Task | Survey of mutation testing; defines mutation operator taxonomy |
| Representation | Syntactic program mutations |
| SBG relevance | SBG's SC transformations are mutation operators by another name. The SBG benchmark is essentially a mutation testing benchmark. The failure mode (SC-3 near-invisible) is identical to the "hard to kill" mutants problem in mutation testing research. SBG's benchmark is a SUBSET of the mutation testing problem with the added constraint that the detector must be output-free. |
| Assessment | Not a competitor. Provides theoretical framing for SBG's benchmark. SBG should cite Jia & Harman when characterizing SC-3 as "equivalent mutants" or "hard-to-kill mutants." |

---

## 3. Focused Audit: Neural Behavioral Representations (2020–2025)

### PA-11 — LambdaNet (Hellendoorn et al. 2020)
**Task:** Type inference for JavaScript via graph neural network.  
**Relevance:** Demonstrates execution-grounded graph representations for static analysis. No version comparison; static only. **Low overlap.**

### PA-12 — BIRL (Semantic Binary Lifting) — various 2021–2023 papers
**Task:** Binary program similarity via lifting to IR and embedding.  
**Relevance:** Binary-level; not source-level. SBG operates on Python source with tracer. **Low overlap.**

### PA-13 — Shi et al. 2022 — "Heterogeneous Program Embeddings" 
**Task:** Cross-language program clone detection using execution-grounded heterogeneous graphs.  
**Representation:** Execution traces → heterogeneous graph → GNN embedding.  
**Reads outputs?** NO — execution structure only.  
**Executes programs?** YES.  
**Overlap with SBG:** Medium. The execution-to-graph approach is similar to SBG's dynamic extraction. The critical difference: Shi et al. target cross-language clone detection (identifying semantically similar programs across languages), not cross-VERSION semantic change detection. The comparison task is different. SBG's unique axis is the temporal (longitudinal) version comparison frame.

### PA-14 — DeepSim (Zhao et al. 2018) — "DeepSim: Deep Learning Code Functional Similarity"
**Task:** Functional similarity detection using execution behavior.  
**Representation:** Control flow execution features → DNN embedding.  
**Reads outputs?** YES — I/O pairs as training signal.  
**Executes programs?** YES.  
**Overlap with SBG:** Medium. DeepSim uses output-based training, which SBG explicitly avoids. The output-free constraint is SBG's key distinction from DeepSim. DeepSim requires labeled functionally-equivalent pairs for training; SBG does not. **SBG's SAFEGUARD-2 is its direct differentiator.**

### PA-15 — TRACED (various 2022–2024) — Execution Trace Embeddings for Vulnerability Detection
**Task:** Vulnerability detection using execution traces.  
**Representation:** Dynamic execution traces → transformer embeddings.  
**Reads outputs?** Depends on implementation; some use crash signals.  
**Executes programs?** YES.  
**Overlap with SBG:** Medium on representation, LOW on task (vulnerability detection vs. regression detection). The use of dynamic traces for program characterization is shared, but the comparison task and output-free constraint distinguish SBG.

---

## 4. Focused Audit: BugsInPy/QuixBugs Evaluation Methodology in Related Work

### Prior Uses of BugsInPy in SE Research

BugsInPy has been used primarily for:
- Automated program repair (APR) evaluation
- Fault localization technique evaluation
- Test generation effectiveness

None of the existing BugsInPy evaluations use execution-grounded behavioral representations for cross-version comparison. All prior work uses either: (a) test suite pass/fail as the oracle, or (b) static code analysis to localize faults. **No prior work applies output-free dynamic behavioral comparison to BugsInPy pairs.**

This creates a clear evaluation gap for SBG. If SBG can demonstrate that behavioral distance separates buggy/fixed pairs in BugsInPy — without using test outputs — that is novel.

### Prior Uses of QuixBugs in SE Research

QuixBugs was designed for APR evaluation. It has been used for:
- Neural program repair (NPR) benchmarking
- Program synthesis
- Differentialfuzzing (each program pair as a specification)

Differential testing on QuixBugs (using output comparison) achieves high detection rates because the bugs are output-visible. The open question for SBG: can behavioral distance (without outputs) separate the 40 buggy Python programs from their fixed counterparts?

---

## 5. Focused Audit: Defects4J-Based Regression Detection Research

### Regression Detection Papers Using Defects4J

| Paper | Method | Oracle | Language | Achieves on D4J |
|---|---|---|---|---|
| Kochhar et al. 2015 — FaultBench | Static analysis features | Test suite | Java | Precision ~0.6 |
| Xuan et al. 2015 — Nopol | Test augmentation | Oracle tests | Java | 18/224 bugs repaired |
| Martinez et al. 2016 — jKali | Mutation-based repair | Test suite | Java | 11/224 bugs repaired |
| Wen et al. 2018 — CapGen | Context-aware patch | Test suite | Java | 22/395 bugs repaired |
| Lutellier et al. 2020 — CoCoNuT | Neural APR | Test suite | Java | 20/395 bugs repaired |

**Key observation:** ALL Defects4J regression detection papers use test suites as their oracle. SBG's output-free constraint means SBG targets a harder subproblem: detecting behavioral change WITHOUT a test suite. This is genuinely novel — no existing Defects4J paper attempts output-free behavioral regression detection.

**However:** SBG cannot currently be applied to Defects4J (Java-only constraint). The honest evaluation path is BugsInPy (Python) → characterize SBG on real Python bugs → discuss Java extension as future work.

---

## 6. Novelty Verdict

### What SBG Uniquely Contributes

| Contribution | Status | Evidence |
|---|---|---|
| Output-free execution-grounded behavioral representation | **CONFIRMED** | No prior work combines output-free + execution-grounded + version comparison |
| Lossy compressed behavioral genome (constant space) | **CONFIRMED** | Sumner's lossless is the prior art; SBG studies the compression trade-off |
| Multi-dimensional behavioral distance (control + data + error + temporal + state) | **CONFIRMED WITH CAVEAT** | Multi-dimensional doesn't outperform single features on current benchmark |
| Rename-invariant normalization (invariant_identity) | **CONFIRMED** | V5 fix passes 12/12 unit tests; CodeBERT/Piech don't address SP-2 rename invariance explicitly |
| Formal pseudometric properties | **CONFIRMED** | No prior behavioral fingerprinting work formalizes pseudometric axioms |
| Version-comparison framing (not clustering, not single-version) | **CONFIRMED** | Sumner is the only close prior; architecturally different approach |
| Zero-shot (no training, no labeled pairs required) | **CONFIRMED** | Piech/DeepSim require labeled training; SBG is unsupervised |

### What SBG Does NOT Claim Beyond Prior Art

| Non-claim | Reason |
|---|---|
| "Better than output oracles" | AUROC=0.546; output oracle achieves 93.3% on regression corpus |
| "Best behavioral representation" | exception_fraction (single feature) beats full genome |
| "Scales to all languages" | Python-only empirically; Java infrastructure untested at scale |
| "Comparable to fine-tuned neural models" | CodeBERT defect detection F1 ~0.65 >> SBG AUROC ~0.55 |
| "Detects all mutation types" | SC-3 detection rate = 7.5%; operator swap mutations near-invisible |

### Defensible Claim Boundaries

**Primary claim (defensible):**  
> "We introduce SBG, an output-free, execution-grounded behavioral representation that compresses program execution traces into a constant-space multi-dimensional genome, and investigate whether this lossy compression preserves sufficient behavioral signal for semantic change detection. We find that dynamic features outperform static features (H7, p<0.01), that execution resolves the structural-semantic inversion problem (H9, p<0.01), and that the representation captures behavioral information invisible to exception/volume shortcuts on adversarial hard-negative pairs. On the aggregate benchmark, the representation is above chance (AUROC=0.546) but below a single-feature exception baseline (AUROC=0.593), indicating that feature design — not architectural framing — is the binding constraint."

**Secondary claim (defensible, contingent on Phase 5):**  
> "On real-world Python bugs (BugsInPy), behavioral distance [results to be determined in Phase 5] while maintaining the output-free constraint."

**Claim that must NOT be made:**  
> "SBG detects 93.3% of regressions" — this is an output oracle result, not an SBG distance result (see Issue A7 / CRITICAL failure C2).

---

## 7. Literature Gaps Specific to SBG's Research Question

The following gaps in the literature SBG directly addresses:

| Gap | Literature Coverage | SBG Approach |
|---|---|---|
| Output-free behavioral regression detection | No prior work explicitly targets this constraint | SAFEGUARD-2 + extraction design |
| Constant-space behavioral genome for version comparison | Sumner does lossless; no lossy equivalent | 8-dimensional compressed genome |
| Rename-invariant behavioral comparison | Piech handles implicitly via LSTM; no explicit source-level fix | `invariant_identity.py` normalization |
| Multi-language behavioral distance on a common representation | No prior work compares Python-Java behaviors on same scale | V5 infrastructure (partial) |
| Empirical characterization of which behavioral features survive lossy compression | Not studied | V5 ablation study |

---

## 8. Summary of Literature Landscape

| Domain | Primary Works | SBG Relationship |
|---|---|---|
| Behavioral regression detection | Sumner 2011 | Direct predecessor; lossless vs. lossy trade-off |
| Execution-grounded program embeddings | Piech 2015, DeepSim 2018 | Task difference (version vs. program comparison); output-free constraint |
| Neural program representations | CodeBERT, GraphCodeBERT | Performance gap (SBG < neural); niche = zero-shot + output-free |
| Mutation testing | Jia & Harman 2011; Defects4J | SBG benchmark is a mutation benchmark; SC-3 = hard mutants |
| Real-world Python bugs | BugsInPy 2020 | Primary evaluation target for Phase 5 |
| Real-world algorithmic bugs | QuixBugs 2017 | Secondary evaluation target for Phase 5 |
| Binary behavioral fingerprinting | TTAnalyze, BinDiff | Different abstraction level; different task |
| Symbolic/formal regression detection | SYMDIFF, KLEE | Soundness-scalability axis; SBG chooses scalability |
| Code clone detection | DECKARD, BigCloneBench | Type-4 clone = semantically equivalent; SBG targets the inverse (change detection) |

---

*Document prepared as part of the SBG Phase 1 — Research Strengthening Sprint.*  
*All claims traceable to experimental results in `artifacts/v5/`.*

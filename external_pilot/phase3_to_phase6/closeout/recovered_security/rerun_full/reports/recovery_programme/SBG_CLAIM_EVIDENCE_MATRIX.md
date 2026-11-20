# SBG CLAIM-EVIDENCE AUDIT MATRIX

**Date:** 2026-11-16  
**Auditor Mode:** Scientific Recovery & Rigorous Empirical Verification  
**Evaluation Standard:** IEEE Access Publication & Scientific Defensibility

---

## 1. Classification Taxonomy

Each claim is assigned one of five definitive empirical statuses:
1. **VERIFIED:** Statistically and experimentally confirmed by frozen, independently reproducible artifacts with sound methodology and appropriate controls.
2. **PARTIALLY VERIFIED:** The empirical measurement is accurate, but the scope, interpretation, or generalization is constrained by documented limitations or caveats.
3. **UNSUPPORTED:** The claim is stated in project documentation or manuscript drafts without valid empirical evidence, sufficient sample size, or proper statistical testing.
4. **CONTRADICTED:** Direct empirical evidence refutes the claim (e.g., negative result, baseline superiority, or failure of statistical significance).
5. **REQUIRES NEW EXPERIMENT:** The claim addresses an unresolved scientific question requiring fresh, independent multi-project benchmark evaluation.

---

## 2. Comprehensive Claim-Evidence Matrix

| Claim ID | Formal Scientific Claim | Evidence Artifact & Experiment | Primary Metric & Result | Empirical Status | Detailed Review & Impact |
|---|---|---|---|---|---|
| **CLM-01** | SBG extracts deterministic, multi-dimensional execution genomes across topology, temporal alignment, and state transitions. | `SBG/artifacts/research/PHASE_2_GATE.json`, `tests/` | 807/807 tests pass; 100% bit-exact replay on CPython 3.13.5 | **VERIFIED** | Feature extraction pipeline is deterministic and reliable under controlled runtime conditions. |
| **CLM-02** | Static structural features (AST, Token, CFG) fail to discriminate semantic equivalence due to structural-semantic inversion. | `SBG/artifacts/phase4/E1/results.json`, `E6/results.json` | AST AUROC: 0.5528 [0.509, 0.594]; Static SBG: 0.3491 [0.301, 0.398] | **VERIFIED** | Foundational negative result: refactoring changes structure more than bug-inducing mutations change structure. |
| **CLM-03** | SBG V5 composite dynamic genome discriminates semantic change significantly better than random chance on synthetic transformation benchmarks. | `SBG/artifacts/final/pairs_v10_test_v6exp.jsonl` (V10 Headline) | AUROC: **0.8968** [0.8629, 0.9216]; AUPRC: **0.8862** | **VERIFIED** | On the 19-program synthetic benchmark `v10_test`, SBG V5 successfully separates SP and SC variants above chance. |
| **CLM-04** | SBG V5 outperforms conventional static code-edit distance features. | `IEEE_ACCESS_PRE_SUBMISSION/WP_A_B_COMPARATIVE_BENCHMARK/raw/EXP-A4R-001/` | SBG AUROC 0.8968 vs Edit AUROC 0.6160 ($\Delta = +0.2808$) | **VERIFIED** | Dynamic behavioural trace alignment carries far more discriminative signal than simple diff/edit size. |
| **CLM-05** | SBG V5 provides statistically significant incremental predictive value beyond execution statistics and edit size (H4). | `IEEE_ACCESS_PRE_SUBMISSION/05_COMPARATIVE_EVALUATION_RESULTS.md` | $\Delta\text{AUROC} = +0.0014\ [-0.0742, 0.0631]$, $p = 0.914$ | **CONTRADICTED** | Adding SBG V5 to $\text{LR(EX)}$ produces no significant gain. The confidence interval spans zero. |
| **CLM-06** | Non-linear combiners of cheap execution statistics and edit features outperform full composite SBG V5. | `IEEE_ACCESS_PRE_SUBMISSION/05_COMPARATIVE_EVALUATION_RESULTS.md` | Random Forest `RF_d4_EXx` AUROC: **0.9552** vs SBG V5: **0.8968** ($\Delta = +0.0584$) | **VERIFIED** | Cheaper scalar counters (loop iterations, call counts, trace lengths) + diff size in a tree model beat complex trajectory alignment. |
| **CLM-07** | The multi-dimensional combination (Topology + Temporal + State) outperforms individual genome components. | `IEEE_ACCESS_PRE_SUBMISSION/WP_C_ABLATIONS/08A_ABLATION_RESULTS.md` | State Genome alone: AUROC **0.9171** vs Composite V5: **0.8968** | **CONTRADICTED** | Ablation reveals dimension fusion hurts performance; state transition entropy alone is superior to the 3-part composite. |
| **CLM-08** | Simple scalar mean trace length (`trace_len_mean`) is competitive with the full SBG V5 representation. | `IEEE_ACCESS_PRE_SUBMISSION/05_COMPARATIVE_EVALUATION_RESULTS.md` | `trace_len_mean` AUROC: **0.8918** vs SBG V5: **0.8968** ($\Delta = -0.0050$, CI overlaps) | **VERIFIED** | A single scalar counter captures nearly all the discriminative signal available in the synthetic benchmark. |
| **CLM-09** | SBG effectively detects real-world software defects in open-source projects (BugsInPy, QuixBugs). | `IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D4_stats/STATS_REPORT.md` | BugsInPy AUROC: **0.4970**; QuixBugs AUROC: **0.4440** | **CONTRADICTED** | On real defects, SBG performs at or below chance because test suites rarely isolate differential trace behavior without crashing. |
| **CLM-10** | SBG representation generalises across programming languages (e.g., Python to Java/C). | `SBG/artifacts/phase4/E9/results.json`, `SBG/phase5/` | $N=5$ illustrative Python style pairs; no real multi-lingual dataset | **UNSUPPORTED** | Insufficient sample size and no systematic cross-language feature alignment protocol. |
| **CLM-11** | The synthetic benchmark evaluation is free of cross-split base program leakage. | `SBG/experiments/final/consistency_check.py`, `C2/C3` gates | 0 base program leakage across train/dev/val/test splits (19 test, 11 val, 13 dev, 45 train) | **VERIFIED** | Splits are strictly project-disjoint; no program in `v10_test` appears in training or validation. |
| **CLM-12** | Output-free protocol v8 eliminates entry-point aliasing and self-test driver execution artifacts. | `SBG/tests/test_entry_policy.py`, `C7` gate | 37/37 entry-policy unit tests pass; 0 driver executions | **VERIFIED** | Structural entry selection reliably targets identical functions under renaming without leaking test harness code. |
| **CLM-13** | SBG provides actionable defect localization and semantic change characterization across diverse domains. | Literature and repo inspection | Not evaluated on standard fault localization benchmarks (e.g., Defects4J FL) | **REQUIRES NEW EXPERIMENT** | Requires evaluation on independent multi-language benchmark suites (Defects4J, BugsInPy, ManyBugs, Bears). |

---

## 3. Summary of Manuscript Positioning & Claims Rectification

To achieve IEEE Access publication standards, the paper must be repositioned from an unjustified "New SOTA Representation" claim to an authoritative **Empirical Software Engineering & Methodological Contribution**:
1. **Highlight the Discovery of Structural Inversion & Benchmark Confounding:** Document how edit size and execution volume confound semantic equivalence evaluation.
2. **Present Rigorous Negative Findings Openly:** Demonstrate that complex trace sequence alignment adds no incremental value over scalar runtime statistics on synthetic benchmarks ($p=0.914$).
3. **Establish Realistic Real-World Performance Boundaries:** Explain why dynamic behavioural signatures succeed on synthetic mutation benchmarks but struggle on real-world bug suites without high-density input synthesis.

# Software Behaviour Genome: An Empirical Investigation into Dynamic Program Representations, Structural Inversion, and Incremental Predictive Value

**Author:** Manas Sakthivel  
**Target Journal:** IEEE Access  
**Specialty:** Software Engineering / Empirical Software Analysis / Program Representations

---

## Abstract

Determining whether two program variants are semantically equivalent or exhibit behavioral divergence is a central challenge in change impact analysis, regression testing, and automated program repair. Conventional static syntax representations (AST differencing, token similarity, neural code embeddings) suffer from a fundamental *structural-semantic inversion*: semantics-preserving refactorings often introduce substantial syntactic modifications, whereas defect-inducing mutations frequently alter only a few tokens, leading static metrics to perform near or below random chance (AUROC $\le 0.61$). To address this, we present the **Software Behaviour Genome (SBG)**, a dynamic program representation that instruments execution traces across three orthogonal behavioral axes: call topology ($V_3$), temporal event sequence alignment ($V_5\text{ temporal}$), and local variable state transition entropy ($V_5\text{ state}$). Under a preregistered, output-free, rename-invariant evaluation protocol across 19 project-disjoint Python programs (638 matched pairs), composite SBG $V_5$ achieves an AUROC of **0.8968** (95% Cluster CI: $[0.8629, 0.9216]$) and an AUPRC of **0.8862**, substantially outperforming static AST edit distance ($\text{AUROC } 0.6160, \Delta = +0.2808$). 

However, rigorous head-to-head benchmarking against progressively stronger conventional baselines reveals critical empirical boundaries:
1. Adding SBG $V_5$ to a baseline model comprising edit size and scalar execution statistics ($\text{LR(EX)}$) yields **zero statistically significant incremental predictive value** ($\Delta\text{AUROC} = +0.0014\ [-0.0742, +0.0631], p = 0.914$).
2. A shallow non-linear decision tree ensemble trained strictly on execution statistics and edit size (`RF_d4_EXx`) achieves an AUROC of **0.9552** ($[0.9318, 0.9733]$), significantly outperforming composite SBG $V_5$ by $+0.0584$ ($p < 0.001$).
3. Component ablations demonstrate that local state transition entropy alone achieves an AUROC of **0.9171**, significantly outperforming multi-dimensional composite fusion ($0.8968, p = 0.006$) due to negative dimension interactions where topological alignment adds false-positive distance to valid refactorings.
4. On independent real-world defect benchmarks (BugsInPy, QuixBugs), SBG performance degrades to random chance (AUROC $0.444–0.497$) due to test input sparsity and execution crash dominance.

Our findings establish that while dynamic state monitoring effectively overcomes syntactic inversion, complex multi-axis trajectory alignment does not provide incremental utility over scalar execution counters on standard transformation benchmarks. We provide an end-to-end, bit-exact reproducibility package.

**Index Terms:** Dynamic program analysis, behavioral representations, semantic equivalence, defect prediction, regression testing, structural inversion, empirical software engineering.

---

## 1. Introduction

Automated detection of semantic changes between program versions is essential for software evolution, patch validation, regression testing, and refactoring verification. When a developer modifies source code, static difference analysis can identify which lines or AST subtrees were altered, but cannot readily establish whether runtime execution behavior has been altered.

Static code similarity representations—such as token overlap metrics, AST tree-edit distances (e.g., GumTree), control flow graph isomorphisms, and pretrained Transformer embeddings (e.g., CodeBERT)—exhibit a profound failure mode in semantic change classification: **structural-semantic inversion**. A valid refactoring (such as renaming variables, inlining functions, or restructuring loops) preserves exact runtime semantics while producing large syntactic edit distances. Conversely, subtle bug-inducing mutations (such as off-by-one boundary adjustments or arithmetic operator flips) alter program semantics while producing minimal syntactic edits. Consequently, static metrics frequently rate buggy mutations as *more similar* to the base program than valid refactorings.

To overcome this limitation, dynamic analysis methods observe program execution directly under controlled input batteries. Prior work has explored execution frequency spectra (Harrold et al., 2000), entry/exit value spectra (Xie & Notkin, 2005), dynamic API call birthmarking (Myles & McCracken, 2004), and differential testing frameworks (Jin et al., 2010). However, the literature has rarely evaluated whether multi-axis dynamic trajectory alignment offers **statistically meaningful incremental predictive power** beyond cheap, scalar execution statistics (such as call counts, branch coverage sizes, and trace event counts) combined with edit size.

In this paper, we formulate and empirically evaluate the **Software Behaviour Genome (SBG)**, an output-free dynamic behavioral representation. SBG captures execution profiles along three dimensions:
- **Call Topology ($V_3$):** Line coverage sets, function invocation frequencies, and call graph bigrams.
- **Temporal Profile ($V_5\text{ temporal}$):** Dynamic sequence alignment over instruction type event streams.
- **State Profile ($V_5\text{ state}$):** Shannon entropy of local variable values and variable transition spectra across execution steps.

We conduct a controlled, preregistered empirical evaluation across 19 base programs (638 matched pairs) in Python, comparing SBG against seven competitor baseline families. We isolate the structural inversion phenomenon, measure component contributions via systematic ablation, evaluate incremental predictive power over conventional baselines, and test generalizability on real-world defect benchmarks.

---

## 2. Motivation and Research Gap

### 2.1 The Structural Inversion Confound
Consider a base sorting function $P$ and two variants:
- $P_{\text{refactor}}$: Variables are renamed and loop structures are converted from `while` to `for`. Semantics are 100% preserved ($y=0$), but AST edit distance is high ($\text{edit} = 14$).
- $P_{\text{buggy}}$: A comparison operator `<` is flipped to `<=`. Semantics are altered ($y=1$), but AST edit distance is minimal ($\text{edit} = 1$).

Under static metrics, $\text{Distance}(P, P_{\text{refactor}}) > \text{Distance}(P, P_{\text{buggy}})$, leading to an inverted classification ranking where buggy mutants receive higher similarity scores than refactorings.

### 2.2 The Benchmark Confounding Crisis
In many synthetic equivalence and defect benchmarks, generator operators inadvertently introduce systematic edit-size or execution-volume asymmetries between semantics-preserving (SP) and semantics-changing (SC) transformations. A trivial classifier relying on line count or mean trace length can achieve artificial AUROCs of $0.85–0.95$ simply by exploiting volume artifacts rather than learning semantic behavior. Evaluating a behavioral representation requires strict volume controls and baseline comparisons against scalar counters.

### 2.3 The Incremental Value Gap
While multi-dimensional trace alignment is conceptually appealing, empirical software engineering requires demonstrating whether such complexity adds incremental value over simpler, computationally inexpensive alternatives. We explicitly quantify the incremental predictive value of SBG when added to standard execution statistics.

---

## 3. Related Work

```
                                Program Equivalence & Behavioral Analysis
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         ▼                                        ▼                                        ▼
   Static Syntactic Metrics              Execution Spectra & State                  Behavioral Regression
   • AST Differencing (GumTree)          • Path Spectra (Harrold et al., 2000)     • BERT (Jin et al., 2010)
   • Token / n-gram Jaccard              • Value Spectra (Xie & Notkin, 2005)      • Shadow Symbolic (Person, 2011)
   • CodeBERT (Feng et al., 2020)        • Dynamic Birthmarks (Myles, 2004)        • EquiBench (Danglot, 2021)
   [Suffers from Inversion: AUROC ≤ 0.61] • SBG Multi-Axis Genome (This Work)       • Kessel & Atkinson (SCAM 2019)
```

1. **Value Spectra:** Xie & Notkin (2005) introduced value spectra comparison for regression testing, monitoring variable value distributions at function boundaries. SBG extends this concept to intermediate local variable transitions across fine-grained execution steps.
2. **Path & Execution Spectra:** Harrold et al. (2000) demonstrated that branch and path execution frequencies correlate with regression faults. We adapt path spectra into our baseline comparison suite.
3. **Dynamic Functional Equivalence:** Kessel & Atkinson (2019) evaluated dynamic method invocation comparison for judging third-party library equivalence. SBG focuses on intra-procedural mutation and refactoring discrimination.
4. **Dynamic Birthmarking:** Myles & McCracken (2004) and Schuler et al. (2007) utilized k-gram opcode and method call sequences for software theft detection. We evaluate dynamic k-gram sequences as a competitive baseline.

---

## 4. Research Questions

- **RQ1 (Representation Fidelity):** *Does dynamic behavioral genome extraction overcome the structural-semantic inversion observed in static and syntactic representations?*
- **RQ2 (Incremental Predictive Value):** *Does multi-dimensional behavioral trace alignment provide statistically significant incremental predictive power beyond code-edit size, scalar execution statistics, and tree ensembles?*
- **RQ3 (Generalization Boundaries):** *Under what benchmark conditions does dynamic behavioral representation maintain discriminative utility, and what are its generalization limits on real-world software defects?*

---

## 5. SBG Architecture & Genome Formulation

SBG executes candidate program versions in a timeout-guarded worker thread sandbox utilizing Python's `sys.settrace` engine. For each input $I_k$ in an 11-input synthesized test battery, SBG records a sequence of `TraceEvent` records:
$$\text{Trace}(P, I_k) = \langle e_1, e_2, \dots, e_M \rangle,\quad e_i = (\text{event\_type}, \text{lineno}, \text{func\_name}, \text{locals\_snapshot})$$

```
Base Program P ──────► [ Structural Entry Policy (v8) ] ──► [ Sandbox Tracer ] ──► Trace Events
                             │                                    │
Variant Program P' ───► [ (Rename-Invariant AST Match) ] ──► [ (5 runs, 1.0s) ] ──► Trace Events
                                                                                       │
                                                                                       ▼
                                                                           [ Genome Extractors ]
                                                                           ├── Call Topology (V3)
                                                                           ├── Temporal Sequence (V5)
                                                                           └── State Transition (V5)
                                                                                       │
                                                                                       ▼
                                                                           Pairwise Composite Distance:
                                                                           d_V5 = 0.50·d_V3 + 0.25·d_temp + 0.25·d_state
```

The composite dissimilarity distance $d_{\text{V5}}(P, P')$ is computed as:
$$d_{\text{V5}}(P, P') = 0.50 \cdot d_{\text{V3}}(P, P') + 0.25 \cdot d_{\text{temporal}}(P, P') + 0.25 \cdot d_{\text{state}}(P, P')$$

Where:
- $d_{\text{V3}}$ computes Jaccard distance over line coverage sets and call graph edge frequencies.
- $d_{\text{temporal}}$ computes dynamic sequence alignment over instruction type event sequences.
- $d_{\text{state}}$ computes Shannon entropy differences and string Jaccard distances over local variable value transitions.

---

## 6. Behavioural Representation Methodology

To eliminate methodological leakage and execution confounds:
1. **Output-Free Protocol ($V_8$):** SBG does not read or compare program return values, stdout strings, or test assertions during feature extraction. Only internal trace events are recorded.
2. **Rename-Invariant Structural Entry Selection:** Protocol $V_8$ selects callable function entry points based on AST structural topology, preventing entry mismatch under function renaming refactorings (SP-2) and ensuring test drivers are never executed.
3. **Execution Resource Budgets:** Executions are capped at 5 runs per input, 5,000 events per trace, and a 1.0 s per-trace timeout.

---

## 7. Benchmark Construction & Acquisition

We evaluate SBG across four benchmark tiers:
1. **$V_{10}$ Headline Synthetic Benchmark:** 19 base programs, 638 matched pairs (319 semantics-preserving refactorings SP-1 to SP-12, 319 semantics-changing mutations SC-1 to SC-12). Strictly project-disjoint from training/validation.
2. **$V_{9c}$ Confirmatory Validation Benchmark:** 11 base programs, 432 pairs.
3. **BugsInPy (Real Open-Source Defects):** 257 pairs across 15 project clusters extracted from real developer bug-fix commits.
4. **QuixBugs (Algorithmic Bugs):** 40 classic algorithmic programs evaluated under canonical and declared test suite inputs.

---

## 8. Experimental Design & Evaluation Protocol

- **Prediction Task:** Binary pairwise classification ($y=0$: EQUIVALENT, $y=1$: CHANGED).
- **Evaluation Metrics:** AUROC (tie-aware rank formulation), AUPRC, and threshold-derived metrics (Precision, Recall, F1) evaluated at maximum Youden's $J$.
- **Statistical Inference:** $B = 2,000$ cluster-bootstrap resamples clustered on base programs to account for intra-program pair correlation.
- **Hypothesis Testing:** Paired permutation tests with Holm-Bonferroni family-wise error rate control ($\alpha = 0.05$).

---

## 9. Baseline Comparisons

We evaluate seven competitor baseline families:
1. **Static Edit Distance:** AST unparsed Levenshtein edit distance.
2. **Static Syntactic Features:** AST node Jaccard, Token Jaccard, AST n-gram TF-IDF cosine distance, and Trivial Compiler Equivalence (TCE).
3. **Scalar Execution Statistics:** Mean trace event length (`trace_len_mean`), call count difference, coverage size difference, exception fraction.
4. **Linear Combiners:** Logistic regression on execution stats (`LR_X`), execution stats + edit size (`LR_EX`, `LR_EXx`).
5. **Non-Linear Tree Ensembles:** Shallow Random Forest (depth 4) on execution stats + edit size (`forest__RF_d4__EXx`).
6. **Spectra Competitors:** Value Spectra (Xie & Notkin, 2005), Path Spectra (Harrold et al., 2000), Dynamic Birthmark 4-grams (Myles & McCracken, 2004).
7. **Differential Output Testing:** Output differencing over 40 independent synthesized inputs (`output_indep__frac40`).

---

## 10. Results (RQ1 & RQ2)

### Table 1: Comparative Evaluation Results on Headline Test Set (`v10_test`, N=638)

| Method / Baseline Family | AUROC | 95% Cluster CI | AUPRC | Youden $J$ | F1 @ $J$ | $\Delta$ vs SBG V5 | Holm $p$-value |
|---|---|---|---|---|---|---|---|
| **Random Forest (`RF_d4_EXx`)** | **0.9552** | [0.9318, 0.9733] | **0.9643** | **0.8122** | **0.9010** | **+0.0584** | **$p = 0.0008$** |
| **Independent Output Diff (`output_indep__frac40`)** | **0.9295** | [0.8912, 0.9584] | **0.9295** | 0.7495 | 0.8697 | **+0.0327** | **$p = 0.0084$** |
| **SBG State Alone (`sbg_state`)** | **0.9171** | [0.8845, 0.9421] | **0.9090** | 0.7145 | 0.8516 | **+0.0203** | **$p = 0.0120$** |
| **Value Spectra (Xie & Notkin)** | **0.9003** | [0.8612, 0.9325] | **0.8629** | 0.6834 | 0.8343 | +0.0035 | $p = 1.0000$ |
| **SBG V5 Composite (Reference)** | **0.8968** | **[0.8629, 0.9216]** | **0.8862** | **0.6708** | **0.8284** | **0.0000** | — |
| **Mean Trace Length (`trace_len_mean`)** | **0.8918** | [0.8492, 0.9261] | **0.9080** | 0.6582 | 0.8214 | −0.0050 | $p = 1.0000$ |
| **Linear Combiner (`LR_EXx`)** | **0.8913** | [0.8475, 0.9270] | **0.9190** | 0.6614 | 0.8232 | −0.0055 | $p = 1.0000$ |
| **Path Spectra (Harrold et al.)** | **0.8887** | [0.8423, 0.9248] | **0.9085** | 0.6520 | 0.8187 | −0.0081 | $p = 1.0000$ |
| **SBG Call Topology (`sbg_v3`)** | **0.8817** | [0.8398, 0.9162] | **0.8758** | 0.6394 | 0.8127 | −0.0151 | $p = 1.0000$ |
| **SBG Temporal (`sbg_temporal`)** | **0.8070** | [0.7512, 0.8541] | **0.7815** | 0.5110 | 0.7470 | −0.0898 | **$p = 0.0008$** |
| **Dynamic Birthmark (`traceseq__kgram4`)** | **0.8009** | [0.7428, 0.8512] | **0.7591** | 0.4952 | 0.7404 | −0.0959 | **$p = 0.0008$** |
| **Logistic Reg Exec Stats (`LR_EX`)** | **0.7953** | [0.7381, 0.8445] | **0.8279** | 0.4858 | 0.7346 | −0.1015 | **$p = 0.0008$** |
| **Trivial Compiler Equiv (`static__tce_ast`)** | **0.7445** | [0.6892, 0.7934] | **0.6618** | 0.4107 | 0.6987 | −0.1523 | **$p = 0.0008$** |
| **AST TF-IDF (`static__tfidf2`)** | **0.6547** | [0.5982, 0.7081] | **0.5777** | 0.2649 | 0.6241 | −0.2421 | **$p = 0.0008$** |
| **Static Edit Distance (`edit`)** | **0.6160** | [0.5591, 0.6702] | **0.5857** | 0.1975 | 0.5925 | −0.2808 | **$p = 0.0008$** |
| **AST Node Jaccard (`static_ast`)** | **0.5915** | [0.5341, 0.6465] | **0.5616** | 0.1536 | 0.5713 | −0.3053 | **$p = 0.0008$** |
| **Token Jaccard (`static_token`)** | **0.5816** | [0.5245, 0.6368] | **0.5554** | 0.1379 | 0.5636 | −0.3152 | **$p = 0.0008$** |

### Findings for RQ1:
Dynamic representations effectively overcome structural inversion. While static representations struggle at AUROCs of $0.5816–0.6160$, composite SBG $V_5$ reaches an AUROC of $0.8968$, confirming that dynamic trace monitoring captures essential runtime semantics.

### Findings for RQ2:
Despite achieving strong absolute performance, SBG $V_5$ provides **no statistically significant incremental value** beyond execution statistics and edit size ($\Delta\text{AUROC} = +0.0014\ [-0.0742, +0.0631], p = 0.914$). Furthermore, a shallow Random Forest on scalar execution counters and edit distance (`RF_d4_EXx`) reaches AUROC $0.9552$, outperforming SBG $V_5$ by $+0.0584$ ($p < 0.001$).

---

## 11. Statistical Analysis & Incremental Value (H4)

To evaluate Hypothesis H4 rigorously, we fitted a logistic baseline on scalar execution features ($\text{LR(EX)}$) and compared it against an augmented model ($\text{LR(EX + SBG V5)}$) across project-disjoint splits:

$$\Delta\text{AUROC} = \text{AUROC}(\text{LR}(\text{EX} + \text{SBG})) - \text{AUROC}(\text{LR}(\text{EX}))$$

On `v10_test`:
- Baseline $\text{LR(EX)}$ AUROC = $0.7953$
- Augmented $\text{LR(EX + SBG V5)}$ AUROC = $0.7967$
- Paired Difference $\Delta = \mathbf{+0.0014}$, 95% Cluster Bootstrap CI: $[-0.0742, +0.0631]$, $p = 0.9140$, Holm-adjusted $p = 1.0000$.

The cluster-bootstrap confidence interval comfortably spans zero, confirming the null hypothesis: SBG adds no incremental predictive power over cheap runtime counters on this benchmark.

---

## 12. Ablation Studies (Negative Dimension Interaction)

Systematic component ablation reveals an important insight for behavioral representation design:
- **State Genome Alone (`sbg_state`):** AUROC = **0.9171** [0.8845, 0.9421]
- **Call Topology Alone (`sbg_v3`):** AUROC = **0.8817** [0.8398, 0.9162]
- **Temporal Alignment Alone (`sbg_temporal`):** AUROC = **0.8070** [0.7512, 0.8541]
- **Composite V5 ($0.50 V_3 + 0.25\text{ temp} + 0.25\text{ state}$):** AUROC = **0.8968**

The state component alone significantly outperforms full composite SBG $V_5$ ($\Delta = +0.0203, p = 0.006$). Analysis of pair score distributions reveals that semantics-preserving refactorings alter call graph sequences and loop structures, causing $V_3$ and temporal distance metrics to assign non-zero distance mass to EQUIVALENT pairs. In contrast, local variable state transitions remain invariant under refactorings (78.9% scored at exact 0.0). Linear fusion of topology and temporal terms degrades discrimination.

---

## 13. Real-World Defect Evaluation (RQ3)

When evaluated on independent real-world software defects:
- **BugsInPy (Real Open-Source Bugs):** Evaluated on 257 pairs (15 project clusters). SBG V5 achieves an AUROC of **0.4970** ($[0.4120, 0.5820]$), performing at random chance.
- **QuixBugs (Canonical Algorithmic Bugs):** Evaluated on 152 pairs (40 algorithms). SBG V5 achieves an AUROC of **0.4440** ($[0.3420, 0.5460]$), performing below chance.

**Root Cause Diagnosis:**
In real-world codebases, test suites are sparse and functions expect complex data structures. Unannotated synthetic inputs frequently trigger premature `TypeError` or `ValueError` exceptions before reaching the buggy statement. For surviving test executions, mutations either cause full test failure (crashing the trace) or execute identical unexercised paths, yielding near-zero internal trace divergence. Dynamic behavioral representations require dense, domain-specific input synthesis to operate effectively on real-world defects.

---

## 14. Threats to Validity

- **Internal Validity:** Evaluated primarily on synthetic transformation families (SP-1–SP-12, SC-1–SC-12). Although audited with 10,000 oracle test cases per pair, synthetic mutations may introduce structural patterns distinct from human developer mistakes.
- **Construct Validity:** Equivalence is defined operationally as behavioral invariance over test batteries rather than formal mathematical equivalence. We mitigated this by testing high-volume input batteries.
- **External Validity:** Findings on Python stdlib programs may not directly transfer to compiled languages or multi-threaded systems without specialized compiler/JVM instrumentation hooks.

---

## 15. Discussion

Our empirical investigation highlights three fundamental lessons for empirical software engineering:
1. **Beware the Edit-Size & Volume Confound:** Synthetic program benchmarks are prone to volume leakage where simple line counts or loop counters achieve deceptive predictive performance. Researchers must evaluate against scalar execution baselines before claiming representational breakthroughs.
2. **State Monitoring Outperforms Structural Alignment:** In program behavior monitoring, local variable value distributions carry significantly cleaner functional signal than execution path topologies or instruction sequence alignments.
3. **Complex Representations Require Incremental Validation:** Complex multi-modal deep representations must be tested for incremental predictive value over cheap runtime counters ($p=0.914$).

---

## 16. Limitations

- SBG requires an executable sandbox and does not apply to unbuildable or statically incomplete code fragments.
- Unannotated functions suffer from input type mismatches under naive type-based input synthesis.
- Current results are bounded to single-threaded Python programs.

---

## 17. Reproducibility

We provide a complete, standalone open-science package in `SBG_REPRODUCIBILITY_PACKAGE/` containing:
- Pinned environment lockfile (`CPython 3.13.5`, `PYTHONHASHSEED=0`).
- Exact experiment manifests and prediction artifacts.
- Single-command recomputation scripts (`SBG_STATISTICAL_ANALYSIS/recompute_statistics.py`).
- Automated regression suite (`SBG_AUTOMATED_TESTS/`, 4/4 passing).

---

## 18. Conclusion

This paper presented an empirical investigation into dynamic behavioral representations for semantic change discrimination. We showed that dynamic state transition monitoring overcomes the structural-semantic inversion that cripples static syntax metrics ($\text{AUROC } 0.8968 \text{ vs } 0.6160$). However, our rigorous head-to-head evaluation established that composite multi-axis trajectory alignment offers zero statistically significant incremental value over cheap scalar execution counters ($p=0.914$), and that shallow tree ensembles on execution statistics achieve superior performance ($\text{AUROC } 0.9552$). These findings demonstrate the necessity of rigorous baseline controls and open negative reporting in software engineering representation learning.

---

## References

1. **[KesselAtkinson2019SCAM]** M. Kessel and C. Atkinson, "On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence," in *Proc. 19th IEEE Int. Working Conf. Source Code Anal. Manipulation (SCAM)*, 2019, pp. 193–203. DOI: `10.1109/SCAM.2019.00030`.
2. **[XieNotkin2005TSE]** T. Xie and D. Notkin, "Checking inside the black box: regression testing by comparing value spectra," *IEEE Trans. Softw. Eng.*, vol. 31, no. 10, pp. 869–883, Oct. 2005. DOI: `10.1109/TSE.2005.107`.
3. **[Harrold2000STVR]** M. J. Harrold, G. Rothermel, R. Wu, and L. Yi, "An empirical investigation of the relationship between spectra differences and regression faults," *Softw. Test. Verif. Reliab.*, vol. 10, no. 3, pp. 171–190, 2000. DOI: `10.1002/1099-1689(200009)10:3<171::AID-STVR209>3.0.CO;2-J`.
4. **[Jin2010BERT]** W. Jin, A. Orso, and T. Xie, "Automated behavioral regression testing," in *Proc. 3rd Int. Conf. Softw. Test. Verif. Validation (ICST)*, 2010, pp. 137–146. DOI: `10.1109/ICST.2010.27`.
5. **[Danglot2021TSE]** B. Danglot et al., "A Large-Scale Empirical Study of Program Equivalence," *IEEE Trans. Softw. Eng.*, vol. 48, no. 12, pp. 4930–4948, Dec. 2021. DOI: `10.1109/TSE.2021.3113422`.
6. **[Myles2004SAC]** G. Myles and C. McCracken, "Detecting Software Theft via Dynamic Program Birthmarks," in *Proc. ACM Symp. Appl. Comput. (SAC)*, 2004, pp. 1491–1495. DOI: `10.1145/967900.968062`.
7. **[Just2014FSE]** R. Just, D. Jalali, and M. D. Ernst, "Defects4J: a database of existing faults to enable controlled testing studies for Java," in *Proc. Int. Symp. Softw. Test. Anal. (ISSTA)*, 2014, pp. 437–440. DOI: `10.1145/2610384.2628055`.
8. **[Widyasari2020ASE]** R. Widyasari et al., "BugsInPy: A Database of Existing Bugs in Python to Enable Controlled Testing and Debugging Studies," in *Proc. 35th IEEE/ACM Int. Conf. Autom. Softw. Eng. (ASE)*, 2020, pp. 1256–1257. DOI: `10.1145/3324884.3415282`.
9. **[Lin2017QuixBugs]** D. Lin et al., "QuixBugs: A Multi-Lingual Program Repair Benchmark Set Based on the Quixey Challenge," in *Companion Proc. ACM SIGPLAN Conf. Syst. Program. Lang. Appl. Softw. Humanity (SPLASH)*, 2017, pp. 55–56. DOI: `10.1145/3135932.3135941`.
10. **[Feng2020EMNLP]** Z. Feng et al., "CodeBERT: A Pre-Trained Model for Programming and Natural Languages," in *Proc. Findings EMNLP*, 2020, pp. 1536–1547. DOI: `10.18653/v1/2020.emnlp-main.122`.

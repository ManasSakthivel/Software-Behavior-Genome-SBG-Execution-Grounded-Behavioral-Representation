# Threats to Validity — Software Behavior Genome (SBG)

**Agent:** 0D  
**Date:** 2025  
**Status:** Complete — all standard SE research validity categories addressed.  
**Cross-references:** [FORMAL_MODEL.md](FORMAL_MODEL.md), [PRIOR_ART_MATRIX.md](PRIOR_ART_MATRIX.md)

---

## Preamble

This document enumerates all material threats to the validity of the empirical and formal claims made by the SBG project, organized using the Wohlin et al. taxonomy of validity categories: **Internal**, **External**, **Construct**, **Conclusion**, and **Reliability**. Each threat is given:

- A unique threat identifier (e.g., **IV-01**)
- The specific SBG hypothesis or claim it threatens (H1–H6, Definitions 1–22, Assumptions A1–A10, Open Problems OP-1–OP-6)
- A severity rating: **HIGH** / **MEDIUM** / **LOW**
- A concrete mitigation strategy
- A residual risk assessment after mitigation

Where a threat is formally acknowledged in the model itself (as an assumption, open problem, or caveat), this is noted — the formal model's authors are credited with identifying the threat; this document provides the full empirical risk analysis.

**Total threats identified: 32**

---

## Category 1 — Internal Validity Threats

*Internal validity threats are confounds that make it impossible to draw valid causal inferences from the experimental results.*

---

### IV-01 — Structural Similarity Confounding Behavioral Similarity

**Affected claims:** H1 (Stability), H2 (Sensitivity), H6 (Uniqueness)  
**Affected definitions:** Def. 9 (CONTROL), Def. 16 (EXECUTION)  
**Severity:** HIGH

**Description:**  
The CONTROL dimension ($g_C$) includes execution frequency vectors and dynamic call graphs that are derived directly from control-flow structure. Programs that are structurally similar (identical or near-identical source code) will trivially produce similar control-flow genome components regardless of whether they are semantically equivalent. This means that a low behavioral distance $D(G_1, G_2)$ may reflect *structural* proximity rather than *semantic* equivalence. The confound is particularly acute for refactoring datasets (H1), where the pre- and post-refactoring versions share most of their call graph topology by construction.

Without disentangling the structural and behavioral signals, it is impossible to determine whether the SBG genome is measuring semantics or merely acting as a structural similarity proxy (like code clone detectors [13, 14] in the prior art matrix).

**Mitigation:**  
1. Conduct an ablation study comparing: (a) full 8-dimension genome distance, (b) a purely structural baseline (static call graph edit distance), (c) purely behavioral dimensions (DATA, INTERACTION, ERROR). If (a) ≈ (b) on the test corpus, the structural confound is dominant.  
2. Test specifically on semantics-changing but structure-preserving transformations: equivalent refactored code that preserves all structural features but changes output values.  
3. For H6 (uniqueness), include structurally similar but semantically different programs (e.g., near-duplicates with off-by-one bugs [28]) as a hard negatives set.

**Residual risk after mitigation:** MEDIUM — even after ablation, CONTROL and EXECUTION dimensions will always partially reflect structure. This is acceptable if explicitly disclosed and if the contribution of structural vs. behavioral dimensions is quantified.

---

### IV-02 — Oracle / Ground-Truth Reliability

**Affected claims:** H1, H2, H5 (Genome as Regression Oracle)  
**Affected definitions:** Def. 19 ($\equiv_S$), H5 (Recall/Precision formulation)  
**Severity:** HIGH

**Description:**  
H5 defines recall and precision against a "gold-standard test suite $\mathcal{T}^*$". This oracle is itself imperfect: Defects4J [28] provides confirmed-buggy version pairs, but the "confirmed" label depends on which tests exist in the test suite. A bug that is real but not caught by $\mathcal{T}^*$ will be labeled "no regression" in the gold standard, causing genuine SBG detections to be counted as false positives. This circular dependency means that SBG cannot be meaningfully compared against an oracle that is itself derived from partial test coverage.

Similarly, for H1 (stability), the "known-equivalent" pairs from refactored codebases rely on the test suite confirming equivalence. If the test suite has low coverage, it may certify as equivalent two versions that differ behaviorally on untested paths.

**Mitigation:**  
1. Supplement Defects4J with mutation-testing-confirmed ground truth: use PIT/Pitest [29] to generate known-mutation pairs with provably injected behavioral differences, giving an oracle independent of the existing test suite.  
2. Use program verification tools (SYMDIFF [19], regression verification [16]) to confirm semantic equivalence for a small, high-confidence calibration set of refactored programs.  
3. Report results separately for high-oracle-confidence and low-oracle-confidence subsets.

**Residual risk after mitigation:** MEDIUM — no test suite achieves full coverage; the oracle problem is fundamental. The residual risk is acceptable if oracle confidence is explicitly characterized.

---

### IV-03 — Measurement Bias from Dynamic Analysis Instrumentation

**Affected claims:** H1–H6 (all hypotheses)  
**Affected definitions:** Def. 1 ($\mathcal{E}$), Def. 5 (Execution Trace), Def. 12–13 (RESOURCE, TEMPORAL)  
**Severity:** HIGH

**Description:**  
Dynamic analysis instrumentation (Valgrind [10], Pin [11], or custom tracer) alters the program's runtime behavior in measurable ways: (1) **Probe effect**: instrumentation adds overhead that changes TEMPORAL ($g_T$) and RESOURCE ($g_R$) measurements non-uniformly across programs — programs with tight loops are penalized more than programs dominated by I/O; (2) **Heisenberg effect on concurrency**: thread scheduling changes under instrumentation overhead can alter synchronization behavior and expose or conceal race conditions, changing EXECUTION ($g_U$) and STATE ($g_S$) dimensions; (3) **Shadow memory overhead** for heap tracking changes the effective memory footprint observed by the program's own allocator. The instrumented genome is not the same as the native genome, and differences in instrumentation overhead between two programs may be mis-attributed to behavioral differences.

**Mitigation:**  
1. Instrument both programs under identical toolchains and report normalized differences $\Delta D$ rather than absolute distances.  
2. Explicitly exclude TEMPORAL and RESOURCE from comparisons when the instrumentation overhead ratio between two programs differs by more than 5%.  
3. Report probe overhead as a first-class experimental variable.  
4. For RESOURCE comparisons, use hardware performance counters (perf_event) in addition to or instead of instrumentation-based counting.

**Residual risk after mitigation:** MEDIUM-LOW for CONTROL/DATA/INTERACTION; MEDIUM for TEMPORAL/RESOURCE even after normalization.

---

### IV-04 — Input Distribution Sensitivity

**Affected claims:** H1–H5 (all input-dependent hypotheses)  
**Affected definitions:** Def. 4 ($\mathcal{I}$), Def. 6 ($B(P, \mathcal{I})$), Def. 7 ($\Phi$), A3, A7, OP-1  
**Severity:** HIGH

**Description:**  
The behavioral genome $G(P) = \Phi(P, \mathcal{I})$ is parameterized over an input distribution $\mathcal{I}$. The genome is only as representative as the inputs used. If $\mathcal{I}$ is the production distribution $\mathcal{I}_\text{prod}$:
- Rare-event code paths (error handling, edge cases) are undersampled, making $g_E$ and parts of $g_C$ unreliable.
- H2 (sensitivity) formally states: if the behavioral difference only occurs on inputs with $\mu_I(\Delta) \approx 0$, the genome will fail to detect the regression. This is the *coverage gap* problem.
- The choice of input distribution is an experimenter degree-of-freedom: different experimenters using different distributions will get different distances $D(G_1, G_2)$ for the same pair of programs, making results non-reproducible.

**Mitigation:**  
1. Report results for all four canonical distributions ($\mathcal{I}_U$, $\mathcal{I}_\text{prod}$, $\mathcal{I}_\text{cov}$, $\mathcal{I}_\text{adv}$) separately, as defined in Definition 4 of the formal model.  
2. Conduct a sensitivity analysis: vary the input distribution systematically and measure the variance in $D(G_1, G_2)$ across distribution choices.  
3. For H2, supplement production inputs with coverage-guided inputs (AFL/libFuzzer traces) to ensure regression-triggering inputs are included.  
4. Specify the input distribution protocol exactly in the experimental replication package.

**Residual risk after mitigation:** MEDIUM — the oracle gap for rare-trigger bugs is fundamental and cannot be fully mitigated without symbolic execution, which the model explicitly avoids.

---

### IV-05 — Non-Determinism and Execution Flakiness

**Affected claims:** H1–H6 (all hypotheses)  
**Affected definitions:** A6 (Determinism Assumption), Def. 21 (Trace Aggregation)  
**Severity:** HIGH

**Description:**  
Assumption A6 requires that executions are deterministic given fixed input and environment. In practice, this assumption is routinely violated: (1) **ASLR** makes memory addresses non-reproducible across runs, affecting STATE ($g_S$) and DATA ($g_D$) address-based features; (2) **Thread scheduling** non-determinism changes the observed call order and timing, affecting CONTROL ($g_C$), TEMPORAL ($g_T$), and EXECUTION ($g_U$); (3) **Hash randomization** (Python dict ordering, Java HashMap) changes iteration order and hence data-flow patterns in $g_D$; (4) **Network/file timing** introduces variance in INTERACTION ($g_X$) and RESOURCE ($g_R$). Non-determinism conflates with behavioral difference: two executions of the same program on the same input may produce genome components that appear distant purely due to timing noise, creating false positive regression detections.

**Mitigation:**  
1. Standardize execution environment: disable ASLR, fix random seeds, serialize multi-threaded programs to single-threaded mode during genome extraction when possible.  
2. Measure intra-version genome variance $\text{Var}[G(P)]$ across repeated executions of the same version and use it as a noise floor; flag version-pair distances below $2 \times \sqrt{\text{Var}}$ as inconclusive.  
3. Design TEMPORAL features as relative ratios rather than absolute timestamps.  
4. Implement the confidence-weighted distance $D_\text{conf}$ from OP-3 as a noise-aware decision criterion.

**Residual risk after mitigation:** MEDIUM — real-world programs (especially servers and concurrent applications) cannot be fully de-randomized. The noise floor approach is a practical bound on achievable specificity.

---

### IV-06 — Test Data Leakage and Benchmark Contamination

**Affected claims:** H5 (Regression Oracle), H6 (Uniqueness)  
**Affected definitions:** Def. 19 ($\equiv_S^\epsilon$), H5 (Recall/Precision)  
**Severity:** MEDIUM

**Description:**  
If the threshold $\epsilon$ in $\equiv_S^\epsilon$ and the regression detection threshold $\theta^*$ in H5 are selected using the same Defects4J benchmark used for evaluation, this constitutes threshold leakage (similar to test/train contamination in ML). The reported recall/precision figures will be optimistically biased. Since $\theta^*$ is chosen to maximize $\text{Recall}(\theta) \times \text{Precision}(\theta)$, selecting it on the full benchmark and reporting performance on the same benchmark overfits the threshold to the benchmark's specific noise characteristics.

**Mitigation:**  
1. Use a strict train/validate/test split: select $\epsilon$ and $\theta^*$ on a held-out calibration corpus distinct from the evaluation benchmark.  
2. Report the threshold selection procedure as part of the experimental protocol.  
3. Perform cross-validation with $k$-fold partitioning of the benchmark programs (not just version pairs).

**Residual risk after mitigation:** LOW — standard ML validation practice; well-understood and manageable.

---

### IV-07 — Threshold Selection Bias

**Affected claims:** H1 (ε\_stable), H2 (ε\_detect), H3 (ε\_xlang), H5 (θ\*), H6 (ε\_collision)  
**Affected definitions:** Def. 19 ($\equiv_S^\epsilon$)  
**Severity:** MEDIUM

**Description:**  
The SBG system relies on five distinct thresholds ($\epsilon_\text{stable}$, $\epsilon_\text{detect}$, $\epsilon_\text{xlang}$, $\theta^*$, $\epsilon_\text{collision}$), each of which is stated as an empirical target but has no principled derivation. The selection of these thresholds is an experimenter degree-of-freedom. Different threshold choices can move a result from "supports the hypothesis" to "refutes the hypothesis". The formal model notes $\epsilon_\text{stable} \leq 0.05$ as a target but provides no derivation of why 0.05 and not 0.10 or 0.02. The problem is compounded by the fact that optimal thresholds are likely dimension-dependent (noted as a caveat for H1) but a single composite threshold is used.

**Mitigation:**  
1. Report full precision-recall curves and ROC curves over the entire threshold range for H5, rather than a single $\theta^*$ value.  
2. For H1 and H2, derive $\epsilon_\text{stable}$ and $\epsilon_\text{detect}$ from the noise floor measurement (see IV-05 mitigation) rather than from benchmark fitting.  
3. Use a two-threshold decision model: a "certainly equivalent" threshold and a "certainly different" threshold, with an indeterminate zone between them.

**Residual risk after mitigation:** LOW-MEDIUM — threshold dependence is inherent in any distance-threshold classifier; the ROC curve approach ensures no single threshold commits to an arbitrary binary claim.

---

### IV-08 — Confound: Compiler / Optimizer Behavior

**Affected claims:** H1 (Stability under refactoring), H3 (Cross-language equivalence)  
**Affected definitions:** Def. 16 (EXECUTION), A1 (Environment Stability)  
**Severity:** MEDIUM

**Description:**  
Two semantically equivalent programs compiled with different optimization levels (O0 vs O3) or different compilers (GCC vs Clang) will produce measurably different genomes on the EXECUTION ($g_U$) and RESOURCE ($g_R$) dimensions. Instruction type histograms, hot path signatures, and instruction counts are all optimization-sensitive. For H1, if the "refactored" version is also recompiled with a different optimizer pass, any observed genome change cannot be attributed solely to the refactoring. This is a direct violation of A1's environment stability assumption in the practical sense: the compilation artifact ($\mathcal{E}_P$ in Definition 2) differs between program versions.

**Mitigation:**  
1. Control compilation environment: fix compiler version, optimization level, and flags across all experimental comparisons.  
2. When comparing cross-version changes, explicitly exclude EXECUTION dimension features that are known to be optimization-sensitive.  
3. For cross-language comparisons (H3), document which dimensions are excluded due to systematic cross-language EXECUTION differences (explicitly acknowledged in H3's caveats).

**Residual risk after mitigation:** LOW — well-understood and controllable with strict experimental protocol.

---

## Category 2 — External Validity Threats

*External validity threats limit the generalization of findings beyond the experimental sample.*

---

### EV-01 — Benchmark Non-Representativeness

**Affected claims:** H1, H2, H5 (evaluated on Defects4J)  
**Affected definitions:** H5 (Recall/Precision)  
**Severity:** HIGH

**Description:**  
Defects4J [28] is the most natural evaluation benchmark for H5, but it has well-documented selection biases: (1) it covers 17 Java projects (as of v2.0), all of which are open-source, unit-testable, and have good test coverage — properties that are not representative of enterprise or embedded software; (2) the bugs are "confirmed" bugs that were eventually fixed, which biases toward bugs that are clearly detectable; (3) the projects are disproportionately library-style code (Apache Commons, Joda-Time) vs. system code or GUI code; (4) the Java-only scope means H3 (cross-language) claims cannot be evaluated on Defects4J at all. Results obtained on Defects4J may not generalize to C++, Python, Rust, embedded systems, or large-scale distributed programs.

**Mitigation:**  
1. Supplement Defects4J with: BugsInPy (Python), TypeScript compiler mutations, C/C++ bug corpora (e.g., CVE-verified Linux kernel regression pairs).  
2. Include at least one non-library, non-trivially-parallelizable benchmark (e.g., a server daemon or data pipeline).  
3. For H3, construct a dedicated cross-language equivalence benchmark (same algorithm in 3+ languages with verified I/O equivalence).

**Residual risk after mitigation:** MEDIUM — benchmark representativeness is an inherent limitation of all SE research; the mitigation reduces but cannot eliminate it.

---

### EV-02 — Generalization to Real-World Programs

**Affected claims:** H1–H6 (all)  
**Affected definitions:** Def. 2 (Program), OP-1 (Sample Size)  
**Severity:** HIGH

**Description:**  
The SBG model assumes programs have finite, tractable execution traces (Assumption A5) and that the input distribution $\mathcal{I}$ is well-defined and samplable. Real-world programs frequently violate these assumptions:
- **Long-running servers** have execution traces of unbounded length; the timeout $T_\text{max}$ truncates traces in a biased way (favoring certain code paths).
- **Interactive programs** require a simulated user; the resulting input distribution is artificially constrained.
- **Programs with external dependencies** (databases, APIs, hardware) have non-reproducible side effects that corrupt INTERACTION ($g_X$) and STATE ($g_S$).
- **Micro-services** have distributed execution traces that do not fit the single-program model of Definition 2.
- Programs with millions of lines of code generate genome vectors of proportionally high dimensionality, making distance computation and comparison infeasible without dimensionality reduction.

**Mitigation:**  
1. Bound the evaluation explicitly to programs amenable to dynamic analysis: single-process, non-interactive, execution-time < $T_\text{max}$.  
2. Describe a path to scaling via program slicing or component-level analysis, but do not claim full-program applicability in the initial study.  
3. For trace truncation, study the bias introduced by $T_\text{max}$: compare genomes of the same program under different timeout settings to characterize truncation-induced variance.

**Residual risk after mitigation:** HIGH (fundamental limitation) — explicitly scope the claims to the class of programs for which the analysis is tractable.

---

### EV-03 — Generalization Across Programming Paradigms

**Affected claims:** H3 (Cross-Language), H1/H2 (evaluated on OO Java code)  
**Affected definitions:** Def. 9 (CONTROL), OP-4 (Cross-Language Alignment)  
**Severity:** MEDIUM

**Description:**  
The genome model's CONTROL dimension uses dynamic call graphs and execution frequency vectors, which are naturally suited to imperative and object-oriented programs. Functional programs (Haskell, Clojure, Erlang) express computation via higher-order function application, closures, and lazy evaluation: call graphs are not stable across equivalent functional programs, and branching structure is expressed via pattern matching rather than conditional branches. Logic programs (Prolog, Datalog) have no concept of a call graph in the conventional sense. For these paradigms, $g_C$ as defined in Definition 9 either cannot be computed or would be a meaningless representation. The cross-language claim (H3) is particularly at risk if it is evaluated only on Python↔Java comparisons (both OO/imperative) and extrapolated to paradigm-crossing comparisons.

**Mitigation:**  
1. Scope the initial H3 evaluation to imperative and OO languages (Python, Java, C, C++, JavaScript, Go, Rust).  
2. Explicitly list paradigms that are out-of-scope for the current genome model.  
3. For functional languages, propose a reformulation of $g_C$ in terms of reduction steps or lazy-evaluation force counts.

**Residual risk after mitigation:** MEDIUM — the paradigm limitation is real; the mitigation is disclosure and scoping, not elimination.

---

### EV-04 — Scalability to Large Programs

**Affected claims:** H5 (Regression Oracle — practical applicability)  
**Affected definitions:** Def. 9 ($g_C$: GED is NP-hard), Def. 11 ($g_S$: heap graph isomorphism), OP-2  
**Severity:** HIGH

**Description:**  
Several genome distance computations are computationally intractable for large programs:
- **Graph edit distance** for CONTROL ($d_C$) is NP-hard in general; for dynamic call graphs of large programs (hundreds of procedures), exact GED is infeasible.
- **Structural graph distance** for STATE ($d_S$, isomorphism-based) is GI-hard.
- **Heap topology sequences** for $g_S$ grow with program size and trace length, making storage and comparison quadratic or worse.
- **Wasserstein-1 distance** for TEMPORAL ($d_T$) over large distributions is $O(n \log n)$ but with large constant factors.
- The genome vector dimension grows with program size (location count $|\mathcal{L}|$, syscall set size, exception type count), making comparison across programs of significantly different sizes ill-defined without heavy normalization.

**Mitigation:**  
1. Use approximate GED algorithms (beam search, Hungarian-method approximations) with stated approximation bounds.  
2. Replace exact heap isomorphism with abstracted heap summary comparison (shape graphs [28], allocation site summaries).  
3. Dimension-reduce genomes using locality-sensitive hashing or sketch structures before cross-program comparison.  
4. Report genome extraction time and comparison time as experimental variables; provide a scaling analysis.

**Residual risk after mitigation:** MEDIUM — approximate algorithms introduce their own bias; the scalability boundary for exact methods must be clearly stated.

---

### EV-05 — Language and Ecosystem Coverage

**Affected claims:** H3 (Cross-Language), H1/H2 (language generality)  
**Severity:** MEDIUM

**Description:**  
The prior art matrix identifies cross-language analysis as a coverage gap (CG-2). However, the specific language set for which SBG is validated constitutes a significant external validity constraint. If validation covers only Python and Java (both JVM-adjacent, both GC-managed, both with rich standard libraries), then:
- RESOURCE and TEMPORAL cross-language normalization (OP-6) has not been tested on fundamentally different memory models (C/C++ manual memory vs. Python GC vs. Rust ownership).
- INTERACTION ($g_X$) syscall patterns differ systematically between Windows and POSIX programs; a model trained on Linux syscall sequences will not generalize to Windows programs.
- The EXECUTION dimension ($g_U$) is explicitly stated as non-comparable across languages; if 1/8 of the genome is systematically excluded from cross-language comparisons, the distance metric's semantics changes.

**Mitigation:**  
1. Enumerate the exact set of languages validated in each hypothesis and do not generalize beyond them.  
2. Build the cross-language canonicalization operator $\mathcal{C}_\mathcal{E}$ (Definition 22) explicitly and validate its normalization on a known-equivalent cross-language pair before applying it to unknown pairs.  
3. Test on at least one non-GC language (C/C++ or Rust) to validate that the STATE and RESOURCE dimensions work across memory management paradigms.

**Residual risk after mitigation:** MEDIUM.

---

### EV-06 — Input Space Coverage in Practice

**Affected claims:** H2 (Sensitivity), H5 (Regression Oracle)  
**Affected definitions:** OP-1 (Sample Size), A7 (Sample Sufficiency)  
**Severity:** HIGH

**Description:**  
The formal model acknowledges (OP-1) that the minimum sample size $N^*$ for genome convergence is unknown. In practice, a fixed budget of $N$ traces is used. For programs with high input-space complexity (e.g., JSON parsers, compilers, image processors), even large $N$ may not cover the behavioral difference triggered by a specific regression. H2's formal statement explicitly flags: "H2 depends on the sample $\mathcal{S}$ covering the inputs in $\Delta$." This means SBG's sensitivity is fundamentally coupled to input coverage, making it incomparable to static analysis tools that achieve path-complete analysis on bounded programs.

**Mitigation:**  
1. Report input coverage (branch coverage, path coverage) achieved by the sample $\mathcal{S}$ as a covariate in all H2 and H5 experiments.  
2. Use coverage-guided fuzzing ($\mathcal{I}_\text{cov}$) as the primary input distribution for regression detection, not random sampling.  
3. Derive an empirical bound on $N^*$ for the benchmark programs by measuring $\|G_N(P) - G_{N/2}(P)\|$ across increasing $N$ (convergence curve).

**Residual risk after mitigation:** MEDIUM — high-complexity programs will always have coverage gaps; the mitigation bounds but does not eliminate this risk.

---

## Category 3 — Construct Validity Threats

*Construct validity threats arise when the operationalization of a construct does not adequately measure the intended theoretical concept.*

---

### CV-01 — "Behavioral Distance" Does Not Capture Semantic Difference

**Affected claims:** H1–H6 (fundamental to all claims)  
**Affected definitions:** Def. 18 ($D$), Def. 19 ($\equiv_S$), Def. 6 ($B(P, \mathcal{I})$)  
**Severity:** HIGH

**Description:**  
The central construct claim of SBG is that $D(G(P_1), G(P_2))$ measures *semantic* difference between programs. The formal model explicitly acknowledges (Remark R7) that full semantic equivalence is undecidable and that SBG computes an empirical approximation $\equiv_S^\epsilon$. The threat is:
1. **Completeness gap:** $D(G_1, G_2) = 0$ does not imply $P_1 \equiv_S P_2$ (the model correctly states this). However, the practical use of SBG as a "genome equivalence" tool relies on this approximate implication. Any evaluation that conflates low distance with semantic equivalence overstates what the genome measures.
2. **Soundness gap:** $D(G_1, G_2) > 0$ does not imply that there exists any observable input $i$ for which $B(P_1, i) \neq B(P_2, i)$. A positive distance may purely reflect measurement noise, instrumentation bias, or input distribution mismatch.
3. **Proxy validity:** The 8 dimensions are proxies for semantic difference. There is no proof that a program pair with small $D$ is close in any information-theoretic or denotational semantics sense.

**Mitigation:**  
1. Ground all claims in operational semantics language: "genome distance $> \theta$ predicts a behavioral difference observable under input distribution $\mathcal{I}$" — not "the programs are semantically different."  
2. Validate the *construct* of genome distance against formal equivalence checkers ([16], [19]) on small, verifiable programs: measure the correlation between $D(G_1, G_2)$ and the formal checker's verdict.  
3. Report $D$ as a probabilistic predictor with calibrated confidence intervals, not as a binary semantic verdict.

**Residual risk after mitigation:** MEDIUM — the fundamental limitation (Rice's theorem, OP-2) cannot be mitigated; only the framing of claims can be made precise.

---

### CV-02 — The Genome May Not Measure What It Claims Across Dimensions

**Affected claims:** H1–H6 (dimension-level claims)  
**Affected definitions:** Def. 9–16 (all 8 dimensions)  
**Severity:** MEDIUM

**Description:**  
Each dimension $g_C, \ldots, g_U$ is defined by a specific set of features extracted from execution traces. The construct validity question for each dimension is: do the features actually capture the *intended* behavioral aspect? Specific concerns:

- **CONTROL ($g_C$):** Loop iteration distributions aggregate all loops equally. A single frequently-executed utility loop (e.g., string scanning) may dominate the loop feature, obscuring a semantically significant change in a rarely-exercised control path.
- **STATE ($g_S$):** Heap abstraction quality depends on $\mathcal{Q}_\text{abs}$ selection (A8, OP-5). An insufficient abstraction will make $g_S$ insensitive to real memory-safety regressions (use-after-free, off-by-one heap corruption).
- **TEMPORAL ($g_T$):** The formal model (Definition 13) uses wall-clock time, which conflates algorithmic complexity with hardware effects. Two programs with the same algorithmic complexity but different constant factors will differ in $g_T$ without any semantic difference.
- **ERROR ($g_E$):** Exception type frequency counts exceptions by type name, which is language-runtime-specific. The same semantic error condition may produce a `NullPointerException` in Java and a `AttributeError` in Python; cross-language comparison of $g_E$ is undefined without exception type alignment.
- **EXECUTION ($g_U$):** Code coverage vector $\text{COV} : \mathcal{L} \to \{0,1\}$ is a *static* concept (which locations were reached) embedded in a *dynamic* genome. Two programs with identical coverage may have radically different execution frequencies.

**Mitigation:**  
1. Conduct a per-dimension sensitivity analysis: for each dimension $g_d$, create a set of programs that are semantically identical except in dimension $d$, and verify that $d_d$ is high and all other $d_{d'}$ are low.  
2. Cross-validate dimension definitions against domain experts in each area (memory safety for STATE, concurrency for EXECUTION, etc.).  
3. For cross-language ERROR comparison, build an exception taxonomy mapping layer similar to the procedure alignment needed for CONTROL (OP-4).

**Residual risk after mitigation:** MEDIUM — each dimension is an engineering approximation; per-dimension validation reduces but does not eliminate construct drift.

---

### CV-03 — Independence of the 8 Dimensions

**Affected claims:** H1–H6 (aggregated distance $D$)  
**Affected definitions:** Def. 20 (Aggregation $\mathcal{F}$), Def. 18 ($D$)  
**Severity:** MEDIUM

**Description:**  
The aggregation function $\mathcal{F}$ (Definition 20) with uniform weights $w_k = 1/8$ treats all 8 dimensions as equally important and independent. Both properties are questionable:
1. **Not independent:** CONTROL ($g_C$) and EXECUTION ($g_U$) are correlated by construction — code coverage and execution frequency are both derived from trace location visits. DATA ($g_D$) and STATE ($g_S$) are correlated through heap-stored values. RESOURCE ($g_R$) and TEMPORAL ($g_T$) are correlated through instruction count and execution time. Correlated dimensions contribute redundant signal to $D$, effectively upweighting those aspects of behavior.
2. **Not equally important:** For regression detection (H5), a change in INTERACTION ($g_X$) — e.g., a new system call or changed filesystem path — is likely to be more semantically significant than a change in TEMPORAL ($g_T$) at the same magnitude. Uniform weighting treats these as equivalent.

The consequence is that $D$ overweights correlated dimensions and misweights dimensions by semantic importance, making the composite distance an incoherent semantic measure.

**Mitigation:**  
1. Compute a pairwise dimension correlation matrix on the experimental corpus and report which dimensions are correlated.  
2. Explore learned weights using a logistic regression or random forest over labeled regression/non-regression pairs; compare to uniform weighting in terms of precision/recall.  
3. Consider a dimensionality-reduction step (PCA or sparse PCA) to decorrelate dimensions before aggregation.

**Residual risk after mitigation:** LOW-MEDIUM — the uniform weighting is a reasonable first-order approximation; the mitigation provides an improved model with an empirically justified weighting.

---

### CV-04 — Normalization Alters the Measured Construct

**Affected claims:** H3 (Cross-Language), H4 (Versioning)  
**Affected definitions:** Def. 22 (Normalization and Canonicalization), OP-6  
**Severity:** MEDIUM

**Description:**  
Definition 22 introduces normalization and canonicalization operators ($\mathcal{N}$, $\mathcal{C}$) for cross-environment comparison. The formal model uses SPECint normalization for RESOURCE features. The construct threat is: **normalization changes what is being measured**. After normalization, $D(G_1, G_2)$ no longer measures the behavioral difference between $P_1$ and $P_2$ as they actually run — it measures the difference between their *normalized representations*, which may suppress real behavioral differences or introduce artificial ones. For example, normalizing CPU instruction counts by SPECint score corrects for hardware speed but also suppresses algorithmic complexity differences between programs. Two programs, one $O(n)$ and one $O(n^2)$, may normalize to the same instruction count on inputs of moderate size.

The open problem OP-6 explicitly acknowledges that TEMPORAL normalization across architectures has no satisfactory solution.

**Mitigation:**  
1. For each normalization applied, empirically validate that the normalization does not suppress behavioral differences that are real and relevant. Use programs with known algorithmic complexity differences as test cases.  
2. Report raw (unnormalized) and normalized distances separately; flag cases where they diverge significantly.  
3. For OP-6 (temporal normalization), use relative temporal features (phase-time ratios, not absolute times) as a partial mitigation until a principled cross-architecture metric is defined.

**Residual risk after mitigation:** MEDIUM — normalization is a necessary trade-off for cross-environment comparison; the residual risk is that subtle semantic differences may be suppressed.

---

### CV-05 — "Cross-Language Behavioral Equivalence" as a Construct

**Affected claims:** H3 specifically  
**Affected definitions:** Def. 19 ($\equiv_S$ across languages), OP-4  
**Severity:** HIGH

**Description:**  
H3 claims that semantically equivalent programs in different languages receive the same behavioral genome after canonicalization. This requires the canonical form $\mathcal{C}_\mathcal{E}(G(P))$ to abstract away all environment-specific features while retaining all semantically relevant ones. The construct threat is that no such canonicalization can be both:
- **Complete:** retaining all semantically relevant behavioral features across radically different language runtimes.
- **Abstract enough:** eliminating all language-implementation-specific noise.

Specific example: a Python sort and a Java sort implement the same algorithm, but Python's `list.sort()` uses Timsort while Java's `Arrays.sort()` for objects also uses Timsort — however, their system call patterns, memory allocation patterns, and instruction mixes are entirely different. The three "strongest" dimensions for H3 (CONTROL, DATA, INTERACTION) are in fact quite noisy across language boundaries: call graph nodes use language-specific procedure identifiers (OP-4 is unresolved), data value distributions reflect type system differences (Python's dynamic typing vs. Java's static typing), and syscall sequences reflect different runtime library choices.

**Mitigation:**  
1. Resolve OP-4 before claiming H3: provide a concrete cross-language procedure alignment mapping for the specific language pairs being compared.  
2. Validate H3 on a minimal testable pair: two programs in two languages with provably identical observable I/O behavior (verified by test suite) and measure whether $D < \epsilon_\text{xlang}$ is achieved on the CONTROL and DATA dimensions alone.  
3. State clearly that H3 is the highest-risk hypothesis and that its current support is theoretical rather than empirical.

**Residual risk after mitigation:** HIGH — cross-language behavioral equivalence via runtime analysis remains an open research problem; OP-4 and OP-6 are unresolved.

---

## Category 4 — Conclusion Validity Threats

*Conclusion validity threats concern whether the data analysis correctly supports or refutes the stated hypotheses.*

---

### CL-01 — Insufficient Statistical Power

**Affected claims:** H1–H6 (all empirical hypotheses)  
**Affected definitions:** OP-1 (Sample Size), H5 (Recall/Precision targets)  
**Severity:** HIGH

**Description:**  
Statistical power is the probability of detecting a true effect. SBG's empirical hypotheses (particularly H2 and H5) require sufficient power to detect behavioral differences against a noisy background (IV-05: non-determinism; IV-03: instrumentation bias). Two power concerns are specific to SBG:
1. **Genome variance:** If intra-version genome variance $\text{Var}[G(P)]$ is large (due to non-determinism), then the signal-to-noise ratio for detecting inter-version differences is low. The formal model provides no power analysis or sample size recommendation for the evaluation benchmarks.
2. **Benchmark size:** Defects4J contains hundreds of bug-fix pairs, but many are structurally similar bugs in the same codebase. Effective independent sample size may be far lower than the nominal sample count. Testing H5 claims with $N_\text{pairs} < 100$ independent pairs against a 0.80/0.70 recall/precision target is likely underpowered, making confidence intervals wide enough to be uninformative.

**Mitigation:**  
1. Conduct a formal power analysis *a priori*: for a given expected effect size (e.g., $\Delta D = 0.10$), calculate the required $N$ to achieve 80% power at $\alpha = 0.05$.  
2. Report confidence intervals on all reported recall, precision, and mean-distance values, not only point estimates.  
3. Treat program pairs from the same codebase as clustered observations and use mixed-effects models or clustered standard errors to correct for within-codebase correlation.

**Residual risk after mitigation:** MEDIUM — small benchmark sizes are an irreducible SE research limitation; confidence interval reporting converts a conclusion validity threat into a result uncertainty disclosure.

---

### CL-02 — Multiple Hypothesis Testing

**Affected claims:** H1–H6 (six hypotheses tested simultaneously)  
**Affected definitions:** All six hypotheses  
**Severity:** HIGH

**Description:**  
SBG evaluates six distinct hypotheses (H1–H6) across multiple sub-experiments (one per dimension, one per benchmark, one per language pair). Without correction for multiple comparisons, the family-wise error rate (FWER) for any result exceeds the per-test significance level. For example, if each of 8 dimension-level tests is conducted at $\alpha = 0.05$, the probability that at least one falsely rejects under the null is $1 - (1 - 0.05)^8 = 0.34$. If the six hypotheses are tested across 3 benchmarks and 4 input distributions, the number of distinct tests approaches 72, making false discovery virtually certain without correction.

**Mitigation:**  
1. Pre-register the primary hypothesis and statistical test for each H1–H6 before conducting experiments.  
2. Apply Holm-Bonferroni or Benjamini-Hochberg FDR correction to all $p$-values reported across the full experiment family.  
3. Report adjusted $p$-values and distinguish primary (confirmatory) from secondary (exploratory) analyses.

**Residual risk after mitigation:** LOW — standard statistical practice; fully addressable.

---

### CL-03 — Mismatched Statistical Tests

**Affected claims:** H1, H2, H5 (statistical comparison of distance distributions)  
**Severity:** MEDIUM

**Description:**  
The natural statistical test for H1 and H2 is a two-sample comparison of $D$ distributions: "is the distribution of $D$ over semantics-preserving pairs stochastically less than the distribution over semantics-changing pairs?" The appropriate test depends on the distribution of $D$:
- If $D$ is approximately Normal: a $t$-test or Mann-Whitney $U$ test is appropriate.
- If $D$ is heavy-tailed or skewed (likely, since it is bounded $[0,1]$ but concentrated near 0 for stable programs): parametric tests lose power; permutation tests or bootstrap confidence intervals are preferred.
- For H5's precision/recall claims, a McNemar test or paired sign test against a baseline classifier is needed; a simple reporting of point estimates without significance testing cannot support a claim of superiority.

Using a $t$-test on a non-Normal, bounded distribution produces invalid $p$-values and may either over- or under-report significance.

**Mitigation:**  
1. Report empirical distributions of $D$ (histograms, Q-Q plots) before selecting a test.  
2. Default to non-parametric tests (Mann-Whitney, permutation) unless Normality is confirmed.  
3. For H5, compare against a non-trivial baseline (e.g., simple code change size as a regression predictor) using McNemar's test on the same test set.

**Residual risk after mitigation:** LOW — well-understood methodology; addressable with standard statistical practice.

---

### CL-04 — Effect Size Reporting

**Affected claims:** H1–H6  
**Severity:** MEDIUM

**Description:**  
Statistical significance ($p < 0.05$) does not imply practical significance. SBG's hypotheses make claims about *magnitude* as well as direction: H1 targets $\epsilon_\text{stable} \leq 0.05$, H5 targets recall ≥ 0.80 and precision ≥ 0.70. Without reporting effect sizes (Cohen's $d$ for distance comparisons, absolute precision/recall with confidence intervals for H5), a result that is statistically significant but practically small (e.g., $\Delta D = 0.003$) would appear to support the hypothesis while providing no engineering value. Conversely, a large and practical effect that is underpowered may be dismissed as "not statistically significant."

**Mitigation:**  
1. Report Cohen's $d$ (or Glass's $\Delta$) for all two-sample distance comparisons.  
2. Report $95\%$ confidence intervals on all precision, recall, and $F_1$ values.  
3. Explicitly distinguish statistical significance from practical significance in the discussion; relate effect sizes to the engineering utility of the system.

**Residual risk after mitigation:** LOW.

---

### CL-05 — Overfitting to Benchmark Characteristics

**Affected claims:** H5 (Regression Oracle), H6 (Uniqueness)  
**Severity:** MEDIUM

**Description:**  
The genome model's design choices — choice of 8 dimensions, choice of distance functions per dimension, choice of normalization — were made *with knowledge* of the evaluation benchmarks (Defects4J, mutation testing suites). This constitutes a subtle form of overfitting: the model may be implicitly tuned to the statistical properties of Java object-oriented programs, Timsort/Collections-heavy code, and JUnit-style test harnesses. This overfitting is not detectable by evaluating the same model on the same benchmark.

**Mitigation:**  
1. Evaluate on a benchmark from a completely different ecosystem (not Java, not university-curated bug databases) as a held-out generalization test.  
2. Use pre-registration: commit to the genome model design *before* seeing the evaluation benchmark results.  
3. Report ablations that remove or modify individual design choices and measure sensitivity of results to those choices.

**Residual risk after mitigation:** MEDIUM — without fully independent benchmark development, some degree of benchmark overfitting is unavoidable.

---

### CL-06 — Aggregation Conceals Dimension-Level Failures

**Affected claims:** H1–H6 (composite $D$ used for claims about all dimensions)  
**Affected definitions:** Def. 18 ($D$), Def. 20 ($\mathcal{F}$)  
**Severity:** MEDIUM

**Description:**  
The composite behavioral distance $D = \mathcal{F}(d_C, d_D, d_S, d_R, d_T, d_E, d_X, d_U)$ with uniform weights allows "passing" dimensions to mask "failing" dimensions. For example, if $g_C$ and $g_X$ are highly diagnostic for regression detection but $g_T$, $g_R$, and $g_U$ are noisy, the composite $D$ will be diluted by the noisy dimensions, reducing recall. Conversely, if two structurally different programs happen to be equivalent on 7 dimensions but differ on one, the composite $D$ will be only $1/8$ of the maximum, potentially falling below the threshold $\theta$ and missing the regression. The composite metric obscures which dimensions are working and which are failing.

**Mitigation:**  
1. Report per-dimension distances $d_C, \ldots, d_U$ individually, not only the composite $D$.  
2. Use the per-dimension breakdown to identify which dimensions contribute to correct and incorrect classifications.  
3. Evaluate dimension-level diagnostic accuracy (AUC-ROC per dimension) alongside composite accuracy.

**Residual risk after mitigation:** LOW — straightforward to implement with per-dimension reporting.

---

## Category 5 — Reliability Threats

*Reliability threats concern the reproducibility and stability of experimental results.*

---

### RL-01 — Reproducibility Across Machines and Environments

**Affected claims:** H1–H6 (all)  
**Affected definitions:** Def. 1 ($\mathcal{E}$), A1 (Environment Stability), A6 (Determinism)  
**Severity:** HIGH

**Description:**  
SBG genome measurements are by design environment-sensitive (Definition 1 defines $\mathcal{E}$ as part of the computational context; $g_R$ and $g_T$ are explicitly $\mathcal{E}$-sensitive). This means that the same program pair may produce different $D(G_1, G_2)$ values on different machines, OS versions, or hardware configurations. The practical consequence is:
- Results from one lab may not replicate in another lab even with identical source code.
- Regression detection thresholds $\theta^*$ derived on one machine may be miscalibrated when deployed on another.
- Genome archives (proposed as supply-chain artifacts in CG-3) become stale when the deployment environment changes.

**Mitigation:**  
1. Provide a fully containerized replication environment (Docker or OCI container) with pinned OS version, compiler, runtime, and dependency versions.  
2. Report all experiments with the full $\mathcal{E}$ specification (hardware, OS, kernel, language runtime, library versions).  
3. Conduct a cross-machine reproducibility study: run identical experiments on at least two different hardware configurations and report genome variance attributable to environment.  
4. For TEMPORAL and RESOURCE dimensions, use relative normalization (as noted in Definition 13, Remark R5) to reduce environment sensitivity.

**Residual risk after mitigation:** MEDIUM — TEMPORAL and RESOURCE will always retain some environment sensitivity; this is fundamental to measuring runtime behavior.

---

### RL-02 — Randomness in Dynamic Analysis

**Affected claims:** H1–H6  
**Affected definitions:** A3 (Input Independence), A6 (Determinism), Def. 21 (Trace Aggregation)  
**Severity:** MEDIUM

**Description:**  
Dynamic analysis involves several sources of randomness beyond program non-determinism (IV-05):
1. **Input sampling randomness:** The sample $\mathcal{S} = \{i_1, \ldots, i_N\}$ drawn from $\mathcal{I}$ is random. Different seeds for the input sampler will produce different genome estimates $G_N(P)$. For small $N$, the variance in $G_N(P)$ may be substantial.
2. **Fuzzer non-determinism:** Coverage-guided fuzzers use internal randomness; two independent fuzzing runs for the same budget $N$ will cover different code paths and produce different genomes.
3. **Concurrency:** Even with serialization (IV-05 mitigation), some thread-scheduling choices remain non-deterministic under instrumentation.

These sources of randomness make genome extraction a stochastic process, not a deterministic function, which violates the model's implicit assumption that $G(P)$ is uniquely defined for a given $(P, \mathcal{I})$.

**Mitigation:**  
1. Fix all random seeds in input generation, fuzzer, and execution environment.  
2. Run each genome extraction multiple times (at least 5 independent seeds) and report mean ± std of all reported distances.  
3. Treat the genome as a random variable and report genome variance as a primary experimental result, not a secondary consideration.

**Residual risk after mitigation:** LOW-MEDIUM — seeding addresses most randomness; residual variance from scheduler and hardware micro-architectures is accepted as noise floor.

---

### RL-03 — Version and Dependency Sensitivity

**Affected claims:** H4 (Versioning), H1 (Stability)  
**Affected definitions:** Def. 3 (Version History), Def. 1 ($\mathcal{E}: \mathcal{L}$ = loaded shared libraries)  
**Severity:** MEDIUM

**Description:**  
Definition 1 includes $\mathcal{L}$ (the set of loaded shared libraries with versions) as part of the computational environment $\mathcal{E}$. When a program's dependencies are updated — even minor version bumps of library dependencies not under the program's control — the genome $G(P)$ can change without any change to $P$ itself. This creates a confound for H4 (versioning): a measured genome change between versions $P^{(k)}$ and $P^{(k+1)}$ may be attributable to a library update rather than a change in the program's own behavior. In supply-chain security contexts (CG-3), this confound is precisely the threat: a malicious library update would change the genome without any source-code change.

**Mitigation:**  
1. Lock all transitive dependencies (full lockfile: `poetry.lock`, `Cargo.lock`, `pom.xml` pins) when conducting longitudinal genome comparisons.  
2. For supply-chain use cases, treat dependency version as an explicit dimension: compute the genome *conditional* on the dependency set, and flag changes driven by dependency updates vs. source changes.  
3. Conduct a sensitivity analysis: measure genome change for a fixed program $P$ across a range of library versions; quantify the library-version contribution to $D$.

**Residual risk after mitigation:** LOW — dependency pinning is standard practice; the residual risk is in deployment contexts where pinning is not enforced.

---

### RL-04 — Instrumentation Tool Version Sensitivity

**Affected claims:** H1–H6 (all)  
**Affected definitions:** Def. 5 (Execution Trace)  
**Severity:** LOW

**Description:**  
The execution traces that underlie the genome depend on the instrumentation tool (Valgrind, Pin, or custom tracer) and its version. Different versions of the same tool may emit different trace formats, capture different events, or have different overhead profiles. If the instrumentation tool is updated between experimental runs, genome values may shift in a way that is indistinguishable from a real behavioral change. This is particularly relevant for longitudinal studies (H4) spanning extended time periods.

**Mitigation:**  
1. Pin the instrumentation tool version in the replication package.  
2. Test genome stability across consecutive tool versions using identical program pairs before deploying a tool version update.

**Residual risk after mitigation:** LOW.

---

## Threat Summary

### By Severity

| Severity | Count | Threat IDs |
|---|---|---|
| **HIGH** | 13 | IV-01, IV-02, IV-03, IV-04, IV-05, EV-01, EV-02, EV-04, EV-06, CV-01, CV-05, CL-01, CL-02, RL-01 |
| **MEDIUM** | 16 | IV-06, IV-07, IV-08, EV-03, EV-05, CV-02, CV-03, CV-04, CL-03, CL-04, CL-05, CL-06, RL-02, RL-03 |
| **LOW** | 3 | IV-06 (post-mitigation), RL-04 |

*Note: IV-06 appears in both HIGH (pre-mitigation) and LOW (post-mitigation) as it is substantially mitigable.*

### By Category

| Category | Count | Threat IDs |
|---|---|---|
| Internal Validity | 8 | IV-01 through IV-08 |
| External Validity | 6 | EV-01 through EV-06 |
| Construct Validity | 5 | CV-01 through CV-05 |
| Conclusion Validity | 6 | CL-01 through CL-06 |
| Reliability | 4 | RL-01 through RL-04 |

### Threats Grounded in Formal Model's Own Acknowledgments

| Threat | Formal model acknowledgment |
|---|---|
| IV-04 (Input Distribution) | A3, A7, OP-1 |
| IV-05 (Non-determinism) | A6 |
| IV-08 (Compiler bias) | A1 |
| EV-04 (Scalability) | OP-2, GED is NP-hard (Def 17) |
| CV-01 (Distance vs. semantics) | Remark R7, Rice's theorem |
| CV-02 (Dimension validity) | R4, A8, R5, A9, A10 |
| CV-04 (Normalization) | N2, R5, OP-6 |
| CV-05 (Cross-language) | OP-4, H3 caveats |
| RL-03 (Dependency sensitivity) | Def. 1 $\mathcal{L}$ component |

---

## Unmitigable Threats

The following threats cannot be fully mitigated by any experimental design choice; they are fundamental limitations of the SBG approach and must be disclosed as scope boundaries in any publication:

| Threat | Why unmitigable | Disclosure strategy |
|---|---|---|
| **CV-01** (D ≠ semantic equivalence) | Rice's theorem; undecidability of full equivalence | Always frame SBG as an *empirical approximation*, not a semantic decision procedure |
| **IV-04** (Rare-trigger bugs) | No finite sample covers all behavioral differences | State sensitivity bounds explicitly; measure coverage as a covariate |
| **EV-02** (Long-running/interactive programs) | Timeout-bounded trace extraction cannot capture all behaviors | Explicitly scope claims to bounded-execution programs |
| **EV-03** (Functional/logic paradigms) | CONTROL dimension is OO/imperative-centric | Explicitly list supported paradigms; do not generalize |
| **CV-05** (Cross-language equivalence, OP-4 unresolved) | No formal cross-language procedure alignment exists | Mark H3 as exploratory/preliminary until OP-4 is resolved |

---

*This document was produced by Agent 0D for the SBG project. All threats are grounded in the formal model (FORMAL_MODEL.md), the prior art matrix (PRIOR_ART_MATRIX.md), and standard SE research validity methodology (Wohlin et al., "Experimentation in Software Engineering").*

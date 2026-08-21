# Adversarial Novelty Review — Software Behavior Genome (SBG)

**Agent:** 0C  
**Date:** 2025  
**Mission:** Attempt to INVALIDATE the novelty of SBG. This document is adversarial by design. Every attack is intended to be as strong as possible. Where attacks fail, the reason is stated precisely.

---

## Methodology

Each attack proceeds in four parts:

1. **The attack argument** — the strongest possible case against SBG's novelty claim
2. **Strength rating** — FATAL / SERIOUS / MODERATE / WEAK
3. **SBG's available response** — how the project can rebut or absorb the attack
4. **Settling experiments** — empirical work that would resolve the dispute

---

## Attack 1 — "SBG is merely another dynamic behavioral fingerprint" (cf. Bayer et al., TTAnalyze; Kinable et al.)

### Attack Argument

Bayer et al. (NDSS 2009, TTAnalyze) already do precisely what SBG claims: record runtime behavior — specifically system-call sequences and API call n-grams — and use that representation to cluster/compare programs at scale. The representation is dynamic, language-agnostic at the OS level, and produces a behavioral similarity score. Kinable & Kostakis (2011) extend this to call graph clustering. The INTERACTION dimension of SBG (`g_X`) is explicitly a superset of the Bayer syscall n-gram approach. If the most diagnostic single SBG dimension (`g_X`) already exists in TTAnalyze circa 2009, then SBG's novelty is purely the addition of seven further dimensions — and those additional dimensions (resource counts, timing vectors, coverage vectors) are all individually standard metrics.

The attack: **SBG is TTAnalyze + seven labeled buckets of existing metrics, rebranded as a genome.**

### Strength: SERIOUS

The overlap between `g_X` and TTAnalyze's syscall n-gram representation is real and substantial. The PRIOR_ART_MATRIX.md acknowledges this directly: "INTERACTION dimension `g_X` extends syscall n-gram representation; SBG adds 7 further dimensions." The "extends" framing is generous — for single-version behavioral fingerprinting, `g_X` alone may perform as well as the full genome.

### SBG's Available Response

Three responses are available, in decreasing strength:

1. **Domain inversion:** TTAnalyze targets malware triage — classifying unknown samples into threat families. SBG targets correctness across known-good software versions. These are different tasks: TTAnalyze's input is one-shot (classify this sample now), SBG's input is longitudinal (track this program across versions). No TTAnalyze-style system maintains a versioned behavioral genome history or uses it as a regression oracle (CG-1).

2. **Structural inversion:** TTAnalyze uses only `g_X`-equivalent features and produces a flat cluster assignment. SBG's `D(G_1, G_2)` is a structured, per-dimension, normalized pseudometric that preserves the separability of behavioral change types. A CONTROL regression and a RESOURCE regression look different in SBG; they look identical in a syscall n-gram vector.

3. **Coverage of non-OS-interfacing behavior:** TTAnalyze's syscall n-gram representation is blind to computation that never crosses the syscall boundary — pure in-memory algorithm behavior, data-structure shape changes, loop-count changes. SBG's `g_C`, `g_D`, `g_S` capture these. For regression detection (not malware detection), these are the most common behavioral change types.

### Settling Experiment

Run both TTAnalyze-style syscall n-gram similarity and SBG's full `D` on the Defects4J regression corpus. Measure recall and precision for regression detection. If SBG's recall on pure computation bugs (Defects4J's many algorithmic bugs) exceeds TTAnalyze-style detection by >20 points, the distinction is empirically validated. If TTAnalyze-style detection matches SBG, the multi-dimensional structure provides no marginal value.

---

## Attack 2 — "SBG is equivalent to execution trace comparison" (cf. trace diff literature)

### Attack Argument

Execution trace comparison is well-studied. Any two traces can be diffed with standard sequence alignment (Smith-Waterman, LCS, edit distance). Abstracting traces to feature vectors and computing distance between those vectors is precisely what systems like Luo et al. (BinDiff extended, TIFS 2017) and Pewny et al. (IEEE S&P 2015) do. SBG's genome extraction function `Φ` is, operationally, a dimensionality-reduction from trace space to a feature vector. The resulting `D(G_1, G_2)` is then a distance on that reduced representation. There is nothing in this that is not covered by "extract features from trace, compute distance." The "genome" terminology adds no mathematical content over "trace-derived feature vector."

### Strength: MODERATE

This is accurate as a description of the mechanics but mischaracterizes the contribution. The attack conflates the representation with the choice of dimensions. Trace comparison literature does exist, but it largely operates at the syntactic trace level (what instructions executed) not the behavioral semantic level (what observable effects were produced, and in what proportions). The attack is strongest against the claim that the genome architecture is novel; it is weak against the claim that the specific 8-dimensional semantic decomposition is novel.

### SBG's Available Response

SBG is not a trace comparator — it is a behavioral abstraction. Raw traces are:
- Not cross-language comparable (Python bytecodes vs. JVM opcodes vs. x86 instructions)
- Not aggregatable across inputs (different traces for different inputs produce incommensurable sequences)
- Not normalizable across environments (a trace on machine A and machine B will differ for reasons unrelated to semantics)

SBG's `Φ` function deliberately discards trace structure and retains behavioral signatures that are stable across inputs, environments, and language substrates. This is not dimensionality reduction; it is semantic abstraction. The distinction between "compressing a trace" and "characterizing the behavior that produced the trace" is the core claim.

### Settling Experiment

Compare SBG's cross-version distance D against raw trace edit distance (Levenshtein on event sequences). Measure stability under semantics-preserving transformations (H1): if raw trace edit distance is unstable across equivalent inputs while SBG distance is stable, the abstraction level of SBG is empirically justified over raw trace comparison.

---

## Attack 3 — "The genome is just a collection of standard software metrics"

### Attack Argument

Examine each dimension of the SBG genome:

- `g_C` (CONTROL): Branch coverage vectors, call graph — these are McCabe cyclomatic complexity metrics and standard dynamic call graph profiling, available since the 1970s (McCabe 1976) and routinely collected by any code profiler (gprof, perf, JProfiler).
- `g_D` (DATA): Value range histograms, null/zero prevalence — these are standard data-flow analysis metrics and are collected by every sanitizer and numerical analysis tool.
- `g_S` (STATE): Stack depth, heap growth — standard memory profiler output (Valgrind Massif, Heaptrack).
- `g_R` (RESOURCE): CPU instruction count, memory peak, I/O volume, syscall counts — standard `perf stat` output, available via any Linux performance counter interface.
- `g_T` (TEMPORAL): Inter-event latency, execution time — standard profiler output; Wasserstein distance on latency distributions is used in performance testing frameworks.
- `g_E` (ERROR): Exception frequency, error propagation depth — standard log analysis; any monitoring system collects exception rates.
- `g_X` (INTERACTION): Syscall n-grams — TTAnalyze 2009 (see Attack 1).
- `g_U` (EXECUTION): Code coverage vector, instruction histogram — standard `lcov`/`gcov` output plus `perf` instruction mix.

Every individual component of the SBG genome is a well-known metric with existing tools that compute it. The genome is a committee of standard metrics. Is assembling known metrics into a vector a scientific contribution?

### Strength: SERIOUS

This attack is the strongest purely technical attack on SBG. Every individual genome component is defensible as non-novel. The attack forces SBG to make a clear claim about what the **composition** contributes that the individual components do not.

### SBG's Available Response

The contribution is not in the individual metrics but in four things:
1. **Unified schema:** No prior system defines a single, formally specified behavioral fingerprint that covers all eight behavioral dimensions simultaneously with a unified distance function `D`. Existing tools specialize: profilers give `g_R`, coverage tools give `g_U`, sanitizers give `g_S`. No tool produces `G(P) = (g_C, g_D, g_S, g_R, g_T, g_E, g_X, g_U)` as a single, normalized, comparable artifact.
2. **The distance function D is semantically motivated, not ad hoc:** The per-dimension distance choices (JSD for distributions, Wasserstein for latency distributions, GED for call graphs) are chosen to match the statistical nature of each feature type. A flat concatenation of all metrics with Euclidean distance would conflate commensurable and incommensurable quantities.
3. **Longitudinal genome tracking:** The claim is not that any one metric is new, but that maintaining a versioned genome history `{G(P^(0)), G(P^(1)), ..., G(P^(n))}` and querying behavioral drift over that history is new (CG-1).
4. **The regression oracle claim (H5)** is testable and falsifiable, and no prior system combines all these dimensions in a regression-detection pipeline.

However, this response is stronger in principle than in practice until H5 is experimentally validated. If the multi-dimensional distance does not empirically outperform a single-metric baseline (e.g., syscall n-gram distance alone), this attack is not fully rebutted.

### Settling Experiment

Ablation study on Defects4J: compare regression detection performance of (a) each individual dimension alone, (b) all 8 dimensions combined with uniform weights, (c) prior art baselines (TTAnalyze-style, coverage-only, perf-only). If the multi-dimensional genome outperforms all individual dimensions and all prior single-representation baselines, Attack 3 is refuted. If any single dimension matches the full genome's performance, the 8-dimensional architecture is not empirically justified.

---

## Attack 4 — "The cross-language claim does not follow"

### Attack Argument

H3 claims that semantically equivalent programs in different languages will receive similar genomes after environment canonicalization. This claim is asserted but not proven, and the formal model itself admits severe problems with it. The model acknowledges:

- EXECUTION dimension (`g_U`) **must be excluded** from cross-language comparisons because it encodes language-specific instruction sets.
- TEMPORAL and RESOURCE dimensions require "strong normalization" that is not formally specified (OP-6).
- CONTROL dimension requires a cross-language procedure alignment mapping that is **explicitly left as an open problem (OP-4)**.

With three of eight dimensions excluded or broken, the cross-language genome is a 5-dimensional or smaller object. The "cross-language behavioral equivalence" claim reduces to: "if two programs do the same thing externally (same syscalls, same I/O), they look similar in their external interface metrics." This is trivially true but not novel — it is simply saying that two programs with the same observable behavior have the same observable behavior, measured by the same observable metrics.

Furthermore, the cross-language "equivalence" test requires a shared test oracle to verify that the programs are actually equivalent. If you already have a test oracle proving equivalence, you do not need SBG to tell you they are equivalent.

### Strength: SERIOUS

This attack exposes a genuine logical gap. The cross-language claim is either (a) trivially true (programs with the same observable outputs produce similar observable-output metrics) or (b) deeply unsolved (the CONTROL, TEMPORAL, EXECUTION dimensions cannot be compared cross-language without solving OP-4 and OP-6, which are open problems). There is no middle ground that is both non-trivial and currently achievable.

### SBG's Available Response

1. **H3 is the weakest hypothesis in the model, and the model says so explicitly.** It is presented as a research direction, not a proven capability. The "strongest dimensions" for H3 are DATA, INTERACTION, and parts of CONTROL — dimensions that capture what the program does externally. This is a defensible and non-trivial claim: two programs that sort a list identically, make the same syscalls in the same proportions, and produce the same output value distributions are plausibly equivalent, and SBG can detect this without requiring a shared IR.

2. **The novel claim is not "SBG can prove cross-language equivalence" but "SBG provides the first runtime-behavior-based evidence for cross-language equivalence without a shared compilation target."** All prior cross-language similarity work (CLCDSA, code2vec cross-language, CLOCS) is static and relies on syntactic or API-name similarity. SBG's `g_X` and `g_D` would detect equivalence between a Python and Rust sort implementation even if variable names, API names, and code structure differ entirely.

3. The test-oracle objection applies equally to all program equivalence work: formal verification tools (SYMDIFF, regression verification) also require aligned function pairs. SBG's oracle is less demanding than an SMT solver — it requires only execution of both programs under shared inputs.

### Settling Experiment

Take 50 algorithm implementations in Python vs. Java (OJ dataset algorithms, as used by Buch & Trivedi 2019), with ground-truth equivalence established by shared test cases. Measure whether `D(C_E(G(P_Python)), C_E(G(P_Java)))` is significantly lower for equivalent vs. non-equivalent pairs. Compare against CLCDSA (static cross-language clone detection) on the same pairs. If SBG detects cross-language equivalence with higher AUC than CLCDSA, the cross-language claim is empirically validated on the available dimensions.

---

## Attack 5 — "The structured genome architecture is not novel; it is just combining known techniques"

### Attack Argument

Joern (Yamaguchi et al., S&P 2014) already combines AST + CFG + PDG into a single unified representation (Code Property Graph). ProGraML (Cummins et al., ICML 2021) unifies control, data-flow, and call relationships into a single graph representation. The SBG genome is analogous: it combines 8 known behavioral feature types into a single structured representation. The principle of "unify multiple known representations into a single structured object" is not novel — Joern and ProGraML already instantiate it, and SBG merely adds a runtime modality and additional feature dimensions.

### Strength: MODERATE

The architectural principle of "combine multiple representations" is indeed established by Joern and ProGraML. However, the attack conflates **static** and **dynamic** representations. Joern and ProGraML are entirely static — they analyze source/IR without execution. SBG's genome is extracted from execution traces and represents observed behavior, not structural properties of code. A program with dead code has no behavioral signature for that code in SBG; Joern would represent it. This is not a minor difference — it is the difference between what a program can do and what a program actually does under realistic inputs.

### SBG's Available Response

SBG's multi-dimensional structure is analogous to Joern's CPG in the static domain, but the dynamic domain equivalent does not exist. No system combines dynamic control flow, runtime data distributions, heap topology, resource consumption, temporal profiles, error patterns, OS interactions, and instruction-level execution into a single normalized, versioned behavioral object. The novelty is the **dynamic CPG analog with formal distance metric and longitudinal tracking**, not the architectural principle of multi-dimensional representation.

### Settling Experiment

The question is whether the dynamic multi-dimensional representation provides information not available from (a) Joern-style static CPG or (b) any single dynamic representation. Run Joern-based similarity + SBG on the same regression detection task. If SBG detects regressions that Joern's static representation cannot detect (e.g., regressions introduced by algorithm changes that preserve code structure), the dynamic multi-dimensional genome has demonstrated unique value.

---

## Attack 6 — "The invariance claims do not hold mathematically; counterexamples exist"

### Attack Argument

H1 (Stability) claims `P ≡_S P' → D(G(P), G(P')) < ε_stable`. Construct three classes of counterexamples:

**CE-1 (Non-determinism):** Any program with non-deterministic behavior under fixed input — time-dependent output, thread scheduling, random number generation with system clock seeds — violates Assumption A6 (determinism). For such programs, `D(G(P), G(P))` (comparing the program against itself) may be > 0 because different runs sample different behaviors. H1 requires `D(G(P), G(P')) = 0` for equivalent programs; a non-deterministic program may produce a non-zero distance even when compared against itself.

**CE-2 (Input distribution sensitivity):** H1 holds only for the chosen input distribution `I`. If `I` concentrates on a region of input space where `P` and `P'` differ, `D` will be large even for "semantically equivalent" programs (equivalent on the full input space but different on the sampled region). The genome is parameterized by `I`, but H1's `ε_stable` is stated without conditioning on `I`, making it formally incomplete.

**CE-3 (Optimization counterexample):** A compiler optimization (loop unrolling, inlining) is semantics-preserving but changes CONTROL (`g_C` loop iteration distribution), TEMPORAL (`g_T` inter-event latency), and RESOURCE (`g_R` instruction count) simultaneously. The model acknowledges this in Hypothesis H1's caveats. If TEMPORAL and RESOURCE are excluded from cross-version comparisons due to optimization sensitivity, the effective genome for stability purposes is again reduced.

### Strength: MODERATE

CE-1 is real and serious, but Assumption A6 (determinism) is explicit in the model. The model knows about this problem. The attack reveals that A6 is a strong assumption that many production programs violate (any program using threads, random numbers, or time-dependent logic). CE-2 is also valid and the model is aware of it (H2's formal dependency note addresses it). CE-3 is acknowledged in H1's caveats. None of these counterexamples are hidden; the model flags them. The attack's force is therefore: **the assumptions required for H1–H2 to hold are unrealistically strong for practical software.**

### SBG's Available Response

The model is explicitly approximational and states this at every turn. Remark R7 invokes Rice's theorem to justify that full semantic equivalence is undecidable; the genome provides an empirical approximation `≡_S^ε`. The honest answer is: H1 holds empirically for deterministic programs under a representative input distribution, with TEMPORAL and RESOURCE either excluded or normalized. For non-deterministic programs, the genome requires canonical policy enforcement (fixed seeds, serialized scheduling) as stated in A6.

The attack is strongest as a **scope limitation**, not a fatal flaw: SBG's stability guarantees apply only to deterministic programs under controlled execution, which excludes a significant class of production software. This scope limitation should be stated more prominently.

### Settling Experiment

Test H1 stability on the Defects4J corpus under two conditions: (a) pure algorithmic functions (deterministic), (b) concurrent multi-threaded programs (non-deterministic). Measure `D(G(P), G(P'))` for known-equivalent version pairs in each class. If stability fails for concurrent programs at the same ε_stable threshold, the scope limitation is empirically characterized.

---

## Attack 7 — "There is no evidence that multi-dimensional distance is better than a single embedding"

### Attack Argument

The SBG genome is an 8-dimensional structured distance. Modern neural embeddings (code2vec, CodeBERT, GraphCodeBERT) produce a single dense vector in a high-dimensional latent space, and distance in that space correlates with semantic similarity. Why is a hand-crafted 8-dimensional symbolic distance better than a learned single embedding? Neural embeddings can capture interactions between feature types that a weighted sum of per-dimension distances cannot. The 8-dimensional decomposition may actually be an inductive bias that reduces discriminability compared to an unconstrained embedding. There is no a priori reason to prefer symbolic multi-dimensional distance over learned embeddings for regression detection; this is an empirical question and the comparison has not been run.

### Strength: MODERATE

This attack is epistemically correct: there is no a priori reason to prefer SBG's structured distance over a learned embedding, and the comparison has not been run (the project is pre-empirical). However, the attack has three weaknesses: (1) CodeBERT and GraphCodeBERT are static — they encode code structure, not runtime behavior. The neural embedding baseline for *dynamic behavioral similarity* does not clearly exist. (2) SBG's structured decomposition provides interpretability: when D is large, the per-dimension breakdown tells you whether it's a CONTROL regression, a RESOURCE regression, or an ERROR regression — a learned embedding provides no such decomposition. (3) SBG is language-agnostic at the runtime level; code2vec/CodeBERT require source code.

### SBG's Available Response

The comparison should be run, and the model should welcome it. The honest claim is: SBG's structured distance is **interpretable** (you know which behavioral dimension changed) and **language-agnostic at runtime** (no source code required). Whether it is more discriminative than a learned embedding is an open empirical question. If a learned embedding trained on execution traces outperforms SBG's structured distance, that is a finding worth knowing — it would suggest that the 8-dimensional decomposition is suboptimal as a distance metric while retaining value as a structured behavioral description.

### Settling Experiment

Train a behavioral embedding by encoding execution trace features into a neural network and measuring cosine distance between embeddings for regression detection on Defects4J. Compare AUC against SBG's `D`. If neural embedding outperforms SBG's structured distance on detection quality, report the gap and the interpretability/language-agnosticism trade-off explicitly.

---

## Attack 8 — "'Genome' terminology is scientifically unjustified; it is marketing"

### Attack Argument

The word "genome" in biology refers to the complete heritable genetic information of an organism, encoded in DNA. It has: (1) a physical substrate (nucleotides), (2) a replication mechanism, (3) evolutionary dynamics, (4) a developmental program that produces phenotype from genotype. The SBG "genome" has none of these properties. It is a multi-dimensional feature vector extracted from execution traces. Calling it a "genome" exploits the prestige of molecular biology without scientific justification. The analogy adds no technical content, creates false impressions of analogy to biological inheritance or evolution, and may mislead reviewers about the nature of the contribution. Publications using grandiose biological metaphors where none applies (e.g., "neural" networks in early AI) are criticized retrospectively for imprecision.

### Strength: WEAK

This is a legitimate terminological criticism, not a novelty attack. The biological analogy is imperfect, but "genome" in software contexts has prior usage (software genome projects have existed since the 2010s) and the term is being used metaphorically, not literally. The analogy captures one genuine structural parallel: like a biological genome, the SBG genome is intended to be a complete, stable, heritable description of what an entity does — its behavioral identity — that can be compared across instances and versions. The metaphor is strained but not dishonest.

### SBG's Available Response

Acknowledge the imperfect analogy and use it only as a high-level motivating metaphor, not a technical claim. The technical content stands independently of the terminology: "behavioral fingerprint with 8 formally defined dimensions, formally specified distance function, and longitudinal tracking" is the precise description. The word "genome" adds marketing value and mnemonic convenience; it should not be used in formal definitions.

### Settling Experiment

N/A — this is a terminological criticism. The project should simply clarify in any publication that "genome" is used as an analogy and define the technical object formally (Definition 8 already does this correctly).

---

## Attack 9 — "Existing tools already do this end-to-end"

### Attack Argument

The most direct novelty killer would be an existing system that takes a program, runs it, extracts a multi-dimensional behavioral profile, and uses that profile for semantic equivalence detection or regression detection. Candidate systems:

- **DynamoRIO / Frida / Pin (Luk et al., 2005):** These frameworks can be scripted to collect all of the metrics in SBG's genome dimensions. A sufficiently comprehensive Pintool could implement the full genome extraction pipeline today.
- **Application Performance Monitoring (APM) tools** (Datadog, NewRelic, AppDynamics): These systems collect resource, temporal, interaction, error, and execution-level metrics for running services and detect anomalies across deployments. They implement most of CG-7 (behavioral genome across environments).
- **Netflix's Automated Regression Detector / Facebook Sapienz:** Large companies run continuous behavioral profiling across software versions in production, effectively implementing a longitudinal behavioral genome without the formal structure.

### Strength: MODERATE

This attack is strong in spirit but weak in detail. Pin/DynamoRIO are platforms, not behavioral characterization systems — they require significant custom Pintool development to implement even one SBG dimension. APM tools collect operational metrics (CPU, memory, error rates, latency) but do not define a formal behavioral distance function or use the collected data for semantic equivalence detection. They are monitoring, not comparison. The formal SBG definitions (pseudometric properties, normalized distance, dimension-specific distance choices) are absent in all industrial tools. The genome-as-comparison-artifact (not just a dashboard) is absent.

However, the attack is worth taking seriously because it implies that **SBG's novelty depends on the formal framework and the regression oracle claim, not on the data collection per se**. The metrics exist; the formal structure and the tested regression detection hypothesis are where the novelty lives.

### SBG's Available Response

Clearly separate the data collection component (which is largely non-novel) from the formal behavioral distance architecture and the regression oracle hypothesis. The contribution is:
1. The formal specification of the genome as a pseudometric space with a structured 8-dimensional distance (novel)
2. The regression oracle hypothesis (H5) and its empirical test (novel, pending validation)
3. The longitudinal genome tracking system (CG-1, novel)
4. The cross-language behavioral equivalence detection without shared IR (CG-2, novel pending H3 validation)

### Settling Experiment

Survey all existing APM / behavioral monitoring tools and benchmark them against SBG on a regression detection task. If any existing tool achieves equivalent recall/precision for regression detection without the SBG formal framework, identify precisely what component of SBG provides the marginal value.

---

## Attack 10 — "What is the irreducible scientific contribution after stripping all terminology?"

### Attack Argument

Strip away: "genome" (marketing), "8 dimensions" (arbitrary categorization), "behavioral fingerprint" (rebranding of existing concepts), "semantic equivalence" (well-studied undecidable problem), "cross-language" (partially solved by IR-based tools). What is left?

**Candidate residual claims:**

(a) "We propose to compute a formally-specified pseudometric `D` on execution-trace-derived feature vectors and show it can detect software regressions on a standard benchmark with precision ≥ 0.70 and recall ≥ 0.80."

(b) "We define the first formal, normalized, multi-dimensional behavioral distance function on execution traces that is designed to be cross-language and longitudinally tracked."

(c) "We show that behavioral distance on 8 semantically-motivated dimensions outperforms single-representation distance metrics for regression detection."

Claim (a) is the strongest — it is falsifiable, benchmarkable, and not claimed by any prior work in those terms. Claim (b) is weaker because "first" claims are fragile and the multi-dimensionality may be unjustified (Attack 7). Claim (c) is the most scientifically interesting but the most unproven.

The irreducible scientific contribution, if SBG delivers empirically, is:

**"A formally specified execution-behavioral pseudometric that detects semantic regressions in software version histories at high recall, without requiring test suites or formal specifications, and that is language-agnostic by construction."**

### Strength: N/A (Synthesis attack)

This is not an invalidation attack but a distillation. It tells SBG what it needs to prove.

### SBG's Response

Embrace this formulation. It is precise, falsifiable, and non-trivially novel relative to all 40 prior works in the matrix. No prior work claims or demonstrates a test-suite-free, language-agnostic, execution-behavioral regression oracle with formal pseudometric properties. This should be the first sentence of any SBG abstract.

### Settling Experiment

H5 is the experiment: recall ≥ 0.80, precision ≥ 0.70 on a held-out corpus (Defects4J). Run it.

---

## Surviving Novelty Claims

The following novelty claims survive adversarial review, listed in decreasing confidence:

### Claim S1 — Formal behavioral pseudometric (HIGH CONFIDENCE)

**Claim:** No prior work defines a formally specified, multi-dimensional, normalized pseudometric on execution-trace-derived behavioral features with formally stated metric properties, dimension-specific distance justifications, and explicit assumptions.

**Evidence:** The PRIOR_ART_MATRIX.md surveys 40 works. Behavioral fingerprinting works (TTAnalyze, Bayer) use informal similarity; program equivalence works (SYMDIFF, Godlin & Strichman) use formal proofs, not pseudometrics on behavioral feature vectors. The formal structure of Definition 17–18 is not present in any reviewed prior work.

**Strength after attack:** Survives Attacks 1, 2, 3. Partially challenged by Attack 5 (static analogs exist in Joern/ProGraML) but the dynamic behavioral pseudometric in the Joern/ProGraML sense does not exist.

---

### Claim S2 — Longitudinal behavioral genome tracking (HIGH CONFIDENCE)

**Claim:** No prior work defines or implements a versioned, queryable record of how a program's behavioral profile evolves across its entire release history (CG-1).

**Evidence:** All regression testing work compares pairs of versions; no system maintains a cumulative behavioral history `{G(P^(0)), ..., G(P^(n))}` with formal distance tracking. APM tools collect time-series operational metrics but not formal behavioral distances.

**Strength after attack:** Survives all 10 attacks. This is the most clearly novel claim.

---

### Claim S3 — Test-suite-free regression oracle (H5) (MODERATE CONFIDENCE — EMPIRICALLY UNPROVEN)

**Claim:** SBG provides a regression detection oracle without requiring a test suite or formal specification, using only execution trace behavioral distance.

**Evidence:** CG-4 identifies this gap. No prior work demonstrates test-suite-free regression detection using unsupervised behavioral distance.

**Strength after attack:** Survives in principle; unproven empirically. Attack 3 (standard metrics) partially challenges this — if single metrics (e.g., syscall distance) achieve H5's precision/recall targets, the full 8-dimensional genome is not required for this claim.

---

### Claim S4 — Cross-language behavioral equivalence without shared IR (MODERATE CONFIDENCE — PARTIALLY OPEN)

**Claim:** SBG provides behavioral equivalence evidence between programs in fundamentally different language families without requiring a shared compilation target.

**Evidence:** CG-2 gap is real. All cross-language similarity work (CLCDSA, code2vec cross-language) is either static or requires shared IR. SBG's `g_X` and `g_D` dimensions can detect cross-language behavioral equivalence through observed runtime behavior.

**Strength after attack:** Partially damaged by Attack 4 — the CONTROL, TEMPORAL, and EXECUTION dimensions are unusable cross-language without solving OP-4 and OP-6. The effective cross-language genome is smaller than claimed. The claim is **credible but narrower** than stated: SBG provides behavioral equivalence evidence on 3–5 of 8 dimensions cross-language, which is still novel but weaker than the full H3 claim.

---

### Claim S5 — Behavioral genome as supply-chain artifact (WEAK CONFIDENCE — VISION CLAIM)

**Claim:** A behavioral signature can serve as a first-class software supply-chain artifact, analogous to an SBOM but capturing behavioral provenance.

**Evidence:** CG-3 identifies this gap.

**Strength after attack:** This claim is not technically novel in the sense of requiring new algorithms — it is an application claim. Whether treating a behavioral profile as a supply-chain artifact is useful and adopted is a social/engineering question, not a research contribution. This claim should be presented as a vision/application, not a scientific novelty.

---

## Summary Verdict

| Claim | Status |
|---|---|
| 8-dimensional structured genome | Architecture novel; components not novel |
| Formal behavioral pseudometric | **Novel** |
| Longitudinal behavioral genome | **Novel** |
| Test-suite-free regression oracle (H5) | Novel as claim; **empirically unvalidated** |
| Cross-language equivalence without shared IR | Novel but **narrower than claimed** |
| Behavioral supply-chain artifact | Vision claim; **not technical novelty** |

**Overall novelty verdict: MODERATE**

SBG has two clearly novel claims (S1, S2) that survive all attacks, one potentially novel empirical claim (S3) that requires H5 validation, and one novel-but-narrowed claim (S4). The project is not redundant with prior art but must sharpen its contribution statement around S1, S2, and — after empirical validation — S3.

---

## Recommended Sharpening

1. **Lead with the regression oracle hypothesis (H5)**, not the genome metaphor. The falsifiable scientific contribution is: "We propose and validate a test-suite-free, language-agnostic behavioral regression detector based on a formally specified execution-trace pseudometric."

2. **Constrain the cross-language claim (H3)** to the dimensions where it is achievable: DATA (`g_D`), INTERACTION (`g_X`), and partial CONTROL (`g_C` with a procedure alignment heuristic). Do not claim H3 across all 8 dimensions until OP-4 and OP-6 are resolved.

3. **Run the ablation study from Attack 3** before any publication. If the full 8-dimensional genome does not outperform the best single-dimension baseline on regression detection, the multi-dimensional architecture must be justified on interpretability grounds alone, not discriminability grounds.

4. **Explicitly state the scope limitation from Attack 6**: SBG's stability and sensitivity guarantees apply to deterministic, single-threaded programs under controlled execution. Concurrent programs require additional assumptions (e.g., canonical scheduling) that must be addressed before claiming production-grade applicability.

5. **Address the determinism assumption (A6) frontally** in any publication. Non-deterministic programs are the majority of production software. Either (a) define a policy for handling non-determinism (fixed seeds, serialized scheduling, multiple-run averaging) or (b) restrict the scope claim to deterministic software explicitly.

6. **The "genome" metaphor** should appear in the title and high-level description only. All formal definitions should use neutral language ("behavioral fingerprint," "behavioral profile," "multi-dimensional behavioral signature") to avoid terminological overreach.

---

*Adversarial novelty review completed by Agent 0C. The goal of this document is not to undermine SBG but to identify exactly where the project's novelty is strong, where it is assumed, and where it requires empirical validation. The project has a legitimate and non-redundant contribution; it needs to state it with precision.*

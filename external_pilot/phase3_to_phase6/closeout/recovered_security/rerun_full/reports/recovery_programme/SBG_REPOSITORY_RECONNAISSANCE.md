# SBG REPOSITORY RECONNAISSANCE & ARCHITECTURAL AUDIT

**Date:** 2026-11-16  
**Auditor:** Principal Empirical Software Engineering Researcher & Independent Reviewer  
**Repository Working Tree:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW`  
**Core Repository:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG` (HEAD `3425693`, branch `remediation/sbg-v4`)  
**Validation & Pre-Submission Suite:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION`

---

## 1. Executive Summary & Core Mission

This reconnaissance report presents the verified architectural, experimental, and empirical reality of the Software Behaviour Genome (SBG) project. The objective is to replace historical assumptions with grounded, mathematically verified facts.

### Key Verified Architectural & Empirical Realities:
1. **What SBG Implements:** A dynamic trace collection and representation system for Python programs (`sys.settrace` in worker thread sandbox, capturing line executions, call/return events, variable value string representations up to 100 chars, and call topology). The composite similarity metric ($d_{\text{V5}}$) is computed as a weighted linear combination:
   $$d_{\text{V5}} = 0.50 \cdot d_{\text{V3}} + 0.25 \cdot d_{\text{temporal}} + 0.25 \cdot d_{\text{state}}$$
   where $d_{\text{V3}}$ is call graph / instruction Jaccard distance, $d_{\text{temporal}}$ is sequence alignment distance, and $d_{\text{state}}$ is variable transition spectrum distance.
2. **Prediction Target & Label Definition:** Pairwise semantic equivalence classification between a base program $P$ and a variant $P'$. Label $y=0$ denotes semantics-preserving (EQUIVALENT / SP transformations, e.g., renaming, restructuring), while $y=1$ denotes semantics-changing (CHANGED / SC mutations, e.g., operator swap, off-by-one).
3. **Historical Performance Evolution:**
   - **V1–V4 (Static representations):** Suffered severe structural-semantic inversion (AUROC 0.22–0.55). SP transforms induced larger AST/token changes than minor SC mutations.
   - **V5–V7 (Early dynamic output-reading):** Suffered output-leakage and entry-point aliasing defects (SP-2 rename defects).
   - **V8–V9c (Output-free protocol):** Addressed entry-point aliasing. V9c validation AUROC = 0.7514.
   - **V10 (Headline frozen benchmark, 19 programs, 638 pairs):** SBG V5 achieved AUROC 0.8968 [0.8629, 0.9216].
4. **The Critical Empirical Finding (H4 / Baseline Crisis):**
   - SBG V5 **does not** provide statistically significant incremental predictive value beyond cheap execution statistics and edit size ($\Delta\text{AUROC} = +0.0014\ [-0.0742, 0.0631]$, $p=0.914$).
   - A non-linear baseline (Random Forest on execution statistics + edit size, `RF_d4_EXx`) significantly outperforms SBG V5 (AUROC 0.9552 vs 0.8968, $\Delta = +0.0584$).
   - Real-world bug benchmarks (BugsInPy: 0.497, QuixBugs: 0.444) perform at or below random chance.

---

## 2. Repository Inventory and Component Decomposition

```
SBG-FINALREVIEW/
├── SBG/                                 # Core Software Behaviour Genome Repository
│   ├── sbg/                             # Feature extraction & genome implementations
│   │   ├── extraction/dynamic/          # Tracer (sys.settrace), state/temporal/resource genomes
│   │   ├── extraction/static/           # Static control, data, error extractors
│   │   ├── v2/                          # Sandbox execution runner & normalizer
│   │   ├── v3/                          # Call graph & instruction topology genome (d_V3)
│   │   └── v5/                          # Temporal sequence alignment & state transition genomes
│   ├── benchmark/                       # Synthetic benchmarks & corpus
│   │   ├── datasets/                    # Synthetic pair datasets (train/dev/val/test across versions)
│   │   ├── corpus/                      # Base programs (121 authored programs across 4 tiers)
│   │   └── transformations/             # SP generators (12 transforms) & SC mutators (12 mutations)
│   ├── external/                        # External real-world bug benchmarks
│   │   ├── bugsinpy/                    # BugsInPy extracted programs & test harnesses
│   │   ├── quixbugs/                    # QuixBugs Python benchmark programs
│   │   └── quixbugs_java/               # QuixBugs Java reference programs
│   ├── experiments/final/               # Scoring, baseline models, statistical evaluation
│   ├── baselines/                       # Static & dynamic competitor baselines
│   └── artifacts/                       # Frozen experiment outputs, predictions, manifests
├── IEEE_ACCESS_PRE_SUBMISSION/          # Full Forensic Audit, Baseline Suite & Work Packages
│   ├── WP_A_B_COMPARATIVE_BENCHMARK/    # Head-to-head competitor models (ValueSpectra, PathSpectra, K-grams)
│   ├── WP_C_ABLATIONS/                  # Systematic genome dimension ablation analyses
│   ├── WP_D_EXTERNAL_VALIDATION/        # BugsInPy, QuixBugs audit, confounds, & leakage logs
│   ├── WP_E_MATH_GRAY_CODE/             # Diagnostic probe on runaway mutant loops
│   ├── WP_F_ADVERSARIAL_REVIEW/         # Peer review simulation & methodological critique
│   └── WP_LITERATURE_FOLLOWUP/          # Literature verification & prior art corrections
└── venvs/                               # CPython 3.13 and 3.9 virtual environments
```

---

## 3. The 10 Fundamental Questions Answered

### Q1: What does SBG actually implement?
SBG implements dynamic program instrumentation using Python's `sys.settrace` inside a timeout-guarded sandbox (`SandboxRunner`, 5 runs, max 5,000 events/trace). It extracts:
- Execution paths and call trees ($V_3$)
- Temporal event alignment profiles ($V_5$ temporal)
- Local variable value snapshots and transition spectra ($V_5$ state)
- Scalar counters (instruction histograms, trace lengths, exception occurrences).

### Q2: What does the behavioural representation contain?
The representation is a multi-modal feature vector containing:
1. **Topology:** Jaccard similarities on line coverage sets, function call sequences, and basic block transitions.
2. **Temporal Profile:** Dynamic time warping / sequence alignment distance over instruction type sequences.
3. **State Profile:** Shannon entropy of variable values, value change frequencies, and string representation Jaccard distances across function entries and exits.

### Q3: How is the representation constructed?
Both base program $P$ and candidate variant $P'$ are executed against a fixed battery of synthesized test inputs. Traces $T(P, I_k)$ and $T(P', I_k)$ are recorded for each input $I_k$. Distances between corresponding traces are computed along each genome axis, normalized, and aggregated into a scalar dissimilarity score $d(P, P')$.

### Q4: What is the prediction target?
Binary classification of program pairs $(P, P')$:
- $y = 0$: Semantically Equivalent (output identical across all valid domain inputs).
- $y = 1$: Semantically Discrepant (output diverges on at least one valid input).

### Q5: How are labels generated?
- **Synthetic Benchmark:** Ground-truth labels are defined by generator construction. $P'$ is produced by applying either an AST semantics-preserving rewrite (SP-1 to SP-12) or a mutation operator (SC-1 to SC-12).
- **Oracle Validation:** In V8–V10, labels were audited with an independent high-volume test generator (10,000 random inputs per pair) to detect dangling references or accidental semantic preservation.

### Q6: Which features are available at prediction time?
In the test-time deployment scenario, SBG assumes that both the base program and the candidate patch/mutant can be executed in a sandbox on pre-existing unit test inputs or synthesized inputs. Features derived strictly from execution traces of $P$ and $P'$ are available. Fixed-version information or future oracle outputs are strictly prohibited.

### Q7: How are training and testing separated?
- In V10: Split by base program (project-disjoint). 19 programs in `v10_test` (638 pairs), 11 programs in `v9c_val` (432 pairs), 13 programs in `v9c_dev` (464 pairs), and 45 programs in `v9c_train` (1610 pairs).
- No base program appears in more than one split.

### Q8: Which results can be reproduced bit-for-bit?
- `v10_test` (638 pairs): SBG V5 AUROC 0.8968, Random Forest on Exec Stats AUROC 0.9552, Linear Combiner AUROC 0.8913.
- `v9c_val` (432 pairs): SBG V5 AUROC 0.7514, Random Forest on Exec Stats AUROC 0.8667.
- Python 3.13.5 environment determinism produces exact matching test statistics and bootstrap confidence intervals.

### Q9: Which results are supported only by historical reports?
- Legacy V1–V4 claims regarding embedding baseline performance (e.g., CodeBERT) where subword n-gram fallback was used.
- Cross-language claims (Java/Python) were evaluated on only 5 illustrative examples and are unsupported.

### Q10: Which claims in previous manuscript drafts are unsupported?
1. Claim that SBG provides state-of-the-art semantic change detection (CONTRADICTED: simple execution statistics + random forest beat it by $\Delta = +0.058$).
2. Claim of incremental value over conventional features (CONTRADICTED: $\Delta\text{AUROC} = +0.0014$, $p=0.914$).
3. Claim of real-world bug detection capability (CONTRADICTED: BugsInPy AUROC = 0.497, QuixBugs AUROC = 0.444).
4. Claim of cross-language generality (UNSUPPORTED: not systematically evaluated).

---

## 4. Architectural & Empirical Bottlenecks Diagnosed

1. **Information Collapse in Dimension Fusion:**
   Ablation studies reveal that the State Genome alone achieves AUROC 0.9171 on `v10_test`, whereas the composite 3-part SBG V5 achieves 0.8968. Combining topology ($V_3$) and temporal alignment with state transitions degrades discrimination.
2. **Confound of Execution Counters:**
   Most synthetic semantic mutations in the benchmark cause significant shifts in loop counts, branch executions, or trace lengths. A scalar feature—`trace_len_mean`—achieves AUROC 0.8918 on its own, rendering complex trajectory alignment redundant on this benchmark.
3. **External Generalization Failure:**
   When applied to real bugs in BugsInPy and QuixBugs, test inputs rarely exercise the exact buggy path with sufficient sensitivity without triggering full test failure or crash, resulting in near-zero trace divergence on surviving executions and random-chance discrimination.

---

## 5. Reconnaissance Conclusion

SBG is not a failed engineering artifact; it is a meticulously audited empirical system whose primary scientific value is **methodological and diagnostic**:
- It demonstrates how subtle structural/execution confounds mislead defect prediction models.
- It proves that complex sequence/state alignment does not add value beyond scalar execution statistics on standard transformation benchmarks.
- It provides a benchmark protocol for isolating genuine behavioural signal from edit-size artifacts.

# SBG INDEPENDENT BENCHMARK STRATEGY & EVALUATION POLICY

**Date:** 2026-11-16  
**Auditor/Author:** Principal Software Engineering Researcher & Empirical Scientist  
**Focus:** Moving Beyond Synthetic Generator Artifacts to Rigorous Independent Benchmarks

---

## 1. Scientific Imperative & Strategy

To satisfy IEEE Access publication standards, SBG's empirical claims must not rely solely on the self-built synthetic benchmark generator (`v10_test`, `v9c`). We establish an auditable, multi-tier benchmark acquisition and evaluation strategy spanning:

1. **Synthetic Replication on Independent Generators (Tier 1):**
   Evaluating independently constructed transformation benchmarks (e.g., SeqCoBench / MBPP mutations) where transformations were written by independent researchers without SBG code or author overlap.
2. **Real-World Python Defect Suites (Tier 2):**
   Auditing and evaluating real developer bug fixes mined from open-source repositories (BugsInPy) and canonical algorithmic repair sets (QuixBugs).
3. **Multi-Language Repository Defect Suites (Tier 3 - Feasibility & Boundaries):**
   Documenting exact operational and architectural requirements for Defects4J (Java), ManyBugs (C), and Bears (Java), establishing exact feasibility boundaries for trace instrumentation.

---

## 2. Benchmark Acceptance & Exclusion Criteria

To prevent survivorship bias and unrepresentative filtering:
1. **Nominal vs Usable Size Audit:** Every benchmark must explicitly distinguish between its nominal catalog size and the actual usable evaluation size.
2. **Zero-Leakage Policy:** Test execution information from fixed versions must never be used at prediction time.
3. **Execution Feasibility Verification:**
   - Single-entry callable interface without unmocked I/O (`stdin`/`stdout` dependence).
   - Traceable within sandbox resource limits (5 runs, $\le 5,000$ events, 1.0 s timeout per execution).
   - Compatibility with CPython runtime without unresolvable binary dependencies.
4. **Exclusion Logging:** Every dropped program, version, or pair must be permanently recorded in an auditable exclusion log with an explicit category (e.g., `IMPORT_ERROR`, `TYPE_MISMATCH`, `TIMEOUT`, `IO_DEPENDENT`, `SYNTAX_ERROR`).

---

## 3. Four-Benchmark Architectural Investigation

### Benchmark A: Defects4J (Java)
- **Official Source:** `https://github.com/rjust/defects4j` (v2.0.0, 854 bugs across 17 open-source Java projects).
- **Target Unit:** Multi-file repository-scale Java codebases (e.g., Commons-Lang, JFreeChart, Closure Compiler).
- **Feasibility Assessment:** Non-Python. Requires JVM bytecode instrumentation (e.g., ASM / Java Agent) rather than `sys.settrace`. Java reference implementation exists as conceptual prototype (QuixBugs-Java EEP pilot), but full Defects4J trace collection requires a standalone Java agent harness.

### Benchmark B: BugsInPy (Python)
- **Official Source:** `https://github.com/soarsmu/BugsInPy` (51 bug cases across 12 Python projects).
- **Target Unit:** Real bug fix commits.
- **Feasibility Assessment:** Usable Python units extracted into `SBG/external/bugsinpy/`. High import dependency rejection rate (10.2% eligibility yield when isolating standalone helper units). Evaluated in WP-D.

### Benchmark C: ManyBugs (C)
- **Official Source:** `https://repairbenchmarks.cs.umass.edu/` (185 C bugs across 9 large open-source programs: gzip, lighttpd, php, wireshark).
- **Target Unit:** Large C applications with POSIX build systems.
- **Feasibility Assessment:** Non-Python. Requires GCC/LLVM compiler instrumentation (`-finstrument-functions` or Clang Sanitizer trace hooks). Incompatible with direct CPython sandbox tracer.

### Benchmark D: Bears (Java)
- **Official Source:** `https://github.com/bears-bugs/bears-benchmark` (251 Java bugs mined from Travis CI build failures).
- **Target Unit:** Multi-file Maven/Gradle Java projects.
- **Feasibility Assessment:** Non-Python. Requires dedicated JVM agent trace infrastructure.

---

## 4. Benchmark Stratification Matrix

| Benchmark | Language | Nature of Defects | Usable Sample Size | Role in SBG Evaluation | Key Methodological Takeaway |
|---|---|---|---|---|---|
| **SBG $V_{10}$ Headline** | Python | Synthetic SP/SC Transformations | 638 pairs (19 programs) | Primary Controlled Headline Evaluation | Demonstrates structural inversion; shows null incremental value over execution stats ($p=0.914$). |
| **SBG $V_{9c}$ Confirmatory** | Python | Synthetic SP/SC Transformations | 432 pairs (11 programs) | Confirmatory Replication Split | Confirms $V_{10}$ baseline trends on independent program split. |
| **BugsInPy** | Python | Real Open-Source Developer Bugs | 257 pairs (15 programs) | Real-World Defect Evaluation | AUROC 0.497 (random chance); reveals input sparsity and crash dominance in real bug traces. |
| **QuixBugs-Python** | Python | Real Algorithmic Bugs | 40 programs (152 pairs) | Algorithmic Defect Evaluation | Canonical AUROC 0.444; reveals parameter type mismatch on unannotated signatures. |
| **SeqCoBench (MBPP)** | Python | Independent Synthetic Mutations | 1,364 pairs (486 programs) | Independent-Generator Replication | Demonstrates external synthetic validity; controlled against token-bag shortcut baselines. |
| **Defects4J / Bears / ManyBugs** | Java / C | Multi-file Real-World Software Faults | Catalog: 854 (D4J), 251 (Bears), 185 (ManyBugs) | Cross-Language Boundary Analysis | Defines the operational boundary: requires native compiler/JVM bytecode instrumentation agents. |

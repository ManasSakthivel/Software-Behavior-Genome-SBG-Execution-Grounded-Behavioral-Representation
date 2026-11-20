# Independent Audit of Previous Benchmark Exclusions: Defects4J, Bears, and ManyBugs

**Author:** Principal Software Engineering Researcher & Empirical Evaluation Reviewer  
**Date:** 2026-11-16  
**Evaluation Scope:** Individual forensic audit of three historical non-evaluated benchmarks (Defects4J, Bears, ManyBugs).

---

## 1. Executive Summary & Audit Overview

In earlier SBG evaluation reports, external defect datasets were reported with 0 evaluated pairs and categorized under a combined label ("NS / Not methodologically suitable"). This audit re-examines Defects4J, Bears, and ManyBugs **individually** across ten strict criteria:

1. Exact reason evaluation stopped.
2. Whether acquisition succeeded.
3. Whether buggy and fixed versions were obtained.
4. Whether compilation succeeded.
5. Whether tests executed.
6. Whether buggy and fixed versions produced valid execution traces.
7. Whether SBG features were extracted.
8. Whether cases were excluded and why.
9. Nature of the blocker (Technical, Environmental, Methodological, or Fundamental Task Mismatch).
10. Actionable remediation pathways and adapter feasibility.

---

## 2. Individual Benchmark Forensic Breakdown

### 2.1 Benchmark 1: Defects4J (Java)
* **Official Repository:** `https://github.com/rjust/defects4j` (Just et al., ISSTA 2014)
* **Nominal Size:** 835 active reproducible real-world Java bugs across 17 open-source projects (`Chart`, `Cli`, `Closure`, `Codec`, `Collections`, `Compress`, `Csv`, `Gson`, `JacksonCore`, `JacksonDatabind`, `JacksonXml`, `Jsoup`, `JxPath`, `Lang`, `Math`, `Mockito`, `Time`).

| Evaluation Stage | Status | Forensic Findings & Evidence |
|:---|:---:|:---|
| **Acquisition** | **Partial (Metadata Only)** | Literature CrossRef metadata downloaded (`literature/crossref/just_defects4j_2014.json`). The full ~150 MB framework and repository checkouts were not downloaded during in-repo runs due to size/bandwidth constraints. |
| **Buggy / Fixed Versions** | **Not Materialized** | Defined upstream via `defects4j checkout -p <project> -v <id>b/f`, but not checked out into the local SBG workspace. |
| **Compilation** | **Blocked** | Defects4J requires project-specific JDK compilation environments (JDK 7/8 for v1.x; JDK 11/17 for v2.0). System host has OpenJDK 21. |
| **Test Execution** | **Not Executed** | Requires invoking `defects4j test` driving project-level JUnit test suites. |
| **Trace Production** | **0 Traces** | SBG's tracer (`TraceCollector`) is implemented in Python via `sys.settrace`, which cannot trace JVM bytecode execution. |
| **Feature Extraction** | **0 Features** | No Java trace representations existed in the repository schema. |
| **Exclusion Log** | **835 / 835 Excluded** | Excluded under reason code `EXC-LANG-JVM` (JVM bytecode boundary). |
| **Blocker Classification** | **Technical & Architectural** | **Technical:** Incompatible language runtime (Java bytecode vs Python runtime). **Architectural:** Requires a dedicated JVM JavaAgent (e.g. ByteBuddy / ASM bytecode injector) hooking into JUnit test execution without leaking functional test assertions. |
| **Remediation Feasibility** | **Feasible via Adapter** | Defects4J can be evaluated if a standalone JavaAgent tracer is built and executed against single-method defect units extracted from Commons-Lang / Commons-Math. |

---

### 2.2 Benchmark 2: Bears Benchmark (Java)
* **Official Repository:** `https://github.com/bears-bugs/bears-benchmark` (Madeiral et al., SANER 2019)
* **Nominal Size:** 251 reproducible Java bugs from 72 open-source projects mined from Travis CI build failures.

| Evaluation Stage | Status | Forensic Findings & Evidence |
|:---|:---:|:---|
| **Acquisition** | **Metadata Only** | Evaluated via GitHub API and published paper specifications. Repository not cloned. |
| **Buggy / Fixed Versions** | **Not Materialized** | Bug and patch revisions are cataloged as JSON commit metadata requiring per-project Maven builds. |
| **Compilation** | **Blocked** | Heterogeneous Maven project builds across 72 external repositories; requires containerized execution environments. |
| **Test Execution** | **Not Executed** | Test harnesses rely on project-level Maven/Surefire test runners. |
| **Trace Production** | **0 Traces** | No JVM tracer attached to Bears test runners. |
| **Feature Extraction** | **0 Features** | None extracted. |
| **Exclusion Log** | **251 / 251 Excluded** | Excluded under reason code `EXC-LANG-JVM` / `EXC-CONTAINER`. |
| **Blocker Classification** | **Environmental & Architectural** | **Environmental:** High build dependency heterogeneity across 72 repositories with broken/stale remote Maven repositories. **Architectural:** Lack of containerized JVM bytecode execution tracing. |
| **Remediation Feasibility** | **Low (High Maintenance Overhead)** | Bears requires maintaining 72 independent Docker build environments. Lower scientific return than structured Java benchmarks like Bugs.jar or isolated Defects4J units. |

---

### 2.3 Benchmark 3: ManyBugs (C)
* **Official Source:** `https://repairbenchmarks.cs.umass.edu/` (Le Goues et al., IEEE TSE 2015)
* **Nominal Size:** 185 C bugs across 9 large open-source systems (`gzip`, `lighttpd`, `nullhttpd`, `php`, `python`, `sed`, `wireshark`, `libtiff`, `fbc`).

| Evaluation Stage | Status | Forensic Findings & Evidence |
|:---|:---:|:---|
| **Acquisition** | **Metadata Only** | Official website inspected. Multi-gigabyte virtual machine / Docker images not fetched. |
| **Buggy / Fixed Versions** | **Not Materialized** | Large multi-file C codebases with complex Autotools / `configure` / `make` systems. |
| **Compilation** | **Blocked** | Requires legacy 32-bit/64-bit GCC toolchains and system libraries (e.g. legacy GLIBC, libxml2, PCRE). |
| **Test Execution** | **Not Executed** | Shell script test suites (`test.sh`). |
| **Trace Production** | **0 Traces** | No C binary function/line execution tracer was integrated into SBG. |
| **Feature Extraction** | **0 Features** | None extracted. |
| **Exclusion Log** | **185 / 185 Excluded** | Excluded under reason code `EXC-LANG-C` (C native binary boundary). |
| **Blocker Classification** | **Technical & Environmental** | **Technical:** Native binary execution requires compiler-assisted instrumentation (e.g. GCC `-finstrument-functions`, Clang XRay, or LLVM sanitizers). **Environmental:** Legacy POSIX build systems difficult to reproduce reliably on modern Apple Silicon / arm64 architecture. |
| **Remediation Feasibility** | **High Overhead for Whole Systems** | Full ManyBugs systems require full OS emulation. A cleaner, direct C evaluation path is single-unit standalone C benchmarks such as **Codeflaws**, which compile cleanly under modern Clang/GCC with deterministic test inputs. |

---

## 3. Comparative Summary & Remediation Strategy

| Benchmark | Language | Scope | Primary Blocker | Was Exclusion Justified? | Replacement / Remediation Path |
|:---|:---:|:---|:---|:---:|:---|
| **Defects4J** | Java | 17 multi-file repos (835 bugs) | JVM JavaAgent bytecode tracer required; multi-file Maven builds | **Yes (Technical barrier)** | Evaluate on isolated Java units / **Bugs.jar** Java defect benchmark. |
| **Bears** | Java | 72 heterogeneous repos (251 bugs) | Broken remote Maven dependencies; Docker container sprawl | **Yes (Environmental fragility)** | Focus on pinned Java benchmarks with self-contained unit harnesses. |
| **ManyBugs** | C | 9 large C systems (185 bugs) | Legacy Autotools/32-bit build systems; lack of C tracer | **Yes (Environmental & Technical)** | Evaluate on standalone C defect benchmark: **Codeflaws** (3,902 C defects). |

---

## 4. Conclusion

The previous blanket exclusion of Java and C benchmarks was technically justified by the architecture of SBG's original Python `sys.settrace` engine, but was presented without sufficient individual documentation.

To provide genuine multi-language independent validation:
1. **Java:** We evaluate **Bugs.jar** and self-contained Java algorithmic units using a dedicated Java execution tracer.
2. **C:** We evaluate **Codeflaws** using Clang compiler instrumentation and native trace parsing.

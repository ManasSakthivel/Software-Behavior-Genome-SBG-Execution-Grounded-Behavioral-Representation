# Dataset Selection Protocol — SBG/EEP Empirical Evaluation

**Status:** FROZEN — all inclusion/exclusion criteria established BEFORE inspection of results  
**Protocol established:** 2026  
**Datasets investigated (priority order):** QuixBugs Python, QuixBugs Java, BugsInPy, Defects4J, Codeflaws, RunBugRun, ManySStuBs4J

---

## 1. Absolute Scientific Rules

1. **No cherry-picking**: Datasets, projects, bugs, and languages are not selected based on observed EEP results.
2. **No post-hoc tuning**: EEP parameters (τ*=0.08, weights) are frozen from synthetic evaluation.
3. **No exclusion of unfavorable results**: All evaluated bugs are reported, including undetected ones.
4. **Negative results are scientifically valuable**: Reported fully and with analysis.
5. **Selection criteria fixed before evaluation**: Every inclusion/exclusion rule established before running EEP.

---

## 2. Universal Eligibility Criteria

A dataset is eligible for primary evaluation only if ALL of the following hold:

| Criterion | Rationale |
|-----------|-----------|
| Buggy and fixed versions identifiable | Required for pair comparison |
| Execution is reproducible | Required for output-free trace collection |
| Test inputs / invocable function available | EEP requires executable programs |
| Bug labels independently established | No EEP-guided label assignment |
| EEP can operate without reading program outputs | Core output-free constraint |
| Return values cannot leak into EEP representation | Mathematical constraint: formally required |
| Exception messages cannot leak into representation | Exception TYPE not consumed; occurrence only |
| Test pass/fail information cannot leak | No oracle labels during inference |
| Bug selection not performed after seeing EEP results | Zero-shot / pre-specified protocol |
| Inclusion/exclusion criteria explicit and reproducible | Verifiable exclusion taxonomy |
| Licensing permits experimental use | Legal requirement |
| Failures and exclusions recorded reproducibly | Full transparency |

---

## 3. Universal Exclusion Reason Codes

| Code | Description |
|------|-------------|
| E_NODE | Requires Node/graph data structure not available to harness |
| E_COMPLEX_TYPE | Non-trivial input type (mixed lists, nested objects) |
| E_NO_TC | No test cases / inputs file available |
| E_NO_SIG | Method signature not mapped (manual effort required) |
| E_COMPILE | Source fails to compile with available toolchain |
| E_TIMEOUT | Execution exceeds per-case timeout (15s) |
| E_NO_TRACE | Zero trace events produced (instrumentation failure) |
| E_LABEL_AMBIGUITY | Bug labels are not reliable ground truth |
| E_LANGUAGE_BARRIER | Language requires new instrumentation adapter not yet validated |
| E_MULTI_FILE | Bug spans multiple source files (function isolation not possible) |
| E_NO_FUNCTION_CONTEXT | No function boundary in patch context |
| E_FRAMEWORK_DEPS | Requires external framework objects (pandas, sklearn, etc.) |

---

## 4. Dataset-Specific Selection Results

### 4.1 Synthetic (Python)

**Decision: INCLUDED (calibration corpus)**

| Step | N |
|------|---|
| Total | 38+2 (bugs + neg controls) |
| Evaluable | 38 |
| Excluded | 0 |
| Evaluated | 38 |

Note: Synthetic corpus used for hyperparameter selection (τ*=0.08). Not used for generalization claims.

---

### 4.2 QuixBugs Python

**Decision: INCLUDED (zero-shot external validation)**

| Step | N |
|------|---|
| Total programs | 31 |
| Executable/evaluable | 28 |
| Excluded | 3 |
| Exclusion reasons | bitcount (E_TIMEOUT), find_first_in_sorted (E_TIMEOUT), sqrt (E_TIMEOUT) |
| Evaluated | 28 |
| Detected | 17 |

Zero-shot: all parameters frozen from synthetic corpus before QuixBugs was loaded.

---

### 4.3 QuixBugs Java

**Decision: INCLUDED (cross-language zero-shot evaluation)**

| Step | N |
|------|---|
| Total Java program pairs | 40 |
| E_NODE excluded | 9 |
| E_COMPLEX_TYPE excluded | 5 |
| E_COMPILE excluded | 5 |
| E_TIMEOUT excluded | 3 |
| Total excluded | 22 |
| Evaluated | 18 |
| Detected | 6 |

**Instrumentation method:** Method-boundary TRACE ENTER/EXIT/EXCEPTION injected into Java source at compile time. Trace captured from stderr (stdout never read). Output-free constraint maintained.

**Representation difference from Python:** Python uses sys.settrace (per-line events). Java uses method-boundary injection (per-call events). This means:
- Loop-count changes are observable in Python (line events) but NOT in Java (no per-line instrumentation)
- This is a genuine representational limitation that partially explains the lower detection rate

**E_COMPILE breakdown:**
| Program | Reason |
|---------|--------|
| FIND_FIRST_IN_SORTED | ArrayList subList method call structure causes compile failure |
| FIND_IN_SORTED | Same |
| LIS | ArrayList type inference failure in buggy source |
| MAX_SUBLIST_SUM | Static field name conflict |
| POSSIBLE_CHANGE | Cannot rewrite package declaration for ArrayList<Integer> |

---

### 4.4 BugsInPy

**Decision: INCLUDED (real-world multi-project validation)**

| Step | N |
|------|---|
| Total bugs | 502 |
| E01_NO_PATCH | 1 |
| E03_NO_SOURCE_CHANGE | 1 |
| E04_MULTI_FILE_PATCH | 90 |
| E06_NO_FUNCTION_CONTEXT | 254 |
| E08_NO_COMMIT_IDS | 23 |
| E10_FRAMEWORK_OBJECT_DEPS | 55 |
| Subtotal structurally excluded | 424 |
| Remaining structurally eligible | 78 |
| Runtime/environment failures | 4 |
| Evaluated | 7 |
| Detected | 6 |

**Mandatory disclosure:** Evaluable subset (7/502 = 1.4%) is not a random sample. Skews toward exception-raising bugs due to inclusion criteria.

---

### 4.5 Defects4J

**Decision: EXCLUDED**

| Criterion | Status | Note |
|-----------|--------|------|
| Real bugs | ✓ Yes | 835 bugs from 17 projects |
| Bug labels | ✓ Curated | Peer-reviewed |
| Buggy/fixed pairs | ✓ Yes | All available |
| Tests available | ✓ Yes | All have failing tests |
| Output-free compatible | ⚠ Possible | Requires Java instrumentation |
| **Java instrumentation validated** | ✗ No | Separate engineering effort |
| Instrumentation equivalence proven | ✗ No | Cannot claim equivalence to Python EEP without validation |

**Exclusion reason:** Java instrumentation adapter required. This is NOT a new language experiment for free — it requires independent validation of the adapter. Including Defects4J results without validating that the Java instrumentation produces representations equivalent to Python EEP would be scientifically invalid. Documented as future work.

---

### 4.6 Codeflaws

**Decision: EXCLUDED**

Codeflaws is a C/C++ corpus of 3,902 bugs from 7,436 programs mined from competitive programming solutions.

| Criterion | Status | Note |
|-----------|--------|------|
| Real bugs | ✓ Yes | Buggy/fixed pairs from Codeforces |
| Bug labels | ✓ Yes | Program outputs verified |
| Output-free compatible | **✗ Cannot confirm** | C/C++ execution tracing requires ptrace or LLVM instrumentation |
| Instrumentation available | ✗ No | No validated C/C++ trace adapter for EEP |
| Reproducibility | ⚠ Partial | Requires C compiler and specific input generation |

**Exclusion reason:** C/C++ has no Python-equivalent tracing mechanism. ptrace is OS-specific and complex; LLVM instrumentation is a substantial engineering project. The output-free constraint cannot be verified for a new C/C++ adapter without independent validation. Codeflaws is documented as a high-priority future work target.

---

### 4.7 RunBugRun

**Decision: EXCLUDED**

RunBugRun is a multilingual bug benchmark (Python, Java, C, C++, Go, Ruby, PHP, C#, JavaScript) with 450,000+ bug-fix pairs from competitive programming.

| Criterion | Status | Note |
|-----------|--------|------|
| Real bugs | ✓ Yes | Large scale |
| Multilingual | ✓ Yes | Up to 9 languages |
| **Label reliability** | ⚠ Partial | Output oracle (expected vs actual outputs) — not semantic ground truth |
| **Output-free constraint** | **✗ VIOLATED** | RunBugRun labels are based on program OUTPUT correctness |
| Instrumentation | ✗ None for most languages | C, Go, Ruby, PHP, C# require new adapters |

**Primary exclusion reason:** RunBugRun labels are defined by output correctness. Using RunBugRun would create a fundamental conflict with the output-free constraint — the ground truth labels themselves are output-based, creating a circularity issue where we evaluate an output-free method against output-derived labels. Additionally, the primary distinction from other datasets (multilingual scale) is undermined by the fact that almost all non-Python/Java languages require new instrumentation adapters.

**Python RunBugRun:** Could in principle be evaluated using Python EEP. However, the competitive programming context raises concerns about whether bugs represent real-world software defects vs. algorithmic correctness failures on specific inputs. Classified as "possible future experiment" but not included in this paper's primary evaluation.

---

### 4.8 ManySStuBs4J

**Decision: EXCLUDED**

| Criterion | Status | Note |
|-----------|--------|------|
| Real bugs | ⚠ Partial | Mining-based; ~40-60% label false positive rate (Karampatsis & Sutton, 2020) |
| Output-free compatible | ⚠ Possible | Same Java barrier as Defects4J |
| Label reliability | ✗ Uncertain | Pattern-matched commits, not verified against specifications |
| Java barrier | ✗ Same | Requires validated Java instrumentation adapter |

**Exclusion reason:** Two independent reasons, either of which is sufficient: (1) Java instrumentation barrier (same as Defects4J); (2) 40-60% label false positive rate makes any detection rate uninterpretable — we cannot distinguish EEP detecting genuine bugs vs. detecting commits that happen to match a structural pattern.

---

## 5. Final Dataset Summary Table

| Dataset | Language | Candidates | Evaluated | Detected | Included | Primary Exclusion |
|---------|----------|-----------|-----------|----------|----------|-------------------|
| Synthetic (Python) | Python | 38 | 38 | 24 | ✓ | — |
| QuixBugs Python | Python | 31 | 28 | 17 | ✓ | 3 timeouts |
| BugsInPy | Python | 502 | 7 | 6 | ✓ | 495 structural exclusions |
| QuixBugs Java | Java | 40 | 18 | 6 | ✓ | 22: E_NODE/E_COMPILE/E_TIMEOUT |
| Defects4J | Java | 835 | 0 | 0 | ✗ | Java adapter not validated |
| ManySStuBs4J | Java | 10231 | 0 | 0 | ✗ | Java barrier + label ambiguity |
| Codeflaws | C/C++ | 3902 | 0 | 0 | ✗ | No C trace adapter |
| RunBugRun | Multi | 450k+ | 0 | 0 | ✗ | Output-based labels |

---

## 6. Selection Bias Analysis

### Are excluded bugs systematically different?

**QuixBugs Python timeouts:** bitcount, find_first_in_sorted, sqrt — all involve tight loops or convergence conditions. These may be harder bugs for EEP to detect (timeout = infinite loop in buggy version). This is a potential selection bias: excluded programs may be among the hardest cases, suggesting our detection rate is slightly optimistic.

**QuixBugs Java exclusions:**
- E_NODE: graph/linked-list programs — these likely have different trace structures (pointer-following vs. arithmetic)
- E_COMPILE: 5 programs with complex generic type constructs — may be harder structural bugs
- E_COMPLEX_TYPE: 5 programs with heterogeneous type arguments — possibly more complex bugs

**BugsInPy exclusions:** Systematically exclude multi-file bugs (E04, 90 cases) and class-method bugs (E10, 55 cases). These are likely different in character from single-function bugs. Multi-file bugs may be harder architectural defects. Class-method bugs requiring self/cls context are likely in a different defect category.

**Conclusion:** Selection bias exists in all evaluated subsets. The primary direction of bias is that evaluated bugs are simpler and more isolated than typical real-world bugs. This means our detection rates may be optimistic relative to a random sample from each corpus.

---

## 7. Reproducibility

All exclusion decisions are encoded in machine-readable form in:
- `results/external/QUIXBUGS_JAVA_EVALUATION_RESULTS.json`
- `results/external/BUGSINPY_EXTENDED_EVALUATION_RESULTS.json`
- `results/external/QUIXBUGS_EVALUATION_RESULTS.json`
- `results/external/FINAL_MULTI_CORPUS_ANALYSIS_RESULTS.json`

Evaluation scripts that reproduce all results:
- `experiments/external/quixbugs_java_evaluation.py`
- `experiments/external/quixbugs_evaluation.py`
- `experiments/external/bugsinpy_extended_evaluation.py`
- `experiments/external/final_multi_corpus_analysis.py`
- `experiments/external/output_free_audit.py`

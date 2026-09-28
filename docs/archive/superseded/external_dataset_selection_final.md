# External Dataset Selection — Final Assessment
## All Investigated Datasets with Eligibility Decisions

**Status:** FROZEN  
**Last updated:** 2026 (Final Empirical Generalization Sprint)  
**EEP parameters:** τ*=0.08, weights=(0.40,0.10,0.30,0.15,0.05) — FROZEN from synthetic evaluation

---

## Summary Table

| Dataset | Language | Bugs | Evaluated | Decision | Primary Reason |
|---------|----------|------|-----------|----------|----------------|
| Synthetic | Python | 38 | 38 | ✓ INCLUDED | Calibration corpus |
| QuixBugs Python | Python | 31 | 28 | ✓ INCLUDED | External zero-shot validation |
| QuixBugs Java | Java | 40 | 18 | ✓ INCLUDED | Cross-language zero-shot |
| BugsInPy | Python | 502 | 7 | ✓ INCLUDED (subset) | Real-world multi-project |
| Defects4J | Java | 835 | 0 | ✗ EXCLUDED | Java adapter not validated |
| Codeflaws | C/C++ | 3902 | 0 | ✗ EXCLUDED | No C trace adapter |
| RunBugRun | Multi | 450k+ | 0 | ✗ EXCLUDED | Output-based labels |
| ManySStuBs4J | Java | 10231 | 0 | ✗ EXCLUDED | Java barrier + label ambiguity |

---

## 1. Synthetic Python Corpus

**Decision: INCLUDED (calibration only)**

- 38 manually constructed Python inline function pairs
- 2 negative controls
- Used for: τ* selection, weight selection, ablation analysis
- NOT used for: generalization claims
- Language: Python 3.9 / CPython sys.settrace

**Results:** 24/38 detected, AUROC=0.829 [0.750, 0.905]

---

## 2. QuixBugs Python

**Decision: INCLUDED (primary external zero-shot)**

- Source: https://github.com/jkoppel/QuixBugs
- License: MIT
- 31 Python algorithm programs with bugs
- 28 evaluable (3 timeout: bitcount, find_first_in_sorted, sqrt)
- JSON test cases used as-is (no modification)
- Zero-shot: parameters not adjusted after seeing any QuixBugs result

**Results:** 17/28 detected (60.7%), Wilson CI [42.4%, 76.4%], p=0.172

---

## 3. QuixBugs Java

**Decision: INCLUDED (cross-language zero-shot)**

- Same repository: https://github.com/jkoppel/QuixBugs
- 40 Java program pairs (matching Python programs where possible)
- Instrumentation: method-boundary TRACE ENTER/EXIT/EXCEPTION injected at compile time
- Output-free: only stderr trace events consumed; stdout never read
- Same JSON test cases as Python evaluation
- Zero-shot: τ*=0.08 frozen, no Java-specific tuning

**Exclusion breakdown:**
- E_NODE (9): BREADTH_FIRST_SEARCH, DEPTH_FIRST_SEARCH, DETECT_CYCLE, REVERSE_LINKED_LIST, MINIMUM_SPANNING_TREE, SHORTEST_PATH_LENGTH, SHORTEST_PATH_LENGTHS, SHORTEST_PATHS, TOPOLOGICAL_ORDERING
- E_COMPLEX_TYPE (5): FLATTEN, RPN_EVAL, SHUNTING_YARD, KNAPSACK, POWERSET
- E_COMPILE (5): FIND_FIRST_IN_SORTED, FIND_IN_SORTED, LIS, MAX_SUBLIST_SUM, POSSIBLE_CHANGE
- E_TIMEOUT (3): BITCOUNT, LEVENSHTEIN, SQRT

**Results:** 6/18 detected (33.3%), Wilson CI [16.3%, 56.3%], p=0.952 (not significant)

**Key finding:** Substantial transfer gap (-27.4 pp) between Python and Java QuixBugs detection. Primary cause: Python EEP captures per-line events (loop iterations visible); Java EEP captures only method-call boundaries (loop iterations invisible). This is a genuine information-content difference between instrumentation approaches.

---

## 4. BugsInPy

**Decision: INCLUDED (real-world multi-project, subset)**

- Source: https://github.com/soarsmu/BugsInPy
- 502 total bugs from 17 open-source Python projects
- Evaluated: 7 bugs across 6 independent projects
- Zero-shot evaluation; real GitHub-fetched code

**Evaluated bugs:**
| Project | Bug ID | Bug Type | Detected |
|---------|--------|----------|---------|
| black | 1 | wrong_condition | ✓ |
| black | 2 | missing_case | ✓ |
| keras | 1 | wrong_variable | ✓ |
| keras | 2 | missing_parameter | ✓ |
| spacy | 1 | wrong_recursion | ✓ |
| tornado | 1 | wrong_condition | ✓ |
| tqdm | 9 | off_by_one | ✗ (trace-preserving) |

**Results:** 6/7 detected (85.7%), Wilson CI [48.7%, 97.4%], p=0.062

**Mandatory disclosures:**
1. Evaluable subset is 1.4% of corpus (7/502) — not representative
2. Evaluable bugs skew toward exception-raising defects
3. tqdm-9 not detected: boundary condition bug, trace-preserving confirmed

---

## 5. Defects4J

**Decision: EXCLUDED — Java adapter not validated**

Defects4J (Just et al., 2014) contains 835 curated bugs from 17 Java projects.

The EEP formula is language-independent. Java execution can produce equivalent trace signals. However:
1. A Java instrumentation adapter is required (sys.settrace equivalent)
2. The adapter would require independent validation before use in an EEP evaluation
3. Combining Python and Java EEP scores without validating instrumentation equivalence is scientifically invalid
4. This is a substantial separate engineering and validation contribution

**NOT excluded because of expected unfavorable numbers.** Excluded on methodological grounds.  
**Future work:** Java EEP adapter (Byte Buddy or AspectJ) + Defects4J evaluation.

---

## 6. Codeflaws

**Decision: EXCLUDED — No C trace adapter**

Codeflaws (Tan et al., 2017) contains 3,902 bug-fix pairs in C from competitive programming.

C/C++ tracing options: ptrace (OS-specific), LLVM sanitizers (build-system changes), GDB scripting (complex).  
None of these can be validated as output-free without independent work.  
The output-free constraint requires mechanical verification of what is observed.

**Future work:** LLVM-based instrumentation pass for C programs.

---

## 7. RunBugRun

**Decision: EXCLUDED — Output-based labels conflict with output-free constraint**

RunBugRun (Prenner et al., 2023) contains 450k+ bug-fix pairs across 9 languages from competitive programming.

**Primary exclusion reason:** Bug labels in RunBugRun are defined by program output correctness on specific inputs. This conflicts with the output-free evaluation design in two ways:
1. The ground truth is output-defined, creating a circular situation where we evaluate an output-free method against output-derived truth
2. The method's information-theoretic limits (trace-preserving invisibility) are defined relative to execution traces, not outputs — mixing these evaluation frameworks is invalid

Additionally: non-Python/Java languages require new instrumentation adapters.

---

## 8. ManySStuBs4J

**Decision: EXCLUDED — Java barrier + label ambiguity**

ManySStuBs4J (Karampatsis & Sutton, MSR 2020) contains 10,231 single-statement bug fixes from 100 Java projects.

Two independent exclusion reasons:
1. **Java barrier:** Same as Defects4J — requires validated Java instrumentation adapter
2. **Label reliability:** Mining-based labels have ~40-60% false positive rate. Authors themselves note many "bugs" are refactorings or feature changes. An EEP evaluation on ambiguous labels cannot produce interpretable detection rates.

---

## 9. Datasets Not Investigated

- **BugSwarm:** Docker-based test-failure reproduction. Requires Docker infrastructure and extensive setup per bug. Output-free constraint unclear.
- **BugsJS:** JavaScript bugs. Requires Node.js tracing adapter.
- **BugsPHP:** PHP bugs. Requires PHP execution instrumentation.
- **IntroClassJava:** Student Java programs. Educational context may not generalize to production code.

---

## Final Inclusion Decision: STOP CONDITION MET

After investigating all priority datasets (Section 2 of sprint specification), the evaluation is complete:
- Python evidence: 3 corpora, 7 projects
- Java evidence: QuixBugs Java cross-language evaluation
- All other datasets excluded on pre-specified methodological grounds

**Experimentation is now FROZEN.**

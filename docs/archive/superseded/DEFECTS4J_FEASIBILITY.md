# SBG — Defects4J Feasibility Analysis
## Can EEP Be Legitimately Adapted to Java?

**Created:** 2025  
**Sprint:** A+ Multi-Corpus External Validity Sprint  
**Status:** Feasibility analysis complete  
**Decision:** Technically valid extension; NOT included in primary evaluation this sprint

---

## Executive Summary

Defects4J is the gold standard Java bug benchmark (835 real bugs, 17 projects, peer-reviewed).
This document formally assesses whether SBG/EEP can be legitimately extended to Java and
what that extension would entail.

**Verdict:** The extension is **technically valid** but requires:
1. A Java execution tracer producing equivalent structural events
2. Validation of the output-free invariant on Java programs
3. A test-input extraction pipeline from JUnit test methods

**This sprint does not include a numerical Defects4J evaluation** because the Java
infrastructure is not yet validated to the standard required by the protocol.
The analysis here documents what evidence would be needed and what exists already.

---

## 1. Language-Independent Components of EEP

The EEP distance function uses five features:

| Feature | Language independence | Java equivalent | Validity |
|---------|----------------------|-----------------|---------|
| `d_exc_frac` | ✓ Independent | `exceptions / total_executions` | ✓ Valid — exceptions exist in Java |
| `d_exc_jaccard` | ✓ Independent | Java exception class names | ✓ Valid — exception types are more explicit in Java |
| `d_trace_length` | ✓ Independent | Method enter/exit event count per input | ✓ Valid — JVMTI or AspectJ can capture this |
| `d_line_seq` | ⚠ Partial | Source-line-relative sequence hash | ⚠ Requires line-number instrumentation |
| `d_sequential_drift` | ✓ Independent | Repeated-call behavioral change | ✓ Valid — mutable static fields create equivalent effect |

**Key finding:** All five features have structurally equivalent counterparts in Java.
The d_line_seq feature requires source line numbers, which are available via Java debug
info (`javac -g`) but require more setup than Python's `sys.settrace`.

---

## 2. What Python EEP Assumptions Transfer to Java

### Transfer cleanly:
- Exception behavior as an output-free signal
- Execution trace length as a structural metric
- Sequential repeat behavior for detecting static state bugs
- Output-free invariant: method call depth, call sequence, exception events — all observable without reading return values

### Transfer with adaptation:
- Line sequence: Python uses `frame.f_lineno - frame.f_code.co_firstlineno` (automatic). 
  Java requires debug info or manual source-line annotation
- Function anonymization: Python uses `frame.f_code.co_name`. Java uses method names 
  which include class qualifier — same anonymization by first-call order is applicable

### Do NOT transfer:
- `sys.settrace` API — Python-specific
- `frame.f_code.co_firstlineno` — Python-specific attribute
- Import-time loading — Java requires compilation step
- Dynamic duck-typing test inputs — Java requires typed test inputs

---

## 3. Existing Java Infrastructure

An existing Java tracer infrastructure is documented in [`docs/v5/JAVA_INFRASTRUCTURE_DESIGN.md`](v5/JAVA_INFRASTRUCTURE_DESIGN.md):

| Component | Status | Coverage |
|-----------|--------|---------|
| `JavaInstrumenter` | Prototype | 3 of 10 benchmark programs |
| `JavaExecutor` | Prototype | Subprocess-based, stderr trace |
| `extract_genome()` | Prototype | Mirrors DynamicGenome schema |
| Output-free verification | Not done | Required before Defects4J use |
| Defects4J checkout pipeline | Not implemented | Required |
| JUnit input extraction | Not implemented | Required |

The existing infrastructure uses **string-level regex instrumentation** of Java sources,
which works for simple programs but has known limitations:
- No support for lambda expressions in hot paths
- No support for multi-catch blocks
- Not validated on the complexity level of Defects4J programs

---

## 4. Defects4J Dataset Properties

| Property | Value |
|----------|-------|
| Source | github.com/rjust/defects4j |
| Language | Java |
| Projects | 17 (Commons-Lang, JFreeChart, Closure Compiler, etc.) |
| Bugs | 835 real bugs (from issue trackers + commit history) |
| Bug provenance | Real developer-reported bugs, not mined patterns |
| Tests | JUnit test suites |
| Checkout | Automated via `defects4j checkout -p <project> -v <bug>b` |
| License | Apache-2.0 |
| Widely cited | Yes — gold standard for program repair research |

**Bug categories available:** null pointer dereference, wrong branch, missing check,
wrong value, API misuse, wrong loop bound, concurrency (not evaluable by EEP)

---

## 5. What Would Be Required for a Valid Defects4J Evaluation

### Prerequisites (not currently implemented):

1. **Java trace instrumentation for Defects4J-level programs**
   - Must handle inner classes, generics, lambda expressions
   - Must capture method-level enter/exit with source line numbers
   - Recommendation: use JVMTI agent or AspectJ (more robust than string-level injection)

2. **Output-free audit for Java adapter**
   - Must pass equivalent of OL-1 through OL-6 on Java programs
   - Must verify that trace events do not include return values
   - Formal proof or automated test suite required

3. **JUnit test input extraction**
   - Must extract concrete inputs from JUnit test methods
   - Must handle parameterized tests, test data providers
   - Edge cases: tests that use mock frameworks, external data files

4. **Defects4J checkout pipeline**
   - Must automate `defects4j checkout` for each bug
   - Must handle project-specific build requirements (Maven, Ant)
   - Must extract the single function under test from the larger codebase

5. **Cross-language validation**
   - Must verify that EEP distances on Java programs are calibrated to the same
     τ* = 0.08 threshold used for Python (or justify a different threshold)
   - Must establish whether d_EEP values are comparable across languages

### Timeline estimate:
A credible Defects4J evaluation would require approximately 2-4 weeks of infrastructure
work before any numerical results could be produced. Doing it in less time would produce
results of insufficient quality for a top-tier publication.

---

## 6. Defects4J Bug Classes That EEP Could Detect

Based on the known trace-changing/trace-preserving dichotomy:

### Likely detectable (trace-changing):
- `wrong_branch` — different branch taken → different line sequence
- `missing_null_check` — NPE thrown vs not → exception fraction changes
- `wrong_loop_bound` — different iteration count → trace length changes
- `wrong_recursion` — different recursion depth → trace length changes
- `wrong_comparison` — different branch selection → line sequence changes

### Likely invisible (trace-preserving):
- `wrong_value_returned` — correct execution path, wrong value
- `wrong_constant` — different constant used but same control flow
- `wrong_cast` — might not change control flow
- Concurrency bugs — not evaluable by single-thread EEP

---

## 7. Estimated Detection Rate on Defects4J

Based on the trace-changing fraction observed in Python datasets:

| Dataset | Trace-changing bugs | Trace-preserving bugs | EEP rate on trace-changing |
|---------|--------------------|-----------------------|---------------------------|
| Synthetic | ~65% | ~35% | ~95% |
| QuixBugs | 61% | 39% | 100% |
| BugsInPy (inline) | ~90% | ~10% | 100% |

**Conservative Defects4J estimate:**
If 50-60% of Defects4J bugs are trace-changing (plausible given the diversity of Defects4J),
and EEP detects ~95% of trace-changing bugs, then:
- Expected detection rate: 47-57%
- This would be a meaningful result but lower than BugsInPy

The lower expected rate is primarily due to:
1. More complex programs (more same-path bugs in large systems)
2. Java-specific test infrastructure overhead
3. Possible calibration difference between languages

---

## 8. Formal Feasibility Verdict

| Criterion | Status |
|-----------|--------|
| Language-independent core of EEP | ✓ VERIFIED — all 5 features have Java equivalents |
| Java instrumentation prototype exists | ✓ EXISTS — partial, needs validation |
| Output-free invariant can hold for Java | ✓ THEORETICALLY VALID — same argument applies |
| JUnit input extraction | ✗ NOT IMPLEMENTED |
| Defects4J checkout pipeline | ✗ NOT IMPLEMENTED |
| Output-free audit on Java programs | ✗ NOT DONE |
| Cross-language calibration | ✗ NOT VALIDATED |

**Overall feasibility: TECHNICALLY VALID, OPERATIONALLY NOT READY**

A Defects4J evaluation would constitute a **legitimate scientific extension** of EEP,
not a forced or invalid application. The theoretical justification is sound.
The engineering work required is substantial but well-defined.

---

## 9. Recommendation

Include Defects4J evaluation in a **follow-up paper** or **extended version** of the
current work, after:
1. Completing the Java JVMTI/AspectJ instrumentation infrastructure
2. Running the output-free audit on ≥ 10 Defects4J programs
3. Establishing cross-language calibration on shared Python/Java programs
4. Running leave-one-project-out analysis on a random 20% sample

**For the current paper:** Document this feasibility analysis as evidence that the
EEP approach is not Python-specific in principle, even if the current evaluation
is Python-only.

---

*Defects4J: Rjust et al., "Defects4J: A Database of Existing Faults to Enable Controlled  
Testing Studies for Java Programs", ISSTA 2014.*

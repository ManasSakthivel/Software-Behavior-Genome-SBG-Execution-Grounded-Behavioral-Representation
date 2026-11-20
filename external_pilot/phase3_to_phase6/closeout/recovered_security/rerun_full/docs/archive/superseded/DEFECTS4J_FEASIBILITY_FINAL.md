# Defects4J — EEP Adaptation Feasibility Analysis

**Decision: EXCLUDED from this paper. Documented as future work.**

Protocol hash: `fac6bd8e0cffc91b52ed88577637d199ccfda8cfe9200edc487094f7e8e5088b`  
Date: 2026  
Status: Feasibility analysis only — no numerical results

---

## 1. Background

Defects4J is a curated database of 835 reproducible real bugs from 17 open-source Java projects (Commons Lang, JFreeChart, Closure Compiler, etc.). It is a standard benchmark in automated program repair and fault localization research.

---

## 2. Language-Independent Components of EEP

EEP is defined over five features derived from execution traces:

| Feature | Definition | Language-Independent? |
|---------|-----------|----------------------|
| `trace_length_distance` | Relative difference in execution event counts | ✓ Yes — requires only event counting |
| `line_seq_divergence` | Normalized edit distance on line-execution sequences | ✓ Yes — requires ordered line-execution log |
| `sequential_drift` | Monotonic drift in line-number order | ✓ Yes — requires line numbers |
| `exception_fraction` | Fraction of inputs causing exceptions | ✓ Yes — requires exception capture |
| `timing_distance` | Normalized timing difference | ✓ Yes — requires wall-clock timing |

The EEP *formula* is language-independent. The *instrumentation layer* is language-specific.

---

## 3. Instrumentation Requirements for Java

Python EEP uses `sys.settrace()` — a standard, zero-dependency, per-line callback mechanism built into CPython.

Java has no equivalent built-in per-line tracing. The following mechanisms would be required:

### Option A: JVM TI (Tool Interface)
- Low-level C/C++ agent
- Per-bytecode/per-line callbacks available
- Requires native agent compilation and JVM startup flags
- High engineering complexity

### Option B: Java Instrumentation API + Byte Buddy / ASM
- Pure-Java bytecode manipulation
- Can inject per-line logging at instrumentation time
- Used by JaCoCo (coverage), OpenClover
- Moderate engineering complexity

### Option C: AspectJ Instrumentation
- AOP-based per-line execution interception
- Works at source or bytecode level
- Well-tested but adds aspect weaving overhead

### Option D: JaCoCo + Custom Reporter
- JaCoCo already collects per-line coverage
- Does NOT provide ordered execution sequences (only coverage bitmaps)
- Cannot reconstruct `line_seq_divergence` from coverage alone
- **Insufficient for EEP**

**Assessment**: A valid Java EEP adapter requires either Option B or Option C — both are substantial engineering efforts producing a new instrumentation component that would itself require validation.

---

## 4. Source-Level Assumptions

The Python EEP evaluator makes the following source-level assumptions that do not directly translate to Java:

| Assumption | Python EEP | Java/Defects4J |
|-----------|-----------|----------------|
| Function isolation | `exec()` in namespace dict | Requires class instantiation, dependency injection |
| Input construction | Python literals, tuples | Java objects, builders, mocks |
| Exception types | Python exception hierarchy | Java checked/unchecked exceptions, different type hierarchy |
| sys.settrace granularity | Per-line callbacks | Bytecode-level (line number map required) |
| Module isolation | Namespace dictionary | Classpath isolation, classloaders |
| No framework dependencies | Assumed for evaluable subset | Many Defects4J bugs involve Spring, Guava, Apache Commons |

---

## 5. Output-Free Invariant in Java

The output-free invariant — EEP never reads return values, stdout, stderr, test pass/fail, or oracle outputs — CAN be maintained for Java IF:

1. The trace collector captures only execution events (line numbers, exception types, counts)
2. The collector does NOT inspect return values or field values
3. The timing collector uses wall-clock or CPU time only

However, three Java-specific concerns arise:

- **JIT Compilation**: HotSpot may JIT-compile hot methods, changing observed trace lengths. Requires JVM warmup normalization.
- **Thread Interleavings**: Multi-threaded Java code may produce non-deterministic traces.
- **GC Pauses**: Wall-clock timing is noisier in Java due to garbage collection.

These are manageable with appropriate methodology but add noise not present in Python evaluation.

---

## 6. Defects4J Bugs — Evaluability Assessment

Of Defects4J's 835 bugs:

| Filter | Estimated Count | Reason |
|--------|----------------|--------|
| All bugs | 835 | — |
| Single-method changes | ~300–400 | Remaining bugs span multiple methods/files |
| Pure static methods (no object state) | ~100–150 | Remaining require object construction |
| Without Spring/Guava/external deps | ~50–100 | Many use Apache Commons APIs |
| Reproducible with simple inputs | ~30–70 | Estimated |

This estimation is based on published Defects4J literature (Just et al., 2014; Sobreira et al., 2018). A precise count would require the full taxonomy analysis performed for BugsInPy.

---

## 7. Scientific Validity Assessment

| Criterion | Status |
|-----------|--------|
| Real bugs | ✓ Yes — Defects4J bugs are real, curated, reproducible |
| Independent projects | ✓ Yes — 17 projects |
| Buggy/fixed versions | ✓ Yes — both available |
| Tests available | ✓ Yes — all bugs have failing tests |
| Output-free compatible | ✓ Possible with proper instrumentation |
| Reproducible by another researcher | ⚠ Requires engineering the Java trace adapter |
| Constitutes legitimate scientific extension | ✓ Yes — IF adapter is independently validated |

**Assessment**: A Defects4J evaluation IS scientifically legitimate — but ONLY if the Java trace adapter is (a) independently implemented, (b) independently validated, and (c) the output-free guarantee is re-verified for Java. These requirements constitute a separate engineering and evaluation project.

---

## 8. Decision

**Defects4J is EXCLUDED from this paper** for the following reasons:

1. **Engineering scope**: Implementing a validated Java trace adapter is outside the scope of this evaluation sprint. It is a substantial standalone contribution.

2. **Validation requirement**: A new instrumentation layer would require its own validation experiments (e.g., does JVM-level tracing produce equivalent signals to Python's sys.settrace?).

3. **Methodological incompatibility**: Combining Python EEP scores and Java EEP scores in one table without validating the instrumentation equivalence would be scientifically invalid.

4. **Honest scope**: This paper evaluates EEP on Python programs. Claiming generalization to Java without a validated Java adapter would be an unsupported extrapolation.

---

## 9. Future Work Statement

> A Java adaptation of EEP using JVM bytecode instrumentation (e.g., Byte Buddy or AspectJ) would enable evaluation on Defects4J's 835 bugs. This is a natural extension of the current work and constitutes a separate engineering and empirical contribution. The language-independent structure of the EEP formula (Section X) is designed to facilitate such adaptation.

---

## 10. What This Document Establishes

- The EEP formula is language-independent ✓  
- Java instrumentation is technically feasible ✓  
- Java adaptation is NOT done in this paper ✓ (documented limitation)  
- Defects4J is not silently ignored — it is assessed and explicitly excluded with justification ✓

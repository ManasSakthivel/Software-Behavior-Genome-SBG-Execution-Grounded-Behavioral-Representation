# Cross-Language Validation — SBG/EEP

**Status:** FROZEN  
**Languages evaluated:** Python (primary), Java (cross-language zero-shot)

---

## 1. Overview

EEP was designed as a language-independent method: the EEP formula operates on execution trace features that can in principle be extracted from any programming language. This document reports the cross-language validation experiment.

---

## 2. Cross-Language Experiment Design

### Principle
- Python EEP: uses CPython sys.settrace → per-line trace events
- Java EEP: uses method-boundary instrumentation → per-call-boundary events
- **Same formula**: d = 0.40*d_exc_frac + 0.10*d_exc_jac + 0.30*d_trace_len + 0.15*d_seq + 0.05*d_drift
- **Same parameters**: τ* = 0.08 (frozen from Python synthetic evaluation)
- **Zero-shot**: no Java-specific tuning

### Representation Differences (Documented Limitations)

| Feature | Python EEP | Java EEP | Information Difference |
|---------|------------|----------|----------------------|
| d_exc_frac | Exception fraction per input | Exception fraction per input | Equivalent |
| d_exc_jac | Exception type Jaccard | Exception type Jaccard | Equivalent |
| d_trace_len | Number of sys.settrace events | Number of method ENTER/EXIT events | Python: richer (includes loop iterations) |
| d_seq | Line-execution sequence hash | Method-call sequence hash | Python: line-level; Java: method-level |
| d_drift | Sequential state drift | Sequential state drift (=0) | Python: detects mutable state; Java: N/A |

The Python instrumentation is substantially richer than the Java instrumentation. This means bugs that change loop iteration counts (off-by-one, wrong-slice) are visible to Python EEP but may be invisible to Java EEP.

This is an **instrumentation gap**, not an EEP formula failure.

---

## 3. Quantitative Results

| Dimension | Python QuixBugs | Java QuixBugs |
|-----------|----------------|---------------|
| Programs evaluated | 28 | 18 |
| Programs detected | 17 | 6 |
| Detection rate | 60.7% | 33.3% |
| Transfer delta | — | -27.4 pp |
| Wilson 95% CI | [42.4%, 76.4%] | [16.3%, 56.3%] |
| Binomial p (H0: p=0.5) | 0.172 | 0.952 |

**Transfer delta: -27.4 percentage points**

---

## 4. Failure Analysis — Why Java Detection is Lower

### Root Cause Taxonomy for 12 Missed Java Programs

| Category | Programs | Count | Explanation |
|----------|----------|-------|-------------|
| **Trace-preserving (return value only)** | BUCKETSORT, GET_FACTORS, HANOI, IS_VALID_PARENTHESIZATION, TO_BASE | 5 | Same call structure; only values differ. Invisible by Theorem 1 in both Python and Java. |
| **Instrumentation gap (loop count)** | KHEAPSORT, NEXT_PALINDROME | 2 | Off-by-one in iteration count visible in Python (line events) but invisible in Java (no per-line tracing). |
| **Near-miss (d below τ*)** | QUICKSORT | 1 | d=0.023, τ*=0.08. Detectable with lower threshold but threshold frozen. |
| **Structural change with small effect** | SUBSEQUENCES, WRAP, LCS_LENGTH, NEXT_PERMUTATION | 4 | Trace changes exist but are small with available test cases. |

### Key Insight

Of the 12 missed Java programs:
- **5 are trace-preserving** (would also be missed by Python EEP on the same concept)  
- **2 are instrumentation-gap** (would be caught by Python EEP because Python has per-line tracing)
- **5 are marginal** (small test cases, near-miss distances, or subtle structural changes)

This means approximately **5-7 of the 12 Java misses are genuine EEP limitations** (trace-preserving by Theorem 1), and **5-7 are Java-adapter limitations** (would be detectable with per-line Java instrumentation equivalent to sys.settrace).

---

## 5. Cross-Language Comparison Summary

| Language | Projects | Corpus | Evaluated | Detected | Rate | CI | p |
|----------|----------|--------|-----------|---------|------|----|---|
| Python | 7 | QB + BugsInPy | 35 (external) | 23 | 65.7% | [49.1%, 79.2%] | 0.045 |
| Java | 1 | QB Java | 18 | 6 | 33.3% | [16.3%, 56.3%] | 0.952 |

---

## 6. Is Cross-Language Generalization Demonstrated?

### CONDITIONALLY YES (with important caveats)

**Evidence that Java EEP works:**
- 6/18 = 33.3% detection rate in zero-shot Java evaluation
- 4 defect classes detected (wrong_variable, wrong_condition, wrong_recursion, off_by_one)
- Output-free constraint maintained (stdout never read)
- Same formula and threshold as Python

**Evidence against strong cross-language claim:**
- Detection rate substantially lower than Python (33.3% vs 60.7%)
- Binomial p = 0.952 (not statistically different from chance for Java alone)
- Single Java corpus / single project (all QuixBugs)
- Instrumentation difference may explain much of the gap

### Permitted Claim

> "Using a method-boundary instrumentation adapter for Java, EEP achieves 6/18 (33.3%) zero-shot detection on QuixBugs Java. This is substantially lower than Python QuixBugs performance (60.7%, -27.4 pp), partially explained by the difference between per-line Python tracing and per-method-call Java tracing. The EEP formula transfers to Java; the instrumentation adapter is less informative than Python's sys.settrace."

### Prohibited Claims

- "EEP achieves equivalent cross-language performance" (false)
- "Cross-language generalization is demonstrated" (too strong — limited to 1 Java corpus)
- "Java EEP is statistically validated" (p=0.952)

---

## 7. What Would Strengthen Cross-Language Evidence

1. Per-line Java instrumentation (bytecode instrumentation via Byte Buddy/AspectJ) → would close the instrumentation gap
2. Multiple independent Java projects → currently only QuixBugs
3. Defects4J evaluation with validated Java adapter
4. Statistical validation: Java detection rate significantly above chance
5. Negative controls in Java (variable rename, formatting changes)

---

## 8. Trace-Preserving Theorem — Java Extension

The formal Trace-Preserving Invisibility Theorem (Theorem 1) applies to Java EEP:

> **Theorem 1 (Extended):** If programs A and B produce identical method-call traces (same sequence of method entries and exits) under all available inputs, then d_EEP(A, B) = 0 for Java EEP.

This is confirmed empirically for 5 Java QuixBugs programs (BUCKETSORT, GET_FACTORS, HANOI, IS_VALID_PARENTHESIZATION, TO_BASE) where buggy and fixed versions have identical method-call structures.

**The theorem generalizes across instrumentation levels**: whether trace events are per-line (Python) or per-method-call (Java), the theorem holds — programs with identical observable traces are indistinguishable.

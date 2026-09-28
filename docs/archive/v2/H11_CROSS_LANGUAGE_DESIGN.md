# H11 — Cross-Language Generalization: Design & Scope Document

**Agent:** G (H11 Cross-Language Experiment Design)  
**Status:** DESIGNED — INSUFFICIENT_EVIDENCE (infrastructure constraint)  
**Date:** 2025-07-07  
**Relates to:** `docs/v2/HYPOTHESES_V2.md` §H11  

---

## 1. The H11 Hypothesis (Pre-Registered)

From `docs/v2/HYPOTHESES_V2.md`:

> **H11 — Cross-Language Generalization Hypothesis**  
> Claim: Hybrid genomes identify equivalent behavior across Python and Java.  
> Formal statement: AUROC(cross_language, test) > 0.6  
> Note on power: N=15 cross-language pairs gives ~25% power at α_corrected=0.0042.  
> H11 is EXPLORATORY regardless of result — explicitly underpowered by design.

**Statistical test:** AUROC with bootstrap CI; explicit power acknowledgment  
**Correction rank:** 5 of 12 (Holm-Bonferroni family)  
**Falsification:** If AUROC ≤ 0.5, H11 is NOT SUPPORTED. If 0.5 < AUROC < 0.6 with wide CI → INSUFFICIENT EVIDENCE.

---

## 2. Infrastructure Audit — Java Execution Not Available

### 2.1 What the v2 execution stack supports

`sbg/v2/execution/runner.py` — `SandboxRunner`:

- Wraps `sbg.extraction.dynamic.tracer.Tracer` (Python-specific, uses `sys.settrace`)
- Accepts a Python **callable** and Python **inputs**
- Returns `ExecutionTrace` objects derived from Python interpreter hooks
- All `DynamicGenome` features (`coverage_size`, `anon_call_freq`, `call_depth_mean`,
  `hot_path_hash`, `exception_type_set`) are built from Python trace events

### 2.2 What is missing for Java

| Required for H11 | Exists? | Notes |
|---|---|---|
| Java subprocess executor (javac + java run) | ❌ NO | No JVM wrapper in runner.py |
| Java execution trace instrumentation | ❌ NO | sys.settrace is Python-only |
| Java AST parser | ❌ NO | No javalang / JavaParser integration |
| Java → DynamicGenome feature extraction | ❌ NO | Requires (1)+(2)+(3) first |
| Java behavioral equivalence ground truth | ⚠️ PARTIAL | Phase 5 has 15 pairs labeled manually |

### 2.3 What Phase 5 did (and its limitations)

`artifacts/phase5/cross_language_results.json` contains N=15 pairs with:

- **AUROC: 0.4091** — below 0.5, structural-semantic inversion present
- Method: **regex heuristics on Java source text** (not execution-derived)
- Limitation: `has_recursion` flag is unreliable (multiple CHANGED pairs have
  `has_recursion=True` matching their EQUIVALENT counterparts — the heuristic
  fires on any function call, not just self-calls)
- Limitation: N=15 bootstrap AUROC confidence interval is extremely wide
  (approximately ±0.20 at 95% CI — the entire range [0.2, 0.6] is plausible)

**This Phase 5 result cannot be used as evidence for or against H11** because
the features are not execution-derived and the corpus is too small for any
inference at α_corrected=0.0042.

---

## 3. Power Analysis

H11 pre-registers N=15 pairs giving approximately **25% power** at
α_corrected = 0.0042 (Holm-Bonferroni corrected across 12 hypotheses).

```
Power calculation basis:
  One-sided AUROC test: H0: AUROC=0.5, H1: AUROC=0.6
  Effect size d ≈ 0.25 (small-medium)
  α = 0.0042 (corrected), two-stage bootstrap
  N = 15 pairs → power ≈ 0.25

For 80% power at α=0.0042:
  Required N ≈ 120–150 cross-language pairs
  (using conservative effect size d=0.20)
```

This was **explicitly acknowledged in the pre-registration**. H11 is designated
EXPLORATORY regardless of outcome. A null result at N=15 does not falsify H11.

---

## 4. What Was Designed (Deliverables)

### 4.1 Behavioral Specification Corpus

`benchmark/cross_language/` — 10 Python programs (N=10), each containing:

| File | Specification | Category |
|---|---|---|
| `p01_bubble_sort.py` | Bubble sort, ascending, in-place copy | sorting |
| `p02_insertion_sort.py` | Insertion sort, stable, ascending | sorting |
| `p03_binary_search.py` | Binary search, sorted list, return index | searching |
| `p04_linear_search.py` | Linear search, first occurrence | searching |
| `p05_factorial.py` | n! iterative, n in [0,12] | arithmetic |
| `p06_gcd.py` | GCD Euclidean, iterative | arithmetic |
| `p07_fibonacci.py` | Fibonacci iterative, 0-indexed | arithmetic |
| `p08_palindrome.py` | Palindrome check, case-sensitive | string |
| `p09_reverse_string.py` | Reverse string, character-level | string |
| `p10_sum_list.py` | Sum of integer list | list_manipulation |

Each file provides:
- **Behavioral specification** in the module docstring (precise contract)
- **Implementation A** — Python idiomatic style
- **Implementation B** — Java-idiomatic style (explicit temp vars, while loops,
  index arithmetic) written in Python
- **Java equivalent note** — the Java method signature and control-flow signature
  (`n_loops`, `n_conditions`, `cyclomatic_complexity`, `has_recursion`)
- **Canonical test inputs** and **expected outputs** — identical for both impls

### 4.2 Experiment Design Script

`experiments/v2/cross_language_design.py` contains:

- `CROSS_LANGUAGE_PAIRS` — N=12 specification pairs (11 EQUIVALENT + 1 CHANGED)
- `PROTOCOL` — formal documentation of the comparison method, limitations, and
  H11 status
- Infrastructure audit — honest statement of why Java execution is infeasible

---

## 5. What This Design Achieves vs. What It Cannot Achieve

### 5.1 What IS achievable (Python-to-Python with Java-style impls)

**Test:** Can `DynamicGenome` recognize that Python-impl-A and Python-impl-B
(same spec, different style) are behaviorally equivalent, even when impl-B
uses Java-idiomatic style (explicit indices, while loops, temp variables)?

This is a **necessary precondition** for cross-language generalization:

```
If DynamicGenome(Python-impl-A) ≈ DynamicGenome(Python-impl-B)
    → supports that behavioral features are style-invariant
    → encouraging signal for future Java evaluation

If DynamicGenome(Python-impl-A) ≠ DynamicGenome(Python-impl-B)
    → DynamicGenome is sensitive to implementation style, not just behavior
    → cross-language generalization would likely fail even with Java execution
```

### 5.2 What is NOT achievable without Java execution

- **H11 formal test:** AUROC(cross_language, test) > 0.6
  requires actual Java `DynamicGenome` objects, which require Java traces
- **Cross-language behavioral signatures:** `coverage_size`, `anon_call_freq`,
  `call_depth_mean` are meaningless unless computed from actual Java execution
- **Claimed Java AUROC:** Any number computed without Java execution is fabricated

### 5.3 Comparison to Phase 5 approach

Phase 5 used regex heuristics (`n_loops`, `n_conditions`, cyclomatic complexity)
on Java source text as a proxy. This is **not execution-derived** and violates
the spirit of H11, which asks about **behavioral** (execution-derived) similarity.

The Phase 5 AUROC=0.4091 should be interpreted as:
*"Structural control-flow similarity between Python and Java source text gives
AUROC=0.4 — below chance, inversion present, feature space is misaligned."*

This is informative for feature engineering but is not a valid H11 test.

---

## 6. H11 Verdict: INSUFFICIENT_EVIDENCE

```
H11 verdict:         INSUFFICIENT_EVIDENCE
Reason:              Infrastructure constraint (no Java execution)
Scientific validity: VALID — absence of infrastructure is a reportable finding
Data available:      N=15 pairs with regex-heuristic features (Phase 5)
                     N=10 pairs with Python-only behavioral specs (this design)
AUROC available:     0.4091 (Phase 5, NOT execution-derived, NOT valid for H11)
Power at N=15:       ~25% — underpowered even if infrastructure existed
Decision:            H11 remains open; Java evaluation is future work
```

### 6.1 Why INSUFFICIENT_EVIDENCE is a valid scientific finding

INSUFFICIENT_EVIDENCE is not failure. It is a precise statement about the
limits of the current experimental apparatus. The pre-registration explicitly
anticipates this: *"H11 is EXPLORATORY regardless of result — explicitly
underpowered by design."*

Reporting INSUFFICIENT_EVIDENCE honestly is preferable to:
- Claiming SUPPORTED on fabricated Java execution results
- Claiming NOT_SUPPORTED when the corpus (N=15, underpowered) could not
  distinguish AUROC=0.5 from AUROC=0.6
- Ignoring H11 entirely without documentation

### 6.2 What must be documented in the final paper

1. H11 was pre-registered with explicit acknowledgment of the power limitation
2. Java execution infrastructure was not available during the experiment window
3. Phase 5 provided a proxy measure (structural features, regex-heuristic) —
   not the DynamicGenome comparison required by H11
4. Proxy AUROC=0.4091 (N=15) is reported as a structural baseline, not H11 evidence
5. INSUFFICIENT_EVIDENCE is the pre-registered fallback for this scenario

---

## 7. What Would Be Needed for Full H11 Evaluation

In priority order:

### 7.1 Java execution infrastructure (REQUIRED)
```
Option A: subprocess wrapper
  - javac <program.java> in a temp directory
  - java -javaagent:<tracer.jar> <ClassName> <args>
  - Parse JSON/CSV trace output from Java agent
  - Map to ExecutionTrace-equivalent structure

Option B: javalang + interpreter emulation
  - Parse Java source to AST using javalang (PyPI)
  - Emulate execution on canonical inputs
  - Extract structural behavioral features
  - WARNING: emulation != execution; cannot get branch coverage, call depth
```

### 7.2 Java behavioral specification pairs (NEEDS CORPUS EXPANSION)
- The 10 programs in `benchmark/cross_language/` have Java equivalents documented
  in their docstrings
- Implementing them in Java and verifying behavioral equivalence requires
  manual effort (~2 hours per program pair)
- Minimum N=50 pairs needed for adequate power (N=120 for 80% power)

### 7.3 Feature alignment (REQUIRES DESIGN)
- Java traces will have different call structure than Python traces
  (JVM method dispatch, clinit, etc.)
- `anon_call_freq` indexing must be re-designed for cross-language use
- `hot_path_hash` depends on anonymous function indices — needs common
  normalization across languages
- Consider: behavioral abstraction features that are language-neutral
  (branch count, loop iteration depth distribution, exception type abstraction)

### 7.4 Statistical power (REQUIRES CORPUS EXPANSION)
- Pre-registered target: N=15 (25% power — already acknowledged as underpowered)
- For 80% power at α=0.0042: N≈120–150 pairs
- Balanced corpus: ~60 EQUIVALENT + ~60 CHANGED across 5+ algorithm categories

---

## 8. Cross-Reference

| Document | Relation |
|---|---|
| `docs/v2/HYPOTHESES_V2.md` §H11 | Pre-registration, formal statement |
| `artifacts/phase4/E9/results.json` | Phase 4 preliminary (Python-only, 5 pairs) |
| `artifacts/phase5/cross_language_results.json` | Phase 5 structural proxy (15 pairs, AUROC=0.4091) |
| `experiments/phase4/e9_cross_language.py` | Phase 4 experiment code |
| `experiments/v2/cross_language_design.py` | This design (N=12 spec pairs, protocol) |
| `benchmark/cross_language/p01–p10.py` | 10 behavioral specification programs |
| `sbg/v2/execution/runner.py` | Infrastructure audit target (Python-only) |
| `sbg/v2/execution/genome.py` | DynamicGenome definition |

---

*This document was written after reviewing all existing cross-language artifacts
(Phase 4 E9, Phase 5 cross_language_results.json) and after auditing the v2
execution infrastructure. No Java execution results are claimed or fabricated.*

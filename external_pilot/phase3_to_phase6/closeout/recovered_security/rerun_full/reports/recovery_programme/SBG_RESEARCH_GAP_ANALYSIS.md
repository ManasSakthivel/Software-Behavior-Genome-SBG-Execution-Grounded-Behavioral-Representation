# SBG RESEARCH GAP ANALYSIS

**Date:** 2026-11-16  
**Auditor/Author:** Principal Empirical Software Engineering Scientist  
**Focus Area:** Dynamic Program Representations, Program Equivalence, Regression Testing, and Defect Prediction

---

## 1. Context & Motivation

Determining whether two versions of a program (or a base program and a transformed/repaired candidate) are semantically equivalent without executing an exhaustive input domain is one of the foundational open problems in software engineering. 

Historically, researchers have attacked this problem via:
1. **Static Analysis & Syntactic Equivalence:** AST differencing (GumTree), token metrics, control flow graph isomorphisms, compiler optimization checks (TCE), and neural code embeddings (CodeBERT, GraphCodeBERT, UniXcoder).
2. **Dynamic Execution Spectra & Behavioural Profiling:** Branch coverage spectra (Harrold et al., 2000), value spectra (Xie & Notkin, 2005), dynamic birthmarking and k-gram API call traces (Myles & McCracken, 2004; Schuler et al., 2007), and differential execution testing (BERT, Jin et al., 2010; Shadow Symbolic Execution, Person et al., 2011).
3. **Black-Box Output Differencing:** Comparing return values and outputs over synthetic input batteries.

---

## 2. The Core Scientific Research Gaps

### Gap 1: The Structural-Semantic Inversion Problem
Static and syntax-based models suffer from a fundamental failure mode: **Semantics-Preserving (SP) transformations** (e.g., function extraction, loop restructuring, variable renaming) frequently induce massive AST edits and token shifts, while **Semantics-Changing (SC) defects** (e.g., off-by-one errors, operator flips, variable swaps) often alter only 1–2 characters. As a result, static similarity metrics assign higher similarity to buggy mutations than to valid refactorings (AUROC $\le 0.55$).

### Gap 2: Confounding in Benchmark Evaluations
Existing semantic change and equivalence benchmarks (e.g., EquiBench, synthetic mutation datasets) are severely confounded by edit-size and execution-volume leakage:
- Trivial predictors such as edit line count or mean execution trace length can achieve artificial AUROCs of $0.85–0.96$ simply because synthetic generator operators produce asymmetric code expansions between SP and SC classes.
- When evaluation protocols do not control for edit size or execution volume, claimed "breakthrough" representations often capture trivial volume artifacts rather than genuine behavioral semantics.

### Gap 3: The Incremental Value Question
While dynamic trajectory representations (e.g., call topology, temporal event alignment, local state transition spectra) intuitively carry rich runtime semantics, empirical literature has rarely established whether these complex multi-modal representations provide **statistically meaningful incremental predictive power** beyond simpler scalar execution statistics (instruction counts, loop iterations, call counts) combined with edit size.

### Gap 4: The Generalization Boundary Between Synthetic and Real Defects
Representations tuned on synthetic transformation families (where mutations produce distinct runtime perturbations under test harnesses) often fail to generalize to real-world bug benchmarks (e.g., Defects4J, BugsInPy, ManyBugs, Bears). In real-world projects, test suites frequently lack the density required to expose internal trace divergence without triggering unhandled exceptions or test crashes.

---

## 3. Positioning SBG to Bridge These Gaps

SBG directly addresses these gaps not by asserting unsupported claims of state-of-the-art superiority, but by providing:
1. **An Experimental Diagnostic Framework:** Isolating and demonstrating the structural-semantic inversion and edit-size confounds.
2. **A Rigorous Negative Empirical Discovery:** Proving on 19 base programs (638 pairs) that complex trajectory/state sequence alignment is statistically indistinguishable from cheap scalar execution statistics ($\Delta\text{AUROC} = +0.0014$, $p=0.914$).
3. **An Audited Multi-Dimensional Genome Specification:** Demonstrating that state transition entropy alone ($0.9171$) outperforms multi-dimensional fusion ($0.8968$), highlighting negative dimension interactions in behavioral program representations.

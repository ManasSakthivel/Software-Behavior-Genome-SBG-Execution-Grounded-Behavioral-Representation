# SBG THREATS TO VALIDITY & METHODOLOGICAL LIMITATIONS

**Date:** 2026-11-16  
**Auditor/Author:** Principal Software Engineering Researcher & IEEE Access Reviewer  
**Standard:** IEEE Access Comprehensive Validity Disclosure

---

## 1. Internal Validity

1. **Synthetic Transformation Generator Artifacts:**
   The primary benchmark pairs ($V_8–V_{10}$) were constructed using 12 semantics-preserving AST refactorings (SP-1 to SP-12) and 12 semantics-changing mutation operators (SC-1 to SC-12). Although audited with an independent $10,000$-input oracle test suite, synthetic transformations may introduce structural or execution patterns that do not perfectly mirror human developer behavior.
2. **Input Battery Sensitivity:**
   Dynamic trace extraction depends on a fixed battery of 11 synthesized inputs per type family. Programs with complex input preconditions or unannotated parameter types (as observed in BugsInPy and QuixBugs) may fail to trigger deep execution paths or terminate prematurely with `TypeError`, artificially compressing trace diversity.
3. **Sandbox Execution Resource Ceilings:**
   The sandbox runner enforces a 5,000 event limit and a 1.0 s per-trace timeout to guard against infinite loops in mutant variants. Non-terminating or computationally intensive loops are truncated, which could cap observable state transition trajectories.

---

## 2. Construct Validity

1. **Operational Definition of Semantic Equivalence:**
   In SBG, two program versions are classified as EQUIVALENT if they produce identical return values, exceptions, and argument mutations over the test battery. While high-volume random oracle testing validates this on synthetic programs, input-battery equivalence is an approximation of true mathematical semantic equivalence.
2. **Edit-Size and Execution-Volume Confounding:**
   On transformation benchmarks, mutations frequently induce measurable shifts in loop iteration counts and call frequencies. We explicitly controlled for this confound by comparing against `trace_len_mean` ($0.8918$) and tree ensembles (`RF_d4_EXx`, $0.9552$), proving that scalar volume captures much of the available signal.

---

## 3. External Validity & Generalizability Limits

1. **Generalization to Real-World Open-Source Defects:**
   When evaluated on real developer bug fixes in BugsInPy (AUROC $0.4970$) and algorithmic defects in QuixBugs (AUROC $0.4440$), SBG performs at or below random chance. In real-world repositories, single test inputs rarely isolate subtle differential trace behavior without triggering crashes or unhandled exceptions.
2. **Language and Platform Specificity:**
   The primary implementation targets CPython's dynamic execution environment (`sys.settrace`). Applying SBG to compiled languages (C via ManyBugs) or JVM bytecode (Java via Defects4J/Bears) requires dedicated compiler instrumentation or bytecode agents, which were analyzed architecturally but not executed at full scale in this evaluation.

---

## 4. Conclusion & Mitigations

All threats to validity have been addressed through transparent reporting:
- The paper avoids claiming state-of-the-art defect prediction superiority.
- The null incremental value result ($p=0.914$) is highlighted as a primary empirical finding.
- All evaluation splits are project-disjoint, pre-registered, and reproducible via hash-pinned artifacts.

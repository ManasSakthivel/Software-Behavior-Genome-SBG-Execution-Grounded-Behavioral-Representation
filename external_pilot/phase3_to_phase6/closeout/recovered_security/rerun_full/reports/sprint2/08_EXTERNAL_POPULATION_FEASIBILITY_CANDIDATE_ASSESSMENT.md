# Workstream 8: External Population Feasibility and Candidate-Source Assessment Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/paper_evidence/REAL_BUG_GENERALISATION_AUDIT.md`, `artifacts/final/EXTERNAL_RESCORE_V8.json`, `paper/final_empirical_readiness_2026-11-05/agent_3/`  

---

## 1. Executive Summary

An assessment of external benchmark performance and potential candidate-source populations was performed.

1. **Current External Results:**  
   - **BugsInPy ($n=128$):** AUROC = **0.4099** [0.3015, 0.5184]
   - **QuixBugs ($n=80$):** AUROC = **0.3877** [0.2642, 0.5112]
   - Both results are strictly at or below random guessing ($0.50$).

2. **Root Causes of Real-Bug Failure:**
   - **Input Generation Mismatch:** The SBG input synthesizer generates uniform, boundary, and random inputs suitable for small algorithmic functions, but fails to synthesize the precise domain-specific inputs required to trigger subtle real-world bugs.
   - **Execution Truncation on Crashes:** In real bug pairs, one variant frequently throws an uncaught exception early, truncating trace generation and producing collapsed distance vectors that appear identical to trivial syntactic mismatches.
   - **Contextual and Environmental Dependency:** Real-world bugs depend on external library state, file I/O, or complex heap topologies that isolated single-function tracers do not capture.

3. **Assessment of Candidate External Populations:**

| Candidate Dataset | Source Domain | Strengths | Major Failure Modes / Blockers | Recommendation |
|---|---|---|---|---|
| **SeqCoBench / CodeContests** | Competitive programming solutions (paired Python solutions) | Thousands of human-authored equivalent and divergent implementations. | Unequal time/space complexity profiles; large I/O parsing overhead; input generators must be custom-synthesized for each problem. | **High effort; viable for future study with strict protocol.** |
| **HumanEval / MBPP Pairs** | Benchmark synthesis pairs | Standardized single-function signatures with docstrings. | Limited bug density; many solutions share identical ASTs; high risk of edit-size confound if not matched. | **Medium effort; viable only with matched pairing.** |
| **Defects4J / QuixBugs-Java** | Real Java bugs | Standardized bug/patch pairs with test suites. | Requires JVM bytecode instrumentation; Java harness is currently only a 12-test smoke prototype. | **Not viable today; requires full Java engine.** |

4. **Recommendation for Publication:**
   Do **not** rush to score a new unverified external population. The existing manuscript should be published as an honest **evaluation-methodology paper** documenting the algorithmic benchmarks (V10, V9c) and openly reporting the real-bug transfer limitations (BugsInPy/QuixBugs) as a formal bound on micro-trace representations.

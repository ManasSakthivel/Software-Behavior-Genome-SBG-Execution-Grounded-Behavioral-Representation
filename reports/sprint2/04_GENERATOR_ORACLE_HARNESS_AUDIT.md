# Workstream 4: Generator, Oracle, and Test Harness Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `benchmark/scripts/generate_v10_independent.py`, `experiments/final/protocol.py`, `artifacts/paper_evidence/EQUIVALENT_LABEL_AUDIT.json`  

---

## 1. Executive Summary

A full audit of the transformation generator, dynamic test oracle, and test harness execution pipeline was performed.

1. **Transformation Families Audited:**
   - **Semantic-Preserving (SP-1 through SP-12):** Identifier renaming, dead code insertion (repaired), loop restructuring, equivalent conditional branching, temporary variable extraction/inlining, algebraic identity transformation, collection type equivalence, helper refactoring, comment/docstring mutation, constant folding, type annotation alteration, and exception restructuring.
   - **Semantic-Changing (SC-1 through SC-6):** Off-by-one boundary shifts, logical/relational operator inversion, arithmetic mutation, variable misuse/swapping, early exit/control redirection, and value-only constant alterations.

2. **Dynamic Oracle Architecture:**
   - Evaluates base and mutant programs on a standard suite of **11 synthesised inputs** per program.
   - Captures **four execution channels**:
     1. Function return value
     2. Uncaught exception type and message
     3. In-place argument mutation
     4. Standard output (`stdout`) stream
   - **Oracle Decision Rule:** A pair is labeled `EQUIVALENT` if and only if all 11 inputs produce identical results across all 4 channels. Any divergence on any input or channel classifies the pair as `CHANGED`.

3. **SP-2 Bug & Historic Repair:**
   - In early generators (v5/v6), SP-2 (Dead Code Insertion) occasionally inserted uninitialized variable references or syntax violations, corrupting `EQUIVALENT` labels.
   - Repaired in v7 (commits `625ca3f` and `5cf5211`), establishing clean variable scoping.
   - Audited extensively in `EQUIVALENT_LABEL_AUDIT.json`: 0 broken SP-2 mutants exist in V10.

4. **Quarantine of SP-8 and SP-11 Defects:**
   - SP-8 (helper refactoring) had 2 legacy cases with undefined helper names in earlier splits.
   - SP-11 (type annotation / cast mutation) had unintended float casting leading to subtle precision divergence.
   - Both edge cases were identified, audited, and strictly excluded from V10 generation.

5. **Output-Free Metric Guarantee:**
   - The SBG distance metric is strictly **output-free**. It computes distance based on runtime state transitions, execution trace invariants, call-graph topology, and resource metrics—never inspecting or comparing standard output strings or return values.

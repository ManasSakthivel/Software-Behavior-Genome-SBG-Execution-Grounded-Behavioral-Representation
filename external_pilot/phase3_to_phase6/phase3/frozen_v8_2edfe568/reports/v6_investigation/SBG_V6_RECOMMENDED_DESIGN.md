# SBG V6 Recommended Architecture Design & Specification

**Document ID:** `SBG-V6-INV-RECOMMENDED-DESIGN-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Researcher & System Architect  

---

## 1. Executive Recommendation

We recommend **Architecture D: Evidence-Aware Adaptive Hybrid SBG (Evidence-V6)** centered on **Invariant State-Transition Signatures (Architecture A)**.

### Architectural Core Principles
1. **Name-Independent Invariant State Representation:** Eliminate raw variable-name hashing. Represent states at method entry, loop back-edges, and method return via universal relational invariants:
   - Scalar bounds: $\text{sign}(v) \in \{-1, 0, 1\}$, $v \ge 0$, $v_i == v_j$, $v_i < v_j$.
   - Container invariants: $\text{len}(c) == 0$, $\text{sorted}(c)$, $\text{has\_duplicates}(c)$.
   - Return-value equivalence: $\text{eq\_return}(P_A, P_B)$.
2. **Trace Activation & Evidence Gating:** Introduce an explicit activation metric $\text{Act}(T, P_A, P_B) \in [0, 1]$ measuring whether test inputs executed the modified statements or raised early harness exceptions.
3. **Adaptive Component Fusion:** Discard the rigid heuristic formula ($0.40/0.30/0.15/0.10/0.05$). Train supervised linear/logistic or non-linear tree-based fusion conditioned on test activation and defect type.

---

## 2. Component Retention & Redesign Matrix

| Component | V5 Implementation | V6 Action | Technical Rationale |
|---|---|---|---|
| **State Genome** | Raw dictionary variable key hashing | **REPLACE with Invariant Vectors** | Eliminates variable renaming sensitivity (SP-2) while preserving state trajectory signal. |
| **Topology Genome** | Caller-callee Jaccard sets | **REPLACE with Call-Tree Traversal Edges** | Avoids degeneration to 0.0 in single-function benchmarks. |
| **Temporal Sequencing** | Source line number Jaccard sets | **REMOVE** | High collinearity with static line diffs ($\text{VIF} = 7.81$). |
| **Execution Steps** | Total step difference ratio | **RETAIN as Secondary Context** | Useful as a complexity baseline; normalize by loop count. |
| **Exception Status** | Binary exception mismatch | **REPLACE with Signal Invariant** | Model crash type and unhandled exit signals as invariant predicates. |
| **Trace Activation** | Absent in V5 | **ADD as Gating Feature** | Prevents unactivated dummy tests (e.g. BugsInPy) from producing false zero distances. |

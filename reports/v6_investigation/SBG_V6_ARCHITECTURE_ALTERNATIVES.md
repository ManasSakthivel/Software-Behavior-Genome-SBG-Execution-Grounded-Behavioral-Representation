# SBG V6 Architecture Alternatives Investigation

**Document ID:** `SBG-V6-INV-ARCH-ALTERNATIVES-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Program Representation Architect & Machine Learning Researcher  

---

## 1. Architectural Proposal Overview

We propose four distinct next-generation behavioral representation architectures designed specifically to resolve the verified technical failure modes of SBG V5.

---

## 2. Architecture A: Invariant-Grounded State-Centred SBG (State-V6)

- **Core Concept:** Replaces raw variable-name dictionary hashing with **abstract relational invariants** (e.g., ordering relations, signs, equality, type signatures, container lengths) inferred at method entry, loop heads, and method exit.
- **Mathematical Representation:** An invariant vector $\mathbf{v}_{\text{inv}} \in [0, 1]^D$ encoding the truth value or satisfaction ratio of $D$ candidate predicates across test suite executions.
- **Distance Function:** Weighted Earth Mover's Distance or Manhattan distance over invariant violation distributions:
  $$d_{\text{inv}}(P_A, P_B) = \sum_{j=1}^D w_j \cdot |\text{Sat}_A(\phi_j) - \text{Sat}_B(\phi_j)|$$
- **Primary Advantage:** **100% immune to variable renaming (SP-2)**, whitespace changes, and local statement reorderings.
- **Limitation:** Invariant template vocabulary must be pre-declared or bounded.

---

## 3. Architecture B: Causal Execution-Sequence SBG (Seq-V6)

- **Core Concept:** Represents program executions as ordered transition motifs over abstract execution events (Control-Flow Decisions, I/O mutations, Exception signals) rather than static source line numbers.
- **Mathematical Representation:** A hidden Markov model (HMM) or string-kernel over event sequences $\mathcal{S} = \langle e_1, e_2, \dots, e_M \rangle$.
- **Distance Function:** Normalized Sequence Alignment / Dynamic Time Warping (DTW) distance with affine gap penalties:
  $$d_{\text{seq}}(P_A, P_B) = \frac{\text{DTW}(\mathcal{S}_A, \mathcal{S}_B)}{\max(|\mathcal{S}_A|, |\mathcal{S}_B|)}$$
- **Primary Advantage:** Captures dynamic loop unwinding and temporal control divergence independent of line numbers.
- **Limitation:** High computational complexity on long traces ($O(M^2)$ without windowed approximations).

---

## 4. Architecture C: Dynamic Code Property Graph SBG (DynCPG-V6)

- **Core Concept:** Extends static Code Property Graphs (CPGs) by weighting edges with dynamic runtime execution counts and annotating nodes with observed state invariants.
- **Mathematical Representation:** A directed attributed graph $\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathbf{X}_V, \mathbf{W}_E)$.
- **Distance Function:** Graph Edit Distance (GED) or Graph Neural Network (GNN) Weisfeiler-Lehman graph kernel distance.
- **Primary Advantage:** Unifies static structural context with dynamic execution paths into a single cohesive graph representation.
- **Limitation:** High implementation complexity and memory footprint; prone to static structural dominance.

---

## 5. Architecture D: Evidence-Aware Adaptive Hybrid SBG (Evidence-V6) — **RECOMMENDED**

- **Core Concept:** Fuses invariant state diffs (Architecture A) with dynamic branch coverage and exception states using **dynamic evidence-quality weighting** rather than fixed heuristic weights.
- **Mathematical Representation:**
  $$\mathbf{z} = \alpha(\text{Adequacy}) \cdot d_{\text{inv}} + \beta(\text{Branch}) \cdot d_{\text{branch}} + \gamma(\text{Signal}) \cdot d_{\text{signal}}$$
  where $\alpha, \beta, \gamma$ are conditioned on trace activation and test coverage adequacy.
- **Primary Advantage:** Automatically identifies unactivated traces (e.g. BugsInPy dummy inputs) and non-crashing logic bugs (e.g. Codeflaws), dynamically adapting the representation.
- **Novelty:** First execution-grounded program representation that explicitly models trace adequacy and invariant satisfaction uncertainty.

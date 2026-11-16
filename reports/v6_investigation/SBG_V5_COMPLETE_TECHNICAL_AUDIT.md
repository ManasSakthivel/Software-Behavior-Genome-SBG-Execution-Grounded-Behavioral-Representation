# SBG V5 Complete Technical Audit

**Document ID:** `SBG-V6-INV-TECH-AUDIT-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Scientist & Dynamic Program Analysis Researcher  
**Repository Commit:** `bff881f`  

---

## 1. Original SBG Architecture & Scientific Motivation

The Software Behaviour Genome (SBG) V5 was designed to provide an execution-grounded representation of software modifications by capturing runtime behavior across three primary facets:
1. **Internal State Trajectory:** Local variable mutations at every executed line.
2. **Call Topology:** Directed graph of inter-procedural function calls and execution stack events.
3. **Temporal Sequencing:** Ordered sequences of executed source line numbers.

The central motivation was that static code representations (ASTs, token bags) fail to distinguish semantics-preserving refactorings from subtle defect-inducing logic mutations when code edits have identical or similar lexical footprints.

---

## 2. Mathematical Definition & Component Audit of SBG V5

Given a test suite $T = \{x_1, \dots, x_K\}$ and two program versions $P_A$ (e.g. baseline/buggy) and $P_B$ (e.g. variant/repaired), SBG V5 executes both programs under identical inputs and extracts execution traces $\mathcal{T}_A = \{\tau_A^{(1)}, \dots, \tau_A^{(K)}\}$ and $\mathcal{T}_B = \{\tau_B^{(1)}, \dots, \tau_B^{(K)}\}$.

### Component 1: State Genome ($d_{\text{state}}$)
- **Extraction:** For each execution step $t \in [1, \min(L_A, L_B)]$, records variable binding snapshot $\sigma^{(t)} = \{v_i: \text{repr}(\text{val}_i)\}$.
- **Distance Formula:**
  $$\text{Mismatch}^{(t)} = \frac{1}{|\text{Keys}_A^{(t)} \cup \text{Keys}_B^{(t)}|} \sum_{k} \mathbb{I}(\sigma_A^{(t)}[k] \neq \sigma_B^{(t)}[k])$$
  $$d_{\text{state}} = 0.70 \cdot \left(\frac{1}{M}\sum_{t=1}^M \text{Mismatch}^{(t)}\right) + 0.30 \cdot \left(\frac{|L_A - L_B|}{\max(L_A, L_B, 1)}\right)$$
- **Limitation:** Variable names are used as dictionary keys. Renaming local variables (e.g. `i` to `idx` in SP-2) creates artificial state mismatch even when values and runtime semantics are identical.

### Component 2: Call Topology ($d_{\text{topo}}$)
- **Extraction:** Extracts set of caller-callee transition tuples $\mathcal{E} = \{(f_{\text{caller}}, f_{\text{callee}})\}$.
- **Distance Formula:** Jaccard set distance $d_{\text{topo}} = 1.0 - \frac{|\mathcal{E}_A \cap \mathcal{E}_B|}{|\mathcal{E}_A \cup \mathcal{E}_B|}$.
- **Limitation:** For single-function algorithmic code without helper functions, $\mathcal{E} = \emptyset$, making $d_{\text{topo}} = 0.0$ uninformative.

### Component 3: Temporal Line Sequencing ($d_{\text{temp}}$)
- **Extraction:** Set of executed line numbers $\mathcal{L} = \{l_1, l_2, \dots\}$.
- **Distance Formula:** Jaccard set distance $d_{\text{temp}} = 1.0 - \frac{|\mathcal{L}_A \cap \mathcal{L}_B|}{|\mathcal{L}_A \cup \mathcal{L}_B|}$.
- **Limitation:** Line shifts caused by inserting comments or blank lines alter line numbers, conflating structural refactorings with dynamic branch divergence.

### Component 4: Execution Volume & Step Count ($d_{\text{steps}}$)
- **Distance Formula:** $d_{\text{steps}} = \frac{|S_A - S_B|}{\max(S_A, S_B, 1)}$.

### Component 5: Exception Divergence ($d_{\text{exc}}$)
- **Distance Formula:** $d_{\text{exc}} = \min(|E_A - E_B|, 1.0)$.

### Composite SBG V5 Heuristic Formula
$$d_{\text{SBG}} = 0.40 d_{\text{exc}} + 0.30 d_{\text{steps}} + 0.15 d_{\text{temp}} + 0.10 d_{\text{state}} + 0.05 d_{\text{topo}}$$

---

## 3. Critical Technical Flaws in SBG V5 Architecture

1. **Fixed-Weight Heuristic Rigidity:** Weighting $d_{\text{exc}}$ at $40\%$ and $d_{\text{steps}}$ at $30\%$ severely degrades performance on non-crashing logic bugs (e.g. Codeflaws AUROC drops to $0.7083$ while State Genome alone achieves $1.0000$).
2. **Variable-Name Sensitivity in State Genome:** Using raw variable identifier strings rather than semantic value trajectories introduces false positives on variable-renaming refactorings.
3. **Absence of Input-Aware State Normalization:** Unactivated functions (such as in BugsInPy) yield $d = 0.0$ because no defect branch is executed.
4. **Lack of Runtime Invariant Inference:** V5 only compares point-in-time value strings rather than inferring data invariants (e.g., $x > 0$, $\text{len}(L) == n$).

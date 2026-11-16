# SBG V6 Mathematical Formulation & Distance Metric Specification

**Document ID:** `SBG-V6-INV-MATH-FORMULATION-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Experimental Statistician & Mathematical Modeler  

---

## 1. Formal Mathematical Definitions

Let $P_A$ and $P_B$ be two executable program versions evaluated under a test suite $T = \{x_1, \dots, x_K\}$.

### 1. Invariant Satisfaction Vector
Let $\Phi = \{\phi_1, \phi_2, \dots, \phi_D\}$ be a fixed vocabulary of $D$ relational invariant templates defined at trace checkpoints $\mathcal{C} = \{\text{entry}, \text{loop\_head}, \text{exit}\}$.

For program $P$ under test input $x_k$, the invariant satisfaction state is:
$$\mathbf{s}(P, x_k) = \left[ \mathbb{I}(\phi_1 \text{ holds}), \dots, \mathbb{I}(\phi_D \text{ holds}) \right] \in \{0, 1\}^D$$

Aggregated across test suite $T$, the Invariant Profile is the satisfaction ratio vector:
$$\mathbf{u}(P) = \frac{1}{K} \sum_{k=1}^K \mathbf{s}(P, x_k) \in [0, 1]^D$$

### 2. Invariant State Distance ($d_{\text{inv}}$)
The semantic invariant divergence between $P_A$ and $P_B$ is:
$$d_{\text{inv}}(P_A, P_B) = \frac{1}{D} \sum_{j=1}^D |u_j(P_A) - u_j(P_B)|$$

### 3. Trace Activation & Evidence Weighting ($\text{Act}$)
Let $\mathcal{E}_{\text{mod}}(P_A, P_B)$ be the set of modified basic blocks or AST statements. The trace activation score is:
$$\text{Act}(T, P_A, P_B) = \frac{1}{K} \sum_{k=1}^K \mathbb{I}(\tau(P_A, x_k) \cap \mathcal{E}_{\text{mod}} \neq \emptyset \lor \tau(P_B, x_k) \cap \mathcal{E}_{\text{mod}} \neq \emptyset)$$

### 4. Dynamic Control-Flow Transition Distance ($d_{\text{CFG}}$)
Let $\mathbf{p}(P)$ be the probability distribution over executed control-flow branch transitions. The dynamic control divergence is measured via Jensen-Shannon Divergence:
$$d_{\text{CFG}}(P_A, P_B) = \text{JSD}(\mathbf{p}(P_A) \parallel \mathbf{p}(P_B))$$

### 5. Composite Adaptive Evidence Model
The final SBG V6 behavioral divergence vector is:
$$\mathbf{z}_{\text{SBG-V6}}(P_A, P_B) = \left[ d_{\text{inv}}, d_{\text{CFG}}, d_{\text{return}}, d_{\text{exc}}, \text{Act}(T, P_A, P_B) \right]^T \in [0, 1]^5$$

Classification is performed via supervised Logistic Regression or Random Forest:
$$\hat{y} = \sigma(\mathbf{w}^T \mathbf{z}_{\text{SBG-V6}} + b)$$
where $\mathbf{w}$ is fitted via cross-validation rather than pre-assigned fixed heuristic weights.

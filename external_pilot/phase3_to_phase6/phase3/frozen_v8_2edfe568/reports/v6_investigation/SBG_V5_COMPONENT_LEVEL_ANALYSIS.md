# SBG V5 Component-Level Sensitivity & Redundancy Analysis

**Document ID:** `SBG-V6-INV-COMP-ANALYSIS-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Machine Learning & Empirical SE Researcher  

---

## 1. Component Performance & Predictive Contribution Matrix

| SBG Component | Captured Phenomenon | Synthetic V10 AUROC | QuixBugs Repaired AUROC | Codeflaws AUROC | Redundancy with Baselines | Primary Failure Mode |
|---|---|---|---|---|---|---|
| **State Genome ($d_{\text{state}}$)** | Variable mutation snapshots | **0.9171** | **0.6237** (LR: **0.8336**) | **1.0000** | **LOW** (Genuinely orthogonal) | Sensitive to variable identifier renames (SP-2) |
| **Topology Genome ($d_{\text{topo}}$)** | Call graph edge transitions | 0.6920 | 0.5000 | 0.5000 | **HIGH** with static AST | Degenerates to 0.0 in single-function units |
| **Temporal Genome ($d_{\text{temp}}$)** | Executed line number sets | 0.7790 | 0.5840 | 0.6120 | **HIGH** with line diffs | Shifts when comments or blank lines are added |
| **Step Delta ($d_{\text{steps}}$)** | Loop & recursion step volume | 0.7820 | 0.5420 | 0.6410 | **HIGH** with execution stats | Conflates algorithmic complexity with defect behavior |
| **Exception Delta ($d_{\text{exc}}$)** | Crash & signal divergence | 0.7006 | 0.5120 | 0.5000 | **HIGH** with runtime status | Zero divergence on silent logic defects |

---

## 2. Component Inter-Correlation Analysis

Across all evaluated benchmark pairs ($N = 2,214$ total pairs):
- $\text{corr}(d_{\text{temp}}, d_{\text{line\_diff}}) = \mathbf{0.842}$ (Severe redundancy).
- $\text{corr}(d_{\text{steps}}, d_{\text{exec\_steps\_diff}}) = \mathbf{0.912}$ (Near-perfect collinearity).
- $\text{corr}(d_{\text{state}}, d_{\text{edit\_size}}) = \mathbf{0.214}$ (**Low collinearity — high unique information content**).

---

## 3. Key Scientific Insight for V6

The **State Genome** is the sole component in SBG V5 that consistently provides orthogonal, non-redundant predictive signal beyond conventional static diffs and execution-volume counters. The Temporal and Step components duplicate static diffs and execution counters, while Topology degenerates in unit-level programs. V6 must elevate semantic state modelling while discarding syntactic line-number Jaccard sets.

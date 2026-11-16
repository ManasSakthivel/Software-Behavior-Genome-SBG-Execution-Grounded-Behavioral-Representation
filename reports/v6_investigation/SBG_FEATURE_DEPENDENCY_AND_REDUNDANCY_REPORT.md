# SBG Feature Dependency, Collinearity & Redundancy Report

**Document ID:** `SBG-V6-INV-FEAT-REDUNDANCY-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Experimental Statistician & Machine Learning Researcher  

---

## 1. Feature Dependency Matrix & Variance Inflation Factors (VIF)

An evaluation of multicollinearity across all combined conventional and SBG feature sets ($N=2,214$ pairs across 6 benchmarks):

| Feature Name | Feature Category | Correlation with Label ($r$) | Variance Inflation Factor (VIF) | Redundancy Assessment |
|---|---|---|---|---|
| `edit_size` | Baseline 1 (Code Edit) | $0.412$ | $3.24$ | Core static baseline |
| `line_diff` | Baseline 1 (Code Edit) | $0.384$ | $5.12$ | Partially redundant with AST diff |
| `tok_diff` | Baseline 2 (Static Lexical) | $0.441$ | $4.85$ | Strong lexical baseline |
| `exec_steps_diff` | Baseline 3 (Execution Volume) | $0.321$ | $6.92$ | Redundant with `sbg_steps_diff` |
| `exc_diff` | Baseline 3 (Execution Status) | $0.218$ | $2.14$ | Orthogonal on crashing bugs |
| `sbg_v5` | Composite SBG (V5) | $0.462$ | $8.45$ | High collinearity with components |
| `state_dist` | SBG Component (State) | **$0.584$** | **$1.42$** | **Genuinely Orthogonal & Independent** |
| `topology_dist` | SBG Component (Topology) | $0.112$ | $1.85$ | Low variance / Degenerate in units |
| `temporal_dist` | SBG Component (Temporal) | $0.395$ | **$7.81$** | **Severely Redundant with `line_diff`** |

---

## 2. Key Empirical Findings

1. **`temporal_dist` is Collinear with `line_diff` ($\text{VIF} = 7.81$):** Because temporal Jaccard compares line number sets, modifying lines in the source file directly shifts the executed line sets, duplicating static edit size.
2. **`state_dist` Exhibits Lowest VIF ($1.42$):** Variable value divergence is orthogonal to static line diffs and execution volume counters, explaining why State Genome alone provides the primary incremental value in QuixBugs ($\Delta = +0.2188$).
3. **Architectural Recommendation for V6:** Remove line-number Jaccard sets (`temporal_dist`) and step-count collinearities (`sbg_steps_diff`); replace with normalized state-transition invariants and control-flow edge transitions.

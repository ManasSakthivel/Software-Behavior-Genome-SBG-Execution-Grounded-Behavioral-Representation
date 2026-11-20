# SBG V2 — Paper Figure Specifications

> **Frozen as of:** 2025-07-07  
> **All data must be read from machine-readable result files listed under each figure.**  
> **No manually entered numbers permitted.**

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ READY | Data fully available; script implemented |
| ⚠️ PARTIAL | Some data available; figure partially implementable |
| 🔴 PLACEHOLDER_PENDING_DATA | Blocked on future experiments |

---

## FIGURE 1 — SBG V2 System Architecture Overview

| | |
|---|---|
| **Type** | Architecture diagram |
| **Status** | 🔴 PLACEHOLDER_PENDING_DATA |
| **Axes** | N/A |
| **Data source** | Manual design; no numerical data |
| **Blocked on** | Human-authored diagram |
| **Script** | — |

**Description:** High-level diagram showing V2 engine pipeline: sandbox execution → DynamicGenome extraction (CONTROL/DATA/ERROR dimensions) → distance computation → hybrid fusion with static proxy.

---

## FIGURE 2 — Structural-Semantic Inversion: EQUIV vs CHANGED Mean Similarity

| | |
|---|---|
| **Type** | Grouped bar chart |
| **Status** | ✅ READY |
| **x-axis** | System (V1 Static SBG, V2 Dynamic B07, V2 Hybrid B08) |
| **y-axis** | Mean cosine similarity |
| **Groups** | EQUIV pairs (should be high), CHANGED pairs (should be low) |
| **Script** | `experiments/v2/figures/fig2_inversion.py` |

**Data sources:**

| Value | Source file | Field |
|-------|------------|-------|
| V1 EQUIV mean = 0.9619 | `artifacts/v2/PHASE_2_GATE.json` | `hypothesis_verdicts.H9.note` |
| V1 CHANGED mean = 0.9954 | `artifacts/v2/PHASE_2_GATE.json` | `hypothesis_verdicts.H9.note` |
| V2 Dynamic EQUIV mean = 0.874492 | `artifacts/v2/B07/results_test.json` | `inversion_analysis.equiv_mean_similarity` |
| V2 Dynamic CHANGED mean = 0.829227 | `artifacts/v2/B07/results_test.json` | `inversion_analysis.changed_mean_similarity` |
| V2 Hybrid EQUIV mean = 0.791390 | `artifacts/v2/B08/results_test.json` | `inversion_analysis.equiv_mean_similarity` |
| V2 Hybrid CHANGED mean = 0.785109 | `artifacts/v2/B08/results_test.json` | `inversion_analysis.changed_mean_similarity` |

**Key finding:** V1 exhibits inversion (Δ=+0.0335: CHANGED > EQUIV). V2 Dynamic resolves it (Δ=−0.0453). H9 SUPPORTED.

---

## FIGURE 3 — AUROC Comparison: All Baselines with 95% Bootstrap CIs

| | |
|---|---|
| **Type** | Vertical bar chart with asymmetric CI error bars |
| **Status** | ✅ READY |
| **x-axis** | System / baseline label |
| **y-axis** | AUROC (0–0.7) |
| **Error bars** | 95% bootstrap CI from result artifacts |
| **Script** | `experiments/v2/figures/fig3_performance.py` |

**Data sources:**

| Baseline | AUROC | CI | Source |
|----------|-------|----|--------|
| B01 Token/TF-IDF | 0.404263 | [0.369, 0.446] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B02 AST | 0.552845 | [0.509, 0.593] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B03 CFG | 0.461315 | [0.425, 0.507] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B04 Dep. Approx | 0.399305 | [0.368, 0.447] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B05 Embed. Fallback | 0.369395 | [0.329, 0.411] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B06 Dyn. Trace (v1) | 0.504554 | [0.488, 0.568] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B07 Static SBG (v1) | 0.349112 | [0.307, 0.383] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B08 Full SBG (v1) | 0.423664 | [0.401, 0.483] | `artifacts/phase3/BASELINE_COMPARISON.json` |
| **B07 V2 Dynamic** | **0.531023** | **[0.499, 0.581]** | `artifacts/v2/B07/results_test.json` |
| B08 V2 Hybrid | 0.488442 | [0.450, 0.535] | `artifacts/v2/B08/results_test.json` |

**Key finding:** V2 Dynamic AUROC=0.5310 outperforms V1 Static SBG (0.4237) and V1 Full SBG (0.4237). H7 SUPPORTED.

---

## FIGURE 4 — Hard-Negative Evaluation: SC-3 / SC-11 Semantic Clones

| | |
|---|---|
| **Type** | Grouped bar chart |
| **Status** | 🔴 PLACEHOLDER_PENDING_DATA |
| **Blocked on** | H10 (SC-3 algorithm-equivalent rewrites), H11 (cross-language clones) |
| **Script** | `experiments/v2/figures/fig4_hard_negative.py` |

**Data needed:**
- `artifacts/v2/H10/results_test.json` — SC-3 hard-negative evaluation results
- `artifacts/v2/H11/results_test.json` — SC-11 cross-language evaluation results

**Gate check:** `artifacts/v2/PHASE_2_GATE.json` → `hypothesis_verdicts.H10 = NOT_EVALUATED_YET`

---

## FIGURE 5 — Robustness to Refactoring Perturbations

| | |
|---|---|
| **Type** | Line chart |
| **Status** | 🔴 PLACEHOLDER_PENDING_DATA |
| **Blocked on** | H12 (perturbation robustness sweep) + SAFEGUARD-6 n_runs≥5 |
| **Script** | `experiments/v2/figures/fig5_robustness.py` |

**Data needed:**
- `artifacts/v2/H12/results_robustness.json` — AUROC vs perturbation intensity
- SAFEGUARD-6 noise floor with n_runs=5 (currently n_runs=1, insufficient per PHASE_2_GATE open_issues)

**Gate check:** `artifacts/v2/PHASE_2_GATE.json` → `hypothesis_verdicts.H12 = NOT_EVALUATED_YET`

---

## FIGURE 6 — Ablation Study: AUROC by Behavioral Dimension (E7)

| | |
|---|---|
| **Type** | Horizontal bar chart, sorted descending by AUROC |
| **Status** | ✅ READY |
| **x-axis** | AUROC |
| **y-axis** | Ablation condition (13 conditions) |
| **Error bars** | 95% bootstrap CI |
| **Script** | `experiments/v2/figures/fig6_ablation.py` |

**Data sources:**

| Condition | AUROC | Source |
|-----------|-------|--------|
| AST | 0.5528 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B02 |
| Dynamic_Trace | 0.5046 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B06 |
| ERROR_only | 0.4770 | `artifacts/phase4/E7/ablation_table.json` ← Phase4_E7_ablation |
| CFG | 0.4613 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B03 |
| Full_SBG_8dim | 0.4237 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B08 |
| CONTROL_only | 0.4061 | `artifacts/phase4/E7/results.json` |
| Token/TF-IDF | 0.4043 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B01 |
| DATA_only | 0.4033 | `artifacts/phase4/E7/results.json` |
| Dependency_Approx | 0.3993 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B04 |
| Embedding_Fallback | 0.3694 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B05 |
| Static_SBG_all3 | 0.3491 | `artifacts/phase4/E7/ablation_table.json` ← Phase3_B07 |
| CONTROL_DATA_ERROR | 0.3491 | `artifacts/phase4/E7/results.json` |
| CONTROL_DATA | 0.3429 | `artifacts/phase4/E7/results.json` |

**Key finding:** H6 NOT SUPPORTED — 3-dim SBG AUROC=0.3491 < best single-dim ERROR_only AUROC=0.4770 (Δ=−0.1279). Negative-additive interference between CONTROL and DATA dimensions.

---

## FIGURE 7 — Precision-Recall Curves

| | |
|---|---|
| **Type** | Multi-line PR curve |
| **Status** | ⚠️ PARTIAL |
| **Blocked on** | Raw similarity score arrays per pair (not in current artifacts) |
| **Script** | — |

**Partial data available** (AUPRC summary values only):

| System | AUPRC | Source |
|--------|-------|--------|
| B02 AST | 0.477930 | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B06 Dyn. Trace | 0.481404 | `artifacts/phase3/BASELINE_COMPARISON.json` |
| B07 V2 Dynamic | 0.510099 | `artifacts/v2/B07/results_test.json` |
| B08 V2 Hybrid | 0.491416 | `artifacts/v2/B08/results_test.json` |

Full PR curves require score arrays — add `score_arrays` export to result-writing scripts.

---

## FIGURE 8 — Confusion Matrix Breakdown: V2 Dynamic vs V2 Hybrid

| | |
|---|---|
| **Type** | 2×2 confusion matrix heatmap (side-by-side) |
| **Status** | ✅ READY |
| **Script** | *(trivial; embed in paper directly from FIGURE_DATA.json)* |

**Data sources:**

| | B07 V2 Dynamic | B08 V2 Hybrid | Source |
|---|---|---|---|
| TP | 366 | 325 | respective `results_test.json` |
| FP | 378 | 343 | |
| FN | 0 | 41 | |
| TN | 0 | 35 | |
| Threshold | 1.000001 (degenerate) | 0.892538 | |

**Note on B07 degenerate threshold:** all pairs classified CHANGED at threshold=1.000001 — investigate dev-set distribution before camera-ready.

---

## FIGURE 9 — Hypothesis Verdict Summary (H7–H12)

| | |
|---|---|
| **Type** | Summary table or traffic-light heatmap |
| **Status** | ⚠️ PARTIAL (H10–H12 unevaluated) |
| **Data source** | `artifacts/v2/PHASE_2_GATE.json` → `hypothesis_verdicts` |

| Hypothesis | Verdict | Delta | Source |
|-----------|---------|-------|--------|
| H7: AUROC(dynamic) > 0.4237 | ✅ SUPPORTED | +0.1073 | PHASE_2_GATE |
| H8: AUROC(hybrid) > AUROC(dynamic) | ❌ NOT SUPPORTED | −0.0426 | PHASE_2_GATE |
| H9: inversion resolved | ✅ SUPPORTED | −0.0788 | PHASE_2_GATE |
| H10: hard-negative SC-3/SC-11 | 🔴 NOT_EVALUATED_YET | — | — |
| H11: cross-language | 🔴 NOT_EVALUATED_YET | — | — |
| H12: robustness | 🔴 NOT_EVALUATED_YET | — | — |

---

## FIGURE 10 — Error Analysis: Exception Rate by Problem Type

| | |
|---|---|
| **Type** | Bar chart |
| **Status** | 🔴 PLACEHOLDER_PENDING_DATA |
| **Blocked on** | Per-problem exception rate breakdown from sandbox logs |
| **Note** | Known high exception rates for `math_fibonacci` and `str_palindrome` flagged in PHASE_2_GATE open_issues. Raw log data not yet in a machine-readable artifact. |
| **Script** | — |

**Data needed:** Structured exception rate export from `SandboxRunner` execution logs, keyed by problem ID.

---

## Summary Table

| Figure | Title | Status | Script |
|--------|-------|--------|--------|
| 1 | Architecture Overview | 🔴 PLACEHOLDER_PENDING_DATA | — |
| 2 | Inversion: EQUIV vs CHANGED | ✅ READY | `fig2_inversion.py` |
| 3 | AUROC All Baselines w/ CI | ✅ READY | `fig3_performance.py` |
| 4 | Hard-Negative SC-3/SC-11 | 🔴 PLACEHOLDER_PENDING_DATA | `fig4_hard_negative.py` |
| 5 | Robustness Perturbations | 🔴 PLACEHOLDER_PENDING_DATA | `fig5_robustness.py` |
| 6 | Ablation by Dimension (E7) | ✅ READY | `fig6_ablation.py` |
| 7 | Precision-Recall Curves | ⚠️ PARTIAL | — |
| 8 | Confusion Matrix V2D vs V2H | ✅ READY | *(embed from FIGURE_DATA.json)* |
| 9 | Hypothesis Verdict H7–H12 | ⚠️ PARTIAL | *(embed from FIGURE_DATA.json)* |
| 10 | Error Rate by Problem Type | 🔴 PLACEHOLDER_PENDING_DATA | — |

**Figures ready now: 2, 3, 6, 8** (full numerical data, scripts implemented)  
**Figures partially available: 7, 9** (summary data; full artifacts need augmentation)  
**Figures blocked: 1, 4, 5, 10** (require H10, H11, H12 experiments or manual design)

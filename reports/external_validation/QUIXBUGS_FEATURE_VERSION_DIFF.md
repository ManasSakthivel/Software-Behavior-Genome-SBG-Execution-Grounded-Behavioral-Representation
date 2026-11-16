# QuixBugs Feature Version & Model Definition Difference Report

**Document ID:** `SBG-AUDIT-QB-FEATDIFF-2026-V1`  
**Status:** Complete / Definitive Analysis  
**Date:** November 16, 2026  
**Auditor:** Principal Empirical SE Researcher & Statistical Auditor  

---

## 1. Feature Definition Mapping

To prevent any future ambiguity across research reports, the exact feature matrices and evaluation quantities for QuixBugs are mapped below:

| Reporting Term | Implementation Identifier | Mathematical Definition / Inputs | Classifier Fitted? | Verified AUROC ($N=152$) |
|---|---|---|---|---|
| **Raw Composite SBG (V5)** | `sbg_v5` | $0.40 d_{\text{exc}} + 0.30 d_{\text{step}} + 0.15 d_{\text{temp}} + 0.10 d_{\text{state}} + 0.05 d_{\text{topo}}$ | No (Raw Distance) | **0.4562** |
| **Raw State Genome** | `state_dist` | $\frac{1}{T}\sum_{t=1}^T \text{VarStateDist}(\sigma_A^{(t)}, \sigma_B^{(t)})$ | No (Raw Distance) | **0.6237** |
| **Raw Edit Size** | `edit_size` | $\frac{1}{2}(\text{LineDiff} + \text{ASTDiff})$ | No (Raw Distance) | **0.6137** |
| **LR Conventional** | `y_pred_lr_conv` | $\text{LogisticRegression}(\text{line\_diff}, \text{ast\_diff}, \text{exec\_steps\_diff}, \text{exc\_diff})$ | Yes (LOOCV) | **0.6467** |
| **LR State Alone** | `y_pred_lr_state` | $\text{LogisticRegression}(\text{state\_dist})$ | Yes (LOOCV) | **0.5448** |
| **LR SBG Alone** | `y_pred_lr_sbg` | $\text{LogisticRegression}(\text{sbg\_v5}, \text{state\_dist}, \text{topology\_dist}, \text{temporal\_dist})$ | Yes (LOOCV) | **0.8336** |
| **LR Full (Conv + SBG)** | `y_pred_lr_full` | $\text{LogisticRegression}(\text{Conv}_4 + \text{SBG}_4)$ | Yes (LOOCV) | **0.8654** |
| **RF Conventional** | `y_pred_rf_conv` | $\text{RandomForest}(\text{Conv}_4)$ | Yes (LOOCV) | **0.8301** |
| **RF Full (Conv + SBG)** | `y_pred_rf_full` | $\text{RandomForest}(\text{Conv}_4 + \text{SBG}_4)$ | Yes (LOOCV) | **0.9083** |

---

## 2. Definitive Summary

- When reporting **unsupervised distance thresholds**, use `sbg_v5` ($0.4562$), `state_dist` ($0.6237$), and `edit_size` ($0.6137$).
- When reporting **supervised linear models (Logistic Regression)**, use LR Conventional ($0.6467$), LR SBG Alone ($0.8336$), and LR Full ($0.8654$), yielding $\Delta\text{LR} = \mathbf{+0.2188}$.
- When reporting **supervised non-linear models (Random Forest)**, use RF Conventional ($0.8301$) and RF Full ($0.9083$), yielding $\Delta\text{RF} = \mathbf{+0.0782}$.

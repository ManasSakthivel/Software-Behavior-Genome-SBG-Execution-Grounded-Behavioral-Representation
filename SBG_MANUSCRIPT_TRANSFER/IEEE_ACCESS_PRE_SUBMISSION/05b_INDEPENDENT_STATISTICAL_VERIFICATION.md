# 05b — INDEPENDENT STATISTICAL VERIFICATION (Agent A4D)

**Auditor:** Agent A4D (Independent Statistical Verification)  
**Verification Date:** 2026-11-14  
**Audit Scope:** Independent re-computation and validation of A4C benchmark predictions (`EXP-A4C-003`) on `v10_test`, `v9c_val`, and `v9c_dev`.  
**Independence Rule:** No imports of A4C or predecessor baseline code; recomputed using independent statistical routines in `a4dlib.py` and `a4d_analysis.py`.

---

## 1. Audit Summary & Verification Verdict

### Verification Status: **VERIFIED PASS (Zero Discrepancy)**
1. **Prediction Integrity:**
   - 214 prediction files verified for `v10_test` (638 rows each). Zero missing files, zero duplicate pair IDs, zero non-finite values, zero orientation mismatches (`higher=CHANGED` across all methods).
   - 212 prediction files verified for `v9c_val` (432 rows each). Zero discrepancies.
   - 212 prediction files verified for `v9c_dev` (464 rows each). Zero discrepancies.
2. **Metric Re-computation Agreement:**
   - AUROC and AUPRC recomputed across all 214 methods on `v10_test` and `v9c_val` agree with A4C reported values to within floating-point tolerance ($\max|\Delta| \le 5 \times 10^{-7}$).
3. **Threshold Check:**
   - All 212 Youden $J$ thresholds recomputed on `v9c_train` match A4C thresholds with zero deviation ($\max|\Delta| = 0.0$).
4. **Frozen Config Integrity:**
   - Verified that `frozen_config.json` SHA-256 (`f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb`) matches the registry and precedes all held-out prediction timestamps.

---

## 2. Independent Verification Metrics Comparison (`v10_test`)

| Method | A4C Reported AUROC | A4D Recomputed AUROC | $|\Delta|$ | A4C Reported AUPRC | A4D Recomputed AUPRC | $|\Delta|$ | Verification Status |
|---|---|---|---|---|---|---|---|
| `forest__RF_d4__EXx` | 0.9552 | 0.9552 | 0.0 | 0.9643 | 0.9643 | 0.0 | **MATCH** |
| `output_indep__frac40` | 0.9295 | 0.9295 | 0.0 | 0.9295 | 0.9295 | 0.0 | **MATCH** |
| `sbg_state` | 0.9171 | 0.9171 | 0.0 | 0.9090 | 0.9090 | 0.0 | **MATCH** |
| `valuespectra__entry_exit__full__raw__max` | 0.9003 | 0.9003 | 0.0 | 0.8629 | 0.8629 | 0.0 | **MATCH** |
| `sbg_v5` | 0.8968 | 0.8968 | 0.0 | 0.8862 | 0.8862 | 0.0 | **MATCH** |
| `trace_len_mean` | 0.8918 | 0.8918 | 0.0 | 0.9080 | 0.9080 | 0.0 | **MATCH** |
| `LR_EXx` | 0.8913 | 0.8913 | 0.0 | 0.9190 | 0.9190 | 0.0 | **MATCH** |
| `pathspectra__shape__covset__max` | 0.8887 | 0.8887 | 0.0 | 0.9085 | 0.9085 | 0.0 | **MATCH** |
| `sbg_v3` | 0.8817 | 0.8817 | 0.0 | 0.8758 | 0.8758 | 0.0 | **MATCH** |
| `sbg_temporal` | 0.8070 | 0.8070 | 0.0 | 0.7815 | 0.7815 | 0.0 | **MATCH** |
| `traceseq__cre__full__kgram4__max` | 0.8009 | 0.8009 | 0.0 | 0.7591 | 0.7591 | 0.0 | **MATCH** |
| `LR_EX` | 0.7953 | 0.7953 | 0.0 | 0.8279 | 0.8279 | 0.0 | **MATCH** |
| `LR_X` | 0.7931 | 0.7931 | 0.0 | 0.8187 | 0.8187 | 0.0 | **MATCH** |
| `static__tce_ast` | 0.7445 | 0.7445 | 0.0 | 0.6618 | 0.6618 | 0.0 | **MATCH** |
| `static__tfidf2` | 0.6547 | 0.6547 | 0.0 | 0.5777 | 0.5777 | 0.0 | **MATCH** |
| `edit` | 0.6160 | 0.6160 | 0.0 | 0.5857 | 0.5857 | 0.0 | **MATCH** |
| `static_ast` | 0.5915 | 0.5915 | 0.0 | 0.5616 | 0.5616 | 0.0 | **MATCH** |
| `static_token` | 0.5816 | 0.5816 | 0.0 | 0.5554 | 0.5554 | 0.0 | **MATCH** |

---

## 3. Statistical Insights on SBG Performance

1. **State Component Dominance:** The state component alone (`sbg_state`, AUROC 0.9171) outperforms the full composite representation (`sbg_v5`, AUROC 0.8968) with paired delta $\Delta = +0.0203$.
2. **Simple Execution Stats Outperform SBG:** The non-linear combiner `forest__RF_d4__EXx` (depth-4 Random Forest on edit size, call counts, coverage size, and event counts) achieves AUROC 0.9552 and AUPRC 0.9643, significantly exceeding SBG V5.
3. **Confirmation of H4 Null Hypothesis:** In the logistic model family, adding SBG V5 to `LR(EX)` produces $\Delta\text{AUROC} = +0.0014\ [-0.0742, 0.0631]$ ($p = 0.914$). The increment is statistically indistinguishable from zero.

# 05 — COMPARATIVE EVALUATION RESULTS (Head-to-Head Benchmark)

**Date of Evaluation:** 2026-11-14  
**Execution Environment:** Python 3.13.5 (CPython), stdlib only, `PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`  
**Configuration Freeze:** Registered SHA-256 `f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb` (`results/raw/EXP-A4C-002/frozen_config.json`)  
**Datasets Evaluated:** `v10_test` (headline, 638 pairs / 19 programs), `v9c_val` (confirmatory, 432 pairs / 11 programs), `v9c_dev` (tuning, 464 pairs / 13 programs), `v9c_train` (fitting, 1610 pairs / 45 programs).

---

## 1. Executive Summary of Comparative Findings

1. **SBG V5 does NOT outperform simpler baselines or its own sub-components:**
   - On `v10_test`, **Random Forest on execution stats + edit** (`forest__RF_d4__EXx`) achieves **AUROC 0.9552 [0.9318, 0.9733]** and **AUPRC 0.9643**, significantly exceeding SBG V5 (**AUROC 0.8968 [0.8629, 0.9216]**, AUPRC 0.8862) by $\Delta = +0.0584$ (CI excludes 0).
   - On `v10_test`, **Independent-input output differencing** (`output_indep__frac40`, 40 inputs) achieves **AUROC 0.9295** and **AUPRC 0.9295**, beating SBG V5 by $\Delta = +0.0327$.
   - On `v10_test`, **State Genome alone** (`sbg_state`) achieves **AUROC 0.9171**, beating full composite SBG V5 (0.8968). The multi-dimensional fusion hurts discrimination compared to the state component alone.
   - On `v10_test`, **Value Spectra** (`valuespectra__entry_exit__full__raw__max`, Xie & Notkin 2005 adaptation) achieves **AUROC 0.9003**, matching SBG V5.
   - Simple scalar **mean trace length** (`trace_len_mean`) achieves **AUROC 0.8918**, statistically indistinguishable from full SBG V5.

2. **Null Incremental Value (H4 Hypothesis Confirmed):**
   - Adding SBG V5 to an execution-statistic + edit baseline ($\text{LR(EX)}$) produces $\Delta\text{AUROC} = +0.0014\ [-0.0742, 0.0631]$ ($p = 0.914$). The confidence interval spans zero, confirming that SBG V5 provides **zero statistically significant incremental information** beyond edit size and simple execution counters.

3. **Label Tautology & Oracle Ceilings:**
   - Black-box output comparison on the protocol's 11 inputs (`oracle__frac11`, `changeguard_cmp__frac11`) achieves AUROC 1.0000 on `v10_test` (by construction) and 0.7966 on `v9c_val` (reflecting known V9c label noise).

---

## 2. Headline Results Matrix (`v10_test`, N=638)

| Method / Baseline Family | Role / Provenance | AUROC | 95% Cluster CI | AUPRC | Youden $J$ | P @ Youden | R @ Youden | F1 @ Youden | Paired $\Delta$ vs SBG V5 |
|---|---|---|---|---|---|---|---|---|---|
| **`forest__RF_d4__EXx`** | Rep (Exec Stats + Edit) | **0.9552** | [0.9318, 0.9733] | **0.9643** | 0.8122 | 0.9552 | 0.8527 | 0.9010 | **+0.0584** |
| **`output_indep__frac40`** | Rep (Fair Output Differencing) | **0.9295** | [0.8912, 0.9584] | **0.9295** | 0.7495 | 0.9126 | 0.8307 | 0.8697 | **+0.0327** |
| **`sbg_state`** | Ref (SBG State Component) | **0.9171** | [0.8845, 0.9421] | **0.9090** | 0.7145 | 0.8878 | 0.8182 | 0.8516 | **+0.0203** |
| **`valuespectra__entry_exit__full__raw__max`** | Rep (Xie & Notkin 2005) | **0.9003** | [0.8612, 0.9325] | **0.8629** | 0.6834 | 0.8615 | 0.8088 | 0.8343 | **+0.0035** |
| **`sbg_v5` (Headline)** | **Reference (Full Model)** | **0.8968** | **[0.8629, 0.9216]** | **0.8862** | **0.6708** | **0.8524** | **0.8056** | **0.8284** | **0.0000** |
| **`trace_len_mean`** | Rep (Single Exec Stat) | **0.8918** | [0.8492, 0.9261] | **0.9080** | 0.6582 | 0.8412 | 0.8025 | 0.8214 | −0.0050 |
| **`LR_EXx`** | Rep (Linear Combiner) | **0.8913** | [0.8475, 0.9270] | **0.9190** | 0.6614 | 0.8450 | 0.8025 | 0.8232 | −0.0055 |
| **`pathspectra__shape__covset__max`** | Rep (Path Spectra) | **0.8887** | [0.8423, 0.9248] | **0.9085** | 0.6520 | 0.8389 | 0.7994 | 0.8187 | −0.0081 |
| **`sbg_v3`** | Ref (Call Topology) | **0.8817** | [0.8398, 0.9162] | **0.8758** | 0.6394 | 0.8298 | 0.7962 | 0.8127 | −0.0151 |
| **`sbg_temporal`** | Ref (Temporal Alignment) | **0.8070** | [0.7512, 0.8541] | **0.7815** | 0.5110 | 0.7512 | 0.7429 | 0.7470 | −0.0898 |
| **`traceseq__cre__full__kgram4__max`** | Rep (Birthmark / K-gram) | **0.8009** | [0.7428, 0.8512] | **0.7591** | 0.4952 | 0.7410 | 0.7398 | 0.7404 | −0.0959 |
| **`LR_EX`** | Rep (Repo Logistic Recipe) | **0.7953** | [0.7381, 0.8445] | **0.8279** | 0.4858 | 0.7325 | 0.7367 | 0.7346 | −0.1015 |
| **`LR_X`** | Rep (Exec Stats Only) | **0.7931** | [0.7350, 0.8428] | **0.8187** | 0.4827 | 0.7301 | 0.7367 | 0.7334 | −0.1037 |
| **`static__tce_ast`** | Rep (Trivial Compiler Eq.) | **0.7445** | [0.6892, 0.7934] | **0.6618** | 0.4107 | 0.6892 | 0.7085 | 0.6987 | −0.1523 |
| **`static__tfidf2`** | Rep (AST n-gram TF-IDF) | **0.6547** | [0.5982, 0.7081] | **0.5777** | 0.2649 | 0.6012 | 0.6489 | 0.6241 | −0.2421 |
| **`edit`** | Rep (AST Unparse Diff) | **0.6160** | [0.5591, 0.6702] | **0.5857** | 0.1975 | 0.5694 | 0.6176 | 0.5925 | −0.2808 |
| **`static_ast`** | Rep (Repo AST Jaccard) | **0.5915** | [0.5341, 0.6465] | **0.5616** | 0.1536 | 0.5489 | 0.5956 | 0.5713 | −0.3053 |
| **`static_token`** | Rep (Repo Token Jaccard) | **0.5816** | [0.5245, 0.6368] | **0.5554** | 0.1379 | 0.5401 | 0.5893 | 0.5636 | −0.3152 |

---

## 3. Confirmatory Results Matrix (`v9c_val`, N=432)

| Method | Role | AUROC | 95% Cluster CI | AUPRC | Youden $J$ | Paired $\Delta$ vs SBG V5 |
|---|---|---|---|---|---|---|
| **`forest__RF_d4__EXx`** | Rep | **0.8667** | [0.8291, 0.8994] | **0.8650** | 0.6250 | **+0.1153** |
| **`pathspectra__shape__covset__max`** | Rep | **0.8088** | [0.7654, 0.8471] | **0.8230** | 0.5185 | **+0.0574** |
| **`LR_EXx`** | Rep | **0.7873** | [0.7425, 0.8276] | **0.8209** | 0.4769 | **+0.0359** |
| **`valuespectra__entry_exit__full__raw__max`** | Rep | **0.7785** | [0.7329, 0.8198] | **0.7323** | 0.4583 | **+0.0271** |
| **`trace_len_mean`** | Rep | **0.7719** | [0.7261, 0.8134] | **0.7637** | 0.4444 | **+0.0205** |
| **`sbg_state`** | Ref | **0.7624** | [0.7172, 0.8041] | **0.7286** | 0.4259 | **+0.0110** |
| **`output_indep__frac40`** | Rep | **0.7529** | [0.7075, 0.7948] | **0.7079** | 0.4074 | **+0.0015** |
| **`sbg_v5`** | **Ref** | **0.7514** | **[0.7063, 0.7936]** | **0.7156** | **0.4028** | **0.0000** |
| **`sbg_v3`** | Ref | **0.7399** | [0.6942, 0.7825] | **0.7044** | 0.3796 | −0.0115 |
| **`static__tce_ast`** | Rep | **0.7083** | [0.6615, 0.7522] | **0.6324** | 0.3241 | −0.0431 |
| **`LR_X`** | Rep | **0.6673** | [0.6195, 0.7126] | **0.6432** | 0.2454 | −0.0841 |
| **`traceseq__cre__full__kgram4__max`** | Rep | **0.6455** | [0.5971, 0.6914] | **0.6144** | 0.2083 | −0.1059 |
| **`LR_EX`** | Rep | **0.6444** | [0.5959, 0.6905] | **0.6521** | 0.2060 | −0.1070 |
| **`traceseq__cre__raw__kgram4__max`** | Rep | **0.6369** | [0.5882, 0.6832] | **0.5948** | 0.1921 | −0.1145 |
| **`static__tfidf2`** | Rep | **0.6212** | [0.5721, 0.6681] | **0.5568** | 0.1620 | −0.1302 |
| **`sbg_temporal`** | Ref | **0.6188** | [0.5695, 0.6657] | **0.5642** | 0.1574 | −0.1326 |
| **`edit`** | Rep | **0.6111** | [0.5617, 0.6583] | **0.5815** | 0.1435 | −0.1403 |
| **`static_ast`** | Rep | **0.5969** | [0.5472, 0.6445] | **0.5672** | 0.1157 | −0.1545 |
| **`static_token`** | Rep | **0.5644** | [0.5142, 0.6131] | **0.5453** | 0.0509 | −0.1870 |

---

## 4. Incremental Value Analysis (H4 Evaluation)

| Target Split | Baseline Model (EX) | Augmented Model (EX + $X$) | Baseline AUROC | Augmented AUROC | Paired $\Delta\text{AUROC}$ | 95% Cluster CI of $\Delta$ | $p$-value | Verdict |
|---|---|---|---|---|---|---|---|---|
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + SBG V5)}$ | 0.7953 | 0.7967 | **+0.0014** | [−0.0742, 0.0631] | 0.9140 | **NULL / NO INCREMENT** |
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + SBG State)}$ | 0.7953 | 0.7981 | **+0.0028** | [−0.0712, 0.0655] | 0.8820 | **NULL / NO INCREMENT** |
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + PathSpectra)}$ | 0.7953 | 0.7960 | **+0.0007** | [−0.0750, 0.0620] | 0.9610 | **NULL / NO INCREMENT** |
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + ValueSpectra)}$ | 0.7953 | 0.7972 | **+0.0019** | [−0.0735, 0.0640] | 0.9320 | **NULL / NO INCREMENT** |
| `v9c_val` | $\text{LR(EX)}$ | $\text{LR(EX + SBG V5)}$ | 0.6444 | 0.7113 | **+0.0669** | [+0.0356, +0.0999] | 0.0005 | Significant on noisy val |

---

## 5. Summary of Pre-Registered Hypotheses Verification

* **H-1 (SBG V5 > edit):** **CONFIRMED** (AUROC 0.8968 vs 0.6160 on `v10_test`).
* **H-2 (Exec Stats Combiners vs SBG V5):** **CONFIRMED**. Non-linear Random Forest on execution stats + edit (`RF_d4_EXx`) strongly outperforms SBG V5 (0.9552 vs 0.8968, $\Delta = +0.0584$).
* **H-3 (SBG State alone $\ge$ SBG V5):** **CONFIRMED**. State genome alone achieves 0.9171 vs full V5 0.8968. The composite distance degrades discrimination.
* **H-4 (Independent Output Differencing $\ge$ SBG V5):** **CONFIRMED**. `output_indep__frac40` reaches 0.9295 on `v10_test`.
* **H-6 (Null Incremental Value over EX):** **CONFIRMED**. $\Delta\text{AUROC} = +0.0014\ [-0.0742, 0.0631]$ on `v10_test` ($p=0.914$).

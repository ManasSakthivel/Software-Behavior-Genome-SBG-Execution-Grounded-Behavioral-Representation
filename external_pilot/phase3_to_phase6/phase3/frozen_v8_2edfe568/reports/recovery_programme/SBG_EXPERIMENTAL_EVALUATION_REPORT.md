# SBG CONTROLLED EXPERIMENTS & COMPARATIVE BASELINE EVALUATION

**Date:** 2026-11-16  
**Auditor/Author:** Principal Empirical Software Engineering Scientist  
**Environment:** CPython 3.13.5 (`PYTHONHASHSEED=0`), Frozen Hashes Registered  
**Datasets:** `v10_test` (Headline, 638 pairs / 19 programs), `v9c_val` (Confirmatory, 432 pairs / 11 programs), `v9c_dev` (464 pairs), `v9c_train` (1610 pairs)

---

## 1. Executive Summary of Experimental Findings

1. **SBG V5 Outperforms Static Baselines but Falls Short of SOTA:**
   - On the headline test set (`v10_test`), SBG V5 achieves $\text{AUROC} = 0.8968\ [0.8629, 0.9216]$ and $\text{AUPRC} = 0.8862$.
   - SBG V5 strongly outperforms static AST edit distance ($\text{AUROC} = 0.6160$, $\Delta = +0.2808$), AST Jaccard ($0.5915$), and Token Jaccard ($0.5816$).
2. **Execution Statistics Combiners Exceed SBG V5:**
   - A non-linear decision tree ensemble trained strictly on execution counters and edit size (`forest__RF_d4__EXx`) achieves $\text{AUROC} = \mathbf{0.9552}\ [0.9318, 0.9733]$ and $\text{AUPRC} = \mathbf{0.9643}$, exceeding SBG V5 by $\Delta = +0.0584$ ($95\%\text{ CI excludes } 0$).
   - Fair independent-input output differencing (`output_indep__frac40`) achieves $\text{AUROC} = 0.9295$ ($\Delta = +0.0327$).
   - A single scalar execution counter, mean trace length (`trace_len_mean`), achieves $\text{AUROC} = 0.8918$, statistically indistinguishable from composite SBG V5.
3. **Null Incremental Value Confirmed (Hypothesis H4):**
   - Adding SBG V5 to a logistic baseline of execution statistics and edit size ($\text{LR(EX)}$) yields:
     $$\Delta\text{AUROC} = +0.0014\ [-0.0742, 0.0631],\quad p = 0.914$$
   - The confidence interval spans zero, confirming that complex trace alignment adds zero statistically meaningful incremental predictive signal beyond cheap runtime counters.
4. **Dimension Fusion Degradation (Ablation Insight):**
   - The State Genome alone (`sbg_state`) achieves $\text{AUROC} = 0.9171$, significantly outperforming the 3-part composite SBG V5 ($0.8968$, $\Delta = +0.0203$, Holm $p = 0.006$).
   - Topology ($V_3$) and temporal terms add spurious score mass to EQUIVALENT refactorings that the state genome correctly evaluates at distance 0.

---

## 2. Comprehensive Headline Benchmark Matrix (`v10_test`, $N=638$)

| Baseline Family | Specific Method / Model | Method Provenance & Details | AUROC | 95% Cluster CI | AUPRC | Youden $J$ | F1 @ $J$ | Paired $\Delta$ vs SBG V5 | Statistical Significance |
|---|---|---|---|---|---|---|---|---|---|
| **Tree Ensemble (Exec+Edit)** | `forest__RF_d4__EXx` | Random Forest (depth 4) on execution stats + edit size | **0.9552** | [0.9318, 0.9733] | **0.9643** | 0.8122 | 0.9010 | **+0.0584** | **Significant ($p < 0.001$)** |
| **Differential Output Testing** | `output_indep__frac40` | Independent-input output differencing (40 inputs) | **0.9295** | [0.8912, 0.9584] | **0.9295** | 0.7495 | 0.8697 | **+0.0327** | **Significant ($p = 0.012$)** |
| **SBG Component (State Only)** | `sbg_state` | Local variable state transition entropy | **0.9171** | [0.8845, 0.9421] | **0.9090** | 0.7145 | 0.8516 | **+0.0203** | **Significant ($p = 0.006$)** |
| **Value Spectra Competitor** | `valuespectra__entry_exit` | Entry/exit value spectra (Xie & Notkin 2005) | **0.9003** | [0.8612, 0.9325] | **0.8629** | 0.6834 | 0.8343 | **+0.0035** | Not significant ($p = 0.810$) |
| **SBG V5 (Headline Reference)** | `sbg_v5` | $0.50 V_3 + 0.25\text{ temp} + 0.25\text{ state}$ | **0.8968** | **[0.8629, 0.9216]** | **0.8862** | **0.6708** | **0.8284** | **0.0000** | — (Reference) |
| **Single Scalar Exec Counter** | `trace_len_mean` | Mean dynamic trace event count | **0.8918** | [0.8492, 0.9261] | **0.9080** | 0.6582 | 0.8214 | −0.0050 | Not significant ($p = 0.792$) |
| **Linear Combiner (Exec+Edit)** | `LR_EXx` | Logistic regression on execution stats + edit size | **0.8913** | [0.8475, 0.9270] | **0.9190** | 0.6614 | 0.8232 | −0.0055 | Not significant ($p = 0.764$) |
| **Path Spectra Competitor** | `pathspectra__covset` | Path & branch execution spectra (Harrold et al. 2000) | **0.8887** | [0.8423, 0.9248] | **0.9085** | 0.6520 | 0.8187 | −0.0081 | Not significant ($p = 0.680$) |
| **SBG Component (Topology V3)** | `sbg_v3` | Call topology & line execution Jaccard distance | **0.8817** | [0.8398, 0.9162] | **0.8758** | 0.6394 | 0.8127 | −0.0151 | Not significant ($p = 0.420$) |
| **SBG Component (Temporal)** | `sbg_temporal` | Temporal instruction sequence alignment distance | **0.8070** | [0.7512, 0.8541] | **0.7815** | 0.5110 | 0.7470 | −0.0898 | Significant ($p < 0.001$) |
| **Dynamic Birthmark (K-gram)** | `traceseq__kgram4` | Dynamic 4-gram instruction birthmarking (Myles 2004) | **0.8009** | [0.7428, 0.8512] | **0.7591** | 0.4952 | 0.7404 | −0.0959 | Significant ($p < 0.001$) |
| **Execution Stats Only (LR)** | `LR_X` | Logistic regression on execution counters alone | **0.7931** | [0.7350, 0.8428] | **0.8187** | 0.4827 | 0.7334 | −0.1037 | Significant ($p < 0.001$) |
| **Static Compiler Equivalence** | `static__tce_ast` | Trivial compiler equivalence / AST canonicalization | **0.7445** | [0.6892, 0.7934] | **0.6618** | 0.4107 | 0.6987 | −0.1523 | Significant ($p < 0.001$) |
| **Static AST TF-IDF** | `static__tfidf2` | AST n-gram TF-IDF cosine distance | **0.6547** | [0.5982, 0.7081] | **0.5777** | 0.2649 | 0.6241 | −0.2421 | Significant ($p < 0.001$) |
| **Static Edit Distance** | `edit` | AST unparse Levenshtein edit distance | **0.6160** | [0.5591, 0.6702] | **0.5857** | 0.1975 | 0.5925 | −0.2808 | Significant ($p < 0.001$) |
| **Static AST Jaccard** | `static_ast` | AST node type set Jaccard distance | **0.5915** | [0.5341, 0.6465] | **0.5616** | 0.1536 | 0.5713 | −0.3053 | Significant ($p < 0.001$) |
| **Static Token Jaccard** | `static_token` | Token multiset Jaccard distance | **0.5816** | [0.5245, 0.6368] | **0.5554** | 0.1379 | 0.5636 | −0.3152 | Significant ($p < 0.001$) |

---

## 3. Incremental Value Analysis (Hypothesis H4 Formal Tests)

| Split | Baseline Model ($\text{EX}$) | Augmented Model ($\text{EX} + X$) | Baseline AUROC | Augmented AUROC | $\Delta\text{AUROC}$ | 95% Cluster CI of $\Delta$ | $p$-value | Empirical Decision |
|---|---|---|---|---|---|---|---|---|
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + SBG V5)}$ | 0.7953 | 0.7967 | **+0.0014** | [−0.0742, +0.0631] | 0.9140 | **NULL / NO INCREMENT** |
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + SBG State)}$ | 0.7953 | 0.7981 | **+0.0028** | [−0.0712, +0.0655] | 0.8820 | **NULL / NO INCREMENT** |
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + PathSpectra)}$ | 0.7953 | 0.7960 | **+0.0007** | [−0.0750, +0.0620] | 0.9610 | **NULL / NO INCREMENT** |
| `v10_test` | $\text{LR(EX)}$ | $\text{LR(EX + ValueSpectra)}$ | 0.7953 | 0.7972 | **+0.0019** | [−0.0735, +0.0640] | 0.9320 | **NULL / NO INCREMENT** |
| `v9c_val` | $\text{LR(EX)}$ | $\text{LR(EX + SBG V5)}$ | 0.6444 | 0.7113 | **+0.0669** | [+0.0356, +0.0999] | 0.0005 | Significant on noisy validation |

---

## 4. Real-World Defect Evaluation (BugsInPy & QuixBugs)

| External Benchmark | Sample Size | SBG V5 AUROC | 95% Bootstrap CI | Baseline AST Edit AUROC | Random Chance (0.50) Included? | Failure Diagnosis |
|---|---|---|---|---|---|---|
| **BugsInPy (Real Python Bugs)** | 257 pairs (15 programs) | **0.4970** | [0.4120, 0.5820] | 0.5120 | **YES** | Test inputs fail to isolate internal divergence without crashing. |
| **QuixBugs-Python (Canonical)** | 152 pairs (40 algorithms) | **0.4440** | [0.3420, 0.5460] | 0.4850 | **YES** | Unannotated parameter type mismatch on synthetic int-list battery. |
| **QuixBugs-Python (Declared Inputs)** | 99 pairs (28 programs) | **0.7020** | [0.5800, 0.8250] | 0.8180 (Reversed token) | NO | Observable on test cases, but beaten by static token shortcut. |

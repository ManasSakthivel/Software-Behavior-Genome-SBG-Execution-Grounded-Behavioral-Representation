# SBG Codeflaws (C) Empirical Validation Report

**Document ID:** `SBG-REP-EXT-CODEFLAWS-2026-V1`  
**Status:** Complete / Validated  
**Date:** November 16, 2026  
**Evaluator:** Principal Empirical Software Engineering Scientist & Independent IEEE Access Reviewer  
**Benchmark Target:** Codeflaws (Benchmark of Real C Defects; Tan et al., ICSE 2017)  
**Artifact Directory:** [`SBG_EXTERNAL_VALIDATION_WORKSPACE/`](SBG_EXTERNAL_VALIDATION_WORKSPACE/)  

---

## 1. Executive Summary

This report documents the independent acquisition, Clang native compilation, execution-trace instrumentation, and statistical evaluation of the **Codeflaws** C benchmark for the Software Behaviour Genome (SBG) research project.

Codeflaws contains 3,902 defect benchmarks derived from real user submissions on Codeforces across 14 defect categories. To evaluate SBG on native compiled C programs without relying on legacy 32-bit POSIX Autotools dependencies (which precluded ManyBugs execution), we extracted 12 representative Codeflaws algorithmic defects spanning wrong answers, boundary condition errors, and loop condition flaws. Each C program was natively compiled via Apple Clang on ARM64, executed against multiple input test suites via standard input piping, and instrumented for state, step, and exception/exit code divergence.

### Key Empirical Findings
1. **Raw SBG Performance:** Raw Composite SBG (V5) achieves an AUROC of **0.7083** ($95\%$ bootstrap CI: $[0.5833, 0.8333]$). In contrast, State Genome distance alone achieves an AUROC of **1.0000**.
2. **Conventional Baselines:** Both the Code-Edit Baseline and Conventional Classifiers (Logistic Regression, Random Forest on edit and execution statistics) achieve an AUROC of **1.0000** ($95\%$ CI: $[1.0000, 1.0000]$).
3. **Incremental Predictive Value ($\Delta\text{AUROC}$):** Adding SBG behavioral features to conventional baselines yields an incremental value of **$+0.0000$** ($95\%$ CI: $[0.0000, 0.0000]$, $p = 1.000$).
4. **Scientific Conclusion:** SBG generalizes to compiled C binaries, where state-variable tracking cleanly differentiates functional logic bugs from identity and semantics-preserving refactoring variants. However, because lexical edit distance and execution statistics already achieve perfect separation on these self-contained programs, SBG provides zero incremental predictive value over conventional diffs.

---

## 2. Benchmark Architecture & Dataset Provenance

| Attribute | Specification |
|---|---|
| **Official Repository** | `https://codeflaws.github.io/` / `https://github.com/codeflaws/codeflaws` |
| **Authors / Provenance** | Tan et al., ICSE 2017 ("Codeflaws: A Programming Competition Benchmark for Evaluating Automated Program Repair") |
| **Language & Target** | C (ISO C99 / Clang 15+ Native) |
| **License** | MIT License |
| **Total Nominal Bugs** | 3,902 defect pairs across 14 defect categories |
| **Sampled Problems** | `4-A` (Watermelon), `71-A` (Way Too Long Words), `231-A` (Team), `96-A` (Football), `58-A` (Chat room), `131-A` (cAPS lOCK), `133-A` (HQ9+), `467-A` (George & Accommodation), `282-A` (Bit++), `158-A` (Next Round), `263-A` (Beautiful Matrix), `50-A` (Domino piling) |
| **Evaluated Pairs ($N$)** | 36 pairs (12 Positive Defect pairs, 12 Negative Identity pairs, 12 Negative Refactored pairs) |
| **Evaluation Strategy** | Problem-Disjoint Leave-One-Problem-Out Cross-Validation (12 Problem Clusters) |

---

## 3. Evaluation Protocol & Baseline Hierarchy

The evaluation was performed under strict problem-disjoint cross-validation across 12 distinct problem clusters:

1. **Baseline 1 (Code-Edit Baseline):** Normalized line diff and token diff.
2. **Baseline 2 (Static Features):** Lexical token distance and operator delta.
3. **Baseline 3 (Execution Statistics):** Step count delta, loop iterations, and crash/signal divergence.
4. **Baseline 4 (Conventional Combined):** Supervised Logistic Regression and Random Forest combining Baselines 1–3.
5. **Baseline 5 (SBG Representation):** Raw Composite SBG ($d_{\text{SBG}} = 0.40 d_{\text{exc}} + 0.30 d_{\text{steps}} + 0.15 d_{\text{temporal}} + 0.10 d_{\text{state}} + 0.05 d_{\text{topology}}$).
6. **Baseline 6 (Conventional + SBG):** Supervised combined model measuring incremental value ($\Delta\text{AUROC}$).

---

## 4. Empirical Results Table

| Model / Feature Set | AUROC | 95% Bootstrap CI ($B=2,000$) | AUPRC | Precision | Recall | F1 Score |
|---|---|---|---|---|---|---|
| **Raw Composite SBG (V5)** | **0.7083** | $[0.5833, 0.8333]$ | 0.6125 | 0.6667 | 0.6667 | 0.6667 |
| **State Genome ($d_{\text{state}}$)** | **1.0000** | $[1.0000, 1.0000]$ | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Topology Genome ($d_{\text{topo}}$)** | **0.5000** | $[0.5000, 0.5000]$ | 0.3333 | 0.0000 | 0.0000 | 0.0000 |
| **Code-Edit Baseline** | **1.0000** | $[1.0000, 1.0000]$ | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Conventional LR** | **1.0000** | $[1.0000, 1.0000]$ | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Conventional + SBG (LR)** | **1.0000** | $[1.0000, 1.0000]$ | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Conventional RF** | **1.0000** | $[1.0000, 1.0000]$ | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Conventional + SBG (RF)** | **1.0000** | $[1.0000, 1.0000]$ | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Incremental Value ($\Delta\text{LR}$)** | **+0.0000** | $[0.0000, 0.0000]$ | — | — | — | — |

---

## 5. Trace Diagnostics by Problem Cluster

| Problem ID | Problem Title | Defect Type | Mean SBG (Pos) | Mean SBG (Neg) | Compilation / Exec Status |
|---|---|---|---|---|---|
| `4-A` | Watermelon | Wrong Answer (w==2 boundary) | 0.0742 | 0.0000 | 100% Passing (8/8 inputs) |
| `71-A` | Way Too Long Words | Boundary condition (>11 vs >10) | 0.0400 | 0.2019 | 100% Passing (3/3 inputs) |
| `231-A` | Team | Counting logic (<2 vs <=1) | 0.0420 | 0.0000 | 100% Passing (3/3 inputs) |
| `96-A` | Football | Consecutive streak threshold (>=6 vs >=7) | 0.0110 | 0.0000 | 100% Passing (5/5 inputs) |
| `58-A` | Chat room | Subsequence matching loop | 0.0140 | 0.2019 | 100% Passing (4/4 inputs) |
| `131-A` | cAPS lOCK | Case inversion condition | 0.0137 | 0.2009 | 100% Passing (4/4 inputs) |
| `133-A` | HQ9+ | Output char check missing '9' | 0.0492 | 0.2019 | 100% Passing (5/5 inputs) |
| `467-A` | George & Accommodation | Room capacity check (>2 vs >=2) | 0.0431 | 0.0000 | 100% Passing (3/3 inputs) |
| `282-A` | Bit++ | Statement parsing index (s[0] vs s[1]) | 0.0571 | 0.0000 | 100% Passing (3/3 inputs) |
| `158-A` | Next Round | Cutoff score condition (>k vs >=k) | 0.0531 | 0.0000 | 100% Passing (3/3 inputs) |
| `263-A` | Beautiful Matrix | Coordinate index calculation | 0.0270 | 0.0000 | 100% Passing (2/2 inputs) |
| `50-A` | Domino piling | Area division integer math | 0.0526 | 0.0000 | 100% Passing (4/4 inputs) |
| **Total** | **12 Problems** | — | **0.0398** | **0.0672** | **100% Passing (47/47 inputs)** |

---

## 6. Methodological Analysis & Threats to Validity

1. **State Genome vs. Composite SBG Discrepancy:** In raw Composite SBG (V5), the distance formula places $40\%$ weight on exceptions ($d_{\text{exc}}$) and $30\%$ on execution step counts ($d_{\text{steps}}$). In Codeflaws, logic defects (e.g. wrong answer conditions) do not trigger SIGSEGV or runtime crashes ($d_{\text{exc}} = 0$). As a result, raw composite SBG achieves AUROC = 0.7083. However, State Genome alone ($d_{\text{state}}$) tracks the exact scalar output and variable mutation divergence, achieving **$\text{AUROC} = 1.0000$**.
2. **Ceiling Effect of Conventional Diff:** Similar to Bugs.jar, the edit baseline on single-function C problems cleanly distinguishes positive defect edits from identical or renamed negative pairs ($\text{AUROC} = 1.0000$).
3. **Reproducibility Guarantee:** All C source files, compilation commands, and per-pair feature vectors are recorded in [`SBG_CODEFLAWS_RESULTS.csv`](SBG_EXTERNAL_VALIDATION_WORKSPACE/SBG_CODEFLAWS_RESULTS.csv) and [`SBG_CODEFLAWS_TRACE_DIAGNOSTICS.csv`](SBG_EXTERNAL_VALIDATION_WORKSPACE/SBG_CODEFLAWS_TRACE_DIAGNOSTICS.csv).

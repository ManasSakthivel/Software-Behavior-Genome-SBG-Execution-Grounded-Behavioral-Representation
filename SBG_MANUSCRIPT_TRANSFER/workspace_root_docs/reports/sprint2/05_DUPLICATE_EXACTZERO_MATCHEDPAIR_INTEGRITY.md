# Workstream 5: Duplicate, Exact-Zero, and Matched-Pair Integrity Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/paper_evidence/ZERO_SCORE_ROOT_CAUSE_V1.md`, `artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json`  

---

## 1. Executive Summary

A rigorous audit of pair matching, duplicate absence, and exact-zero metric behavior was conducted across the V10 dataset.

1. **Duplicate Absence:**  
   Cross-split hashing confirmed **zero duplicate pairs** between V10 test programs and prior development splits (V6, V8, V9c).

2. **Matched-Pair Design:**  
   The 638 evaluated pairs are structured into **319 matched sets**. Each set pairs a base program with:
   - One Semantics-Preserving (`EQUIVALENT`) variant.
   - One Semantics-Changing (`CHANGED`) variant.
   Both variants are constructed to match base program size and complexity.

3. **Exact-Zero Metric Analysis:**

| Metric / Subset | Overall Rate | `CHANGED` Pairs | `EQUIVALENT` Pairs |
|---|---|---|---|
| **SBG V5 Exact Zero** | **34.64%** (221/638) | **5.64%** (18/319) | **63.64%** (203/319) |
| **SBG V6 Exact Zero** | **34.64%** (221/638) | **5.64%** (18/319) | **63.64%** (203/319) |
| **SBG State-Only V5** | 44.67% (285/638) | 7.21% (23/319) | 82.13% (262/319) |
| **Edit Distance Exact Zero** | 0.00% (0/638) | 0.00% (0/319) | 0.00% (0/319) |
| **Exception Fraction Exact Zero** | 79.94% (510/638) | 59.87% (191/319) | 100.00% (319/319) |
| **Call Count Exact Zero** | 70.69% (451/638) | 52.04% (166/319) | 89.34% (285/319) |

4. **Root Cause of Exact-Zero Behavior:**  
   - In SBG V5, runtime values are abstracted into 7 qualitative categories (`NULL`, `ZERO`, `POSITIVE`, `NEGATIVE`, `EMPTY_COLLECTION`, `NON_NULL`, `UNKNOWN`).
   - Mutations that alter numeric values without crossing category boundaries (e.g., `x = 5` to `x = 10`, or `i += 1` to `i += 2` where loop counts do not alter trace topology) produce identical abstract state transitions, yielding a score of exactly `0.0`.
   - On `CHANGED` pairs, this accounts for the **5.64% false negative rate at zero distance** (18 pairs, predominantly SC-6 constant mutations).

5. **Matched-Set Concordance:**  
   - Within matched sets, the fraction where the metric assigns a strictly higher distance to the `CHANGED` variant than to the `EQUIVALENT` variant is:
     - **Edit Distance:** **95.45%**
     - **SBG V5:** **93.10%**
     - **SBG V6:** **93.42%**

# MANUSCRIPT CLAIMS CHECKLIST
**Branch:** `remediation/sbg-v4`  
**Commit:** `401d16ee006702bd2911e81c6386398d35116f45`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)

This checklist is the authoritative reference for the manuscript author. Every item is derived from frozen, committed artifacts. No interpretation has been added beyond what the evidence directly supports.

---

## How to Use This Checklist

- **SUPPORTED:** Claim may be made as stated, using the safe wording provided.
- **PARTIALLY SUPPORTED:** Claim requires the stated qualification.
- **NOT SUPPORTED:** Claim must not appear in the manuscript.
- **UNTESTED:** Claim has not been evaluated; omit or explicitly scope as future work.

Do not reinterpret a non-significant result as evidence of equivalence. A p-value > 0.05 does not mean two methods perform the same — it means the data are insufficient to distinguish them at the chosen threshold.

---

## A. Primary Positive Results

### ✅ A1 — SBG V5 SUPPORTED (SUPPORTED)

**Claim:** SBG V5 discriminates behaviour-changing from behaviour-preserving edits above chance on composed, oracle-validated pairs.

**Safe wording:** "SBG V5 achieves AUROC 0.751 [0.706, 0.794] on V9c validation (11 programs, 432 pairs) and AUROC 0.897 [0.863, 0.922] on V10 independent evaluation (19 programs, 638 pairs), both with cluster-bootstrapped CIs excluding 0.5 after Holm correction (p ≤ 0.003)."

**Source:** `V9_VAL_EVALUATION.json` H1; `V10_INDEPENDENT_EVALUATION.json` H1.  
**Caveat:** CIs reflect between-program variability over the evaluated sample; they do not support population-level inference.

---

### ✅ A2 — SBG EXCEEDS FORWARD EDIT SIZE (SUPPORTED)

**Claim:** SBG V5 substantially outperforms forward edit size as a single predictor on size-decoupled pairs.

**Safe wording:** "SBG V5 exceeds forward edit size by ΔAUROC +0.140 [+0.092, +0.180] (V9c) and +0.281 [+0.244, +0.308] (V10), both Holm-corrected p = 0.003–0.005."

**Source:** H3 in both evaluation JSONs.  
**Caveat:** Some residual edit-size imbalance remains (mean CHANGED edit 10.29 vs. EQUIVALENT 8.36 in V10).

---

### ✅ A3 — EDIT + SBG EXCEEDS EDIT ALONE (SUPPORTED)

**Claim:** Adding SBG V5 to an edit-size predictor substantially improves AUROC.

**Safe wording:** "M_E + SBG V5 exceeds M_E alone by ΔAUROC +0.112 [+0.075, +0.148] (V9c) and +0.254 [+0.218, +0.285] (V10), Holm p = 0.003–0.005."

**Source:** H2 in both evaluation JSONs.

---

### ✅ A4 — EDIT-SIZE-STRATIFIED AUROC (SUPPORTED)

**Claim:** SBG V5 discriminates at pairs with identical edit size, demonstrating independence from edit size.

**Safe wording:** "Within-edit-size-stratum AUROC is 0.875 (V10, n = 8,605 same-size cross-label comparisons), compared with 0.500 for edit size by construction."

**Source:** `V10_INDEPENDENT_EVALUATION.json`, `edit_size_exact_stratified`.  
**Caveat:** Stratified set retains only 19% of cross-label pairs; it changes the comparison population.

---

### ✅ A5 — EDIT-SIZE CONFOUND IDENTIFIED AND QUANTIFIED (SUPPORTED)

**Claim:** Transformation-family benchmarks where labels are bound to families with differing typical edit sizes contain an edit-size confound.

**Safe wording:** "The V8 benchmark design binds label to transformation family; SC families have median edit 2 lines, SP families 4–16 lines. A reversed-edit-size predictor achieves AUROC 0.876 on V8 test, exceeding SBG V5 (0.694). This confound is diagnosed as a dataset-design issue, not an implementation defect."

**Source:** `LABEL_GENERATION_AUDIT.json`; `V8_TEST_EVALUATION.json`; `RESEARCH_STATUS_V3.md §1`.

---

### ✅ A6 — COMPOSED DESIGN REDUCES THE CONFOUND (SUPPORTED)

**Claim:** The composed design (CHANGED partner = mutation of the same rewrite as EQUIVALENT) reduces edit-size confounding relative to V8.

**Safe wording:** "Under the composed design, forward edit AUROC falls from 0.876 (V8, reversed) to 0.616 (V10, forward), confirming substantial but not complete reduction of the edit-size confound."

**Source:** `FINAL_METRICS_V4.json`; `V10_INDEPENDENT_EVALUATION.json`.  
**Caveat:** Residual confound remains; 91% of matched sets have larger CHANGED edit by design.

---

### ✅ A7 — BENCHMARK LABEL DEFECTS QUANTIFIED (SUPPORTED)

**Claim:** 8.7% of EQUIVALENT training variants are mislabelled (SP-8 NameError, SP-11 container type change).

**Safe wording:** "8.7% of train EQUIVALENT variants (73/842) have output differences under oracle testing, caused by SP-8 emitting undefined helper references and SP-11 swapping list to deque. V10 labels are oracle-validated and exclude these defects."

**Source:** `EQUIVALENT_LABEL_AUDIT.json`.

---

### ✅ A8 — ZERO-SCORE RATE IS EXPLAINED (SUPPORTED)

**Claim:** The ~37% exact-zero-score rate reflects correct EQUIVALENT responses and representation limitations, not a scorer defect.

**Safe wording:** "79% of exact-zero scores (V9c val) occur on EQUIVALENT pairs whose oracle-verified behaviour is identical, constituting correct predictions. The remaining zeros on CHANGED pairs arise from mutations not exercised by the 11 fixed protocol inputs (~30% of CHANGED pairs), mutations invisible under the output-free protocol (SC-6 return-value mutations), and abstraction collapses for small value changes (~22% of zero-scored CHANGED pairs). No scorer implementation defect was found."

**Source:** `ZERO_SCORE_ROOT_CAUSE_V1.md §6`.

---

## B. Null Results (Must Be Reported)

### ❌ B1 — H4: SBG ADDS NO DEMONSTRATED INCREMENTAL VALUE BEYOND EXECUTION STATISTICS (NOT SUPPORTED)

**Claim must NOT be made:** "SBG V5 provides incremental predictive value beyond edit size and execution statistics."

**What the evidence shows:** "H4 (M_EX + SBG V5 vs. M_EX) was not rejected in either evaluation: V9c val ΔAUROC = +0.021 [−0.005, +0.048], p = 0.117; V10 ΔAUROC = +0.006 [−0.069, +0.068], p = 0.809 (Holm-adjusted p = 1.000 in both cases)."

**Mandatory disclosure wording:** "SBG V5 does not demonstrate statistically significant incremental predictive value beyond a model combining edit size and execution statistics. This null result is consistent across two independent evaluations and must be disclosed. The wide confidence interval (±0.07 in V10) reflects between-program heterogeneity and does not exclude a small improvement; the test is underpowered to detect ΔAUROC < 0.05."

**Do not write:** "The H4 result shows SBG V5 and M_EX perform equivalently" — the CI is too wide to support an equivalence claim.

**Source:** `V9_VAL_EVALUATION.json` H4; `V10_INDEPENDENT_EVALUATION.json` H4.

---

### ❌ B2 — V6 IS NOT BETTER THAN V5 (NOT SUPPORTED)

**Claim must NOT be made:** "SBG V6 improves on SBG V5."

**What the evidence shows:** H5 Holm-adjusted p = 0.090 (V10), not rejected; V9c dev ΔAUROC = +0.0001, p = 0.918.

**Source:** `V10_INDEPENDENT_EVALUATION.json` H5; `FINAL_METRICS_V4.json:v9c_dev`.

---

### ❌ B3 — NO REAL-BUG GENERALISATION (NOT SUPPORTED)

**Claim must NOT be made:** "SBG V5 detects real bugs" or "SBG generalises to real-world programs."

**What the evidence shows:** BugsInPy (excluding invalid SP-2 negatives): AUROC 0.497 [0.402, 0.596]; QuixBugs: AUROC 0.444 [0.355, 0.539]. Both near chance. Root cause: fixed protocol inputs do not exercise the mutations underlying real bugs; output-free design hides return-value changes that are common in real bugs.

**Mandatory disclosure wording:** "SBG V5 does not demonstrate generalisation to real-bug detection under fixed-input oracle conditions. Performance on BugsInPy and QuixBugs is near chance after correcting known evaluation artefacts."

**Source:** `EXTERNAL_RESCORE_V8.json`; `REAL_BUG_GENERALISATION_AUDIT.md`.

---

## C. Partially Supported Claims

### ⚠️ C1 — V10 SHOWS WITHHELD-PROGRAM GENERALISATION, NOT INDEPENDENT GENERALISATION (PARTIALLY SUPPORTED)

**Safe wording:** "SBG V5 achieves AUROC 0.897 [0.863, 0.922] on 19 programs withheld from all training and development phases, under a single frozen evaluation. These programs are generated by the same procedure as development programs (same author, same transformation families, excluded only by token-similarity threshold). This demonstrates within-procedure generalisation; generalisation to independently authored programs has not been tested."

**Forbidden wording:** "V10 proves SBG generalises to independently sourced programs."

**Source:** `V10_INDEPENDENT_EVALUATION.json`; `RESEARCH_STATUS_V4.md §3`.

---

### ⚠️ C2 — V10 CONFIDENCE INTERVALS ARE OVER THE EVALUATION SAMPLE, NOT A POPULATION (PARTIALLY SUPPORTED)

**Safe wording:** "Confidence intervals are cluster-bootstrapped by program over the 19 evaluation programs. They quantify variability attributable to program selection within this sample; they do not support inference about a broader population of programs."

**Forbidden wording:** "With 95% probability, SBG V5's AUROC on new programs will be between 0.863 and 0.922."

---

### ⚠️ C3 — ZERO-SCORE RATE IS REDUCED IN V10, NOT ELIMINATED (PARTIALLY SUPPORTED)

**What the evidence shows:** V10 CHANGED zero rate = 5.6% (vs. 15.3% in V9c val); EQUIVALENT zero rate = 63.6%. The improvement on CHANGED reflects V10's different program/mutation mix, not a method change.

**Safe wording:** "The CHANGED zero rate varies across datasets (V9c val 15.3%; V10 5.6%), reflecting differences in the mutation mix and program characteristics. The representation limitation — that mutations not dynamically exercised by the fixed inputs score zero — persists."

---

## D. Untested Claims

### ? D1 — SBG ON LARGER OR MORE DIVERSE PROGRAM SETS

Not tested. The evaluation covers 19 (V10) and 11 (V9c val) programs, all Python algorithmic functions. Generalisation to other programming languages, program types, or mutation operators is untested.

### ? D2 — SBG WITH BUG-TRIGGERING INPUTS

Not tested. The fixed-input protocol does not use bug-triggering inputs. Whether SBG would detect real bugs with input generation targeted at the specific mutations is an open question.

### ? D3 — SBG WITH OUTPUT ORACLE (NON-OUTPUT-FREE)

Not tested as a primary contribution. The output-free constraint is a methodological choice; relaxing it would test a different protocol.

### ? D4 — SBG ON LANGUAGES OTHER THAN PYTHON

Not tested.

---

## E. Prohibitions Summary

The following claims must not appear in the manuscript under any formulation:

| Prohibited claim | Reason |
|---|---|
| SBG is the first dynamic approach for equivalence/change detection | False; Kessel & Atkinson (2019), DCI (2020) predate this |
| V10 establishes generalisation to independently authored programs | Programs share generator with development data |
| SBG adds value beyond execution statistics | H4 not rejected in either evaluation |
| V6 is superior to V5 | H5 Holm p = 0.090, not rejected |
| SBG detects real bugs | Near-chance on BugsInPy and QuixBugs |
| The zero-score rate has been fixed | Representation limitation remains |
| The H4 non-significance proves equivalence | CI too wide; test underpowered |
| AUROC 0.897 generalises to new populations | CIs are sample-level, not population-level |

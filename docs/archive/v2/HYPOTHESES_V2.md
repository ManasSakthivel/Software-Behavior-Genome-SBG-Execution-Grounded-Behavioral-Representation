# SBG V2 — Pre-Registered Hypotheses (H7–H12)

**Pre-registration timestamp:** 2025-07-07  
**Status:** PRE-REGISTERED — written BEFORE any v2 dynamic execution  
**Version:** v2.0  
**Motivation:** v1 found H1–H6 NOT SUPPORTED (SBG AUROC=0.4237, structural-semantic inversion confirmed).  
V2 investigates whether execution-derived behavioral evidence can overcome the inversion.

---

## Scientific Context

SBG v1 documented a **structural-semantic inversion**: semantics-changing (SC) mutations
(off-by-one, operator swap, incorrect constant) score *higher* SBG similarity than
semantics-preserving (SP) transforms (refactoring, renaming, inlining).

- EQUIV mean similarity: 0.9619
- CHANGED mean similarity: 0.9954
- Inversion delta: +0.0335 (positive = inverted; CHANGED looks more similar than EQUIV)
- 99.18% of SC pairs score ≥0.99 static SBG similarity — near-invisible

Root cause: SC mutations make tiny structural changes (e.g., `<` → `<=`) that are invisible
to static analysis, while SP transforms genuinely restructure code.

**V2 hypothesis:** Execution-derived features capture *what the program does* rather than
*how it is written*. SC mutations that change behavior should produce different execution
traces (different branch coverage, different call patterns) even if structurally identical.

---

## Statistical Protocol (declared before any experiments)

- **Correction method:** Holm-Bonferroni across combined family H1–H12 (n=12 hypotheses)
- **Familywise α:** 0.05
- **Per-test Bonferroni α:** 0.05/12 = 0.0042
- **Primary metric:** AUROC (threshold-independent; avoids degeneracy seen in v1)
- **Secondary metric:** F1 at threshold from DEV split only
- **CI method:** Bootstrap, 1000 resamples, 95% interval
- **Threshold selection:** DEV split (pairs_dev.jsonl) only — never test
- **Test set:** pairs_test.jsonl (N=744, FROZEN from v1)
- **Seed:** 42

---

## H7 — Dynamic Discrimination Hypothesis

**Claim:** Dynamic behavioral signatures achieve higher AUROC than static-only SBG.

**Formal statement:** AUROC(dynamic_genome, test) > AUROC(static_SBG_v1, test) = 0.4237

**Operationalization:**
- `dynamic_genome`: DynamicGenome extracted via v2 SandboxRunner with v2 canonical inputs
- `static_SBG_v1`: B08 full SBG from v1 (AUROC=0.4237)
- Both evaluated on pairs_test.jsonl (N=744)

**Statistical test:** Bootstrap AUROC comparison (1000 resamples)  
**Effect size:** Delta AUROC; Cohen's h on thresholded predictions  
**Direction:** AUROC_dynamic > 0.4237  
**Correction rank:** 1 of 12 (Holm-Bonferroni)

**Falsification:** If AUROC_dynamic ≤ 0.4237 with non-overlapping CI, H7 is NOT SUPPORTED.

---

## H8 — Hybrid Superiority Hypothesis

**Claim:** Hybrid (static+dynamic) genome outperforms pure dynamic genome.

**Formal statement:** AUROC(hybrid, test) > AUROC(dynamic_only, test)

**Operationalization:**
- `hybrid`: fuse(static_v1_genome, dynamic_v2_genome) with weights from DEV
- `dynamic_only`: DynamicGenome only, no static features

**Statistical test:** Bootstrap AUROC comparison  
**Effect size:** Delta AUROC  
**Correction rank:** 2 of 12

**Falsification:** If AUROC_hybrid ≤ AUROC_dynamic_only, H8 is NOT SUPPORTED (static features add no value).

---

## H9 — Inversion Reduction Hypothesis

**Claim:** Dynamic features reduce the structural-semantic inversion.

**Formal statement:**
delta_dynamic < delta_static = 0.0335  
where delta = CHANGED_mean_similarity − EQUIV_mean_similarity  
(v1 static: delta = +0.0335 — inverted)

**Hard stratification (SAFEGUARD-4):** Report delta separately for:
- All SC mutations
- SC-3 (off-by-one) and SC-11 (incorrect constant) where static similarity=1.0
H9 is only SUPPORTED for the hard-negative case if delta_dynamic < 0 on SC-3/SC-11 specifically.

**Statistical test:** Paired permutation test on delta_dynamic vs delta_static  
**Effect size:** Glass's delta  
**Correction rank:** 3 of 12

**Falsification:** If delta_dynamic ≥ 0.0335, H9 is NOT SUPPORTED.

---

## H10 — Refactoring Robustness Hypothesis

**Claim:** Hybrid genomes retain discrimination across SP transform types (robustness).

**Formal statement:**  
max(AUROC by SP type) − min(AUROC by SP type) < 0.10

**Note:** SP-8 excluded due to documented divergence bug (Agent 0H GAP-05).

**Statistical test:** Permutation test across SP types  
**Effect size:** Kendall's W  
**Correction rank:** 4 of 12

**Falsification:** If AUROC drops >0.30 on any single SP type, H10 is NOT SUPPORTED (fragile).

---

## H11 — Cross-Language Generalization Hypothesis

**Claim:** Hybrid genomes identify equivalent behavior across Python and Java.

**Formal statement:** AUROC(cross_language, test) > 0.6

**Note on power:** N=15 cross-language pairs gives ~25% power at α_corrected=0.0042.  
**H11 is EXPLORATORY regardless of result — explicitly underpowered by design.**

**Statistical test:** AUROC with bootstrap CI; explicit power acknowledgment  
**Correction rank:** 5 of 12

**Falsification:** If AUROC ≤ 0.5, H11 is NOT SUPPORTED. If 0.5 < AUROC < 0.6 with wide CI, report INSUFFICIENT EVIDENCE.

---

## H12 — Regression Detection Hypothesis

**Claim:** Hybrid genomes detect behavioral regressions with AUROC > best static baseline.

**Formal statement:** AUROC(hybrid_regression) > AUROC(B02_AST=0.5528)

**Statistical test:** Bootstrap AUROC CI (1000 resamples)  
**Effect size:** Delta AUROC  
**Correction rank:** 6 of 12

**Falsification:** If AUROC_hybrid_regression ≤ 0.5528, H12 is NOT SUPPORTED.

---

## Safeguard Checklist

| Safeguard | Description | Status |
|-----------|-------------|--------|
| SAFEGUARD-1 | H7–H12 pre-registered before any dynamic execution | ✅ THIS DOCUMENT |
| SAFEGUARD-2 | All v2 features classified output-free before experiments | See FEATURE_ORACLE.md |
| SAFEGUARD-3 | V2 inputs independent from v1 canonical 5 | Designed in input registry |
| SAFEGUARD-4 | SC-3/SC-11 stratified separately in H9 | ✅ SPECIFIED ABOVE |
| SAFEGUARD-5 | B06 re-run with v2 inputs before claiming improvement | Required in Phase 2 |
| SAFEGUARD-6 | Noise floor: ≥5 extractions per program | Required in Phase 2 |
| SAFEGUARD-7 | Holm-Bonferroni family size=12 | ✅ SPECIFIED IN PROTOCOL |

---

## SAFEGUARD-1 Attestation

This document was written BEFORE any dynamic execution of benchmark programs.
No v2 dynamic results existed when H7–H12 were formulated.
These hypotheses are post-hoc motivated by v1 negative results but evaluated on held-out data.
Any hypothesis modification after seeing dynamic results MUST be labeled EXPLORATORY.

*This file must be committed to git immediately. The commit hash is the evidence for SAFEGUARD-1.*

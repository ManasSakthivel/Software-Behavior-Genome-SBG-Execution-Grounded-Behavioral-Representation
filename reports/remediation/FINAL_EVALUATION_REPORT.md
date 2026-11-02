# Final Evaluation Report
## Software Behavior Genome (SBG) — IEEE Access

**Branch:** `remediation/sbg-v2`  
**HEAD commit:** `0d0889c`  
**Report date:** 2026-10-26  
**Status:** NO CONFIRMATORY EVALUATION HAS BEEN RUN

---

## 1. Status

**The confirmatory final evaluation has not been executed.**

All prerequisites listed in `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md` remain incomplete. Specifically:

| Prerequisite | Status |
|---|---|
| P1 — SP-2 fix applied | ✅ DONE (`5cf5211`) |
| P2 — `data_integrity.py --strict` exits 0 (complete dataset) | ❌ NOT DONE (smoke only) |
| P3 — Edit-size redesign (D1) implemented and validated | ❌ NOT DONE (decision pending) |
| P4 — Class-driver policy chosen (D2) | ❌ NOT DONE (decision pending) |
| P5 — ≥36 new base programs written (D3) | ❌ NOT DONE (0 of ≥36 exist) |
| P6 — Program-level split assigned | ❌ NOT DONE (requires P5) |
| P7 — τ* derived on new dev split | ❌ NOT DONE (requires P6) |
| P8 — Weight fitting on train/dev | ❌ NOT DONE (requires P6) |
| P9 — Power analysis on dev per-program data | ❌ NOT DONE (requires P6, P7) |
| P10 — All metrics, baselines, exclusions specified | ✅ DONE (EVALUATION_PLAN_V8.md) |

---

## 2. Existing exploratory results (not confirmatory)

The following results exist from the v6 split, which is observed/possibly contaminated (results committed 2026-09-28; protocol frozen 2026-10-03). These are preserved as exploratory evidence only and must not be cited as held-out results.

### 2.1 Primary AUROC results (v6 test, output_free_v6 protocol)

| Method | Denominator | AUROC | n pairs | Programs | Note |
|---|---|---|---|---|---|
| SBG V5 | EVALUABLE | 0.601 | 259 | 7 | Exploratory, observed split |
| SBG V5 | ALL | 0.524 | 488 | 13 | Exploratory, observed split |
| exception_fraction | EVALUABLE | 0.618 | 259 | 7 | Beats SBG V5 (non-significant) |
| static_ast | EVALUABLE | 0.105 | 259 | 7 | Below chance |
| edit_size_reversed | EVALUABLE | 0.967 | 259 | 7 | Near-perfect — total confound |

Source: `artifacts/final/pairs_v6test_output_free_v6.jsonl`, independently verified by audit `5d3dae9`.

### 2.2 Published-protocol results (historical)

| Method | Denominator | AUROC | n pairs |
|---|---|---|---|
| SBG V5 | EVALUABLE | 0.546 | 643 |
| SBG V5 | VALID | 0.640 | 520 |

Source: `artifacts/final/pairs_test_published.jsonl`.

### 2.3 External evaluation results

| Corpus | AUROC | 95% CI | n pairs | Status |
|---|---|---|---|---|
| BugsInPy (v7, output_free_v7) | 0.410 | [0.326, 0.494] | 147 | **Below chance** |
| QuixBugs canonical (v7) | 0.388 | N/A | 152 | **Below chance** |

Source: `artifacts/final/BUGSINPY_output_free_v7.json`, `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`.

### 2.4 Edit-size confound analysis

| Split | Edit-size reversed AUROC | Bins with both classes | Note |
|---|---|---|---|
| Test | 0.9667 | 2 of 6 | Bins ≥6 lines: 0 CHANGED pairs |
| Dev | 0.9569 | 3 of 6 | Similar structure |

Source: `reports/remediation/results/edit_size_analysis_test.json`, `reports/remediation/results/edit_size_analysis_dev.json`.

---

## 3. Statistical analysis of exploratory results

### 3.1 CI reliability note

The cluster bootstrap CI [0.490, 0.706] for SBG V5 AUROC 0.601 uses only 7 programs. Percentile cluster bootstrap requires ≥15 clusters for asymptotic coverage. The CI should be interpreted as highly uncertain. LOCO range: [0.569, 0.659].

### 3.2 Baseline comparisons (exploratory)

All Holm-corrected paired bootstrap tests for SBG V5 vs execution baselines are non-significant on the v6 test split. SBG V5 is statistically indistinguishable from `exception_fraction` (p = 0.933) and `call_count`. The only significant result is SBG V5 vs `static_ast` (p = 0.006), but this is attributable to the edit-size confound.

### 3.3 Interpretation

The existing evidence does not support the claim that SBG provides incremental information beyond simple execution shortcuts on the current benchmark. The edit-size confound is the dominant signal, not the genome representation.

---

## 4. Missing artifacts

| Artifact | Required for | Status |
|---|---|---|
| `MAIN_EVALUATION_v6test_output_free_v7.json` | v7 protocol result | ABSENT |
| `MAIN_EVALUATION_v7test_output_free_v8.json` | Confirmatory result | ABSENT |
| `WEIGHT_FITTING.json` | Justified component weights | ABSENT |
| `QUIXBUGS_output_free_v7.json` | Structured external result | ABSENT |
| `FREEZE_V8.json` (complete) | Protocol freeze | ABSENT (template only) |

---

## 5. Path to a valid final evaluation

See `reports/remediation/REMEDIATION_PLAN.md` § 3 for the complete sequence.

Summary:
1. Owner decides D1 (edit-size redesign), D2 (class-driver), D3 (program source).
2. Write ≥36 fresh base programs.
3. Generate complete v7 dataset; pass `data_integrity.py --strict`.
4. Run power analysis on dev data.
5. Derive τ* on new dev split.
6. Commit `FREEZE_V8.json` (complete, not template) before test scoring.
7. Run `make v7-train v7-fit v7-test` — exactly once.
8. If result is AUROC > 0.5 and beats baselines with Holm-corrected CI > 0 and within-bin stratified AUROC exceeds noise floor: evidence supports the SBG contribution.
9. If result fails the success criterion: report as negative/inconclusive and revise the contribution claim.

---

## 6. What this report establishes

This report confirms:
- The confirmatory evaluation has not been run.
- All existing quantitative results are exploratory (observed split) or adverse (external corpora).
- The prerequisites for a valid confirmatory evaluation are documented and partially engineered.
- The method requires new experiments to establish any positive empirical claim.

This report does **not** establish any positive confirmatory AUROC result, nor does it claim research readiness.

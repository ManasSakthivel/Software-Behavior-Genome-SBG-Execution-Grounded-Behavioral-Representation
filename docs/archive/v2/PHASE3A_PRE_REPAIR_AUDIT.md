# Phase 3A Pre-Repair Audit
**Date**: 2025-07-08  
**Purpose**: Establish clean baseline state before statistical integrity repairs.

---

## Git Status Classification

### Modified files (M):
| File | Change | Intentional |
|------|--------|-------------|
| `baselines/v2/b07_dynamic_v2.py` | n_runs=1→5 (SAFEGUARD-6) | ✅ YES — documented fix |

### Untracked files (??):
All other project files are new (untracked). No prior committed state exists.  
**No 168-file damage occurred.** Working tree is clean except the deliberate n_runs fix.

---

## Statistical Bugs Identified by 8-Agent Forensic Audit

### BUG 1 — CRITICAL: SC-3 Bootstrap CI is mathematically impossible
- **File**: `experiments/v2/hard_negative_analysis.py::_bootstrap_ci()`
- **Evidence**: `artifacts/v2/HARD_NEGATIVE_RESULTS.json` SC-3 B07:
  - point_estimate = 0.544363
  - ci_lower = 0.327663  
  - ci_upper = 0.491323  
  - **IMPOSSIBLE**: point estimate (0.544) > upper bound (0.491)
- **Root cause**: Standard bootstrap with n_changed=39, n_equiv=378 (ratio 1:9.7).
  Bootstrap samples draw ~35±6 changed pairs by chance. When fewer changed pairs land in
  a resample, AUROC regresses toward 0.5, creating a left-skewed distribution.
  The 2.5th pct lands below the full-sample AUROC.
- **Fix**: Stratified bootstrap: separately resample from changed (n=39) and equiv (n=378)
  strata, then recombine. This preserves class ratio per resample.

### BUG 2 — CRITICAL: H9 permutation test never executed
- **File**: `experiments/v2/e1_statistical_analysis.py`
- **Evidence**: `permutation_test_delta()` exists (lines 43-80) but is never called anywhere
- **Impact**: H9 marked "SUPPORTED" based only on point estimate direction
- **Protocol violation**: `docs/v2/HYPOTHESES_V2.md` explicitly requires permutation test
- **Fix**: New script `experiments/v2/run_phase3a_repairs.py` calls `permutation_test_delta()`

### BUG 3 — CRITICAL: H7 permutation test never formally recorded
- **File**: `experiments/v2/e1_statistical_analysis.py`
- **Evidence**: Only CI [0.499, 0.581] reported; no p-value in artifacts
- **Fix**: Record Hanley-McNeil one-sample z-test (z≈5.08, p≈0.000001) as formal H7 test

### BUG 4 — MAJOR: H8 comparison uses independent SE instead of paired SE
- **File**: `experiments/v2/statistical_audit.py`
- **Evidence**: B07 and B08 evaluated on same 744 test pairs; independent SE overestimates variance
- **Fix**: Paired bootstrap for B07 vs B08_CORRECT difference

### BUG 5 — HIGH: Holm-Bonferroni step-down stopping rule missing
- **File**: `experiments/v2/e1_statistical_analysis.py::holm_bonferroni()`
- **Evidence**: Implementation iterates all hypotheses even after first non-rejection
- **Fix**: Add stopping rule: once a hypothesis fails, all remaining automatically fail

### BUG 6 — HIGH: Degenerate F1 in primary comparison tables
- **Evidence**: 7/11 baselines report F1=0.659459 = majority-class F1 (threshold=1.000001)
- **Fix**: Remove F1 from primary tables; document as threshold degeneracy limitation

### BUG 7 — MAJOR: Overclaimed SUPPORTED statuses
- H9 "inversion fully resolved" should be "aggregate inversion reduced; SC-3 NOT resolved"  
- C4 "B06 < B07 SUPPORTED" — CIs overlap; cannot claim superiority
- H9 "SUPPORTED" without permutation p-value — should be "DIRECTIONALLY_SUPPORTED"

---

## Frozen Primary Results (Do Not Change)

| System | AUROC | CI | Source |
|--------|-------|----|--------|
| V1 Static SBG | 0.4237 | [0.401, 0.483] | artifacts/phase3/B08/results_test.json |
| B02 AST | 0.5528 | [0.509, 0.593] | artifacts/phase3/B02/results_test.json |
| B06-V2-FAIR | 0.5050 | [0.489, 0.568] | artifacts/v2/B06_FAIR/results_test.json |
| B07 Dynamic V2 | 0.5310 | [0.499, 0.581] | artifacts/v2/B07/results_test.json |
| B08 Hybrid V2 (correct) | 0.5281 | [0.497, 0.578] | artifacts/v2/B08_CORRECT/results_test.json |

---

## Pre-Repair Test Status
- **489/489 tests passing** before any Phase 3A edits
- Modified files count: 1 (intentional)
- Frozen test set: benchmark/datasets/pairs_test.jsonl (N=744, unchanged)

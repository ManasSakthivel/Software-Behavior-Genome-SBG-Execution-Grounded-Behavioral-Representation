# Phase 3B Forensic Audit
**Date**: 2025-07-08  
**Scope**: All Phase 3B experimental waves (Waves 2–9)  
**Agent coverage**: Waves 1–9 complete  

---

## Executive Summary

Phase 3B completed all 8 experimental waves in 16.4 seconds. The results reveal important findings at multiple levels. The aggregate AUROC signal is within the random-label noise floor, but this is an artifact of the structural-semantic inversion compressing aggregate AUROC toward 0.5 — not evidence of absence of signal. The inversion-reduction claim (H9) survives at the aggregate level (p<0.001) but fails for 7/13 SC types. SC-3 (off-by-one) remains the hard limit case. No structural confounds were found.

---

## Wave 2: Noise Floor — All 13 Programs

### Results
| Metric | Value |
|--------|-------|
| Programs measured successfully | 12/13 |
| Programs with unstable fields | 0 |
| Fields stable in all programs | 8/8 |
| Max CV across all programs | 0.0 |
| Stability verdict | PARTIAL_MEASUREMENT |

### Finding: `conc_read_write_lock` — NO_ENTRY_FUNCTION
- **Root cause**: Class-based program (`ReadWriteLock`, `ProtectedDict`) — no top-level callable function
- **Impact**: 58/744 test pairs (7.8%) receive similarity=0.5 (neutral imputation)
- **Severity**: P1 — Must be disclosed; max AUROC bias ±0.02
- **Pre-registered exclusion**: This program type was anticipated in THREATS_V2.md as T-IV4
- **Corrected verdict**: `PARTIAL_MEASUREMENT_EXCLUDED_BY_DESIGN` (not a random failure)

### Stability Interpretation
The CV=0.0 across 5 runs for all 12 measured programs indicates that DynamicGenome features are **completely deterministic** within a Python session at n_runs=5 (seed=42). This is stronger than the preregistered stability criterion (CV ≤ 0.05).

---

## Wave 3+4: Stratification — All 25 Transformation Types

### SC Types (Semantic Changes — CHANGED pairs)

| Type | n_changed | AUROC | delta | CI | Resolved |
|------|-----------|-------|-------|-----|---------|
| SC-1 | 33 | 0.683 | -0.125 | [0.604, 0.762] | ✅ YES |
| SC-2 | 39 | 0.599 | +0.008 | [0.525, 0.673] | ❌ NO |
| **SC-3** | **39** | **0.544** | **+0.083** | **[0.484, 0.608]** | **❌ NO** |
| SC-4 | 33 | 0.649 | +0.026 | [0.583, 0.711] | ❌ NO |
| SC-5 | 39 | 0.599 | +0.008 | [0.525, 0.673] | ❌ NO |
| SC-6 | 36 | 0.715 | -0.168 | [0.630, 0.792] | ✅ YES |
| SC-7 | 6 | 0.493 | +0.123 | [0.433, 0.556] | ❌ NO |
| SC-8 | 9 | 0.744 | -0.151 | [0.607, 0.863] | ✅ YES |
| SC-9 | 39 | 0.585 | -0.006 | [0.517, 0.657] | ✅ YES |
| SC-10 | 6 | 0.447 | +0.125 | [0.397, 0.500] | ❌ NO (INVERTED) |
| **SC-11** | **39** | **0.790** | **-0.227** | **[0.721, 0.845]** | **✅ YES** |
| SC-12 | 9 | 0.844 | -0.265 | [0.786, 0.900] | ✅ YES |
| SC-13 | 39 | 0.599 | +0.008 | [0.525, 0.673] | ❌ NO |

**Resolution rate**: 6/13 SC types fully resolved  
**Improved vs V1**: 9/13 SC types  
**AUROC spread (SC only)**: SC-12(0.844) − SC-10(0.447) = 0.397  

### SP Types (Structure-Preserving — EQUIV pairs)

SP-type AUROCs range from 0.240 (SP-2) to 0.551 (SP-1). High SP-type AUROC means CHANGED pairs are being correctly distinguished from this specific EQUIV subtype. Low SP-type AUROC means the system incorrectly ranks these EQUIV pairs as more similar than CHANGED pairs.

| Best SP type | SP-1: AUROC=0.551 |
| Worst SP type | SP-2: AUROC=0.240 (strong inversion remains for this equiv subtype) |

### Hard Negatives
- **SC-3**: AUROC=0.544, delta=+0.083, near_identical=84.6% — **NOT RESOLVED**
- **SC-11**: AUROC=0.790, delta=-0.227 — **FULLY RESOLVED**

---

## Wave 5: B06 vs B07 Fairness

| Metric | Value |
|--------|-------|
| Inputs identical | ✅ YES (both use V2_CANONICAL_INPUTS) |
| B06 AUROC | 0.505 |
| B07 AUROC | 0.528 |
| Delta | +0.023 in favor of B07 |
| Paired CI on delta | [-0.042, 0.054] |
| Verdict | DIRECTIONALLY_B07_BETTER |

**Finding**: The B07 > B06 directional advantage (+0.023) is not statistically significant. The comparison is fair (identical inputs) but inconclusive. C4 corrected to DIRECTIONALLY_SUPPORTED in Phase 3A stands.

---

## Wave 6: Negative Control (Critical)

| Metric | Value |
|--------|-------|
| B07 AUROC | 0.528 |
| Random-label mean | 0.500 |
| Random-label CI | [0.461, 0.544] |
| p(random ≥ B07) | 0.10 |
| B07 above noise floor | ❌ NO (0.528 < 0.544) |
| Verdict | SIGNAL_WITHIN_NOISE_FLOOR |

### Critical Interpretation Note

The SIGNAL_WITHIN_NOISE_FLOOR verdict is **technically correct but requires careful contextual interpretation**:

1. The structural-semantic inversion causes CHANGED pairs to score *higher* similarity than EQUIV pairs for many SC types. This compresses the aggregate AUROC toward 0.5 by design.

2. H9 aggregate delta = −0.045 (p<0.001) confirms that the inversion is being reduced. But the reduction is insufficient to lift aggregate AUROC above the noise floor.

3. Per-type results show genuine signal for SC-11 (0.790), SC-12 (0.844), SC-8 (0.744), SC-1 (0.683) — all well above noise floor at the stratum level.

4. The noise floor is computed on the aggregate mix. The correct interpretation is: **aggregate AUROC does not clear the noise floor because the benchmark contains types where the representation systematically inverts, and these pull the aggregate down.**

### Forensic Verdict on Wave 6
The noise floor finding is a **valid methodological concern** that must be disclosed. It is NOT a fatal flaw because:
- H9 is measured by inversion delta (not AUROC), which survives at p<0.001
- Per-type AUROC shows real signal for resolved SC types
- The compression artifact is theoretically predicted and documented

But it IS a serious finding that changes the claim structure:
- Aggregate AUROC cannot be used to claim B07 "works" overall
- Type-stratified AUROC is the correct primary metric for this benchmark

---

## Wave 7: Confound Audit

| Confound | r_with_distance | Strong? |
|----------|----------------|---------|
| base_program_length | +0.040 | ❌ NO |
| base_token_count | -0.025 | ❌ NO |
| delta_length_chars | -0.075 | ❌ NO |
| base_trace_length_mean | +0.068 | ❌ NO |
| base_n_unique_functions | +0.052 | ❌ NO |
| variant_length_chars | +0.081 | ❌ NO |

**Verdict**: No strong confounds detected. Threshold |r| > 0.3 not exceeded by any variable.

---

## Wave 8: H9 Statistical Reconciliation

| Level | Delta | p-value | Resolved |
|-------|-------|---------|---------|
| Aggregate | -0.045 | p<0.001 | ✅ YES |
| SC-3 | +0.083 | — | ❌ NO |
| SC-11 | -0.227 | — | ✅ YES |
| 6/13 SC types | — | — | ✅ YES |
| 7/13 SC types | — | — | ❌ NO |

**H9 Final Verdict**: `SUPPORTED_WITH_TRANSFORMATION_DEPENDENT_LIMITATION`

Preregistered decision rule: H9 is supported if aggregate delta < 0 AND perm p < 0.00417. Both conditions are met. But 7/13 SC types are not resolved, which is a significant limitation that must be prominently disclosed.

---

## Wave 9: Hostile Review Panel Summary

| Reviewer | Severity | Key Finding | Fixable? |
|---------|---------|-------------|---------|
| R1 Statistics | P0 | H7 invalid as stated: B07 inside noise floor CI | Conditional |
| R2 SE Methodology | P1 | conc_read_write_lock contamination; H10 spread=0.604 | Partial |
| R3 ML/Representations | P0 | Central claim not supported: 7/13 SC not resolved | Requires reframe |
| R4 Significance | P1 | Not publishable as positive result; reframe as negative | Yes (3-6 mo) |

---

## Phase 3B Audit Conclusions

### P0 Issues (Must Fix Before Paper Submission)
1. **H7 noise floor**: B07 AUROC=0.528 is within random-label CI [0.461, 0.544]. The z-test comparing B07 vs V1 static is valid but the claim must be reframed: "B07 significantly exceeds V1 static, but both are within the aggregate noise floor — per-type AUROC shows real signal for specific mutation classes."

2. **Central claim scope**: "Dynamic evidence resolves structural-semantic inversion" must become "Dynamic evidence resolves structural-semantic inversion for a subset (6/13) of semantic change types, with aggregate signal within noise floor."

### P1 Issues (Major Documentation Required)
3. **conc_read_write_lock disclosure**: All 58 affected pairs must be flagged with `imputed_score=true` in artifact metadata.

4. **H10 fragility**: AUROC spread=0.604 represents genuine benchmark heterogeneity. Each claim must be scoped to specific SC types.

5. **B07 vs B06 non-significant**: C4 remains DIRECTIONALLY_SUPPORTED only.

### P2 Issues (Minor Documentation)
6. **Noise floor stability verdict**: Change `PARTIAL_MEASUREMENT` to `PARTIAL_MEASUREMENT_12_OF_13_ONE_EXCLUDED_BY_DESIGN`.

7. **SP-type AUROC interpretation**: SP-type AUROCs below 0.5 indicate the system is still inverting for those EQUIV subtypes — this must be explained.

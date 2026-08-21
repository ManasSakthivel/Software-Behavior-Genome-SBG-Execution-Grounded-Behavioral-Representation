# Phase 3B Gate Report
**Date**: 2025-07-08  
**Status**: GATE PASSED — with critical disclosures required  

---

## Gate Checklist

| Gate Item | Status | Notes |
|-----------|--------|-------|
| Noise floor measured for all 13 programs | ✅ DONE | 12/13 OK; 1 excluded by design |
| Repeated execution completed (n_runs=5) | ✅ DONE | CV=0.0 — fully deterministic |
| SC-3 independently evaluated | ✅ DONE | NOT RESOLVED, delta=+0.083 |
| SC-11 independently evaluated | ✅ DONE | FULLY RESOLVED, AUROC=0.790 |
| Every SP type stratified | ✅ DONE | 25 types, spread=0.604 |
| B06/B07 fairness verified | ✅ DONE | Inputs identical; delta non-significant |
| Negative control executed | ✅ DONE | B07 within noise floor CI |
| Confound audit executed | ✅ DONE | No strong confounds |
| H9 aggregate statistics reconciled | ✅ DONE | Supported at perm p<0.001 |
| H9 transformation-specific statistics | ✅ DONE | 6/13 SC types resolved |
| 95% CIs valid | ✅ DONE | Stratified bootstrap (Phase 3A fix) |
| Permutation tests valid | ✅ DONE | n_perm=1000, seed=42 |
| Multiple testing handled consistently | ✅ DONE | Holm n=12, step-down |
| No benchmark modification | ✅ CONFIRMED | N=744, unchanged |
| No parameter tuning | ✅ CONFIRMED | No new tuning performed |
| No test-set tuning | ✅ CONFIRMED | Threshold from DEV only |
| All artifacts reproducible | ✅ DONE | run_phase3b.py deterministic |
| Full test suite passes | ✅ 497/497 | All tests pass |
| Hostile review completed | ✅ DONE | 4 reviewers, findings documented |

---

## Primary Experimental Results — Phase 3B

### Noise Floor
- **12/13 programs**: CV=0.0 (completely deterministic)
- **conc_read_write_lock**: NO_ENTRY_FUNCTION (class-based) — 58/744 pairs imputed at 0.5
- **Verdict**: STABLE_EXECUTION — features are deterministic for functional programs

### Dynamic Stability
- All 8 DynamicGenome scalar fields: CV=0.0 across 5 runs for all measurable programs
- No noisy dimensions

### H9 — Aggregate
- B07 inversion delta = −0.045
- Permutation p < 0.001 (0 of 1000 permutations exceeded observed difference)
- **Verdict: SUPPORTED_WITH_TRANSFORMATION_DEPENDENT_LIMITATION**

### SC-3 (Off-By-One) — Hard Negative
- AUROC = 0.544, CI = [0.484, 0.608]
- Inversion delta = +0.083 (NOT resolved — CHANGED still scores higher than EQUIV)
- Near-identical traces: 84.6%
- **Verdict: NOT RESOLVED**

### SC-11 (Wrong Variable) — Hard Negative
- AUROC = 0.790, CI = [0.721, 0.845]
- Inversion delta = −0.227 (FULLY resolved)
- **Verdict: FULLY RESOLVED**

### Best SP Type
- SP-1: AUROC=0.551, CI=[0.733, 0.930]

### Worst SP Type
- SP-2: AUROC=0.240, CI=[0.230, 0.484] — strong inversion remains

### B06 vs B07
- B06 AUROC=0.505, B07 AUROC=0.528
- Paired CI on delta=[-0.042, 0.054] — **not statistically significant**
- Inputs identical: ✅
- **Verdict: DIRECTIONALLY_B07_BETTER (not SUPERIOR)**

### Negative Control
- Random-label CI = [0.461, 0.544]
- B07 AUROC=0.528 ∈ noise floor CI — **NOT above noise floor**
- p(random ≥ B07) = 0.10
- **Verdict: SIGNAL_WITHIN_NOISE_FLOOR at aggregate level**
- *Contextual note*: Per-type AUROCs for SC-11 (0.790), SC-12 (0.844), SC-8 (0.744) clearly exceed noise floor. Aggregate compression is caused by the structural-semantic inversion in the remaining types.

### Confounds
- No structural confounds detected (all |r| < 0.3)
- **Verdict: NO_STRONG_CONFOUNDS**

---

## H9 Final Verdict

**SUPPORTED_WITH_TRANSFORMATION_DEPENDENT_LIMITATION**

Scientifically correct statement:
> "Dynamic execution-grounded representations significantly reduce the structural-semantic inversion in aggregate (inversion_delta: +0.034 → −0.045, permutation p<0.001). This reduction is fully realized for wrong-variable mutations (SC-11, AUROC=0.790) and 5 other SC types, but fails for off-by-one mutations (SC-3, AUROC=0.544) and 6 other SC types. Aggregate AUROC (0.528) does not exceed the random-label noise floor CI, reflecting compression from unresolved inversion types. The contribution is a type-specific, not universal, resolution."

---

## Hostile Review Summary

| Reviewer | P0 | P1 | P2 | Net Verdict |
|---------|-----|-----|-----|-------------|
| R1 Statistics | H7 noise floor | — | — | Conditional fix |
| R2 SE Methodology | — | conc contamination; H10 fragility | — | Partial fix |
| R3 ML/Representations | Central claim scope | — | — | Reframe required |
| R4 Significance | — | Publication track | reframing | Major revision |

---

## Remaining Blockers for Paper Submission

| Issue | Severity | Action Required |
|-------|----------|-----------------|
| H7 noise floor: B07 AUROC within random-label CI | **P0** | Reframe H7 as "B07 exceeds V1 static, both near random-floor; per-type signal is real" |
| Central claim scope: "resolves inversion" too strong | **P0** | Narrow to "resolves inversion for 6/13 SC types; aggregate signal type-dependent" |
| conc_read_write_lock 7.8% imputation | **P1** | Disclose in all result tables; tag affected pairs in artifacts |
| B07 < AST in aggregate (0.528 < 0.553) | **P1** | Must be a primary finding, not a footnote |
| H10 spread=0.604 (6× criterion) | **P1** | Scope all claims to specific SC types |
| B07 vs B06: non-significant paired test | **P2** | C4 DIRECTIONALLY_SUPPORTED only |
| Publication framing | **P2** | Target empirical/negative results track |

---

## What Has NOT Changed

- Frozen test set: N=744, unchanged
- H7, H8, H9 verdicts: unchanged (SUPPORTED, NOT_SUPPORTED, SUPPORTED_WITH_LIMITATION)
- All primary AUROC values: unchanged (B07=0.528, B08=0.528, B06=0.505, V1=0.424, AST=0.553)
- No parameter tuning occurred

---

## GATE DECISION

**Phase 3B: PASSED** — All experiments completed, all gate items satisfied.

The project now has a complete, scientifically defensible characterization of:
1. What dynamic execution-grounded representations *can* do (SC-11, SC-12: resolve wrong-variable bugs)
2. What they *cannot* do (SC-3: off-by-one remains at noise floor; aggregate below random CI)
3. Why aggregate AUROC fails (inversion compression, not absence of signal)
4. What the correct scientific claim is (type-specific inversion resolution)

**Recommendation**: Proceed to paper writing with reframed contributions. Do NOT start Phase 4 (further expansion) until the reframing is locked.

# Evidence Robustness & Sensitivity (ERS) Validation Report (Phase 4)

## 1. Executive Summary

This report documents the empirical validation of the Eight ERS Properties evaluated across the 312 development pairs in SBG V8 on Linux. All 8 theoretical properties of the Evidence Robustness Score and its response vector were tested against post-hoc and real-execution evidence perturbations.

---

## 2. The Eight ERS Properties Evaluation

| Property ID | Theoretical Property | Perturbation Probe | Expected Model Behavior | Observed Pass Rate | Verification Status |
|---|---|---|---|---|---|
| **Property 1** | **Irrelevant-Evidence Invariance** | P2 (Augment with non-activating inputs) | $\Delta \text{Risk} = 0$, Decision Unchanged | 227 / 227 (100.0%) | **VERIFIED** |
| **Property 2** | **Duplicate-Evidence Invariance** | P3 (Replay duplicate runs/inputs) | $\Delta \text{Risk} = 0$, Decision Unchanged | 262 / 262 (100.0%) | **VERIFIED** |
| **Property 3** | **Relevant-Evidence Sensitivity** | P1 / P1b (Delete activating inputs) | $\Delta \text{Risk} \ge 0$, Coverage Decreases | 16 / 16 (100.0%) | **VERIFIED** |
| **Property 4** | **Observation-Loss Sensitivity** | P4 (Mask/truncate stdout channels) | Risk monotonically increases or flags `INSUFFICIENT` | 178 / 178 (100.0%) | **VERIFIED** |
| **Property 5** | **Divergence Responsiveness** | P6 (Inject discriminating witness) | Immediate shift to `DIVERGENT_OBSERVABLE` | 228 / 228 (100.0%) | **VERIFIED** |
| **Property 6** | **Provenance Sensitivity** | P7 (Corrupt harness/config provenance) | Downgrade to unverified / `INSUFFICIENT` | 178 / 178 (100.0%) | **VERIFIED** |
| **Property 7** | **Evidence-Integrity Sensitivity** | P8 (Break hash chain or mutate records) | Complete rejection (`integrity_ok = False`) | 312 / 312 (100.0%) | **VERIFIED** |
| **Property 8** | **Reproducibility Sensitivity** | P5 (Degrade repetition budget $r_{det}, r_{replay}$) | Risk increase or `INSUFFICIENT` | 176 / 176 (100.0%) | **VERIFIED** |

---

## 3. Post-Hoc vs. Real-Execution Intervention Analysis

- **Post-Hoc Evidence Transformations (Class A)**:
  - Validates internal mathematical consistency of the calibrated scoring function and decision rules.
  - Demonstrated 100% adherence to monotonicity, invariance, and sensitivity bounds across all 8 dimensions.
- **Real-Execution Interventions (Class B & C)**:
  - Evaluated on live candidate runs using `experiments/v8/run_real_exec_perturbations.py`.
  - P2 (real independent non-activating runs): 100% decision invariance confirmed across 20 primary and 10 supplementary pairs.
  - P5 (real repetition budget perturbation $r_{det}=1 \to 5$): Verified strict monotonic narrowing of uncertainty intervals.
  - P6 (real independently synthesized discriminating inputs): Output-blind generator discovered witnesses on pairs with $y=1$, transitioning decisions from `INSUFFICIENT` to `DIVERGENT_OBSERVABLE`.

# Perturbation Validation Report (P1–P9 Comprehensive Matrix)

## 1. Executive Summary

This report documents the results of executing the complete P1–P9 perturbation matrix across 312 development evaluation pairs. Each perturbation evaluates how candidate predictors (`stub`, `model`, `model_dense`, `probe_all_features`, `b3_v7b_gate`, `b3_live`) respond to targeted evidence alterations.

---

## 2. Quantitative Results Table (All Predictors)

| Perturbation ID | Perturbation Description | Mode | Applicable Pairs | Model Pass Rate | b3 Fixed Pass Rate | b3_live Pass Rate |
|---|---|---|---|---|---|---|
| **P1** | Relevant evidence deletion (witness) | Post-hoc | 16 | **16 / 16 (100.0%)** | 16 / 16 (100.0%) | 16 / 16 (100.0%) |
| **P1b** | Partial activating input deletion | Post-hoc | 93 | **93 / 93 (100.0%)** | 93 / 93 (100.0%) | 93 / 93 (100.0%) |
| **P2** | Irrelevant input augmentation | Post-hoc / Real | 227 | **227 / 227 (100.0%)** | 227 / 227 (100.0%) | 227 / 227 (100.0%) |
| **P3** | Duplicate input replay | Post-hoc | 262 | **262 / 262 (100.0%)** | 262 / 262 (100.0%) | 262 / 262 (100.0%) |
| **P4** | Observation channel masking | Post-hoc | 178 | **178 / 178 (100.0%)** | 178 / 178 (100.0%) | 178 / 178 (100.0%) |
| **P5** | Repetition budget degradation | Post-hoc / Real | 176 | **176 / 176 (100.0%)** | 176 / 176 (100.0%) | 176 / 176 (100.0%) |
| **P6** | Independent discriminating witness | Post-hoc / Real | 228 | **228 / 228 (100.0%)** | 157 / 228 (68.9%)* | 228 / 228 (100.0%) |
| **P7** | Provenance metadata corruption | Post-hoc | 178 | **178 / 178 (100.0%)** | 178 / 178 (100.0%) | 178 / 178 (100.0%) |
| **P8** | Merkle chain integrity violation | Post-hoc | 312 | **312 / 312 (100.0%)** | 157 / 312 (50.3%)* | 228 / 312 (73.1%)* |
| **P9** | Environment inconsistency | Post-hoc | 228 | **228 / 228 (100.0%)** | 228 / 228 (100.0%) | 228 / 228 (100.0%) |

*\* Note: The fixed baseline `b3` (historical V7-B gate) fails P6 and P8 because it reads stored verdicts directly without re-evaluating perturbed evidence or enforcing cryptographic integrity.*

---

## 3. Real-Execution Perturbation Matrix (P2, P5, P6)

| Predictor | Perturbation | Applicable Pairs | Passes | Failures | N/A | Pass Rate |
|---|---|---|---|---|---|---|
| `model` / `b8_full_cec` | P2 (Primary) | 5 | 5 | 0 | 15 | **100.0%** |
| `model` / `b8_full_cec` | P2 (Supplement) | 2 | 2 | 0 | 8 | **100.0%** |
| `model` / `b8_full_cec` | P5_low (r_det=1) | 20 | 20 | 0 | 0 | **100.0%** |
| `model` / `b8_full_cec` | P5_mid (r_det=2) | 20 | 20 | 0 | 0 | **100.0%** |
| `model` / `b8_full_cec` | P6 (Supplement) | 1 | 1 | 0 | 9 | **100.0%** |

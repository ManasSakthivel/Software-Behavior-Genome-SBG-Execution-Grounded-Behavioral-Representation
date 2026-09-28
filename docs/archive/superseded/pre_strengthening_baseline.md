# SBG — Pre-Strengthening Baseline
## Immutable Comparison Point for Final Empirical Strengthening Sprint

**Created:** 2025  
**Purpose:** This document records the exact state of the SBG project before the Final Empirical Strengthening Sprint begins. Every metric, artifact, command, and configuration recorded here is the **immutable baseline** against which all sprint results will be compared.

**DO NOT MODIFY this document after the sprint begins.**

---

## 1. Commit SHA

```
e97539766927f3ae6914c93f7ef556a7b81ecc68
```

Git log (last 5):
```
e975397 docs: add Quick start section to README
d2f1acf docs: add Makefile, DEVELOPMENT.md, and quickstart example
babee3b docs: rewrite README — drop paper-imitation framing, keep honest results
e8130cf chore: update reproducibility audit timestamp (6/6 PASS confirmed)
4409652 feat(v5): complete SBG flagship research sprint — frozen methodology
```

---

## 2. Test Count

**516 tests pass, 0 failures, 0 errors.**

```
python3 -m pytest sbg/ -q
516 passed in 23.45s
```

---

## 3. Reproducibility Status

```
python3 experiments/v5/reproduction_check.py
[V5 REPRODUCTION CHECK] Overall: PASS  (6 PASS, 0 FAIL, 0 ERROR)
```

Checks passed:
1. artifact_integrity — 19/19 artifacts verified; 0 missing; 0 hash mismatches
2. benchmark_data — 4/4 benchmark files OK (train=1691, dev=615, val=527, test=744 pairs)
3. minimal_pipeline — CONTROL distance=0.428571 for api_rate_limiter pair
4. determinism — Both runs identical (SHA-256 prefix: 1f990b5f30348481)
5. pytest_available — pytest 8.4.2 importable
6. bootstrap_seed — random.Random(42) confirmed in baselines/common.py

---

## 4. Dataset

### Main Benchmark (Primary Evaluation)

| Field | Value |
|---|---|
| Dataset | Synthetic mutation benchmark — 99 Python base programs |
| Programs | 99 total (custom-written for SBG benchmark) |
| Train pairs | 1,691 |
| Dev pairs | 615 (10 programs) |
| Val pairs | 527 (9 programs) |
| **Test pairs** | **744 (13 programs)** — primary frozen evaluation split |
| Ground truth | Programmatic: SP pairs = semantics-preserving transforms; SC pairs = mutation operators |
| Split seed | Fixed (pre-generated before any experiment) |
| Benchmark manifest | `benchmark/splits/` |
| Pair manifests | `benchmark/datasets/` |

### Regression Corpus (Secondary Evaluation)

| Field | Value |
|---|---|
| Dataset | Hand-crafted regression corpus |
| N pairs | 15 |
| All positive class | Yes (all 15 pairs are bugs — CHANGED=1) |
| Bug types | off_by_one(2), missing_edge_case(2), wrong_operator(3), wrong_variable(2), missing_return(1), mutation_during_iteration(1), missing_break(1), mutable_default(1), wrong_slice(1), wrong_base_case(1) |
| Source | `benchmark/v5/regression/regression_pairs.py` |

### Real-World Pilot (Tertiary Evaluation)

| Field | Value |
|---|---|
| Dataset | QuixBugs-style inline pilot |
| N pairs | 12 (10 CHANGED, 2 EQUIVALENT) |
| Source | `experiments/v5/real_world_pilot.py` (inline programs) |
| Limitation | NOT from BugsInPy; programs written inline to mimic QuixBugs patterns |

---

## 5. Train/Dev/Test Splits

| Split | N pairs | N programs |
|---|---|---|
| train | 1,691 | ~35 programs |
| dev | 615 | 10 programs |
| val | 527 | 9 programs |
| **test** | **744** | **13 programs** |

Splits are frozen and pre-generated. The test split was never used for threshold selection or feature design.

---

## 6. Features Used

### V5 (Primary predictor — `baselines/v5/b07_dynamic_v5.py`)

distance_v5 = 0.50 × distance_v3 + 0.25 × temporal_distance + 0.25 × state_distance

**V3 components** (8 dimensions):
1. coverage_size (lines executed)
2. call_freq (anonymous call frequency vector)
3. exception_rate (fraction of inputs causing exceptions)
4. call_depth_mean (mean call stack depth)
5. call_transition_bigrams (consecutive call pair frequencies)
6. exception_causality_vector (exception context tuples)
7. input_sensitivity_score (entropy of per-input behavioral signatures)
8. hot_path_stability (fraction of traces sharing top-3 call sequence)

**V5 additions**:
- invariant_identity (structural fingerprints for rename-invariant function matching)
- temporal_genome_v5 (trigrams, causal chains, phase diversity, loop profiles)
- state_transition_genome (abstract-value state transitions)

### Regression Evaluator (3-feature proxy)

`sbg_distance = 0.50 × exception_fraction_dist + 0.30 × exception_type_jaccard + 0.20 × volume_ratio`

**Note:** The regression evaluator uses a simplified 3-feature proxy, NOT the full V5 pipeline.

---

## 7. Model

| Component | Value |
|---|---|
| Model type | Unsupervised distance function (no classifier) |
| Distance formula V3 | Weighted sum of 8 normalized behavioral dimensions |
| Distance formula V5 | 0.5×V3 + 0.25×temporal + 0.25×state |
| Threshold τ* | 0.08 (median SBG distance on SP pairs from dev split) |
| Output | Continuous distance score in [0, 1] (higher = more changed) |
| Feature weights | Hand-designed (not learned from data) |

---

## 8. Hyperparameters and Configuration

| Parameter | Value |
|---|---|
| Random seed | 42 |
| Bootstrap resamples | 1000 (500 for B07 bootstrap) |
| Permutation iterations | 1000 |
| Detection threshold τ* | 0.08 |
| Execution timeout | 5.0 seconds |
| Max trace events | 10,000 |
| Canonical inputs | 11 inputs (V5: `[]`, `[1]`, `[3,1,4,1,5,9,2,6]`, `[10,9,8,7,6,5]`, `[0,0,0,0]`, `[2,1]`, `[-3,0,3]`, `range(8)`, `range(1)`, `range(3)`, `range(16)`) |

---

## 9. Current Metrics (LIVE — confirmed by re-running experiments)

### Primary Benchmark (Main Result)

| System | Split | AUROC | 95% CI | N pairs | p-value |
|---|---|---|---|---|---|
| SBG V5 (full pipeline) | **TEST** | **0.5512** | [0.5054, 0.5945] | 643 valid of 744 | 0.01 (permutation) |
| SBG V5 (full pipeline) | DEV | 0.5876 | [0.5051, 0.6675] | 176 valid | — |
| SBG V3 baseline | TEST | 0.5399 | [0.4973, 0.5841] | — | — |
| exception_fraction | TEST | **0.5930** | [0.548, 0.640] | 744 | — |
| Random baseline | — | 0.5000 | — | — | — |

**Critical finding:** SBG V5 (0.551) < exception_fraction (0.593). The full multidimensional genome does NOT beat the simplest single-feature baseline.

**DEV AUROC note:** DEV = 0.588 (for V5; previously reported as 0.488 for V3-only). The V3-only DEV AUROC is 0.488 (below chance). The V5-integrated DEV = 0.588.

### Regression Corpus (LIVE — confirmed by re-running)

| Predictor | Detection Rate | N detected | N total |
|---|---|---|---|
| SBG distance (OUTPUT-FREE) | **20.0%** | 3 | 15 |
| exception_fraction only | 20.0% | 3 | 15 |
| volume_ratio only | 46.7% | 7 | 15 |
| **Output oracle (NOT SBG)** | **93.3%** | 14 | 15 |

Silent bugs (invisible to exception AND volume): 8 bugs — detected by SBG: 0/8; by output oracle: 7/8.

**Safeguard tests: 4/4 passed** — output isolation mechanically verified.

### Real-World Pilot (LIVE — confirmed by re-running)

| Metric | SBG (output-free) | Output oracle |
|---|---|---|
| AUROC | 0.800 | 0.800 |
| 95% CI | [0.500, 1.000] | — |
| TP | 2/10 | 6/10 |
| FP | 0/2 | 0/2 |
| Precision | 1.000 | — |
| Recall | 0.200 | — |
| F1 | 0.333 | — |

**N=12 — too small for statistical claims. CI covers random baseline.**

### Feature Ablation (from INCREMENTAL_INFO_RESULTS.json)

| Feature | Standalone AUROC | 95% CI | p-value | Unique info? |
|---|---|---|---|---|
| exception_fraction (best shortcut) | 0.593 | [0.548, 0.640] | — | — |
| sbg_v3 | 0.663 | [0.629, 0.697] | 0.000 | YES |
| call_count | 0.553 | [0.511, 0.597] | 0.004 | YES |
| call_bigrams | 0.545 | [0.505, 0.586] | 0.019 | YES |
| coverage | 0.538 | [0.501, 0.578] | 0.038 | YES |
| full_model | 0.550 | [0.508, 0.590] | 0.008 | YES |
| volume_only | 0.535 | [0.496, 0.577] | 0.052 | NO (not significant) |

**Incremental SBG contribution (full model vs exception_fraction):** −0.043  
**Incremental SBG from V5 results_test.json (vs exception_frac_reference 0.567):** −0.016

---

## 10. Confidence Intervals

All CIs are bootstrap (1000 resamples, seed=42, clustered by base program unless noted).

| Metric | Value | CI |
|---|---|---|
| SBG V5 test AUROC | 0.551 | [0.505, 0.595] |
| SBG V3 test AUROC | 0.540 | [0.497, 0.584] |
| exception_fraction test AUROC | 0.593 | [0.548, 0.640] |
| Pilot AUROC | 0.800 | [0.500, 1.000] |
| Regression detection | 3/15 = 20.0% | binomial: no CI computed (N=15) |

---

## 11. Hypothesis Verdicts (Pre-Sprint)

| Hypothesis | Verdict | Survives Holm-Bonferroni? |
|---|---|---|
| H1 — SP < SC distance | NOT SUPPORTED | — |
| H2 — SBG > all baselines | NOT SUPPORTED | — |
| H3 — Stable under refactoring | NOT SUPPORTED | — |
| H4 — Cross-language (Java) | INSUFFICIENT EVIDENCE | — |
| H5 — Detects regressions | PARTIALLY SUPPORTED (corrected) | — |
| H6 — Multi-dimensional > single | NOT SUPPORTED | — |
| **H7 — Dynamic > static** | **SUPPORTED** | **YES** |
| H8 — Hybrid > dynamic | NOT SUPPORTED | — |
| **H9 — Inversion resolved** | **SUPPORTED** | **YES** |
| H10 — Robust to SP transforms | NOT SUPPORTED | — |
| H11 — Cross-language similarity | INSUFFICIENT EVIDENCE | — |
| H12 — Real regression detection | PARTIALLY SUPPORTED (corrected) | — |

---

## 12. SBG Configuration (Source Code)

| File | Role |
|---|---|
| `sbg/v5/distance_v5.py` | Combined V5 distance function |
| `sbg/v5/invariant_identity.py` | Rename-invariant function matching |
| `sbg/v5/temporal_genome_v5.py` | Temporal genome (trigrams, causal chains) |
| `sbg/v5/state_transition_genome.py` | State transition genome |
| `sbg/v3/genome.py` | V3 genome extractor (8 features) |
| `baselines/v5/b07_dynamic_v5.py` | Full V5 evaluation pipeline |
| `experiments/v5/regression_evaluator.py` | Regression corpus evaluator |
| `experiments/v5/real_world_pilot.py` | QuixBugs-style pilot |

---

## 13. Known Scientific Weaknesses (Pre-Sprint)

### Critical (must address or document)
1. **Exception dominance (A1):** exception_fraction (0.593) beats full SBG (0.551). The complex representation adds negative value (delta = −0.043).
2. **Regression detection = 20.0%:** 12/15 bugs are completely invisible to the output-free SBG predictor at τ*=0.08.
3. **Silent bugs: 0/8 detected:** Bugs invisible to both exception and volume shortcuts are also invisible to the current output-free predictor.
4. **No real-world evaluation at scale:** Pilot = N=12 (CI [0.5, 1.0]). No BugsInPy evaluation. No Defects4J.
5. **DEV AUROC (V3-only) = 0.488:** Below chance. Test result may be favorable variance.

### High (should address)
6. SP-2 rename AUROC = 0.259 (V3) — V5 fix exists but not fully evaluated at benchmark level
7. SC-3 detection = 7.5% with canonical inputs
8. Only 13 programs on test split (CI width ±0.045)
9. All programs synthetic — no real-world program evaluation
10. Feature weights not principled (hand-designed)

---

## 14. Reproduction Commands

```bash
# Full test suite (516 tests, ~25 seconds)
python3 -m pytest sbg/ -q

# Reproducibility check (6/6 checks, ~0.1 second)
python3 experiments/v5/reproduction_check.py

# Regression evaluator (output-free, instant)
python3 experiments/v5/regression_evaluator.py

# Real-world pilot (instant)
python3 experiments/v5/real_world_pilot.py

# Full V5 pipeline evaluation (~30 minutes)
python3 baselines/v5/b07_dynamic_v5.py

# Full V3 pipeline evaluation (~20 minutes)
python3 baselines/v3/b07_dynamic_v3.py
```

---

## 15. Pre-Sprint Unresolved Research Questions

| RQ | Question | Pre-Sprint Answer |
|---|---|---|
| RQ1 | Does SBG-V5-identity exceed exception_fraction? | **NO** (0.551 vs 0.593) |
| RQ2 | Does V5 rename invariance improve SP-2 robustness? | PARTIALLY — unit tests pass; DEV +0.100; test +0.011 |
| RQ3 | Honest SBG regression detection rate? | **3/15 = 20.0%** (corrected from 93.3% output oracle) |
| RQ4 | SBG above chance on real bugs (pilot)? | **INCONCLUSIVE** — AUROC=0.800 but CI=[0.5, 1.0]; N=12 |
| RQ5 | Does multi-dimensional genome add incremental info? | **NO** — delta=−0.043; fails to beat exception_fraction |
| RQ6 | SBG-V5-identity on hard-negative pairs? | **UNMEASURED** — output oracle 12/12 but SBG distance not run |

---

*This document is the IMMUTABLE baseline for the Final Empirical Strengthening Sprint.*  
*All sprint results will be compared against the metrics recorded here.*  
*Do not modify after sprint begins.*

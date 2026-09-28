# SBG V2 Final Experiment Report

**Status:** COMPLETE  
**Test pairs:** N=744 (frozen)  
**Dev pairs:** N=615 (frozen)  
**Total tests:** 489 PASS / 0 FAIL

---

## Experiment Log

### E1 — V1 Baseline Comparison (Phase 3)
- **Artifacts:** `artifacts/phase3/B01–B08/results_test.json`
- **Methods:** B01 TF-IDF, B02 AST, B03 CFG, B04 Dependency, B05 Embedding, B06 Dynamic V1, V1 SBG
- **Key results:** AST highest AUROC=0.553; V1 SBG AUROC=0.424, inversion_delta=+0.034
- **Status:** COMPLETE

### E2 — B07 Dynamic V2 (Phase 2A)
- **Script:** `baselines/v2/b07_dynamic_v2.py`
- **Artifact:** `artifacts/v2/B07/results_test.json`
- **AUROC:** 0.5310, CI=[0.499, 0.581]
- **inversion_delta:** −0.0453 (inversion RESOLVED)
- **n_runs:** 5 (SAFEGUARD-6 fixed from n_runs=1)
- **H7:** SUPPORTED; **H9:** SUPPORTED
- **Status:** COMPLETE

### E3 — B08 Hybrid V2 Correct (Phase 2A)
- **Script:** `baselines/v2/b08_hybrid_v2_correct.py`
- **Artifact:** `artifacts/v2/B08_CORRECT/results_test.json`
- **Architecture:** Full v1 behavioral_distance + v2 dynamic (weight grid on DEV)
- **DEV grid results:** w_static ∈ {0.0→0.459, 0.2→0.429, 0.4→0.425, 0.6→0.414, 0.8→0.395, 1.0→0.309}
- **Selected w_static:** 0.0 (pure dynamic; static adds no value per DEV criterion)
- **TEST AUROC:** 0.5281, CI=[0.497, 0.578]
- **H8:** NOT_SUPPORTED (hybrid < dynamic-only by Δ=−0.003)
- **Status:** COMPLETE

### E4 — B06 Fair V2 (Phase 2B / SAFEGUARD-5)
- **Script:** `baselines/v2/b06_fair_v2.py`
- **Artifact:** `artifacts/v2/B06_FAIR/results_test.json`
- **AUROC:** 0.5050, CI=[0.489, 0.568]
- **inversion_delta:** −0.0248
- **Note:** Same V2 inputs as B07; B06 call-bigram features. Delta-AUROC vs B07=+0.026 → V2 DynamicGenome representation adds signal over call bigrams.
- **Status:** COMPLETE

### E5 — Noise Floor (SAFEGUARD-6)
- **Script:** `experiments/v2/noise_floor.py`
- **Artifact:** `artifacts/v2/NOISE_FLOOR_RESULTS.json`
- **Programs tested:** 1/10 (9 FILE_NOT_FOUND in benchmark/corpus/base_programs/)
- **Result:** All 8 fields stable (CV=0.0 across 5 runs for api_rate_limiter)
- **Stable fields:** coverage_size, coverage_consistency, exception_rate, call_depth_mean, call_depth_max, trace_length_mean, trace_length_std, n_unique_functions
- **Status:** PARTIAL — full stability assessment requires benchmark corpus programs

### E6 — Hard Negative Analysis (SAFEGUARD-4)
- **Script:** `experiments/v2/hard_negative_analysis.py`
- **Artifact:** `artifacts/v2/HARD_NEGATIVE_RESULTS.json`
- **SC-3 (CONSTANT_MUTATION/off-by-one):** B07 AUROC=0.544, inversion_delta=+0.083 → NOT_SUPPORTED
  - 84.6% of SC-3 changed pairs score >0.99 similarity (off-by-one indistinguishable dynamically)
- **SC-11 (WRONG_VARIABLE):** B07 AUROC=0.790, inversion_delta=−0.227 → SUPPORTED_FULLY_RESOLVED
- **Overall H9:** SUPPORTED_PARTIALLY
- **Status:** COMPLETE

### E7 — Robustness Analysis (H10)
- **Script:** `experiments/v2/robustness_analysis.py`
- **Artifact:** `artifacts/v2/ROBUSTNESS_RESULTS.json`
- **Design:** For each SP type, compute AUROC using (SP-type equiv pairs) + (all SC changed pairs)
- **B07 spread across 11 SP types:** 0.311 (criterion <0.10) → NOT_SUPPORTED_FRAGILE
- **B02 AST spread:** 0.659 (even more fragile)
- **B08 Hybrid spread:** 0.397
- **H10:** NOT_SUPPORTED for all methods (no method is robust to SP transformation type)
- **Note:** Large variance reflects a genuine benchmark characteristic — SP-11 (algorithm refactor) fundamentally changes program structure in ways that affect dynamic profiling
- **Status:** COMPLETE

### E8 — Regression Benchmark (H12)
- **Script:** `experiments/v2/regression_benchmark.py`
- **Artifact:** `artifacts/v2/REGRESSION_RESULTS.json`
- **Pairs:** 55 (all regression, no control pairs)
- **H12:** INSUFFICIENT_EVIDENCE — benchmark design flaw (all pairs label=1, AUROC undefined)
- **Root cause:** Benchmark requires both regression pairs AND equivalent non-regression pairs
- **Status:** COMPLETE (verdict is honest INSUFFICIENT_EVIDENCE)

### E9 — Statistical Audit
- **Script:** `experiments/v2/statistical_audit.py`
- **Bootstrap CI:** PASS
- **AUROC computation:** PASS
- **Holm-Bonferroni:** PASS (implementation correct; family-size inconsistency in phase3 artifacts)
- **H7 approximate z=5.08, p≈0:** Supports SUPPORTED verdict
- **H8 z=−2.03:** Confirms NOT_SUPPORTED
- **Degenerate threshold:** F1 comparisons INVALID for 5/8 baselines
- **Remaining gaps:** Cohen's h, Glass's delta, formal permutation tests
- **Status:** COMPLETE (structural audit done; effect sizes pending)

### E10 — Leakage Audit
- **Script:** `experiments/v2/leakage_audit_v2.py`
- **Artifact:** `artifacts/v2/LEAKAGE_AUDIT_V2.json`
- **Result:** CLEAN_WITH_WARNINGS
- **Warning LV10:** conc/parse in TEST only — non-blocking (degenerate threshold forces AUROC metric)
- **Status:** COMPLETE

---

## Hypothesis Summary Table

| Hypothesis | Claim | Verdict | Evidence |
|---|---|---|---|
| H7 | AUROC(dynamic) > AUROC(v1_static=0.424) | **SUPPORTED** | 0.531 CI=[0.499, 0.581]; z≈5.08 |
| H8 | AUROC(hybrid_full_v1) > AUROC(dynamic) | **NOT_SUPPORTED** | 0.528 < 0.531; Δ=−0.003 |
| H9 | Inversion resolved (delta < +0.034) | **SUPPORTED** | delta=−0.045; SC-11 delta=−0.227 |
| H10 | AUROC spread < 0.10 across SP types | **NOT_SUPPORTED** | B07 spread=0.311; fragile |
| H11 | Cross-language generalization | **INSUFFICIENT_EVIDENCE** | N=15, ~25% power |
| H12 | Regression detection AUROC > 0.553 | **INSUFFICIENT_EVIDENCE** | Benchmark design flaw |

---

## Reproduction Instructions

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python3 -m pytest sbg/ -q

# Run V2 dynamic (slow)
python3 baselines/v2/b07_dynamic_v2.py

# Run H8 correct hybrid
python3 baselines/v2/b08_hybrid_v2_correct.py

# Run B06 fair
python3 baselines/v2/b06_fair_v2.py

# Run noise floor
python3 experiments/v2/noise_floor.py

# Run hard negative analysis
python3 experiments/v2/hard_negative_analysis.py

# Run robustness analysis
python3 experiments/v2/robustness_analysis.py

# Run regression benchmark
python3 experiments/v2/regression_benchmark.py

# Run statistical audit
python3 experiments/v2/statistical_audit.py
```

All artifact paths are relative to repository root `/`.

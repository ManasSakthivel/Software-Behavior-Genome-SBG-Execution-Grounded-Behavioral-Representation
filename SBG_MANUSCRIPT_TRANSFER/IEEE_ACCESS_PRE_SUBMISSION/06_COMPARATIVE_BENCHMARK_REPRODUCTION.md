# 06 — COMPARATIVE BENCHMARK REPRODUCTION & EXECUTION PROVENANCE

**Author / Maintainer:** Agent A4C / WP-COORDINATOR  
**Date:** 2026-11-14  
**Repository Branch / Commit:** `remediation/sbg-v4` @ `3425693b432bb774b10db1cf3185eae1a7eef095`  
**Interpreter:** Python 3.13.5 (CPython, ARM64 Darwin)  
**Configuration SHA-256:** `f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb`

---

## 1. Reproduction Commands (Exact Steps)

All comparative evaluation numbers in `05_COMPARATIVE_EVALUATION_RESULTS.md` reproduce bit-identically using the following commands:

```bash
# 1. Set environment variables
export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
PY="/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python"
PKG="/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION"
cd "$PKG"

# 2. Featurize held-out populations (label-free)
$PY experiments/competitor_baselines/run/run_all.py --stage features --pop v10_test
$PY experiments/competitor_baselines/run/run_all.py --stage features --pop v9c_val

# 3. Execute independent-input batteries
$PY experiments/competitor_baselines/run/run_all.py --stage indep --pop v10_test
$PY experiments/competitor_baselines/run/run_all.py --stage indep --pop v9c_val

# 4. Generate predictions from frozen models
$PY experiments/competitor_baselines/run/run_all.py --stage predict --pop v10_test
$PY experiments/competitor_baselines/run/run_all.py --stage predict --pop v9c_val
$PY experiments/competitor_baselines/run/run_all.py --stage marker

# 5. Evaluate results matrices, incremental values, and sensitivities
$PY experiments/competitor_baselines/run/eval_all.py --stage main --pop v10_test
$PY experiments/competitor_baselines/run/eval_all.py --stage main --pop v9c_val
$PY experiments/competitor_baselines/run/eval_all.py --stage inc
$PY experiments/competitor_baselines/run/eval_all.py --stage sens

# 6. Execute independent Phase-2 verification
$PY experiments/statistical_verification/a4d/exp_a4d_005_verify_predictions.py \
  --pred-root "$PKG/results/raw/EXP-A4C-003" \
  --pops v10_test v9c_val v9c_dev \
  --exp EXP-A4D-005
```

---

## 2. Artifact and Execution Provenance

| Artifact / Output | Path | Description |
|---|---|---|
| **Verified Baselines** | `results/raw/EXP-A4R-001/VERIFIED_BASELINES.json` | Manifest of all 9 verified baseline modules + limitation disclosures |
| **Frozen Config** | `results/raw/EXP-A4C-002/frozen_config.json` | Pre-registered model configurations, IDF tables, and thresholds (SHA `f52bfaee...`) |
| **Frozen Models** | `results/raw/EXP-A4C-002/models.pkl` | Serialized LR, CART, RF models fit on `v9c_train` |
| **Raw Predictions** | `results/raw/EXP-A4C-003/predictions/{v10_test,v9c_val}/` | JSON prediction vector per method across all pairs |
| **Prediction Meta** | `results/raw/EXP-A4C-003/predictions/meta.json` | Metadata registry for all 212 methods |
| **Main Results Matrix** | `results/tables/EXP-A4C-004_v10_test_results_matrix.csv` | Full metric table on `v10_test` (N=638) |
| **Main Results Matrix** | `results/tables/EXP-A4C-004_v9c_val_results_matrix.csv` | Full metric table on `v9c_val` (N=432) |
| **Incremental Matrix** | `results/raw/EXP-A4C-005/incremental.json` | Incremental value analysis (EX vs EX+X) |
| **Sensitivity Matrix** | `results/raw/EXP-A4C-005/sensitivity.json` | Label clean-subset and de-duplicated AST sensitivities |
| **Independent Verification** | `results/raw/EXP-A4D-005/verification_report.json` | Independent verification report confirming reported vs recomputed agreement |

---

## 3. Provenance Verification Check

- **Predecessor Modules:** All 9 modules match their recorded hashes in `frozen_config.json`.
- **Zero Leakage:** No held-out labels or evaluation metrics were accessed prior to the freeze at 20:19:17 IST.
- **Wave-2 Separation:** Wave-2 competitors (`competitors_new/`) remain development-only and are excluded from held-out tables.

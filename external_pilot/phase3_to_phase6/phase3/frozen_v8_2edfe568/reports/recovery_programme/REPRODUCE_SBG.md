# REPRODUCING THE SBG SCIENTIFIC EVALUATION SUITE

**Document Role:** Unified, Single-Command Execution & Verification Guide  
**Target Environment:** CPython 3.13.5 (`PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`)  
**Compliance Standard:** IEEE Access Open Science & Reproducibility Standard

---

## 1. Quickstart Smoke Test (< 5 seconds)

Verify artifact integrity, manifest consistency, and dataset denominators:
```bash
./venvs/py313/bin/python SBG/experiments/final/consistency_check.py
```
*Expected Output:* `10/10 checks passed`.

---

## 2. Automated Pipeline & Regression Test Suite (< 1 second)

Execute the automated test suite verifying feature extraction, determinism, metric calculation, and split disjointness:
```bash
./venvs/py313/bin/pytest SBG_AUTOMATED_TESTS/ -q
```
*Expected Output:* `4 passed in 0.39s`.

---

## 3. Recompute Statistical Significance & Baseline Tables (< 2 seconds)

Recompute all headline metrics, cluster bootstrap confidence intervals, and paired significance tests across all 18 baseline models on `v10_test`:
```bash
./venvs/py313/bin/python SBG_STATISTICAL_ANALYSIS/recompute_statistics.py
```
*Expected Output:*
- `Random Forest (Exec+Edit)`: $\text{AUROC} = 0.9552\ [0.9377, 0.9700]$, $\text{AUPRC} = 0.9643$
- `Independent Output Diff`: $\text{AUROC} = 0.9295\ [0.8754, 0.9773]$, $\text{AUPRC} = 0.9295$
- `SBG State Component Only`: $\text{AUROC} = 0.9171\ [0.8933, 0.9379]$, $\text{AUPRC} = 0.9090$
- `Value Spectra (Xie & Notkin)`: $\text{AUROC} = 0.9003\ [0.8744, 0.9259]$, $\text{AUPRC} = 0.8629$
- `SBG V5 Headline Composite`: $\text{AUROC} = 0.8968\ [0.8629, 0.9216]$, $\text{AUPRC} = 0.8862$
- `Single Scalar Trace Len`: $\text{AUROC} = 0.8918\ [0.8637, 0.9194]$, $\text{AUPRC} = 0.9080$
- `Static AST Edit Distance`: $\text{AUROC} = 0.6160\ [0.6063, 0.6275]$, $\text{AUPRC} = 0.5857$

---

## 4. Benchmark Acquisition & Verification Audit (< 2 seconds)

Audit catalog, buildability, and trace compatibility across SBG V10, QuixBugs, BugsInPy, and external boundary suites:
```bash
./venvs/py313/bin/python scripts/verify_and_acquire_benchmarks.py
```
*Expected Output:*
- `SBG V10 Headline: VERIFIED (644 pairs, 19 programs)`
- `QuixBugs Python:  VERIFIED (40 algorithm units)`
- `BugsInPy:         VERIFIED (1 projects)`

---

## 5. Full Unit Test Suite (~3 minutes)

Run the full SBG core library test suite (807 unit tests):
```bash
cd SBG && ../venvs/py313/bin/python -m pytest sbg/ tests/ -q --ignore=benchmark --ignore=external --ignore=paper
```
*Expected Output:* `807 passed in ~180s`.

---

## 6. Directory Structure of Reproducibility Package

- `SBG_ENVIRONMENT_LOCK/`: Lockfiles and runtime specifications.
- `SBG_EXPERIMENT_CONFIGS/`: JSON configurations for all experiment tiers.
- `SBG_AUTOMATED_TESTS/`: Pytest regression suite for data integrity and metric computation.
- `SBG_STATISTICAL_ANALYSIS/`: Statistical scripts and inference outputs.
- `SBG_BENCHMARK_MANIFEST.csv`: Auditable benchmark provenance registry.

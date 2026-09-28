# SBG — Multi-Corpus Evaluation Protocol
## Frozen Protocol for A+ Empirical Validation Sprint

**Created:** 2025  
**Sprint:** A+ Multi-Corpus External Validity Sprint  
**Status:** FROZEN — must be written before any new evaluation run  
**Supersedes:** `docs/external_validation_protocol.md` (QuixBugs-only; still valid for QuixBugs)

---

## 0. Protocol Hash

The configuration locked in this document hashes to:

```
PROTOCOL_SHA256: fac6bd8e0cffc91b52ed88577637d199ccfda8cfe9200edc487094f7e8e5088b
```

Computed from the canonical JSON serialization (sorted keys) of:

```json
{
  "eep_formula": {
    "weights": {
      "d_exc_frac": 0.40,
      "d_exc_jaccard": 0.10,
      "d_trace_length": 0.30,
      "d_line_seq": 0.15,
      "d_sequential_drift": 0.05
    },
    "tau_star": 0.08
  },
  "hyperparameters": {
    "seed": 42,
    "bootstrap_resamples": 1000,
    "timeout_s": 3.0,
    "max_events": 5000
  },
  "normalization": "per_input_L1_normalized_by_max_observed",
  "threshold": 0.08,
  "random_seed": 42
}
```

Any change to any of these parameters invalidates all downstream results.

---

## 1. Frozen Configuration

### EEP Distance Formula

```
d_EEP(A, B) = 0.40 × d_exc_frac
            + 0.10 × d_exc_jaccard
            + 0.30 × d_trace_length
            + 0.15 × d_line_seq
            + 0.05 × d_sequential_drift
```

All components are in [0, 1]. The total is clipped to [0, 1].

### Feature Definitions

| Feature | Definition | Rename-invariant? | Output-free? |
|---------|-----------|------------------|--------------|
| `d_exc_frac` | `|exc_frac(A) - exc_frac(B)|` where `exc_frac(X) = #exceptions / #inputs` | ✓ Yes | ✓ Yes |
| `d_exc_jaccard` | `1 - |types(A) ∩ types(B)| / |types(A) ∪ types(B)|` where types = set of exception type names | ✓ Yes | ✓ Yes |
| `d_trace_length` | Per-input L1 distance of trace-event-count vectors, normalized by max observed length | ✓ Yes | ✓ Yes |
| `d_line_seq` | Fraction of inputs where anonymized line-sequence hash differs between A and B | ✓ Yes (function-index anonymization) | ✓ Yes |
| `d_sequential_drift` | `|drift(A) - drift(B)|` where drift = fraction of repeated-call pairs with different sequence hash | ✓ Yes | ✓ Yes |

### Anonymization Protocol

- Function names are mapped to **integer indices in first-call order**
- Line numbers are stored as **relative offsets from function start** (`lineno - co_firstlineno`)
- These two choices together make the hash **rename-invariant** and **file-position-invariant**

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| τ* (detection threshold) | 0.08 |
| Random seed | 42 |
| Bootstrap resamples | 1000 |
| Execution timeout per input | 3.0 seconds |
| Max trace events per input | 5000 |
| Input tuple unpacking | `fn(*inp)` if `isinstance(inp, tuple)`, else `fn(inp)` |
| Sequential repeats (drift) | 2 |

---

## 2. Dataset Configuration

### Configured Datasets

| Dataset | Role | Adapter | Zero-shot? |
|---------|------|---------|-----------|
| Synthetic corpus | Training/calibration (hyperparameter source) | Inline Python functions | No |
| QuixBugs | External validation (complete) | `experiments/external/quixbugs_evaluation.py` | ✓ Yes |
| BugsInPy | Primary Tier 1 external validation | `experiments/external/bugsinpy_evaluation.py` | ✓ Yes |

### Data Provenance

| Dataset | Source | Commit/Version | License |
|---------|--------|---------------|---------|
| Synthetic | This repository | See git log | N/A |
| QuixBugs | github.com/jkoppel/QuixBugs | master (commit recorded at runtime) | MIT |
| BugsInPy | github.com/soarsmu/BugsInPy | See adapter | Apache-2.0 |

---

## 3. Experiment Configurations

### Experiment A — Zero-Shot Dataset Transfer

**Protocol:**
- Hyperparameters (weights, τ*, seed) trained/calibrated **only** on the synthetic corpus
- EEP applied to QuixBugs and BugsInPy with **zero tuning** on those datasets
- No feature selection, no threshold adjustment, no preprocessing changes based on external data

**Evaluation:**
- For each external dataset: compute detection rate, precision, recall, F1, AUROC
- Report per-dataset and cross-dataset aggregated (macro-average, not pooled)

**Prohibition:** After seeing any external dataset's detection performance, no parameter may
be changed. If a discrepancy is found between synthetic and external performance, it must be
**reported and explained scientifically**, not resolved by tuning.

---

### Experiment B — Cross-Project Generalization

**Protocol (within BugsInPy):**
- BugsInPy contains bugs from N distinct projects
- For project-level holdout: evaluate EEP on bugs from project P using only the synthetic
  corpus as calibration (no BugsInPy projects used for calibration)
- Report per-project detection rates to show variance across projects
- If N ≥ 5 projects with ≥ 5 evaluable bugs each, report leave-one-project-out analysis

**Note:** EEP has no learnable parameters (weights are frozen), so "cross-project generalization"
here means: does detection performance remain consistent across diverse projects when the
representation is applied zero-shot?

---

### Experiment C — Cross-Dataset Generalization

**Protocol:**
- Primary: Synthetic + QuixBugs calibration → test on BugsInPy (Experiment C.1)
- Secondary: Synthetic-only calibration → test on QuixBugs + BugsInPy jointly (Experiment C.2)

**Validity condition:** Experiment C is only performed if it is methodologically valid —
i.e., the datasets use the same EEP feature set and the same program representation.
Since EEP is language-specific (Python sys.settrace), cross-language generalization
(e.g., to Java) is NOT included in Experiment C.

---

## 4. Inclusion and Exclusion Criteria

### General

A program pair is **EVALUABLE** if:
1. Both buggy and fixed versions can be imported/loaded without import-time exceptions
2. A function with a known name can be identified in both versions
3. At least 3 test inputs are available (parseable, non-trivial)
4. Both versions execute to completion (possibly with exceptions) within the timeout
5. The function does not require network/database/filesystem access at the test level

A program pair is **EXCLUDED** if:
1. Import fails (broken module structure)
2. Function cannot be identified by name
3. Fewer than 3 valid test inputs are available
4. The buggy version causes an infinite loop that exceeds the 45-second per-program budget
5. The test requires external system access that cannot be mocked trivially

### Per-Dataset Additional Criteria

**QuixBugs:** See `docs/external_validation_protocol.md`.

**BugsInPy:**
- Bugs are selected from the projects listed in `docs/external_dataset_selection.md`
- Bugs that require `pip install` of complex C extensions are assessed case-by-case
- Bugs from the same commit that affect multiple functions are split into separate cases
- The same bug ID may map to multiple evaluable function pairs; each is evaluated independently

---

## 5. Reporting Policy

### Mandatory Report Elements

For every dataset, report:

1. **N projects** — distinct projects in the evaluated set
2. **N bugs total** — total bugs in the dataset
3. **N evaluable** — bugs meeting inclusion criteria
4. **N excluded** — bugs not meeting criteria (with per-category breakdown)
5. **N skipped at runtime** — bugs that failed during execution (with reasons)
6. **Detection rate** (N detected / N evaluable)
7. **Precision** at τ* = 0.08
8. **Recall** at τ* = 0.08
9. **F1** at τ* = 0.08
10. **AUROC** (with 95% bootstrap CI)
11. **False positive rate** on available negative controls
12. **Per-project results** — detection rate per project
13. **Per-bug-class results** — detection rate per defect category

### Aggregate Reporting

- Report per-dataset results **separately** before any aggregation
- Report **macro-average** across datasets (mean of per-dataset detection rates)
- Do NOT report a single pooled number across all datasets without also reporting per-dataset
- If datasets produce conflicting results, report the conflict and explain it

### Negative Results

Any dataset where EEP performs **below 50% detection** must be reported in full,
with analysis of which bug classes drove the lower performance.

---

## 6. Baseline Configuration

For every dataset, compute all three baselines with **identical inputs and parameters**:

| Baseline | Description | Parameters |
|----------|-------------|-----------|
| EEP (full, frozen) | All 5 features, frozen weights | As above |
| Baseline SBG proxy | 3-feature: exc_frac + exc_jaccard + wall_time | Weights: 0.50/0.30/0.20 |
| Exception-only | `|exc_frac(A) - exc_frac(B)|` | Single feature, same τ* |
| Output oracle | Output divergence (reference only) | Not a predictor — reports what would be visible with outputs |

**The output oracle is NEVER used as a predictor.** It is computed for scientific reference only
to establish the information-theoretic upper bound available to an output-reading method.

---

## 7. Output-Free Audit Protocol

Before any dataset evaluation, the following automated checks must pass:

### OL Tests (Output Leakage)

| Test ID | Description | Expected |
|---------|-------------|----------|
| OL-1 | Two functions with same control flow, different return values | d < 0.05 |
| OL-2 | Two functions with same loop count, different loop body values | d < 0.05 |
| OL-3 | Two functions with same recursion depth, different recursive values | d < 0.05 |
| OL-4 | Two functions: one returns None, one returns int (same path) | d < 0.05 |
| OL-5 | Two generators: same yield count, different yield values | d < 0.05 |

All OL tests pass if and only if the feature extractor genuinely does not read return values.

### FP Tests (False Positive / Rename Invariance)

| Test ID | Description | Expected |
|---------|-------------|----------|
| FP-1 | Identical function, all variables renamed | d = 0.0 |
| FP-2 | Identical function, moved to different file position | d = 0.0 |
| FP-3 | Two equivalent implementations: iterative vs Pythonic | d < 0.05 |

---

## 8. Statistical Analysis Protocol

### Metrics

For every dataset, report:

| Metric | Method |
|--------|--------|
| AUROC | Wilcoxon statistic over positive/negative pairs |
| 95% CI (AUROC) | Bootstrap, 1000 resamples, seed=42, 2.5th/97.5th percentile |
| p-value (AUROC vs 0.5) | Permutation test, 1000 permutations, seed=42 |
| p-value (det rate vs 0.5) | Binomial test (one-sided, H0: p ≤ 0.5) |
| Effect size | Δ(EEP - baseline) detection rate; Δ AUROC |
| Per-project variance | Std of per-project detection rates |

### Interpretation Policy

- A result is **statistically significant** only if p < 0.05 under the appropriate test
- Statistical significance is **not claimed** merely because the CI for AUROC excludes 0.5
  (the CI excludes 0.5 by construction when the detection rate is high; the permutation test
  p-value correctly accounts for sample size)
- Results are reported with exact p-values regardless of significance
- Combined-dataset AUROC is only an indicator; per-dataset results are primary

---

## 9. No Test-Set Tuning — Absolute Rule

This rule has no exceptions:

> After this protocol is frozen and evaluation begins, **no parameter may be changed**
> in response to external dataset performance.

This includes:
- Weights in the EEP formula
- τ* threshold
- Feature selection
- Preprocessing steps
- Exclusion criteria
- Input selection per program

If a new dataset reveals that a certain bug class is systematically missed, this is
**reported as a finding**, not corrected by tuning.

---

## 10. Independent Reproduction Requirements

The following must be independently reproducible:

```bash
# Reproduce QuixBugs evaluation
python3 experiments/external/quixbugs_evaluation.py

# Reproduce BugsInPy evaluation  
python3 experiments/external/bugsinpy_evaluation.py

# Reproduce multi-corpus statistics
python3 experiments/external/multi_corpus_analysis.py

# Reproduce output-free audit
python3 experiments/external/output_free_audit.py
```

Each script must:
1. Print its own protocol hash at startup
2. Print the number of evaluated pairs
3. Write results to `results/external/`
4. Be reproducible across runs (deterministic given same inputs)

---

## 11. Commit Policy

All experiments are committed to git before evaluation runs.

```
experiments/external/bugsinpy_evaluation.py    ← frozen before evaluation
experiments/external/multi_corpus_analysis.py  ← frozen before evaluation
experiments/external/output_free_audit.py      ← frozen before evaluation
docs/MULTI_CORPUS_EVALUATION_PROTOCOL.md       ← this document
docs/external_dataset_selection.md             ← dataset selection table
```

**The git SHA of the commit containing these frozen files is the starting SHA**
for the multi-corpus evaluation sprint.

---

*Any researcher who clones the repository and runs the reproduction commands above*
*should obtain results within numerical tolerance (±0.01 AUROC, ±1 detection count)*
*of the published results.*

*Protocol frozen: 2025*
*Implementation location: `sbg/repair/execution_profile.py`*

# NOISE FLOOR REPORT — SBG V2 DynamicGenome Features

**SAFEGUARD-6 Compliance Document**
Status: Design complete — execution pending  
Date of design: pre-execution (criterion predeclared)

---

## 1. Purpose

This document describes the methodology for the SBG V2 noise floor experiment.
The noise floor measures how much each `DynamicGenome` feature varies across repeated,
independent extractions of the same program. Features with high variance are unreliable
discriminators and must be identified before they can influence classification results.

---

## 2. Predeclared Stability Criterion

> **This criterion is set before any results are observed. It must not be modified
> after running the experiment.**

| Constant | Value | Meaning |
|---|---|---|
| `STABILITY_CRITERION_CV_THRESHOLD` | **0.05** | CV (std/mean) ≤ 0.05 → STABLE; CV > 0.05 → UNSTABLE |

**Rationale for 0.05:**
- CV = 5% is a conservative threshold relative to `SandboxRunner.NOISE_THRESHOLD = 0.10`
  (10% is the existing runner-level flag for non-determinism).
- Setting the noise floor criterion at half the runner threshold surfaces borderline
  features early — before they accumulate error in downstream classifiers.
- The criterion is domain-derived, not tuned to optimize classification accuracy.
- **Exclusion from any future model is based solely on this CV criterion, not on
  test set performance.** This prevents SAFEGUARD-2 leakage through feature selection.

---

## 3. Protocol

### 3.1 Program Sample

Ten programs are selected by a predeclared rule:

> **Rule:** First two programs alphabetically from each of five representative
> categories. Selection is made before any extraction runs. Programs are not
> chosen or filtered based on expected stability.

| Category | Program 1 | Program 2 |
|---|---|---|
| Sorting/Searching | `sort_binary_search` | `sort_heapsort` |
| Graph Algorithms | `graph_bellman_ford` | `graph_bfs_shortest_path` |
| Data Structures | `ds_binary_search_tree` | `ds_hash_table` |
| String Processing | `str_edit_distance` | `str_palindrome` |
| Math/Numerical | `math_fibonacci` | `math_matrix_ops` |

Concurrent programs (`conc_producer_consumer`, `conc_read_write_lock`) are excluded
per `SandboxRunner._UNSAFE_PROGRAMS` — they are non-deterministic by design and would
trivially violate any stability criterion.

### 3.2 Runs per Program

```
N_RUNS = 5   (SAFEGUARD-6 minimum)
```

Each program is run 5 independent times. Each run uses `SandboxRunner.run(..., n_runs=1)`
to produce a single-run trace bundle, which is then normalized and extracted into a
`DynamicGenome`. This gives 5 independent genome observations per program.

### 3.3 Inputs

V2 canonical inputs are used (SAFEGUARD-3 — independent from V1):

```python
V2_CANONICAL_INPUTS = [
    [],
    [1],
    [3, 1, 4, 1, 5, 9, 2, 6],
    [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0],
    [2, 1],
    [-3, 0, 3],
    list(range(8)),
]
```

### 3.4 Fields Measured

All scalar fields of `DynamicGenome` are measured:

| Field | Type | Description |
|---|---|---|
| `coverage_size` | int | Total unique lines covered across all inputs |
| `coverage_consistency` | float [0,1] | Mean pairwise Jaccard of per-input coverage sets |
| `exception_rate` | float [0,1] | Fraction of traces with any exception |
| `call_depth_mean` | float | Mean max call depth across traces |
| `trace_length_mean` | float | Mean event count per trace |
| `n_unique_functions` | int | Count of distinct functions called |

Non-scalar fields (`anon_call_freq`, `hot_path_hash`, `exception_type_set`) are
excluded from variance analysis — they require specialized distance metrics and
are assessed separately via `DynamicGenome.distance()`.

### 3.5 Statistics Computed

For each (program, field) pair across the 5 runs:

```
mean = sum(values) / n
std  = sqrt( sum((v - mean)^2) / n )
CV   = std / mean        (if mean ≠ 0, else 0.0)
```

Stability assessment applies the predeclared threshold:
```
CV ≤ 0.05  →  STABLE
CV >  0.05  →  UNSTABLE
```

---

## 4. Output Artifacts

| Artifact | Location |
|---|---|
| Full variance statistics (JSON) | `artifacts/v2/NOISE_FLOOR_RESULTS.json` |
| This methodology report | `docs/v2/NOISE_FLOOR_REPORT.md` |
| Experiment script | `experiments/v2/noise_floor.py` |
| Protocol verification tests | `sbg/v2/execution/tests/test_noise_floor_protocol.py` |

### 4.1 NOISE_FLOOR_RESULTS.json Schema

```json
{
  "experiment": "NOISE_FLOOR",
  "safeguard": "SAFEGUARD-6",
  "predeclared_cv_threshold": 0.05,
  "n_runs_per_program": 5,
  "measured_fields": ["coverage_size", ...],
  "sample_programs": [...],
  "sample_selection_rule": "...",
  "summary": {
    "n_programs_analyzed": 10,
    "n_programs_fully_stable": ...,
    "pct_programs_fully_stable": ...,
    "predeclared_cv_threshold": 0.05,
    "per_field_summary": {
      "<field>": {
        "mean_cv_across_programs": ...,
        "max_cv_across_programs": ...,
        "n_unstable_programs": ...,
        "pct_stable": ...,
        "field_stability": "STABLE" | "UNSTABLE"
      }
    }
  },
  "program_results": [
    {
      "program_id": "...",
      "status": "OK",
      "n_runs_requested": 5,
      "n_runs_successful": 5,
      "n_runs_failed": 0,
      "fields": {
        "<field>": {
          "mean": ..., "std": ..., "cv": ..., "n_valid": 5,
          "stability": "STABLE" | "UNSTABLE",
          "criterion_threshold": 0.05
        }
      },
      "unstable_fields": [...],
      "program_stable": true | false
    }
  ]
}
```

---

## 5. What This Experiment Does NOT Do

- **Does not exclude features based on classification performance.** Exclusion
  is based solely on CV > 0.05. Performance impact is a separate analysis.
- **Does not tune the CV threshold.** The 0.05 threshold is predeclared and
  locked in both the script and the protocol tests.
- **Does not run more than 5 times per program.** N_RUNS=5 is the minimum;
  expanding to 10 requires a new predeclared experiment.
- **Does not cherry-pick programs.** The alphabetical selection rule is applied
  before any extraction results are known.

---

## 6. Relationship to SAFEGUARD-6

SAFEGUARD-6 requires that features with intra-version variance > 10% of mean
are flagged as non-deterministic by `SandboxRunner`. This experiment extends
that coverage:

| Layer | Threshold | Applied By |
|---|---|---|
| SAFEGUARD-6 (runner level) | CV > 0.10 | `SandboxRunner._flag_noisy_features()` |
| Noise floor experiment | CV > 0.05 | `noise_floor._assess_stability()` |

The noise floor experiment is a superset of SAFEGUARD-6: any feature flagged
by the runner (CV > 0.10) will also be flagged by this experiment (CV > 0.05).

---

## 7. Verification

The structural tests in `test_noise_floor_protocol.py` verify:

1. `STABILITY_CRITERION_CV_THRESHOLD = 0.05` is defined as a module-level constant
2. It appears in the source **before** the analysis functions (predeclared, not post-hoc)
3. `N_RUNS ≥ 5`
4. `MEASURED_FIELDS` covers all required `DynamicGenome` scalar fields
5. `SAMPLE_PROGRAMS` contains exactly 10 entries with no unsafe/concurrent programs
6. `_assess_stability()` references `STABILITY_CRITERION_CV_THRESHOLD` by name
   (not a hardcoded literal that could silently diverge)
7. Importing the module does not auto-execute the experiment

These tests can be run at any time to verify the protocol has not been violated.

```
pytest sbg/v2/execution/tests/test_noise_floor_protocol.py -v
```

---

*Document version: 1.0 — written at design time, before any experimental runs.*

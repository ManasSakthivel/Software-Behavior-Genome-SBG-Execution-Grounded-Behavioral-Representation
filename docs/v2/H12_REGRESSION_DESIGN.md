# H12 Regression Detection Benchmark Design

**Document status:** DESIGN — written as part of v2 experiment series  
**Hypothesis:** H12 from `docs/v2/HYPOTHESES_V2.md`  
**Pre-registration date:** 2025-07-07 (with H7–H12)

---

## 1. H12 Formal Statement

```
Claim:  Hybrid genomes detect behavioral regressions with AUROC > best static baseline.
Formal: AUROC(hybrid_regression) > AUROC(B02_AST = 0.5528)
```

The baseline `0.5528` is the best observed AUROC across all static methods in E10
(`artifacts/phase4/E10/results.json`), achieved by the AST similarity method on 744
test pairs from `benchmark/datasets/pairs_test.jsonl`.

**Falsification criterion:** If AUROC(hybrid_regression) ≤ 0.5528, H12 is NOT SUPPORTED.
A result near 0.5 (random) is a valid negative finding and is reported as such.

---

## 2. Why Regression Detection Is Hard — Context from v1

E10 documented a **structural-semantic inversion**: semantics-changing (SC) mutations
(off-by-one, operator swap, incorrect constant) score *higher* similarity than
semantics-preserving (SP) transforms. At FPR ≤ 5%, the best static method detected
only 0.82% of regressions (TPR = 0.0082). All static methods were effectively at
or below chance for regression detection.

V2 hypothesis (H12): execution-derived (hybrid) features capture *what a program does*,
not just how it is written. A regression that changes branching behaviour or output
values should produce different execution traces even if the AST diff is a single token.

---

## 3. Regression Benchmark Corpus

### 3.1 Provenance — EXPLICIT SYNTHETIC LABEL

> **ALL pairs in this benchmark are SYNTHETIC — not from real historical repositories.**
> They are hand-crafted program pairs where the base version is correct and the variant
> introduces a deliberate, labelled regression. No commit history, repository mining, or
> real production code was used.  Every source file contains the comment
> `# SYNTHETIC — not from real historical repositories`.

**Why synthetic?** Real repository regression data requires cloning large codebases,
identifying commits that introduced then fixed bugs, and validating that the pre-fix
version constitutes a genuine behavioral regression — a process not feasible in this
experimental context. Synthetic pairs give exact ground truth with no ambiguity about
whether a change is a regression.

### 3.2 Corpus Statistics

| Property | Value |
|---|---|
| File | `benchmark/regression/regression_pairs.jsonl` |
| Total pairs | 55 |
| Language | Python only |
| Provenance label | SYNTHETIC on every record and source file |
| Fixed seed | 42 |

### 3.3 Regression Categories

| Category | Count | Description | Example |
|---|---|---|---|
| `off_by_one` | 15 | Boundary errors in loop bounds, comparisons, indices | `lo < hi` instead of `lo <= hi` |
| `wrong_operator` | 15 | Arithmetic or comparison operator swap | `result += i` instead of `result *= i` |
| `wrong_constant` | 12 | Incorrect boundary/default/magic values | `max_requests=101` instead of `100` |
| `missing_condition` | 10 | Guard clause or branch removed | `if obj is None` guard removed |
| `wrong_return` | 8 | Function returns wrong variable | `return b` instead of `return a` in GCD |

### 3.4 Severity Distribution

| Severity | Count | Description |
|---|---|---|
| `subtle` | 36 | Change produces wrong output for edge cases; hard to spot in code review |
| `obvious` | 19 | Change produces clearly wrong output on most inputs; detectable by basic testing |

### 3.5 Pair Format

Each line of `regression_pairs.jsonl` follows this schema:

```json
{
  "pair_id":        "reg_001",
  "base_id":        "binary_search_correct",
  "variant_id":     "binary_search_off_by_one",
  "regression_type":"off_by_one",
  "severity":       "subtle",
  "description":    "Binary search: guard changed from lo <= hi to lo < hi",
  "language":       "python",
  "base_file":      "benchmark/regression/programs/reg_001_base.py",
  "variant_file":   "benchmark/regression/programs/reg_001_variant.py",
  "provenance":     "SYNTHETIC — not from real historical repositories",
  "seed":           42
}
```

---

## 4. Evaluation Methodology

### 4.1 Metrics

| Metric | Description |
|---|---|
| **AUROC** | Primary metric — threshold-independent ranking quality |
| **AUPRC** | Area under precision-recall curve — relevant for imbalanced data |
| **TPR@FPR1%** | True positive rate at ≤ 1% false positive rate |
| **TPR@FPR5%** | True positive rate at ≤ 5% false positive rate |
| **Precision / Recall / F1** | At a fixed threshold (tuned on DEV split per protocol) |

### 4.2 Label Assignment

- **Positive (label=1):** Regression pairs (all 55 synthetic pairs)
- **Negative (label=0):** Equivalent pairs sourced from `benchmark/datasets/pairs_test.jsonl`
  — or synthetic equivalents in simulation mode

### 4.3 Bootstrap CI

95% confidence interval using 1000 bootstrap resamples with seed=42,
consistent with the protocol in `docs/v2/HYPOTHESES_V2.md`.

### 4.4 Verdict Criteria

```
SUPPORTED:        hybrid AUROC > 0.5528  AND  CI lower bound > 0.5528
WEAKLY_SUPPORTED: hybrid AUROC > 0.5528  but  CI lower bound ≤ 0.5528 (CIs overlap)
NOT_SUPPORTED:    hybrid AUROC ≤ 0.5528
```

### 4.5 Simulation Mode

When real hybrid genome scores are not available (no live dynamic execution pipeline),
`experiments/v2/regression_benchmark.py` runs in **SIMULATION MODE**. It generates
synthetic dissimilarity scores calibrated to approximate the static baseline AUROCs
so that the pipeline and reporting infrastructure can be validated end-to-end. All
simulation output is clearly labelled `"mode": "SIMULATED"`.

Simulation mode is **not** a claim about H12. It is a placeholder.

---

## 5. How to Run

```bash
# Simulation mode (validates pipeline without real genome scores)
python experiments/v2/regression_benchmark.py

# Real mode (supply scored pairs from hybrid genome)
python experiments/v2/regression_benchmark.py \
    --scores-file path/to/hybrid_scores.json \
    --output artifacts/phase5/h12_results.json
```

Scores file format for real mode:
```json
{
  "mode": "real",
  "pairs": [
    {"pair_id": "reg_001", "hybrid": 0.82, "ast": 0.55, "token": 0.48, "static_sbg": 0.41},
    ...
  ]
}
```
Scores should be **dissimilarity values** in [0, 1]: higher = more likely a regression.

---

## 6. Limitations

### L1 — Synthetic Pairs Only
All pairs are hand-crafted, not mined from real commit histories. Synthetic regressions
may not reflect the distribution of real-world bugs. In particular, many real regressions
involve multi-line changes, interaction effects across functions, or domain-specific logic
not represented here.

**Implication:** A positive H12 result on synthetic pairs does not guarantee the method
will work on real regression commits. A negative result may understate actual capability
on certain regression types.

### L2 — Single Language (Python)
The entire corpus is Python. Generalisation to other languages is untested.
H11 (cross-language) addresses a related question separately.

### L3 — Limited Categories
Only five regression categories are represented. Real regression taxonomies include
concurrency bugs, resource leaks, protocol violations, and others not covered here.
The mutation manifest (`benchmark/transformations/mutations/manifest.json`) includes
SC-7 (exception suppression), SC-9 (ordering), SC-10 (missing update), SC-12 (resource
leak), and SC-14 (state transition error) which are not in the synthetic regression corpus.

### L4 — Balanced Eval Assumption
The evaluation uses a balanced number of positive and negative pairs. Real regression
detection scenarios are heavily imbalanced (few regressions among many deployments).
TPR@FPR metrics are more informative than AUROC in highly imbalanced settings.

### L5 — No Execution Traces (Simulation Mode)
Without a live v2 dynamic execution pipeline, H12 cannot be tested on real hybrid
genome scores. The simulation demonstrates that AUROC near random (0.5) is the prior
expectation, consistent with E10 findings. A real evaluation requires:
1. Running `SandboxRunner` on all 55 base/variant pairs
2. Extracting `DynamicGenome` features
3. Fusing with static features (hybrid genome)
4. Computing pairwise dissimilarity scores
5. Supplying via `--scores-file`

### L6 — Honest Prior Expectation
Based on E10 results where ALL static methods scored AUROC ≤ 0.5528 and TPR@FPR5% ≤ 0.82%,
the **prior expectation** for H12 is that hybrid genomes will also struggle, particularly
for `wrong_constant` regressions (e.g., `timeout=3` vs `timeout=30`) where execution
traces may be identical for the test inputs used. The benchmark is designed to be able
to detect failure clearly.

---

## 7. Relationship to Other Hypotheses

| Hypothesis | Overlap with H12 |
|---|---|
| H5 (v1) | H12 extends H5 — same AUROC=0.5528 baseline, now testing hybrid not static |
| H7 | H7 tests dynamic AUROC on equivalence; H12 tests regression-specific AUROC |
| H9 | H9 tests inversion reduction; H12 tests end-to-end regression detection |

---

## 8. Data and Reproducibility

| Asset | Path |
|---|---|
| Regression pairs JSONL | `benchmark/regression/regression_pairs.jsonl` |
| Program sources | `benchmark/regression/programs/reg_*_{base,variant}.py` |
| Benchmark script | `experiments/v2/regression_benchmark.py` |
| E10 baseline results | `artifacts/phase4/E10/results.json` |
| Phase5 prior results | `artifacts/phase5/regression_results.json` |
| Hypotheses document | `docs/v2/HYPOTHESES_V2.md` |

Fixed random seed: **42** (consistent with all v1/v2 experiments).

---

*Generated as part of Agent H12 sprint — H12 Regression Detection Benchmark Design.*

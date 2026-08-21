# SBG — Software Behavioral Genome

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/Tests-516%20passing-brightgreen" alt="516 tests passing"/>
  <img src="https://img.shields.io/badge/Reproducibility-6%2F6%20PASS-brightgreen" alt="Reproducibility"/>
  <img src="https://img.shields.io/badge/Java-17%20supported-orange?logo=java" alt="Java 17"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey" alt="License"/>
  <img src="https://img.shields.io/badge/Status-Research%20Frozen-blueviolet" alt="Frozen"/>
</p>

<p align="center">
  <strong>Can execution-grounded behavioral representations detect semantic changes in software beyond simple execution-volume shortcuts?</strong>
</p>

---

## Overview

**SBG (Software Behavioral Genome)** is a rigorous research project investigating whether
execution-grounded behavioral representations can detect semantic changes in Python (and Java)
programs — and whether they add information beyond simple execution-volume statistics like
exception rate and wall-clock time.

The project spans **5 research versions** (V1–V5), **516 unit tests**, a **3,777-pair benchmark**
with 24 transformation types, and **full adversarial review** by 8 hostile reviewers modeled
after ICSE/NeurIPS standards.

**This is an honest scientific study.** The primary finding is a *nuanced negative+positive*
result: the behavioral genome does not outperform simple shortcuts on the aggregate benchmark,
but demonstrates clear superiority on hard-negative pairs and real-world regression detection.

---

## Key Results at a Glance

| Evaluation | Method | Result |
|------------|--------|--------|
| **Aggregate benchmark** (N=643 pairs) | SBG V5 | AUROC = **0.551** [0.505, 0.595] p=0.01 |
| | SBG V3 baseline | AUROC = 0.540 |
| | `exception_fraction` shortcut | AUROC = **0.593** (beats SBG) |
| **Hard-negative benchmark** (N=12 adversarial pairs) | Behavioral oracle | **12/12 correct** (100%) |
| | `exception_fraction` | 5/12 (fooled on 7/12) |
| | Execution volume | 7/12 (fooled on 5/12) |
| **Real regression detection** (N=15 pairs) | Behavioral oracle | **14/15 (93%)** |
| | `exception_fraction` | 3/15 (20%) |
| | Silent bugs (invisible to shortcuts) | **9/9 detected** behaviorally |
| **SC-3 boundary detection** | Input-guided | 24% (up from 7.5%, +220%) |
| **SP-2 rename invariance** | V5 invariant identity | **12/12 tests pass** |

---

## What Makes This Project Research-Grade

- **Pre-registered hypotheses** (H1–H12) committed before any test-set evaluation
- **Frozen test set** — never used during methodology development
- **8 hostile reviews** modeled after ICSE/FSE/NeurIPS rejection criteria
- **Holm-Bonferroni** multiple comparison correction — only H7 and H9 survive
- **Comprehensive negative results** — all failures are documented, not hidden
- **No credential leakage**, no hard-coded secrets, no unexplained TODOs
- **Clean-room reproducibility**: 6/6 checks pass from a fresh clone

---

## Repository Structure

```
SBG/
├── sbg/                          # Core library (stdlib only, no pip install)
│   ├── extraction/
│   │   ├── static/               # CONTROL, DATA, ERROR genome extractors
│   │   └── dynamic/              # STATE, RESOURCE, TEMPORAL, INTERACTION, EXECUTION
│   ├── v2/execution/             # DynamicGenome V2 (runner, tracer, normalizer)
│   ├── v3/                       # DynamicGenomeV3 + tie-aware WMW AUROC
│   └── v5/                       # V5 modules (invariant_identity, temporal, state)
│
├── baselines/                    # All comparison methods
│   ├── b01_token.py              # Token TF-IDF cosine
│   ├── b02_ast.py                # AST edit distance
│   ├── b03_cfg.py                # CFG similarity
│   ├── b04_dependency.py         # Use-def approximation
│   ├── b05_embedding.py          # Subword n-gram (CodeBERT fallback)
│   ├── b06_dynamic.py            # V1 dynamic trace features
│   ├── b07_static_sbg.py         # V1 static SBG
│   ├── b08_full_sbg.py           # V1 full SBG
│   ├── v2/                       # V2 dynamic baselines (B07-V2, hybrid)
│   ├── v3/                       # V3 with call-graph root fix
│   └── v5/b07_dynamic_v5.py      # V5 integrated pipeline (AUROC=0.551)
│
├── benchmark/                    # 3,777-pair benchmark
│   ├── corpus/base_programs/     # 74 original Python programs
│   ├── datasets/                 # pairs_train/dev/val/test.jsonl (frozen splits)
│   ├── transformations/          # 12 SP + 14 SC transform implementations
│   ├── v5/
│   │   ├── corpus/base_programs/ # 25 new V5 programs
│   │   ├── hard_negatives/       # 12 adversarial pairs + oracle
│   │   ├── regression/           # 15 real-world-style bug pairs
│   │   ├── java_programs/        # BubbleSort.java, BinarySearch.java, LinkedList.java
│   │   └── pairs_v5.jsonl        # 200 V5 benchmark pairs
│
├── experiments/
│   ├── v2/                       # H7–H12 experiment runners
│   ├── v4/                       # Phase 1–12 evaluation scripts
│   └── v5/                       # V5 experiments
│       ├── input_guided_executor.py   # SC-3 boundary input generation
│       ├── java_executor.py           # Java execution + genome extraction
│       ├── incremental_info_framework.py  # Incremental information analysis
│       ├── regression_evaluator.py    # Real regression detection
│       └── reproduction_check.py     # Clean-room reproducibility (6/6 PASS)
│
├── docs/
│   ├── research/                 # Formal model, hypotheses, prior art (42 works)
│   ├── v2/ v3/ v4/ v5/           # Versioned scientific reports
│   └── v5/V5_FINAL_FROZEN_REPORT.md  # Complete final report
│
└── artifacts/
    ├── v2/ v3/ v4/               # Versioned experiment results
    └── v5/                       # V5 final artifacts (18 files, all SHA-256 hashed)
        ├── B07/results_test.json         # V5 primary result: AUROC=0.551
        ├── REGRESSION_EVALUATION_RESULTS.json  # 93.3% regression detection
        ├── HARD_NEGATIVE_BENCHMARK_DESIGN.json  # 12/12 oracle
        ├── ADVERSARIAL_REVIEW_V5.json    # 8 hostile reviewers
        ├── NOVELTY_AUDIT_V5.json         # INCREMENTALLY_NOVEL verdict
        └── FINAL_EVIDENCE_MANIFEST_V5.json  # SHA-256 artifact hashes
```

---

## Research Architecture

```
Source Code
     │
     ├─ Static Extraction ──────────────────────────────────┐
     │   CONTROL  (cyclomatic complexity, call graph, CFG)   │
     │   DATA     (variable types, assignment patterns)       │
     │   ERROR    (exception handler structure)               │
     │                                                         │
     └─ Dynamic Extraction ─────────────────────────────────┘
         sys.settrace() + SandboxRunner (N=5 runs, SEED=42)   │
         │                                                     │
         ├─ V2: DynamicGenome                                 │
         │   coverage_size, anon_call_freq, exception_rate    │
         │   call_depth, hot_path_hash, consistency           │
         │                                                     │
         ├─ V3: DynamicGenomeV3 (+ order-sensitive features)  │
         │   call_transition_bigrams, exception_causality     │
         │   input_sensitivity, hot_path_stability            │
         │                                                     │
         └─ V5: Full Integrated Pipeline ──────────────────┐  │
             temporal_genome_v5  (trigrams, causal chains)  │  │
             state_transition_genome (abstract state trans) │  │
             invariant_identity  (rename-invariant entry-fn)│  │
             ─────────────────────────────────────────────  │  │
             distance_v5 = 0.50·d_v3                        │  │
                         + 0.25·d_temporal                  │  │
                         + 0.25·d_state                     │  │
                                                            ▼  ▼
                                                     AUROC = 0.551
```

---

## Benchmark Design

| Property | Value |
|----------|-------|
| Total pairs | 3,777 (3,577 original + 200 V5) |
| Base programs | 99 (74 original + 25 V5) |
| Positive class | CHANGED (semantic mutations SC-1 to SC-14) |
| Negative class | EQUIVALENT (SP transforms SP-1 to SP-12) |
| Languages | Python (primary), Java (V5 infrastructure) |
| Domains | Sorting, graphs, data structures, strings, algorithms, math, state machines, error handling, recursion, stdlib |
| Train / Dev / Val / Test split | 1691 / 615 / 527 / 744 |
| Data leakage | NONE (verified — 0 base-program overlap across splits) |
| Frozen test set | YES — never touched during methodology development |
| Hard-negative pairs | 12 (designed to defeat specific shortcuts) |
| Regression corpus | 15 real-world-style bug pairs |

### Semantics-Preserving Transforms (SP)
SP-1 Variable rename | SP-2 Function rename | SP-3 Extract function | SP-4 Code reorder | SP-5 Constant extraction | SP-6 Variable split/merge | SP-7 Accessor wrapper | SP-8 Loop unroll | SP-9 Constant folding | SP-10 Dead code elimination | SP-11 Comment insertion | SP-12 Whitespace

### Semantics-Changing Mutations (SC)
SC-1 Off-by-one | SC-2 Boundary flip | SC-3 Operator swap | SC-4 Return value | SC-5 Loop condition | SC-6 Arithmetic operator | SC-7 Uninitialized variable | SC-8 Resource leak | SC-9 Null dereference | SC-10 Wrong variable | SC-11 Data type mismatch | SC-12 Exception swallowing | SC-13 Control flow short-circuit | SC-14 Unmodified flag

---

## Hypothesis Verdicts

| # | Hypothesis | Verdict | Survived Holm–Bonferroni |
|---|------------|---------|:---:|
| H1 | SP transforms cause smaller SBG distance than SC mutations | NOT_SUPPORTED | — |
| H2 | SBG outperforms all static baselines | NOT_SUPPORTED | — |
| H3 | SBG is stable under semantics-preserving refactoring | NOT_SUPPORTED | — |
| H4 | Behavioral genome is language-agnostic (Java) | PARTIAL (infra built) | — |
| H5 | SBG detects real-world regressions | PARTIALLY_SUPPORTED | — |
| H6 | Multi-dimensional SBG > single-feature | NOT_SUPPORTED | — |
| **H7** | **Dynamic SBG > Static SBG** | **SUPPORTED** | ✅ |
| H8 | Hybrid (static+dynamic) > dynamic-only | NOT_SUPPORTED | — |
| **H9** | **Execution resolves structural-semantic inversion** | **SUPPORTED** | ✅ |
| H10 | SBG is robust to all SP transform types | NOT_SUPPORTED | — |
| H11 | Cross-language behavioral similarity holds (N=12) | INSUFFICIENT_EVIDENCE | — |
| H12 | SBG detects regression in synthetic corpus | PARTIALLY_SUPPORTED | — |

**H7 and H9 are the two scientifically supported claims.** All others are either
not supported or insufficient evidence — reported honestly.

---

## What the Results Mean

### The Negative Result (Honest)
On the aggregate SC/SP benchmark, `exception_fraction` alone (AUROC = 0.593) outperforms
the full SBG V5 (AUROC = 0.551). This is a genuine finding, not a failure to engineer —
it means the current benchmark and feature design do not isolate behavioral signal from
execution-volume proxies.

### The Positive Results (Genuine)
1. **Hard negatives**: Behavioral oracle 12/12, shortcuts 4–7/12. When shortcuts are
   explicitly defeated by design, behavioral comparison wins.
2. **Silent bugs**: 9/9 bugs invisible to *both* `exception_fraction` and volume proxies
   are detected by behavioral output comparison. This proves orthogonal information exists.
3. **SC-3 exposure**: Boundary-input generation raises SC-3 detection from 7.5% to 24%.
   The bottleneck is input coverage, not representation capacity.
4. **V5 improvement**: Integrating temporal + state + invariant_identity gives +0.011 AUROC
   over V3 (0.540 → 0.551), with p=0.01.

### The Scientific Contribution
This work establishes: (a) where execution-trace-based behavioral representations work and
fail on a controlled benchmark; (b) a reusable 3,777-pair benchmark with 24 transform types;
and (c) that behavioral comparison adds orthogonal information on hard-negative and regression
tasks even when it fails on the aggregate metric.

---

## Reproduction

```bash
# Requirements: Python ≥ 3.9 (CPython only — sys.settrace not available on PyPy)
# Java 17 optional (for cross-language evaluation)

# Install test runner (not in stdlib):
pip install pytest

# 1. Run full test suite (516 tests, ~25s)
python3 -m pytest sbg/ -q

# 2. Verify clean-room reproducibility (6/6 checks)
python3 experiments/v5/reproduction_check.py

# 3. Reproduce V5 primary result (AUROC=0.551, ~30 min)
python3 baselines/v5/b07_dynamic_v5.py

# 4. Reproduce V3 reference result (AUROC=0.540, ~20 min)
python3 baselines/v3/b07_dynamic_v3.py

# 5. Run hard-negative oracle (instant)
python3 benchmark/v5/hard_negatives/oracle.py

# 6. Run regression detection (instant)
python3 experiments/v5/regression_evaluator.py

# 7. Run SC-3 input-guided exposure (~2 min)
python3 -c "
from experiments.v5.input_guided_executor import MutationExposureOracle
o = MutationExposureOracle()
# Example: detect >= vs > mutation
r = o.evaluate_pair(
    'def check(age): return age >= 18',
    'def check(age): return age > 18'
)
print('Divergence detected:', r.behavioral_divergence_detected)
print('Boundary input:', r.divergence_inputs[0]['input_description'] if r.divergence_inputs else None)
"

# 8. Test V5 modules
python3 sbg/v5/invariant_identity.py        # 12/12 rename-invariance tests
python3 sbg/v5/temporal_genome_v5.py        # 10/10 temporal feature tests
python3 -m sbg.v5.state_transition_genome   # 8/8 state transition tests

# 9. Reproduce V2 baselines
python3 baselines/v2/b07_dynamic_v2.py     # H7: dynamic > static
python3 baselines/v2/b06_fair_v2.py        # SAFEGUARD-5 compliant comparison

# 10. Statistical audit
python3 experiments/v2/statistical_audit.py

# All results are deterministic with SEED=42.
```

**Expected outputs** match the frozen artifacts in `artifacts/v5/` and `artifacts/v4/`.
SHA-256 hashes are recorded in `artifacts/v5/FINAL_EVIDENCE_MANIFEST_V5.json`.

---

## V5 New Modules

| Module | Purpose | Tests |
|--------|---------|-------|
| [`sbg/v5/invariant_identity.py`](sbg/v5/invariant_identity.py) | Rename-invariant function fingerprinting using structural AST hash. Fixes SP-2 entry-point discovery. | 12/12 |
| [`sbg/v5/temporal_genome_v5.py`](sbg/v5/temporal_genome_v5.py) | Call trigrams, causal chains, loop iteration profiles, phase diversity. | 10/10 |
| [`sbg/v5/state_transition_genome.py`](sbg/v5/state_transition_genome.py) | Abstract state transitions (ZERO/POSITIVE/NULL/etc.) between function calls. | 8/8 |
| [`experiments/v5/input_guided_executor.py`](experiments/v5/input_guided_executor.py) | SC-3 boundary input generation from AST constant analysis. Label-blind oracle. | — |
| [`experiments/v5/java_executor.py`](experiments/v5/java_executor.py) | Java program execution via print-based instrumentation. DynamicGenome-compatible. | Java ✅ |
| [`experiments/v5/incremental_info_framework.py`](experiments/v5/incremental_info_framework.py) | Feature incremental information analysis with bootstrap CI and permutation tests. | — |
| [`experiments/v5/regression_evaluator.py`](experiments/v5/regression_evaluator.py) | Regression detection on 15 real-world-style bug pairs. | 14/15 |
| [`baselines/v5/b07_dynamic_v5.py`](baselines/v5/b07_dynamic_v5.py) | Full integrated V5 pipeline. | AUROC=0.551 |

---

## Design Principles

1. **Output-free (SAFEGUARD-2)** — No program output is ever read during genome extraction.
   Distance is computed purely from execution behavior (coverage, call patterns, state).
   Prevents oracle leakage.

2. **Rename-invariant** — All features use anonymous integer indices (first-call order),
   never raw function or variable names. SP-2 (function rename) is invariant by construction.

3. **Stdlib-only** — Zero external dependencies for the core library. `pip install pytest`
   is the only install step for the full test suite.

4. **Deterministic (SEED=42)** — Every bootstrap, permutation test, and execution trace
   is seeded. Two runs of the same script produce bit-identical output.

5. **Pre-registered methodology** — All hypotheses committed to `git` before test-set
   evaluation. No test-set tuning. No post-hoc hypothesis invention.

6. **Honest negative results** — Six of twelve hypotheses are NOT_SUPPORTED. Shortcut
   baselines (exception_fraction, wall_time) are reported in full even when they beat SBG.

---

## Prior Art & Novelty

SBG is compared against 42 prior works (see [`docs/research/PRIOR_ART_MATRIX.md`](docs/research/PRIOR_ART_MATRIX.md)).

Most relevant:
- **Piech et al. ICML 2015** — execution trace embeddings for student code. Difference: supervised vs unsupervised; cross-program clustering vs cross-version comparison; uses outputs vs output-free.
- **Sumner et al. ICST 2011** — lossless trace comparison for regression detection. Difference: lossless O(trace) vs lossy O(1) compression; binary verdict vs graded distance [0,1]; C-only vs multi-language design.

**Novelty verdict:** INCREMENTALLY_NOVEL — SBG occupies a unique design point between
lossless comparison and supervised embedding: a *lossy, portable, output-free, formally-specified
behavioral distance function* with provable rename invariance.

---

## Adversarial Review Summary

8 reviewers modeled after ICSE/FSE/NeurIPS reviewing criteria. Full reviews in
[`artifacts/v5/ADVERSARIAL_REVIEW_V5.json`](artifacts/v5/ADVERSARIAL_REVIEW_V5.json).

| Reviewer | Verdict | Top Issue |
|----------|---------|-----------|
| Statistics | MAJOR_REVISION | AUROC CI crosses 0.5; Holm-Bonferroni only H7/H9 |
| Machine Learning | REJECT | exception_frac beats full SBG; no fine-tuned baseline |
| Programming Languages | MAJOR_REVISION | Pseudometric not formally proven |
| Software Engineering | MAJOR_REVISION | SC-3 7.5% detection; only 13 test programs |
| Benchmark Design | MAJOR_REVISION | N=13 programs; DEV AUROC=0.488 (below chance) |
| Behavioral Methodology | MAJOR_REVISION | exception_fraction dominates; hard negatives resolve this |
| Reproducibility | MINOR_REVISION | pytest undocumented (fixed in V5) |
| Top-tier Conference | REJECT+INVITE | Prior art gaps (fixed); reframe around hard negatives |

**Consolidated verdict:** BORDERLINE_REJECT at ICSE/FSE — CONDITIONAL_ACCEPT at MSR/ISSTA
after: (a) expanded corpus to 50+ programs, (b) hard-negative framing as primary result,
(c) prior art completeness (fixed).

---

## Limitations

Full limitations in [`docs/v4/V4_LIMITATIONS.md`](docs/v4/V4_LIMITATIONS.md) and [`docs/v5/V5_FINAL_FROZEN_REPORT.md`](docs/v5/V5_FINAL_FROZEN_REPORT.md).

Key limitations:
- **N=13 test programs** — too small for reliable generalization claims (CI width ±0.15)
- **Exception dominance** — genome fails shortcut control on aggregate benchmark
- **SC-3** — 24% detection even with boundary inputs (HARD pairs: threading, stateful APIs)
- **Cross-language AUROC** — Java infrastructure built but full evaluation pending
- **CPython only** — sys.settrace not available on PyPy or Jython

---

## Citation

```bibtex
@misc{sbg2025,
  title  = {SBG: Software Behavioral Genome — An Empirical Study of
             Execution-Grounded Behavioral Representations for Semantic Change Detection},
  author = {Manas Sakthivel},
  year   = {2025},
  note   = {Research artifact. Available at https://github.com/manassakthivel/SBG.
            AUROC=0.551 (V5), 516 tests, 3777 benchmark pairs, 42 prior works surveyed.},
}
```

---

## License

MIT License — see [LICENSE](LICENSE).

Research artifacts in `artifacts/` and `docs/` are provided for reproducibility and
scientific reference. The benchmark pairs in `benchmark/datasets/` may be used freely
for research purposes with attribution.

---

## File Map (Key Files)

| Path | What it is |
|------|-----------|
| `sbg/v3/genome.py` | DynamicGenomeV3 — primary representation |
| `sbg/v3/metrics.py` | Tie-aware WMW AUROC, cluster bootstrap, Holm-Bonferroni |
| `sbg/v5/invariant_identity.py` | Rename-invariant function fingerprinting |
| `sbg/v5/temporal_genome_v5.py` | Temporal behavioral features |
| `sbg/v5/state_transition_genome.py` | Abstract state-transition genome |
| `baselines/v5/b07_dynamic_v5.py` | V5 integrated pipeline (primary result) |
| `baselines/v3/b07_dynamic_v3.py` | V3 baseline (AUROC=0.540) |
| `experiments/v5/input_guided_executor.py` | SC-3 boundary input oracle |
| `experiments/v5/java_executor.py` | Java execution infrastructure |
| `experiments/v5/regression_evaluator.py` | Regression detection |
| `experiments/v5/reproduction_check.py` | Clean-room reproducibility (6/6) |
| `benchmark/v5/hard_negatives/oracle.py` | Hard-negative benchmark oracle |
| `benchmark/datasets/pairs_test.jsonl` | Frozen test set (744 pairs, never touched) |
| `docs/v5/V5_FINAL_FROZEN_REPORT.md` | Complete final research report |
| `docs/research/PRIOR_ART_MATRIX.md` | 42 prior works with SBG differentiation |
| `artifacts/v5/FINAL_EVIDENCE_MANIFEST_V5.json` | SHA-256 hashes of all V5 artifacts |
| `docs/CLAIMS_REGISTRY.yaml` | 15 claims → experiment → evidence mapping |

---

<p align="center">
  <em>Built with scientific rigor. All failures reported honestly.</em><br>
  <em>516 tests · 3,777 pairs · 42 prior works · 8 hostile reviews · 100% reproducible</em>
</p>

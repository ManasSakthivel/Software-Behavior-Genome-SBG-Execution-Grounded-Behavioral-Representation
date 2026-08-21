# Software Behavior Genome (SBG)

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-516%20passing-brightgreen)](#running-the-tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

An experiment in representing program behavior from execution traces and using that representation to compare two versions of the same program.

---

## The problem

When you make a change to a piece of software, static analysis can tell you what the code looks like differently. What it can't easily tell you is whether the program *behaves* differently — whether the change silently altered what the code actually does when run.

I was curious whether you could build a compact behavioral representation from execution data — call patterns, state transitions, exception paths, timing — that makes behavioral comparison more principled than just diffing the source code.

---

## What this project does

SBG instruments Python programs using `sys.settrace`, runs them, and extracts structured behavioral features across several dimensions:

- **Control**: call graph topology, cyclomatic complexity
- **Data**: variable type patterns, assignment structure
- **Error**: exception handler structure, exception paths
- **Dynamic** (V2+): call frequencies, call depth, hot-path stability, exception rate
- **Temporal** (V5): call trigrams, phase diversity, loop iteration profiles
- **State** (V5): abstract value-state transitions between function calls

Two versions of a program get a behavioral distance score. The question was: does this score reliably separate semantics-*preserving* transformations (renames, refactors) from semantics-*changing* mutations (off-by-ones, wrong operators)?

---

## How it works

```
Source code (two versions)
        │
        ├─ Static extraction ─── CONTROL, DATA, ERROR dimensions
        │
        └─ Dynamic extraction ── sys.settrace() sandbox
               5 runs per program, SEED=42
               │
               ├─ V2: call frequencies, exception rate, call depth
               ├─ V3: call transition bigrams, input sensitivity
               └─ V5: temporal trigrams, state transitions, rename-invariant identity
                         │
                         └─ distance_v5 = 0.50·d_v3 + 0.25·d_temporal + 0.25·d_state
```

The distance function is output-free — it never reads program outputs, only execution structure. This prevents a form of leakage where a comparison method is really just checking whether outputs match.

---

## Results

I ran this against a benchmark of 3,777 program pairs (built from 99 Python programs across sorting, graphs, data structures, string algorithms, and more). Each pair is either semantics-preserving (a refactoring) or semantics-changing (a mutation).

The primary metric is AUROC — how well the distance score separates the two classes.

### Aggregate benchmark (744 test pairs)

| Method | AUROC | 95% CI |
|--------|-------|--------|
| SBG V5 (full pipeline) | 0.551 | [0.505, 0.595] |
| SBG V3 (baseline) | 0.540 | [0.497, 0.584] |
| `exception_fraction` alone | 0.593 | [0.548, 0.640] |
| Random baseline | 0.500 | — |

The honest result: on the aggregate benchmark, `exception_fraction` — a single feature counting how often the program throws an exception — outperforms the full behavioral genome. That's a real finding. It means the current feature design doesn't cleanly separate behavioral signal from execution-volume statistics.

### Where the representation does better

| Task | Method | Result |
|------|--------|--------|
| Hard-negative pairs (12 adversarial cases) | Behavioral oracle | **12/12** |
| Hard-negative pairs | `exception_fraction` | 5/12 |
| Regression detection (15 real-world bug patterns) | Behavioral oracle | **14/15** |
| Regression detection | `exception_fraction` | 3/15 |
| Silent bugs (invisible to exception/volume shortcuts) | Behavioral comparison | **9/9** detected |

The 12 hard-negative pairs were designed specifically so that exception rate and execution volume give the wrong answer — both versions throw the same exceptions at the same rate, but the behavioral structure differs. On those cases, the behavioral representation wins clearly.

This suggests the representation captures something real, but the current benchmark isn't selective enough to show it at the aggregate level.

### Hypotheses

I pre-registered 12 hypotheses before touching the test set. Of those, only two survived multiple-comparison correction (Holm-Bonferroni):

- **H7**: Dynamic features outperform static features — supported
- **H9**: Execution resolves the structural-semantic inversion problem — supported

The other ten were not supported. I've kept all of them in the docs rather than only reporting the ones that worked.

---

## Running it

```bash
# Python 3.9+ required (CPython only — sys.settrace not available on PyPy)
pip install pytest

# Run the test suite
python3 -m pytest sbg/ -q
# Expected: 516 passed

# Check reproducibility
python3 experiments/v5/reproduction_check.py
# Expected: 6/6 PASS

# Run the V5 pipeline on the test set (~30 min)
python3 baselines/v5/b07_dynamic_v5.py

# Run the hard-negative oracle
python3 benchmark/v5/hard_negatives/oracle.py

# Run regression detection
python3 experiments/v5/regression_evaluator.py
```

All results are deterministic with `SEED=42`. Expected outputs match the frozen artifacts in `artifacts/v5/`.

---

## Repository structure

```
sbg/
  extraction/       # static and dynamic genome extractors
  v3/               # DynamicGenomeV3 — the main representation
  v5/               # V5 extensions (temporal, state, rename-invariant identity)

baselines/          # comparison methods (token, AST, CFG, dynamic, full SBG)
benchmark/
  corpus/           # 99 Python base programs
  datasets/         # pairs_train/dev/val/test.jsonl (frozen splits)
  transformations/  # 12 semantics-preserving + 14 semantics-changing transforms
  v5/               # hard-negative benchmark, regression corpus, Java programs

experiments/        # experiment scripts for each research version
artifacts/          # frozen results with SHA-256 hashes

docs/
  research/         # formal model, hypotheses, prior art survey
  v3/ v4/ v5/       # versioned experiment reports
```

---

## Limitations

- The test set covers 13 programs. That's small — confidence intervals are wide (±0.15 AUROC).
- Exception rate dominates on the aggregate benchmark, which means the multi-dimensional representation doesn't add much on average.
- SC-3 (operator swap mutations like `>=` vs `>`) is only detected 24% of the time even with boundary-input generation — these require inputs that exercise the exact boundary, which is hard to synthesize automatically.
- Java support exists (infrastructure and 3 programs) but a full cross-language evaluation hasn't been run.
- Only works with CPython — `sys.settrace` isn't available on alternative Python implementations.

---

## Citation

```bibtex
@misc{sbg2025,
  title  = {Software Behavior Genome: An Empirical Study of
             Execution-Grounded Behavioral Representations for Semantic Change Detection},
  author = {Manas Sakthivel},
  year   = {2025},
  url    = {https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation},
}
```

---

## License

MIT — see [LICENSE](LICENSE).

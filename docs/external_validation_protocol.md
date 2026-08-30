# SBG — External Validation Protocol
## Phase 5: Frozen Protocol for QuixBugs Evaluation

**Sprint:** Final External Validation & Research Closure Sprint
**Status:** FROZEN — must be written before any evaluation run
**Dataset Source:** QuixBugs (https://github.com/jkoppel/QuixBugs, MIT License)

---

## 1. Dataset Description

**QuixBugs** is a real-world benchmark of single-statement bugs in classic algorithms.
Each program has exactly one bug (one wrong line) introduced by the original authors.
Programs are paired with correct versions and test cases.

| Property | Value |
|---|---|
| Source | github.com/jkoppel/QuixBugs |
| Language | Python |
| Programs | 40 total (31 with test cases available as JSON) |
| Bug type | Single-statement bugs (one wrong line per program) |
| Labels | Genuinely buggy vs. correct — from original authors |
| Provenance | Published, peer-reviewed, widely used in SE research |
| License | MIT |
| Program domain | Classic algorithms (sorting, searching, DP, graphs, strings) |

---

## 2. Inclusion Criteria

A QuixBugs program pair is INCLUDED if:

1. The buggy Python program exists at `python_programs/{name}.py`
2. The correct Python program exists at `correct_python_programs/{name}.py`
3. JSON test cases exist at `json_testcases/{name}.json` with ≥ 3 test cases
4. Both programs can be imported and executed without crashing at import time
5. The function can be identified by name (function name in source)
6. At least 3 test inputs can be successfully parsed from JSON

---

## 3. Exclusion Criteria

A program pair is EXCLUDED if:

1. It requires `node.py` (LinkedList node class) at runtime — separate handling needed
2. Import itself raises an exception (broken code)
3. No test cases available in json_testcases
4. The program's function requires a `Node` object argument that cannot be constructed
5. The function requires more than 5 seconds to run on any input (infinite loop risk)

---

## 4. Test Input Protocol

For each program pair:
- Use ALL available JSON test cases as inputs
- JSON format: `[[arg1, arg2, ...], expected]` or `[[[args...]], expected]`
- Parse inputs from line 0 (first JSON line) to last
- Cap at 10 inputs per program to keep execution time bounded
- Inputs are passed as positional arguments: `fn(*args)`

---

## 5. EEP Configuration (Frozen — identical to synthetic evaluation)

```
d_EEP(A,B) = 0.40 × d_exc_frac + 0.10 × d_exc_jaccard
           + 0.30 × d_trace_length + 0.15 × d_line_seq
           + 0.05 × d_sequential_drift
```

- τ* = 0.08 (same threshold as synthetic evaluation)
- max_events = 5000
- timeout_s = 3.0 seconds per input
- seed = 42

**CRITICAL:** The EEP feature configuration and threshold τ* are FROZEN from the synthetic evaluation. They are NOT tuned on QuixBugs data.

---

## 6. Split Policy

QuixBugs is evaluated as a **fully held-out external test set**:
- No training on QuixBugs programs
- No threshold tuning on QuixBugs
- No feature weight adjustment on QuixBugs
- All hyperparameters frozen from synthetic evaluation

This enforces **zero-shot cross-corpus generalization**: the model trained on nothing from this dataset.

---

## 7. Negative Controls

The 6 programs WITHOUT test cases (breadth_first_search, depth_first_search,
detect_cycle, minimum_spanning_tree, reverse_linked_list, topological_ordering) 
will be used as negative controls if possible: we can test whether correctly-named 
variants can be loaded without generating spurious detections.

Additionally, we will test **renaming equivalents**: programs that are semantically 
identical to correct versions with only variable name changes.

---

## 8. Evaluation Metrics

For each program pair:
- EEP distance: `d_EEP(buggy, correct)`
- Baseline distance: `d_baseline(buggy, correct)`
- Exception-only distance
- Output oracle: `output_divergence(buggy, correct)` (reference, not prediction)
- Detection flag: `d > τ*`

Aggregate:
- AUROC (with bootstrap CI)
- Detection rate (N detected / N total)
- F1, precision, recall at τ*
- False positive rate on negative controls
- Per-program results

---

## 9. Bug Class Taxonomy

For QuixBugs, each bug is classified as:
- **off_by_one**: boundary condition (loop ≤ vs <, index n vs n-1)
- **wrong_operator**: wrong comparison/arithmetic operator
- **wrong_variable**: wrong variable name or argument order
- **wrong_return**: wrong return statement or value
- **missing_return**: return statement omitted
- **wrong_recursion**: wrong recursive call
- **wrong_condition**: wrong conditional expression

Classification is based on code inspection of the diff between buggy and correct.

---

## 10. Baselines

| Baseline | Description | Fair to compare? |
|---|---|---|
| EEP (repaired) | Full EEP distance function | PRIMARY |
| Baseline proxy | 3-feature (exc_frac + exc_jac + wall_time) | YES |
| Exception-only | |d_exc_frac| only | YES |
| Output oracle | Output comparison (reference) | REFERENCE ONLY (forbidden as predictor) |

---

## 11. Reporting Policy

- Report ALL programs (no exclusion of difficult cases after evaluation)
- Report per-program results
- Report per-bug-class results
- Report cases where EEP fails to detect (with analysis)
- Report false positives (if any negative controls included)
- Compare directly with synthetic corpus results
- Explicitly note differences in program complexity

---

## 12. Reproducibility Gate

All raw program files are fetched from the public QuixBugs GitHub repository.
The exact commit hash will be recorded.
All test inputs are from publicly available JSON files.
No private or proprietary data is used.

Reproduction command:
```bash
python3 experiments/external/quixbugs_evaluation.py
```

---

*Protocol frozen before any QuixBugs evaluation run.*
*Any changes to this protocol invalidate downstream results.*

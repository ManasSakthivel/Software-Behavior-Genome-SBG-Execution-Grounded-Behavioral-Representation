# QuixBugs Implementation Fixes & Harness Engineering

## 1. Overview of Harness Defects and Corrective Actions

| Issue ID | Affected Scope | Root Cause | Implementation Fix | Verification Method |
|:---|:---|:---|:---|:---|
| **FIX-QB-01** | 9 Graph Algorithms | Forcing flat list arguments on functions expecting `Node` instances caused immediate `AttributeError` / `TypeError` on line 1. | Implemented native `Node` graph constructors (`Node(value, successor, successors, predecessors, incoming_nodes)`) supplying strongly-connected, branching, and cyclic graph topologies. | 100% clean execution without line-1 type exceptions. |
| **FIX-QB-02** | 18 Multi-Param Algorithms | Single-list inputs passed to $k$-ary functions (e.g., `gcd(a, b)`, `knapsack(cap, items)`) raised `TypeError: missing required positional argument`. | Created multi-parameter input tuples matching exact function signatures. | All multi-argument functions execute their full loop/recursion logic. |
| **FIX-QB-03** | 9 Missing JSON Testcases | Graph programs were excluded from the declared regime because test drivers were located only in `*_test.py` files. | Extracted test cases from upstream Python test drivers into native callable arguments. | Evaluated all 40 QuixBugs programs without arbitrary exclusions. |
| **FIX-QB-04** | Infinite Loop / Non-Termination | Defective programs with recursive loops (e.g. `mergesort`, `possible_change`) hung subprocesses when step caps returned `None`. | Modified `TraceCollector.trace_fn` to raise `RuntimeError("Execution step limit exceeded")` upon reaching `max_steps=2000`. | Subprocesses terminate deterministically within milliseconds. |
| **FIX-QB-05** | SP-2 Renaming Artifact | Transformation SP-2 renamed top-level function names, causing entry mismatches and artificial trace distance in equivalent negative pairs. | Added structural ordinal function lookup: resolving the top-level callable at the same ordinal AST position. | Clean identity tracing for SP-2 variants. |

---

## 2. Code Implementation Reference

The complete repaired execution driver is located at:
[`SBG_EXTERNAL_VALIDATION_WORKSPACE/quixbugs_full_forensic_eval.py`](SBG_EXTERNAL_VALIDATION_WORKSPACE/quixbugs_full_forensic_eval.py)

Key harness components:
- `Node` class definition matching upstream QuixBugs architecture.
- `get_native_test_inputs(prog_name)` returning type-correct inputs for all 40 programs.
- `execute_and_trace(func, args, max_steps)` with active step-limit exception guards.
- Multi-baseline feature extraction (`compute_sbg_distances`, `compute_static_features`).
- Leave-one-program-out Cross Validation with `StandardScaler` pipeline.

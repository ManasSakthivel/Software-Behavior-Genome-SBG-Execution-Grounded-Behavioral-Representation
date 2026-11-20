# Rename-Invariant Function Identity Design (SP-2 Fix)

**Module:** `g_ID` — Invariant Identity  
**Implementation:** [`sbg/v5/invariant_identity.py`](../../sbg/v5/invariant_identity.py)  
**Formal reference:** [`artifacts/v5/SP2_INVARIANT_DESIGN.json`](../../artifacts/v5/SP2_INVARIANT_DESIGN.json)

---

## A. Problem Statement

SP-2 (function rename) invariance is broken in the current SBG system because function identity is anchored to raw function names. A rename — even a pure cosmetic one — changes the genome key, producing a false non-zero distance between identical programs.

### Root Cause

| Layer | How names leak | Effect |
|---|---|---|
| Genome keys | `variable_assignment_counts` keyed by variable name | SP-1 broken |
| Call graph | Edges stored as `(caller_name, callee_name)` | SP-2 broken |
| State transitions | v5 `g_T` uses `func_idx` already | SP-2 fixed at trace level |
| Static alignment | No pre-trace alignment exists | SP-2 breaks before tracing |

This module addresses the **static alignment gap**: given two programs A and B (one a rename of the other), identify which function in A corresponds to which in B, without using names.

### Relationship to `g_T`

[`StateTransitionGenome`](../../sbg/v5/state_transition_genome.py) is rename-invariant at the **trace level** (it uses `func_idx` from first-call order). `g_ID` provides **pre-trace structural fingerprints** that enable:

1. Verifying two programs are structurally equivalent before tracing.
2. Aligning functions across programs so `func_idx` assignments are consistent.
3. Computing a rename-invariant program-level identity hash.

---

## B. FunctionFingerprint Design

Each function is reduced to a `FunctionFingerprint` — a compact structural descriptor from which all identifier names have been removed.

### Fields

| Field | Type | Invariant to |
|---|---|---|
| `param_count` | int | param names, variable names |
| `has_return_value` | bool | all names |
| `has_default_params` | bool | all names |
| `has_varargs` | bool | all names |
| `n_branches` | int | all names |
| `n_recursive_calls` | int | all names (count only) |
| `has_loop` | bool | all names |
| `has_nested_loop` | bool | all names |
| `has_exception_handler` | bool | all names |
| `nesting_depth` | int | all names |
| `comprehension_count` | int | all names |
| `literal_types` | str | literal values (types only) |
| `builtin_calls` | str | variable names |
| **`body_structure_hash`** | str | **all names, all values** |
| `n_module_fn_calls` | int | callee names (count only) |

### Invariance Proofs

**Variable rename** → `body_structure_hash` walks only AST node type names. `ast.Name` nodes emit the string `"Name"`, never the `.id` value. All integer/bool fields are count-only. **Invariant by construction.**

**Function rename** → The function name is never stored in any field. `body_structure_hash` walks only the function *body* (not the `def` header). **Invariant by construction.**

**Parameter rename** → Argument names are `ast.arg` nodes; the walk emits `"arg"` not the `.arg` string. `param_count` is a count. **Invariant by construction.**

**Comments/whitespace** → `ast.parse` strips all comments and normalises whitespace before any walk. **Invariant by construction.**

**Dead-code insertion** → Each function is fingerprinted independently. A new, uncalled function in the module does not affect any existing function's fingerprint. **Invariant by construction.**

---

## C. Body Structure Hash

The `body_structure_hash` is the primary structural identity for a function. It captures the *shape* of the AST — operator types, control flow topology, expression structure — without any names or values.

### Algorithm

```
1. Walk all AST nodes reachable from function body in field order (DFS).
2. For each node, emit: type(node).__name__   (e.g. "If", "BinOp", "Return")
3. Join with "/"
4. SHA-256 the UTF-8 string → take first 8 hex characters
```

### Example

```python
def f(x):
    if x > 0:
        return x
```

Walk emits: `If / Compare / Name / Constant / Gt / Return / Name`

The node types `Name` are emitted but the actual names `x` and `x` are **not**. Renaming `x` to `value` produces the identical sequence and identical hash.

### What Is Included vs. Excluded

| Included | Excluded |
|---|---|
| Node type sequence (`If`, `BinOp`, `Return`, …) | `ast.Name.id` (variable/function names) |
| Tree shape (child order) | `ast.Constant.value` (literal values) |
| Operator types (`ast.Add`, `ast.Gt`, …) | `ast.arg.arg` (parameter names) |
| Comparison types | `ast.Attribute.attr` (attribute names) |

---

## D. Similarity Function

```
fingerprint_similarity(fp1, fp2) → float in [0, 1]
```

Weighted sum of per-field similarity scores:

| Field | Weight | Score function |
|---|---:|---|
| `body_structure_hash` | 4.0 | 1.0 if equal, 0.0 otherwise |
| `param_count` | 2.0 | `1 - |a-b| / max(a,b)` |
| `n_branches` | 2.0 | `1 - |a-b| / max(a,b)` |
| `nesting_depth` | 1.5 | `1 - |a-b| / max(a,b)` |
| `comprehension_count` | 1.5 | `1 - |a-b| / max(a,b)` |
| `literal_types` | 1.5 | exact string match |
| `builtin_calls` | 1.5 | exact string match |
| `has_return_value` | 1.0 | 1.0 if equal |
| `has_loop` | 1.0 | 1.0 if equal |
| `has_nested_loop` | 1.0 | 1.0 if equal |
| `has_exception_handler` | 1.0 | 1.0 if equal |
| `n_recursive_calls` | 1.0 | `1 - |a-b| / max(a,b)` |
| `n_module_fn_calls` | 1.0 | `1 - |a-b| / max(a,b)` |
| `has_default_params` | 0.5 | 1.0 if equal |
| `has_varargs` | 0.5 | 1.0 if equal |

**Identity property:** `fingerprint_similarity(fp, fp) == 1.0` — verified by T12.

---

## E. Matching Algorithm

```
match_functions(fps_a, fps_b, threshold=0.4) → List[(idx_a, idx_b, score)]
```

**Greedy bipartite matching:**

1. Compute all |A| × |B| pairwise similarity scores.
2. Filter to pairs with `score ≥ threshold`.
3. Sort by descending similarity.
4. Greedily assign: take the best pair where neither index has been matched yet.
5. Return matched triples `(idx_a, idx_b, score)` sorted by descending score.

**Complexity:** O(|A| × |B| × log(|A||B|)) — suitable for module-scale programs.

**Threshold rationale:** `0.4` balances recall (correctly match renamed functions) vs. precision (reject structurally unrelated functions). Identical renamed functions score 1.0.

---

## F. Program Identity

```
compute_program_identity(program_text) → ProgramIdentity
```

### Fields

| Field | Description |
|---|---|
| `fingerprints` | `List[FunctionFingerprint]` in definition order |
| `call_graph` | `Dict[int, List[int]]` — caller index → callee indices. **No names stored.** |
| `root_index` | Index of root function (not called by any other) |
| `program_hash` | SHA-256[:16] of sorted body structure hashes — rename-invariant |

### Root Selection

1. **Primary:** Function whose index does not appear in any other function's callee list.
2. **Tiebreak (if multiple roots):** `(lowest n_branches, highest param_count)` — purely structural.
3. **Fallback (all cyclic):** `root_index = 0`.

### Program Hash Construction

```
sorted_bodies = sorted(fp.body_structure_hash for fp in fingerprints)
program_hash  = SHA-256("|".join(sorted_bodies))[:16]
```

Sorting makes the hash invariant to function definition order. Using `body_structure_hash` values makes it invariant to all renames.

---

## G. Test Coverage

| Test | Description | Result |
|---|---|---|
| T01 | Variable rename → same fingerprint | PASS |
| T02 | Function rename → same fingerprint | PASS |
| T03 | Parameter rename → same fingerprint | PASS |
| T04 | Semantically different → different fingerprints | PASS |
| T05 | Loop vs no-loop → different `has_loop` | PASS |
| T06 | `body_structure_hash` ignores variable names | PASS |
| T07 | `match_functions` aligns renamed program functions | PASS |
| T08 | `compute_program_identity` finds correct root | PASS |
| T09 | Dead-code insertion doesn't change other fingerprints | PASS |
| T10 | Comment insertion doesn't change fingerprint | PASS |
| T11 | `program_hash` is stable across renames | PASS |
| T12 | `fingerprint_similarity` returns 1.0 for identical structures | PASS |

**12 / 12 PASS**

Run with:
```
python3 sbg/v5/invariant_identity.py
```

---

## H. Integration Notes

- **No external dependencies.** `ast`, `hashlib`, `collections`, `itertools`, `dataclasses`, `typing` only.
- **Complement to `g_T`:** Use `compute_program_identity` to align programs structurally before computing `StateTransitionGenome` distances. This ensures `func_idx` assignments are consistent across aligned programs.
- **Drop-in alignment:** `match_functions` returns `(idx_a, idx_b, score)` triples; use these to reindex one program's `call_graph` before Jaccard distance computation.

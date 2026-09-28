# State-Transition Genome Design (v5)

**Genome dimension:** `g_T`  
**Formal reference:** Definition 11 extension — see `STATE_TRANSITION_DESIGN.json`  
**Implementation:** [`sbg/v5/state_transition_genome.py`](../../sbg/v5/state_transition_genome.py)

---

## A. Current State Model — What Exists and What Is Missing

### What the Current State Genome Captures

The existing [`StateGenome`](../../sbg/extraction/dynamic/state_genome.py) (g_S) aggregates state features from execution traces into six scalar/histogram summaries:

| Field | What it measures | What it loses |
|---|---|---|
| `variable_assignment_counts` | How often each name appeared | No sequence, no abstract value shape |
| `state_space_size` | Number of distinct snapshots | No path through the space |
| `mutation_rate` | Fraction of pairs with any change | Which variables changed, and how |
| `heap_object_types` | Type histogram | No lifecycle (create/mutate/delete) |
| `stack_depth_profile` | Depth histogram | No call structure |
| `state_transition_count` | Raw count of variable changes | No structural identity of transitions |

The [`Tracer`](../../sbg/extraction/dynamic/tracer.py) captures four event types per step — `call`, `return`, `exception`, `line` — each with a full `local_vars_snapshot` (repr-capped at 100 chars). The v2 [`TraceNormalizer`](../../sbg/v2/execution/normalizer.py) goes further by anonymising function names to first-call-order integer indices.

### What Is Currently Recorded vs What Is Missing

```
                   Tracer            StateGenome       g_T (new)
                   ──────────────    ──────────────    ──────────────────────────
Event types        ✓ call/ret/exc/ln  ✗ counted only   ✓ structured per pair
Per-var abstract   ✗ only repr str    ✗                 ✓ ZERO/POSITIVE/NULL/…
Transition key     ✗                 ✗                  ✓ (func_idx, pre, ek, post)
Lifecycle          ✗                 ✗ counts only      ✓ create / mutate / delete
Resource seq.      ✗                 ✗                  ✓ acquire → release
Error path         ✗                 ✗                  ✓ NORMAL → EXCEPTION → NORMAL
Data flow          ✗                 ✗                  ✓ ABSENT → value (producer)
Rename-invariant   ✗ uses fn names   ✓ (via key sets)   ✓ func_idx + abstract labels
```

---

## B. State Transition Graph Design

### Core Concepts

**Abstract Value Domain** — a fixed set of labels that abstract away concrete values:

```
Scalar:     ZERO | POSITIVE | NEGATIVE | NULL | NON_NULL
Collection: EMPTY_COLLECTION | SINGLETON | MULTI_ELEMENT
Control:    EXCEPTION_STATE | NORMAL
Sentinels:  ABSENT | UNKNOWN
```

**Transition Key** (a 4-tuple, always integer × 3 strings):

```
TransitionKey = (func_idx: int, pre_state: str, event_kind: str, post_state: str)
```

**Transition Graph** = `Dict[TransitionKey, frequency]`

**Invariants by construction:**
- `func_idx` is the anonymous integer index (first-call order), never the function name → **SP-2 invariant**
- `pre_state` / `post_state` are abstract labels, never repr strings or variable names → **SP-1 invariant**
- Only abstract-value-*changing* pairs generate transitions → **compact representation**

---

## C. Six Specific Feature Categories

### 1. `state_creation_events`
Variable absent in `snap_pre`, present in `snap_post`:

```
(func_idx, ABSENT, state_creation, post_abstract_value)
```

### 2. `state_mutation_events`
Variable present in both snapshots, abstract value changed:

```
(func_idx, pre_abstract_value, state_mutation, post_abstract_value)
  e.g.  (0, ZERO, state_mutation, POSITIVE)
```

### 3. `state_deletion_events`
Variable present in `snap_pre`, absent in `snap_post`:

```
(func_idx, pre_abstract_value, state_deletion, ABSENT)
```

### 4. `resource_acquisition_releases`
Variable name matches heuristic pattern (`file`, `lock`, `conn`, `socket`, `fd`, `fp`, `handle`, `mutex`, `resource`):

```
NULL   → NON_NULL:  (func_idx, NULL,    resource_acquire, NON_NULL)
NON_NULL → NULL:    (func_idx, NON_NULL, resource_release, NULL)
```

This allows detection of **resource leak bugs** (acquire without release) and **double-free patterns** (release without prior acquire).

### 5. `error_state_transitions`
The tracer fires an `"exception"` event type on uncaught exceptions. We additionally emit a per-event-pair control-flow record:

```
Normal → Error:     (func_idx, NORMAL,          error_transition, EXCEPTION_STATE)
Error  → Recovery:  (func_idx, EXCEPTION_STATE, error_recovery,   NORMAL)
```

### 6. `data_flow_transitions`
A variable appearing for the first time in scope (ABSENT → value) outside an exception context signals that the prior step produced a value now in scope — a proxy for a data-flow edge:

```
(func_idx, ABSENT, data_flow, post_abstract_value)
```

---

## D. Canonicalization

Four normalisation steps applied by [`StateTransitionGenome.canonicalize()`](../../sbg/v5/state_transition_genome.py):

| Step | Operation | Rationale |
|---|---|---|
| 1. Drop zero/negative | Remove transitions with freq ≤ 0 | Clean artefacts |
| 2. Sort keys | `(func_idx ASC, pre LEX, event_kind LEX, post LEX)` | Deterministic ordering for comparison and hashing |
| 3. Normalise frequencies | `freq / total` → float `[0,1]` rounded to 6 dp | Scale-invariance across traces of different lengths |
| 4. Rebuild metadata | Recompute `event_kind_totals`, `has_error_states` | Consistency |

**Idempotence:** `canonicalize(canonicalize(g)) == canonicalize(g)` — verified by test 8.

---

## E. Distance Function

### Formula

Let T = T₁ ∪ T₂ (union of all transition keys from both graphs):

```
         Σ_{k ∈ T1 ∩ T2}  min(f1(k), f2(k))
S  =  ──────────────────────────────────────────
         Σ_{k ∈ T1 ∪ T2}  max(f1(k), f2(k))

d(g1, g2) = 1 − S    ∈ [0, 1]
```

This is a **frequency-weighted Jaccard similarity** turned into a distance.

### Properties

| Property | Proof |
|---|---|
| `d(g, g) = 0` | min(f,f) = max(f,f) always → S = 1 |
| `d(g1,g2) = d(g2,g1)` | min and max are symmetric |
| `d ∈ [0, 1]` | numerator ≤ denominator (min ≤ max), so ratio ∈ [0,1] |

### Why frequency-weighted vs plain Jaccard?

A mutation from `ZERO → POSITIVE` that happens 1,000 times (tight loop) is behaviorally more significant than the same transition appearing once. Weighted Jaccard penalises frequency mismatches, making SC-1 (off-by-one) detectable even when the abstract state vocabulary is identical.

---

## F. Sensitivity Analysis

### SC-3: Operator Mutation (`a + b` → `a - b`)

The result variable's abstract value may change sign: `POSITIVE → NEGATIVE`.

```
Before:  (func_idx, ZERO, state_mutation, POSITIVE)
After:   (func_idx, ZERO, state_mutation, NEGATIVE)
```

These are **different transition keys** → `d > 0`. **Detected with HIGH confidence.**

### SC-1: Off-by-One (`range(n)` → `range(n+1)`)

An additional loop-body execution appends one more occurrence of each intra-loop transition, and potentially adds a new boundary transition if the counter crosses zero on the extra iteration.

- **Frequency difference** → weighted Jaccard penalises it even without a new key.
- If boundary crosses zero: `POSITIVE → ZERO` key appears that didn't before.

**Detected with MEDIUM confidence** (higher when abstract boundary is crossed).

### SC-11: Wrong Variable (`result = x` → `result = y`)

If `x` and `y` have different abstract values (e.g. `x = POSITIVE`, `y = NULL`), the mutation transition post_state changes: `POSITIVE → NULL`. **Detected with HIGH confidence**. If both happen to have the same abstract value, the transition key is identical → undetected.

### SP-2: Function Rename (`def compute()` → `def calculate()`)

`func_idx` is assigned by first-call order in trace, not by name. Same call order → same index → **identical transition keys**. **Completely invariant by construction.**

### SP-1: Variable Rename (`counter = 0` → `idx = 0`)

Variable names are **never stored** in transition keys. Only the abstract label `ZERO` participates. **Completely invariant by construction.**

---

## G. Implementation Overview

```
sbg/v5/
  __init__.py
  state_transition_genome.py
    ├── _repr_to_abstract(r: str) → str          # repr → abstract domain label
    ├── StateTransitionGraph                      # g_T dataclass
    └── StateTransitionGenome
          ├── extract(traces) → StateTransitionGraph
          ├── distance(g1, g2) → float [0,1]
          └── canonicalize(graph) → StateTransitionGraph
```

### Event Kind Constants

| Constant | Meaning |
|---|---|
| `EK_CREATE` | `state_creation` — variable appeared |
| `EK_MUTATE` | `state_mutation` — abstract value changed |
| `EK_DELETE` | `state_deletion` — variable left scope |
| `EK_ACQUIRE` | `resource_acquire` — resource variable acquired |
| `EK_RELEASE` | `resource_release` — resource variable released |
| `EK_ERROR` | `error_transition` — normal → exception |
| `EK_RECOVER` | `error_recovery` — exception → normal |
| `EK_DATAFLOW` | `data_flow` — value appeared via data flow |

### Unit Tests (8)

| # | Test | What it checks |
|---|---|---|
| 1 | `test_repr_to_abstract` | All abstract domain mappings correct |
| 2 | `test_extract_empty` | Empty trace list → empty graph |
| 3 | `test_extract_mutation` | ZERO→POSITIVE mutation recorded |
| 4 | `test_extract_creation_deletion` | ABSENT→value and value→ABSENT transitions |
| 5 | `test_extract_error_state` | Exception event type → error/recovery transitions |
| 6 | `test_resource_acquire_release` | `file` variable NULL→NON_NULL→NULL |
| 7 | `test_distance_properties` | Reflexivity, symmetry, range [0,1] |
| 8 | `test_canonicalize_idempotent` | Canonical form stable, sorted, marked |

### Running Tests

```bash
python sbg/v5/state_transition_genome.py
# or
python -m pytest sbg/v5/state_transition_genome.py -v
```

---

## Relationship to Existing Genome Dimensions

```
g_U  ExecutionGenome     — coverage, call counts, hot path hash
g_S  StateGenome         — mutation rate, heap types, stack depth (aggregate)
g_R  ResourceGenome      — execution time, exception rate, var count
g_D  DynamicGenome (v2)  — rename-invariant call freq, coverage consistency
g_T  StateTransitionGraph (v5, NEW)
       — sequenced abstract state transitions, resource lifecycle,
         error paths, data flow, frequency-weighted Jaccard distance
```

`g_T` is **complementary** to all existing dimensions: it is the first representation that explicitly models *how* program state evolves step-by-step rather than *what* aggregate distributions were observed.

---

*See also:* [`artifacts/v5/STATE_TRANSITION_DESIGN.json`](../../artifacts/v5/STATE_TRANSITION_DESIGN.json) for the machine-readable specification.

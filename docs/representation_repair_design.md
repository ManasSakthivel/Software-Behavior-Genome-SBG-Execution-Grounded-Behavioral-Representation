# SBG — Representation Repair Design
## Phase 5: Formal Design Before Implementation

**Sprint:** Final Representation Repair & Empirical Validation Sprint
**Status:** FROZEN design — to be implemented in Phase 6

---

## 1. Problem Statement

The current output-free SBG proxy (3 features) detects 5/38 = 13.2% of real regressions.
33/38 missed bugs produce NO exception change and NO meaningful timing change.
They change only return values through control-flow-neutral operations.

However, the diagnosis in `docs/missing_behavior_analysis.md` shows:
- 18+ of 33 missed cases DO produce observable STRUCTURAL differences
- These differences manifest as: different trace length, different iteration count,
  different recursion depth — all control-flow properties
- The current proxy does NOT capture these

---

## 2. Candidate Repairs

### Candidate A — Per-Input Execution Profile (SELECTED — PRIMARY)

**Exact definition:**
For each input `i` in the canonical input set of size N, compute:
```
profile(P) = [trace_length(P, i₁), trace_length(P, i₂), ..., trace_length(P, iₙ)]
```
where `trace_length(P, iₖ) = number of sys.settrace events captured for input iₖ`.

**Normalized representation:**
Each trace length is normalized by the maximum observed:
```
norm_profile(P) = profile(P) / max(max(profile(A)), max(profile(B)), 1)
```

**Distance function:**
```
d_profile(A, B) = (1/N) * Σ |norm_profile(A)[i] - norm_profile(B)[i]|
```
= per-input L1 distance between normalized trace length vectors

**Mathematical representation:**
d_profile: ℝᴺ × ℝᴺ → [0, 1]
- d(P, P) = 0 (identity)
- d(A, B) = d(B, A) (symmetric)
- range ⊂ [0, 1] (bounded)

**Normalization:** Divide by max observed trace length across both programs.
Alternative: normalize by N_inputs × max_events. Both work.

**Output-free guarantee:**
- `trace_length` = cardinality of TraceEvent list = structural control-flow feature
- CANNOT distinguish two programs that take the SAME branches but compute different values
- DOES distinguish programs that take DIFFERENT branches or different iteration counts
- No access to return_value, stdout, stderr, or any program output

**Potential leakage risk:** NONE under the following careful check:
A mutation that changes ONLY the final returned expression (same control flow, same branches)
will have IDENTICAL trace lengths. This is the CORRECT behavior: such a mutation is
invisible to structural analysis (which is exactly what our output-free premise accepts).

**Expected benefit:**
- Off-by-one in loops: direct trace length change
- Missing break: direct trace length change
- Wrong variable in loop (branch changes): indirect trace length change
- Wrong slice in recursion: depth changes → trace length changes
- Mutable default accumulation: trace length changes on repeated calls

**Computational complexity:** O(N × max_events) per program — same as current tracing cost.

**Deterministic behavior:** YES — trace length is deterministic for deterministic programs
with fixed seed. Mutable defaults add non-determinism which is itself the behavioral signal.

---

### Candidate B — Per-Input Line-Sequence Fingerprint

**Definition:**
For each input `i`, compute a fingerprint of the SEQUENCE of line numbers executed:
```
seq_hash(P, i) = hash([(fn₁, l₁), (fn₂, l₂), ..., (fnₖ, lₖ)])
```
where (fn, l) are (function_name, line_number) pairs from call/line events.

**Distance:**
```
d_linesig(A, B) = fraction of inputs where seq_hash(A, i) ≠ seq_hash(B, i)
```

**Output-free justification:**
Line sequences capture CONTROL FLOW structure — which code is executed, in what order.
This is NOT the return value. Two programs computing `return x+1` vs `return x+2`
with identical control flow will have IDENTICAL line sequences.

**Sensitivity:**
More sensitive than trace length: captures branch selection, not just iteration count.
Can detect wrong operator in conditional, missing break, off-by-one in bounds.

**Risk:** Over-sensitive — structural refactoring (SP-2 type transforms) may change line
numbers even when semantics are preserved. Mitigated by: function-anonymization and
using only line NUMBER WITHIN FUNCTION (relative line offset), not absolute line number.

**Decision:** Include as secondary feature in the combined repair.

---

### Candidate C — Recursive Depth Profile Per Input

**Definition:**
For each input `i`, compute the MAXIMUM call stack depth reached during execution:
```
max_depth(P, i) = max call stack depth in trace(P, i)
```

**Distance:**
```
d_depth_profile(A, B) = (1/N) × Σ |norm_depth(A, i) - norm_depth(B, i)|
```

**Output-free:** YES — call depth is a structural property.

**Benefit:** Detects changes in recursion depth (wrong slice, wrong base case in some inputs).

**Decision:** Include as tertiary feature.

---

### Candidate D — Sequential Call Divergence (Mutable State Detection)

**Definition:**
Run MULTIPLE IDENTICAL INPUTS SEQUENTIALLY through the same function instance.
If the function has hidden state (mutable default argument), behavior will differ
on the 2nd call versus the 1st.

```
state_drift(P) = distance(trace(P, i₁_first_call), trace(P, i₁_second_call))
```

**Output-free:** YES — measures structural change in execution across calls, not output.

**Benefit:** Directly detects mutable default argument bugs.

**Decision:** Include as specialized feature.

---

## 3. Selected Repair: Extended Execution Profile Distance (EEP)

The most scientifically justified single repair that addresses the maximum number of
failure classes is a combination of Candidates A + B:

```
d_EEP(A, B) = α × d_trace_length_profile(A, B)
             + β × d_line_seq_divergence(A, B)
             + γ × d_depth_profile(A, B)
             + δ × d_state_drift(A, B)
```

**Combined SBG-Repair distance:**
```
d_repair(A, B) = 0.50 × d_current_sbg(A, B)    # preserve existing signal
               + 0.25 × d_EEP(A, B)             # new: execution profile
               + 0.25 × d_line_sig(A, B)         # new: line sequence
```

**Weights rationale:**
- Existing SBG at 0.50: preserves exception-detection signal for F6/missing-edge cases
- EEP at 0.25: new primary structural signal for F2/F3/F7/F8/F9
- Line signature at 0.25: secondary signal for F1/F4

---

## 4. Feature Specification: trace_length_profile_distance

| Attribute | Value |
|---|---|
| Input | Two lists of ExecutionTrace objects (one per program) |
| Output | float in [0, 1] |
| Formula | L1(normalized_length_A, normalized_length_B) / N_inputs |
| Normalization | divide by max(max_len_A, max_len_B, 1) per input position |
| Distance | L1 between normalized vectors |
| Complexity | O(N × max_events) — same as tracing |
| Deterministic | YES for deterministic programs |
| Output-free | YES — counts events only, never reads values |
| Leakage test | Programs differing only in final return value → distance = 0.0 |

---

## 5. Feature Specification: line_sequence_divergence

| Attribute | Value |
|---|---|
| Input | Two lists of ExecutionTrace objects |
| Output | float in [0, 1] |
| Formula | fraction of inputs with different anonymized line sequences |
| Normalization | anonymize by function-call-order index (rename-invariant) |
| Distance | fraction mismatch |
| Complexity | O(N × max_events) |
| Deterministic | YES |
| Output-free | YES — line numbers are structural |
| Leakage test | Identical control flow, different return value → distance = 0.0 |

---

## 6. Output-Free Guarantee Formal Statement

**Theorem (informal):** Let P₁ and P₂ be programs that differ only in a final return expression,
with identical control flow, branches, loop iterations, function call counts, and call depths.
Then:
- d_trace_length_profile(P₁, P₂) = 0
- d_line_seq_divergence(P₁, P₂) = 0
- d_depth_profile(P₁, P₂) = 0

BECAUSE: the trace length, line sequence, and call depth are fully determined by
which code paths execute and how many times — not by what values are computed along those paths.

**Counterexample to check:** What if a conditional branches on the RETURN VALUE of an inner call?
E.g., `if inner() > 0: do_something()`. Here the return value of `inner()` determines
which branch executes. Is this output leakage?

Answer: NO. This is a legitimate behavioral difference. If `inner()` returns a different value
(due to a bug), the outer conditional takes a different branch — this IS a structural change
observable in the execution profile. The profile distance > 0 reflects that the BUG CAUSES
DIFFERENT STRUCTURAL BEHAVIOR. We are not reading the OUTPUT; we are observing the
downstream effect of the output on control flow. This is a key distinction.

---

## 7. Failure Classes Addressed

| Class | Representative | Mechanism | Expected detection? |
|---|---|---|---|
| F2: Off-by-one (loop) | E12, E03 | Loop count changes trace length | YES |
| F3: Wrong variable (branch) | E14, E15 | Branch taken changes differ | PARTIAL |
| F4: Wrong slice (recursion) | E19 | Recursion depth changes | YES |
| F7: Mutable default | E20, REG_12 | Sequential call divergence | YES |
| F8: Missing break | REG_11 | Loop runs longer → trace length | YES |
| F9: Mutation during iter | REG_09 | Fewer iterations → trace length | YES |

**Expected newly-detectable:** approximately 10-15 cases out of 33 missed.
Conservative bound after accounting for:
- Some inputs may not expose the divergent path
- Same canonical inputs used for both programs

**Cases NOT expected to improve:**
- F5 (wrong base case returns 0 vs 1): pure value change, same structure
- F1 (wrong arithmetic operator with same branches): value change, same structure
- REG_03, REG_07, REG_14: operator swap with identical loop/branch structure

---

*This design is frozen. Implementation proceeds in Phase 6.*
*See experiments/repair/phase6_repair_implementation.py for implementation.*

# SBG — Missing Behavior Analysis
## Phase 2 Output: Determining What is Observable Without Outputs

**Sprint:** Final Representation Repair & Empirical Validation Sprint
**Status:** Analysis complete — feeds into Phase 4/5 design

---

## 1. Preamble

The Phase 1 forensic classification established that 33/38 regressions are missed by the current
output-free proxy. This document answers, for each failure class:

- **Question A:** Can the behavioral difference be observed through execution structure alone?
- **Question B:** Does SBG currently encode that information?
- **Question C:** If not, can it be encoded without observing program output?
- **Question D:** Would adding it preserve the output-free research definition?

---

## 2. Failure Class Analysis

### Class F1 — Wrong Operator (arithmetic, comparison, logical)

**Representative cases:** REG_03 (wrong_comparison_operator), REG_07 (integer_division_truncation),
E01 (parens_wrong_return), E04 (gcd_wrong_mod), E09 (rotate_wrong_direction),
E11 (gray_code_wrong_shift), E18 (max_vs_min)

**What changed in program behavior?**
The computation produces a different RETURN VALUE on affected inputs, but:
- The same code paths are executed
- The same functions are called
- The same number of iterations occur
- No exception is raised
- Execution timing is nearly identical

**Question A — Observable without output?**
In most cases, NO for the specific output value. HOWEVER:

For some operators, there are **observable execution-structure consequences**:
- Loop termination: wrong operator in a loop condition can change iteration count
- Branch selection: `>=` vs `>` at a boundary changes which branch is taken
- Recursion depth: wrong base-case operator can change recursion depth

The key observable: **per-line variable snapshots** (already captured by sys.settrace).
When the tracer records `local_vars_snapshot`, it captures the intermediate state of
variables at every `line` event. This is NOT the return value — it's intermediate computation.

For `gcd(48, 18)` with buggy `b%a` vs correct `a%b`:
- Correct: a,b sequence = (48,18) → (18,12) → (12,6) → (6,0)
- Buggy: a,b sequence = (48,18) → (18,18) → (18,18) → ... (infinite loop or ZeroDivisionError)
- The INTERMEDIATE STATE at the assignment line differs measurably

**Question B — Does SBG currently encode this?**
NO. The current 3-feature proxy (`exception_fraction`, `exception_types`, `wall_time`) does
not use `local_vars_snapshot` data. The full V3 genome also does not use local variable state
— it uses call sequences and coverage only.

**Question C — Can it be encoded without output?**
YES — with a critical design choice:

Instead of comparing exact variable values (which would encode output semantics),
we can compare **abstract type signatures of local variable states**:
- Variable type at each line (int, str, list, bool, NoneType...)
- Variable count changes (loop accumulator growth patterns)
- Boolean-valued variable transitions (True→False, False→True)
- Variable existence patterns (None vs non-None)

OR we can use **execution path line-sequence hashing** — the sequence of (function, lineno)
pairs executed for each input. If a wrong operator causes a different code branch to be
taken, the line sequence changes, even if the final value doesn't create an exception.

**Question D — Preserves output-free definition?**
YES for type signatures and line-sequence hashing.
RISKY for concrete variable values.

---

### Class F2 — Off-By-One (loop bounds, index, range)

**Representative cases:** REG_01 (binary_search_off_by_one — DETECTED), REG_04
(loop_fencepost_error), E03 (sum_range_off_by_one), E07 (sieve_wrong_range),
E08 (edit_distance_wrong_return), E12 (reverse_off_by_one), E16 (string_search_off_by_one)

**What changed in program behavior?**
- `range(n)` vs `range(1,n+1)`: loop variable `i` takes different values; same iteration count
- `i>0` vs `i>=0`: one fewer iteration of the while loop
- `n-m` vs `n-m+1`: one fewer iteration of the for loop

For REG_01 (DETECTED): The binary search off-by-one causes an **IndexError** on specific inputs
(array boundary access), which is why it's detected. This confirms: exceptions are observable.

For E12 (`i>0` vs `i>=0`): The loop executes one fewer time. The LOOP ITERATION COUNT changes.
This is observable via:
- Number of `line` events inside the loop body
- The total number of trace events (trace length) for that input

**Question B — Does SBG currently encode this?**
PARTIALLY. `coverage_size` captures the set of distinct lines executed (which doesn't change
for same-code-path loops). `trace_length_mean` (V3) captures total event count — but with
low weight and high noise.

**Question C — Can it be encoded?**
YES — **per-input trace length** (not just mean) is a precise, output-free signal.
For an off-by-one in a loop over N items, the buggy version executes exactly
`N-1 * loop_body_size` events vs `N * loop_body_size`. This is:
- Observable from trace event count
- Not the return value
- Different from exception behavior

**Design:** Per-input event count histogram or normalized per-input trace length vector.

---

### Class F3 — Wrong Variable (wrong index, wrong accumulator)

**Representative cases:** REG_05 (wrong_variable_in_product), REG_10 (wrong_index_access),
E06 (max_subarray_no_restart), E14 (max_missing_update), E15 (remove_dupes_wrong_compare),
E17 (flatten_wrong_variable), QB08 (wrong_operator)

**What changed in program behavior?**
Using `r[0]` instead of `r[-1]` for comparison: the BRANCH taken at the comparison line
may differ, affecting whether `r.append(x)` is called. This changes:
- Whether certain lines are executed (append call vs. skip)
- The SIZE of intermediate data structures (if append is called differently)

For E14 (max_missing_update): `if x>m: pass` vs `if x>m: m=x`
- Same branch conditions (same comparison evaluations)
- Different assignment executed → different variable state at subsequent lines
- No structural change to call graph or coverage set (same lines visited!)

**Question A — Observable?**
For E14: The `if x>m:` branch evaluates the same way both programs. The difference is
whether the assignment in the true branch executes. The assignment IS a traceable line event.
But in the BUGGY version, the `if` body contains only `pass` (no event), while the correct
version has `m=x` (a line event). This means:

**The SET OF EXECUTED LINES DIFFERS** even though the branch structure is the same:
- Correct: line for `m=x` appears in trace coverage
- Buggy: line for `pass` or empty body — may not generate an event

**For the regression evaluator** (inline functions): Both programs are defined as closures,
not source files, so line numbers may be allocated differently. The line-set comparison
may or may not work. However, the TRACE LENGTH still differs (one fewer line event per
loop iteration where the condition is true).

**Question C — Can it be encoded?**
YES via:
1. Per-input trace length (counts the actual number of events executed)
2. Line-number sequence fingerprinting (sensitive to which lines execute)

---

### Class F4 — Wrong Slice

**Representative cases:** REG_13 (wrong_string_slicing), E02 (palindrome_wrong_slice),
E19 (lcs_wrong_recursion)

**What changed?**
Slice bounds determine how much of a data structure is processed. For `s[1:]` vs `s[:]`:
- Recursion depth may differ (LCS with wrong slice terminates earlier or later)
- Number of recursive calls differs → call count changes

For E19 (lcs_wrong_recursion): `t[:-2]` vs `t[:-1]` — the wrong slice makes the string
shorter than intended at each recursive step. This changes RECURSION DEPTH — an observable
structural feature.

**Question B:** Not currently well-encoded. Call frequency captures function call count,
but the specific depth profile for recursive functions differs.

**Question C:** YES — call depth profile per input (not just mean) captures recursion changes.

---

### Class F5 — Wrong Base Case

**Representative cases:** E05 (power_wrong_base_case), E13 (climb_stairs_wrong_base), REG_15

**What changed?**
Base case `exp==0: return 0` vs `return 1`. The base case is reached for certain inputs.
When reached:
- The return value differs (0 vs 1)
- The recursion UNWINDS with a different value propagating up
- All recursive calls execute identically until the base case

**Observable without output?**
The base case itself is a specific LINE in the code. If the wrong base case returns `0`
vs `1`, the only observable difference is the VALUE returned. There is NO structural
difference in call graph, coverage, or trace length.

**Question C:** This is the HARDEST class. The only observable without output:
- The base case LINE executes (traceable) — SAME in both programs
- Intermediate state: the local variable `exp==0` evaluates True — but we'd need to
  observe the variable STATE to know this

**Partial encoding possible:** Variable type/None-ness at specific lines can hint at this.
For `return 0` vs `return 1`: both are int — no type difference. This class may be
fundamentally hard without output observation for all inputs.

---

### Class F6 — Missing Edge Case

**Representative cases:** REG_02 (missing_base_case_empty_list — DETECTED),
REG_06 (missing_empty_guard — DETECTED), E10 (brackets_missing_empty_check)

**Status:** 2/3 already DETECTED via exception signals.

E10 misses because `return True` vs `return len(stk)==0` — on the input `("(("`:
- Buggy returns True (wrong)
- Correct returns False
- No exception on either; no structural difference

Same analysis as F1 — return-value only, no structural difference.

---

### Class F7 — Mutable Default

**Representative cases:** REG_12 (mutable_default_argument), E20 (fib_mutable_default)

**What changed?**
The mutable default dict/list accumulates state across calls. On subsequent calls,
the buggy version returns different results due to accumulated state. This is a
**cross-call state dependency** — the behavioral difference emerges only when
the function is called MULTIPLE TIMES.

**Observable without output?**
YES! The state accumulation is observable as a difference in TRACE BEHAVIOR across
sequential calls:
- Call 1: both buggy and correct behave identically (empty dict/list)
- Call 2: buggy has accumulated state; branch taken by `if n in memo` differs

The LINE SEQUENCE for call 2 differs if `memo` already contains `n`:
- Buggy: takes the early-return path (`return memo[n]`) for previously seen inputs
- Correct: always starts with empty memo

This changes the **branching pattern** across calls — observable as a change in
coverage/trace length on the SECOND execution of the same function.

**Design:** Use sequential inputs in a fixed order and track trace-length/coverage
CHANGE between successive calls. If behavior changes across sequential calls,
the function has state-dependent behavior.

---

### Class F8 — Missing Break

**Representative cases:** REG_11 (missing_break_finds_last)

**What changed?**
The loop continues past the first match (finds last instead of first). This means
the loop body executes MORE times than expected:
- Correct: loop terminates at first match → N/2 iterations on average
- Buggy: loop runs to completion → N iterations always

**Observable without output?** YES — trace length is directly observable and changes.

---

### Class F9 — Mutation During Iteration

**Representative cases:** REG_09 (mutation_during_iteration)

**What changed?**
Modifying a list while iterating over it causes non-deterministic skipping.
On Python, this doesn't raise an exception but silently skips elements.
The iteration count is reduced → trace length changes.

**Observable?** YES — per-input trace length changes when elements are skipped.

---

## 3. Summary Table

| Failure Class | N cases | Observable w/o output? | Current SBG encodes? | Proposed feature |
|---|---|---|---|---|
| F1: Wrong operator | 8 | PARTIALLY (line seq) | NO | Per-input line sequence hash |
| F2: Off-by-one (loop) | 6 | YES (trace length) | PARTIAL | Per-input trace length vector |
| F3: Wrong variable | 5 | PARTIALLY (branch trace) | NO | Per-input trace length vector |
| F4: Wrong slice | 3 | YES (recursion depth) | NO | Per-input depth profile |
| F5: Wrong base case | 3 | HARD (value-only) | NO | Partial: type-at-line |
| F6: Missing edge case | 3 | YES (exception) | YES (2/3) | Already captured |
| F7: Mutable default | 2 | YES (cross-call state) | NO | Sequential-call divergence |
| F8: Missing break | 1 | YES (trace length) | NO | Per-input trace length |
| F9: Mutation during iter | 1 | YES (trace length) | NO | Per-input trace length |

**Key finding:** Classes F2, F3, F4, F7, F8, F9 (18 cases) are detectable via trace-length
or execution-depth signals WITHOUT using return values. Class F1 is partially detectable
via line-sequence hashing. Class F5 (3 cases) remains fundamentally hard.

**Expected improvement from principled repair:** 15-20 additional detections out of 33 missed.
Conservative estimate: from 5/38 (13.2%) to ~18-23/38 (47-61%).

---

## 4. The Core Proposed Feature: Per-Input Execution Profile

**Name:** `execution_profile_distance`

**Definition:** For each input `i`, compute the normalized trace length
`tl(P, i) = |trace_events(P, i)| / max_events`. Compare the vectors
across inputs: `d_profile = L1(tl_A, tl_B) / N_inputs`.

**Why this works:**
- Off-by-one in a loop: directly changes trace length
- Missing break: directly changes trace length
- Wrong variable in accumulator: changes branch count
- Wrong slice in recursion: changes recursion depth → trace length
- Mutable default (repeated calls): trace length changes across sequential calls

**Why this is output-free:**
- Trace length = number of sys.settrace events = control flow structure
- Does NOT encode what value was computed
- Does NOT read return_value, stdout, or stderr
- Two programs with identical control flow (same branch paths, same iteration counts)
  will have identical trace lengths regardless of what values they compute at the return

**Output-free guarantee:** Two programs that differ ONLY in the FINAL RETURN VALUE
(with identical control flow) will have IDENTICAL trace lengths. The only way trace
length differs is if control flow differs (different branches, different loop iterations).

**Leakage risk:** LOW — trace length is a structural/control-flow property, not a value property.
The one risk: if a program's loop runs to `n` (derived from a parameter) and returns `f(n)`,
a mutation that changes `f` but not `n` will have the same trace length (as intended —
the control flow is the same). The output differs but trace length does not → this is
CORRECT behavior for an output-free system.

---

*Analysis complete. See docs/representation_repair_design.md for formal design.*

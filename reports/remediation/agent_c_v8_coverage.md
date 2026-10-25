# Agent C: v8 entry-point coverage, class-driver assessment, class-tier policy

Branch `remediation/sbg-v2`. Read-only analysis. No source, test or data file was modified and nothing was
committed. The `test` split was not read or scored. All numbers below were produced by scripts run from the
repo root against the committed `benchmark/datasets/v6/pairs_{train,dev,val}.jsonl` (47 base programs, 1852 pairs;
see §1 and §6) and `benchmark/corpus/base_programs/`.

## 0. Summary

* The "580 explicit failures" in `docs/current/ENTRY_POINT_POLICY.md` and `docs/CLAIMS_REGISTRY.yaml` (C018) is
  reproduced **exactly**. It is a count of **EQUIVALENT pairs** (out of 954) whose base *or* variant makes
  `select_entry_structural` raise. It is not a count of programs.
* At program level the same defect is **29 of 47 base programs** failing (16 `NoEntryPoint`, 11
  `AmbiguousEntryPoint`, 2 `UnsupportedSignature`); **18** succeed.
* The doc's phrase "mostly class-based programs" is only roughly true: **299 / 580 (51.6 %)** of the failing pairs
  have a side with no function entry (`NoEntryPoint`): 293 belong to the 16 class-based programs, 6 are SP-7 variants
  of two function-plus-class programs whose only function was inlined away (a class tier recovers them, but as a
  mixed-tier pair); **281 / 580 (48.4 %)** are
  `AmbiguousEntryPoint` / `UnsupportedSignature` function-only programs that no class tier can recover.
* The current class driver is not rename-invariant, and the problem is bigger than "alphabetical ordering": the
  *eligibility* filter is also name-based (`_` prefix, `Test` prefix). On the committed v6 variants the
  alphabetical driver order differs between base and variant for 25 / 293 class-program EQUIVALENT pairs, all SP-2.
  It **still** differs for 25 / 48 non-no-op variants produced by the *repaired* SP-2 transformer.
* The "sort by sha256 of normalized AST" ordering proposed in the task is rename-invariant but **not invariant under
  the other semantics-preserving transformations** (SP-3/5/6/8/11 change method bodies): it reorders the driven
  sequence in 106 / 293 pairs (vs 25 for the status quo). It should not be adopted as specified. A coarse
  interface key with declaration-order tie-break differs in only 15 / 293 v6 pairs, all dangling-reference SP-2 defect pairs (0 / 48 for source order under the repaired SP-2; §5).
* **Recommendation:** Option 1 (function-only, class programs `not_evaluable`) as the frozen primary v8 policy.
  Option 2 is recommended as a *pre-declared, dev-validated secondary stratum*, using the corrected ordering key in
  §5, not the raw-fingerprint key. Option 3 is not recommended.

## 1. Reproduction of the failures

Command: the script in the task, extended to also count pairs (exit status 0, no exceptions other than the three
`EntryPointError` subclasses; no pair file lacked its `base_path`).

### 1.1 Program level (the script as given): 47 programs

| Category | Programs | train | dev | val |
|---|---|---|---|---|
| `ok` | **18** | 11 | 4 | 3 |
| `NoEntryPoint` | **16** | 10 | 4 | 2 |
| `AmbiguousEntryPoint` | **11** | 7 | 1 | 3 |
| `UnsupportedSignature` | **2** | 0 | 1 | 1 |
| total | 47 | 28 | 10 | 9 |

Programs per category:

* **ok (18):** err_validation_chain→`validate`, file_log_processor→`summary`, graph_dijkstra→`reconstruct_path`,
  math_dynamic_programming→`knapsack_01`, parse_json_subset→`parse_json`, sort_mergesort→`mergesort`,
  sort_binary_search→`binary_search`, sort_radix_sort→`radix_sort`, str_kmp_search→`kmp_count`,
  str_edit_distance→`edit_distance_bounded`, str_word_frequency→`top_n_words` (train); file_csv_aggregator→`load_csv`,
  fsm_parser_state→`parse_dsv`, graph_connected_components→`_same_partition`, sort_quicksort→`quicksort` (dev);
  math_polynomial→`poly_roots_bisection`, parse_ini_config→`parse_ini`, sort_timsort_runs→`timsort_runs` (val).
* **NoEntryPoint (16):** api_mock_http_client, api_rest_crud_mock, conc_thread_safe_counter, ds_min_heap, ds_trie,
  ds_lru_cache, fsm_connection_pool, fsm_traffic_light, res_memory_allocator, res_task_scheduler (train);
  api_event_bus, ds_stack_queue, err_circuit_breaker, res_cache_ttl (dev); ds_binary_search_tree,
  fsm_order_lifecycle (val).
* **UnsupportedSignature (2):** math_numerical_integration (dev; candidates `trapezoid`, `simpsons`,
  `adaptive_simpsons`), conc_producer_consumer (val; candidate `run_pipeline`).
* **AmbiguousEntryPoint (11):**

  | Program | split | tied candidates |
  |---|---|---|
  | err_retry_backoff | train | retry_with_backoff, retry_with_backoff_no_sleep |
  | file_binary_encoder | train | 7 (encode/decode_base64, _hex, _nibble_rle, checksum_xor) |
  | graph_topological_sort | train | topological_sort_kahn, topological_sort_dfs |
  | graph_bellman_ford | train | bellman_ford, reconstruct_path |
  | math_prime_sieve | train | is_prime, goldbach |
  | math_matrix_ops | train | mat_add, mat_mul |
  | sort_topk_select | train | quickselect, top_k_elements |
  | str_run_length_encode | dev | compression_ratio, is_beneficial |
  | file_word_count_stream | val | _extract_words, process_stream, merge_counters |
  | graph_cycle_detect_dfs | val | has_cycle_directed, has_cycle_undirected |
  | str_anagram_groups | val | find_anagram_pairs, longest_anagram_group, ungrouped_words |

  These are multi-function "library" programs with several parallel public APIs of equal call-graph rank. This is
  a different problem from classes (§7.3).

### 1.2 Pair level: the 580

954 EQUIVALENT pairs (559 train, 213 dev, 182 val). A pair "fails" if the base or the variant raises:

| (base, variant) | Pairs |
|---|---|
| NoEntry / NoEntry | 281 |
| Ambiguous / Ambiguous | 211 |
| Unsupported / Unsupported | 44 |
| Ambiguous → ok | 21 |
| NoEntry → ok | 12 |
| ok → NoEntry | 6 |
| ok → Ambiguous | 5 |
| **Total failing** | **580** (= 281+211+44+21+12+6+5) |
| both ok | 374 |

Mixed outcomes (44 pairs) come from SP-7 (inline) and SP-8 (extract), the transformations that legitimately
change the call graph (breakdown: SP-8 NoEntry→ok 11, SP-8 Ambiguous→ok 10, SP-7 Ambiguous→ok 11, SP-7 ok→NoEntry 6,
SP-7 ok→Ambiguous 4, SP-8 ok→Ambiguous 1, SP-6 NoEntry→ok 1).

Class-tier-recoverable pairs (at least one side `NoEntryPoint`: NoEntry/NoEntry 281 + NoEntry→ok 12 + ok→NoEntry 6) =
**299** (293 from the 16 class programs plus the 6 SP-7 pairs of parse_json_subset / parse_ini_config). Non-class remainder (Ambiguous + Unsupported, 211+44+21+5) = **281**. 299 + 281 = 580.

By transformation, the pure-failure pairs are spread evenly (SP-1…SP-6 each 37–48 NoEntry/NoEntry, 26–33
Ambiguous/Ambiguous); this is a program-level property, not a transformation-level one.

The CHANGED pairs fail for the same reason: 588 of 898 CHANGED pairs fail (§6), but the 580 figure counts only
EQUIVALENT.

## 2. NoEntryPoint cases (16 programs)

Message split: 15 × `only self-test drivers are defined`, 1 × `no top-level function`.

| Class | Description | Programs | Count |
|---|---|---|---|
| (a) pure class, no module-level function | `class` only, `__main__` guard inline | err_circuit_breaker | **1** |
| (b) functions only inside classes | every one of the 16 has ≥ 1 public class with methods; the only module-level functions are the scaffolding in (c). Strictly "methods and nothing else" = same single program as (a) | (a) | 1 |
| (c) class(es) + driver-only module functions | module level has only self-test/driver functions: 14 programs with `test_*` carrying `assert`s; conc_thread_safe_counter has `stress_test()` (no asserts, called from the main guard) | the other 15 | **15** |

So the real answer to "are they class-only?": all 16 are class programs; 15 have a `test_*`/driver function
at module level that v8 (correctly) excludes as scaffolding, 1 has no function at all. None has a module-level
*API* function. Every one has ≥ 1 class accepted by `class_driver.eligible_classes`
(e.g. api_mock_http_client: `MockRequest`, `MockResponse`, `MockServer`; ds_stack_queue: `Deque`, `Queue`,
`Stack`), so the class tier would have a target in all 16.

Representative source (first 30 lines of err_circuit_breaker, category (a); the rest of the file is one class and
the `if __name__ == "__main__":` block at line 65):

```python
"""
program_id: err_circuit_breaker
category: Error Handling
spec_version: 1.0
spec: Circuit breaker pattern: CLOSED->OPEN on failure threshold, HALF_OPEN after timeout.
"""
import time


class CircuitBreaker:
    """
    Three-state circuit breaker.
    ...
    """
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=3, cooldown_seconds=5.0):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = self.CLOSED
        self.failure_count = 0
        self.opened_at = None

    def call(self, func, *args):
```

Category (c) example (ds_min_heap): a 10-method `MinHeap` class (line 24 onward) followed by `def test_min_heap():`
with `assert` statements (line 104) called from the main guard (line 170). conc_thread_safe_counter: `ThreadSafeCounter`
(lines 10–40), then `stress_test(n_threads=10, n_increments=1000)` (line 42) which is only reached from the guard.

Per-program structure (module-level functions / classes with method counts):

| Program | Module functions | Classes (methods) |
|---|---|---|
| api_mock_http_client | test_mock_http | MockRequest(0) MockResponse(1) MockServer(3) MockClient(4) +RoutingError |
| api_rest_crud_mock | test_rest_crud_mock | MockAPIResponse(1) MockRESTAPI(9) |
| conc_thread_safe_counter | stress_test | ThreadSafeCounter(5) |
| ds_min_heap | test_min_heap | MinHeap(10) |
| ds_trie | test_trie | _TrieNode(1) Trie(12) |
| ds_lru_cache | test_lru_cache | _DNode(1) LRUCache(10) |
| fsm_connection_pool | test_connection_pool | Connection(2) ConnectionPool(10) + 2 enums |
| fsm_traffic_light | test_traffic_light | TrafficLight(9) + enum |
| res_memory_allocator | test_memory_allocator | _Block(1) MemoryAllocator(6) |
| res_task_scheduler | test_task_scheduler | Task(0) TaskScheduler(5) + enum |
| api_event_bus | test_event_bus | Event(0) EventBus(8) |
| ds_stack_queue | test_stack, test_queue, test_deque, test_all | Stack(6) Queue(6) Deque(9) |
| err_circuit_breaker | none | CircuitBreaker(4) |
| res_cache_ttl | test_cache_ttl | CacheTTL(9) |
| ds_binary_search_tree | test_bst | BinarySearchTree(13) |
| fsm_order_lifecycle | test_order_lifecycle | Order(13) |

Note api_mock_http_client's `MockClient` is not class-tier eligible (constructor parameter is not synthesisable), and
enum/`Enum` subclasses are `constructor_inherited_from_external_base`. A class tier drives only the eligible subset.

## 3. UnsupportedSignature cases (2 programs, 44 EQUIVALENT pairs)

Both are **function** programs, not class programs.

| Program | Unsupported parameter | Why |
|---|---|---|
| math_numerical_integration | `f: Callable[[float], float]` on `trapezoid`, `simpsons`, `adaptive_simpsons` | `protocol._UNSUPPORTED` contains `Callable`; no battery |
| conc_producer_consumer | `producer_fn: Callable`, `consumer_fn: Callable` on `run_pipeline` | same |

**Could a battery extension support them?**

* math_numerical_integration: yes, plausibly. A small fixed battery of pure, deterministic callables
  (`lambda x: x`, `x*x`, constants, `math.sin`) defined in the harness would cover `Callable[[float], float]`.
  Costs: (i) the callables' own frames appear in the trace unless added to `HARNESS_CODE` (the tracer records
  `frame.f_code.co_name`), so they must be registered; (ii) `repr` of a function includes an address, so inputs
  must be wrapped like `_Plan.__repr__`; (iii) it changes `protocol.BATTERIES`, which would alter the input set for
  every historical protocol that shares `annotation_family`, so it needs a v8-only battery. This recovers 1
  program / 24 EQUIVALENT pairs.
* conc_producer_consumer: not reasonably. `producer_fn` must return an iterable and `consumer_fn` must accept an
  item; the program also spawns threads over a bounded queue. Arbitrary callables would crash or hang, and thread
  interleaving makes the trace non-deterministic. Leave as `not_evaluable`.

Net: 2 programs / 44 pairs; at most 1 recoverable with a v8-only `Callable` battery.

## 4. Class-driver assessment (`experiments/final/class_driver.py`)

### 4.1 What it does

* Applies only when the v8 function tier raises `NoEntryPoint` (`extraction._extract_v8`, lines 301–310); other
  failure kinds (Ambiguous, Unsupported) are *not* routed to the class tier.
* `eligible_classes(tree)`: for each top-level class in `sorted(classes)`, excludes `_`-prefixed and `Test*` classes,
  exception classes, abstract classes, classes whose constructor is inherited from a non-module base or has a
  non-synthesisable parameter.
* Methods: `for method_name in sorted(functions)`, dropping names starting with `_` (including dunders), async
  methods, properties/accessors, and methods with non-synthesisable parameters. Inherited methods are merged via an
  in-module MRO.
* `build_plan`: one trace per (eligible class, battery index i) for i in 0..10 (`BATTERY_SIZE`). Each trace
  constructs the class from battery index i and then makes `L = 8` calls: step k calls
  `methods[(i + k) % len(methods)]` with battery index `(i + k) % 11`, arguments pickled/unpickled so no stdlib frames
  enter the trace. `drive` never reads a return value.
* Output: `ClassPlan(Name[i])` input reprs, `entry_detail["rename_invariant"] = False` set by the caller.

### 4.2 Why it is not rename-invariant

Three name-dependent decisions, all in `eligible_classes`:

1. **Order of classes:** `sorted(classes)` (line `for name in sorted(classes)`), alphabetical by class name.
2. **Order of methods:** `sorted(functions)`, alphabetical by method name. Because step k indexes
   `methods[(i+k) % len(methods)]`, renaming a method moves it in the list and changes *which method is called at
   every step of every trace*, hence the whole trace.
3. **Eligibility by spelling:** `method_name.startswith("_")` and the class `_`/`Test` prefix. SP-2 adds the prefix
   `fn_` to many names, so `_swap` → `fn__swap` becomes public and enters the driven set; `len(methods)` changes,
   which changes the modulus and therefore every step.

Item 3 is a separate and underappreciated source of non-invariance: fixing only the sort order would not make the
driver rename-invariant.

Measured on the committed v6 variants of the 16 class programs (293 EQUIVALENT pairs). Metric: sequence of
*declaration indices* of the methods the driver would call, base vs variant:

| Driver | Pairs with a different driven sequence |
|---|---|
| status quo, alphabetical (v6 variants) | **25 / 293** (all SP-2; spread over 13 of the 16 class programs) |
| status quo, alphabetical, repaired SP-2 (working-tree `sp2_function_rename.py`, 3 seeds × 16 programs, 48 non-no-op variants) | **25 / 48** |

The second line is the important one: the SP-2 label-defect fix does not repair the class driver. The two issues are
independent.

### 4.3 What a rename-invariant class driver looks like

Replace every spelling-derived decision by a structural one:

1. **Eligibility:** drop the `_`/`Test` prefix rules and the dunder rule in favour of structural ones, e.g. a method
   referenced as `self.<m>` by another method of the same class is a helper (mirror of the function-tier "referenced
   by a non-driver function" rule); dunder methods stay excluded because dunder names are protocol, not spelling
   (SP-2 skips them: `_collect_function_names` ignores `__x__`). Exception classes are already detected from *base
   class* names, which no current SP renames.
2. **Method order:** sort by a key that no semantics-preserving rewrite changes (§5) with a deterministic
   tie-break.
3. **Class order:** sort classes by the sorted tuple of their method keys, then by source position.
4. Keep `_Plan`, `drive`, `STEPS_PER_TRACE`, pickled arguments and `HARNESS_CODE` registration unchanged.

### 4.4 Feasibility

Yes, without external dependencies: only `ast`, `hashlib`, `pickle`, which `class_driver.py` / `entry_policy.py`
already import. The change is localised to `eligible_classes` (the sort keys and the helper filter): on the order
of 30–50 lines plus tests, and no change to the traced driver itself. It is *not* free: it changes the class-tier
trace of every class program, so it must be frozen under a new protocol id, validated on dev only, and the
pre-registration (`PHASE2_PREREGISTRATION.md` §1) describes the alphabetical rule, so a new pre-registration entry
is required.

## 5. Specification of "rename-invariant structural ordering"

### 5.1 The proposed key, tested

The task proposes ordering methods by `sha256(normalised AST)`. I implemented it with the same normaliser idea as
`entry_policy.structural_id` (identifiers → slots, method names → `<m>`, docstring dropped) and measured how often
the driven sequence differs between base and variant across the 293 EQUIVALENT class-program pairs (class set held
fixed, only the method ordering varied):

| Ordering key | Pairs where base/variant driven sequence differs | By transformation |
|---|---|---|
| declaration (source) order | 15 | SP-2 only (all are old-SP-2 dangling `self.m()` variants; see below) |
| coarse interface key `(required-param annotations, is_static, return annotation)`, declaration-order tie-break | 15 | SP-2 only (same pairs) |
| `sha256` of normalised AST (as proposed) | **106** | SP-2 16, SP-3 44, SP-6 29, SP-5 8, SP-8 5, SP-11 4 |

Conclusion: a body fingerprint is invariant to *renaming* but not to the other semantics-preserving edits (dead
code SP-3, loop rewrite SP-5, condition rewrite SP-6, extraction SP-8, data structure SP-11), all of which change the
AST of the method bodies. Used as the ordering key it would trade one instability (SP-2) for five. It is fine for
*identifying* an entry (as in the function tier, where a tie is an error) but wrong as a *positional ordering* key
when the benchmark's equivalence relation includes body rewrites.

The 15 residual differences for source/coarse ordering all correspond to v6 SP-2 variants with dangling
`self.<renamed>()` references (every one of the 15 has more unresolved `self.method()` calls in the variant than
in the base); those are the documented label-defect pairs, not an ordering defect. With the repaired SP-2 the
source-order driver gives **0 / 48** differences (the coarse key was measured only on the v6 variants, where it matches source order pair for pair), and the fingerprint order also 0 / 48 (SP-2 alone
is body-preserving).

### 5.2 Recommended definition

* **Method key:** `(is_static, tuple of required-parameter annotation texts, return annotation text)`; none of
  these is touched by a rename or by SP-3/5/6/8/11.
* **Tie-break:** declaration order (`ast.ClassDef.body` position). Ties are common (many methods share
  `(self)` with no annotation), so the tie-break does most of the work; this is stated as an assumption, not hidden.
* **Class key:** the tuple of the class's method keys, then declaration order.
* **What is and is not guaranteed:** invariant to identifier renaming and to every v6/v7 SP transformation tested.
  Not invariant to a pure *reordering* of method definitions among methods with equal keys (the function-tier
  `reorder` test in `tests/test_entry_policy.py` does hold for function selection; it would not for the class
  driver). If reordering invariance is required, the fingerprint can be used **only as a secondary tie-break within
  equal-key methods**, but then SP-3/5/6 body edits can permute tied methods, so the two properties cannot both
  be had from AST content alone. The choice must be declared in the plan.
* The original wording ("order by sha256 of normalised AST, not by name") should be amended in
  `EVALUATION_PLAN_V8.md` §4 option 2 ("sort methods by structural id") accordingly.

## 6. Coverage cost

Counts are over train/dev/val of v6. "Evaluable pair" = base and variant both obtain an entry (function tier
for Option 1; function tier or class tier for Options 2/3). Option 1 numbers come from `select_entry_structural`
only. Option 2/3 numbers are statically derived from the same rule used by `extraction._extract_v8`
(function tier raises `NoEntryPoint` and `eligible_classes` is non-empty). For the 954 EQUIVALENT pairs I also
ran the real `extract_program(..., "output_free_v8")` to confirm (673 ok, 211+44+21+5 failing; it agrees).

### 6.1 Under the current v8 function-only policy (Option 1)

| | train | dev | val | total |
|---|---|---|---|---|
| base programs | 28 | 10 | 9 | 47 |
| programs with ≥ 1 evaluable pair | 11 | 4 | 3 | **18 (38.3 %)** |
| programs not evaluable | 17 | 6 | 6 | **29** |
| pairs total | 1129 | 372 | 351 | 1852 |
| evaluable pairs | 411 | 142 | 131 | **684 (36.9 %)** |

Pair relations: 898 CHANGED + 954 EQUIVALENT.

| Relation | total | evaluable | not evaluable |
|---|---|---|---|
| EQUIVALENT | 954 | **374** | **580** |
| CHANGED | 898 | 310 | 588 |
| both | 1852 | 684 | 1168 |

The 580 in the document is therefore the EQUIVALENT-only slice of 1168 non-evaluable pairs. For CHANGED pairs
the picture is: class,class 363 and function,function 310 evaluable by tier, fail,fail 219, function→fail 6.

Not-evaluable breakdown (programs / EQUIVALENT pairs): class-tier-recoverable 16 programs (+2 partial) / 299 pairs (18 of them mixed-tier, see below); Ambiguous 11 / 237 (211+21+5); Unsupported 2 / 44.

Of the 374 evaluable EQUIVALENT pairs, 49 have different entry *names* in base and variant (renames, which
the structural id is designed to absorb); 99 differ in structural id (body rewrites change the fingerprint
legitimately); 12 fail `interfaces_correspond` (SP-7 6, SP-8 6) and would have to be excluded by a pre-declared rule,
leaving **362** usable EQUIVALENT pairs. All 18 evaluable programs also contribute CHANGED pairs.

### 6.2 Under each option

| | Option 1 function-only | Option 2 invariant class tier | Option 3 alphabetical class tier, flagged |
|---|---|---|---|
| programs evaluable | 18 / 47 (38 %) | 34 / 47 (72 %) | 34 / 47 (72 %) |
| train / dev / val programs | 11 / 4 / 3 | 21 / 8 / 5 | 21 / 8 / 5 |
| EQUIVALENT pairs | 374 | 673 → 655 after dropping 18 mixed-tier pairs | same 673 / 655 |
| CHANGED pairs | 310 | 673 | 673 |
| all pairs | 684 (36.9 %) | 1346 (72.7 %); 1328 after mixed-tier exclusion | same |
| still failing | 29 programs | 13 programs (11 Ambiguous + 2 Unsupported) / 281 EQ pairs | same |
| rename-invariant | yes | yes (with §5.2 key; fingerprint key fails) | **no**: 25 / 293 class EQ pairs differ in v6 variants; 25 / 48 under repaired SP-2 |
| new code | none | ~30–50 lines, new tests, new protocol id, new pre-reg | none (already in `_extract_v8`) |

"Mixed-tier" = 18 EQUIVALENT pairs whose base and variant land in different tiers. 12 have a class base and a
*function* variant (SP-8 extracts `_extracted_N_M` from the test function and v8 selects that helper, 11 pairs;
SP-6 rewrites the `if __name__ == "__main__":` guard of conc_thread_safe_counter (seed 1: `if not __name__ !=
'__main__':`) so it is no longer recognised and the driver `stress_test` is picked, 1 pair). 6 are the reverse
(SP-7 inlines the only function of parse_json_subset / parse_ini_config, leaving a function base and a class
variant). Scoring them
compares two different traced things and should be excluded by a pre-declared rule.

Option 2 and Option 3 have the same coverage; they differ only in whether the class tier is
rename-invariant.

## 7. Recommendation

### 7.1 Choice

**Primary policy: Option 1** (function-only; class programs → `not_evaluable`).
**Pre-declared secondary stratum: Option 2** (rename-invariant class tier, §5.2), only if implemented and
validated on dev before the plan is frozen, reported separately, and never mixed into the primary number.
**Reject Option 3.**

### 7.2 Justification

* **Correctness:** Option 1 is the only option whose every trace is selected by a rule shown rename-invariant. Option 3
  puts a component into the primary result that this analysis shows differs between base and variant in 25 / 48
  pairs, even after the SP-2 repair; it would contaminate exactly the instability that v8 exists to remove.
* **Simplicity:** Option 1 needs no new code and no new pre-registration, and the data are already produced.
  Option 2 needs a new driver ordering, the removal of the name-based eligibility filters (§4.2 item 3), a new
  protocol id, new tests and a new pre-registration; and its ordering key cannot be the raw AST fingerprint (§5.1).
* **Coverage:** Option 1 is expensive (18 / 47 programs, 684 / 1852 pairs; 362 usable EQ pairs). Option 2
  recovers 16 programs (all class programs) and nearly doubles pairs, and it is the only way to reintroduce the
  stateful programs (heaps, tries, caches, FSMs, locks) which are a distinct behavioural family. That is a real
  loss for a paper claiming general behavioural distance, so it should not be discarded; it should be a labelled
  secondary analysis.
* **Fit to the plan:** `EVALUATION_PLAN_V8.md` §2 recommends writing ≥ 30 new programs so that ≥ 20 survive. Under
  Option 1 the observed survival rate on the current corpus is 18 / 47 = 38 %, so ~30 programs yield ~11–12
  survivors, which is **below** the plan's target of 20. Under Option 2 the survival rate is 72 %: 30 programs →
  ~22. Either write ≥ 50 programs, authored so that each has a single unambiguous root function, or make Option 2
  part of the frozen protocol. This should be decided before data are written; it is the main way the policy
  choice affects the plan.

### 7.3 Two things Option 2 does not fix (and the plan should say so)

* 11 Ambiguous programs (237 EQ pairs) are the largest non-class loss after classes and are untouched by any of
  the three options. They are multi-API function modules. A multi-root driver (trace every root, as the class tier
  already does for methods) would recover them, but that is a larger protocol change than the task assumes.
* 2 Unsupported programs (44 pairs); 1 may be recoverable with a v8-only `Callable` battery (§3).

## 8. Additional threats to validity

1. **Pair vs program unit.** 580 is a pair count. Programs are the unit of independence (cluster bootstrap in the
   plan). The effective sample after v8 is 18 programs (Option 1) or 34 (Option 2), not 684 or 1346 pairs.
2. **Sample of 18 includes questionable entries.** graph_dijkstra→`reconstruct_path` (a helper, not `dijkstra`),
   graph_connected_components→`_same_partition` (a test-support predicate), file_log_processor→`summary`,
   str_edit_distance→`edit_distance_bounded`. `ENTRY_POINT_POLICY.md` already notes one such case in the test set
   (`graph_bfs_shortest_path→reconstruct_path`). The policy picks a defensible *structural* root, not necessarily the
   program's primary API; these should be listed in the report and must not be hand-fixed after seeing scores.
3. **SP-8 manufactures entries.** On driver-only class programs SP-8 extracts a block from the test function
   into `_extracted_N_M`; v8 then picks it as an "entry" (11 pairs). Because the extracted helper may have
   parameters taken from the test's locals, the traced behaviour is unrelated to the class API. These "NoEntry → ok"
   pairs look like successes if only failure kinds are counted. Gate on `interfaces_correspond` plus a tier check.
4. **The main-guard detector is syntactic.** SP-6 rewrites `if __name__ == "__main__":` into a negated form in
   conc_thread_safe_counter, so `_is_main_guard` no longer matches and a driver is selected (1 pair). This is a
   transformation-invariance gap in `entry_policy` that is separate from renaming and applies to any program whose
   only driver is identified through the guard. Currently 1 pair; it will recur on new data.
5. **SP-7 can delete the entry** (parse_json_subset, parse_ini_config: the whole function inlined away, 6 pairs).
6. **Selection effect on the coverage filter.** Survivors under Option 1 are disproportionately pure
   algorithms (sorting, string, parsing). Any claim about "behavioural distance" then rests on stateless programs;
   class-based stateful programs, the structurally hardest case, are removed by construction. State this in the
   claim boundary (it is in `LIMITATIONS`-style language only implicitly in C018 "coverage ... is low").
7. **Pickle/step rotation.** `methods[(i+k) % len(methods)]` makes the trace depend on `len(methods)`; any
   transformation that adds or removes a *public* method (SP-8 adds only `_`-prefixed names today, so is excluded)
   would alter the whole sequence. The §5.2 helper rule must run before the length is taken.
8. **Dataset coupling.** The class programs are exactly the programs hit by the SP-2 label defect (75 flagged
   pairs). Any Option 2/3 numbers on v6 variants are confounded with that defect; v7 regeneration
   (`benchmark/datasets/v7`, currently a smoke test of 133 pairs) is a prerequisite for a clean class-tier
   evaluation.
9. **Scope of this study.** Statically derived tier assignment for CHANGED pairs (not extracted); extraction
   was run for the 954 EQUIVALENT pairs only. The fingerprint/ordering experiments hold the driven-class set fixed
   and measure driven-sequence equality, not actual SBG distances; a final decision needs dev-split distance
   measurements. The test split was not touched.

## 9. Reproduction notes

Scripts were run from the repo root and kept outside the repository (`/tmp/agc/t1.py` … `t12.py`); all inputs are
the committed files, `git status` before/after shows no change to tracked or other files by this analysis (the only
other untracked file seen, `reports/remediation/agent_d_baselines_stats.md`, belongs to Agent D).
Core checks:

* failure categories: `select_entry_structural(path.read_text())` for each EQUIVALENT pair's base and variant, grouped
  by `EntryPointError.kind`;
* tier assignment: add `eligible_classes(ast.parse(src))` when the function tier raised `NoEntryPoint`
  (mirrors `extraction._extract_v8`);
* validation of the tier rule: `extract_program(path, {}, "output_free_v8")` for all 954 EQUIVALENT pairs
  (11 min wall clock) produced 673 ok (374 function tier, 299 class tier with `rename_invariant=False`) and
  the failing counts above;
* ordering experiments: the `method key` variants of §5 applied to base and variant, comparing the
  resulting sequences (the class set held fixed), plus the repaired SP-2
  (`FunctionRenameTransformation().apply(src, seed)` for seeds 0–2 on the 16 class programs).

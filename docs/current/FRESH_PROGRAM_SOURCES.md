# Fresh program sources (candidate base programs for the v8 confirmatory split)

Status: **reference for whoever writes the programs. Not frozen, not approved.** Companion to
`EVALUATION_PLAN_V8.md` (§2 option A) and `reports/remediation/agent_e_fresh_dataset.md`
(rationale, power, order of operations). Nothing in this list has been written, generated,
traced or scored.

Hard rule: **no fresh program may be given to the variant generator, the extractor, or any
baseline until the transformer code is frozen and the program has passed the static screening
in §5.** Programs may be edited only before that point, and never on the basis of a score.

Quota: write **≥ 30** (recommended 36) so that **≥ 20** (recommended ≥ 24) have evaluated
pairs. The plan's hard floor is 15 evaluated programs (§8 of the plan).

---

## 1. Eligibility criteria

A program is eligible only if **all** hold.

| # | Criterion | How checked |
|---|---|---|
| E1 | Python only, **standard library only**, no third-party imports, no imports of repo code | AST import scan |
| E2 | Self-contained **single file**, **< 300 lines** (target 80–220; the existing 64 range 19–257, median 155) | `wc -l` |
| E3 | Runs under **Python 3.13 (canonical) and 3.9 (floor)**: no `match`, no `X \| Y` in runtime-evaluated annotations (use `from __future__ import annotations` or `typing`), no 3.10+ stdlib API | run on both |
| E4 | Importing the module has **no side effects** (no printing, no I/O, no threads started, no sleeping) | import in subprocess |
| E5 | **Deterministic**: no `random` without a fixed internal seed (prefer an explicit LCG), no wall clock, no `time.sleep`, no `os.environ`, no file or network access, no dependence on `hash()` of str or on dict/set ordering beyond insertion order | review + two runs identical |
| E6 | At least one function or class with a **testable API** whose behaviour is described in a spec docstring | review |
| E7 | A self-test that `assert`s on ≥ 6 cases and is called from an `if __name__ == "__main__":` guard (same convention as the 64), exits 0 | run |
| E8 | **Enough algorithmic content** for meaningful SP and SC variants: ≥ 2 functions or ≥ 4 methods, ≥ 3 distinct control-flow constructs (loop / conditional / early return / exception), at least one numeric or comparison operator and one integer literal that a mutation can change in code reachable from the entry | review + generator pre-check (observable SC site exists) |
| E9 | **Not derived from the existing corpus**: not in the 64, not in `benchmark/v5/corpus/base_programs/`, not in `external/quixbugs/`, not in `benchmark/regression/`, `benchmark/cross_language/`, `external/bugsinpy/` (all of which were used or scored); algorithm family not in the exclusion list of §2 unless flagged `family_overlap=true` | §5 screening |
| E10 | **Entry-resolvable by construction** (see template §4): the v8 static selector `experiments/final/entry_policy.select_entry_structural` returns exactly one function entry on the base program, parameters annotated with types the fixed batteries can supply (`list`, `str`, `int`, `float`, `bool`, `dict`) | run selector (static only) |
| E11 | Licence/provenance recorded; adapted code only from MIT/BSD/PSF/Apache-2.0/CC0/public domain | provenance file |
| E12 | A program may be **class-based only if** it is counted in the stateful subgroup (§4.2) and the owner's class-tier decision (plan §4) is recorded | review |

Fresh = never scored and not derived from anything scored. "Write from scratch" is the
preferred route (clean-room from a textbook description). Adaptation of public, permissively
licensed code is acceptable only with the provenance record in §6. Owner confirmation of this
reading is open decision D1 in the Agent E report.

---

## 2. Exclusion list (do **not** use these algorithms/programs)

* The 64 in `benchmark/corpus/base_programs/` (60 assigned + 4 unassigned:
  `err_assert_guard`, `math_fibonacci`, `sort_insertion_sort`, `str_palindrome`).
* `benchmark/v5/corpus/base_programs/`: Huffman, interval merge, iterative/recursive
  Fibonacci, divide-and-conquer (closest pair), union-find, AVL tree, ring-buffer deque,
  segment tree, exception hierarchy, resource guard, TSV transformer, FSM lexer, A\*, Prim MST,
  Fenwick tree, number theory (gcd/lcm/mod-pow/mod-inverse/Miller–Rabin), expression
  evaluator, iterative merge sort, `stdlib_collections_*`, `stdlib_datetime_*`, Rabin–Karp,
  suffix array.
* QuixBugs (50): bitcount, BFS, bucketsort, DFS, detect_cycle, find_first_in_sorted,
  find_in_sorted, flatten, gcd, get_factors, hanoi, is_valid_parenthesization, kheapsort,
  knapsack, kth, lcs_length, levenshtein, lis, longest_common_subsequence, max_sublist_sum,
  mergesort, minimum_spanning_tree (Kruskal), next_palindrome, next_permutation, pascal,
  possible_change, powerset, quicksort, reverse_linked_list, rpn_eval, shortest_path_length(s)
  (includes Floyd–Warshall), shortest_paths, shunting_yard, sieve, sqrt, subsequences, to_base,
  topological_ordering, wrap.
* `benchmark/regression/programs` (55 small synthetic functions: binary search, sliding-window
  max, merge intervals, FizzBuzz, balanced parentheses, primality, tree depth, deque rotate,
  bank account, …) and `benchmark/cross_language` (bubble/insertion sort, binary/linear search,
  factorial, gcd, Fibonacci, palindrome, reverse, sum).
* Families already in the 64 (use only as `family_overlap=true`, ≤ 20 % of fresh programs):
  sorting (merge/quick/heap/counting/radix/timsort/top-k), binary search, Dijkstra,
  Bellman–Ford, topological sort, BFS, DFS cycle detection, connected components,
  KMP, edit distance, anagram grouping, word frequency, run-length encoding, tokenizer, LRU cache,
  min-heap, trie, BST, hash table, stack/queue/deque, sieve, matrix ops, polynomial, statistics,
  numerical integration, 0/1 knapsack, LCS, coin change, INI/JSON-subset/recursive-descent
  parsers, retry/backoff, circuit breaker, Result type, validation chain, rate limiter,
  event bus, mock HTTP client, REST CRUD mock, object pool, memory allocator (free-list),
  task scheduler (priority/dependencies), TTL cache, traffic light, vending machine, order
  lifecycle, connection pool, producer–consumer, read–write lock, thread-safe counter,
  CSV aggregator, log processor, word-count stream, binary encoder, config parser.

---

## 3. Candidate sources (7 sources, 77 candidates for a 30–36 program target)

Tier: **F** = function-entry (counts under every class-tier option), **C** = class-based
stateful (counted only per the owner's class-tier decision). "Size" is an author estimate.
Ids are proposals, prefixed `fresh_` while in preparation; they take the usual
`<category>_<name>` form in the frozen set. A candidate does not become part of the set until it
passes §5.

### S1. CLRS (*Introduction to Algorithms*, 4th ed.): 10 candidates, mostly F

Textbook pseudocode, implemented clean-room (no reference code to copy).

| Id | Algorithm | Cat. | Tier | Size | Notes |
|---|---|---|---|---|---|
| `graph_tarjan_scc` | Strongly connected components (CLRS §20.5) | graph | F | ~80 | Entry `scc(graph: dict) -> list`; iterative DFS to avoid recursion limits |
| `graph_bipartite_check` | BFS 2-colouring (CLRS ex. 20.2-6) | graph | F | ~60 | |
| `graph_edmonds_karp` | Max-flow, BFS augmenting paths (§24.2) | graph | F | ~110 | Capacities in `dict` |
| `graph_eulerian_path` | Hierholzer, Euler circuit (§20 problems) | graph | F | ~90 | |
| `math_matrix_chain` | Matrix-chain order DP (§14.2) | math/DP | F | ~70 | |
| `math_rod_cutting` | Rod cutting, bottom-up + reconstruction (§14.1) | math/DP | F | ~70 | |
| `math_optimal_bst` | Optimal BST cost DP (§14.5) | math/DP | F | ~80 | |
| `algo_activity_selection` | Greedy activity selection (§15.1) | greedy | F | ~60 | |
| `algo_fractional_knapsack` | Greedy fractional knapsack (§15.2) | greedy | F | ~60 | float arithmetic: check E5 |
| `geom_graham_scan` | Convex hull, integer coordinates (§33.3) | geometry | F | ~90 | integer cross-product only |

Independence: none of these algorithms is in the exclusion list (the corpus's DP file covers
0/1 knapsack, LCS, coin change only). Family-overlap flags: none expected.

### S2. Knuth, TAOCP vols. 1–4A: 8 candidates, F

| Id | Algorithm | Cat. | Size | Notes |
|---|---|---|---|---|
| `math_gray_code` | Reflected binary Gray code generation / rank / unrank (4A §7.2.1.1) | math/bit | ~60 | |
| `algo_n_queens` | Backtracking N-queens, count + first solution (4B-style) | backtracking | ~80 | bound n ≤ 8 inside the function |
| `algo_exact_cover_x` | Algorithm X with list-of-sets representation (4B) | backtracking | ~110 | no dancing-links pointers; dict-of-sets |
| `math_josephus` | Josephus permutation, list simulation + closed form check (vol. 1 §1.3.2) | math | ~60 | |
| `math_lcg_shuffle` | Linear congruential generator + Fisher–Yates (vol. 2 §3.4.2) | math/PRNG | ~70 | PRNG state is an explicit argument, deterministic |
| `math_balanced_ternary` | Balanced ternary conversion and addition (vol. 2 §4.1) | math | ~70 | |
| `math_stirling_bell` | Stirling/Bell triangles with memo (vol. 1 §1.2.6 exercises) | math | ~60 | |
| `algo_combinations_lex` | Lexicographic combination generation (4A §7.2.1.3) | combinatorics | ~70 | |

Independence: no combinatorial-enumeration, backtracking or PRNG-driven program exists in the
corpus; `sort_*` and `math_prime_sieve` are unrelated.

### S3. Standard Python/engineering patterns, clean-room: 14 candidates, C (stateful)

These are the programs SBG is *for* (method-call sequences with state). Each is specified from
scratch with a spec docstring before any code is written.

| Id | Pattern | Cat. | Tier | Size |
|---|---|---|---|---|
| `fsm_undo_redo_editor` | Command history, undo/redo stacks, coalescing | state machine | C | ~150 |
| `res_kv_transactions` | In-memory KV store: begin/commit/rollback, nested | resource | C | ~170 |
| `fsm_elevator` | Elevator controller, request queue, direction logic | state machine | C | ~170 |
| `fsm_atm_session` | ATM session: card/PIN/lockout/withdraw limits | state machine | C | ~160 |
| `res_library_loans` | Loans, holds, fines (day counter is an argument) | resource | C | ~170 |
| `api_ledger_double_entry` | Double-entry ledger, balance invariants | api | C | ~150 |
| `api_cart_promotions` | Shopping cart with ordered promotion rules | api | C | ~170 |
| `ds_gap_buffer` | Text-editor gap buffer | data structure | C | ~130 |
| `err_dead_letter_queue` | Bounded retry queue with dead-letter | error handling | C | ~130 |
| `fsm_saga_orchestrator` | Order saga with compensation steps | state machine | C | ~170 |
| `res_semaphore_sim` | Deterministic counting-semaphore / wait-queue simulation (no real threads) | concurrency | C | ~130 |
| `ds_ring_log_index` | Append-only log with compaction and offset index | data structure | C | ~140 |
| `api_pagination_cursor` | Cursor-based pagination service with invalidation | api | C | ~130 |
| `res_lease_manager` | Lease grant/renew/expire with logical clock argument | resource | C | ~140 |

Independence: corpus stateful programs are API mock, cache, pool, allocator, scheduler,
circuit breaker, event bus, FSM-light (traffic light, vending machine, order lifecycle,
connection pool), rate limiter, RW-lock, counter, producer–consumer. None has transaction,
rollback, undo/redo, compensation or lease semantics. `res_semaphore_sim` and
`ds_ring_log_index` are the closest in family to existing ones and should be flagged
`family_overlap` if the dedup screen says so.

### S4. OS / database / distributed-systems texts: 12 candidates, mixed

Silberschatz *Operating System Concepts*, Tanenbaum *Modern Operating Systems*, Kleppmann
*Designing Data-Intensive Applications*, Lamport/Fidge/Mattern papers.

| Id | Algorithm | Cat. | Tier | Size |
|---|---|---|---|---|
| `res_page_replacement` | FIFO / LRU-stack / Clock / OPT fault counters | resource | F | ~110 |
| `res_cpu_scheduling` | Round-robin, SJF, multilevel feedback; Gantt output | resource | F | ~130 |
| `res_bankers_algorithm` | Banker's safety check and request grant | resource | F | ~90 |
| `res_disk_scheduling` | SSTF / SCAN / C-SCAN head movement | resource | F | ~90 |
| `conc_dining_philosophers_sim` | Deterministic step simulation with resource ordering | concurrency | F | ~100 |
| `conc_vector_clock` | Vector clocks: tick / merge / compare | concurrency | C | ~110 |
| `fsm_election_step` | Raft-style leader election step function (terms, votes) | state machine | C | ~170 |
| `fsm_two_phase_commit` | Coordinator/participant 2PC with failure injection by argument | state machine | C | ~170 |
| `ds_consistent_hash_ring` | Consistent hashing with virtual nodes (own integer hash) | data structure | C | ~120 |
| `ds_bloom_filter` | Bloom filter with own integer hash functions | data structure | C | ~110 |
| `ds_skip_list_seeded` | Skip list with an explicit LCG for level choice | data structure | C | ~160 |
| `res_wal_recovery` | Write-ahead log with replay and checkpoint | resource | C | ~170 |

Independence: corpus has a free-list `res_memory_allocator` and a priority/dependency
`res_task_scheduler`; no page replacement, disk, banker, clock, election or 2PC logic.
Hash functions must be hand-written integer functions, **not** `hash()` or `hashlib` (E5).

### S5. LeetCode/HackerRank-*style* problems, independently implemented: 14 candidates

Use the *problem idea* only: do not copy statement text, examples, or any published solution.
Implement from scratch with your own function names, signatures and tests.

| Id | Technique | Cat. | Tier | Size |
|---|---|---|---|---|
| `algo_monotonic_stack` | Next-greater-element and largest rectangle in histogram | arrays | F | ~80 |
| `algo_trapping_water` | Two-pointer trapped-water computation | arrays | F | ~60 |
| `algo_game_of_life` | Conway step on a bounded grid (list of rows) | grid | F | ~80 |
| `algo_matrix_rotate_spiral` | Rotate in place, spiral traversal | grid | F | ~90 |
| `algo_word_break` | Word-break DP / segmentation count | string/DP | F | ~70 |
| `algo_decode_ways` | Decode-ways DP | string/DP | F | ~60 |
| `algo_partition_subset_sum` | Subset-sum / equal-partition DP with bitset-as-int | DP | F | ~70 |
| `algo_merge_k_sorted` | k-way merge with a heap of tuples | arrays | F | ~70 |
| `algo_min_window_substring` | Sliding window with counts | string | F | ~80 |
| `algo_interval_scheduling_rooms` | Meeting rooms (min rooms via sort + heap) | arrays | F | ~70 |
| `api_time_map` | Time-versioned key-value store with binary search | design | C | ~100 |
| `api_snapshot_array` | Snapshot array with copy-on-write deltas | design | C | ~100 |
| `fsm_browser_history` | Back/forward history with truncation | design | C | ~90 |
| `api_hit_counter` | Sliding-window hit counter, timestamps passed as arguments | design | C | ~90 |

Independence: none of these techniques is present (the only sliding-window-like file in the
repo is `api_rate_limiter`, and `reg_004` is a tiny synthetic regression pair that is itself
excluded). **Do not** include LRU cache, two-sum, Dijkstra, binary search or merge intervals.
`algo_merge_k_sorted` and `algo_interval_scheduling_rooms` touch heap/interval ideas: flag
`family_overlap` if the screen says so.

### S6. PSF-licensed CPython stdlib algorithms, re-implemented in reduced form: 10 candidates, F

Take the *algorithm* from the documented stdlib behaviour, re-implement it without importing the
module itself. Record the CPython version and the file/function referenced.

| Id | Source algorithm | Cat. | Size |
|---|---|---|---|
| `str_posix_normpath` | `posixpath.normpath` | string | ~60 |
| `str_glob_match` | `fnmatch` pattern translation + matcher (own matcher, no `re`) | string/parser | ~100 |
| `str_text_wrap` | `textwrap.wrap` greedy fill | string | ~90 |
| `math_color_convert` | `colorsys` RGB↔HSV↔HLS with integer rounding | math | ~90 |
| `str_cidr_arith` | `ipaddress` network containment / supernet (integers only) | parser/math | ~100 |
| `parse_shlex_split` | `shlex.split` POSIX quoting state machine | parser | ~110 |
| `math_calendar_weekday` | `calendar` leap-year / weekday / month-matrix arithmetic | math | ~80 |
| `str_longest_match` | `difflib.SequenceMatcher.find_longest_match` core | string | ~90 |
| `str_html_escape` | `html.escape` / `unescape` for numeric+named subset | string | ~90 |
| `parse_query_string` | `urllib.parse.parse_qs` percent-decoding | parser | ~90 |

Independence: real-world-origin code absent from the repo (repo has no stdlib re-implementations
apart from the excluded v5 `stdlib_*` files, which *use* collections/datetime). PSF licence
permits adaptation. Each program must not import the module it re-implements. Because this is
public code, set `adapted=true` (relevant to learned-baseline contamination, R7 in the report).

### S7. Encoding / checksum / codec classics: 9 candidates, F

| Id | Algorithm | Cat. | Size |
|---|---|---|---|
| `file_lzw_codec` | LZW compress/decompress (dict of byte strings → ints) | file/stream | ~90 |
| `file_crc16_table` | Table-driven CRC-16/CCITT and CRC-32 over `bytes`-as-`list` | file/stream | ~80 |
| `str_luhn_isbn` | Luhn + ISBN-10/13 validation | string | ~70 |
| `str_vigenere` | Vigenère/Caesar encrypt/decrypt | string | ~70 |
| `str_soundex` | American Soundex | string | ~70 |
| `str_roman_numerals` | Roman ↔ integer with validity rules | string | ~70 |
| `parse_bencode` | Bencode encode/decode (ints, bytes-as-str, lists, dicts) | parser | ~110 |
| `parse_semver_compare` | Semantic-version parse/compare/range check | parser | ~100 |
| `parse_cron_field` | Cron field expression parser and matcher | parser | ~110 |

Independence: repo has RLE and one varint/base64-style binary encoder; none of these.
Huffman is in `benchmark/v5/corpus` and is therefore **excluded**.

### Summary

| Source | Candidates | F | C |
|---|---|---|---|
| S1 CLRS | 10 | 10 | 0 |
| S2 Knuth | 8 | 8 | 0 |
| S3 engineering patterns | 14 | 0 | 14 |
| S4 OS/DB/distributed | 12 | 5 | 7 |
| S5 LeetCode-style (ideas only) | 14 | 10 | 4 |
| S6 stdlib re-implementations | 10 | 10 | 0 |
| S7 codecs/checksums | 9 | 9 | 0 |
| **Total** | **77** | **52** | **25** |

Target composition for 36 written: ≈ 24 F + 12 C, with no category contributing more than 6.
Suggested draw, in priority order for balance: S1 × 6, S2 × 4, S3 × 6, S4 × 6, S5 × 5, S6 × 5,
S7 × 4 = 36. (Draw is a suggestion for balance, not a pre-registered selection; the owner may
change it **before** any program is run through the generator.)

---

## 4. Template for a new base program

### 4.1 File skeleton (function-entry programs, tier F)

```python
# program_id: <category>_<name>
# category: <category label as in programs_manifest.json>
# spec_version: 1.0
# provenance: <source id S1..S7> | <reference> | <author> | adapted=<true|false>

"""
<One-line title>.

Spec: <what the public API does, precisely: inputs, outputs, edge cases,
exceptions raised and when>. Complexity: <O(...)>.
"""
from typing import Dict, List, Tuple           # stdlib only


def helper_a(x: List[int], i: int) -> int:     # referenced by the entry, so it is not a root
    ...


def solve(items: List[int], limit: int) -> List[int]:   # <- the single entry (call-graph root)
    """<contract>"""
    ...                                         # >= 3 control-flow constructs, several literals/operators
    return result


# ---------- tests ----------

def test_solve():                               # contains assert -> classified as driver and excluded
    assert solve([], 3) == []
    ...                                         # >= 6 cases including empty/boundary/duplicate/negative
    print("All tests passed.")


if __name__ == "__main__":
    test_solve()
```

Requirements encoded in the skeleton (all traceable to `entry_policy.select_entry_structural`
and `ENTRY_POINT_POLICY.md`):

1. **Exactly one module-level call-graph root** among non-driver functions. Other functions are
   helpers called (directly or transitively) from the root. If the program has several
   independent public functions, one must be a documented orchestrator that calls the others,
   or the selector raises `AmbiguousEntryPoint`: the cause of 12 of the 64 current programs'
   failure (`graph_bellman_ford`, `math_matrix_ops`, `math_prime_sieve`, `str_run_length_encode`,
   …).
2. **Fully annotated entry**, parameters in `{list, List[...], str, int, float, bool, dict, Dict[...]}`
   (and `Optional[...]` of those). Avoid `Callable`, `IO`, `Iterator`, `Generator`, custom types
   as entry parameters (these produce `unsupported_signature`).
3. The entry must be **total on the fixed batteries** or fail cleanly: it will be called with
   `[]`, `[1]`, `[3,1,4,1,5,9,2,6]`, strings `""`, `"abc"`, `"3 + 4 * 2"`, ints `0..100, -1, -5`,
   floats, dicts such as `{}`, `{"a": ["b"]}`, cyclic graphs, etc. (see
   `experiments/final/protocol.py`). An exception is allowed (SBG records exceptions), but a
   program in which **every** battery input raises is useless: aim for ≥ 50 % non-raising
   inputs; this is checked statically only through the signature, so design for it.
4. Test driver(s): zero-argument function with `assert` and/or called from the `__main__`
   guard; named anything (no name rule exists in policy v8; the legacy `test_*` convention is
   kept for consistency).
5. Mutable arguments: the extractor copies inputs, but write the entry so that it does not rely
   on mutation of a shared global between calls.
6. No identifiers or literals that encode a transformation hint (the existing 64 contain
   "Suggested mutations" comments in the v5 corpus; **do not** add such comments).

### 4.2 Stateful (class-based) programs, tier C

Same header, spec docstring, self-test and `__main__` guard. Differences:

* One or two public classes (≤ 6 public methods each) whose method order matters; class and
  method constructors/args take battery-compatible types (`int`, `str`, `list`, `dict`,
  `float`, `bool`). Avoid constructor parameters of other classes or callables.
* **No module-level function other than the test driver** if the program is meant to enter the
  class tier (otherwise the function tier takes precedence and the stateful behaviour is not what
  is traced). Conversely, a module-level facade function would turn a C program into an F
  program that does not exercise method sequences; that is a methodological choice and must not
  be used merely to raise coverage. If the owner prefers it, declare it per program in the
  provenance (`facade=true`) and report both.
* Time/clock are **arguments** or a logical counter owned by the object, never `time`.
* Exceptions raised by the API must be documented in the spec; invalid transitions must raise
  (not silently ignored) so that mutations of the guard (SC-4/SC-5) are observable.
* Counted in the confirmatory total only per plan §4 / owner's class-tier decision; otherwise
  reported as the exploratory stateful subgroup.

### 4.3 Provenance file (one per program, kept outside the program file)

`benchmark/corpus/fresh_provenance.json` (to be created by the program writer; not created here):

```json
{"program_id": "...", "source_id": "S1..S7", "reference": "CLRS 4e §20.5",
 "licence": "n/a (clean-room) | MIT | PSF | ...", "author": "...",
 "created": "YYYY-MM-DD", "adapted": false, "family_id": "...",
 "family_overlap": false, "tier": "F|C", "llm_assisted": false,
 "sha256": "..."}
```

---

## 5. Validation checklist before a program may enter the corpus

Run on each candidate **before** the transformer-generated variants exist. Tick every box;
record the evidence file and its SHA-256 in the freeze record.

**Independence**

- [ ] Provenance record complete (source, licence, author, adapted flag, LLM-assistance flag).
- [ ] Algorithm family not in §2 (or `family_overlap=true`, and total flagged ≤ 20 %).
- [ ] Name-free structural fingerprint of every function/method differs from every function in
      the 64, `benchmark/v5/corpus`, and QuixBugs.
- [ ] 5-gram token Jaccard ≤ 0.10 against each of the 64, each v5 corpus file, each QuixBugs
      program, and every other fresh program (reference: the existing 64 have median 0.003,
      maximum 0.18 between `sort_mergesort`/`sort_timsort_runs`).
- [ ] Reviewer other than the author compared the 3 nearest matches and signed off.
- [ ] No fresh program has been run through the generator, extractor, any baseline or any
      scoring script (attestation).

**Eligibility and quality**

- [ ] E1–E8 satisfied (stdlib only, single file < 300 lines, 3.9 and 3.13, no import side
      effects, deterministic, spec docstring, ≥ 6 asserts, algorithmic content).
- [ ] Self-test exits 0 under Python 3.13 and 3.9; two consecutive runs print identical output.
- [ ] `ast.parse` + `compile` succeed; no `exec`/`eval`/`__import__`/`open`/`socket`/
      `subprocess`/`threading`/`time`/`random` use.
- [ ] v8 static selector (`select_entry_structural`) resolves exactly one entry for tier F; for
      tier C it reports `no_entry_function` as intended (class tier) and `class_driver`'s static
      eligibility is true. **Static only, no tracing.**
- [ ] At least one SC mutation site exists in code reachable from the entry (e.g. a comparison,
      arithmetic operator and integer literal in the entry's call closure).

**After variant generation (frozen generator, one run)**

- [ ] `python experiments/final/data_integrity.py --dataset <fresh dataset> --strict` exits 0.
- [ ] ≥ 1 SP and ≥ 1 SC variant per program compile **and run** (module executes without
      exception).
- [ ] Every EQUIVALENT variant's self-test exits 0 where the base's exits 0 (no exception where
      base passes).
- [ ] Every CHANGED variant is observable and its normalised AST differs from the base.
- [ ] ≥ 10 EQUIVALENT and ≥ 10 CHANGED accepted pairs per program (so each program is a
      cluster with both classes). *(planning threshold; the v6 programs range 19–54 accepted
      pairs in total)*
- [ ] Edit-size diagnostic computed and archived (S1–S3 from Agent B's report gate the
      **dev** split; for the fresh split it is a post-hoc, non-gating report).

**Freeze**

- [ ] SHA-256 of each base file, each `pairs_*.jsonl`, the `variants/` tree, provenance
      manifest, dedup report, entry-resolution report.
- [ ] Program-to-split map recorded: all fresh programs ⇒ `fresh_test`; no overlap with any
      existing split (`program_in_multiple_splits` = 0).
- [ ] `FREEZE_V8.json` (plan §9) committed **before** any score is computed on any fresh
      program, in a commit that does not contain results.

---

## 6. Ordering reminder

1. SP-2 fix + Agent B edit-size configuration fixed and frozen (validated on train/dev/val).
2. Write ≥ 30 programs; static screening (§5, first two groups); fix/replace now.
3. Apply all transformations with the frozen generator.
4. `data_integrity.py --strict`; execution gates; any generator fix ⇒ full regeneration + log.
5. Freeze dataset SHAs and program-level split.
6. Derive τ\* and evaluate v8 on **dev** only.
7. One frozen test evaluation.

Rationale, power analysis and the independence risks behind this order are in
`reports/remediation/agent_e_fresh_dataset.md`.

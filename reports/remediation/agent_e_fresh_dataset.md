# Agent E: Fresh Test Dataset Plan (≥ 30 new base programs)

**Branch:** `remediation/sbg-v2`
**Scope:** planning only. No benchmark data, experimental code, or evaluation artifact was
modified; nothing was committed. Companion document: `docs/current/FRESH_PROGRAM_SOURCES.md`.
**Status of every number below:** either (a) read from a committed file, (b) re-measured by a
read-only script run for this report (marked **[measured]**), or (c) an explicit planning
assumption (marked **[assumption]**). Nothing here is a test result.

Environment note: the measurements ran on `python3` = 3.9.6. The canonical interpreter is 3.13
(`docs/current/PYTHON_VERSIONS.md`); `python3.13` is not installed on this machine. Static
measurements (AST, token n-grams, entry-policy selection) do not depend on this; anything that
executes programs must be re-run on 3.13 before the freeze.

---

## 1. Prerequisites from `EVALUATION_PLAN_V8.md`

### 1.1 Prerequisites before a fresh split may be generated (plan §3)

| # | Prerequisite | State in this checkout |
|---|---|---|
| P1 | SP-2 repaired (attribute/method references renamed consistently, or methods skipped); benchmark version bumped; `data_integrity.py --strict` exits 0 on the new dataset | Repair is in the working tree (modified `sp2_function_rename.py`, Agent A report, untracked `benchmark/datasets/v7/` with 133 pairs and an **empty** `pairs_val.jsonl`). Not committed. v6 itself still fails: `data_integrity.py --dataset benchmark/datasets/v6 --strict` exits **1** **[measured]** (75 dangling SP-2 pairs: train 30, dev 13, val 10, test 22). |
| P2 | Input-copy fix kept (order-independent extraction) | Stated "done" in the plan. |
| P3 | Automatic check that every EQUIVALENT variant's **own self-test passes when executed** | **Not found.** `data_integrity.py` only calls `compile()`; the only execution check is `sp2_execution_check.py`, which covers SP-2 pairs already flagged. Must be built before the freeze (§4.3). |
| P4 | Class-tier policy decided (plan §4: function-only / rename-invariant class driver / alphabetical tier) | Open owner decision. It determines how many fresh programs can count (§3.4). |
| P5 | Edit-size confound addressed (plan §6; Agent B) | Not in the plan's §3 list but required by §6 and §7: reversed edit size alone reaches AUROC 0.967 on v6 test (0.957 dev). Agent B's v7 redesign (constrained-scope SP, multi-site SC, gate S1–S3 on **dev**) must be finished and frozen first. |

### 1.2 Required program count and why

* Plan §2 Option A: "Write ≥ 20 new base programs, not derived from the current 64 … but given v8
  coverage losses (§4), write **≥ 30** so that **≥ 20** survive."
* The 20 comes from the sizing sentence: 7 contributing clusters gave a cluster-bootstrap CI of
  width 0.22; resolving a 0.10 AUROC difference needs "≥ 20 programs *with evaluated pairs*".
  The plan itself says "This is a planning estimate, not a power analysis". §5 below is that
  analysis.
* The plan's stopping rule (§8): **< 15 programs yielding evaluated pairs ⇒ report as exploratory.**
  So 15 is a hard floor, 20 a planning target, 30 the write quota.
* **The 30→20 survival ratio (67 %) is not supported by current evidence.** Running the committed
  v8 selector `select_entry_structural` on the 64 existing base programs **[measured]** gives a
  function-level entry for only **28 / 64 (44 %)**: 22 `no_entry_function` (class-only),
  12 `ambiguous_entry_point`, 2 `unsupported_signature`. By split: train 11/28, dev 4/10, val 3/9,
  test 6/13. If fresh programs are written in the same style, 30 programs would leave ≈ 13
  evaluable under class-tier option 1, **below the 15 floor**. Fresh programs therefore have to be
  *designed* to be entry-resolvable (template in `FRESH_PROGRAM_SOURCES.md`), and this is checked
  statically (no scoring) before the freeze.

### 1.3 What "fresh" means

* Plan §2 / `TEST_SET_CHRONOLOGY.md`: "new programs, not new variants of the 13"; "not derived
  from the current 64"; plan §1: "on programs **never scored before**".
* The plan says "**write**" but does not forbid adaptation from public sources. The defensible
  reading, which I recommend the owner confirm in writing (open decision D1):
  1. **Primary:** independently implemented from a textbook/algorithm description (clean-room);
     no copying from any file in this repo.
  2. **Allowed with provenance:** adaptation of permissively licensed public code (MIT/BSD/PSF/
     CC0/public-domain) with URL, commit/version, licence, and a diff-vs-original recorded.
  3. **Not allowed:** anything already in this repository, **including material outside the 64**
     that has been scored or used in development: `benchmark/v5/corpus/base_programs/` (25
     programs: Huffman, AVL, segment tree, Fenwick, Prim, A*, union-find, Rabin–Karp, suffix
     array, number theory, …), `external/quixbugs/` (50 programs, scored in external
     evaluations), `benchmark/regression/` (55 pairs), `benchmark/cross_language/` (10),
     `external/bugsinpy/`. These were scored or analysed in earlier phases, so they fail "never
     scored before" even though they are not among the 64.
* Algorithm-family overlap with the existing corpus is not forbidden by the plan, but it weakens
  a "generalises to unseen programs" reading. Policy proposed here: prefer new families; allow
  adjacent families for ≤ 20 % of fresh programs, tag them `family_overlap=true`, and report the
  result with and without them.

### 1.4 Split and grouping requirements (plan §5)

* train / dev / val / **fresh test**, split **by program, never by variant**; stratify by category;
  no program in two splits (`data_integrity.py` already reports `program_in_multiple_splits`).
* All tuning (weights, threshold, entry-policy coverage decisions) on train/dev/val only; τ\* from
  `derive_threshold.py` on dev, written to a hashed artifact before test scoring.
* The 13 old test programs may become extra *dev* material only with owner approval and are then
  permanently excluded from test.
* Seeds: global 42; bootstrap 2000; permutation 2000; noise floor 2000. No others.
* Statistics (plan §7): cluster bootstrap by program; Holm–Bonferroni over §6 baselines; success
  criterion fixed in advance.

---

## 2. Coverage audit of the existing corpus

The 64 base programs live in `benchmark/corpus/base_programs/`; **60** are assigned to splits
(28 / 10 / 9 / 13, matching `generation_report.json` and `split_assignment.json`). Four tiny
programs (`err_assert_guard`, `math_fibonacci`, `sort_insertion_sort`, `str_palindrome`; 19–39
lines) are unassigned and appear in no split. They must not be used as fresh programs either.

Entry column = result of the v8 static selector on the **base** program **[measured]**:
`fn` = function entry found; `class` = `no_entry_function` (class-only API); `ambig` =
`ambiguous_entry_point`; `unsup` = `unsupported_signature`.

| # | Program | Category | Split | Lines | Class? | v8 entry |
|---|---|---|---|---|---|---|
| 1 | `api_event_bus` | API/HTTP | dev | 186 | yes | class |
| 2 | `api_mock_http_client` | API/HTTP | train | 218 | yes | class |
| 3 | `api_rate_limiter` | API/HTTP | test | 207 | yes | class |
| 4 | `api_rest_crud_mock` | API/HTTP | train | 193 | yes | class |
| 5 | `conc_producer_consumer` | Concurrency | val | 77 | no | unsup |
| 6 | `conc_read_write_lock` | Concurrency | test | 110 | yes | class |
| 7 | `conc_thread_safe_counter` | Concurrency | train | 76 | yes | class |
| 8 | `ds_binary_search_tree` | Data structures | val | 210 | yes | class |
| 9 | `ds_hash_table` | Data structures | test | 213 | yes | class |
| 10 | `ds_lru_cache` | Data structures | train | 171 | yes | class |
| 11 | `ds_min_heap` | Data structures | train | 177 | yes | class |
| 12 | `ds_stack_queue` | Data structures | dev | 249 | yes | class |
| 13 | `ds_trie` | Data structures | train | 180 | yes | class |
| 14 | `err_assert_guard` | Error handling | unassigned | 39 | no | fn |
| 15 | `err_circuit_breaker` | Error handling | dev | 94 | yes | class |
| 16 | `err_result_type` | Error handling | test | 102 | yes | fn |
| 17 | `err_retry_backoff` | Error handling | train | 69 | no | ambig |
| 18 | `err_validation_chain` | Error handling | train | 71 | yes | fn |
| 19 | `file_binary_encoder` | File/stream | train | 186 | yes | ambig |
| 20 | `file_config_parser` | File/stream | test | 257 | yes | class |
| 21 | `file_csv_aggregator` | File/stream | dev | 207 | yes | fn |
| 22 | `file_log_processor` | File/stream | train | 187 | yes | fn |
| 23 | `file_word_count_stream` | File/stream | val | 182 | yes | ambig |
| 24 | `fsm_connection_pool` | State machines | train | 224 | yes | class |
| 25 | `fsm_order_lifecycle` | State machines | val | 203 | yes | class |
| 26 | `fsm_parser_state` | State machines | dev | 166 | yes | fn |
| 27 | `fsm_traffic_light` | State machines | train | 197 | yes | class |
| 28 | `fsm_vending_machine` | State machines | test | 197 | yes | class |
| 29 | `graph_bellman_ford` | Graph | train | 145 | no | ambig |
| 30 | `graph_bfs_shortest_path` | Graph | test | 130 | no | fn |
| 31 | `graph_connected_components` | Graph | dev | 155 | yes | fn |
| 32 | `graph_cycle_detect_dfs` | Graph | val | 133 | no | ambig |
| 33 | `graph_dijkstra` | Graph | train | 140 | no | fn |
| 34 | `graph_topological_sort` | Graph | train | 155 | yes | ambig |
| 35 | `math_dynamic_programming` | Math/numerical | train | 174 | no | fn |
| 36 | `math_fibonacci` | Math/numerical | unassigned | 27 | no | fn |
| 37 | `math_matrix_ops` | Math/numerical | train | 162 | no | ambig |
| 38 | `math_numerical_integration` | Math/numerical | dev | 145 | no | unsup |
| 39 | `math_polynomial` | Math/numerical | val | 162 | no | fn |
| 40 | `math_prime_sieve` | Math/numerical | train | 169 | no | ambig |
| 41 | `math_statistics` | Math/numerical | test | 183 | yes | fn |
| 42 | `parse_ini_config` | Parser | val | 101 | yes | fn |
| 43 | `parse_json_subset` | Parser | train | 130 | yes | fn |
| 44 | `parse_recursive_descent` | Parser | test | 104 | yes | fn |
| 45 | `res_cache_ttl` | Resource mgmt | dev | 206 | yes | class |
| 46 | `res_memory_allocator` | Resource mgmt | train | 223 | yes | class |
| 47 | `res_object_pool` | Resource mgmt | test | 210 | yes | class |
| 48 | `res_task_scheduler` | Resource mgmt | train | 220 | yes | class |
| 49 | `sort_binary_search` | Sorting/search | train | 142 | no | fn |
| 50 | `sort_counting_sort` | Sorting/search | test | 116 | no | fn |
| 51 | `sort_heapsort` | Sorting/search | test | 93 | no | fn |
| 52 | `sort_insertion_sort` | Sorting/search | unassigned | 25 | no | fn |
| 53 | `sort_mergesort` | Sorting/search | train | 83 | no | fn |
| 54 | `sort_quicksort` | Sorting/search | dev | 85 | no | fn |
| 55 | `sort_radix_sort` | Sorting/search | train | 92 | no | fn |
| 56 | `sort_timsort_runs` | Sorting/search | val | 143 | no | fn |
| 57 | `sort_topk_select` | Sorting/search | train | 121 | no | ambig |
| 58 | `str_anagram_groups` | String/text | val | 140 | no | ambig |
| 59 | `str_edit_distance` | String/text | train | 141 | no | fn |
| 60 | `str_kmp_search` | String/text | train | 134 | no | fn |
| 61 | `str_palindrome` | String/text | unassigned | 19 | no | fn |
| 62 | `str_run_length_encode` | String/text | dev | 142 | no | ambig |
| 63 | `str_tokenizer` | String/text | test | 143 | yes | ambig |
| 64 | `str_word_frequency` | String/text | train | 165 | no | fn |

Size: median 155 lines, max 257 (all < 300). 36 / 64 define a top-level class.

### 2.1 Category balance (from `programs_manifest.json`, 12 categories, 64 programs)

| Category | n | v8 `fn` | Comment |
|---|---|---|---|
| Sorting/searching | 9 | 8 | Over-represented (14 %); 8/9 function-entry. Few new ones needed. |
| String/text | 7 | 4 | 3 ambiguous. |
| Math/numerical | 7 | 4 | Only one DP file; no combinatorics/backtracking/greedy/geometry/bit-level. |
| Graph | 6 | 3 | 3 ambiguous (multiple roots tie). |
| Data structures | 6 | 0 | All class-only. |
| State machines | 5 | 1 | |
| File/stream | 5 | 2 | |
| Error handling | 5 | 3 | |
| API/HTTP | 4 | 0 | All class-only. |
| Resource mgmt | 4 | 0 | All class-only. |
| Concurrency | 3 | 0 | Smallest; all simulated, none function-entry. |
| Parser | 3 | 3 | |

### 2.2 What matters for SBG, and the gaps

* SBG's distinctive object is the **method-call sequence of stateful programs**. The proxy
  "class-only API, no function entry" covers **22 / 64 programs** [measured], 6 of the 13 test
  programs. Under plan §4 option 1 these are `not_evaluable`; under option 3 they carry a known
  rename-instability flag. So the stateful half of the corpus is exactly the half whose
  scoring is policy-dependent.
* Under-represented *algorithmic* classes (no program in the 64): backtracking/combinatorial
  enumeration, greedy scheduling, geometry, bit-level/Gray code, checksums, dictionary
  compression (LZW), text layout, pattern/glob matching, version/date parsing, two-pointer and
  monotonic-stack techniques, DP beyond one file, flow networks, strongly-connected components.
* Under-represented *stateful* classes: undo/redo command history, transactional key–value store
  (begin/commit/rollback), elevator/ATM/loan sessions, page-replacement and OS scheduling
  simulators, distributed-systems state machines (election, two-phase commit, vector clocks),
  deterministic dining-philosophers simulation. The existing stateful programs are API-mock,
  cache, pool, allocator, scheduler, FSM-light, circuit-breaker; there is no transaction or
  rollback semantics, which produces richer method-sequence dependence.
* Entry-resolvability is a corpus-wide weakness (44 %); see §1.2.

---

## 3. Feasible sources for ≥ 30 new base programs

Seven sources, **≈ 70 named candidates** from which 36 are to be selected (full lists with
proposed ids, category, tier, and rough size in `FRESH_PROGRAM_SOURCES.md`). Counts are
candidates available, not commitments.

| # | Source | Candidates | Tier mix | Categories covered | Why it is independent of the 64 |
|---|---|---|---|---|---|
| S1 | **CLRS** (*Introduction to Algorithms*, 4th ed.): Tarjan SCC, bipartite 2-colouring, Edmonds–Karp max-flow, matrix-chain, rod cutting, activity selection, fractional knapsack, Graham-scan convex hull, optimal-BST DP, LCS-length variants not present, … | 10 | function | graph, math/DP, greedy, geometry | None of these algorithms is in the 64 (corpus has Dijkstra, Bellman–Ford, topological sort, DFS cycle, components, one DP file). Textbook pseudocode, so authored clean-room. |
| S2 | **Knuth, TAOCP** vols. 1, 2, 4A: Gray-code generation, Algorithm X / exact cover + N-queens backtracking, Josephus, Fisher–Yates/Algorithm S with an explicit LCG, balanced ternary, Bell/Stirling triangles, combination generation | 8 | function | math/combinatorics, backtracking, PRNG-driven | No combinatorial enumeration or PRNG program exists in the 64. Randomness is made deterministic by an explicit LCG. |
| S3 | **Standard Python/engineering patterns** (clean-room): undo/redo command history, transactional KV store, elevator controller, ATM session FSM, library loan, double-entry ledger, shopping cart with promotions, text-editor gap buffer, order saga, bounded retry queue with dead letter | 14 | **class** | state machines, resource mgmt, API, error handling, data structures | The 64 contain caches, pools, allocator, scheduler, circuit breaker, event bus; none has transaction/rollback or undo semantics. Each is specified from scratch (spec docstring first). |
| S4 | **OS/DB/distributed-systems texts** (Silberschatz *OS Concepts*, Tanenbaum, Kleppmann *DDIA*): page replacement (FIFO/Clock/OPT), CPU scheduling (RR/SJF/MLFQ), Banker's algorithm, disk scheduling (SCAN/C-SCAN), dining philosophers (deterministic), vector clocks, Raft-style election step function, two-phase commit, consistent-hash ring, Bloom filter, skip list (seeded), WAL + recovery | 12 | mixed (5 function, 7 class) | resource mgmt, concurrency simulation, state machines, data structures | Corpus has a memory allocator and a task scheduler (excluded as families: no buddy allocator, no generic scheduler); no replacement/disk/banker/clock/election/2PC. |
| S5 | **LeetCode/HackerRank-*style* problems, independently implemented** (problem *ideas* only; no statement text, no copied solution): monotonic stack (next greater / largest rectangle), trapping rain water, Game of Life, spiral/rotate matrix, word break, decode ways, subset-sum partition, merge-k sorted (heap), TimeMap, snapshot array, browser history, hit counter | 14 | mostly function; 4 class | arrays/two-pointer, matrix/grid, DP, design-style stateful | Different techniques from the 64 (no stack-based, two-pointer, grid simulation or word-break programs). `sliding_window_max` exists only as a tiny synthetic regression pair (`reg_004`, excluded: do not use). LRU is *not* a candidate. |
| S6 | **PSF-licensed CPython stdlib algorithms, re-implemented in reduced form**: `posixpath.normpath`, `fnmatch.translate`-style glob matcher, `textwrap` wrapping, `colorsys` conversions, `ipaddress`-style CIDR arithmetic, `shlex`-style splitting, `calendar` helpers, `difflib` longest-match, `html.escape/unescape`, `urllib.parse.parse_qs` | 10 | function | string/text, parser, math | Real-world-origin code (PSF licence permits adaptation) not present in repo. Only the algorithm is retained; imports from the stdlib module itself are removed to keep it self-contained. |
| S7 | **Encoding/checksum/codec classics**: LZW, CRC-16/CRC-32 (table-driven), Luhn + ISBN-10/13, Vigenère/Caesar, Soundex, Roman numerals, Bencode encode/decode, semantic-version comparison, cron-field matcher | 9 | function | file/stream, string, parser | Repo has RLE and one binary encoder (varint/base64-like); none of these algorithms. `huffman` is in the v5 corpus, so **excluded**. |

Aggregate: 77 listed candidates before de-duplication; after removing adjacent-family and
overlapping items I expect ≈ 70 usable, i.e. roughly **2× over-supply** for a 36-program target.
Over-supply is needed because programs are rejected at the static gates (entry policy,
de-duplication) and at the integrity gates before the freeze (never after).

### 3.1 Target composition (36 programs)

| Group | Target n | Rationale |
|---|---|---|
| Function-entry, entry-resolvable by construction | 24 | Counts under every class-tier option. |
| Class-based stateful (method-sequence programs) | 12 | The programs SBG is *for*. Counted toward the confirmatory total only if class-tier option 2 is validated on dev before the freeze; otherwise reported as an exploratory subgroup. |

Expected evaluable programs **[assumption, checkable statically before the freeze]**:
24 × ~0.9 = 21–22 under option 1; ≈ 30 under option 2 if the class driver covers ~0.8 of the 12.
The ~0.9 is the target for the entry-resolvability gate, not an observation; the pre-freeze static
check (§4.3 item 6) turns it into a measured value.

Writing 36 rather than exactly 30 is my recommendation; the plan's minimum is 30.

### 3.2 Time frame

**[assumption, not measured]** The existing 64 programs average ≈ 148 lines. Authoring a 100–200
line program with spec docstring and self-test, plus review and provenance, ≈ 1.5–3 person-hours
each ⇒ 36 programs ≈ 55–110 person-hours (≈ 1.5–3 calendar weeks for one person; shorter if
parallelised across independent authors). Variant generation and integrity checking are
automated; the repo does not record the wall-clock time of v6 generation, so I give no estimate
for it. 30 programs are achievable in a "reasonable" time frame; the binding constraints are
(i) prerequisites P1–P5, not authoring effort, and (ii) review/dedup effort.

---

## 4. Selection and validation protocol

### 4.1 No overlap with the current corpus (independence screen)

Run in order; a program failing any step is rejected or reworked *before* any variant is made.

1. **Provenance record** for each program (source type S1–S7, reference, licence, author or tool,
   date, adaptation yes/no). No record ⇒ reject.
2. **Excluded-family check.** Reject any program whose algorithm is in the exclusion list in
   `FRESH_PROGRAM_SOURCES.md` §2 (union of the 64, `benchmark/v5/corpus`, QuixBugs names,
   regression and cross-language names).
3. **Structural fingerprint.** Compute a name-free structural id of every top-level function and
   class method (the construction already used by `entry_policy.structural_id`, i.e. identifiers
   replaced by positional slots). Any equality with a function in the 64 or v5 corpus ⇒ reject.
4. **Token n-gram Jaccard.** On the 64 existing programs **[measured; ad hoc, not committed]**,
   5-gram token-set Jaccard over all 2,016 pairs has median 0.003, p99 0.039, maximum **0.183**
   (`sort_mergesort`/`sort_timsort_runs`). Rule: a fresh program must score **≤ 0.10** against
   every program in the 64 + v5 corpus + QuixBugs, and ≤ 0.10 against every other fresh program
   (otherwise they are one family; see 4.2). The existing `leakage_audit.py` check D uses a
   whitespace-token Jaccard threshold of **> 0.95** and cannot detect derivation; do not rely on
   it. Recommended follow-up: commit this as `benchmark/scripts/fresh_dedup.py` (not in my scope).
5. **Human derivation review.** One reviewer other than the author reads the closest 3 matches per
   program and signs off "independently implemented".

### 4.2 Grouping related programs

* Statistical unit = program (plan §7). If two fresh programs share an algorithm family or
  helper code, assign both the same `family_id` and bootstrap by `family_id` (needs a one-line
  change in the analysis code, outside my scope; otherwise exclude one of them). Default: at most
  one program per family, so program = cluster.
* All fresh programs are assigned to a single `fresh_test` split; **no fresh program is used in
  train/dev/val**. Hence the "same algorithm family → same split" rule is satisfied trivially for
  the fresh set. If the owner instead decides to hold some fresh programs out as dev (not
  recommended, since it lowers test power), assign by `family_id`, never by program.
* Fresh programs vs. the 60: no program-level overlap. Family-level overlap allowed ≤ 20 %,
  flagged, and analysed with/without (§1.3).

### 4.3 Label validation before freezing

Gate G1–G7; all must pass on the *complete* fresh dataset in one run with the frozen generator.

| Gate | Check | Source / status |
|---|---|---|
| G1 | `python experiments/final/data_integrity.py --dataset <fresh> --strict` exits 0 | exists |
| G2 | Every program compiles and its own self-test exits 0 under 3.13 **and** the 3.9 floor | new (loop over `subprocess`) |
| G3 | ≥ 1 SP and ≥ 1 SC variant per program compile **and run** (module executes without exception) | new |
| G4 | Every EQUIVALENT variant's self-test exits 0 when the base's exits 0; EQUIVALENT variants raise no exception where base passes (plan §3.3; generalises `sp2_execution_check.py`) | new; this is P3 |
| G5 | Every CHANGED variant is observable (existing `observability_audit` rule) and is not byte/AST-identical to base | exists (`generate_benchmark_v6.py::check_candidate`) |
| G6 | Per-program minimum pairs: ≥ 10 EQUIVALENT and ≥ 10 CHANGED accepted, so each cluster has both classes. Reference: v6 programs range 19–54 accepted pairs, min 19 (`conc_read_write_lock`, `err_circuit_breaker`) | new threshold **[assumption]** |
| G7 | Static entry-policy resolution of the base program and of ≥ 90 % of its SP-2/SP-7/SP-8-free variants (`select_entry_structural` + `interfaces_correspond`); **no tracing, no distances** | new; static only |

What a failure means: a *label-validity* defect (G1, G4, G5) in a generator is fixed once, in the
generator, then **all** fresh variants are regenerated from scratch (never a patch applied only to
the failing pair) and the incident is logged as a deviation. A *program* that fails G2/G6/G7 is
repaired or replaced **while fresh programs are still unscored**. Nothing is ever replaced based
on a score or a behaviour of SBG or any baseline.

### 4.4 Test vs. development split

* Development material = the 60 assigned existing programs (train 28 / dev 10 / val 9 / old-test
  13 if the owner approves them as dev). Fresh test = 30–36 programs, i.e. ≈ 33–38 % of
  (60 + fresh). Fresh test is **100 %** of the confirmatory evaluation; 0 % of fresh programs
  may be used for tuning.
* Smoke-testing the *pipeline* (extraction, scoring, result manifest) uses dev programs only.
* The dev set is small for the function-only tier: 4 of 10 dev programs have a function entry, so
  τ\* under class-tier option 1 would be derived from ≈ 4 programs. Flagged for the owner as a
  fragility (open decision D3: allow τ\* from train+dev+val?). The plan currently says dev.

### 4.5 Freeze record required before any scoring

`artifacts/final/FREEZE_V8.json` per plan §9, **plus** these fresh-dataset items:

1. Git SHA of the generator, transformers (SP-2 fix **and** Agent B's constrained-scope/multi-site
   configuration), `entry_policy`, `class_driver`, `data_integrity`.
2. SHA-256 of every fresh base program file, of every `pairs_*.jsonl`, and of the `variants/` tree.
3. Program→split map (all fresh ⇒ `fresh_test`), with `family_id` and `family_overlap` flags.
4. SHA-256 of the provenance manifest and of the dedup report (§4.1).
5. G1–G7 reports (SHA-256) and the static entry-resolution report.
6. Edit-size diagnostic on **dev** (S1–S3 of Agent B) and, as post-hoc non-gating check, on fresh.
7. τ\* artifact path and SHA-256; plan SHA-256; baseline list; seeds; Python 3.13 and
   `requirements-lock.txt` hash.
8. Attestation: "No extraction, distance, or baseline score has been computed on any fresh
   program before this commit". Enforced mechanically where possible: the evaluation entry point
   refuses to run a split whose files do not match a committed freeze file.
9. Commit ordering: the freeze commit is separate from, and precedes, any results commit.
   `TEST_SET_CHRONOLOGY.md` documents the failure mode where test data and test results were
   committed together on the same date.

---

## 5. Power and sample size

**Unit of analysis = program.** Do not use `benchmark/scripts/power_analysis.py`'s verdict
("ADEQUATE" at N = 800 *pairs*, McNemar/Mann–Whitney): it treats pairs as independent, whereas
the plan's inference is a cluster bootstrap over programs. The relevant sample size is the number
of programs with both classes among evaluated pairs.

### 5.1 Inputs actually observed (v6 test, 7 clusters with both classes; `audit_recompute.json`)

| Quantity | Value | Note |
|---|---|---|
| Per-program SBG V5 AUROC | mean 0.623, SD **0.145** | n = 7 |
| Paired per-program ΔAUROC, SBG − exception_fraction | mean +0.024, SD **0.073** | n = 7 |
| Paired per-program ΔAUROC, SBG − static_ast | mean +0.488, SD 0.179 | n = 7; static_ast is a weak comparator here |
| Reversed edit-size AUROC | 0.967 test / 0.957 dev | Agent B reproduction |
| CI half-width at k = 7, SD 0.15 | ≈ 0.11 | consistent with ±0.11 / width 0.22 in the plan |

SD from 7 clusters is itself uncertain (± roughly a third); I treat 0.10 / 0.15 / 0.20 as a
sensitivity range. The per-program ΔAUROC against the **edit-size** baseline, which is the
comparator that matters, has not been computed per program and should be computed on dev before
the freeze.

### 5.2 Minimum detectable ΔAUROC (normal approximation) **[calculation]**

MDE = (z₁₋α + z₀.₈₀)·SD/√k, one-sided α = 0.025 per comparison (equivalent to a 95 % two-sided
lower bound), power 0.80. "Holm m = 8" is the conservative first-step level for the plan's
baselines (7 implemented + the learned baseline).

| Evaluable programs k | SD 0.10, m=1 / m=8 | SD 0.15, m=1 / m=8 | SD 0.20, m=1 / m=8 |
|---|---|---|---|
| 15 (plan floor) | 0.072 / 0.092 | 0.109 / 0.138 | 0.145 / 0.185 |
| 20 (plan target) | 0.063 / 0.080 | 0.094 / 0.120 | 0.125 / 0.160 |
| 30 | 0.051 / 0.065 | 0.077 / 0.098 | 0.102 / 0.131 |
| 40 | 0.044 / 0.057 | 0.066 / 0.085 | 0.089 / 0.113 |

Programs needed to detect ΔAUROC = 0.10 at 80 % power:

| SD of per-program ΔAUROC | m = 1 | m = 8 |
|---|---|---|
| 0.07 | 4 | 7 |
| 0.10 | 8 | 13 |
| 0.15 | 18 | 29 |
| 0.20 | 32 | 52 |

Power to detect Δ = 0.10, m = 8: k = 20 ⇒ 0.96 / 0.60 / 0.31 for SD 0.10 / 0.15 / 0.20;
k = 30 ⇒ 1.00 / 0.82 / 0.50; k = 36 ⇒ 1.00 / 0.90 / 0.60.

Caveats: normal approximation is optimistic at small k; with a t-correction add ≈ 2–3 programs
(≥ 15 clusters is also the plan's own reliability threshold for the percentile CI). The effect
direction is assumed positive; power says nothing about whether the true Δ is positive.

### 5.3 Assessment

* **Is 30 achievable?** Yes on effort grounds (§3.2), conditional on P1–P5 and on the entry gate.
* **Is 30 *sufficient*?** Not unconditionally. 30 *written* is not the relevant number; 30
  *evaluable* programs supports a Δ = 0.10 claim at 80 % power only if the SD of per-program ΔAUROC
  is ≲ 0.15 (m = 8). At SD 0.20 it does not (power 0.50). 20 evaluable supports it only if SD ≲ 0.125.
  The plan's "≥ 20 evaluable" is therefore a lower bound valid for low-variance differences.
* **Minimum for a credible confirmatory claim:**
  * hard floor: **15 evaluable programs** (plan §8; below it the run is exploratory by rule);
  * credible: **≥ 20 evaluable** with per-program ΔSD ≤ 0.125 estimated on dev, or **≥ 30 evaluable**
    with ΔSD ≤ 0.15; treat anything with a wider CI than the pre-declared MDE as "not demonstrated".
  * The recommended quota (36 written, ≥ 24 evaluable function-entry + class tier if validated) is
    chosen to reach the second tier, not because 30 is a magic number.
* **Stateful subgroup.** 12 class programs cannot support a separate confirmatory claim (MDE at
  k = 12 with SD 0.15 is ≈ 0.12 for m = 1, ≈ 0.15 for m = 8). Report it as exploratory.

### 5.4 Effect of Agent B's edit-size redesign on power

1. **It is what makes a positive Δ possible at all.** On v6 the reversed edit-size baseline scores
   0.967 vs SBG 0.601 (test), Δ ≈ −0.37. No sample size rescues that; the plan's success
   criterion needs SBG to beat the *best* baseline. With Agent B's target S3 (reversed edit-size
   AUROC ≤ 0.75 on dev), a Δ = 0.10 claim requires SBG ≳ 0.85 on that data. The observed v6
   values are 0.60 test / 0.667 dev (and are contaminated by the SP-2 defect). Power analysis is
   conditional on a true effect that has not been shown to exist; the dominant uncertainty is the
   effect size, not n.
2. **Within-bin analysis reduces effective n.** Today only 2 of 6 bins contain both classes on
   test (bins 0–1), so the stratified AUROC rests on ≈ 135 pairs. Overlap raises the number of
   usable bins but spreads each program's pairs over more bins, increasing per-program AUROC
   variance. **[assumption]** inflating the ΔSD from 0.15 to 0.20 raises the programs needed for
   Δ = 0.10 from 29 to 52 (m = 8). So the pair-weighted within-bin metric is likely to need more
   than 30 evaluable programs unless ΔSD stays small. This is the strongest reason to over-write
   (36) rather than write exactly 30.
3. **Pairs per program may drop.** Constrained-scope SP and multi-site SC change the
   no-op/unobservable rejection rates (v6 train rejected 1,055 candidates: 896 no-op, 159
   unobservable). G6 (≥ 10 pairs per class per program) guards against programs with too few
   pairs to have a defined AUROC.
4. **Coupling with SP-2.** Agent B proposes renaming a function at the definition and "at most 2"
   call sites. For methods, an unrenamed `self.name(...)` call is exactly the SP-2 defect class.
   The two transformer changes must be frozen **together** and verified by execution (G4), not
   by the static dangling-reference check alone.
5. **Gate on dev, not on fresh.** S1–S3 are passed on dev first; the fresh data uses identical
   parameters and the diagnostic is a post-hoc report there, as Agent B specifies.

---

## 6. Independence risks and mitigations

| # | Risk | How it could happen | Mitigation |
|---|---|---|---|
| R1 | **Tuning SP-2 (or other transformer) parameters on known programs** | The SP-2 defect was found on observed data (22 of the 75 dangling pairs are in the old test split). The *choice between* "rename attributes consistently" and "skip methods", and `max_sites`, changes which SP-2 pairs exist and their edit sizes, i.e. the metric. If those choices are made after looking at fresh programs or at any SBG score, the confirmatory split is no longer independent. | Choose and freeze on train/dev/val and on structural criteria only (integrity = 0, Agent B S1–S3). Freeze generator + config **before the first fresh program is run through it**. Hash it. Any later generator change ⇒ deviation + full regeneration of all fresh variants; programs are never swapped on the basis of behaviour. |
| R2 | **Loop "fix generator after seeing fresh failures"** (plan stopping rule §8 says regenerate) | G1/G4 failures on fresh programs lead to patches that overfit them. | Restrict post-seeing fixes to label-validity defects (do not depend on any SBG score); document each; regenerate everything; re-verify on dev. |
| R3 | **Authors who know SBG's behaviour** | Writing programs that happen to suit or defeat SBG. | Authors follow the template and source list; selection is by structural gates and provenance, never by scores; author ≠ SBG maintainer where possible; disclose any LLM assistance in provenance. |
| R4 | **Tracing fresh programs "just to check coverage"** | Running extraction yields exception fractions and failure kinds, which can steer program edits. | Coverage is checked **statically** (entry selector) only; no tracing, scoring or baselines on fresh data before the freeze commit. |
| R5 | **Programs designed around the entry policy** | Editing programs until the selector picks an entry is a form of coverage tuning. | Allowed (the policy code is frozen and no scores are involved) but must be declared: the policy is frozen first, program edits are logged, coverage target stated in advance (≥ 90 % of programs). |
| R6 | **Hidden derivation** | Subtle reuse of existing corpus code, v5 corpus, or QuixBugs. | §4.1 steps 2–5, including v5 + QuixBugs in the exclusion set. |
| R7 | **Learned-baseline training-data leakage** | Adapted public code (TheAlgorithms, CPython) is likely in the pretraining or training data of any learned model; SBG itself is not learned. | Prefer clean-room for the confirmatory set; record adaptation flag so the learned baseline (plan §6, not yet implemented) can be analysed with/without adapted programs. |
| R8 | **τ\* from too few dev programs** | Only 4/10 dev programs resolve under function-only entry. | Open decision D3; report τ\* provenance with n programs; do not re-derive after seeing fresh data. |
| R9 | **Version drift** | Distances differ between 3.9.6 and 3.13 (largest observed change 0.41). | Freeze and run on 3.13 only; this machine has 3.9.6, so the final steps need a 3.13 environment. |
| R10 | **Chronology** | Prior history committed test data and results together. | Separate freeze commit, tagged, strictly before the results commit. |
| R11 | **v7 dataset in the tree is untracked** | `benchmark/datasets/v7/` (133 pairs, empty `val`) can be mistaken for the final dataset. | The freeze names the fresh dataset directory explicitly and records hashes; v7 is a smoke-test of Agent A's repair, not a deliverable. |

---

## 7. Recommended sequence of operations

0. **Owner decisions (before anything):** D1 clean-room vs. adapted sources; D2 class-tier option
   (1/2/3) and whether old 13 test programs become dev; D3 τ\* data (dev only or train+dev+val);
   D4 write quota (36 recommended, 30 minimum). Source selection and authoring may proceed in
   parallel with steps 1–2 but **no fresh program may be given to the generator or the extractor
   until step 3**.
1. **Fix SP-2 completely and freeze all transformer code**: Agent A's repair **plus** Agent B's
   constrained-scope SP / multi-site SC configuration, validated on train/dev/val only: integrity
   = 0, execution check (G4) passes, dev gate S1–S3 passes. Commit; record git SHA and hashes.
   Freeze `entry_policy` and the class-tier decision at the same time.
2. **Write or adapt ≥ 30 (recommended 36) fresh programs** per `FRESH_PROGRAM_SOURCES.md`,
   with provenance records. Run §4.1 screening and the **static** entry-resolution report
   (G7, no tracing). Repair/replace programs *now*; this is the last point at which programs
   may change.
3. **Apply all transformations** with the frozen generator to produce SP and SC variants
   (single run; seeds 0, 1, 2 as in v6).
4. **Run `data_integrity.py --strict`** and G2–G6. Any generator fix ⇒ deviation log and
   regeneration of all fresh variants (R2); any unrecoverable program is dropped by a pre-declared
   rule (lowest priority, not by behaviour) and the final count re-checked against the floor.
5. **Freeze dataset SHAs and program-level split assignment** (all fresh ⇒ `fresh_test`),
   write `FREEZE_V8.json` sections for the dataset (§4.5); commit and tag. No scoring so far on any
   fresh program.
6. **Only then derive τ\* and run the v8 evaluation on dev** (never on fresh). Record the
   τ\* artifact hash in the freeze file; commit.
7. **Only then run the single frozen test evaluation** on the fresh set; one run, one artifact;
   report all three denominators, failure ledger, per-program AUROCs, tie fractions,
   edit-size-stratified AUROC, noise floor, Holm-corrected ΔAUROC, and every deviation, per plan §10.

Step 6 depends on step 5 only for hygiene (τ\* is derived from dev, which is already available);
the order is kept as specified so τ\* and the dataset hashes live in one freeze record committed
before the test run.

---

## 8. Open items for the owner / other agents (not done here)

* Decisions D1–D4 above.
* Build G2–G4, G7 (execution and static-entry loops) and the committed dedup script; they are
  prerequisites, not part of this plan's scope.
* Compute the per-program ΔAUROC SD of SBG vs. **edit size** on dev, and re-run the table in §5.2
  with that SD. Without it the "20 vs 30" question is open.
* Install Python 3.13 for the freeze.
* `benchmark/scripts/power_analysis.py`'s "ADEQUATE" verdict (pair-level) should not be cited as
  support for the program-level sample size.

## 9. Read-only verification performed for this report

* Read `docs/current/EVALUATION_PLAN_V8.md`, `TEST_SET_CHRONOLOGY.md`, `ENTRY_POINT_POLICY.md`,
  `reports/remediation/agent_a_sp2_repair.md`, `agent_b_edit_size.md`, `agent_d_baselines_stats.md`
  (headings), `benchmark/datasets/v6/generation_report.json`, `pairs_{train,dev,val,test}.jsonl`,
  `benchmark/splits/split_assignment.json`, `benchmark/corpus/programs_manifest.json`,
  `experiments/final/{data_integrity,entry_policy,protocol,class_driver}.py`,
  `benchmark/scripts/power_analysis{,_report}.py|json`.
* Counted programs/pairs per split from the JSONL files (28/10/9/13 programs; 1129/372/351/488 pairs).
* Called `select_entry_structural` on each of the 64 base programs (no tracing, no scoring).
* Computed pairwise 5-gram token Jaccard on the 64 base programs.
* Re-read per-cluster AUROCs from `reports/remediation/results/audit_recompute.json` and
  computed the SD figures in §5.1; power tables in §5.2 are closed-form normal-approximation
  calculations (no simulation).
* Confirmed `data_integrity.py --dataset benchmark/datasets/v6 --strict` exits 1.
* Wrote only this file and `docs/current/FRESH_PROGRAM_SOURCES.md`.

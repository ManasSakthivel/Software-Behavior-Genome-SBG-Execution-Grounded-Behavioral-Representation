# 08B — Return-Value Limitation: Architectural Analysis (WP-C, Part B)

**Status:** research findings from session WP-C; contains no publication recommendation.
**Provenance rules:**
* V10 / v9c_val were used **label-free and descriptively only** (existing frozen scores + cached traces; no scorer was run, no metric was computed). Every V10 number below is a count from frozen `sbg_v5` scores and cached traces, or is cited from an existing A3 output.
* Every "RV" (return-value) variant is an **exploratory modified representation**, designed *after* V10 results were observed. **V10 is burned for them.** They were evaluated only on v9c_train and v9c_dev, with specification and weights frozen **before** any label-joined metric was computed (`configs/WPC_RV_PREDECLARATION.json`, SHA-256 `e89f5226…bcd08`, in `configs/WPC_RV_PREDECLARATION.sha256`). They are **never original-SBG evidence**.

---

## 0. Short answers

| Question | Answer |
|---|---|
| What is "17/23"? | **Confirmed.** In v10_test, 17 of 23 SC-6 CHANGED pairs have frozen `sbg_v5 == 0.0` exactly (the same 17 are 0 on V3, temporal and state). Analogous zero counts: val 10/18, dev 8/18, train 31/62. |
| What is invisible? | Every SC-6 edit in all four splits (23 + 18 + 18 + 62 pairs) mutates a **`return` expression**: `return X → return not X`, or `return <const> → return <const> + 1`. For the 17 zero pairs, everything SBG reads is **identical** between the SC-6 variant and its SP-only partner. |
| It is worse than 17/23. | The 6 "visible" V10 SC-6 pairs have `sbg_v5` **exactly equal** to their SP-only EQUIVALENT partner (difference 0.0 in 6/6). **SC-6 contributes zero measurable score in 23/23 V10 pairs** (likewise 31/31 train, 10/10 dev, 8/8 val). The 6 are "visible" only because the composed SP transform itself moves the score. |
| Why does the representation miss it? | The changed quantity — the value returned — is *not an input of any genome term*: not a local variable (so not in the state genome's snapshots), not a control-flow event, not an exception, not a call. For 16/17 V10 zero pairs: identical event skeleton, identical call/return/exception locals snapshots, outputs differ on 3–11 of 11 inputs (the 17th is a truncated trace). |
| Is return-value capture technically feasible? | **Yes, trivially.** `sys.settrace` supplies the return value as the `arg` of every `'return'` event; the frozen tracer receives it and discards it; the *outermost* return value is already stored (`ExecutionTrace.return_value`). I recovered per-event return values with a wrapper around the frozen tracer without altering frozen behaviour (state graphs reproduced on 2146/2146 trace files; 2074/2074 pair scores equal to 9 d.p.). |
| Fundamental or implementation limitation? | **Both, at different levels** (§5): an *implementation* limitation of the V5 code (the data is already there), a *design-choice* limitation of SBG as documented (return values are classified output-proximate and barred from the genome, SAFEGUARD-2), and **fundamental for any representation limited to control flow + internal locals**, which cannot see a return-expression-only change by construction. |
| Does adding it fix SC-6? | **Largely, on permitted data, exploratory only.** SC-6 zero-rate 0.49 → 0.10 (pooled dev+train); SC-6 pairs strictly above their SP-matched partner 0/78 → 52/78 (ties 26/78); overall AUROC +0.035 pooled (Holm p = 0.002). But the **output-comparison ceiling on the same input battery is only 0.804 AUROC** (§4.4), so return values do not fix the representation's broader problems. |

---

## 1. Which changes are invisible (EXP-WPC-004, label-free)

Source: `raw/EXP-WPC-004/SC6_FORENSICS_SUMMARY.md`, `sc6_summary.json`, `sc6_pairs_<split>.csv`, `sc6_diffs_<split>.txt` (all 23 V10 diffs were read). "Invisible" := frozen `sbg_v5 == 0` (exact). Partner := label-0 row with the same `group` (same SP transform, no SC-6); cross-checked against the repo's `matched_pair_id` fields: 0 mismatches.

### 1.1 Zero-score counts (SC-6, label 1)
| split | n | v5 = 0 | v3 = 0 | temporal = 0 | state = 0 | all four = 0 | v5 > 0 |
|---|---|---|---|---|---|---|---|
| v10_test | 23 | **17** | 17 | 21 | 21 | 17 | 6 |
| v9c_val | 18 | 10 | 11 | 12 | 11 | 10 | 8 |
| v9c_dev | 18 | 8 | 8 | 13 | 13 | 8 | 10 |
| v9c_train | 62 | 31 | 35 | 52 | 48 | 31 | 31 |

### 1.2 Which V10 pairs
The 17 invisible V10 pairs (SC-6 composed with an SP transform):
`ds_ranked_set__sc6+sp2_s2`, `ds_union_find__sc6+sp2_s2`, `graph_cycle_detection_dfs__sc6+sp2_s2`, `graph_network_delay__sc6+sp2_s2`, `math_coin_change__sc6+sp2_s2`, `math_knapsack_01__sc6+sp2_s2`, `sort_bitonic_sort__sc6+sp2_s2`, `sort_gnome_sort__sc6+sp1_s2`, `sort_gnome_sort__sc6+sp2_s0`, `sort_gnome_sort__sc6+sp2_s1`, `sort_gnome_sort__sc6+sp2_s2`, `sort_gravity_bead__sc6+sp2_s2`, `sort_pancake__sc6+sp2_s2`, `sort_stooge_sort__sc6+sp2_s2`, `sort_tree_sort__sc6+sp2_s2`, `str_decode_run_length__sc6+sp2_s2`, `str_group_anagrams__sc6+sp2_s2`.
The 6 non-zero V10 pairs: `ds_min_heap_array__sc6+sp3_s1` (0.0246), `graph_topological_kahn__sc6+sp3_s2` (0.0237), `graph_topological_kahn__sc6+sp8_s2` (0.4616), `math_fib_matrix__sc6+sp2_s2` (0.0197), `math_knapsack_01__sc6+sp8_s1` (0.2771), `sort_radix_sort_lsd__sc6+sp3_s0` (0.0260). **All six equal their SP-only partner's score exactly.**

### 1.3 Pattern of the invisible set
* **Edit:** return-expression mutations only (`not X`, `+ 1`). On V10, 17/19 pairs with edit-size ≤ 10 are zero; 0/4 with larger edits are zero.
* **SP-type confound:** SP-2 → 16/17 zero in V10, 8/9 in dev, 29/30 in train; SP-3 / SP-8 / SP-11 are almost never zero (V10 0/3, 0/2; train SP-8 2/12). Edit size tracks SP type (every SP-2 pair has edit = 4), so **edit size and SP type cannot be separated** in this data. What the data does show: SBG's score on an SC-6+SP pair equals the score of the SP-only partner in every case I could check.
* **Program families:** sorting 9/17 (`sort_*`), the rest from ds/graph/math/str — no single family explains it.

---

## 2. Why the current representation misses them

### 2.1 What SBG V5 consumes (verified in source: `SBG/sbg/v3`, `SBG/sbg/v5`, `SBG/sbg/v2/execution/normalizer.py`)
* V3 (50% of V5): line-coverage sets, call-bigram sequence, call-frequency histogram, exception-type distribution, call depth, coverage consistency across inputs, input sensitivity of coverage, exception-causality hash.
* Temporal (25%): trigrams, entropy, exception triples, causal/phase/loop structure — derived from event types and function names.
* State (25%): abstract classes of **local-variable** values at every event (including `line`), converted into creation/mutation/deletion/error transitions.
* **Return values and stdout are never read.** The normalizer docstring says "return_value and stdout are never accessed" (SAFEGUARD-2). My grep of `sbg/v3`, `sbg/v5` and `sbg/v2/execution/normalizer.py` for `return_value`/`stdout` finds: (i) that docstring; (ii) `sbg/v5/invariant_identity.py`, a static-AST `has_return_value` flag — I found no source file importing it, so it is not part of the dynamic distance; (iii) `state_transition_genome.py:581`, which sets `return_value=None` when it builds a synthetic trace. The tracer records `return_value` for the outer call (`tracer.py:316`), but nothing in V3/V5 consumes it.

### 2.2 Channel analysis on the 17 invisible V10 pairs (partner → variant; the SP transform cancels)
| Channel | result (V10, 17 zero pairs) |
|---|---|
| Event skeleton (event types + functions incl. line events) | **identical in 17/17** |
| Locals snapshots at call/return/exception events (memory addresses masked) | **identical in 17/17** |
| Return value on the protocol inputs | **differs on ≥ 1 input in 17/17** (3–11 of 11 inputs per pair) |
| Exceptions / stdout | identical |
| Coverage-set size | differs on 0 inputs |
| Cause class | A (return-expression only, all else identical): **16**; B (abstraction collapse): **0**; C (battery-blind: outputs identical on all 11 inputs): **0**; D (truncated trace, `sort_stooge_sort`): **1** |

Other splits: A = val 8 / dev 8 / train 21; C (battery-blind) = val 1 / train 7; D = val 1 / train 3 (of which 2 truncated, 1 missing cache). **Class B (abstraction-granularity collapse) was never observed**, so it is not supported as a cause.

**Mechanism.** `return not result` changes only the expression on the final `return` line. The new value exists only as the transient value of that expression: it is not bound to a local, so the locals snapshots are unchanged; the `return` line executes either way, so the control-flow skeleton and coverage are unchanged; calls and exceptions are unchanged. Every channel SBG reads is identical while the observable output differs. Caveat: the shared cache stores no line-event snapshots, so "identical locals at every line event" is not directly checked for these pairs — it follows by construction for a pure `return <expr>` edit, and the in-process re-extraction (EXP-WPC-001) reproduced all frozen state scores, which is consistent with it.

**Partial visibility through locals.** If the returned value is also bound to a local (`result = …; return result`), a change to *that* value moves the state genome. Across the 2146 dev+train trace files, 129,420 / 268,125 return events (48%) have a return value that coincides with some local at that event. For the SC-6 mutations here (`not X`, `X + 1`) the *mutated* value is by construction not that local: in the V10 zero pairs, the returned `repr` appears among the entry function's return-event locals on an input where the return differs in only 1 of 17 pairs (val 1, dev 1, train 4 in the other splits).

### 2.3 What the 6 "visible" pairs show
Their scores are identical to their SP-only partner's (difference exactly 0.0). SBG's score for an SC-6+SP pair is the score of the SP transform. "Visible" therefore does not mean "SC-6 detected"; it means "the SP transform changed some structural feature". SC-6-attributable detection by SBG is **0/23 on V10** (and 0/78 strictly-above-partner on dev+train, §4.2), not 6/23.

---

## 3. Is return-value capture technically feasible?

| Aspect | Evidence |
|---|---|
| Interpreter support | `sys.settrace` callback `(frame, event, arg)`; for `event == 'return'`, `arg` is the return value (None when unwinding by exception). The frozen tracer (`SBG/sbg/extraction/dynamic/tracer.py:336`) takes `arg` but never reads it. |
| Existing data | `ExecutionTrace.return_value` (tracer.py:65, 316) already holds the outermost return value; the shared cache stores a capped `repr` of it (used in EXP-WPC-004). |
| My implementation | `scripts/wpc_extract.py` (≈ line 222) wraps the frozen trace function: it calls it unchanged, then on `'return'` events attaches `ret_repr = repr(arg)` to the already-recorded `TraceEvent`. Frozen state graphs reproduced exactly (2146/2146 trace files; 2074/2074 pair scores to 9 d.p.). |
| Cost | One `repr()` per return event (the tracer already does this for every local, capped at 100 chars). 268,125 return events in the 2146 trace files; no new failure mode observed. |
| Determinism hazards | `repr` of functions/objects contains memory addresses (`<function … at 0x…>`) — nondeterministic across processes; must be masked/abstracted (the frozen abstraction maps them to a fixed class). |
| Other hazards | Huge or side-effecting `__repr__`; traces truncated by the event cap (class D) never reach the return event; the in-tracer `repr` cap (100 chars) limits what distinguishes large collections (`rv_abs_full` with a 1500-char cap gave identical scores in the pair table). |

**Conclusion:** capture is a few-line engineering change. The open questions are *design* (§5) and *evaluation* (§6), not feasibility.

---

## 4. Exploratory feasibility experiment (EXP-WPC-006; permitted data; not SBG evidence)

Variants (pre-declared, fixed weights, **no weight sweep or tuning run**): `RV_abs100`, `RV_abs_full`, `RV_type_abs` = frequency-weighted Jaccard distance over the multiset of `(function_index | abstract(return repr))` (same abstraction domain as the frozen state genome; `RV_type_abs` adds a Python-type bucket). `V5+RV_*` = 0.8·V5 + 0.2·d_RV; `S+RV_abs_full` = 0.8·State + 0.2·d_RV. Ceilings (label oracles, **not competitors**): `ceiling_rv_hash` (concrete-value hashes of all returns), `ceiling_rv_entry_hash` (entry function only) — these equal output comparison on the protocol inputs.
Holm family (declared): the four `V5+RV…`/`S+RV…` variants vs frozen V5. Source: `raw/EXP-WPC-006/rv_results.json`. Program-cluster bootstrap B = 2000, seed 42.

### 4.1 Overall AUROC
| Variant | v9c_dev (464) | v9c_train (1610) | pooled (2074) | Δ vs V5, pooled |
|---|---|---|---|---|
| V5 (frozen) | 0.7854 | 0.7352 | 0.7458 | — |
| State (frozen) | 0.8161 | 0.7534 | 0.7663 | +0.0205 (Holm 0.006; EXP-WPC-003) |
| RV_abs100 (alone) | 0.7893 | 0.7252 | 0.7387 | −0.0071 (p 0.57, outside family) |
| RV_type_abs (alone) | 0.7896 | 0.7255 | 0.7390 | −0.0068 (p 0.59, outside family) |
| V5 + RV_abs100 | 0.8299 | 0.7679 | 0.7808 [0.759, 0.803] | **+0.0350 (Holm 0.002)** |
| V5 + RV_type_abs | 0.8300 | 0.7679 | 0.7809 | +0.0351 (Holm 0.002) |
| S + RV_abs_full | 0.8539 | 0.7828 | **0.7977** [0.775, 0.820] | **+0.0519 (Holm 0.002)**; vs State +0.0314 (p 0.001, outside family) |
| ceiling: rv_hash (all returns) | 0.8421 | 0.7725 | 0.7870 | label-oracle |
| ceiling: rv_entry_hash | 0.8528 | 0.7906 | **0.8040** [0.776, 0.831] | label-oracle |

`RV_abs100` and `RV_abs_full` are identical in every row. `RV_type_abs` differs from `RV_abs100` by ≤ 0.0004 AUROC: the type bucket adds essentially nothing beyond the abstract value class.

### 4.2 SC-6 effect (permitted splits; SC-6 n = 78 usable pairs)
| Variant | SC-6 zero-rate (dev / train / pooled) | matched-set concordance, pooled | strictly above SP-matched partner | tied |
|---|---|---|---|---|
| V5 (frozen) | 0.44 / 0.50 / 0.49 | 0.500 | **0 / 78** | 78 |
| State (frozen) | 0.72 / 0.78 / 0.77 | 0.500 | 0 / 78 | 78 |
| RV_abs100 alone | 0.06 / 0.18 / 0.15 | 0.833 | 52 / 78 | 26 |
| RV_type_abs alone | 0.06 / 0.18 / 0.15 | 0.840 | 53 / 78 | 25 |
| V5 + RV_abs100 | 0.00 / 0.13 / 0.10 | 0.833 | 52 / 78 | 26 |
| ceiling rv_entry_hash | 0.06 / 0.17 / 0.14 | 0.846 | 54 / 78 | 24 |

(Concordance 0.500 for frozen scores = all ties, consistent with §2.3.) Coarse abstraction-level RV variants reach 52–53 / 78, close to the concrete-output ceiling of 54 / 78.

### 4.3 Why do 24–26 SC-6 pairs still tie with their partner? (EXP-WPC-006b, descriptive)
Source: `raw/EXP-WPC-006/rv_sc6_breakdown.json` (78 pairs).
| edit form | n | RV above partner | RV tied | return type changed on some input |
|---|---|---|---|---|
| `return X → return not X` | 74 | 51 | 23 | 53 |
| `return const → return const + 1` | 4 | 1 | 3 | 1 |

Of the 26 ties: 18 are `not`-form with unchanged return type on every input, 5 are `not`-form with a type change on some input, 3 are `+1`-form (type unchanged). I did **not** diagnose individual tied pairs. Candidate explanations — abstraction classes that do not separate the changed values, battery-blindness, truncated traces, broken SP-8 partners — are *untested hypotheses*. The concrete-hash ceiling also ties on 24/78, so a large share of the ties is not separable by any output comparison on this battery.

### 4.4 Side effects and the ceiling
* **EQUIVALENT / CHANGED zero-rates (pooled):** V5 0.569 / 0.168; State 0.789 / 0.261; RV_abs100 alone 0.843 / 0.364; V5+RV_abs100 0.569 / 0.129. Adding the RV term leaves V5's equivalent-side zero-rate unchanged and lowers its CHANGED zero-rate.
* **The ceiling is low.** Concrete entry-return hashes — plain differential testing on the 11 protocol inputs — reach only **0.804** pooled AUROC (zero-rate CHANGED 0.293, zero-rate EQUIV 0.920: 29% of CHANGED pairs have identical outputs on all battery inputs, and 8% of "EQUIVALENT" pairs have different outputs). The input battery and pair-label quality (e.g. the broken SP-8 partners in EXP-WPC-004 §5) cap *any* output-based detector on this data. Return-value capture removes the SC-6 blind spot; it does not make the instrument near-perfect.
* **Tautology risk.** An RV term that distinguishes `not X` from `X` is an output comparison; if labels derive from output comparison, the metric is partly circular.

---

## 5. Fundamental limitation or implementation limitation?

1. **Implementation level (this codebase):** the return value is available (settrace `arg`; `ExecutionTrace.return_value`) and unused; the fix is a few lines. → **implementation limitation**.
2. **Design level (documented SBG principle):** `SBG/docs/archive/v2/FEATURE_ORACLE.md` (SAFEGUARD-2) classifies *return value hash* (F11) and *stdout hash* (F12) as OUTPUT-PROXIMATE: "Equivalent to differential testing. NEVER in SBG genome." F13 (return value *type name*) is classified output-free and admissible but is not implemented in V5; EXP-WPC-006 shows the type bucket adds ≤ 0.0004 AUROC over the abstract value class, and a type name cannot separate `X + 1` from `X`. Adding return values changes the method's identity (structure genome → structure + differential testing), and every RV variant above breaches the documented guard. → **design-choice limitation**.
3. **Representation-class level:** for any representation built only from control flow, call structure, exception structure and the values of *internal locals*, a return-only expression change (no new local, same branches, same calls) is invisible by construction. → **fundamental limitation of that class**, not of SBG's weighting or thresholds. Widening the class to return values (or every evaluated sub-expression) is the only remedy, and it is output-proximate by definition.
4. **Not a thresholding artefact:** the zero scores are exact zeros, and the same 17 pairs are zero in every sub-genome.

---

## 6. Additional experiments needed (none run in this session unless stated)

| # | Experiment | Why | Data requirement |
|---|---|---|---|
| 1 | **Confirmatory test of any RV variant:** freeze spec + weights (config + code SHA-256) → score once on a **fresh withheld set**, with one pre-declared primary contrast (e.g. V5+RV vs V5, SC-6 stratum + overall) | The dev/train results are exploratory; V10 and val cannot be used for variants designed after their results were seen | New programs/pairs unused in any design decision (not in the current populations) |
| 2 | **SC-6 power / SP crossing:** only 23 V10 pairs, SP-2 confounded (16/17 zeros). Build SC-6 crossed with every SP type | Separates "SC-6 invisible" from "SP-2 + small edit invisible"; gives detection-rate CIs | Newly generated |
| 3 | **Negative controls:** value-preserving return edits (`return (X)`, `return x if True else x`, `return +x`) | Shows an RV term does not flag semantically null edits (false-positive control) | Generated |
| 4 | **Abstraction-granularity sweep (pre-declared):** value class, size class, exact hash; truncation caps | Class B never observed in frozen state; tests whether granularity explains the ties in §4.3 | permitted splits first, then fresh set |
| 5 | **Mutation-type taxonomy** beyond `not`/`+1`: sub-expression changes, off-by-one in a non-return expression whose result is only returned (no local), edits inside lambdas/comprehensions | Quantifies which value-only edits are invisible vs partly visible through locals | Generated |
| 6 | **Diagnose the 24–26 residual ties** individually (abstraction collapse / battery-blind / truncated / broken SP-8 partner) | Separates representation from battery from label noise | Existing dev/train |
| 7 | **Independent input battery:** rerun SC-6 detection with a different, larger input set (or per-pair distinguishing inputs) | The ceiling is only 0.804 on the protocol battery; separates battery from representation effects | New inputs, sandboxed execution |
| 8 | **Line-/sub-expression-level value capture** (e.g. `sys.monitoring` or AST-level instrumentation) | Tests whether widening beyond `return` events catches more value-only edits | Implementation work |
| 9 | **Plain differential-testing baseline** on matched inputs | RV-augmented SBG approaches differential testing; the 0.804 ceiling here *is* that baseline on this battery — a proper baseline needs its own inputs | Existing baselines; outside WP-C scope |
| 10 | **Tracer-limit sensitivity** (event cap, timeout, input subset; handoff item 4) — **not done**; class D (truncated/missing) in 1/17 V10, 1/10 val, 3/31 train zero pairs | Quantifies how many invisible pairs are artefacts of truncation | Existing data, re-extraction with altered limits |

---

## 7. Limits of this analysis
* V10/val were not re-scored; V10 numbers are descriptive counts of frozen scores and cache properties (no metrics).
* RV variants were designed after V10 results were observed (they target a known V10 weakness) and evaluated only on v9c_dev/train; those SC-6 sets use the same generator and the same two edit forms as V10, so they do not show generalisation to other value-only edit types.
* The shared trace cache keeps only run 0 of the runs and no line-event snapshots (EXP-WPC-004 analyses); the RV variants and state variants come from the in-process re-extraction that follows the frozen extraction procedure (EXP-WPC-001 logs).
* Class "C (battery-blind)" is defined on 11 inputs only; the oracle's distinguishing input is unknown.
* The EQUIVALENT label is imperfect for some SP-8 pairs (crash on all inputs); this limits every AUROC above.
* `math_gray_code` is missing from the train cache (2 SC-6 pairs: 1 zero, 1 visible, not in EXP-WPC-006; counted D in EXP-WPC-004).

## 8. Raw outputs
`raw/EXP-WPC-004/*` (forensics); `raw/EXP-WPC-006/rv_results.json` (RV variant metrics); `raw/EXP-WPC-006/rv_sc6_breakdown.json` (tie breakdown); `raw/EXP-WPC-001/**/*.json.gz` (per-program extraction incl. `rv_*` multisets and leakage diagnostics); `raw/EXP-WPC-002/*pairs.csv` (per-pair `rv_*` distances); `configs/WPC_RV_PREDECLARATION.json(.sha256)`.

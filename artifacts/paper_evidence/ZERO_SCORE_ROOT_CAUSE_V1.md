# ZERO_SCORE_ROOT_CAUSE_V1

Branch `remediation/sbg-v4` (from `8386eb5`). Everything here is EXPLORATORY diagnosis; no frozen artifact, scorer or dataset was modified.
Evidence: `raw/zero_score_population_v1.json` (scores only, all splits), `raw/zero_score_diagnostic_v1.json` (pair-level forensics, train+dev, 2114 pairs),
`EQUIVALENT_LABEL_AUDIT.json`. Code: `experiments/final/zero_score_population.py`, `diagnose_zero_scores.py`, `audit_equivalent_label_validity.py`.

**Forensic discipline.** The output-oracle forensics were run on v9c **train and dev only**. The v9c val split appears here only through its already-frozen scores
(`zero_score_population_v1.json`). The burned v8 TEST split was not forensically examined; the only test-derived content is its score-file zero count in the
population table, and one aggregate label-audit pass over test EQUIVALENT variants (17/409 differ) that was run once, discarded, and then removed from the audit (the
committed `EQUIVALENT_LABEL_AUDIT.json` covers train/dev/val only). Nothing from it informed any decision.

## 1. The 37% figure, exactly
| Item | Value | Source |
|---|---|---|
| Population | v9c VAL matched-complete: 432 pairs = 216 matched sets, 11 programs | `V9_VAL_EVALUATION.json:v9c_matched`, `evaluate_v9.matched_complete` |
| Exact zeros (`sbg_v5 == 0.0`) | **160 / 432 = 37.04 %** | `fraction_sbg_v5_exactly_zero` = 0.3704; reproduced from `pairs_v9c_val_*` + `pairs_v8val_*` |
| CHANGED | **33 / 216 = 15.3 %** | `zero_score_population_v1.json` |
| EQUIVALENT | **127 / 216 = 58.8 %** | same |
| Unevaluated | 4 rows in the val files (1 nonterminating, 1 import_error on each side's file; 2 matched sets dropped); **none of them carries a score** (`unevaluated_rows_have_scores = false`) | same |

The 37 % is therefore a **mixture of two very different things**: the zero rate among CHANGED pairs (15 %) and among EQUIVALENT pairs (59 %). A zero on an EQUIVALENT pair is the *correct* answer.
Same pattern elsewhere: dev 32.1 % (CH 31/232, EQ 118/232), train 38.1 % (CH 147/825, EQ 481/825). In the v8 design 34.9–42.7 % (v8 test 388/956 = 40.6 %, score-file count only).

Are the zeros exact or rounded? Scores are `round(.., 9)`. The smallest non-zero `sbg_v5` in any file is 1.07e-5, so rounding cannot create zeros. For the 178 zero-scored CHANGED pairs given a fresh genome-level re-extraction (train+dev), the **unrounded** `d_v3`, `d_temporal` and `d_state` are all exactly `0.0`.
Every zero has all three components exactly zero in every scored file (`components_all_exact_zero_given_v5_zero = true`).

Category G (unevaluated represented as zero): **ruled out.** `score_pair` returns `None` when either side failed; unevaluated rows carry `scores = null` and are excluded before any metric; `v5_full == 1.0` for all evaluated rows in every file (the `d_temporal := d_v3` / `d_state := d_v3` fallback branches in `extraction.score_pair` were never taken), so no zero arises from a fallback.

## 2. Breakdown (v9c matched; counts are n_zero / n)
**By label and split:** val CH 33/216, EQ 127/216; dev CH 31/232, EQ 118/232; train CH 147/825, EQ 481/825.

**EQUIVALENT zeros by SP family (train+dev, `diagnose_zero_scores.py`):** SP-1 115/123, SP-2 161/173, SP-4 162/174, SP-6 134/144, SP-9 3/3 (all ≈ zero); SP-5 10/116, SP-3 **0/172**, SP-8 11/104, SP-11 3/48. All 481+118 EQUIVALENT zeros have **identical return value, exception and argument mutation on the protocol inputs** (`EQ_zero_behaviour_identical`) → category B, legitimate.

**CHANGED zero rate by SC family (train+dev):** SC-13 0/112, SC-5 4/90, SC-8 5/82, SC-2 12/125, SC-10 19/83, SC-4 21/139, SC-11 26/158, SC-1 29/135, SC-3 23/52, SC-6 **39/80**.
By val edit bucket: CHANGED edit 3-5 → 17/55, 6-10 → 12/69, 11-20 → 4/76, >20 → 0/16; EQUIVALENT ≤2 → 37/43, 3-5 → 30/41, 6-10 → 59/80, 11-20 → 1/37, >20 → 0/15.
So **zeros concentrate in small edits, and the zero indicator is itself strongly correlated with edit size** (EQ with edit ≥ 11 almost never zero, because SP-3/SP-8/SP-11 are the large, non-zero rewrites).
**By truncation:** val 14/46 truncated vs 146/386 not (30 % vs 38 %) → truncation is not a driver (84 truncated pairs in train+dev, 25 zero, all from `math_catalan_number`, `math_pascal_row`, `math_gray_code`).

## 3. Why a CHANGED pair scores zero (train+dev: 178 zero-scored CHANGED pairs, oracle on the protocol's own 11 inputs)
| Class | train | dev | Meaning |
|---|---|---|---|
| (i) **No output difference on the protocol inputs** and identical raw state values | 65 | 14 | The labelled-CHANGED mutation is **not dynamically exercised / not observable** on these inputs. Zero is the correct answer for the *inputs*; the label is only statically checked. Category B. |
| (ii) No output difference, raw local values differ, but the abstraction collapses them | 28 | 7 | e.g. `str_atoi_manual` SC-2: snapshots differ, all values stay in the same sign/size class. Category B/D (representation limit). |
| (iii) **Output differs, trace byte-identical** (event types and all local values) | 23 | 4 | e.g. `ds_ring_buffer_stats` SC-6 (`return averages` → `return not averages`). The return value is never recorded in a trace (output-free protocol, `SAFEGUARD-2`). 23 of 27 are SC-6. By design, not a defect. |
| (iv) **Output differs, raw values differ, abstraction collapses them** | 23 | 6 | e.g. `ds_rle_encode` SC-10: `run_count` 2 vs 1 and `averages` `[3.0]` vs `[1.0]` both map to `POSITIVE` / `SINGLETON` (`_repr_to_abstract`). Category **D/F**: a coarse, information-discarding abstraction (a mathematical limitation of the representation, not a bug). |
| (v) Output differs, abstract values differ, state transitions identical | 3 | – | `ds_skip_list_search` SC-10+SP-4: the state genome records only *changes* of abstract value between consecutive events (`pre_av == post_av → continue`). |
| (vi) Output differs, event stream differs (e.g. 465 vs 415 events), all three genomes still identical | 5 | – | `line` events are not consumed by the v3/temporal features (calls/returns/exceptions only) and state transitions are unchanged. Representation limit. |

Fraction of CHANGED pairs by oracle (train): **249 / 825 = 30.2 %** show no output difference on the protocol inputs (dev 57/232 = 24.6 %); zero-rate there 93/249 = 37.3 %.
For CHANGED pairs with an output difference the zero rate is only **54 / 576 = 9.4 %** (train). That is, **SBG V5 returns non-zero for ~91 % of CHANGED pairs whose behaviour verifiably differs on the protocol inputs.**
The `changed_nonzero_with_no_output_difference` count (156 train) shows non-zero scores are also given to pairs whose outputs are identical (internal state / call structure differs).

## 4. Population-level label defects found (not scorer defects)
`EQUIVALENT_LABEL_AUDIT.json` (train/dev/val EQUIVALENT variants; static undefined-name rule + dynamic output oracle; no SBG score read):
| Split | EQ pairs | output differs | SP-8 (extract-method) | SP-11 (container swap) |
|---|---|---|---|---|
| train | 842 | **73** (8.7 %) | 37/83 variants raise `NameError` (`_extracted_0_3` undefined) | 36/42 return a `deque` instead of a `list` (27 are repr-only type changes; 3 raise) |
| dev | 233 | 13 | 7/23 | 6/6 |
| val | 218 | 16 | 10/23 | 6/12 |
Example (`ds_lfu_simulation`, `sp-8_s0`): the helper call `_extracted_0_3(lru_key)` is emitted but the helper is not defined in the variant → `NameError` on the first eviction. These pairs are labelled EQUIVALENT, score high (SP-8 median `sbg_v5` = 0.478), and so **depress SBG's AUROC through label noise**.
Direction of bias: invalid EQUIVALENT labels count as false positives for SBG, but also contaminate every other predictor; they are a benchmark defect that cannot be fixed in place (frozen), only quantified.

## 5. Code paths that can return zero, classified
| Path | Location | Class |
|---|---|---|
| `distance_v3`: identical coverage size, call-transition bigrams, call frequencies, exception stats, depth stats, consistency, input sensitivity, causality hash | `sbg/v3/genome.py::distance_v3` | B (identical observed call-level behaviour) |
| `d_call_trans = 0.0` / `d_trigrams = 0.0` when both bigram/trigram sets are empty | same / `sbg/v5/temporal_genome_v5.py::distance` | A (mathematical convention); empty only for call-free programs; not the source here |
| `StateTransitionGraph` distance 0 when `all_keys` empty or transition multisets equal; unchanged abstract values are skipped | `sbg/v5/state_transition_genome.py::distance`, `extract` (`pre_av == post_av: continue`) | B for identical behaviour; **D/F** for collapsed value changes (§3 iv, v) |
| `_repr_to_abstract`: sign/size-class abstraction (every positive int → `POSITIVE`, every 2+ element container → `MULTI_ELEMENT`, every non-empty string → `NON_NULL`) | same file | D/F: information discarded by design |
| `score_pair` clip `min(1, max(0, d))`, `round(.., 9)` | `experiments/final/extraction.py` | F: **ruled out** (min non-zero 1e-5; unrounded = 0) |
| Fallback `d_temporal = d_v3`, `d_state = d_v3` when a component fails | `extraction.score_pair` | G-candidate: **ruled out** (`v5_full == 1` everywhere) |
| `score_pair` returns `None` for failed extraction | same | G: correctly unevaluated, not zero |
| Return values never traced | `sbg/extraction/dynamic/tracer.py` (events carry locals only), `SAFEGUARD-2` | A (protocol choice) |

## 6. Conclusions established by evidence
1. **No scorer implementation defect that produces zero was found** (categories C, E, F, G ruled out by data; D is a design-level information loss, not a coding error). I do not claim a "fix" for the 37 %.
2. **~79 % of the zeros (127/160 in val) are on EQUIVALENT pairs; in train+dev all 599 EQUIVALENT zeros were verified behaviour-identical by the oracle (val was not oracle-run, so the val statement rests on the same pattern, not on a separate check).** The zero rate cannot be "reduced" without making SBG worse on EQUIVALENT pairs.
3. The CHANGED-side zeros (15 % in val, 17.8 % train / 13.4 % dev) arise from: (a) mutations with **no behavioural effect on the protocol inputs** (the benchmark labels CHANGED by static reachability only; 25–30 % of CHANGED pairs are not dynamically distinguishable), (b) deliberate omission of return values, (c) a coarse state abstraction (classes (ii)+(iv) = 64 of 178 zero-scored CHANGED in train+dev), (d) call-level features that ignore line-level structure.
4. The pooled 37 % number is largely a **property of the benchmark's EQUIVALENT half**, not of the method's recall.
5. Benchmark label defects (SP-8 `NameError`, SP-11 type change, CHANGED-not-observable-on-protocol-inputs) are real, quantified, and unresolved in the frozen datasets.

## 7. Hypotheses NOT established
* That increasing abstraction resolution (magnitude/size buckets) will improve discrimination: motivated by §3 (ii)+(iv) (64 of 178 zero CHANGED in train+dev) but untested; it may also raise EQUIVALENT-pair noise.
* That recording return values would help: excluded by protocol (output-free), not evaluated.
* That wall-clock / hash-seed effects alter zeros: not observed on this machine for v8 programs.

## 8. Corrective actions and required regression tests
| Item | Action | Test |
|---|---|---|
| Label-validity (SP-8/SP-11) | New validator `audit_equivalent_label_validity.py`; flagged-pair sensitivity analysis; **no change to frozen datasets** | static undefined-name rule (existing test), dynamic-oracle test on a NameError helper |
| Unevaluated ≠ zero | Regression guard that every unevaluated row has `scores = null` and no evaluated row has `v5_full != 1` in frozen files | `tests/test_zero_score_v4.py` |
| Legitimate zero | Identical programs/renames score exactly 0; a mutated-but-unobservable program scores 0 | same |
| Abstraction collapse | Document current behaviour (V5 maps `run_count` 2 and 1 to the same state) as a **characterisation test**; V6 variant (if built) must separate them while preserving rename invariance and `d(g,g)=0` | same |

## 9. Correction to §3 classes (ii)/(iv) (added after the V6 development run; `raw/zero_score_address_correction_v1.json`)

The §3 forensic compared raw local-variable `repr` strings. `repr` of a function/iterator object embeds a memory address and (after SP-2) the renamed
qualname, so a raw "value difference" can be an artefact. Re-checking the 72 zero-scored CHANGED pairs whose raw values differed (this includes the
(ii)/(iv)/(v)/(vi) populations) after normalising `0x…` addresses and `<function qualname at 0x…>`:

* **32 of 72 differ only by object address / renamed qualname** — no value difference exists. They belong with classes (i)/(iii) (not exercised / invisible), not with "information lost by the abstraction".
* **40 of 72 are real value differences** (e.g. `gaps [701,…]` vs `[702,…]`, `sequence [0]` vs `[2]`, `INT_MAX 2147483647` vs `…649`, `run_count 2` vs `1`).

So the abstraction-collapse population is **40, not 64** of 178 (22 %, not 36 %). §6 item 3(c) and §7 should be read with 40 in place of 64.
Of the 40 real differences the graded V6 abstraction recovers 19 and 21 stay zero (large integers beyond digit-count resolution, long-list elements
beyond the 100-char `repr` cap, dict-key edits, and 1-element containers whose element value is not tracked).

# Representation case studies (FINAL SPRINT, Part 3)

Status: **qualitative, trace-backed case studies on frozen V10 data.** They illustrate behaviour; they are not evidence
of generalisation. V10 is the 19-program, 638-pair split produced by the same author and generation procedure as
development (see `INDEPENDENT_EVALUATION_LIMITATIONS.md`); it is *not* independently authored software.

Reproduce:

```bash
cd experiments/final
PYTHONHASHSEED=0 ../../../venvs/py313/bin/python sprint_case_studies.py select   # -> REPRESENTATION_CASES_selection.json
PYTHONHASHSEED=0 ../../../venvs/py313/bin/python sprint_case_studies.py trace    # -> REPRESENTATION_CASES_traces.json
```

* Selection rules are deterministic and are written at the top of
  [`sprint_case_studies.py`](../../experiments/final/sprint_case_studies.py). They were fixed before any case was
  inspected; each case is the **median** member of a rule-defined pool (or the first member by `pair_id` in the most
  frequent family for the failure), not a hand-picked best example. Pool sizes: C1 = 45, C2 = 10, C3 = 18, C4a = 11,
  C4b = 11 matched sets/pairs.
* `trace` re-extracts only the 10 selected pairs with the frozen extractor (protocol `output_free_v8`, CPython 3.13) and
  **asserts the re-scored values equal the frozen scored file: 10 / 10 match** (tolerance 1e-9).
* Raw numbers: [`REPRESENTATION_CASES_selection.json`](REPRESENTATION_CASES_selection.json),
  [`REPRESENTATION_CASES_traces.json`](REPRESENTATION_CASES_traces.json).
* Model scores `M_*` are the **frozen logit scores** of `V10_MODELS_FROZEN.json` (fitted on v9c train only).
  `M_EX` = logistic model on `edit + exception_fraction + call_count + coverage_size`; `M_EX+V5` adds `sbg_v5`.
  Higher = more "changed"; only the *ordering inside a matched set* is meaningful.
* "State transition" means a tuple `(func_idx, pre_state, event_kind, post_state)` with abstract value states
  (`ZERO`, `POSITIVE`, `MULTI_ELEMENT`, …) and call-order function indices (rename-invariant); counts are over
  5 runs × 11 inputs (55 traces).
* Ground-truth labels were validated by a dynamic oracle on the protocol inputs (`label_validation: dynamic_oracle`,
  `gt_tier: GT-T3` in `pairs_test.jsonl`). They establish **equivalence/difference under the fixed inputs and
  observation protocol only**, not universal semantic equivalence.

## What the representation is (verified in code)

SBG V5 = 0.50 · V3 call-level + 0.25 · temporal + 0.25 · state-transition distance between the traces of base and
variant ([`sbg/v3/genome.py`](../../sbg/v3/genome.py),
[`sbg/v5/state_transition_genome.py`](../../sbg/v5/state_transition_genome.py)). The tracer is `sys.settrace`
([`sbg/extraction/dynamic/tracer.py`](../../sbg/extraction/dynamic/tracer.py)) and records call/return/line/exception
events with ≤100-character `repr` snapshots of **locals**. The state module documents SAFEGUARD-2: output values are
never read. A consequence (Case 3) is that a change that alters only *what is returned*, without altering control flow,
call counts or locals, is invisible.

## Summary table

| Case | Pair (CHANGED / EQUIVALENT) | Label | edit (C / E) | SBG V5 (C / E) | `M_EX` (C / E) | `M_EX+V5` (C / E) | Set outcome SBG / `M_EX` / `M_EX+V5` |
|---|---|---|---|---|---|---|---|
| 1 Correct detection | `sort_pancake__sc10+sp3_s1` / `sort_pancake__sp3_s1` | SC-10 mutation changes behaviour | 28 / 26 | 0.132 / 0.028 | 0.218 / 0.563 | −1.492 / 0.310 | correct / **wrong** / wrong |
| 2 Correct equivalence | `graph_cycle_detection_dfs__sc2+sp1_s1` / `…__sp1_s1` | SP-1 rename only | 14 / 14 | 0.524 / **0.000** | 0.257 / −0.534 | 0.718 / −0.488 | correct / correct / correct |
| 3 Failure to detect | `ds_ranked_set__sc6+sp2_s2` / `…__sp2_s2` | SC-6 return mutation | 4 / 2 | **0.000** / 0.000 | −0.539 / −0.540 | −0.655 / −0.689 | tie (scored 0.5) / correct by 0.001 (edit-size artefact) / correct by 0.03 |
| 4a Adding SBG hurts | `ds_ranked_set__sc5+sp2_s1` / `…__sp2_s1` | SC-5 guard inversion | 4 / 2 | 0.313 / 0.000 | 0.890 / −0.540 | −1.062 / −0.689 | correct / correct / **wrong** |
| 4b Adding SBG helps | `ds_min_heap_array__sc11+sp3_s2` / `…__sp3_s2` | SC-11 argument swap | 26 / 24 | 0.701 / 0.031 | 0.302 / 0.622 | 2.058 / 0.317 | correct / **wrong** / correct |

(Case 3: for `M_EX` the CHANGED variant scores −0.5386 vs −0.5396 for the EQUIVALENT one. Every execution statistic
is exactly 0 for both, so the difference comes solely from the 2-token edit-size difference (edit weight +0.003 per
standardised unit) and is not behaviour information; for SBG the tie is exact, 0.0 vs 0.0.) All values:
`REPRESENTATION_CASES_selection.json`.

---

## Case 1 — Correct detection of a behavioural change (median pool member, pool = 45)

**Source change.** Both variants share the same decoration (SP-3: dead branches such as `if False: pass`, `if 1 == 0:
_ = 'dead'`, docstring turned into an expression statement). The CHANGED variant additionally applies SC-10 at one
line (canonical `ast.unparse` diff, `lo += 1` → `pass`):

```diff
-            lo += 1
+            pass
```

Raw edit size 28 vs 26 for the matched equivalent: the two variants are nearly the same size of edit, so edit size
carries almost no information about which one changes behaviour (edit-size baseline M_E: 0.84 vs 0.75 — a ranking
driven by the 2-token difference).

**Trace evidence (base → variant).**

| | EQUIVALENT variant | CHANGED variant |
|---|---|---|
| calls | 125 → 125 | 125 → **145** |
| distinct state transitions | 20 → 20 | 20 → **19** |
| transitions only in base | 0 | 1: `(1, ZERO, state_mutation, POSITIVE)` × 70 |
| shared transitions with different frequency | 0 | **14** (e.g. `(1, ABSENT, state_creation, POSITIVE)` 310 → 390; `(1, ZERO, state_deletion, ABSENT)` 15 → 180) |
| line coverage (`coverage_size`) | 19 → 26 (dead-code lines) | 19 → 26 |

The removed `lo += 1` is a state *mutation* of a loop index from `ZERO` to `POSITIVE`. It disappears from the
transition multiset, and the changed loop bounds shift the frequency of 14 other transitions. The equivalent variant
is *byte-for-byte identical* in its transition graph despite a 26-token edit.

**Scores.** SBG V5 0.132 (CHANGED) vs 0.028 (EQUIVALENT); components V3 0.084/0.056, temporal 0.057/0.000,
**state 0.302/0.000**. Here the state component is the only one that is exactly zero on the equivalent variant and
clearly non-zero on the changed one.

**Baseline comparison.** `M_EX` ranks this set *wrongly* (0.218 < 0.563). Recomputing from the frozen weights
(`V10_MODELS_FROZEN.json`, model `EX`): `coverage_size` is 0.875 for *both* variants (dead code moves coverage
identically, so that term cancels), `exception_fraction` is 0 for both, and the edit term is ≈0 (weight +0.003). The
difference is therefore carried by `call_count` (0.952 for the CHANGED variant, 0 for the EQUIVALENT one), whose
standardised weight is **negative** (−0.122): the more the call count differs, the *lower* `M_EX`. The combined
baseline thus orders this set wrongly because of a negatively-weighted correlated feature fitted on v9c train, not
because the mutation was undetectable from execution statistics (`call_count` 125 → 145 is a real signal). This is a
property of the fitted baseline, not an evaluation defect; the baseline is retained unchanged.

**Why this is informative.** It is a clean illustration of *why edit size and coverage mislead* under heavy,
behaviour-preserving decoration, and of what the state component adds: it ignores dead code and responds to the mutation.

## Case 2 — Correct identification of equivalence under the protocol (median pool member, pool = 10)

Pool rule: EQUIVALENT pairs with edit ≥ 11 whose SBG V5 and all three execution statistics are exactly zero.
(Only 10 of the 72 EQUIVALENT pairs with edit ≥ 11 satisfy it; 13.9 % of those 72 have SBG V5 exactly 0 — the
rest, including all SP-3 dead-code pairs, have small non-zero scores. **This case is therefore not representative.**)

**Source change (SP-1 rename, edit 14):**

```diff
-    def _dfs(node: str) -> bool:
-        color[node] = 1
+    def _dfs(vertex: str) -> bool:
+        color[vertex] = 1
 ...
-    for node in sorted(all_nodes, key=str):
-        if color[node] == 0:
-            if _dfs(node):
+    for vertex in sorted(all_nodes, key=str):
+        if color[vertex] == 0:
+            if _dfs(vertex):
```

**Trace evidence.** 180 calls → 180, 24 transitions → 24, 2485 events → 2485, 0 transitions only on either side, 0
frequency differences. Edit size is 14 (non-trivial), yet the observed behaviour is *identical under the protocol's
55 traces*. SBG V5 = 0.000, and every execution statistic is 0.

**Matched CHANGED partner.** A single-token SC-2 operator flip (`color[node] == 0` → `color[vertex] != 0`) has the **same
edit size (14)** — so edit size cannot separate the pair at all (M_E equal for both) — and collapses the traversal:
calls 180 → 55, coverage 25 → 13, 24 → 12 transitions, SBG V5 = 0.524.

**Caveat.** "Equivalent" means equal under the oracle's inputs and the observation protocol; SBG scoring 0.000 here does
not prove semantic equivalence.

## Case 3 — A real failure: a behaviour change SBG cannot see (first SC-6 member, pool = 18)

Pool rule: CHANGED pairs for which SBG V5 and all execution statistics are exactly 0. Of 18 such pairs, **17 are SC-6
(return-value mutation) and 1 is SC-2**; the case is the first SC-6 pair by `pair_id`.

**Source change (the entire behavioural edit, edit size 4 including the SP-2 rename):**

```diff
-def kth_smallest(nums: list, k: int) -> int:
+def fn_kth_smallest(nums: list, k: int) -> int:        # SP-2: rename (behaviour-preserving)
 ...
-    return work[target]
+    return not work[target]                             # SC-6: changes the returned value
```

**Trace evidence.** Base and variant: 150 calls, 25 covered lines, 1665 events, 31 transitions, 0 differing
transitions, 0 frequency differences, 0 exceptions. The variants produce *byte-identical trace summaries*; the oracle,
which compares outputs, labels the pair CHANGED.

**Why it is invisible (verified, not assumed).** The edit alters only the value that flows out of the final `return`
statement. Control flow, call counts, covered lines and the abstract *local-variable* state sequence are unchanged, and
the representation by design never reads return values (SAFEGUARD-2, `state_transition_genome.py` docstring; the
tracer's per-event snapshot holds `f_locals` only). Because the oracle compares outputs and SBG deliberately does
not, this is an **observation-protocol blind spot**, not a bug in the scoring.

**Scale of the failure (V10, frozen).** SBG V5 is exactly 0 on **73.9 %** of CHANGED SC-6 pairs
(`V10_INDEPENDENT_EVALUATION.json`, `changed_zero_rate_by_sc_family`); SC-6 matched-set concordance: SBG V5 **0.50** vs
`M_EX` 1.00 vs edit 1.00 (23 sets, 18 programs; exploratory subgroup, `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`); the `M_EX` and edit concordance of 1.00 reflects that in SC-6 sets the CHANGED variant has the larger edit on average, 7.7 vs 5.7 tokens, while trace statistics are mostly zero for both, so it should not be read as behavioural detection).
In the 26 % of SC-6 pairs where SBG is non-zero, the mutated return value presumably altered downstream control flow
(not verified pair by pair).
All three execution statistics are also zero in 73.9 % of SC-6 CHANGED pairs (non-zero in 26.1 %), so the baseline shares the blind spot
(it is derived from the same traces); the `M_EX` ordering in the case above (−0.5386 vs −0.5396) is an edit-size
artefact, not an observation of behaviour.

**Implication.** Anything that changes a result without changing its execution path — arithmetic on a returned value,
wrong constant, swapped returned field — is outside what this representation can ever detect. A fixed-input differential
comparison of *outputs* would catch it; SBG-style trace comparison cannot. Any manuscript use case must therefore
position SBG as a *trace-level* signal complementary to output comparison, not as a replacement.

## Case 4 — Disagreement between SBG and the combined baseline

Selection rule: matched sets where adding `sbg_v5` to `M_EX` flips the outcome. In V10 there are **11 sets that
improve and 11 that worsen** (plus 3 half-credit improvements), so the pools are symmetric (see
`INCREMENTAL_CONTRIBUTION_ANALYSIS.md`). The two median members are shown *together* so the reader does not see only
the favourable one.

### 4a — Adding SBG makes the combined model wrong (`ds_ranked_set__sc5+sp2_s1`)

SC-5 inverts a guard (`if not valid or … :` → `if not (not valid or …):`). Calls 150 → 170, exceptions in 35 of 55
traces (0 in base), 31 → 38 transitions with 7 new error-path transitions (e.g.
`(1, NORMAL, error_transition, EXCEPTION_STATE)` × 70, `(0, EXCEPTION_STATE, error_recovery, NORMAL)` × 35).
SBG V5 = 0.313 vs 0.000: **SBG alone ranks the set correctly.** `M_EX` also ranks it correctly (0.890 vs −0.540,
driven by `exception_fraction` = 0.389). The combined model `M_EX+V5` ranks it *wrongly* (−1.062 vs −0.689): the frozen
weights give `sbg_v5` +1.259 but `call_count` −0.883 and `call_count` is 0.952 for this pair, so the negative
`call_count` term outweighs the SBG term. The failure belongs to the fitted combiner (correlated, opposite-signed
coefficients that were fitted on a different distribution), not to either feature family.

### 4b — Adding SBG fixes the combined model (`ds_min_heap_array__sc11+sp3_s2`)

SC-11 replaces `isinstance(arr, list)` by `isinstance(bool, list)`, so the function takes its early-exit branch. Calls
680 → 55, coverage 28 → 6, **25 → 0 transitions** (all 25 base transitions are missing in the variant; e.g.
`(1, ABSENT, state_creation, POSITIVE)` × 2245). SBG state = 1.000, V5 = 0.701. `M_EX` is wrong (0.302 < 0.622) for the
same reason as in Case 1: `call_count` is 0.998 (CHANGED) vs 0 (EQUIVALENT) and carries a negative weight (−0.122),
contributing ≈ −0.31 vs ≈ +0.05, which outweighs the coverage term (0.957 vs 0.923). `M_EX+V5` is right
(2.058 vs 0.317) because the +1.259 weight on `sbg_v5` dominates.

**What Case 4 shows.** Adding SBG to the execution statistics changes outcomes in both directions with similar frequency
(11 improved, 11 worsened; 260 stay correct, 34 stay wrong on 319 sets), which is the matched-set view of the formal
H4 null (+0.006 AUROC, 95 % CI [−0.069, +0.068]). The cases show *mechanisms* by which individual rankings change
(negative-weight `call_count`; dead-code-inflated `coverage_size`), they do not establish value beyond the baseline.

---

## Component-level evidence (what each part encodes, and what is shown)

| Component | Encodes | Intended failure mode | Evidence available in frozen artifacts | Stand-alone evidence of usefulness |
|---|---|---|---|---|
| V3 call-level | call-transition bigrams, hot-path hash, exception set/rate, coverage size, depth | rename-invariant control-flow change | V9c-val AUROC 0.740; E+V3 +0.096 over edit | Yes (V9c-val) |
| Temporal | ordering/timing of events | order-only changes | V9c-val AUROC 0.619; E+temporal +0.042 (borderline) | Weak |
| State transition | `(func_idx, pre, event, post)` multiset over abstract value states | value-flow changes with unchanged calls | V9c-val AUROC 0.762; E+state +0.130. V10: **state alone 0.917 [0.893, 0.938] > V5 0.897** | Strongest single component |

* The component AUROCs come from `V9_VAL_EVALUATION.json` and `V10_INDEPENDENT_EVALUATION.json` (frozen). In V10 the
  state component alone is higher than the frozen V5 composite; V5's weights (0.50/0.25/0.25) were fixed before V10 and
  are **not** changed. This is reported descriptively; it is not a claim that V5 should be replaced.
* **What cannot be isolated with current data:** the contribution of each component *beyond* the others, and what is
  lost when a component is absent (no leave-one-component-out ablation was frozen; running one would be an
  exploratory post-hoc analysis on V10 and was not done, because it cannot change the manuscript's central claim).
* Case 1 shows state non-zero where V3/temporal are small; Cases 2/4b show V3, temporal and state moving together;
  Case 3 shows all components zero. No case isolates temporal.

## Blind spots (all backed by cases or frozen statistics)

1. **Output-only changes** (Case 3): SC-6 undetected in 73.9 % of cases.
2. **Rename + extract refactorings** produce false-positive risk: SP-8 equivalents have non-zero SBG scores (median 0.42),
   SP-8 concordance SBG 0.64 vs `M_EX` 0.89; SP-2 CHANGED pairs score exactly 0 in 32 % of cases
   (`INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`, exploratory).
3. **Inputs are fixed and synthesised** (11 inputs × 5 runs): unexercised mutants are invisible by construction.
4. **Python-only tracer** (`sys.settrace`): no cross-language claim follows (see `COBOL_EVALUATION_REPORT.md`).

## Proposed manuscript figures / tables

* **Fig. A** — side-by-side state-transition multisets for Case 1 (CHANGED vs EQUIVALENT), showing the single removed
  `(1,ZERO,state_mutation,POSITIVE)` transition.
* **Fig. B** — Case 2 pair: identical 26-token vs 14-token edits, one trace-identical, one collapsed.
* **Table C** — the summary table above, including Case 3 *and* Case 4a (so failures are not hidden).
* **Table D** — SC-/SP-family concordance (SBG vs `M_EX` vs edit) from `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`,
  labelled exploratory, with set counts.
* **Table E** — component AUROCs (V9c-val and V10).

## Limitations of this analysis

* Five pools with deterministic median selection give an illustration, not a sample: no statement about typical cases
  beyond the pool sizes given above should be inferred.
* All cases come from the same generator family as development (V10 is a held-out split, not independent software).
* Only one example per category was traced; the SC-6 failure is supported by a family-level statistic (73.9 %),
  the others only by the single case.

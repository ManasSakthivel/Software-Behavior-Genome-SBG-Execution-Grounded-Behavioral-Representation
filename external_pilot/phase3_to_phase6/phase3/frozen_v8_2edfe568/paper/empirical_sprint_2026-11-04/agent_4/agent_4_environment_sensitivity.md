# Agent 4: Python version and environment sensitivity of SBG trace features

Repo: `SBG`, branch `remediation/sbg-v4`, HEAD `93ef3f38b840fc1e2a16a478b27bc9a2fb2b2146`, tree `d778de242372d8a25a9fc9b701ded11280bdee29`.
Date: 2026-11-04. Host: macOS arm64.
Interpreters used: CPython 3.9.6 (`venvs/py39`), 3.13.5 (`venvs/py313`), and for boundary localisation only 3.11.15 (Homebrew), 3.12.10 (pyenv) and 3.14.5 (Homebrew).

Everything labelled **EXPLORATORY** is a micro-diagnostic. It is not a re-evaluation. V8, V9c and V10 were not rescored, rerun or re-extracted.

## 0. Evidence protection

- No repo file was modified. `git status` after the work shows only the four untracked `artifacts/final/*_v8*` files that were already untracked in `_baseline/status_before.txt`, plus `paper/`.
- `experiments/final/python_version_sensitivity.py` was read but never executed.
- All runs used a `git archive HEAD | tar -x` copy under this directory.
- Before running I confirmed from the code that `regression_evaluation.py` and `hard_negative_evaluation.py` write only to `REPO_ROOT/artifacts/final/…`, where `REPO_ROOT` is the copy. I also confirmed `SandboxRunner` and the genome modules perform no file writes.
- The copies were deleted afterwards, so `agent_4/` is about 1 MB. `PYTHONDONTWRITEBYTECODE=1` was set on every run.
- No make targets were used.

## 1. What was actually measured

### 1.1 The stored artifact

`artifacts/final/PYTHON_VERSION_SENSITIVITY.json` (sha256 `c0334be6…`):

| | HARD_NEGATIVE_V5 | REGRESSION_V5 |
|---|---|---|
| numeric fields under `distances` | 120 | 75 |
| fields that changed | 30 | 4 |
| max abs change | 0.119626 | **0.408546** |
| `reported_values_changed` | `[]` | `[]` |

The generator's `_walk` only descends into keys present in both runs. It then selects every numeric leaf whose path contains `"distances"`. The reported maximum is therefore the largest change in **any** of the five fields per pair: `sbg_v5`, `sbg_v3`, `temporal`, `state`, `exception_component`. It is not a change in the headline `sbg_v5` distance.

The programs are:

- **15 regression bug/fix function pairs** (`benchmark/v5/regression/regression_pairs.py`). These are toy functions with 2–3 trigger inputs each.
- **12 hard-negative pairs**. They are scored under two input regimes, `canonical` (the 11 protocol inputs) and `declared`, so there are 24 rows. 24 rows × 5 fields = 120.
- Total: 39 scored rows and 195 distance fields. The fields are mostly zero, because many pairs are structurally identical.
- **No corpus program and no V6/V7/V8/V9c/V10 pair was in the sensitivity study.**

The experiment is `tracer → SandboxRunner(n_runs=5, max_events=5000) → V3 genome + temporal + state → V5 = 0.5·V3 + 0.25·temporal + 0.25·state`.

The stored artifact compares 3.9.6 against 3.13.15. The raw per-version distances are **not** in the sensitivity JSON. Only the summary counts are stored there.

The raw values of the 3.13 side are in the committed `REGRESSION_V5_RESULTS.json` and `HARD_NEGATIVE_V5_RESULTS.json`. There is no committed 3.9 raw output, so the per-version distances and rankings can't be recovered from stored data alone. I regenerated them (§2) and reproduced the stored summary exactly:

| | HARD_NEGATIVE | REGRESSION |
|---|---|---|
| distance values | 120 | 75 |
| changed (stored / my 3.9.6 vs 3.13.5) | 30 / 30 | 4 / 4 |
| max abs change (stored / mine) | 0.119626 / 0.119626 | 0.408546 / 0.408546 |

`outputs/replicate_sensitivity_report.txt` re-derives these numbers by importing the repo's own `_walk` from the copy without calling `main()`. It prints `MATCH_STORED` for both artifacts.

### 1.2 What the 0.41 refers to

It is the **`state` component** of pair **REG_09** (`mutation_during_iteration`), at 0.4891 on 3.9.6 versus 0.0805 on 3.13.5. The same pair moves the other fields as follows:

| field | 3.13.5 | 3.9.6 | abs shift |
|---|---|---|---|
| `temporal` | 0.0000 | 0.3500 | 0.3500 |
| `sbg_v3` | 0.1530 | 0.3780 | 0.2250 |
| **`sbg_v5` (headline)** | 0.0966 | 0.3988 | **0.3021** |

The four changed fields in the regression experiment are all REG_09. The other 14 regression pairs have identical distances on both interpreters.

`docs/current/PYTHON_VERSIONS.md` says "distance values change … largest observed change 0.41". That is literally true, but it is the max over five fields on one pair. For the headline score, the maximum shift is 0.30 (REG_09) in the regression set and 0.088 (hard-negative `pair_05`, canonical regime) in the hard-negative set. Both are single pairs.

### 1.3 Interpreter versions and the 3.13.15 vs 3.13.5 discrepancy

- The artifact says 3.13.15. `requirements-lock.txt`, `docs/current/REPRODUCTION.md` and `docs/current/PYTHON_VERSIONS.md` also say the committed artifacts came from "CPython 3.13.15".
- `FREEZE_V8.json` says "CPython 3.13.5 (venvs/py313)" and `FREEZE_V10.json` says `"python": "3.13.5"`. The audit also ran the test suite on 3.13.5.
- On 3.13.5, with `PYTHONHASHSEED` of 0, 1 or 7, `REGRESSION_V5_RESULTS.json` is **byte-identical** to the committed file (sha256 `7561b35c…`). The `HARD_NEGATIVE` output is byte-identical except for one string field, `threshold_provenance`, discussed in §6.
- **I cannot establish** which interpreter produced the committed `PYTHON_VERSION_SENSITIVITY.json`, or whether a 3.13.15 build was ever used. The text in the repo is not supported by any recorded manifest, and no experiment here distinguishes 3.13.5 from 3.13.15. What I can say is that 3.13.5 gives bit-identical numbers for this suite.
- `.python-version` is `3.13`, with no patch level. `FINAL_REPRODUCIBILITY_MANIFEST.json` records `python_version_required: ">=3.9"` and no actual interpreter version.

## 2. What I ran (all EXPLORATORY, all on copies)

`scripts/run_full_evals.sh` runs both fast experiments on a fresh copy per interpreter and seed. `scripts/compare_all.py` then compares the outputs. 195 distance fields were compared per run.

| comparison | changed fields | max abs | Spearman(sbg_v5, 39 rows) | sbg_v5 decisions flipped at τ=0.08 |
|---|---|---|---|---|
| 3.13.5 vs 3.13.5 (rerun) | 0 | 0 | 1.0 | 0 |
| 3.13.5, seed 0 vs 1 vs 7 | 0 | 0 | 1.0 | 0 |
| 3.9.6, seed 0 vs 1 | 0 | 0 | 1.0 | 0 |
| **3.9.6 vs 3.13.5** | **34** | **0.4085** | **0.968** | **0** |
| 3.9.6 vs 3.11.15 | 4 | 0.0104 | 0.980 | 0 |
| 3.11.15 vs 3.12.10 | 30 | 0.4085 | 0.989 | 0 |
| **3.12.10 vs 3.13.5** | **0** | 0 | 1.0 | 0 |
| 3.14.5 vs 3.13.5 | 0 | 0 | 1.0 | 0 |

Note that 34 = 30 (hard-negative) + 4 (regression), the two stored per-experiment counts summed.

Within an interpreter and across `PYTHONHASHSEED` values, these two experiments are fully deterministic. The cross-version shift is real and reproducible.

The interpreter boundaries are exact:

- **3.9 → 3.11 changes 4 fields**. All four are in `pair_07_dead_code_insertion`, `sbg_v3` and `sbg_v5`, in both regimes. Max shift is 0.0104.
- **3.11 → 3.12 changes 30 fields**. This includes all of REG_09's shift.
- **3.12, 3.13 and 3.14 are bit-identical** to each other on this suite.

So, on this suite, PEP 667 (the 3.13 `f_locals` change) has no measurable effect. The `ci.yml` comment says 3.13 is included "because the tracer reads frame.f_locals on every event, and PEP 667 changed what that returns in 3.13 -- a difference that can move trace-derived features". On 3.12 vs 3.13 this suite shows no such movement. `PYTHON_VERSION_SENSITIVITY.py` also attributes the shift in part to PEP 667. The data here does not support that attribution for these experiments.

## 3. Which families are environment-sensitive

### 3.1 By component (stored data + my regenerated raw outputs)

Changed fields out of 39 rows per component, 3.9.6 vs 3.13.5:

| component | rows changed | max abs shift |
|---|---|---|
| `state` | 9 | 0.4085 |
| `temporal` | 6 | 0.3500 |
| `sbg_v3` | 6 | 0.2250 |
| `sbg_v5` (composite) | 13 | 0.3021 |
| `exception_component` | **0** | 0 |

The ordering is consistent with how the features are built:

- **State** is a frequency-weighted Jaccard on `(func_idx, pre_abstract, event_kind, post_abstract)` tuples. These are built from consecutive events in the trace and local-variable snapshots. Any change in event adjacency, frame structure, or which variables are in `f_locals` changes the tuples. A single extra frame, such as `<listcomp>`, adds variables like `.0` and call/return event pairs.
- **Temporal** uses call trigrams, causal precedence sets and loop run-length profiles over the event sequence, so it depends on the call sequence.
- **V3** uses coverage size, call bigrams and call frequency, depth, and the exception components. The extra `<listcomp>` frame appears as an extra function index, extra call bigrams, depth+1 and different frequencies.
- **Exception component**: nothing moved. But only 4 of the 39 rows (3 regression, 1 hard-negative declared) have a non-zero exception component. Absence of movement is weak evidence here (see §7).

The per-component ordering is from stored data. The mechanisms below are from micro-diagnostics.

### 3.2 Mechanisms confirmed by micro-diagnostics (EXPLORATORY)

All micro-diagnostics are small toy programs from the existing hard-negative and regression sets, or self-contained toys, traced with the repo's `Tracer` imported from the copy, with `PYTHONHASHSEED=0`. Outputs are in `outputs/micro_*`.

**M1. PEP 709 comprehension inlining (3.12) removes a `<listcomp>` frame.** This is the dominant mechanism for REG_09 and for the largest hard-negative shifts.
- 3.9 and 3.11 emit an extra frame for each list, set or dict comprehension: `call <listcomp>` … `return <listcomp>`, with the locals `.0 = <enumerate object at 0x…>` and the loop variables in that frame.
- 3.12, 3.13 and 3.14 inline it into the enclosing function. There is no `<listcomp>` call event, and the loop variables appear in the enclosing function's `f_locals`.
- Concrete effects of `[x for … ]` in the micro-diagnostic:

| case | n_events 3.9 / 3.11 / 3.12 / 3.13 | difference |
|---|---|---|
| REG_03 buggy and fixed | 13 / 13 / 10 / 10 | −3 per trace, from `call`, `return` and one `line` |
| REG_09 fixed | 12 / 12 / 9 / 9 | −3 |
| REG_09 buggy (no comprehension) | 14 / 14 / 14 / 14 | 0 |
| `pair_04` base and variant | 16 / 16 / 13 / 13 | −3 (both sides) |
| `pair_03` base | 32 / 32 / 23 / 23 | −9 (3 `<listcomp>` frames) |

- REG_09 compares a buggy version that has no comprehension against a fixed version that does. The fixed side loses a frame on 3.12+, but the buggy side does not, so the **asymmetry** between the two sides changes. That is why REG_09 moves a lot (0.40 → 0.10) while REG_03, which has a comprehension on **both** sides, keeps the same distance even though its event counts change (95 → 125, both sides).
- This is the mechanism for the headline "0.41" shift.

**M2. 3.11+ emits line events for constant-condition control flow that 3.9 does not.**
- Self-contained toy (`outputs/micro_constfold.txt`) with `if False:`, `if 0:`, `if True:` and `while True:`:
  - 3.9.6 line events: `[7, 9, 10, 9, 10, 9, 10, 11, 12]`. There are no events for lines 2, 4 or 6 (the constant `if`s) and none for line 8 (`while True:`).
  - 3.11, 3.12, 3.13, 3.14: `[2, 4, 6, 7, 8, 9, 10, 8, 9, 10, 8, 9, 10, 11, 12]`.
- Effect on `sort_heapsort`: `_sift_down` has `while True:`. At line 31 there are 0 line events on 3.9 versus 22 on 3.13 for one 8-element input. This is the full explanation of the documented 8771 (3.13) vs 8024 (3.9) event counts for `sort_heapsort`. 3.11, 3.12, 3.13 and 3.14 all give 22 line events at line 31 and 8771 events overall.
- Effect on `pair_07_dead_code_insertion`, which is the "equivalent" pair with `if False:` dead code:
  - 3.9.6 distance is exactly 0.0, with coverage lines `[8, 9, 16, 18, …]`.
  - 3.11+ distance is 0.0052 (canonical) or 0.005 (declared). It covers line 11 (`if False:`) as an extra covered line.
  - So on 3.11+ the dead-code semantic-preserving transformation is **visible** to the tracer, and on 3.9 it is invisible.
- This is the most important finding for the benchmark. SP-3 (dead code insertion) variants will have a different baseline distance depending on interpreter. This 3.9→3.11 difference is separate from, and smaller than, the 3.12 comprehension difference. It explains the 4 fields that moved between 3.9.6 and 3.11.15.

**M3. Hash seed and hash algorithm.**
- CPython 3.9 uses SipHash-2-4 for `str` hashing. 3.11, 3.13 and 3.14 use SipHash-1-3 (`sys.hash_info.algorithm`). With the same `PYTHONHASHSEED`, set-of-string iteration order is therefore different between 3.9 and 3.11+. See `outputs/hash_probe.txt`: `list({'x','y','z','w','abc','def'})` gives `['x','def','y','z','w','abc']` on 3.9.6 and `['y','abc','x','def','z','w']` on 3.11, 3.13 and 3.14.
- `graph_connected_components` (`output_free_v6` and `output_free_v7`, the stored `hashseed_sensitivity.json` program):

| seed | 3.13.5 n_events | 3.9.6 n_events | 3.11.15 | 3.14.5 |
|---|---|---|---|---|
| 0 | 2065 | 2055 | 2065 | 2065 |
| 1 | 2065 | 2075 | 2065 | 2065 |
| 5 | 2075 | 2065 | 2075 | 2075 |

- This reproduces the stored `hashseed_sensitivity.json` values for 3.13 (2065, 2065, 2075). `PYTHONHASHSEED=0` is deterministic **within** an interpreter but does **not** make 3.9 and 3.13 agree.
- For the toy suite (regression plus hard-negative), none of the programs iterate string sets, so seeds 0, 1 and 7 produce byte-identical output on both interpreters.

**M4. Other mechanisms examined and not observed to matter:**
- `repr` of objects with addresses: 3.9 listcomp frames show `.0 = <enumerate object at 0x…>`. `_repr_to_abstract` maps any `<…` string to `NON_NULL`, so the address is abstracted away. No address-dependent output was observed.
- PEP 667 `f_locals`: no effect on the tested suite (3.12 ≡ 3.13 bit-for-bit).
- `sort_quicksort`, `math_fibonacci` and `str_run_length_encode` (`output_free_v6` and `output_free_v7`): identical event counts on 3.9 and 3.13 (7999, 220, 1620).

### 3.3 What is not established

- Exception-event semantics: the toy programs exercised `exception` events only in a TypeError path, with identical counts apart from the `<listcomp>` frame. I did not test generators, `StopIteration` events, `finally`/`with` bytecode changes (3.11+ zero-cost exceptions), or async. No evidence of a difference either way.
- Tracer caps: `max_events=5000` per trace. If a program gets within a few thousand events of the cap, the additional 3.11+ line events from M2 will make it truncate earlier. Stored `pairs_v8test_output_free_v8.jsonl` shows 0 truncated pairs among 956 evaluated, so the cap is not the issue for V8 test. The `base_truncated` field is absent in `pairs_v10_test_v6exp.jsonl`, so I cannot say for V10.
- Wall-clock timeouts (1 s per trace): not measured across versions.
- stdlib changes: the `external_bugsinpy.py` stdlib fix is mentioned in the docs, but I did not test it.
- `sys.monitoring` (3.12): the tracer uses `sys.settrace`, which remains supported. I did not test a deprecation path.

## 4. Does the shift affect rankings or just magnitudes?

Answer based on the 39-row toy suite only: **rankings largely survive, but not entirely**. All of the following are EXPLORATORY and based on tiny n.

Spearman correlation of `sbg_v5` across the 39 rows (3.9.6 vs 3.13.5) is 0.968. Per-set, from `outputs/comparison_summary.json`:

| set | n | Spearman sbg_v5 | Spearman state | Spearman temporal |
|---|---|---|---|---|
| regression | 15 | 0.943 | 0.920 | 0.763 |
| hard-neg canonical | 12 | 0.957 | 0.988 | 1.0 |
| hard-neg declared | 12 | 0.957 | 1.0 | 1.0 |

Decisions at τ* = 0.08 for `sbg_v5`: 0 flipped. `temporal` alone flips 1 row (REG_09, 0.0 → 0.35).

Rank orderings that change (`outputs/rank_detail.txt`):

- **Regression**: REG_09 goes from 6th of 9 non-zero (3.13) to 1st (3.9). The other eight keep their relative order.
- **Hard-negative**: `pair_07` (an *equivalent* pair, dead code) is above `pair_01` and `pair_06` (both *changed*) on 3.13 and below them on 3.9, in both regimes. This is a ranking change between a negative and positives, caused by M2. The ordering of `pair_04` vs `pair_03` and the others is unchanged.
- AUROC on the 12 hard-negative pairs (7 CHANGED, 5 EQUIVALENT, `sbg_v5`):

| regime | 3.13.5 | 3.9.6 | |
|---|---|---|---|
| canonical | 0.4286 | 0.4857 | 3.9 is +0.057 |
| declared | 0.4000 | 0.4571 | 3.9 is +0.057 |

With n = 12 and 35 positive-negative pairs, one swapped pair moves AUROC by 1/35 = 0.029, so these differences correspond to two swapped pairs. Both AUROCs are below 0.5 on both interpreters. The regression set has only positive labels, so AUROC is undefined.

Interpretation: on the pairs tested, the cross-version shift moves magnitudes by up to 0.3 on isolated pairs, leaves the rank structure mostly intact (ρ ≈ 0.96–0.99), and changes discrimination only by a couple of adjacent swaps. **This cannot be extrapolated to V8, V9c or V10 AUROC.** Those use 4,000+ pairs from the 122-program corpus, with `output_free` protocols, which the sensitivity study never covered.

### 4.1 Exposure of the real datasets (static AST only, nothing executed or scored)

`scripts/static_exposure_variants.py` and `scripts/static_comprehension_exposure.py` count constructs. They do not predict score shifts.

| set | pairs | pairs whose variant and base differ in count of constant-condition `if`/`while` | pairs with a list/set/dict comprehension on either side | pairs where comprehension count differs |
|---|---|---|---|---|
| v8 train | 2057 | 146 (all SP-3) | 936 | 43 |
| v8 val | 461 | 33 | 201 | 6 |
| v8 dev | 597 | 42 | 141 | 3 |
| v8 test | 1130 | 78 | 449 | 18 |
| v10 test | 644 | 110 | 368 | 28 |

Corpus level: 36 of 64 base programs and 52 of 121 fresh programs contain at least one list/set/dict comprehension. 6 corpus programs have `while True:`.

Consequences:

- **M1 exposure is large**: roughly 40% of v8 test pairs and 57% of v10 test pairs have a comprehension on at least one side. Those traces differ between 3.11 and 3.12 in event counts and state tuples. Most pairs where both sides have the same comprehension would have shifted distances only mildly, as REG_03 shows. The ~2–3% of pairs where the comprehension count differs between base and variant are the REG_09 pattern.
- **M2 exposure**: SP-3 variants exist in every split. For v8 test, 78 of 1130 pairs (6.9%) have a different constant-condition count.
- **Stored-score observation (read-only, no rescoring; `outputs/stored_sp3_zero_score_check.txt`)**: in the stored 3.13.5 scores for V8 test, all 66 SP-3 evaluated pairs (label 0) have `sbg_v5` > 0, and in V10 test all 55 SP-3 equivalent pairs have `sbg_v5` > 0. In contrast, 247 of 343 other V8 equivalent pairs score exactly 0. This is *consistent with* M2 making dead code visible on 3.11+, but it is **not shown** to be caused by M2. SP-3 dead code also adds covered lines when `if False:` is visible, and that is exactly the M2 effect. I did not run any SP-3 pair under 3.9 because that would be a rescoring of V8/V10 data. Whether SP-3 would be 0 on 3.9 across the corpus is **untested**, but the one toy pair (`pair_07`) says it would be 0.0.

## 5. Is environment normalisation justified?

**Not as a post-hoc correction of results.** There is no principled mapping from a 3.9 trace to a 3.13 trace.

- M1 and M2 change which events exist, not just their magnitude. A 3.9 trace has frames and events that 3.13 does not, and vice versa.
- The effect is pair-specific and depends on the asymmetry between base and variant (REG_03 versus REG_09). A single scalar shift can't correct it.
- Applying a correction to published numbers after observing them would be an undisclosed post-hoc analysis.

**Justified: a canonical-interpreter policy plus recording the interpreter.**

1. The canonical interpreter is CPython 3.13 and the claim "results are interpreter-specific" should be explicit. My data support one stronger statement: **3.12, 3.13 and 3.14 are bit-identical on this suite**. That would justify a "3.12+" equivalence class for the fast experiments only, not for the corpus-level results.
2. Treat 3.9 and 3.11 as "code runs", not as "artifacts reproduce". This is what `PYTHON_VERSIONS.md` already says.
3. Re-introducing a 3.9 comparison as a result would need a new, preregistered sensitivity study on the corpus pairs.

## 6. Reproducibility policy recommendation

**R1. Pin the full interpreter and record it in every manifest.**
- Record `sys.version`, `sys.implementation`, `sys.hash_info.algorithm`, platform and `PYTHONHASHSEED` in every `FREEZE_*` / `*_MANIFEST` / result artifact. `FREEZE_V10.json` records `python: "3.13.5"` and the seed. `FINAL_REPRODUCIBILITY_MANIFEST.json` records neither.
- Resolve the 3.13.5 vs 3.13.15 discrepancy by choosing one value and stating it everywhere. The data here support 3.13.5 for the committed fast-experiment artifacts (byte-identical rerun). The frozen V8/V10 numbers were recorded as 3.13.5 by their own freeze files. I'd treat "3.13.15" in `requirements-lock.txt`, `REPRODUCTION.md` and `PYTHON_VERSIONS.md` as an unverified statement and correct or remove it rather than assert it. I did not edit them.
- The `3.13.15` string also appears in `STANFORD_GATE.json`, `THRESHOLD_FROZEN.json`, `BUGSINPY_output_free_v6/v7.json` and `FINAL_STANFORD_READINESS_REPORT.md`. Those need the same check.

**R2. Pin in a container or lockfile.**
- A Dockerfile or equivalent using an exact tag (for example `python:3.13.5-slim`) with `PYTHONHASHSEED=0`. There is none in the repo.
- Pin the OS/arch too. The audit notes `check_reproduction.py --strict` fails byte-exact on the Linux runner, so platform matters beyond Python version. I did not investigate the cause of that failure.

**R3. Always set `PYTHONHASHSEED=0`, but don't rely on it for cross-version equality.** M3 shows a different hash algorithm in 3.9. Cross-version comparisons on string-set programs differ even with the same seed.

**R4. CI matrix.**
- Keep the canonical leg as an exact patch version with `--strict`.
- The 3.9 leg checks "code runs and counts are unchanged" via `check_reproduction.py` without `--strict`, as already done. The audit says the 3.9 job fails at setup on the runner (no 3.9 on Ubuntu 26.04). That needs a fix such as a pinned container.
- Optionally add 3.12 and 3.14 as non-strict equivalence checks. They are cheap and my results say they match 3.13 on the fast suite.
- The CI comment about PEP 667 is not supported by this data and should say comprehension inlining (3.12) and line-event changes (3.11) instead.

**R5. How to report in a paper.**
- State: all results come from CPython 3.13.x on macOS arm64 with `PYTHONHASHSEED=0`; the tracer is `sys.settrace`-based; trace-derived distances are interpreter-version-specific.
- Report the sensitivity study with its real scope: 27 toy function pairs (15 regression plus 12 hard-negative, the latter in two input regimes). Include per-component maxima, and say the 0.41 is the `state` component of one pair (REG_09). The headline `sbg_v5` shift is up to 0.30 on that one pair and 0.088 on the worst hard-negative pair.
- State explicitly that **no corpus-scale cross-interpreter study was performed**, so the AUROC of V8/V9c/V10 is not shown to be interpreter-robust.
- Disclose M1 and M2 as known mechanisms, and that SP-3 dead-code equivalents are visible to the 3.11+ tracer.
- Fix the `threshold_provenance` mismatch before citing the hard-negative artifact. The committed `HARD_NEGATIVE_V5_RESULTS.json` says "median SBG distance of semantics-preserving dev pairs; fixed before these pairs were scored and not re-tuned here". The current script writes "inherited constant, not re-tuned in this script; no derivation artifact exists". The numbers are identical, only the text differs, and the code comment says the derivation is unverified. That difference is why my rerun of this artifact is not byte-identical to the committed one. I did not alter anything.

## 7. What cannot be established

1. Which interpreter produced the committed artifacts (3.13.5 or 3.13.15). 3.13.5 reproduces the fast-experiment artifacts bit-for-bit, but I can't exclude other 3.13.x.
2. The effect of interpreter version on V8, V9c or V10 AUROC, ranks or thresholds. Doing so would require rescoring, which was forbidden. The static exposure counts say the exposure is large, but not what the effect is.
3. Whether SP-3 pairs would score exactly 0 on 3.9 at corpus scale. Only one toy pair was tested.
4. A causal link between M2 and the all-non-zero SP-3 scores in the stored 3.13.5 data. The pattern is consistent, not shown.
5. The effect of exceptions, generators, `with`/`finally`, async and the stdlib on traces. Not tested.
6. The cause of the `check_reproduction.py --strict` failure on the Linux CI runner. Not investigated.
7. Whether `exception_component` is truly insensitive. 35 of 39 rows have a zero value, so absence of movement means little.
8. Wall-clock and timeout effects across versions.
9. The AUROC differences in §4 are two adjacent swaps on 12 pairs. They are not evidence of any systematic direction.
10. The claim "CI runs 3.9 and 3.13" is false according to the audit; I did not verify CI logs.

## 8. Input hashes (sha256, `outputs/input_sha256.txt`)

```
c0334be6c02661237d4fd437f588df2d73d8603ce1f336805189fd52d48f43a4  artifacts/final/PYTHON_VERSION_SENSITIVITY.json
e4f7efc11d2e6bf182569bae8373081eb37a3b2711e1bf5274f5810338af2571  artifacts/final/HARD_NEGATIVE_V5_RESULTS.json
7561b35cedada19a5baa29140511925bae780cf3369922050d46abac84377d12  artifacts/final/REGRESSION_V5_RESULTS.json
a406a4212ad00bb23f3a68e13eac4f51096da5d5a5e0809b1b57165768717470  experiments/final/python_version_sensitivity.py
2e26a9954660e1506898b2a44b52ace37bf78abe549248d9d14fb5573eba64e1  experiments/final/hard_negative_evaluation.py
25f16e9c44b88e62a24a9a8b7f1c092c1a6b0962fed3c3f42058218242bc8e0f  experiments/final/regression_evaluation.py
76676e91725142aac4314a52f005ea1494f43e3385ac42bd810a9fd7e4fced6f  sbg/extraction/dynamic/tracer.py
750ba4d15b9d6044fc2d8768e505b7d7530145b0d717ab23d8e5b6c459613ab8  docs/current/PYTHON_VERSIONS.md
d17b9f5d47e3fab5faa9c4c356ba186e927c4ea2df0489e07a4501d640fdd38e  artifacts/paper_evidence/raw/hashseed_sensitivity.json
0d191794afa3624e84b2a44c5b7ad559442260045f2ad7f57cf212b52ae7086c  artifacts/paper_evidence/raw/cold_start_probe.json
965a5279ee41a13a26f0f61fcf0dc0638a063829bcad8e540051be0ca6e64ae8  experiments/final/diagnose_hashseed.py
c25aba80f1521902486d3e31cd2e664282c0177039377d641c254d36377a883f  requirements-lock.txt
77e95252e9d27e3910c06c3b686c659ff7b8f70b3c03a8b6eda0f9fed0f55c3a  artifacts/final/FREEZE_V10.json
caf0a06b0adfabfd72929ca7b15b3f39f09974cc140755ef78120a2e98d33d0d  .github/workflows/ci.yml
```

Rerun output hashes are in `outputs/rerun_outputs_sha256.txt`. Key ones:

- 3.13.5, 3.12.10, 3.14.5 (and all 3.13.5 seeds): HN `8265cc3b…`, REG `7561b35c…`.
- 3.9.6 (seeds 0 and 1): HN `ddcda077…`, REG `9d1bf7bc…`.
- 3.11.15: HN `3ee86047…`, REG `9d1bf7bc…`.

## 9. Rerun commands

The scripts are in `scripts/`. Paths are absolute for this host.

```bash
# 1. Full fast-experiment reruns on copies (writes only under agent_4/; ~2-3 min). Never run the repo's own make targets.
cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/empirical_sprint_2026-11-04/agent_4
bash scripts/run_full_evals.sh      # needs the interpreters listed in the script; it creates copy/ and copy_<tag>/ and removes copy_<tag>/ after each run
python3 scripts/compare_all.py      # -> outputs/compare_all.txt, compare_all.json
python3 scripts/compare_versions.py # per-pair detail, needs outputs/py313 and outputs/py39
python3 scripts/pair_diffs.py       # 3.9 vs 3.11, 3.11 vs 3.13 pair lists
python3 scripts/replicate_sensitivity_report.py   # re-derives the stored report; needs copy/ present

# 2. Micro-diagnostics (EXPLORATORY; copy/ must exist)
bash scripts/run_micro_trace.sh                   # outputs/micro_trace_py{39,311,312,313}.json
bash scripts/run_micro_extract.sh                 # outputs/micro_extract.jsonl (5 corpus programs, seeds 0/1/5, 3.9 and 3.13)
P=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 $P/py313/bin/python scripts/micro_lines.py copy
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 $P/py313/bin/python scripts/micro_snap.py copy
PYTHONDONTWRITEBYTECODE=1 $P/py39/bin/python scripts/micro_constfold.py

# 3. Static exposure (no execution of corpus code)
python3 scripts/static_comprehension_exposure.py
python3 scripts/static_exposure_variants.py
```

Notes on provenance of the commands:

- The shell invocations were typed interactively on 2026-11-04. `run_full_evals.sh`, `run_micro_trace.sh` and `run_micro_extract.sh` are transcriptions of those commands and were run as files, apart from `run_full_evals.sh`, which I wrote last as a consolidated version of the per-tag calls I made by hand. It has not been executed as a single file.
- `copy/`, `copy_*/` and `scratch/` were deleted after use. Re-run step 1 first to regenerate `copy/` before steps 2 and 3.
- `outputs/` contains all the generated evidence.

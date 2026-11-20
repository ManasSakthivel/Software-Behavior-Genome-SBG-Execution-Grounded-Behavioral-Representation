# RESEARCH_STATUS (updated EOD 2026-10-29)

**SBG is NOT validated.** A single frozen v8 TEST evaluation now exists and does **not** support the pre-declared success
criterion: SBG V5 (AUROC 0.694) is clearly below the trivial reversed-edit-size baseline (0.876). Diagnostics are in
`DIAGNOSTIC_REPORT.md`; all numbers trace to `V8_TEST_EVALUATION.json`, `FINAL_METRICS.json`, `BASELINE_COMPARISON.csv`,
`V8_COMPONENT_COMPARISON.json`, `DIAGNOSTIC_*.json`.

## A. Final verified metrics

### v8 TEST — CONFIRMATORY-BY-FREEZE, single run (`V8_TEST_EVALUATION.json`; frozen `evaluate_v8.py`)
22 programs, 956 valid pairs (547 CHANGED / 409 EQUIVALENT); 4 stale-variant programs (163 pairs) excluded a priori.
CIs: cluster bootstrap by base program, 2000 resamples, seed 42.

| Predictor | AUROC | 95 % CI | Δ(SBG V5 − predictor) [CI] |
|---|---|---|---|
| **edit_size_reversed** (shortcut) | **0.876** | [0.859, 0.892] | −0.182 [−0.220, −0.144] (Holm p = 0.006) |
| learned_m2 (secondary; v6-train weights) | 0.771 | [0.727, 0.812] | −0.078 [−0.105, −0.042] |
| learned_m1 (secondary) | 0.751 | [0.683, 0.807] | −0.057 |
| **sbg_v5 (primary)** | **0.694** | [0.659, 0.727] | — (permutation p = 0.0005; noise-floor p95 0.528) |
| coverage_size | 0.612 | [0.584, 0.639] | +0.082 [0.045, 0.119] |
| exception_fraction | 0.569 | [0.541, 0.600] | +0.124 [0.081, 0.168] |
| call_count | 0.494 | [0.443, 0.549] | +0.200 [0.150, 0.249] |
| static_token | 0.260 | [0.240, 0.281] | +0.433 |
| static_ast | 0.259 | [0.242, 0.277] | +0.434 |

* Edit-size-exact-stratified SBG V5: **0.776 [0.722, 0.825]** (19.4 % of cross-label pairs; edit size alone = 0.5 there). Edit 1–5 subset: SBG 0.749 vs reversed edit 0.657 (n = 695, 148 EQUIVALENT).
* Leave-one-program-out SBG range 0.686–0.701. Per-program SBG AUROC < reversed edit AUROC in every listed program.
* Operating point τ_v8 = 0.040511 (dev-derived): TPR 0.505 / FPR 0.147 on test. 40.6 % of test pairs score exactly 0.
* **Pre-declared verdict: NOT DEMONSTRATED** (stratified criterion met; beating best baseline not met).
* Component comparison (exploratory, `V8_COMPONENT_COMPARISON.json`): on both dev and test the state-only component `sbg_state` (test 0.751 [0.715, 0.787]) beats the composite V5 (Δ −0.057, CI excludes 0). This was observed after the test; it is a hypothesis, **not** a result to promote.

### Development (exploratory)
| Set | n pairs / programs | SBG V5 | reversed edit | note |
|---|---|---|---|---|
| v8 dev (frozen script, 1 stale prog. excluded) | 550 / 13 | 0.739 [0.694, 0.782] | 0.877 [0.854, 0.898] | τ_v8 derived here |
| v8 dev (all, original analysis) | 593 / 14 | 0.739 [0.698, 0.781] | 0.845 | |
| v6 dev (frozen artifact) | 345 / 9 | 0.667 [0.603, 0.745] | 0.957 | not byte-reproducible (46 diffs, explained) |
| v6 train | 1033 / 28 | 0.665 [0.599, 0.731] | 0.954 | in-sample for weights |
| v6 test (historical, OBSERVED not held-out) | 259 | 0.601 | 0.967 | |

### External (exploratory, pre-freeze; `DIAGNOSTIC_EXTERNAL.json`)
BugsInPy 0.410 [0.326, 0.494] (147 pairs, 39 bugs; 0.472 [0.38, 0.56] without SP-2; 0.429 after `re` cache purge). QuixBugs canonical 0.388 [0.285, 0.503] (152 pairs, 40 programs; 0.451 without SP-2); declared-input subset 0.702 [0.584, 0.817] (28 programs). **No transfer shown.**

## B. Confirmatory vs exploratory
* **Confirmatory-by-freeze:** v8 TEST only (weakened by a priori exclusion of 4 programs, two pre-scoring amendments, three stalled harness attempts, and v8 sharing generator design with dev).
* **Exploratory:** everything else — v6 train/dev/test, v8 dev (incl. τ_v8, weights M1/M2), external corpora, all diagnostics, component comparison.

## C. Claims SUPPORTED
1. On held-out v8 programs, SBG V5 separates CHANGED from EQUIVALENT variants above chance (0.694, CI excludes 0.5, perm. p ≈ 0.0005).
2. SBG V5 outperforms the dynamic and static baselines `exception_fraction`, `call_count`, `coverage_size`, `static_ast`, `static_token` on v8 test (paired CIs exclude 0).
3. Static AST/token distance is inverted (AUROC ≈ 0.26) because EQUIVALENT variants are edited more.
4. A trivial reversed-edit-size baseline outperforms SBG on every dataset including test (0.876 vs 0.694); the benchmark label is confounded with edit size by construction of transformation families.
5. Within exact edit-size strata SBG retains signal on v8 (0.776 test, 0.859 dev), above the label-shuffle noise floor; not shown on v6.
6. The v6 dev score drift is explained (hash-order nondeterminism + aliasing fix) and small (≤ 0.011 AUROC).
7. External real-bug results contain no scoring/label error, and are depressed by two identified harness artifacts; the corrected values are not distinguishable from chance.

## D. Claims NOT supported (do not make)
* "SBG is validated / state of the art / beats baselines" (it loses to reversed edit size on test).
* "SBG detects real bugs" or "transfers to real programs" (0.43–0.51 corrected; CIs include 0.5; inputs seldom expose real bugs).
* "Beyond-edit-size signal is established across datasets" (absent/inconclusive on v6; stratum covers 19 % of pairs, only small edits).
* "v6 results are confirmatory" or "v6 dev reproduces byte-for-byte".
* "sbg_state / learned models are the proposed method" (post-hoc, exploratory).
* Anything about large-edit behaviour: no CHANGED pairs exist with edit > 5 lines in v8.

## E. Limitations
Synthetic benchmark; label determined by transformation family; edit-size confound; 22 test programs from one author-curated pool; 4 programs excluded; stale-variant defect in committed v8 data (dataset left untouched, audited); tracer is wall-clock/event-cap dependent; harness stalls required a chunked scorer (equivalence verified on dev only); `re` cache global state; Java not run; no power analysis; no val-split scoring; Python 3.13.5 on one machine.

## F. Blocked / not done
`fit_weights.py test`, v8 val, Java, power analysis for v8, external re-score under a cleaned harness (would be a new experiment; `re`-purge variant is diagnostic only), Stanford gate remains 8/20 PASS (12 BLOCKED — mostly missing v6/v7-test and Java artifacts that this work deliberately did not create).

---
# Prior status (2026-10-28, pre-test) — retained for history; superseded where it conflicts with the above
# RESEARCH_STATUS: what the evidence supports (2026-10-28)

**SBG is NOT research-ready.** No held-out confirmatory evaluation exists. Everything below is
exploratory or development-set evidence. All numbers trace to `FINAL_METRICS.json`,
`BASELINE_COMPARISON.csv` and `ABLATIONS.json` (each lists source paths + SHA-256).

Primary set everywhere = VALID (evaluable pairs minus statically invalid/unobservable pairs).
CIs = cluster bootstrap by base program, 2000 resamples, seed 42.

## 1. Claims the evidence DOES support (as development-set / exploratory statements)

| # | Claim | Evidence | Strength |
|---|---|---|---|
| S1 | SBG V5 distance separates CHANGED from EQUIVALENT above chance on synthetic pairs | v6 train 0.665 [0.599, 0.731] (n=1033, 28 prog); v6 dev 0.667 [0.603, 0.745] (n=345, 9 prog); v8 dev 0.739 [0.698, 0.781] (n=593, 14 prog); label-shuffle noise floor ≈ 0.50–0.55 | Moderate; dev-type data only |
| S2 | On fresh v8 dev programs SBG V5 beats `exception_fraction` (Δ=+0.168, CI [0.122, 0.209]) and `call_count` (Δ=+0.194, CI [0.127, 0.262]) | `raw/recomputed_comparisons.json` | Exploratory (v8 dev, 14 programs, protocol not frozen) |
| S3 | SBG V5 beats `exception_fraction` on v6 train (Δ=+0.089, CI [0.029, 0.148]) | same | Exploratory |
| S4 | Static baselines (`static_ast`, `static_token`) are not competitive: AUROC 0.10–0.32 (below chance, inverted) on v6 train/dev/v8 dev, because the generator edits more lines in EQUIVALENT than in CHANGED variants | MAIN_EVALUATION_* | Descriptive |
| S5 | A dev-selected linear model on 9 execution features (M2) improves on V5 fixed weights | train 0.724 (in-sample), dev 0.713 (selection set), v8 dev 0.804 vs V5 0.739 (Δ V5−M2 = −0.064, CI [−0.096, −0.034]) | Exploratory; M2 never scored on a TEST split |

## 2. Findings that CONTRADICT or limit any positive claim (must be reported)

| # | Finding | Evidence |
|---|---|---|
| N1 | **Edit-size confound.** Reversed edit size alone beats SBG V5 on every run: 0.954 (v6 train), 0.957 (v6 dev), 0.845 (v8 dev); Δ(V5 − edit_size_reversed) = −0.289 / −0.290 / −0.106, all CIs exclude 0. Historical v6 test: 0.9667. The `max_names=1` redesign (v8) lowers but does not remove it | `raw/recomputed_comparisons.json`, `ABLATIONS.json` |
| N2 | Within the smallest edit-size stratum (0–2 changed lines, where most CHANGED pairs live) V5 AUROC is 0.62 (v6 train), 0.49 (v6 dev), 0.86 (v8 dev). Large strata contain almost no CHANGED pairs, so most strata cannot be evaluated | `ABLATIONS.json › edit_size_confound_control` |
| N3 | **External transfer is below chance**: BugsInPy 0.410 [0.326, 0.494] (147 pairs, 39 bugs); QuixBugs 0.388 (152 pairs, no CI in source). Both predate the protocol freeze | `BUGSINPY_output_free_v7.json`, `QUIXBUGS_output_free_v7.json` |
| N4 | On v6 dev, V5 does not significantly beat `exception_fraction` (Δ=+0.054, CI [−0.051, 0.177]); on the observed v6 test it is below it (0.601 vs 0.618) | MAIN_EVALUATION_* |
| N5 | Frozen τ\*=0.072905 gives TPR/FPR 0.558/0.180 on dev (by construction), 0.500/0.195 on v6 train, 0.515/0.104 on v8 dev (cross-protocol, diagnostic only) | `raw/tau_operating_points.json` |
| N6 | Large coverage loss: v6 test under output_free_v6 evaluated 259 of 488 pairs (7 of 13 programs). v7 dev 345/372 | MAIN_EVALUATION_* |

## 3. Failed or non-reproducing checks (accurate accounting)

1. **Frozen v6 dev scores do not reproduce under current code.** Re-scoring dev (same protocol, same dataset): 46/345 pair scores differ at committed HEAD `f15cb9a` (max |ΔSBG| 0.0167; programs `sort_quicksort`, `graph_connected_components`); with the uncommitted tracer edits 7 of those pairs also become non-evaluable and 39 scores differ (max 0.036). Derived τ changes 0.072905 → 0.072531 (J unchanged). The frozen artifact was **kept unmodified**. Cause not isolated (suspected: time-budget/event-cap dependent traces on non-terminating mutants).
2. **Pre-existing v8 dev artifacts were stale.** `pairs_dev_output_free_v8.jsonl` / `pairs_v8dev_output_free_v8.jsonl` were scored before `benchmark/datasets/v8` was regenerated (07:53); 181–186 of 593 scores differ from a re-score and `pairs_v8dev_*` has 598 rows (1 extra pair). They were **not used**; the v8 results use the fresh re-score `*_v8devrescore_*` (two consecutive re-scores matched exactly → deterministic).
3. **Training run (PID 36301) died** without a completion marker at 1000/1129 (an earlier run also stopped at 1000/1129). Cause unknown (process absent; no traceback). Recovered by resuming from the checkpoint (resume logic verified: 1000 unique, in-order, same protocol/dataset). The resumed run produced 1129 rows in dataset order.
4. **Resume limitation:** `run_main_evaluation.py` does not rebuild its programs cache on resume, so `programs_v6train_output_free_v7.json` lists 133 programs (those extracted in the resumed segment), not all 1157 distinct files. Pair-level evidence (`pairs_*`) is complete; the programs file is **partial by construction** and is not used for any count in the evidence package.
5. **C7 consistency exception list grew**: 19 train EQUIVALENT SP-2 pairs trace a renamed `test_*` driver (the known v6/v7 entry-policy defect, absent in v8). They were added to `KNOWN_HISTORICAL_DRIVER_TRACES` (test expects 30). They remain in the fit data (inside the 1033 valid train pairs).
6. Consistency check 10/10 and pytest 760 passed after these changes (`logs/`).
7. Gate: `STANFORD_GATE.json` = **8/20 PASS, 12 BLOCKED** (was 7/20). The one improvement is `scientific_integrity` (weights chosen before any test scoring). Gate logic was edited so "test scored" requires `WEIGHT_FITTING.json['test'] is not None` (previously `"test" in w`, which a freshly-fit file satisfied vacuously).

## 4. Outstanding blockers (not done today; do not assume they exist)

| Item | State |
|---|---|
| Held-out TEST evaluation under a frozen protocol | **Not run.** v6 test is observed (committed alongside dev results 5 days before the pre-registration commit); v8 test (26 programs, 1130 pairs) unscored |
| `FREEZE_V8.json`, `THRESHOLD_V8_FROZEN.json`, v8 pre-registration | **Absent.** Hence no τ\* for protocol v8 and no frozen v8 protocol |
| Weight models M1/M2 scored on any test split | **Never.** `WEIGHT_FITTING.json['test']` = null |
| Power analysis for v8 (`power_analysis.py`) | Not run |
| Java (QuixBugs Java) | Not run |
| CI for QuixBugs | Absent in source artifact |
| Root cause of external below-chance AUROC | Hypothesis (edit-size inversion) untested |
| Why frozen v6 dev scores drift under re-scoring | Not isolated |
| Fresh programs' provenance (`benchmark/corpus/fresh_programs`, 123 files, 100 used) | Authored in-repo; Jaccard ≤ 0.10 check is specified in `FRESH_PROGRAM_PROTOCOL.md`; verification status of that check not re-run today |

## 5. Wording guidance for the writer

* Say "development-set / exploratory"; never "held-out", "confirmatory" or "state of the art".
* Always report the reversed-edit-size baseline next to any SBG AUROC.
* Report external AUROC < 0.5 in the main results.
* v6 vs v8 are different datasets, protocols and program sets: do not pool or average across them.
* The v6 test numbers (0.601 under output_free_v6) come from a historical run on an observed split.

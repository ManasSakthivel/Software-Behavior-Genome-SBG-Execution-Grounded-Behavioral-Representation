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

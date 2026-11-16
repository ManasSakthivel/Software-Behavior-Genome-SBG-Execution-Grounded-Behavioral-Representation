# WP-C Experiment Registry (ablations + return-value analysis)

Session: WP-C (SBG A5 ablation and architectural analysis). Started 2026-11-14T15:13:43Z (`logs/START_UTC.txt`, marker `logs/.start_marker`).
This registry contains no publication recommendation. All numbers in `08A_ABLATION_RESULTS.md` and `08B_RETURN_VALUE_ARCHITECTURAL_ANALYSIS.md` trace to the files listed here.

## 1. Integrity rules and compliance

| Rule | Status |
|---|---|
| `SBG/` read-only | **Complied.** `find SBG -newer WP_C_ABLATIONS/logs/.start_marker -type f -not -path "*/__pycache__/*"` returned no files at the end of the session (run before this registry was finalised). `PYTHONDONTWRITEBYTECODE=1` was set for every run. No make/git commands were run. |
| v10_test / v9c_val not rescored | **Complied.** No scorer, variant or label-joined metric was run on them. The only reads were label-free descriptive reads of existing frozen scores/caches in EXP-WPC-004 (zero counts, channel comparison). V10 gap numbers are cited from the existing A3 table (`results/tables/EXP-A3-002_v10_test_comparison.csv`: `sbg_state` 0.9171, `sbg_v5` 0.896768). |
| V10 burned for post-hoc variants | All state/RV variants here were designed after V10 results were observed, so none was evaluated on V10. |
| Modified representations are exploratory | Every non-frozen variant is labelled "exploratory / not original SBG" in the outputs and docs. Frozen columns reproduced exactly: `full` = `sbg_v5`, `state_raw` = `sbg_state`, `v3_only` = `sbg_v3`, `temporal` = `sbg_temporal` (2074/2074 pairs, 9 d.p.). |
| Existing results not overwritten | All scripts refuse to overwrite existing outputs. Nothing outside `WP_C_ABLATIONS/` was written. |
| Raw predictions/labels/configs/logs kept | Per-pair scores + labels: `raw/EXP-WPC-002/*_pairs.csv`; configs: `configs/`; logs: `logs/`; failed attempts kept. |
| Environment | `venvs/py313/bin/python`, `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`, pure stdlib, ≤ 4 worker processes. |
| Statistics | `experiments/common/eval_lib.py` conventions: tie-aware AUROC/AUPRC; program-cluster bootstrap B = 2000, seed 42; Youden thresholds fitted on train only; Holm over declared families (12 in EXP-WPC-003, 7 in EXP-WPC-005a, 4 in EXP-WPC-006). |

## 2. Populations

| Population | Programs | Pairs (CHANGED/EQUIV) | Note |
|---|---|---|---|
| v9c_dev | 13 | 464 (232/232) | |
| v9c_train (primary) | 45 | 1610 (805/805) | **`math_gray_code` excluded (40 primary pairs)** — no cached trace |
| pooled | 58 | 2074 (1037/1037) | |

## 3. Experiments

| ID | Title | Status | Script | Output |
|---|---|---|---|---|
| EXP-WPC-001 | Re-extraction of V3/temporal/state genomes + exploratory state/return-value artefacts (in-process, frozen extractor) for dev + train | **DONE** (58/58 programs; first attempt FAILED on 5, see §5) | `scripts/wpc_extract.py` | `raw/EXP-WPC-001/{v9c_dev,v9c_train}/<program>/*.json.gz`, `DONE`, `RUN_LOG.json`; `logs/EXP-WPC-001_*` |
| EXP-WPC-002 | Per-pair component distances + verification against frozen scores | **DONE** | `scripts/wpc_pairs.py` | `raw/EXP-WPC-002/{v9c_dev,v9c_train}_pairs.csv`, `*_exclusions.json`, `VERIFY.json`; `logs/EXP-WPC-002_pairs.log` |
| EXP-WPC-003 | Component ablations (A.1–A.8), significance of state − full | **DONE** | `scripts/wpc_ablation.py` | `raw/EXP-WPC-003/ablation_results.json`, `tables/WPC-003_ablation_auroc_table.csv`; `logs/EXP-WPC-003_ablation.log` |
| EXP-WPC-004 | SC-6 forensics (label-free, V10/val/dev/train; delegated to a subagent, outputs verified against frozen scores by me) | **DONE** | `scripts/wpc_sc6_forensics.py` | `raw/EXP-WPC-004/*`; `logs/EXP-WPC-004_forensics.log` |
| EXP-WPC-005a | State-genome variants (return events, line events, arguments, structure, shuffle) — leakage / composition test; family of 7, Holm | **DONE** (exploratory) | `scripts/wpc_variants.py` | `raw/EXP-WPC-005/variants_results.json` (`state_variants`, `full_with_state_variant`, `leakage_label_free_diagnostics`) |
| EXP-WPC-005b | State sub-distance by event kind | **DONE** (exploratory) | same | `…variants_results.json` (`state_by_event_kind`) |
| EXP-WPC-005c | Spearman redundancy, state-weight sweep, complementarity, train-fit/dev-eval logistic combiner | **DONE** (exploratory; descriptive, not multiplicity-controlled) | same | `…variants_results.json` (`spearman_*`, `state_weight_sweep`, `complementarity_*`, `fitted_combiner_dev`). **Do not use `equiv_by_sp_type` in this file (degenerate).** |
| EXP-WPC-005d | False-positive mass on EQUIVALENT pairs by SP transform (SP type from `group` id) | **DONE** (descriptive) | `scripts/wpc_equiv_sp.py` | `raw/EXP-WPC-005/equiv_by_sp_from_group.json`; `logs/EXP-WPC-005d_equiv_sp.log` |
| EXP-WPC-006 | Return-value variants (pre-declared) + SC-6 metrics + label-oracle ceilings | **DONE** (exploratory) | `scripts/wpc_variants.py` | `raw/EXP-WPC-006/rv_results.json`; `configs/WPC_RV_PREDECLARATION.json` (+`.sha256`); `logs/EXP-WPC-005_006.log` |
| EXP-WPC-006b | Breakdown of SC-6 pairs still tied under RV | **DONE** (descriptive) | `scripts/wpc_rv_breakdown.py` | `raw/EXP-WPC-006/rv_sc6_breakdown.json`; `logs/EXP-WPC-006b_rv_breakdown.log` |

### Pre-declaration
`configs/WPC_RV_PREDECLARATION.json` (SHA-256 `e89f522620a8903e817de1480649354e26e8456b89707cc30616a394519bcd08`, time recorded in `.sha256`) was written before any label-joined RV metric was computed. The `rv_*` distance columns already existed in the pairs CSV at that time, but had not been scored against labels. Weights (0.8/0.2) are fixed a priori; no RV weight sweep was run.

### Not done / blocked
| Item | Status |
|---|---|
| Handoff item 4: tracer event-cap, timeout, input-subset sensitivity | **Not done** (no time/compute budget used; listed as experiment #10 in 08B). |
| Paired state-vs-V5 test on V10 or v9c_val | **Deliberately not run** (forbidden re-scoring). Continuation (for a session with authority): paired program-cluster bootstrap of `sbg_state − sbg_v5` on frozen scores/labels, 1 pre-declared comparison. |
| Confirmatory evaluation of any modified variant (state weight, RV, combiners) | **Not possible with current data**; needs a fresh withheld set and a new freeze (config + code SHA-256 before scoring, scored once). |
| Sensitivity analysis excluding SP-8 (behaviourally broken "equivalents") | **Not run.** |
| Individual diagnosis of the 24–26 residual SC-6 ties under RV | **Not run.** |
| `math_gray_code` (train) | No cached trace (killed rc = −9 in the earlier extraction; owned by WP-E). 40 primary pairs (2 SC-6) excluded. |

## 4. Verification records
* `raw/EXP-WPC-002/VERIFY.json`: dev 464/464 and train 1610/1610 pairs match frozen `sbg_v5`, `sbg_v3`, `sbg_temporal`, `sbg_state` at 9 d.p.; V3 eight-term sum bit-equal to `distance_v3` in all pairs; `s0` (identity state variant) equals frozen state graph in all pairs; `n_v5_not_full = 0`.
* `ablation_results.json`: `sanity_ci_eval_lib_equal = true`; `sanity_recomposed_vs_frozen_max_abs = 1.1e-16`.
* `variants_results.json`: `s0_equals_frozen_state_auc_max_abs = 0.0`; 2146/2146 trace files with `s0_equals_frozen = true`.
* EXP-WPC-004: SC-6 partner matching cross-checked against repo `matched_pair_id` fields (0 mismatches); V10 zero count 17/23 reproduced.

## 5. Failures, exclusions and anomalies (all retained)
1. **EXP-WPC-001 first attempt:** `KeyError: 'base_path'` for 5 programs whose rows were placeholders (no paths). Script fixed (`wpc_extract.py` final SHA below) and re-run with resume; failed-attempt logs: `logs/EXP-WPC-001_{dev,train}_RUN_LOG_first_attempt.json`, `logs/EXP-WPC-001_extract.log`; rerun: `logs/EXP-WPC-001_extract_rerun.log`.
2. **EXP-WPC-005/006 first run killed:** the process, started with `nohup … &` from a shell call, disappeared after that call returned (cause not diagnosed; probably the tool harness reaping it); it had printed 5a/5c/6-dev lines but wrote no output files. Rerun as a tool-managed background process; `logs/EXP-WPC-005_006_attempt1_killed.log` kept (partial prints only).
3. **`equiv_by_sp_type` in `variants_results.json` is degenerate** (`sp_type` is blank on label-0 rows; one bucket). Not edited; superseded by EXP-WPC-005d.
4. **`math_gray_code` exclusion** (see above).
5. **Cache limitation:** the shared trace cache stores locals snapshots only at call/return/exception events and only one run, so it cannot recompute the state genome; the frozen extractor was re-run in-process (EXP-WPC-001).
6. **Cached snapshots contain `<function … at 0x…>` reprs** (address-nondeterministic); the frozen abstract domain maps them to a fixed class; raw snapshot equality needs masking (applied in EXP-WPC-004).
7. **SP-8 "equivalent" partners that crash on every input** (visible SC-6+SP-8 pairs: val 3, dev 3, train 7; e.g. `UnboundLocalError`). Not investigated.
8. **Stray empty file** `scripts/pc_sc6_forensics.py` (0 bytes; created by the delegated subagent's mis-named write); unused, left in place, not an experiment script.
9. **Subagent status reports** were unreliable ("cancelled"); outputs were checked by file mtimes and by re-deriving counts from frozen scores.

## 6. Reproduction commands
Run from the repository package directory with a pinned environment:
```bash
cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
PY=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python

# EXP-WPC-001  (re-run frozen extraction in-process; resumable; refuses forbidden splits)
$PY WP_C_ABLATIONS/scripts/wpc_extract.py --split v9c_dev   --workers 4
$PY WP_C_ABLATIONS/scripts/wpc_extract.py --split v9c_train --workers 4 --skip math_gray_code
# EXP-WPC-002  (pair table + verification against frozen scores)
$PY WP_C_ABLATIONS/scripts/wpc_pairs.py
# EXP-WPC-003  (ablations; ~40 s)
$PY WP_C_ABLATIONS/scripts/wpc_ablation.py --procs 4
# EXP-WPC-005a/b/c + EXP-WPC-006  (state variants, mechanism, RV variants; ~1-2 min)
$PY WP_C_ABLATIONS/scripts/wpc_variants.py --procs 4
# EXP-WPC-005d, 006b  (descriptive follow-ups)
$PY WP_C_ABLATIONS/scripts/wpc_equiv_sp.py
$PY WP_C_ABLATIONS/scripts/wpc_rv_breakdown.py
# EXP-WPC-004  (SC-6 forensics; label-free; run from scripts/)
(cd WP_C_ABLATIONS/scripts && $PY wpc_sc6_forensics.py)
```
All scripts exit with "refusing to overwrite …" if the output exists; to reproduce into a clean place, copy `WP_C_ABLATIONS/scripts` and change the output root, or move existing `raw/EXP-WPC-00X/` aside (do not delete the originals). Exact determinism: `PYTHONHASHSEED=0`, bootstrap seed 42, shuffle seed derived from `wpc-shuffle:<trace>:<event>`.

Final SBG-untouched check (expected: no output):
```bash
cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW
find SBG -newer IEEE_ACCESS_PRE_SUBMISSION/WP_C_ABLATIONS/logs/.start_marker -type f -not -path "*/__pycache__/*"
```

## 7. Integrity hashes (SHA-256, computed at registry time)

| File | SHA-256 |
|---|---|
| scripts/wpc_extract.py | `db0997f6d39006590c9c6c5a32cc0e8bb86cb4a0990d5eea293f1b2efa3063a3` |
| scripts/wpc_pairs.py | `fad8d67f474177e154fe8c586f5a64b35015b89fedfdc8bbfa427eee2c24b3f1` |
| scripts/wpc_ablation.py | `723ee5b2a6e1c4a95e3172e8914990de22cad7f425c992d0fb3d1dfbebcdcdb6` |
| scripts/wpc_variants.py | `764007d0bca88629200a3e35e135a2a5ceb2e7f0b7c419efeee226f202355fe6` |
| scripts/wpc_equiv_sp.py | `262e169800a03f7732de4d491c82c7ba920455e0d4e68e8f55894405a5ba13a6` |
| scripts/wpc_rv_breakdown.py | `a68c2de5a20db37ed7c3cc67b6658585f96d8008e91dc570a709d7ee03e82516` |
| scripts/wpc_sc6_forensics.py | `5e167d82f206499c272892790e09400b55d2796a24c824763dda63f360f8d5f2` |
| configs/WPC_RV_PREDECLARATION.json | `e89f522620a8903e817de1480649354e26e8456b89707cc30616a394519bcd08` |
| raw/EXP-WPC-002/v9c_dev_pairs.csv | `4d5bd0eb8450fd50b505a2f2ec4398f11fe02b9e2c457f1335157f65a8c76b5d` |
| raw/EXP-WPC-002/v9c_train_pairs.csv | `045717abb6e25e90b59ff35f3030011588bcc121b7282843151218f3231b1de6` |
| raw/EXP-WPC-002/VERIFY.json | `565966d23fa476aa746a0b8813a49a793a9c5c94a42e8e0e49df0fc39c2d576c` |
| raw/EXP-WPC-003/ablation_results.json | `5b7db50f7e9e33e1cdf609957ddcbfb479b54b09b1f3ca3ab65eb18a27148596` |
| raw/EXP-WPC-004/sc6_summary.json | `5ed887e0cbc9d50fbfa4d776a18a2c3e1da0fc9cad94b020660629bdfebe9e07` |
| raw/EXP-WPC-005/variants_results.json | `923c149b993b4fda770696f7690c8466bcf5efa757b7b42db863d874ce0c8d9e` |
| raw/EXP-WPC-005/equiv_by_sp_from_group.json | `666a3f15389006c7f9ec6f932ec795a871900544f9492afcc15472f68f0ac585` |
| raw/EXP-WPC-006/rv_results.json | `da587de6c87caaeabd9217f746eef9039b97e8a2ccd98bc1563bddd5fc817a84` |
| raw/EXP-WPC-006/rv_sc6_breakdown.json | `cc1e5a165d326ee891b057f9fbc12192be7878069c4410c7e4440b963e274eb5` |
| tables/WPC-003_ablation_auroc_table.csv | `1b15c725d191a83ac907dd916e4478f3e4b61c1db5929eb1d723142d4b543ef8` |

## 8. Component definitions used (exploratory; WP-C-defined)
"Call topology" is not defined in the repo; WP-C defined: `call_topology = 0.5·(0.20·d_freq + 0.10·d_depth)`, `bigrams = 0.5·0.25·d_seq`, `exception = 0.5·(0.10·d_exc + 0.05·d_exc-causality)`, `coverage_resid = 0.5·(0.20·d_cov + 0.05·d_con + 0.05·d_inp)`, `temporal = 0.25·d_temporal`, `state = 0.25·d_state` (V5 = 0.5·V3 + 0.25·temporal + 0.25·state). Another grouping would change the "only/minus" numbers.

## 9. Deliverables
`08A_ABLATION_RESULTS.md`, `08B_RETURN_VALUE_ARCHITECTURAL_ANALYSIS.md`, this registry, `raw/`, `tables/`, `configs/`, `logs/`, `scripts/`.

# 09 — Reproducibility and Artifact-Freeze Audit (Agent A2)

Repo: `SBG/` at HEAD `3425693` (branch `remediation/sbg-v4`), read-only. Canonical interpreter: `venvs/py313` (CPython 3.13.5). All runs used `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`, and every writing step ran on a copy under `PKG/reproduction/`.
Registry: `logs/registry/A2_repo.jsonl` (`EXP-A2-001 … 018`). Paths below are relative to `PKG/` unless prefixed `SBG/`.

---

## 0. Verdict

| Question | Verdict |
|---|---|
| Are the frozen artifacts intact? | **Yes.** 533 of 536 pinned SHA-256 values match. The 3 mismatches are one disclosed change (`evaluate_v8.py`, pinned twice) and one disclosed change (`run_chunked.py`, AMENDMENT2). Both are explained below and both are disclosed in the amendments. |
| Were frozen artifacts modified after their freeze commit? | Only the V8 pins, and the V8 amendments disclose each change. FREEZE_V9 and FREEZE_V10 pins have 0 later commits (EXP-A2-002). |
| Is "frozen before scoring" enforced by git? | **No, it is self-attested.** The V10 freeze, scored pairs, evaluation and dataset all sit in one commit, `c5bc130`. |
| Are the V10 and V9c-val SBG scores reproducible from scratch? | **Yes, bit-exactly, on CPython 3.13.5.** V10: 644/644 rows identical. V9c-val: 436/436 rows identical. 0 cross-label orderings change (EXP-A2-007/008). |
| Does that hold on other Python versions? | **No.** 3.9.6, 3.11.15 and 3.14.5 all give different scores, and rankings flip (§6). Reproduction is exact on 3.13.x only. |
| Do the tests pass on a clean checkout? | **Yes: 807 passed, 0 failed, 0 skipped, 3 warnings** (399 s, py313). The py39 run aborts the interpreter on macOS (§8). |
| 35/35 and 10/10? | `verify_trace_v4.py` prints 35/35, but it is mostly a doc-string check and is not an independent verification (§8.2). `consistency_check.py` prints 10/10 (C1–C10). |
| Is the headline path documented and reachable? | **No.** README, `docs/current/REPRODUCTION.md` and the Makefile never mention `evaluate_v10`, `score_v6_experimental` or `FREEZE_V10` (§9). |
| What could not be done? | The `FREEZE_V10.variants_tree_sha256` digest could not be reproduced (algorithm undocumented). The Orchestrator trace dump stalled at 3/19 V10 programs and 0 V9c-val programs. py39 full pytest aborts. |

---

## 1. Hash verification (EXP-A2-001)

Script: `reproduction/verify_hashes.py` (pure stdlib, independent of the repo's own verifier). Output: `results/raw/repro/hash_verification.{json,tsv}` and `hash_verification_stdout.txt`.

**Result: 536 pins checked, 533 MATCH, 3 MISMATCH.**

| Source file | Pins | Match | Mismatch |
|---|---|---|---|
| `artifacts/final/FREEZE_V10.json` | 25 | 25 | 0 |
| `artifacts/final/FREEZE_V10_SCORED.json` | 1 | 1 | 0 |
| `artifacts/final/FREEZE_V9.json` | 21 | 21 | 0 |
| `artifacts/final/FREEZE_V8.json` | 21 | 19 | 2 |
| `artifacts/final/FREEZE_V8_AMENDMENT1.json` | 14 | 14 | 0 |
| `artifacts/final/FREEZE_V8_AMENDMENT2.json` | 4 | 3 | 1 |
| `artifacts/final/PHASE2_FREEZE.json` | 1 | 1 | 0 |
| `artifacts/final/freeze_handoff.json` | 10 | 10 | 0 |
| `artifacts/final/freeze_bugsinpy.json` | 256 | 256 | 0 |
| `artifacts/final/freeze_quixbugs.json` | 113 | 113 | 0 |
| `artifacts/final/freeze_threshold.json` | 1 | 1 | 0 |
| `artifacts/paper_evidence/EXPERIMENT_MANIFEST.json` | 35 | 35 | 0 |
| `artifacts/paper_evidence/EXPERIMENT_MANIFEST_V3.json` | 16 | 16 | 0 |
| `artifacts/paper_evidence/EXPERIMENT_MANIFEST_V4.json` | 18 | 18 | 0 |

### 1.1 The three mismatches

| Pin | Expected | Actual | Explanation |
|---|---|---|---|
| `FREEZE_V8.json` `code_sha256/experiments/final/evaluate_v8.py` | `8e567b8c…` | `34f303af…` | Expected equals the git blob at `496fb4f` (the freeze). `evaluate_v8.py` was changed in `465be1b` ("freeze amendment 1: score test on non-stale pairs only"). Disclosed in `FREEZE_V8_AMENDMENT1.json`, which pins the new hash (14/14 match). |
| `FREEZE_V8.json` `evaluation_script_sha256` | `8e567b8c…` | `34f303af…` | Same pin as above, listed twice. |
| `FREEZE_V8_AMENDMENT2.json` `run_chunked_sha256` | `32a9eb05…` | `7d8e67ff…` | Expected equals the git blob at `c0f6c6d`. The current file is the one `FREEZE_V9.json` pins (21/21 match). `run_chunked.py` was modified again in `6dd5a0f`, the commit that introduces FREEZE_V9 ("committed BEFORE val scores are opened"), and FREEZE_V9 pins the new hash. Amendment 2 was not updated, so its pin is stale; the change is visible in git. |

None of the three affects a V10 or V9c result: those use `evaluate_v10.py`/`evaluate_v9.py` and the scored files pinned by FREEZE_V10/FREEZE_V9, all of which match. The V8 test result depends on `evaluate_v8.py`; its current hash is pinned by Amendment 1 and it matches.

### 1.2 Combined and tree digests

| Digest | Expected | Result |
|---|---|---|
| `freeze_bugsinpy.combined_sha256` (from pinned hashes and from live files) | `4946b113…` | verified, both ways |
| `freeze_quixbugs.negatives.combined_sha256` | `2e1c3bba…` | verified |
| `FREEZE_V8.variants_tree_sha256` | `c250047b…` | verified (4,693 `.py` files; path ⧺ `\0` ⧺ bytes, sorted) |
| `FREEZE_V8.base_programs_tree_sha256` | `3494f09e…` | verified, but it is computed over `benchmark/corpus/fresh_programs` (121 `.py`), so the key name is misleading |
| **`FREEZE_V10.variants_tree_sha256`** | `f22f0c6c…` | **NOT reproduced.** Hundreds of candidate algorithms over the 644 variants (and plausible subsets) were tried, with no match. The algorithm is not documented in code. The 25 per-file FREEZE_V10 pins still match, and the regeneration test (§4.3) shows all 646 dataset files are byte-identical. So the dataset is verified by other means, but this one digest cannot be checked by a third party. |

### 1.3 Older 16-hex-prefix manifests

`FINAL_REPRODUCIBILITY_MANIFEST` and `FINAL_EVIDENCE_MANIFEST` (dated 2026-08-20): 49 of 51 prefixes match. The 2 mismatches are both `docs/CLAIMS_REGISTRY.yaml` (modified after August; size 12,828 vs 23,119 bytes). This is drift in a document, not in an evidence file.

`benchmark/datasets/v8/manifest.json` `program_hashes`: 8 of 100 differ from the current files. These are the 8 known stale programs (disclosed in the amendments).

---

## 2. Git-history proof (EXP-A2-002)

Script: `reproduction/git_history_audit.py`. Output: `results/raw/repro/git_history_audit.{json,md}`. Read-only `git log --follow`.

| Freeze | Introduced at | Pinned paths with later commits |
|---|---|---|
| FREEZE_V8 (+AMEND 1/2) | `ebb8c44` | 4: `FREEZE_V8_AMENDMENT1.json` (`465be1b`), `FREEZE_V8_AMENDMENT2.json` (`c0f6c6d`), `v8_test_nonstale/pairs_test.jsonl` (`465be1b`), `evaluate_v8.py` (`465be1b`). All are the amendments themselves. |
| FREEZE_V9 | `6dd5a0f` | 0 |
| FREEZE_V10 | `c5bc130` | 0 |

Caveats:
* FREEZE_V10's anchor commit `c5bc130` contains the freeze file, the scored pairs, the evaluation output and the dataset together. Git ordering therefore cannot show that the freeze preceded scoring. The ordering is self-attested.
* `PHASE2_FREEZE.json` records a timestamp (2026-09-28) earlier than the commit that holds it.
* `sbg/v2/execution/runner.py` (the sandbox runner on the headline path) is not hash-pinned in any freeze file.

---

## 3. Traceability table: claim → artifact → script → command → verified?

Source: EXP-A2-014; `results/raw/repro/traceability.{md,json}`, generated by `reproduction/trace_claims.py`.

**What "verified" means here:** the value appears in the HEAD artifact at the cited line, the generating script exists in HEAD, and its pin status in freeze files is shown. It does **not** mean the statistic was re-derived; that is Agent A3's job. The only things A2 re-derived are the scored inputs of V10 and V9c-val (§4).

Result: 34 claims, all 34 values found in HEAD artifacts, all 34 scripts found in HEAD. **24 of 34 scripts are hash-pinned; 10 are not.**

| # | Claim | Artifact : line | Script (pin) |
|---|---|---|---|
| 1 | V10 H1 AUROC 0.8968, p 0.0005 (n=638) | `artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json`:39 | `experiments/final/evaluate_v10.py` (FREEZE_V10, MANIFEST_V4) |
| 2 | V10 H1 Holm p_adj 0.003 | same :373 | same |
| 3 | V10 H2 +0.2545 [0.2178, 0.2851] | same :337 | same |
| 4 | V10 H3 +0.2807 | same :344 | same |
| 5 | V10 H4 +0.0063, p 0.81 (null) | same :351 | same |
| 6 | V10 H5 +0.0029, Holm p_adj 0.090 (not rejected) | same :358 | same |
| 7 | V10 H6 +0.0085 (null) | same :365 | same |
| 8 | V10 state genome AUROC 0.917 (> SBG-V5 0.897) | same :68 | same |
| 9 | V10 edit forward 0.616 / reversed 0.384 | same :96 | same |
| 10 | V10 exact-zero rate 0.3464 (eq 0.6364, changed 0.0564) | same :48 | same |
| 11 | V10 SC-6 changed zero-rate 0.7391 = 17/23 | same :701 | same |
| 12 | V10 scored pairs | `artifacts/final/pairs_v10_test_v6exp.jsonl` | `score_v6_experimental.py --design v10 --split test` (FREEZE_V10) |
| 13 | V9c-val H1 0.7514, p 0.0005 (n=432) | `artifacts/paper_evidence/V9_VAL_EVALUATION.json`:51 | `evaluate_v9.py` (FREEZE_V9) |
| 14 | V9c-val H2 +0.1122 | same :186 | same |
| 15 | V9c-val H3 +0.1402 | same :194 | same |
| 16 | V9c-val H4 +0.0210, p 0.117 (null) | same :202 | same |
| 17 | V9c-val zero rate 0.3704 | same :440 | same |
| 18 | V9c-val matched concordance SBG 0.806 vs edit 0.924 | same :412 | same |
| 19 | V8 test SBG-V5 AUROC 0.6937 | `V8_TEST_EVALUATION.json`:64 | `evaluate_v8.py` (FREEZE_V8, AMEND1; 2 disclosed mismatches) |
| 20 | V8 test reversed edit size 0.8759 | same :89 | same |
| 21 | V8 test non-stale scored pairs | `artifacts/final/v8_test_nonstale/pairs_test.jsonl` | `run_chunked.py` (AMEND2 mismatch, FREEZE_V9 match) |
| 22 | BugsInPy 0.497 (SP-2 excluded rescore) | `EXTERNAL_RESCORE_V8.json`:32 | `rescore_external_v8.py` (MANIFEST_V3) |
| 23 | BugsInPy 0.410 (147 valid pairs) | `artifacts/final/BUGSINPY_output_free_v7.json`:25 | `external_bugsinpy.py` (**not pinned**) |
| 24 | QuixBugs 0.388 (all 152) | `artifacts/final/QUIXBUGS_output_free_v7.json`:22 | `external_quixbugs.py` (**not pinned**) |
| 25 | QuixBugs 0.444 (111 pairs) | `EXTERNAL_NEGATIVE_AUDIT.json`:146 | `audit_external_negatives.py` (MANIFEST_V3) |
| 26 | QuixBugs within-program 0.3884 | `DIAGNOSTIC_EXTERNAL.json`:80 | `diagnose_external.py` (**not pinned**) |
| 27 | Edit-size diagnostics | `DIAGNOSTIC_EDIT_SIZE.json` | `diagnose_edit_size.py` (**not pinned**) |
| 28 | Ablations | `ABLATIONS.json` | `build_ablations.py` (**not pinned**) |
| 29 | Post-hoc V10 supplement | `V10_POSTHOC_SUPPLEMENT.json` | `posthoc_v10_supplement.py` (**not pinned**) |
| 30 | Zero-score population | `raw/zero_score_population_v1.json` | `zero_score_population.py` (**not pinned**; needs 4 untracked v8-dev files) |
| 31 | Zero-score root cause | `ZERO_SCORE_ROOT_CAUSE_V1.md` | `diagnose_zero_scores.py` (**not pinned**) |
| 32 | Weight fitting (fixed 0.50/0.25/0.25) | `WEIGHT_FITTING.json` | `fit_weights.py` (FREEZE_V8/V9/V10) |
| 33 | "35/35 trace verifications" | `RESEARCH_STATUS_V4.md` | `verify_trace_v4.py` (**not pinned**) |
| 34 | "10/10 consistency checks" | `docs/current/REPRODUCTION.md`:107 | `consistency_check.py` (**not pinned**) |

Reading notes on specific headline numbers:
* **BugsInPy 0.497 and 0.410 are different populations.** 0.497 is the SP-2-excluded rescoring (`EXTERNAL_RESCORE_V8.json:32`). 0.410 is the 147 valid pairs in `BUGSINPY_output_free_v7.json:25`. Quoting both without stating the population invites a contradiction claim.
* **QuixBugs 0.388 and 0.444 are also different populations.** 0.388 is all 152 pairs (`QUIXBUGS_output_free_v7.json:22`). 0.444 is 111 pairs after excluding invalid negatives and SP-2 (`EXTERNAL_NEGATIVE_AUDIT.json:146`).
* V8 test 0.694 (`V8_TEST_EVALUATION.json:64`) vs reversed edit size 0.876 (`:89`) are both in the committed artifact. The values 0.6944 and 0.8765 also appear as per-program numbers elsewhere in that file; this is coincidence.
* **Unpinned scripts that produce reported numbers:** `external_bugsinpy.py`, `external_quixbugs.py`, `diagnose_external.py`, `diagnose_edit_size.py`, `diagnose_zero_scores.py`, `build_ablations.py`, `posthoc_v10_supplement.py`, `zero_score_population.py`, `verify_trace_v4.py`, `consistency_check.py` (and `check_reproduction.py`). Their *input corpora* are pinned (`freeze_bugsinpy.json`, `freeze_quixbugs.json`), but the scripts themselves can change without any pin failing.

---

## 4. Recomputation of the scored files from scratch

Script: `reproduction/recompute_scores.py` (imports the frozen `experiments/final/extraction.py` from the clean checkout via `sys.path`; protocol `output_free_v8`; `N_RUNS=5, MAX_EVENTS=5000`, trace timeout 1 s, program budget 60 s, `MAX_TIMEOUTS=2`). Comparison keys: `sbg_v5, sbg_v3, sbg_temporal, sbg_state, exception_fraction, exception_component_v3, exception_type_jaccard, call_count, n_functions, coverage_size, combined_shortcut, v5_full`.

| Experiment | Population | Result | Output |
|---|---|---|---|
| EXP-A2-007 | V10 test, py313, hash seed 0 | **644/644 rows bit-identical** (641 evaluated plus 3 unevaluated). 0 key differences over 12 score keys. 0 of 102,718 cross-label orderings change. 0 timeouts. | `results/raw/repro/recompute_v10_py313_seed0/COMPARE.json` |
| EXP-A2-008 | V9c-val, py313, hash seed 0 | **436/436 rows bit-identical** (partner file `pairs_v8val_output_free_v8.jsonl`). 0 of 47,088 orderings change. 2 timeouts, both in `math_lis_length__sc3+sp6_s1_j16.py`, the one documented nonterminating file. | `results/raw/repro/recompute_v9cval_py313_seed0/COMPARE.json` |
| EXP-A2-012 | V10 dataset regeneration (`generate_v10_independent.py`, clean copy only) | **All 646 files byte-identical** (644 variants, `pairs_test.jsonl`, `manifest.json`). Rejection log `{'eq_check': 316, 'eq_oracle': 32, 'ch_none': 14}`. | `reproduction/generate_v10_clean.log` |
| EXP-A2-015 | Orchestrator trace cache (`experiments/common/dump_traces.py`) | Only 3 of 19 V10 programs (`ds_ranked_set`, `graph_alien_dict`, `graph_cycle_detection_dfs`) and 0 V9c-val programs had a DONE file. The 86/86 pairs from those 3 are identical to the frozen scores. The dump job appears stalled; it was still at 3/19 when polled again at the end of this audit. | `results/raw/repro/crosscheck_orch_trace_cache.json` |

Notes:
* `math_lis_length` alone takes 74 s. The background run died before it, so I re-ran it through the worker entry point and copied the output into the directory (`results/raw/repro/recompute_v9cval_lis.log`).
* Because the scored files reproduce exactly, `evaluate_v10.py` and `evaluate_v9.py` (pinned) will produce the same statistics from them. A2 did not re-run the statistics.

### 4.1 Silent fallbacks (measured, EXP-A2-003)

`extraction.score_pair` replaces a missing temporal or state layer with `d_v3`, and replaces the whole V5 score with `d_v3` when `v5_full` is false. `extract_temporal` and the state extraction are wrapped in `try/except → None`. I measured how often this fires.

| Population | Evaluated pairs | `v5_full=1.0` | Fallback fired |
|---|---|---|---|
| V10 test | 638 primary | 638 | **0** |
| V9c-val | 432 primary | 432 | **0** |
| V9c-dev | 464 | 464 | 0 |
| V9c-train | 1,650 | 1,650 | 0 |

(`results/raw/repro/fallback_rates_frozen.json`, from `reproduction/fallback_rates.py`.)
In the recompute, 660/660 V10 files and 445/445 V9c-val files had both temporal and state layers (`results/raw/repro/fallback_files_recompute.json`). The unevaluated pairs are explicit failures, not silent fallbacks: V10 has 3 nonterminating; V9c-val has 1 nonterminating and 1 import_error.
Files whose traces hit the `MAX_EVENTS=5000` cap: V10 29/660, V9c-val 40/445. The cap is a fixed protocol parameter, not a silent failure, but it does mean 4–9% of files are scored on truncated traces.

### 4.2 Determinism of the 5 runs per file

Across all 663 V10 files, the event-sequence digests of the 5 runs are identical in every file. The locals-snapshot digests differ in 267/663 files because the snapshot reprs contain memory addresses (for example `<list_iterator object at 0x…>`). The scores do not use those digests, which is why the scores are still bit-identical.

### 4.3 Zero-score rates (counts from the frozen files)

| Population | Exact-zero `sbg_v5` among primary pairs |
|---|---|
| V10 | 221/638 = 34.64% (63.6% of equivalent pairs, 5.64% of changed pairs) |
| V9c-val | 160/432 = 37.04% |
| V9c-dev | 158/464 |
| V9c-train | 628/1,650 |

---

## 5. Sensitivity of the 3.13 result to environment (EXP-A2-009)

Subset: 4 V10 programs (`ds_ranked_set`, `sort_radix_sort_lsd`, `graph_topological_kahn`, `sort_stooge_sort`), 140 pairs, 4,830 cross-label pairs. Script: `reproduction/sensitivity_driver.sh`. Summary: `results/raw/repro/sens/SENSITIVITY_SUMMARY.json`. Reference pooled AUROC of the frozen subset: 0.8407.

| Condition (all py313 unless stated) | Rows differing | Max abs diff | Orderings changed |
|---|---|---|---|
| hash seed 0 (baseline) | 0/140 | 0 | 0 |
| hash seed 1; 3 runs with random seeds (12 program-runs) | 0/140 each | 0 | 0 |
| working directory `/tmp` | 0/140 | 0 | 0 |
| `re.purge()` never / always / per pair | 0/140 each | 0 | 0 |
| 28 / 56 busy-loop processes on 14 cores (wall time ×2.6 / ×5) | 0/140 | 0 | 0 |
| 84 busy-loop processes (wall time ×6); a different 4-program subset chosen for long runtimes (`math_coin_change`, `sort_gravity_bead`, `math_fib_matrix`, `graph_network_delay`) | 0/142 (140 exact plus 2 rows equal as unevaluated; 4,899 cross-label pairs, pooled AUROC 0.9312 unchanged) | 0 | 0 |

The 1 s trace timeout never fired in any run, even at 84 competing processes. 92 of the 140 subset rows had at least one trace truncated at `MAX_EVENTS`, so the truncation path was exercised. `PYTHONHASHSEED` unset was not run literally (the harness always sets it); the random-seed runs are the equivalent test.

---

## 6. Sensitivity to the CPython version (EXP-A2-009/010/017)

The scored files are exact only on 3.13.x.

| Interpreter | Population | Pairs differing | Max abs diff | Orderings flipped | Pooled AUROC (frozen → new) |
|---|---|---|---|---|---|
| 3.13.5 | V10 full, V9c-val full, subset | 0 | 0 | 0 | unchanged |
| 3.9.6 | subset (140 pairs) | 82/140 | 0.999 | 406/4,830 | 0.8407 → 0.9018 |
| 3.9.6 | V10 full (18 of 19 programs; `math_fib_matrix` aborts) | 299/613 evaluated | 0.533 | 3,837/93,942 | 0.8947 → 0.9226 |
| 3.9.6 | V9c-val full | 187/434 | 0.287 | 3,006/47,088 | 0.7530 → 0.7815 |
| 3.11.15 | subset | 65/140 | 0.990 | 319/4,830 | 0.8407 → 0.8980 |
| 3.14.5 | subset | 2/140 | 1.0 | 84/4,830 | 0.8407 → 0.8280 |

* The dependence on the minor version is non-monotonic: 3.11 and 3.9 raise the pooled AUROC, 3.14 lowers it, and the magnitude varies from 2 to 82 differing rows.
* The two 3.14.5 pairs are `sort_stooge_sort__sc11+sp3_s1` (sbg_v5 0.7593 → 0.0721) and `sort_stooge_sort__sc11+sp4_s1` (0.7771 → 0.0).
* Python 3.9 recompute of V10 aborts the whole interpreter on `math_fib_matrix__sc1+sp1_s0.py` (rc −6, `Fatal Python error: _Py_CheckRecursiveCall: Cannot recover from stack overflow`, raised from `sbg/extraction/dynamic/tracer.py:371`).
* The repository itself documents this class of sensitivity (`PYTHON_VERSION_SENSITIVITY.json`: 3.9.6 vs 3.13.15 shifts distances by up to 0.41) and declares 3.9 as a floor. The paper should state that the headline numbers are defined for CPython 3.13.x only.
* The 3.11/3.14 results are subset-only (4 programs). They show that the 3.13 dependence is real; they do not give full-population AUROC changes for those versions.

Outputs: `results/raw/repro/sens/{py39_seed0,py39_seed_random,py311,py314}` and `…/compare_recompute_*_py39_seed0.txt`.

---

## 7. Environment and seeds

| Item | Value | Source |
|---|---|---|
| OS / hardware | macOS 26.6.2, Apple M4 Max, 14 cores, 36 GB | `sw_vers`, `sysctl` |
| Python (canonical) | `venvs/py313` 3.13.5 | `venvs/py313/bin/python --version` |
| Other Pythons | `venvs/py39` 3.9.6; `/opt/homebrew/bin/python3.11` 3.11.15; `python3.14` 3.14.5 | |
| `.python-version` | `3.13` | `SBG/.python-version` |
| Declared version | **3.13.15** in `requirements-lock.txt`, `external/bugsinpy/manifest.json`, `docs/current/PYTHON_VERSIONS.md`, `docs/current/REPRODUCTION.md`; **3.13.5** in `FREEZE_V8/V10` and in the venv | grep |
| Seeds | `SEED=42` in `extraction.py` is logged but no RNG is seeded by it. The tracer path is deterministic. Dataset generation uses seeded `random.Random` and reproduces byte-exactly (§4). | code read |
| `PYTHONHASHSEED` | Not required for the scores on 3.13.5 (12 random draws plus seed 0 and 1 give identical results). Still recommended for set/dict-order safety. | §5 |

**3.13.15 vs 3.13.5 (minor, unresolved):** 3.13.15 does not exist among the installed interpreters, and the freeze files record 3.13.5. The scores reproduce bit-exactly on 3.13.5, so the 3.13.15 text in four documents is wrong or refers to a CI image I cannot check. It should be corrected to match the interpreter actually used.

Sources of nondeterminism found in the code:
1. CPython minor version (dominant; §6).
2. Memory addresses in locals-snapshot reprs (affects snapshot digests only).
3. Wall-clock trace timeout of 1 s and program budget of 60 s. Not triggered in any measured condition.
4. Tracer threads: one daemon thread per trace with `join(timeout)`. After the deadline the trace stops silently while the function keeps running, with no flag. Not triggered here, but the mechanism can fire under extreme load.
5. Hash seed, cwd and the `re` cache had no effect on 3.13.

---

## 8. Tests and checks on a clean checkout

Clean checkout: `git archive HEAD | tar -x` into `reproduction/clean_checkout/`. No untracked file was needed.

### 8.1 pytest (EXP-A2-004)

`PYTHONHASHSEED=0 venvs/py313/bin/python -m pytest -p no:cacheprovider`. Log: `reproduction/pytest_py313.log`.

**807 passed, 0 failed, 0 skipped, 3 warnings, 399 s.**

Warnings:
1. `PytestRemovedIn10Warning` in `sbg/extraction/static/test_error_genome.py::TestCircuitBreakerCorpus`.
2. `SyntaxWarning: "is not" with a literal` in `benchmark/datasets/v6/variants/val/graph_cycle_detect_dfs__sc1_s0_p0.py:37` (two occurrences).

The slowest test is `tests/test_zero_score_v4.py::test_37_percent_figure_reproduces` (130 s).

### 8.2 `verify_trace_v4.py` → 35/35 (EXP-A2-005)

Log: `reproduction/verify_trace_v4.log`. Output: "35/35 trace checks passed". `verify_trace_v3.py` gives 31/31.
The script checks that strings appear in `RESEARCH_STATUS_V4.md`, and most of its predicates are hard-coded True. It confirms the document is self-consistent. It is **not** an independent verification of the traces and should not be cited as such.

### 8.3 `consistency_check.py` → 10/10 (EXP-A2-005)

Log: `reproduction/consistency_check.log`. The CHECKS list has 10 entries (C1–C10), and all pass. See report 01 §7 for the 7-vs-10 resolution.

### 8.4 `check_reproduction.py --strict`

Passes on py313 (`reproduction/check_reproduction_strict_py313.log`), with a note that 2 lines differ only in the allowed `threshold_provenance` free-text key. This is the behaviour added by `3425693`.

### 8.5 CI scientific-integrity emulation (EXP-A2-006)

On py3.11 using `reproduction/ci_emulation.sh`: the four generators return rc 0; the 3 CI-tracked artifacts are byte-identical to the pristine archive; consistency 10/10; `tests/test_integrity.py` 25 passed (6 warnings); the quickstart runs.
The throw-away repo's `git commit` step was blocked by a global secret-scanner hook (false positive on the word "seed" in `artifacts/v2/REPRODUCIBILITY_AUDIT.json`). I did not bypass the hook and used `diff -r` against a pristine archive instead.

### 8.6 py39 pytest (EXP-A2-011) — informational

The interpreter aborts (exit 134, SIGABRT), 3 of 3 attempts, at `tests/test_tracer_isolation.py::TestRecursionErrorCountsAsTimeout::test_recursion_error_triggers_early_abort`. 758 passed with 0 failures before the abort. With that test deselected, the three trailing files (`test_tracer_isolation`, `test_v10_independent`, `test_zero_score_v4`) give 56 passed. GitHub's py3.9 on `ubuntu-22.04` passes this test, so the crash is specific to macOS CPython 3.9.6. The 3.13 suite is canonical.

### 8.7 CI status at HEAD

GitHub Actions (public API): run #9 (workflow_dispatch) success; run #10 (pull_request) success with all 5 jobs green (tests py3.9 and py3.13, scientific-integrity, fast-experiments py3.9 and py3.13); run #11 (push to main, merge `f3e40db`, tree `6f89be5` equal to `3425693`) success. The py3.13 tests job took 25 min. The prior audit's "CI red" claim is therefore contradicted for HEAD.

---

## 9. Reproduction package and overwrite risks

Deliverables: `reproduction/REPRODUCE.md` and `reproduction/run_repro.sh`.

`run_repro.sh --quick` (EXP-A2-016): fail=0 in 2 min 20 s. It checks 533 matching pins, consistency 10/10, 35/35, V10 `644 644 0 0`, and V9c-val `436 436 0 0`. It works on a throw-away clean checkout, never writes to REPO, and never rewrites a frozen artifact. `--full` adds pytest and the sensitivity driver; I ran the parts separately but not the `--full` flow end-to-end. The first attempt of `--quick` failed because of a bug in the driver's own hash-summary parsing; I fixed it, and the first-attempt outputs are kept in `results/raw/repro/run_FIRSTATTEMPT_hashstep_parse_bug`.

### 9.1 Documented path does not reach the headline results

`README.md` and `docs/current/REPRODUCTION.md` never mention `evaluate_v10`, `score_v6_experimental` or `FREEZE_V10` (grep). The Makefile has no target for V8/V9/V10. A third party following the README cannot regenerate the V10 headline. They need the commands in `REPRODUCE.md` or the traceability table above.

### 9.2 Overwrite risks

| Command | Overwrites | Risk |
|---|---|---|
| `make reproduce-fast`, `make check-reproduction`, `experiments/final/check_reproduction.py` | `artifacts/final/HARD_NEGATIVE_V5_RESULTS.json` and `REGRESSION_V5_RESULTS.json` in place | Major. In REPO these two files have a Nov 7 mtime but their content equals HEAD (`git status` clean), so someone ran it earlier and restored them. |
| `make tables`, `figures`, `readme`, `verify-artifacts`, `check` | docs, README and manifests | Major |
| `make reproduce-v5`, `reproduce-output-free`, `v7-*` | `artifacts/final/pairs_*` | Major (touches frozen scored files) |
| `evaluate_v10.py run` / `evaluate_v9.py run` | Refuse to re-run unless output is deleted and FREEZE hashes match | Guard present |
| `evaluate_v8.py run --allow-overwrite-never-use` | Suppressed flag exists | Minor |

I ran none of these in REPO. All write-capable steps ran on copies.

---

## 10. Failed / could not be done / continuation commands

| Item | Status | Continuation |
|---|---|---|
| `FREEZE_V10.variants_tree_sha256` (`f22f0c6c…`) | Not reproduced; algorithm unknown | Ask the author for the exact tree-hash code. Alternatively replace the digest with the per-file pins, which all match. |
| Orchestrator trace dump (`experiments/common/dump_traces.py`) | Stalled at 3/19 V10 programs, 0 V9c-val | `python reproduction/crosscheck_orch_trace_cache.py` once the Orchestrator finishes the dump. A2's own recompute (§4) already covers all programs. |
| py39 full pytest | Interpreter abort at one test (macOS 3.9.6 only) | `venvs/py39/bin/python -m pytest -p no:cacheprovider --deselect tests/test_tracer_isolation.py::TestRecursionErrorCountsAsTimeout::test_recursion_error_triggers_early_abort` on a copy |
| py39 V10 full recompute | `math_fib_matrix` aborts the interpreter; 18/19 programs scored | Informational only |
| 3.11 / 3.14 full-population recompute | Subset (4 programs) only | `SBG_REPO=<copy> python reproduction/recompute_scores.py run --design v10 --split test --python /opt/homebrew/bin/python3.11` |
| `run_repro.sh --full` end-to-end | Not run as one command | `reproduction/run_repro.sh --full` (≈ 20 min) |
| `PYTHONHASHSEED` literally unset | Not run; equivalent random-seed runs done | |
| Statistics re-derivation | Out of scope for A2 | Agent A3 |

---

## 11. Supported / unsupported / contradicted

**Supported**
* 533/536 frozen hashes match; every mismatch is explained and disclosed.
* The V10 and V9c-val SBG scored files are reproducible bit-exactly from the committed code on CPython 3.13.5 (EXP-A2-007/008), independent of hash seed, cwd, `re` cache and 84× CPU load.
* The V10 dataset regenerates byte-identically (EXP-A2-012).
* 807 tests pass; 10/10 consistency checks pass; CI is green at HEAD.
* The silent-fallback mechanism exists but fired 0 times on every evaluated population.
* FREEZE_V9 and FREEZE_V10 pins have not changed since their freeze commits.

**Unsupported**
* "Frozen before scoring" for V10 as a git-enforced fact (self-attested, single commit `c5bc130`).
* Independence of the 35/35 check (mostly document string matches).
* Results on any interpreter other than 3.13.x.
* Third-party reproducibility from the README (the headline path is undocumented).
* 3.13.15 as the interpreter version.
* Hash-pinning of `sbg/v2/execution/runner.py` and ten reporting scripts.

**Contradicted**
* Prior audit's "CI red" at HEAD: CI is green.
* Prior audit's "7 vs 10 open": fixed in `9bed2f0`; only one stale file remains (report 01 §7).
* `FINAL_PREMANUSCRIPT_RELEASE_CHECK.md` treats the gap as open in its body and as resolved in its §8, so it contradicts itself.
* `FREEZE_V8.base_programs_tree_sha256` name versus content (it is over `fresh_programs`).
* "py3.13.15" versus the 3.13.5 actually used.

---

## 12. Tree integrity

Final re-hash (EXP-A2-018): the REPO tree vs `logs/sbg_tree_sha256_BEFORE.txt` (16,137 entries, excluding `.git`, `__pycache__`, `.pyc`, `.DS_Store`) gives **0 changed, 0 missing**. Five extra files exist, all in the gitignored `SBG/.pytest_cache/` (mtime 14 Nov 18:34); A2 used `-p no:cacheprovider` on copies only, so they are not attributed to A2. HEAD is still `3425693`.

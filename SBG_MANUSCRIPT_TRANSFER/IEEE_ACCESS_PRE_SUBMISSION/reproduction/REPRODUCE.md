# REPRODUCE.md — SBG reproducibility package (written by Agent A2, audited commit `3425693`)

Everything below was executed by A2 on macOS 26.6.2 / Apple M4 Max (14 cores, 36 GB) with CPython **3.13.5**
(`venvs/py313`, stdlib + pytest 9.x only). Nothing here writes inside the `SBG/` repository and nothing rewrites a frozen artifact.

## 0. One command

```bash
cd IEEE_ACCESS_PRE_SUBMISSION
reproduction/run_repro.sh --quick      # ~2.5 min: hash audit + clean checkout + 10/10 + 35/35 + V10 and V9c-val score recompute
reproduction/run_repro.sh --full       # ~20 min: adds the 807-test pytest suite and the tracer-sensitivity subset
```
Env overrides: `REPO=<path to SBG>`, `PY=<python 3.13>`, `OUT=<output dir>`. The driver exits non-zero if any expected value below is not met.
The only file it overwrites outside `$OUT` is the scratch result of the hash verifier
(`results/raw/repro/hash_verification.{json,tsv}`, a deterministic function of the repo).

## 1. Expected results (all observed by A2; EXP ids in `logs/registry/A2_repo.jsonl`)

| Step | Command (from `IEEE_ACCESS_PRE_SUBMISSION/`) | Expected output | Runtime | EXP |
|---|---|---|---|---|
| Hash pins | `PYTHONHASHSEED=0 venvs/py313/bin/python reproduction/verify_hashes.py` | `533 MATCH / 3 MISMATCH` of 536 pins; the 3 mismatches are the disclosed `FREEZE_V8` `evaluate_v8.py` (×2, expected `8e567b8c…`, actual `34f303af…`; Amendment 1) and `FREEZE_V8_AMENDMENT2` `run_chunked_sha256` (expected `32a9eb05…`, actual `7d8e67ff…`; pinned by `FREEZE_V9`). 5 of 6 combined/tree digests verify; `FREEZE_V10.variants_tree_sha256` (`f22f0c6c…`) cannot be reproduced (algorithm undocumented). 16-hex prefix manifests: 49 match, 2 mismatch (`docs/CLAIMS_REGISTRY.yaml`). | 15 s | A2-001 |
| Git history | `python reproduction/git_history_audit.py` | only the V8 pins changed after their freeze commit; V9/V10 pins: 0 later commits | 20 s | A2-002 |
| Clean checkout | `git -C SBG archive HEAD \| tar -x -C <dir>` | 15,038 tracked files; no untracked file is needed for tests | 5 s | A2-004 |
| Test suite (py313, `PYTHONHASHSEED=0`) | `cd <clean> && venvs/py313/bin/python -m pytest sbg/ tests/ -p no:cacheprovider -q -rfEs` | **807 passed, 0 failed, 0 skipped, 3 warnings** | 399 s | A2-004 |
| Consistency gate | `python experiments/final/consistency_check.py` (clean copy) | `10/10 checks passed` (C1–C10) | 0.4 s | A2-005 |
| Trace verifier | `python experiments/final/verify_trace_v4.py` (clean copy) | `35/35 trace checks passed` (a doc-vs-artifact string check) ; `verify_trace_v3.py` → 31/31 | 1 s | A2-005 |
| Fast reproduction | `python experiments/final/check_reproduction.py --strict` (clean copy ONLY: it overwrites artifacts in place) | pass; 2 lines differ only in the allowed `threshold_provenance` string | ~1 min | A2-005 |
| CI scientific-integrity job (py311) | `reproduction/ci_emulation.sh /opt/homebrew/bin/python3.11 <copy> <pristine copy>` | all 4 generators rc 0, 3 CI-tracked artifacts byte-identical, 10/10, `tests/test_integrity.py` 25 passed | 30 s | A2-006 |
| **V10 score recompute** | `PYTHONHASHSEED=0 venvs/py313/bin/python reproduction/recompute_scores.py run --design v10 --split test --out $PWD/results/raw/repro/recompute_v10 --workers 3` then `… compare --design v10 --split test --dir …` | **644/644 pairs bit-identical to `artifacts/final/pairs_v10_test_v6exp.jsonl`** (641 evaluated + 3 unevaluated); 0 of 102,718 cross-label orderings change; 0 timeouts | 40 s (3 workers), 89 s CPU | A2-007 |
| **V9c-val score recompute** | same, `--design v9c --split val` | **436/436 pairs bit-identical** to `pairs_v9c_val_output_free_v8.jsonl` + `pairs_v8val_output_free_v8.jsonl`; 0 of 47,088 orderings change; 2 timeouts in the one non-terminating file `math_lis_length__sc3+sp6_s1_j16.py` (= the 1 documented `nonterminating` failure) | 70 s (3 workers); `math_lis_length` alone 74 s | A2-008 |
| V10 dataset regeneration | `PYTHONHASHSEED=0 python benchmark/scripts/generate_v10_independent.py` (clean copy ONLY) | all 646 files (644 variants, `pairs_test.jsonl`, `manifest.json`) byte-identical to the committed ones; `pair_file_sha256` identical | 601 s | A2-012 |
| Sensitivity subset | `reproduction/sensitivity_driver.sh` | 3.13: 140/140 pairs bit-identical under hash seeds {0, 1, 12 random draws (3 runs × 4 programs)}, cwd=/tmp, `re.purge` never/always/per-pair, 28/56/84 competing busy processes; **3.9.6: 82/140 differ** (max |Δsbg_v5| 0.999) | ~7 min | A2-009/010 |
| Python 3.9 recompute | `… run --python venvs/py39/bin/python` | V10: 299/614 evaluated pairs differ (max Δ 0.53), 3,837 of 93,942 cross-label orderings flip; `math_fib_matrix` aborts the interpreter (`Fatal Python error: _Py_CheckRecursiveCall`) | 60 s | A2-010 |
| Python 3.11 / 3.14 subset | `… run --python /opt/homebrew/bin/python3.11` (and `python3.14`) `--programs ds_ranked_set,sort_radix_sort_lsd,graph_topological_kahn,sort_stooge_sort` | 3.11.15: 65/140 pairs differ (max Δ 0.990; 319/4830 orderings flip; pooled AUROC 0.841→0.898). 3.14.5: 2/140 differ (`sort_stooge_sort__sc11+sp3_s1` 0.759→0.072, `…sp4_s1` 0.777→0.0; 84/4830 flip; AUROC 0.841→0.828) | ~30 s each | A2-017 |

## 2. Why the headline numbers reproduce — and what they depend on

* Scores are a deterministic function of (program file, protocol, interpreter). On CPython 3.13.5 they were bit-identical across
  `PYTHONHASHSEED` ∈ {0, 1, 12 random draws}, working directory, `re.purge()` policy, and up to 84 busy-loop processes on 14 cores
  (the 1 s trace timeout never fired). They are **not** invariant to the interpreter minor version (exact reproduction only on 3.13.x; 3.11.15 and 3.14.5 also differ on the 4-program subset): 3.9.6 moves 43–49 % of the evaluated pair distances (V9c-val 187/434, V10 299/614 with one program aborting).
* `recompute_scores.py` re-extracts every program with the frozen `experiments/final/extraction.py` (protocol `output_free_v8`,
  `N_RUNS=5, MAX_EVENTS=5000, trace timeout 1 s, program budget 60 s, MAX_TIMEOUTS=2, seed 42`), scores pairs with `score_pair`
  (0.50·d_V3 + 0.25·d_temporal + 0.25·d_state) and compares with the committed scored files key by key (`sbg_v5, sbg_v3, sbg_temporal,
  sbg_state, exception_fraction, exception_component_v3, exception_type_jaccard, call_count, n_functions, coverage_size, combined_shortcut, v5_full`).
* Statistics (AUROC, bootstrap, Holm) are **not** recomputed here (Agent A3). Because the scored files are reproduced exactly,
  `evaluate_v10.py` / `evaluate_v9.py` (pinned by `FREEZE_V10` / `FREEZE_V9`) will produce the same numbers from them.
* `evaluate_v10.py run` and `evaluate_v9.py run --split val` *refuse* to re-run unless the output is deleted — by design. To verify them
  without touching the frozen result, run them on a clean copy after deleting the output there.

## 3. Things you must not do in `SBG/` (overwrite risks)

| Command | Overwrites |
|---|---|
| `python experiments/final/check_reproduction.py [--strict]`, `make check-reproduction`, `make reproduce-fast` | `artifacts/final/HARD_NEGATIVE_V5_RESULTS.json`, `REGRESSION_V5_RESULTS.json` in place; never restores them (the regenerated `threshold_provenance` text differs from the committed one) |
| `make tables / figures / readme / verify-artifacts / check` | `docs/generated/*`, `docs/figures/*`, `README.md` results block, `benchmark/benchmark_manifest.json`, `artifacts/final/ARTIFACT_PROVENANCE.json`, `BENCHMARK_VALIDITY_AUDIT.json` |
| `make reproduce-v5 / reproduce-output-free / v7-* / reproduce-v7 / quixbugs / bugsinpy / java` | `artifacts/final/pairs_*`, `programs_*`, result JSONs for those splits |
| `python benchmark/scripts/generate_v10_independent.py`, `generate_v9_composed.py` | the frozen dataset directories (regeneration was byte-identical for V10 on a copy) |
| `python experiments/final/evaluate_v8.py run … --allow-overwrite-never-use` | frozen V8 result |

## 4. Known non-reproducible / unverifiable items

1. `FREEZE_V10.variants_tree_sha256` — undocumented algorithm (hundreds of candidates tried, none matches). Per-file integrity is carried by the pinned `pairs_test.jsonl` and, now, by byte-identical regeneration (A2-012).
2. Four untracked files `artifacts/final/{pairs_dev,pairs_v8dev,programs_dev,programs_v8dev}_output_free_v8.{jsonl,json}` are read by `zero_score_population.py` and listed in `EXPERIMENT_MANIFEST.json`; they are not in git, so the all-split zero-score population table is not regenerable from a clone. No headline H1–H6 depends on them.
3. COBOL inventory (`cobol_inventory.py`) reads `/Users/manassakthivel/Desktop/COBOLSRC` (outside the repo).
4. `requirements-lock.txt` / `external/bugsinpy/manifest.json` claim CPython 3.13.15; every freeze file says 3.13.5 and A2 reproduced everything on 3.13.5 (venv). Treat "3.13.15" as a documentation error until the author states otherwise.

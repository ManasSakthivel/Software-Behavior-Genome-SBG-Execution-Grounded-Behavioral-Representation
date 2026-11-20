# Phase 2 reproduction guide (local, exploratory)

Scope: re-running the Phase 2 experiments E1 and E3-E7 on the existing 321 non-pristine development pairs, macOS only. Nothing here reproduces a confirmatory, independent, Linux or published-tool-comparison result, because none exists. E2 (hash-order sensitivity) is not part of this guide: it was not run.

Reference run: 2026-11-18, engine commit `a6afa639` (implementation `5efcef74`; `git diff 5efcef74 HEAD -- sbgv7 tests` is empty), CPython 3.13.15, macOS 26.7 arm64 (Apple M4 Pro). Pre-registration: [`reports/phase2/E3_E7_PROTOCOLS.md`](../reports/phase2/E3_E7_PROTOCOLS.md) and [`reports/phase2/LOCAL_EXPERIMENT_RERUN_MATRIX.md`](../reports/phase2/LOCAL_EXPERIMENT_RERUN_MATRIX.md); summary in [`EXPERIMENT_PROTOCOL.md`](EXPERIMENT_PROTOCOL.md).

## 0. Rules (all experiments)
1. Use NEW output directories under `results/repro/` (gitignored). Never write into `results/raw`, `results/processed`, `results/postfix`, `results/statistics` or `artifacts/`.
2. One experiment at a time, nothing else CPU-heavy running: per-run limits (2 CPU-s, 5 s wall) and the 60 CPU-s budget make `resource_limit` timing dependent, and `test_no_stray_processes` reads the process table. Prefer mains power.
3. Before each run record `git rev-parse HEAD`, `python --version`, `sw_vers`, `sysctl machdep.cpu.brand_string hw.ncpu hw.memsize` and the exact command in a `RUN_RECORD.md` in the output directory; confirm `git status` shows no change under `results/` or `artifacts/`.
4. Environment: `OMP_NUM_THREADS=1 PYTHONHASHSEED=0` (the child hash seed is pinned by the engine regardless of the parent).
5. Setup: `python3.13 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt numpy scipy pandas matplotlib`.

## 1. E1: K2 determinism re-measurement (about 16 min)
```bash
E1=results/repro/p2_e1_$(date +%Y%m%d_%H%M%S)
K1_RAW=$E1/raw K1_PROC=$E1/proc .venv/bin/python experiments/v7b/k1_spike.py run
K1_RAW=$E1/raw K1_PROC=$E1/proc .venv/bin/python experiments/v7b/k1_spike.py summarize
.venv/bin/python scripts/e1_analyze.py $E1/proc results/postfix/processed $E1/e1_analysis.json   # reads the old run read-only
for d in $(find $E1/raw -name evidence.jsonl -exec dirname {} \;); do .venv/bin/python -m sbgv7 verify $d; done
```
Expected (reference run): 312 driven and 9 not driven pairs; 1 pair with a QUARANTINED input (old engine: 2); 414/414 directories `"verified": true`. Use the `"verified"` field, not a pipeline exit status.

## 2. E3: detection, false assurance, abstention
Do NOT run `scripts/run_evaluation.sh --full` as is: its first stage is the legacy `pytest tests -q` (V5/V6, unrelated to V7-B), which in the Phase 2 campaign was killed after more than 77 CPU-minutes without finishing. Use the stage sequence that was actually run, recorded in [`results/v7b_phase2_summary/p2_e3_20261118_092700/E3_COMMANDS.sh`](../results/v7b_phase2_summary/p2_e3_20261118_092700/E3_COMMANDS.sh). It is `run_evaluation.sh --full` with the tests stage replaced by `pytest tests/v7 tests/v6`:
```bash
RUN=results/repro/p2_e3_$(date +%Y%m%d_%H%M%S); mkdir -p $RUN
export K1_PROC=$RUN/processed K1_RAW=$RUN/raw/k1_spike BL_RAW=$RUN/raw/baselines POSTFIX_DIR=$RUN OMP_NUM_THREADS=1 PYTHONHASHSEED=0
PY=.venv/bin/python
$PY -m pytest tests/v7 tests/v6 -q                  # reference: 286 passed, 1 skipped
$PY experiments/v7b/k1_spike.py run --arms quixbugs,quixbugs_neg,synthetic,bugsinpy_units --rerun 25
$PY experiments/v7b/k1_spike.py summarize
$PY -m sbgv7.baselines.run run --arms quixbugs,quixbugs_neg,synthetic,bugsinpy_units
$PY -m sbgv7.baselines.run summarize
$PY scripts/build_dev_pairs_csv.py
$PY scripts/analyze_results.py $K1_PROC/dev_pairs_per_system.csv --out $RUN/statistics --reference B1 --seed 42 --boot 10000
$PY scripts/power_actual.py --processed $K1_PROC/dev_pairs_per_system.csv --test V7-B --reference B1 --out $RUN/statistics/power_actual.json
$PY scripts/generate_figures.py
```
Expected headline (reference run): V7-B false assurance 13/106 = 0.123, B1 24/106 = 0.226; detection 0.708 versus 0.774; abstention 122/258 = 0.473; false alarm 0/152 versus 0.303 (46/152). Strict per-pair verdict identity with the E1 run: 321/321.

## 3. E4: ablations; E5: S2 floor
```bash
E4=results/repro/p2_e4_NEW; E5=results/repro/p2_e5_NEW; E3=$RUN; mkdir -p $E4/statistics $E5/statistics
for V in V0 V1 V2 V3 V4 V5; do OMP_NUM_THREADS=1 PYTHONHASHSEED=0 .venv/bin/python experiments/v7b/p2_variants.py run --variant $V --out $E4/$V | tee $E4/$V.log; done
.venv/bin/python experiments/v7b/p2_variants.py csv --e3 $E3 --runs V0=$E4/V0 V1=$E4/V1 V2=$E4/V2 V3=$E4/V3 V4=$E4/V4 V5=$E4/V5 --out $E4/statistics/e4_ablation.csv
.venv/bin/python scripts/analyze_results.py $E4/statistics/e4_ablation.csv --out $E4/statistics/ablation --reference V0 --seed 42 --boot 10000
for F in S2F06 S2F08 S2F09; do OMP_NUM_THREADS=1 PYTHONHASHSEED=0 .venv/bin/python experiments/v7b/p2_variants.py run --variant $F --out $E5/$F | tee $E5/$F.log; done
```
The remaining `csv`/`analyze_results.py` calls for E4 (ungated) and E5 (versus B1, floors) are in `reports/phase2/E3_E7_PROTOCOLS.md` sections E4 and E5. Expected: no verdict value or level changes in E4 (one reason code moves); E5 S2 counts 71/55/43.

## 4. E6: runtime (about 30-45 min, sequential, battery off)
```bash
E6=results/repro/p2_e6_NEW; mkdir -p $E6
.venv/bin/python scripts/p2_e6_runtime.py records --src E3=$E3 V0=$E4/V0 --out $E6/records.json
.venv/bin/python scripts/p2_e6_runtime.py select --out $E6/subset.json
.venv/bin/python scripts/p2_e6_runtime.py timing --out $E6/timing --reps 5
```
Absolute times depend on the machine; the reference ratios are V7-B/B1 about 1.6 (wall) and V7-B/B1+rep about 1.02. Repeat once if the load average at start or end exceeds 1.5 (pre-registered rule).

## 5. E7: verification and corruption suite
```bash
.venv/bin/python scripts/p2_e7_verify.py run --out results/repro/p2_e7_NEW --src E3=$E3/raw/k1_spike E1=$E1/raw --workers 2
```
Expected: every directory exits 0 (828 in the reference run); 42 corruption cases behave as listed in the protocol (including the documented non-detections: re-chained forgery, deleted `verdict.json`).

## 6. Consolidation
`.venv/bin/python scripts/p2_consolidate.py build --out results/repro/p2_consolidated_NEW --e1 ... --e3 ... --e4 ... --e5 ... --e6 ... --e7 ... --postfix results/postfix` (read-only on its inputs).

## 7. Documentation checks (CPU-light)
```bash
.venv/bin/python scripts/check_docs_v7b.py
make verify-docs-v7b
.venv/bin/python -m pytest tests/v7/test_second_stage.py -q -k tamper_proof
```

## 8. Where the reference outputs are
Compact tracked summaries: [`results/v7b_phase2_summary/`](../results/v7b_phase2_summary). Raw per-run evidence (about 470 MB, about 27,000 files) is outside git in `~/Desktop/SBG-V6-phase2-raw-archive/*.tar.gz` (sha256 in `results/v7b_phase2_summary/RAW_ARCHIVE_SHA256SUMS.txt`; verify with `shasum -a 256 -c`). Reproduction is judged by verdict counts and the pre-registered consistency rule (at most 3 differing pairs of 321 between same-engine runs), not by byte equality: witness ids can depend on timing near resource limits.

## 9. Known deviations in the reference campaign
The first E3 attempt was killed in the legacy pytest stage; a second aborted on a docs-wording guard that has since been fixed; the reported E3 run uses the stage sequence above. E6 tripped the load rule and was run twice; the machine was on battery. These are recorded in the `RUN_RECORD.md` files and the consolidated analysis, section 9.

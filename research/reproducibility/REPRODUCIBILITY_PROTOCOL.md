# Reproducibility protocol (V7-B, exploratory development evaluation)

Status: describes how the existing exploratory results can be regenerated and checked. It does not describe a confirmatory study; none exists. All data are non-pristine.

## 1. Environment
| Item | Value used for the committed results | Evidence |
|---|---|---|
| OS | macOS (Darwin 25.6), single machine | `research/security/EXECUTION_ISOLATION_AUDIT.md` |
| Interpreter | CPython 3.13.15 in `.venv` | `requirements-lock.txt` |
| Libraries | stdlib for `sbgv7/`; numpy 2.5.5, scipy 1.18.1, pandas 3.1.1, matplotlib 3.11.2, pytest 9.2.0 in `.venv` for analysis, figures, tests (`requirements-lock.txt` pins only the pytest side; the analysis libraries are not pinned there) | `.venv/bin/python -c "import numpy,scipy,pandas,matplotlib"` |
| Isolation | `sandbox-exec` (macOS only). Linux/Docker: not implemented, not tested | audit |

## 2. Determinism controls
- `OMP_NUM_THREADS=1`, `PYTHONHASHSEED=0`, at most 4 worker processes (set by `experiments/v7b/k1_spike.py` and `scripts/run_evaluation.sh`).
- Seeds: bootstrap and sign-flip `42`, power simulation `20261117`, B3 mutation baseline `1001`.
- Evidence log: content-addressed, hash-chained `evidence.jsonl` per pair; `records.read_log` verifies the chain.
- Observed determinism: the K1 spike re-ran a subset (139 pairs) and every verdict, level, reason and witness id was identical (`results/processed/k1_spike_summary.json`, `determinism` fields; confirmed by the red-team review).
- Not controlled: wall/CPU times vary by machine and load; V7-B CPU is child-process only; memory was not recorded.

## 3. Pipeline (each stage is a script, all stages are run by `scripts/run_evaluation.sh`)
1. `pytest tests` (V7-B tests are in `tests/v7`; the rest are legacy V5/V6 tests).
2. `experiments/v7b/k1_spike.py run` then `summarize`: V7-B on the 321 development pairs via `python -m sbgv7 compare`.
3. `python -m sbgv7.baselines.run run` then `summarize`: baselines B1, B1+rep, B2, B3 (B4, B5 derived in `summarize`).
4. `scripts/build_dev_pairs_csv.py`: one CSV row per (pair, system); truth is never relabelled.
5. `scripts/analyze_results.py` (project-cluster bootstrap B=10000, seed 42, Holm) and `scripts/power_actual.py`.
6. `scripts/generate_figures.py`.
Output of a reproduction run goes to `results/repro/<mode>_<timestamp>/`; committed `results/` files are never overwritten by the script.

## 4. What counts as reproduced
- Exact: verdict, sufficiency level, primary reason and witness id per pair; counts per verdict (e.g. QuixBugs 27 DIVERGENT / 4 INSUFFICIENT).
- Tolerance: bootstrap CIs (same seed should match to numeric precision on the same numpy/scipy; a different library version may shift them); CPU seconds (hardware dependent).
- A diff in verdict counts against `results/processed/k1_spike_summary.json` is a failure to reproduce and must be reported, not tuned away.

## 5. Not reproducible / not available
- Any confirmatory result: none exists (no sealed holdout; K1 not met; K5 not met).
- Linux or container isolation results: not implemented.
- Published-tool baselines (Testora, DiffTestGen, Mokav, shadow symbolic execution): not run.
- The 2 pre-existing non-V7-B results quoted in the old README (V5/V6 AUROC) are reproduced by the legacy `make` targets, not by this protocol (see `docs/README_pre_v7b.md`, `Makefile`).
- Manuscript compilation: no LaTeX toolchain was available; the manuscript was not compiled.

## 6. Known hazards
- `experiments/v7b/k1_spike.py` and `sbgv7/baselines/run.py` open their per-pair JSONL in append mode. Re-running into `results/processed/` duplicates rows; use the `K1_PROC`, `K1_RAW`, `BL_RAW` overrides (the script does) to write elsewhere.
- `tests/v7/test_isolation.py::test_no_stray_processes` inspects the process table and fails if another V7-B run is active on the same machine. Run tests when nothing else is running.
- `make readme` (legacy) splices generated text into `README.md`; the current README is hand-written, so do not run it.

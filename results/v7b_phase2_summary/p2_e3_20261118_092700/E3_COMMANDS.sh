#!/usr/bin/env bash
# E3 stages = scripts/run_evaluation.sh --full minus the legacy `pytest tests -q` stage (killed after 77 CPU-min; unrelated V5/V6 tests).
# Deviation (documented): tests stage replaced by `pytest tests/v7 tests/v6` (the --quick set). Everything else identical to --full.
set -euo pipefail
RUN="$(cd "$(dirname "$0")" && pwd)"; cd "$RUN/../../.."; PY="$PWD/.venv/bin/python"
export K1_PROC="$RUN/processed" K1_RAW="$RUN/raw/k1_spike" BL_RAW="$RUN/raw/baselines" POSTFIX_DIR="$RUN" OMP_NUM_THREADS=1 PYTHONHASHSEED=0
st(){ echo; echo "=== [$1] ${*:2}"; t=$SECONDS; "${@:2}"; echo "=== [$1] OK in $((SECONDS-t)) s"; }
st tests "$PY" -m pytest tests/v7 tests/v6 -q
st spike "$PY" experiments/v7b/k1_spike.py run --arms quixbugs,quixbugs_neg,synthetic,bugsinpy_units --rerun 25
st spike-summary "$PY" experiments/v7b/k1_spike.py summarize
st baselines "$PY" -m sbgv7.baselines.run run --arms quixbugs,quixbugs_neg,synthetic,bugsinpy_units
st baselines-sum "$PY" -m sbgv7.baselines.run summarize
st pairs-csv "$PY" scripts/build_dev_pairs_csv.py
st analysis "$PY" scripts/analyze_results.py "$K1_PROC/dev_pairs_per_system.csv" --out "$RUN/statistics" --reference B1 --seed 42 --boot 10000
st power "$PY" scripts/power_actual.py --processed "$K1_PROC/dev_pairs_per_system.csv" --test V7-B --reference B1 --out "$RUN/statistics/power_actual.json"
st figures "$PY" scripts/generate_figures.py
echo "E3 DONE"

#!/usr/bin/env bash
# Reproduce the V7-B exploratory development evaluation end to end.
#   scripts/run_evaluation.sh --dry-run   preflight + print every stage command, execute nothing
#   scripts/run_evaluation.sh --quick     tests + QuixBugs-only spike/baselines (~minutes) + analysis + figures
#   scripts/run_evaluation.sh --full      all 321 pairs, all baselines (long: tens of minutes; macOS only)
# Output goes to a NEW directory results/repro/<mode>_<timestamp>/ and never overwrites committed results/.
# Any failing stage aborts the script with a non-zero exit. Nothing is skipped silently:
# stages a mode does not run are printed as NOT RUN with the reason.
set -euo pipefail

MODE="${1:-}"
case "$MODE" in --dry-run|--quick|--full) ;; *) echo "usage: $0 --dry-run|--quick|--full" >&2; exit 2;; esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
STAMP="$(date +%Y%m%d_%H%M%S)"
RUN="$ROOT/results/repro/${MODE#--}_$STAMP"
START=$SECONDS
trap 'rc=$?; echo "FAILED (exit $rc) at line $LINENO in mode $MODE; output dir: $RUN" >&2' ERR

die() { echo "ERROR: $*" >&2; exit 1; }

# ---- preflight (always, including --dry-run) ----
[ "$(uname -s)" = "Darwin" ] || die "macOS required: isolation uses sandbox-exec; no Linux path exists (see README Limitations)"
command -v sandbox-exec >/dev/null || die "sandbox-exec not found"
[ -x "$PY" ] || die "$PY missing: python3.13 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt numpy scipy pandas matplotlib"
"$PY" -c 'import sys; assert sys.version_info[:2]==(3,13), sys.version' || die "CPython 3.13 required in .venv"
"$PY" -c 'import pytest, numpy, scipy, pandas, matplotlib' || die "missing python packages (pytest numpy scipy pandas matplotlib)"
for f in experiments/v7b/k1_spike.py sbgv7/baselines/run.py scripts/build_dev_pairs_csv.py scripts/analyze_results.py \
         scripts/power_actual.py scripts/generate_figures.py external/quixbugs/manifest.json external/bugsinpy/manifest.json \
         results/processed/dev_pairs_per_system.csv; do
  [ -e "$f" ] || die "required file missing: $f (see datasets/README.md)"
done
echo "preflight OK (mode $MODE)"

# ---- stage plan ----
if [ "$MODE" = "--full" ]; then
  ARMS="quixbugs,quixbugs_neg,synthetic,bugsinpy_units"; RERUN=25; BLONLY=""; BOOT=10000; TESTS="tests"
else
  ARMS="quixbugs"; RERUN=0; BLONLY="--only B1,B1rep,B2"; BOOT=500; TESTS="tests/v7 tests/v6"  # legacy V5/V6 suite takes >10 min
fi
export K1_PROC="$RUN/processed" K1_RAW="$RUN/raw/k1_spike" BL_RAW="$RUN/raw/baselines" POSTFIX_DIR="$RUN"
export OMP_NUM_THREADS=1 PYTHONHASHSEED=0

stage() { # name, command...
  local name="$1"; shift
  echo; echo "=== [$name] $*"
  if [ "$MODE" = "--dry-run" ]; then echo "(dry-run: not executed)"; return 0; fi
  local t=$SECONDS; "$@"; echo "=== [$name] OK in $((SECONDS-t)) s"
}

[ "$MODE" = "--dry-run" ] || mkdir -p "$K1_PROC" "$RUN/statistics"
echo "output dir: $RUN"

# shellcheck disable=SC2086
stage tests          "$PY" -m pytest $TESTS -q
stage spike          "$PY" experiments/v7b/k1_spike.py run --arms "$ARMS" --rerun "$RERUN"
stage spike-summary  "$PY" experiments/v7b/k1_spike.py summarize
# shellcheck disable=SC2086
stage baselines      "$PY" -m sbgv7.baselines.run run --arms "$ARMS" $BLONLY
stage baselines-sum  "$PY" -m sbgv7.baselines.run summarize
stage pairs-csv      "$PY" scripts/build_dev_pairs_csv.py
stage analysis       "$PY" scripts/analyze_results.py "$K1_PROC/dev_pairs_per_system.csv" --out "$RUN/statistics" --reference B1 --seed 42 --boot "$BOOT"
stage power          "$PY" scripts/power_actual.py --processed "$K1_PROC/dev_pairs_per_system.csv" --test V7-B --reference B1 --out "$RUN/statistics/power_actual.json"
stage figures        "$PY" scripts/generate_figures.py

if [ "$MODE" = "--dry-run" ]; then
  echo; echo "dry-run executed NOTHING beyond preflight (plan shown is the --quick plan)."
elif [ "$MODE" != "--full" ]; then
  echo
  echo "NOT RUN in $MODE (reason: scope limited to the QuixBugs arm, baselines B1/B1+rep/B2 only):"
  echo "  legacy tests outside tests/v7 and tests/v6; arms quixbugs_neg, synthetic, bugsinpy_units; baselines B3 (mutation loop), B4/B5 beyond what summarize derives; 25-pair determinism re-runs."
  echo "  Numbers from this run are NOT comparable with results/ and must not be cited."
fi
echo; echo "DONE mode $MODE in $((SECONDS-START)) s; output: $RUN"

#!/bin/bash
# A2 one-command reproducibility driver.   Never writes inside the SBG repository and never rewrites a frozen artifact:
#   * hash verification reads REPO (read-only);
#   * everything that can write (pytest, consistency_check, verify_trace) runs on a throw-away `git archive HEAD` copy;
#   * score recomputation imports SBG code by sys.path insertion (PYTHONDONTWRITEBYTECODE=1) and writes only under $OUT.
#
# Usage:   reproduction/run_repro.sh [--quick | --full]        (default --quick, ~6 min;  --full adds pytest (~7 min), sensitivity (~10 min))
# Env:     REPO (default ../SBG)  PY (default ../venvs/py313/bin/python)  OUT (default results/raw/repro/run_<timestamp>)
set -u
HERE=$(cd "$(dirname "$0")" && pwd); PKG=$(cd "$HERE/.." && pwd)
REPO=${REPO:-$PKG/../SBG}; PY=${PY:-$PKG/../venvs/py313/bin/python}; PY39=${PY39:-$PKG/../venvs/py39/bin/python}
MODE=${1:---quick}; TS=$(date +%Y%m%d_%H%M%S); OUT=${OUT:-$PKG/results/raw/repro/run_$TS}; WORK=${WORK:-$HERE/work_$TS}
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT" "$WORK"; LOG="$OUT/run_repro.log"; fail=0
say() { echo "[$(date +%T)] $*" | tee -a "$LOG"; }
chk() { if [ "$1" = "$2" ]; then say "  OK   $3 (= $2)"; else say "  FAIL $3: got '$1', expected '$2'"; fail=1; fi; }

say "interpreter: $($PY --version 2>&1)  (canonical 3.13.5; requirements-lock.txt claims 3.13.15 -- see report 09 §environment)"
say "REPO HEAD : $(git -C "$REPO" rev-parse --short HEAD)  (audited: 3425693)"
say "REPO dirty: $(git -C "$REPO" status --porcelain --untracked-files=no | wc -l | tr -d ' ') tracked-file changes (expected 0)"

say "STEP 1  independent SHA-256 verification of every freeze/manifest pin (read-only; ~15 s)"
"$PY" "$HERE/verify_hashes.py" --repo "$REPO" > "$OUT/verify_hashes_stdout.txt" 2>&1
tail -n 40 "$OUT/verify_hashes_stdout.txt" | grep -E "MATCH|MISMATCH" | head -3 | tee -a "$LOG"
M=$("$PY" -c "import json;print(json.load(open('$PKG/results/raw/repro/hash_verification.json'))['summary']['totals']['MATCH'])")
chk "$M" "533" "pins matching (expected 533 of 536; the 3 mismatches are the disclosed FREEZE_V8 evaluate_v8.py x2 and AMENDMENT2 run_chunked.py)"

say "STEP 2  clean checkout (git archive HEAD) -> $WORK/co"
mkdir -p "$WORK/co" && git -C "$REPO" archive HEAD | tar -x -C "$WORK/co"
cd "$WORK/co" || exit 2
export SBG_REPO="$WORK/co"      # recompute_scores.py imports the code and reads frozen scored files from the CLEAN COPY

say "STEP 3  consistency gate on the clean copy (expect 10/10, ~1 s)"
"$PY" experiments/final/consistency_check.py > "$OUT/consistency_check.txt" 2>&1; tail -1 "$OUT/consistency_check.txt" | tee -a "$LOG"
chk "$(tail -1 "$OUT/consistency_check.txt")" "10/10 checks passed" "consistency_check"

say "STEP 4  verify_trace_v4 on the clean copy (expect 35/35; NOTE: a doc-vs-artifact string check, not an independent verification)"
"$PY" experiments/final/verify_trace_v4.py > "$OUT/verify_trace_v4.txt" 2>&1; tail -2 "$OUT/verify_trace_v4.txt" | tee -a "$LOG"
grep -q "35/35" "$OUT/verify_trace_v4.txt" && say "  OK   35/35" || { say "  FAIL 35/35 not found"; fail=1; }

say "STEP 5  recompute V10 (19 programs, 644 pairs) and V9c-val (11 programs, 436 pairs) scores from the clean-checkout code; exact equality vs frozen scored files"
for spec in "v10:test:recompute_v10" "v9c:val:recompute_v9cval"; do
  IFS=: read D S N <<< "$spec"
  "$PY" "$HERE/recompute_scores.py" run --design $D --split $S --out "$OUT/$N" --workers 3 > "$OUT/$N.log" 2>&1
  "$PY" "$HERE/recompute_scores.py" compare --design $D --split $S --dir "$OUT/$N" > "$OUT/$N.compare.txt" 2>&1
  R=$("$PY" -c "import json;j=json.load(open('$OUT/$N/COMPARE.json'));t=j['totals'];print(t['rows'],t['exact']+t['evaluated_equal'],t['differing']+t['evaluated_flag_diff'],j['cross_pairs_order_changed'])")
  say "  $D/$S rows exact differing order_flips = $R"
  case $D in v10) chk "$R" "644 644 0 0" "V10 recompute";; v9c) chk "$R" "436 436 0 0" "V9c-val recompute";; esac
done

if [ "$MODE" = "--full" ]; then
  say "STEP 6  full pytest on the clean copy, py313 (expect 807 passed, 3 warnings, ~6.5 min)"
  "$PY" -m pytest sbg/ tests/ -p no:cacheprovider -q -rfEs > "$OUT/pytest_py313.log" 2>&1; tail -n 3 "$OUT/pytest_py313.log" | tee -a "$LOG"
  grep -q "807 passed" "$OUT/pytest_py313.log" && say "  OK   807 passed" || { say "  FAIL 807 passed not found"; fail=1; }
  say "STEP 7  tracer sensitivity subset (hashseed random x3, py39, cwd, re.purge, CPU load) -- see reproduction/sensitivity_driver.sh (~7 min)"
  OUT_S="$OUT/sens" bash "$HERE/sensitivity_driver.sh" >> "$LOG" 2>&1
fi
say "DONE  fail=$fail  outputs in $OUT   (clean copy $WORK can be deleted)"
exit $fail

#!/usr/bin/env bash
# WP-D / D2 Task D: rerun experiments/final/diagnose_bugsinpy_cache.py on a fresh copy (writes into the COPY's artifacts/).
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
cd "$D2"
[ -d runs/D_diag_bugsinpy_cache ] || cp -R sbg_copy runs/D_diag_bugsinpy_cache
python3 "$W/scripts/d2_run.py" --tag D2_diagnose_bugsinpy_cache_py313 --timeout 3000 --cwd "$D2/runs/D_diag_bugsinpy_cache" -- \
  "$S/venvs/py313/bin/python experiments/final/diagnose_bugsinpy_cache.py --workers 2"

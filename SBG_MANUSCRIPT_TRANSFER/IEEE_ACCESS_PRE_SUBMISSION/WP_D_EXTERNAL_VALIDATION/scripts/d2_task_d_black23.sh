#!/usr/bin/env bash
# WP-D / D2 Task D: black23 cold-start probe, cwd = the copy root (the 420 s run from cwd=D2 timed out, rc 124).
# usage: d2_task_d_black23.sh SEED LABEL
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
R=$D2/runs/D_cold_start_py313
python3 "$W/scripts/d2_run.py" --tag "D1_cold_${2}_black23_cwdcopy" --timeout 1500 --cwd "$R" --env "PYTHONHASHSEED=$1" -- \
  "$S/venvs/py313/bin/python $W/scripts/d2_cold_start_probe.py $R 3 external/bugsinpy/units/black__23__black_py__assert_equivalent/fixed.py"

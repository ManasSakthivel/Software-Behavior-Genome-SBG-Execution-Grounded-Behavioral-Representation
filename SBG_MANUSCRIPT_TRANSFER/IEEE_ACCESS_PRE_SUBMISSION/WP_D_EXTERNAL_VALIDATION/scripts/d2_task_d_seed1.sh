#!/usr/bin/env bash
# WP-D / D2 Task D: quick cold-start probes with PYTHONHASHSEED=1 and a second seed-0 repeat (units that finished < 25 s).
set -u
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
R=$D2/runs/D_cold_start_py313
for cfg in "seed1:1" "seed0b:0"; do
  lab=${cfg%%:*}; seed=${cfg##*:}
  for u in "black21 external/bugsinpy/units/black__21__black_py__dump_to_file/fixed.py" \
           "youtube_dl37 external/bugsinpy/units/youtube_dl__37__youtube_dl_utils_py__uppercase_escape/fixed.py" \
           "powerset external/quixbugs/correct_python_programs/powerset.py"; do
    set -- $u
    python3 "$W/scripts/d2_run.py" --tag "D1_cold_${lab}_$1" --timeout 420 --env "PYTHONHASHSEED=$seed" -- \
      "$S/venvs/py313/bin/python $W/scripts/d2_cold_start_probe.py $R 3 $2"
  done
done

#!/usr/bin/env bash
# WP-D / D2 Task C: BugsInPy `score --protocol output_free_v7` under other interpreters (one process each).
# Two chains run in parallel (2 heavy processes). Each uses its own verified copy of SBG/.
set -u
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
cd "$D2"
[ -d runs/C_py313_repeat ] || cp -R sbg_copy runs/C_py313_repeat
bp() {  # tag copy python
  python3 "$W/scripts/d2_run.py" --tag "C_bugsinpy_score_$1" --timeout 5400 --cwd "$D2/runs/$2" -- \
    "$3 experiments/final/external_bugsinpy.py score --protocol output_free_v7"
}
( bp py39 C_py39 $S/venvs/py39/bin/python; bp py314 C_py314 /opt/homebrew/bin/python3.14 ) &
( bp py311 C_py311 /opt/homebrew/bin/python3.11; bp py313_repeat C_py313_repeat $S/venvs/py313/bin/python ) &
wait

#!/usr/bin/env bash
# WP-D / D2 Task D: cold-start probes, ONE UNIT PER PROCESS (v1 of this script, all 5 units in one process,
# hit the 1200 s timeout with no output -> see D1_cold_probe_seed0_runA in command_log.jsonl, rc 124).
# usage: d2_task_d_probes.sh SEED RUNLABEL
set -u
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
P=$S/venvs/py313/bin/python
R=$D2/runs/D_cold_start_py313
seed=$1; lab=$2
cd "$D2"
run() { # name unit
  python3 "$W/scripts/d2_run.py" --tag "D1_cold_${lab}_$1" --timeout 420 --env "PYTHONHASHSEED=$seed" -- "$P $W/scripts/d2_cold_start_probe.py $R 3 $2"
}
run powerset external/quixbugs/correct_python_programs/powerset.py &
run youtube_dl37 external/bugsinpy/units/youtube_dl__37__youtube_dl_utils_py__uppercase_escape/fixed.py &
wait
run black21 external/bugsinpy/units/black__21__black_py__dump_to_file/fixed.py &
run ansible_control external/bugsinpy/units/ansible__11__lib_ansible_modules_network_ios_ios_banner_py__map_obj_to_commands/fixed.py &
wait
run black23 external/bugsinpy/units/black__23__black_py__assert_equivalent/fixed.py

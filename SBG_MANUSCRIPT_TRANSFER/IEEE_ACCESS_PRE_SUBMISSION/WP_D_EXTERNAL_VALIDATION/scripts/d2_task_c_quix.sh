#!/usr/bin/env bash
# WP-D / D2 Task C: QuixBugs CANONICAL regime re-scoring (protocol output_free_v7) across interpreters and
# PYTHONHASHSEEDs, using d2_quix_driver.py (calls the repository's own `worker` per program).
# Each configuration: fresh output file; copy roots are verified-identical copies of SBG/.
set -u
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
cd "$D2"
run() {  # tag copy python seed
  local tag=$1 copy=$2 py=$3 seed=$4
  python3 "$W/scripts/d2_run.py" --tag "C_quix_canonical_$tag" --timeout 3000 --env "PYTHONHASHSEED=$seed" -- \
    "$py $W/scripts/d2_quix_driver.py $D2/runs/$copy $py canonical $D2/runs/$copy/quix_canonical_rows_$tag.jsonl 2"
}
run py311_seed0        C_py311                     /opt/homebrew/bin/python3.11  0
run py314_seed0        C_py314                     /opt/homebrew/bin/python3.14  0
run py313_seed0_repeat1 B2_quix_score_py313        $S/venvs/py313/bin/python     0
run py313_seed0_repeat2 B2_quix_score_py313        $S/venvs/py313/bin/python     0
run py313_seed1        B2_quix_score_py313         $S/venvs/py313/bin/python     1
run py313_seed2        B2_quix_score_py313         $S/venvs/py313/bin/python     2
run py39_seed0_repeat1 C_py39                      $S/venvs/py39/bin/python      0
run py39_seed1         C_py39                      $S/venvs/py39/bin/python      1

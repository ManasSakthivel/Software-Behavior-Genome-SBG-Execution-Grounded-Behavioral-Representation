#!/usr/bin/env bash
# WP-D / D2 Task C: compare BugsInPy reruns (other interpreters) vs committed and vs B1 (py313 3.13.5).
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
P=$S/venvs/py313/bin/python
COMMITTED=$S/SBG/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl
B1=$D2/runs/B1_bugsinpy_score_py313/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl
cd "$D2"
for v in C_py39 C_py311 C_py314 C_py313_repeat; do
  N=runs/$v/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl
  python3 "$W/scripts/d2_run.py" --tag "C_cmp_bp_${v#C_}_vs_committed" --timeout 300 -- "$P $W/scripts/d2_compare_scores.py bugsinpy $COMMITTED $N compare/C_bp_${v#C_}_vs_committed"
  python3 "$W/scripts/d2_run.py" --tag "C_cmp_bp_${v#C_}_vs_B1py313" --timeout 300 -- "$P $W/scripts/d2_compare_scores.py bugsinpy $B1 $N compare/C_bp_${v#C_}_vs_B1py313"
done

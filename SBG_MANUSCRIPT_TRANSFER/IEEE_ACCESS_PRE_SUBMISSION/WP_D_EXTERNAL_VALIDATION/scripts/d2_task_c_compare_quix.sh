#!/usr/bin/env bash
# WP-D / D2 Task C: compare every QuixBugs-canonical re-scoring against (i) the committed v7 pairs and
# (ii) the py313 seed0 rerun B2 (cross-version AUROC delta). Own stdlib comparison code.
set -u
S=/Users/manassakthivel/Desktop/SBG-FINALREVIEW
W=$S/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
D2=$W/raw/WPD-D2_repro
P=$S/venvs/py313/bin/python
COMMITTED=$S/SBG/artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl
B2=$D2/runs/B2_quix_score_py313/artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl
cd "$D2"
for pair in "py39:runs/C_py39/quix_canonical_rows.jsonl" "py39_seed0_repeat1:runs/C_py39/quix_canonical_rows_py39_seed0_repeat1.jsonl" \
            "py39_seed1:runs/C_py39/quix_canonical_rows_py39_seed1.jsonl" \
            "py311_seed0:runs/C_py311/quix_canonical_rows_py311_seed0.jsonl" "py314_seed0:runs/C_py314/quix_canonical_rows_py314_seed0.jsonl" \
            "py313_seed0_repeat1:runs/B2_quix_score_py313/quix_canonical_rows_py313_seed0_repeat1.jsonl" \
            "py313_seed0_repeat2:runs/B2_quix_score_py313/quix_canonical_rows_py313_seed0_repeat2.jsonl" \
            "py313_seed1:runs/B2_quix_score_py313/quix_canonical_rows_py313_seed1.jsonl" \
            "py313_seed2:runs/B2_quix_score_py313/quix_canonical_rows_py313_seed2.jsonl"; do
  tag="${pair%%:*}"; f="${pair##*:}"
  python3 "$W/scripts/d2_run.py" --tag "C_cmp_quix_${tag}_vs_committed" --timeout 100 -- \
    "$P $W/scripts/d2_compare_scores.py quixbugs $COMMITTED $f compare/C_quix_${tag}_vs_committed" >/dev/null
  python3 "$W/scripts/d2_run.py" --tag "C_cmp_quix_${tag}_vs_B2py313" --timeout 100 -- \
    "$P $W/scripts/d2_compare_scores.py quixbugs $B2 $f compare/C_quix_${tag}_vs_B2py313" >/dev/null
done

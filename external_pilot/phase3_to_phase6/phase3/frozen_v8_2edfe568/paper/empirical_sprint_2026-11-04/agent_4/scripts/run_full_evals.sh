#!/bin/bash
# Transcribed from the interactive commands used on 2026-11-04 (NOT re-executed as a file).
# Creates a throwaway copy of HEAD under this dir; the repo is never written to.
# Usage: bash scripts/run_full_evals.sh   (from agent_4/)  -- then python3 scripts/compare_all.py
set -e
cd "$(dirname "$0")/.."
REPO=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG; P=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs
mkdir -p copy outputs && (cd $REPO && git archive HEAD) | tar -x -C copy
run() { tag=$1; py=$2; seed=$3; rm -rf copy_$tag; cp -R copy copy_$tag
  ( cd copy_$tag
    PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=$seed "$py" -W ignore experiments/final/regression_evaluation.py >/dev/null
    PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=$seed "$py" -W ignore experiments/final/hard_negative_evaluation.py >/dev/null
    mkdir -p ../outputs/$tag && cp artifacts/final/{HARD_NEGATIVE_V5_RESULTS,REGRESSION_V5_RESULTS}.json ../outputs/$tag/ )
  rm -rf copy_$tag; }
run py313       $P/py313/bin/python 0
run py313_rep2  $P/py313/bin/python 0
run py313_seed1 $P/py313/bin/python 1
run py313_seed7 $P/py313/bin/python 7
run py39        $P/py39/bin/python 0
run py39_seed1  $P/py39/bin/python 1
run py311_seed0 /opt/homebrew/bin/python3.11 0
run py312_seed0 $HOME/.pyenv/versions/3.12.10/bin/python 0
run py314_seed0 /opt/homebrew/bin/python3.14 0

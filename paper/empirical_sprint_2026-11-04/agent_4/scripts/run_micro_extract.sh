#!/bin/bash
P=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs
cd "$(dirname "$0")/.."
PROGS="sort_heapsort.py graph_connected_components.py sort_quicksort.py math_fibonacci.py str_run_length_encode.py"
rm -f outputs/micro_extract.jsonl outputs/micro_extract.err
for v in py313 py39; do for seed in 0 1 5; do for proto in output_free_v6 output_free_v7; do
  PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=$seed $P/$v/bin/python -W ignore scripts/micro_extract.py copy $proto $PROGS >> outputs/micro_extract.jsonl 2>>outputs/micro_extract.err
done; done; done

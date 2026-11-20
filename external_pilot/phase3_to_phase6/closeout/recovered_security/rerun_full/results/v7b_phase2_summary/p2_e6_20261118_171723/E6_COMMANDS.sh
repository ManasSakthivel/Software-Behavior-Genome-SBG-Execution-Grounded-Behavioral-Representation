#!/usr/bin/env bash
set -euo pipefail
cd /Users/manassakthivel/Desktop/SBG-V6
export OMP_NUM_THREADS=1 PYTHONHASHSEED=0
.venv/bin/python scripts/p2_e6_runtime.py timing --out results/repro/p2_e6_20261118_171723/timing --reps 5
uptime > results/repro/p2_e6_20261118_171723/load_end.txt
echo "E6 TIMING DONE"

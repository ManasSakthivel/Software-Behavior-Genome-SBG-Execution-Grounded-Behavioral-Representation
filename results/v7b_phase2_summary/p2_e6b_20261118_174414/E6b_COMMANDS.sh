#!/usr/bin/env bash
# E6 repeat (pre-registered: first run had load average 4.81 at start and 1.65 at end, above the 1.5 limit). Waits for 1-min load < 1.5 (max 20 min), records it, then reruns the same timing study.
set -uo pipefail
cd /Users/manassakthivel/Desktop/SBG-V6
export OMP_NUM_THREADS=1 PYTHONHASHSEED=0
for i in $(seq 1 80); do l=$(sysctl -n vm.loadavg | awk '{print $2}'); awk -v l=$l 'BEGIN{exit !(l<1.5)}' && break; sleep 15; done
uptime > results/repro/p2_e6b_20261118_174414/load_start.txt; { echo "commit $(git rev-parse HEAD)"; echo "date $(date -u +%FT%TZ)"; pmset -g batt | head -2; } > results/repro/p2_e6b_20261118_174414/RUN_RECORD.md
.venv/bin/python scripts/p2_e6_runtime.py timing --out results/repro/p2_e6b_20261118_174414/timing --reps 5
uptime > results/repro/p2_e6b_20261118_174414/load_end.txt
echo "E6b DONE"

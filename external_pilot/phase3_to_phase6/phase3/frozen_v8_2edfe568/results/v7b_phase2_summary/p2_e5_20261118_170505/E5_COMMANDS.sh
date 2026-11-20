#!/usr/bin/env bash
set -euo pipefail
cd /Users/manassakthivel/Desktop/SBG-V6
E3=results/repro/p2_e3_20261118_092700; E5=results/repro/p2_e5_20261118_170505
export OMP_NUM_THREADS=1 PYTHONHASHSEED=0
for F in S2F06 S2F08 S2F09; do echo "=== $F"; .venv/bin/python experiments/v7b/p2_variants.py run --variant $F --out $E5/$F > $E5/$F.log 2>&1; echo "$F done"; done
.venv/bin/python experiments/v7b/p2_variants.py csv --e3 $E3 --runs S2F06=$E5/S2F06 S2F08=$E5/S2F08 S2F09=$E5/S2F09 --baselines B1,B1+rep --out $E5/statistics/e5_vs_b1.csv
.venv/bin/python scripts/analyze_results.py $E5/statistics/e5_vs_b1.csv --out $E5/statistics/vs_b1 --reference B1 --seed 42 --boot 10000
.venv/bin/python experiments/v7b/p2_variants.py csv --e3 $E3 --runs S2F06=$E5/S2F06 S2F08=$E5/S2F08 S2F09=$E5/S2F09 --out $E5/statistics/e5_floors.csv
.venv/bin/python scripts/analyze_results.py $E5/statistics/e5_floors.csv --out $E5/statistics/floors --reference S2F08 --seed 42 --boot 10000
echo "E5 DONE"

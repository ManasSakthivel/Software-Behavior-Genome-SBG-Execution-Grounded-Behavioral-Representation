#!/usr/bin/env bash
set -euo pipefail
cd /Users/manassakthivel/Desktop/SBG-V6
E3=results/repro/p2_e3_20261118_092700; E4=results/repro/p2_e4_20261118_154218
export OMP_NUM_THREADS=1 PYTHONHASHSEED=0
for V in V0 V1 V2 V3 V4 V5; do echo "=== $V"; .venv/bin/python experiments/v7b/p2_variants.py run --variant $V --out $E4/$V > $E4/$V.log 2>&1; echo "$V done"; done
.venv/bin/python experiments/v7b/p2_variants.py csv --e3 $E3 --runs V0=$E4/V0 V1=$E4/V1 V2=$E4/V2 V3=$E4/V3 V4=$E4/V4 V5=$E4/V5 --out $E4/statistics/e4_ablation.csv
.venv/bin/python scripts/analyze_results.py $E4/statistics/e4_ablation.csv --out $E4/statistics/ablation --reference V0 --seed 42 --boot 10000
.venv/bin/python experiments/v7b/p2_variants.py csv --e3 $E3 --runs V0=$E4/V0 --baselines B1,B1+rep --out $E4/statistics/e4_ungated.csv
.venv/bin/python scripts/analyze_results.py $E4/statistics/e4_ungated.csv --out $E4/statistics/ungated --reference V0 --seed 42 --boot 10000
echo "E4 DONE"

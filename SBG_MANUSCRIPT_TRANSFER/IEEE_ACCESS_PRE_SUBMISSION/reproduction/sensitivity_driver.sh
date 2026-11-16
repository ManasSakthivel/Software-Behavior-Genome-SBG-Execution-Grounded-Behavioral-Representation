#!/bin/bash
# A2 tracer-sensitivity subset: 4 V10 programs, all their pairs; one factor varied at a time vs the frozen scored file.
PKG=$(cd "$(dirname "$0")/.." && pwd)
PY13=$PKG/../venvs/py313/bin/python; PY39=$PKG/../venvs/py39/bin/python
S=$PKG/reproduction/recompute_scores.py; O=${OUT_S:-$PKG/results/raw/repro/sens}
PROGS=ds_ranked_set,sort_radix_sort_lsd,graph_topological_kahn,sort_stooge_sort
export PYTHONDONTWRITEBYTECODE=1
run() { name=$1; shift; mkdir -p $O/$name; echo "== $name $(date +%T)"; "$@" --design v10 --split test --programs $PROGS --out $O/$name --workers 2 > $O/$name.log 2>&1;
        $PY13 $S compare --design v10 --split test --dir $O/$name > $O/$name.compare.txt 2>&1; }
export PYTHONHASHSEED=0
run baseline_py313_seed0 $PY13 $S run
for i in 1 2 3; do run hashseed_random_$i $PY13 $S run --hashseed random --seed-for-seeds $i; done
run hashseed_unset_note_seed1 $PY13 $S run --hashseed 1
run py39_seed0 $PY13 $S run --python $PY39
run py39_seed_random $PY13 $S run --python $PY39 --hashseed random --seed-for-seeds 7
run cwd_tmp $PY13 $S run --cwd tmp --cwd-path /tmp
run purge_never $PY13 $S run --purge never
run purge_always $PY13 $S run --purge always
run load_28procs $PY13 $S run --load 28 --workers 4
run load_56procs $PY13 $S run --load 56 --workers 4
echo ALLDONE > $O/DONE

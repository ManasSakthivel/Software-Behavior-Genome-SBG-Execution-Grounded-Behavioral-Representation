#!/bin/bash
# A2: emulate .github/workflows/ci.yml jobs on a throw-away copy (never REPO).  Usage: ci_emulation.sh <python> <workdir> <refdir>
PY=$1; W=$2; REF=$3; export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1; cd $W
echo "== python: $($PY --version)"
for s in "benchmark/scripts/observability_audit.py" "experiments/final/output_oracle_leak_audit.py" "benchmark/scripts/build_manifest.py" "experiments/final/artifact_provenance.py"; do
  /usr/bin/time -p $PY $s > /tmp/ci_step.out 2>&1; echo "step $s rc=$?"; tail -2 /tmp/ci_step.out; done
echo "== git diff --exit-code equivalent (CI tracked-artifact drift check)"
for f in benchmark/benchmark_manifest.json artifacts/final/BENCHMARK_VALIDITY_AUDIT.json artifacts/final/OUTPUT_ORACLE_LEAK_AUDIT.json; do
  if diff -q $f $REF/$f >/dev/null; then echo "UNCHANGED $f"; else echo "DRIFT $f"; diff $f $REF/$f | head -8; fi; done
echo "== all files changed vs pristine archive:"; diff -rq $W $REF | grep -v "__pycache__\|\.pyc" | head -20
echo "== consistency_check"; $PY experiments/final/consistency_check.py | tail -3; echo rc=$?
echo "== integrity tests"; $PY -m pytest tests/test_integrity.py -q -p no:cacheprovider 2>&1 | tail -3
echo "== quickstart"; $PY examples/quickstart.py 2>&1 | tail -4

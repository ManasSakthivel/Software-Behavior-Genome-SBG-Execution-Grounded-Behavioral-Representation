#!/usr/bin/env bash
# WP-E: math_gray_code diagnostic reproduction script
set -euo pipefail

export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
PY="/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python"
PKG="/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION"
WP_E="$PKG/WP_E_MATH_GRAY_CODE"

echo "=== Running WP-E Micro Probe (Thread Accumulation & Memory Explosion) ==="
"$PY" "$WP_E/micro_probe_threads.py"

echo "=== Running Full 49-Variant Diagnostic Profiler ==="
"$PY" "$WP_E/run_full_diagnostic.py"

echo "Diagnostic reproduction complete. Results saved in $WP_E/diagnostic_probe_results.json"

#!/usr/bin/env python3
"""
experiments/v3/run_b07_v3_full.py
===================================
Runner for B07-v3 full evaluation with stack overflow protection.

SC-11 mutations create infinite recursion in some variants (wrong variable
used in recursive DFS base case). Python's tracer thread times out after 5s
but deeply recursive programs may overflow the stack before the timeout fires.

This runner increases the process stack size and runs with appropriate guards.
"""
import resource
import sys
import os
import pathlib

# Increase stack size to handle deeply recursive programs
try:
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    new_soft = min(hard, 64 * 1024 * 1024)  # 64MB stack
    if new_soft > soft:
        resource.setrlimit(resource.RLIMIT_STACK, (new_soft, hard))
except (ValueError, AttributeError, resource.error):
    pass  # On macOS, RLIMIT_STACK changes may be restricted

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import after path setup
from baselines.v3.b07_dynamic_v3 import run as run_b07_v3

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pairs", type=int, default=None)
    args = parser.parse_args()
    dev_metrics, test_metrics, threshold = run_b07_v3(max_pairs=args.max_pairs)
    print(f"\n[FINAL] B07-V3 TEST AUROC={test_metrics['auroc']:.4f} "
          f"CI=[{test_metrics['ci_auroc_lower']:.4f},{test_metrics['ci_auroc_upper']:.4f}]")

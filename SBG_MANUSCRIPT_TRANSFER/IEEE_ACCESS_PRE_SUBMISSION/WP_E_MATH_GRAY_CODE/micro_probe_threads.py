#!/usr/bin/env python3
"""WP-E Isolated Micro-Benchmark & Failure Mechanism Proof.
Demonstrates the exact mechanism of math_gray_code runaway thread accumulation.
"""
import sys
import os
import pathlib
import time
import threading
import resource

REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from experiments.final import extraction as ex
from sbg.extraction.dynamic.tracer import Tracer, _WorkerThread

def get_max_rss_mb():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return rss / (1024 * 1024)
    return rss / 1024

def main():
    print("=== MECHANISM PROBE: math_gray_code runaway worker threads ===")
    
    # 1. Inspect the mutants
    sc4_path = REPO / "benchmark/datasets/v9_composed/variants/train/math_gray_code__sc4+sp2_s0_j3.py"
    sc5_path = REPO / "benchmark/datasets/v9_composed/variants/train/math_gray_code__sc5+sp2_s1_j4.py"
    
    print(f"Testing mutant SC-4: {sc4_path.name}")
    print(f"Testing mutant SC-5: {sc5_path.name}")
    
    # 2. Check active threads before
    t_before = threading.active_count()
    rss_before = get_max_rss_mb()
    print(f"Initial active threads: {t_before}, RSS: {rss_before:.2f} MB")
    
    # 3. Trace mutant with 1.0s timeout per trace
    t0 = time.time()
    res = ex.extract_program(str(sc4_path), {}, "output_free_v8")
    t1 = time.time()
    
    t_after = threading.active_count()
    rss_after = get_max_rss_mb()
    
    print(f"Extraction result: ok={res.ok}, failure_kind={res.failure_kind}, failure_detail={res.failure_detail}")
    print(f"Time taken: {t1-t0:.2f}s")
    print(f"Active threads after extraction: {t_after} (diff: +{t_after - t_before})")
    print(f"RSS after extraction: {rss_after:.2f} MB (diff: +{rss_after - rss_before:.2f} MB)")
    print(f"Stats: {res.stats}")

    print("\nThread inventory:")
    for th in threading.enumerate():
        print(f"  Thread: name={th.name}, daemon={th.daemon}, alive={th.is_alive()}")

if __name__ == "__main__":
    main()

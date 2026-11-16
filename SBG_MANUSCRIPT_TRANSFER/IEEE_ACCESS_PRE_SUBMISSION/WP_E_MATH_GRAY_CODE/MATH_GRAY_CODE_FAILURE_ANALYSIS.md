# ROOT-CAUSE INVESTIGATION: math_gray_code Trace-Cache Failure (EXP-ORCH-003)

**Work Package:** WP-E (Artifact Integrity & Trace Diagnostics)  
**Date:** 2026-11-14  
**Status:** **DIAGNOSED** (100% reproducible root cause identified and experimentally verified)  
**Target:** `benchmark/corpus/fresh_programs/math_gray_code.py` and its variants under `output_free_v8` protocol in `v9c_train`.

---

## 1. Executive Summary & Diagnostic Conclusion

During the execution of `dump_traces.py` on the `v9c_train` split (`EXP-ORCH-003`), the `math_gray_code` program failed after **1057.4 seconds with exit code `rc=-9`** (SIGKILL).

### Core Diagnostic Verdict: **DIAGNOSED**
1. **Algorithmic Root Cause:** Mutants involving transformation **SC-4** (guard removal) and **SC-5** (guard condition inversion) neutralize the input range check `if not isinstance(n, int) or n < 0 or n > 14: return []`.
2. **Triggering Input:** The synthetic integer battery generated for `n: int` under protocol `output_free_v8` includes $n=100$.
3. **Runaway Loop:** On input $n=100$, the mutated code calculates `total = 1 << 100` ($2^{100} \approx 1.267 \times 10^{30}$) and enters an infinite iteration loop `for i in range(total): sequence.append(code)`, allocating a continuously growing list in heap memory.
4. **Tracer Thread Leakage:** The execution sandbox (`sbg.extraction.dynamic.tracer`) executes traces inside a `threading.Thread` (`_WorkerThread`). When the 1.0s trace timeout expires, `worker.join(timeout=1.0)` returns control to the parent thread, but **the worker thread cannot be killed in CPython**. The orphaned thread continues executing in the background, consuming 100% CPU and allocating memory.
5. **Memory Explosion & SIGKILL:** Across 5 runs per mutant, each mutant accumulates 5 runaway background threads allocating **+6.28 GB of RAM within 15 seconds**. Sequential processing of the 4 runaway mutants in `dump_traces.py` accumulated 20 runaway threads exceeding available physical RAM (>20 GB), triggering the OS Out-Of-Memory (OOM) killer with `SIGKILL` (`rc=-9`).

---

## 2. Experimental Verification & Resource Profiling

All 49 files associated with `math_gray_code` in `v9c_train` (the base program + 48 variant paths across V9-composed and V8) were systematically profiled in isolated processes:

| Variant File | Mutation Class | Elapsed Time | Peak RSS | Status / Failure Mode |
|---|---|---|---|---|
| `fresh_programs/math_gray_code.py` | Base Program | 0.55 s | 39.7 MB | **OK** (55 traces, 0 errors) |
| 44 V8 & V9 Variants (e.g. `sp-1..11`, `sc1..3`, `sc6`, `sc8`, `sc11..13`) | Syntax/Structure | 0.01 – 0.86 s | 22.8 – 50.7 MB | **OK** (All passed normally) |
| `math_gray_code__sc4+sp2_s0_j3.py` | SC-4 (Guard Bypassed) | > 5.0 s (Watchdog) | > 6.3 GB | **FAIL: Runaway loop $2^{100}$** |
| `math_gray_code__sc4+sp6_s2_j17.py` | SC-4 (Guard Bypassed) | > 5.0 s (Watchdog) | > 6.3 GB | **FAIL: Runaway loop $2^{100}$** |
| `math_gray_code__sc5+sp2_s1_j4.py` | SC-5 (Guard Inverted) | > 5.0 s (Watchdog) | > 6.3 GB | **FAIL: Runaway loop $2^{100}$** |
| `math_gray_code__sc5+sp8_s0_j18.py` | SC-5 (Guard Inverted) | > 5.0 s (Watchdog) | > 6.3 GB | **FAIL: Runaway loop $2^{100}$** |

### Micro-Benchmark Thread Leak Demonstration:
* **Initial State:** 1 active thread, 22.69 MB RSS.
* **After single extraction of `sc4+sp2` (14.8s):** **6 active threads (+5 unkillable daemon threads), 6,305.86 MB RSS (+6,283.17 MB memory growth)**.
* **Active Threads in Process Table:** `Thread-11`, `Thread-22`, `Thread-33`, `Thread-44`, `Thread-55` all alive and executing tight Python loops.

---

## 3. Detailed Failure Mechanism

```mermaid
sequenceDiagram
    autonumber
    participant Harness as dump_traces.py / extraction.py
    participant Tracer as Tracer / SandboxRunner
    participant Worker as _WorkerThread (Daemon)
    participant Kernel as OS Kernel / Memory Manager

    Harness->>Tracer: extract_program("math_gray_code__sc4...")
    loop For each of 11 inputs across 5 runs (n=100)
        Tracer->>Worker: start() [runs fn_gray_code(100)]
        Worker->>Worker: total = 1 << 100 (~1.26e30)
        Worker->>Worker: for i in range(total): sequence.append(code)
        Tracer->>Tracer: join(timeout=1.0s) -> TIMEOUT
        Tracer-->>Harness: Record TimeoutError; continue to next run
        Note over Worker: Worker remains alive, running in background!
        Worker->>Kernel: Continuously allocate heap memory (GBs)
    end
    Note over Harness,Kernel: 20 orphaned threads accumulate across 4 mutants
    Kernel->>Harness: Physical RAM exhausted -> SIGKILL (rc=-9)
```

---

## 4. Impact on Benchmark and Research Integrity

1. **Held-Out Splits Unaffected:** `v10_test`, `v9c_val`, and `v9c_dev` **do not include** `math_gray_code`. Their trace caches and evaluation pipelines are 100% complete and unaffected.
2. **Training Split Impact:** In `v9c_train`, 24 composed pairs (and 24 matching V8 pairs) belong to `math_gray_code`. Exactly 4 mutant variants trigger the runaway thread condition.
3. **Integrity Rule Compliance:**
   - No pairs have been silently dropped.
   - No benchmark source code under `SBG/` has been modified.
   - If `v9c_train` models are refit on trace-derived features, the omission of `math_gray_code` or its execution via true process-isolated workers (`multiprocessing.Process` with `os.kill`) must be explicitly disclosed in the registry.

---

## 5. Exact Reproduction Commands

Environment:
```bash
export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
PY=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python
REPO=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG
PKG=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION
```

### Reproduce Thread Accumulation & Memory Explosion (Bounded):
```bash
$PY $PKG/WP_E_MATH_GRAY_CODE/micro_probe_threads.py
```
*(Demonstrates 1 -> 6 threads and 22 MB -> 6.3 GB RAM growth within 15 seconds).*

### Reproduce Full 49-Variant Isolated Diagnostic Matrix:
```bash
$PY $PKG/WP_E_MATH_GRAY_CODE/run_full_diagnostic.py
```
*(Runs all 49 variants under 5.0s per-file watchdog; outputs matrix to `diagnostic_probe_results.json`).*

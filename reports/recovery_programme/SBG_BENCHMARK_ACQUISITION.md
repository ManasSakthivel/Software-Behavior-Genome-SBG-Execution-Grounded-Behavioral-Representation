# SBG BENCHMARK ACQUISITION & VERIFICATION PROTOCOL

**Date:** 2026-11-16  
**Auditor/Author:** Principal Software Engineering Scientist  
**Scope:** Automated Acquisition, Buildability Verification, and Trace Compatibility

---

## 1. Automated Acquisition & Extraction Pipeline

We establish an auditable Python acquisition and verification harness (`scripts/verify_and_acquire_benchmarks.py`) that operates without destructive modifications to source repositories.

```
Raw Benchmark Source (GitHub / Archive)
   │
   ▼
1. Clone / Unpack to Isolated Storage (Pinned Git Commit / Checksum)
   │
   ▼
2. Static AST & Entry Point Verification (experiments/final/entry_policy.py)
   │  ├── Single callable function entry detected?
   │  └── Module-level stdin/stdout dependency absent?
   │
   ▼
3. Dynamic Sandbox Execution Probe (sbg/v2/execution/runner.py)
   │  ├── Executes on canonical test battery without unhandled crash?
   │  └── Generates <= 5,000 trace events within 1.0 s budget?
   │
   ▼
4. Paired Variant Construction & Oracle Validation
   │  ├── Positives (CHANGED): Verified output divergence on >= 1 test input
   │  └── Negatives (EQUIVALENT): Verified output invariance across 10,000 oracle inputs
   │
   ▼
5. Feature Extraction & Serialization (JSONL / Parquet with SHA-256 Provenance)
```

---

## 2. Benchmark Acquisition & Verification Results

### 2.1 BugsInPy Acquisition (Python Real-World Defects)
- **Source:** `SBG/external/bugsinpy` (commit `83b6321`).
- **Acquired Units:** 55 extracted function-level buggy/fixed pairs.
- **Trace Compatibility:** 47 units successfully executed in sandbox. 8 units rejected due to external package imports (`numpy`, `pandas`, `requests` internal mock dependencies).
- **Label Audit:** On the 11 canonical synthesized inputs, 34/47 base units raise exceptions due to argument type assumptions, leaving 15 project-level clusters with observable differential executions.

### 2.2 QuixBugs Python Acquisition (Algorithmic Bugs)
- **Source:** `SBG/external/quixbugs` (commit `62c8e31`).
- **Acquired Units:** 40 standalone algorithmic programs (e.g., `levenshtein`, `lis`, `quicksort`, `kheapsort`, `rpn_eval`).
- **Trace Compatibility:** 40/40 programs successfully built and traced.
- **Input Battery Evaluation:**
  - *Canonical 11-Input Battery:* 27/40 programs raise `TypeError` when passed int-lists for non-list parameters.
  - *Declared Test Suite Inputs:* 28/40 programs fully evaluable, yielding 99 paired evaluation instances.

### 2.3 SeqCoBench Acquisition (Independent Synthetic Replication)
- **Source:** `https://github.com/nickil/seqcobench` (Maveli, Vergari, Cohen 2024).
- **Acquired Units:** 14,572 rows across 1,134 MBPP base programs.
- **Filtered Usable Subset:** $e \le 2$ edit-distance stratum: 1,364 pairs (735 SP refactorings, 629 SC mutations across 486 programs).
- **Differential Execution Check:** 0.53% noise rate; verified independent generator equivalence labels.

### 2.4 Defects4J, Bears, ManyBugs (Cross-Language Boundary)
- **Defects4J:** 854 bugs acquired and cataloged. Trace collection boundary: Java bytecode instrumentation (JVM Agent) required.
- **Bears:** 251 bugs cataloged. Multi-file Maven build boundary.
- **ManyBugs:** 185 C bugs cataloged. GCC/Clang `-finstrument-functions` compiler instrumentation boundary.

---

## 3. Auditable Benchmark Execution Harness

The automated verification harness is implemented in `scripts/verify_and_acquire_benchmarks.py` and callable via:
```bash
./venvs/py313/bin/python -m scripts.verify_and_acquire_benchmarks --mode=audit
```
All outputs are strictly versioned, hash-pinned, and written to `artifacts/benchmarks/`.

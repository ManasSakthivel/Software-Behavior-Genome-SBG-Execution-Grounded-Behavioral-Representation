# SBG Trace Quality, Test Adequacy & Activation Audit

**Document ID:** `SBG-V6-INV-TRACE-ADEQUACY-2026-V1`  
**Status:** Investigation / Research Proposal Only  
**Date:** November 16, 2026  
**Auditor:** Principal Program Analysis & Software Testing Specialist  

---

## 1. Trace Quality Assessment Across Evaluated Benchmarks

| Benchmark | Test Input Source | Test Activation Rate | Trace Completeness | Crash / Signal Frequency | Impact on SBG V5 Distance |
|---|---|---|---|---|---|
| **Synthetic V10** | Synthetic Generator (10–20 inputs) | 100% | 100% (Clean loop/recursion) | 12.4% (Explicit bug triggers) | High discriminative accuracy (AUROC = 0.8968) |
| **QuixBugs (Canonical)** | Serialized JSON strings | 32.5% (27/40 crashed on line 1) | < 5% (Truncated at entry) | 67.5% (Harness `TypeError`) | Severely corrupted (AUROC = 0.3587) |
| **QuixBugs (Repaired Native)** | Native Python data structures | 100% (40/40 clean) | 100% (Full execution paths) | 14.2% (Real defect crashes) | Clean behavioral signal (AUROC = 0.8654) |
| **BugsInPy** | Default dummy arguments | 27.6% (13/47 executed) | < 10% (Early returns / raises) | 72.4% (Unbound inputs) | Degenerated to zero distance (AUROC = 0.4099) |
| **SeqCoBench (e<=2)** | Problem assert statements | 100% | 100% | 8.1% | Clean traces; bounded by token baseline |
| **Bugs.jar (Java)** | Unit test fixtures | 100% | 100% | 33.3% (Target exceptions) | Clean traces; bounded by edit baseline |
| **Codeflaws (C)** | Codeforces stdin testcases | 100% | 100% | 0.0% (Logic/Wrong Answer) | Clean traces; diluted by exception weight |

---

## 2. Test Adequacy & Activation Invariants for V6

1. **The Fundamental Pre-Condition for Behavioral Tracing:** Dynamic representations can only extract behavioral differences if the test inputs execute past the function boundary into the modified control-flow graph (CFG) or data-flow edges.
2. **Confidence / Evidence-Weighting Mechanism:** If test inputs fail to execute the modified lines or crash immediately on type mismatches, the trace collector must flag the trace as **"Unactivated / Inadequate Evidence"** rather than emitting a zero distance ($d=0.0$).
3. **Multi-Input Invariant Aggregation:** Instead of averaging point-by-point traces across heterogeneous inputs, V6 should infer universal and existential invariants ($\forall x \in T: \phi(x)$) over test suites.

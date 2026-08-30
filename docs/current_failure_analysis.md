# SBG Current Failure Analysis
## Phase 0 Forensic Audit — Failure Inventory

**Date:** 2025  
**Auditor:** Phase 0 Principal Investigator  
**Status:** Frozen — point-in-time snapshot as of V5 final sprint

---

## Preamble

This document catalogs known failure modes in the SBG system. Failures are classified by type: algorithmic, empirical, oracle/ground-truth, generalization, and infrastructure.

---

## FAILURE CLASS A — Algorithmic / Representation Failures

### A1 — Exception Dominance (CRITICAL)

**Description:** The full behavioral genome (AUROC=0.551) is outperformed by a single feature — `exception_fraction` — which achieves AUROC=0.593. The incremental delta of adding the full SBG over the best shortcut is **-0.043** — the complex representation is actively harmful on the aggregate benchmark.

**Root cause (diagnosed):** The V3 distance function weights `coverage_size` (0.20) and `call_freq` (0.20) heavily. Both are execution-volume statistics that correlate with `exception_fraction`. The multi-dimensional genome does not decorrelate these dimensions; it amplifies the volume proxy rather than complementing it.

**Evidence:** `artifacts/v5/EXCEPTION_FORENSIC_ANALYSIS.json`, `artifacts/v5/INCREMENTAL_INFO_RESULTS.json`

**Status:** UNRESOLVED — multi-view ensemble proposed but not implemented

---

### A2 — Structural-Semantic Inversion (CRITICAL)

**Description:** Semantics-preserving transforms (rename, extract-function, refactor) cause **larger** structural behavioral distances than semantics-changing mutations (off-by-one, operator swap). This is the opposite of what SBG's design assumes.

**Quantification:**  
- SP (semantics-preserving) mean SBG_static similarity: 0.9619  
- SC (semantics-changing) mean SBG_static similarity: 0.9954  
- Delta: +0.0335 (SC is MORE similar to original than SP)

**Root cause:** Structural refactoring (extracting a function, renaming) changes call graphs, coverage vectors, and call frequency distributions. Minor semantic changes (off-by-one in a boundary check) leave these structures unchanged while only changing values.

**Evidence:** `docs/FINAL_SBG_COMPLETION_REPORT.md`, `artifacts/phase4/E1/results.json`

**Status:** PARTIALLY MITIGATED by dynamic features (H9 supported), but aggregate benchmark still affected

---

### A3 — SC-3 Near-Invisibility (HIGH)

**Description:** Operator swap mutations (`>=` vs `>`, `+` vs `-` at boundaries) are detected at only 7.5% rate with canonical inputs. With input-guided boundary execution, this improves to ~24%, but the SC-3 class remains the hardest mutation type.

**Root cause:** SC-3 mutations only affect behavior at exact boundary inputs (e.g., `age=18` for a `>=18` vs `>18` check). Random or typical inputs rarely hit these boundaries. The dynamic tracer cannot distinguish programs that behave identically on all provided inputs.

**Evidence:** `docs/v5/SC3_EXPOSURE_REPORT.md`, `artifacts/v5/SC3_EXPOSURE_RESULTS.json`

**Status:** PARTIALLY MITIGATED — V5 input-guided executor achieves 24%; integration into full pipeline not complete

---

### A4 — SP-2 Rename Sensitivity (HIGH)

**Description:** SBG is supposed to be invariant to function/variable renames (SP-2). The SP-2 benchmark AUROC is 0.259 — far below 0.5, meaning SBG actively predicts renamed programs as MORE different (not less).

**Root cause:** The V3 `anon_call_freq` uses first-call-order anonymization, but the anonymization maps differ between program versions because the function order changes when refactoring. The V5 `invariant_identity.py` fixes this, but the fix is not integrated into the main pipeline.

**Evidence:** `docs/v5/SP2_INVARIANT_DESIGN.md`, `artifacts/v5/SP2_INVARIANT_DESIGN.json`

**Status:** V5 fix exists but NOT INTEGRATED into benchmark evaluation

---

### A5 — Hash-Based Identity for Exception Causality (MEDIUM)

**Description:** The `exception_causality_hash` in V3 uses a SHA-256 prefix of sorted exception context tuples. Distance is binary (0 = same hash, 1 = different hash). This is a coarse comparison that loses gradation — two programs with one different exception context look identical to two programs with all different contexts.

**Root cause:** Architectural choice — binary hash comparison was a shortcut.

**Evidence:** `sbg/v3/genome.py:distance_v3()` lines 527

**Status:** KNOWN LIMITATION — not addressed

---

### A6 — Causal Precedence Computation is O(n²) per Trace (MEDIUM)

**Description:** The causal precedence extraction in `sbg/v5/temporal_genome_v5.py` computes all pairwise ordered pairs for the call sequence — O(n²) in sequence length. For programs with long call sequences (>1000 events), this becomes a bottleneck.

**Root cause:** Double loop over call sequence pairs; no optimized algorithm used.

**Evidence:** `sbg/v5/temporal_genome_v5.py` lines 373-390

**Status:** KNOWN — capped by tracer's 10,000-event limit; unlikely to be blocking in practice

---

### A7 — Regression Evaluation Uses Output Oracle, Not SBG Distance (HIGH)

**Description:** The regression evaluator claims "output oracle 93.3%" but this is `output_divergence`, not the SBG distance function. The `sbg_proxy` score in the evaluator is a manually constructed proxy, not the full V5 pipeline distance.

**Root cause:** The regression evaluator (`experiments/v5/regression_evaluator.py`) computes output divergence directly from return values, which is output-reading — explicitly forbidden by SAFEGUARD-2.

**Evidence:** `artifacts/v5/REGRESSION_EVALUATION_RESULTS.json`, methodology section; `sbg_proxy = 0.40 * volume_ratio + ...` is a hand-weighted proxy

**Status:** CRITICAL FINDING — the 93.3% regression detection number uses an oracle that is NOT the SBG behavioral distance. It uses output comparison.

---

## FAILURE CLASS B — Empirical / Experimental Failures

### B1 — DEV AUROC Below Chance (HIGH)

**Description:** The DEV split AUROC is 0.488, below 0.5 (random). This means the model is actively wrong on dev-set programs, predicting more SP pairs as CHANGED and more SC pairs as EQUIVALENT.

**Diagnosed causes:** Transform distribution mismatch (SC-14 present only in DEV/VAL); small N (9 programs); program family differences.

**Evidence:** `artifacts/v5/CROSS_FORMULATION_ANALYSIS.json`

**Impact:** Raises serious questions about generalizability. Test AUROC (0.546) may be a favorable random fluctuation.

---

### B2 — No Statistical Test for Hard-Negative Results (MEDIUM)

**Description:** The hard-negative result (behavioral oracle 12/12) has no statistical test. With N=12 pairs designed specifically to defeat shortcuts, this cannot be generalized to a distribution.

**Root cause:** Small curated dataset; no distributional sampling.

**Evidence:** `benchmark/v5/hard_negatives/oracle.py` output; no p-values reported

---

### B3 — Test Set Has Only 13 Programs (HIGH)

**Description:** The test split covers only 13 base programs. The confidence interval width is ~±0.045 AUROC. Benchmark-level generalization claims cannot be made with 13 programs.

**Evidence:** `artifacts/v5/CROSS_FORMULATION_ANALYSIS.json`, `benchmark/datasets/generation_summary.json`

---

### B4 — Feature Weights Not Principled (MEDIUM)

**Description:** The V3 distance function uses weights (W_cov=0.20, W_seq=0.25, W_freq=0.20, etc.) that were set by manual design reasoning, not learned from data or validated by ablation. Changing these weights significantly changes the AUROC.

**Evidence:** `sbg/v3/genome.py:distance_v3()`, weights documented with rationale but not empirically validated

---

### B5 — Regression Result Not on Held-Out Test Set (HIGH)

**Description:** The 15 regression pairs are a separate hand-crafted corpus, not derived from the main benchmark test set. The "93.3% detection" is on a different distribution than the main benchmark evaluation. These cannot be compared directly.

**Evidence:** `experiments/v5/regression_evaluator.py` creates its own corpus inline

---

## FAILURE CLASS C — Oracle / Ground Truth Failures

### C1 — Synthetic Ground Truth Circularity Risk (HIGH)

**Description:** The ground truth labels (SP vs SC) are generated by applying pre-defined transformation rules. The SBG representation was designed with knowledge of these transformation types. There is a non-trivial risk that the representation is implicitly tuned to the benchmark's specific transform set, not to semantic change detection in general.

**Manifestation:** SBG performs better on some SC types (SC-12, SC-9) than others (SC-3, SC-2). If the benchmark were constructed differently, the performance profile could change substantially.

---

### C2 — Oracle for "Silent Bugs" Uses Output Comparison (CRITICAL)

**Description:** The claim "9/9 silent bugs detected by behavioral comparison" uses `output_divergence > 0` as the detection criterion — not the SBG distance. The "behavioral comparison" in this context is output checking, which is exactly what SAFEGUARD-2 forbids.

**Impact:** If the claim is "output-free SBG detects silent bugs," the evidence does not support this. The evidence supports "output checking detects silent bugs that exception/volume shortcuts miss." This is true but less novel.

---

### C3 — Hard-Negative Pairs Designed by the Same Team (MEDIUM)

**Description:** The 12 hard-negative adversarial pairs were designed by the SBG team to specifically defeat shortcuts. The behavioral oracle (output comparison) then gets credit for detecting them. This is circular: the team knows the ground truth when evaluating the oracle.

**Risk level:** Moderate — the program pair code is available for inspection; an independent replicator could verify

---

## FAILURE CLASS D — Generalization Failures

### D1 — Single Language Only (HIGH)

**Description:** All main benchmark results are Python-only. Java infrastructure exists (3 programs compile and run) but no AUROC was measured. The "language-agnostic" claim is theoretical, not empirical.

**Evidence:** `artifacts/v5/JAVA_INFRASTRUCTURE_DESIGN.json`

---

### D2 — Synthetic Programs Only (HIGH)

**Description:** All 99 base programs are custom-written for this benchmark. No real-world programs from production codebases are included. The distribution of mutations may not match real bug distributions.

**Evidence:** `benchmark/corpus/base_programs/` — all programs are hand-crafted benchmark programs

---

### D3 — No Defects4J Evaluation (HIGH)

**Description:** The formal research hypotheses (RESEARCH_HYPOTHESES.md) require evaluation on Defects4J (395+ real Java bugs). This evaluation has never been conducted. All regression detection results use the 15 hand-crafted pairs.

---

### D4 — Single Training Distribution (MEDIUM)

**Description:** The distance function was designed using observations from this specific benchmark. Performance on programs from different domains (e.g., web servers, data processing pipelines, concurrent systems) is unknown.

---

## FAILURE CLASS E — Infrastructure Failures

### E1 — CPython-Only (MEDIUM)

**Description:** `sys.settrace` is CPython-specific. The entire dynamic extraction pipeline fails on PyPy, Jython, and other Python implementations. This is documented but narrows the applicable scope.

---

### E2 — 5-Second Timeout Truncation (LOW-MEDIUM)

**Description:** Programs exceeding 5 seconds of execution time or 10,000 trace events are truncated. Long-running programs produce incomplete genomes with `truncated=True` flags. The behavior of the distance function on truncated genomes is not formally characterized.

**Evidence:** `sbg/extraction/dynamic/tracer.py` line 102

---

### E3 — Figure Scripts Are Placeholders (LOW)

**Description:** `experiments/v2/figures/fig4_hard_negative.py` and `fig5_robustness.py` are `PLACEHOLDER_PENDING_DATA` — they do not generate actual figures.

**Evidence:** `docs/v5/REPRODUCIBILITY_AUDIT_V5.md` section F

---

### E4 — Dynamic Results Are Hardware-Dependent (LOW-MEDIUM)

**Description:** Execution timing features (`wall_time_ms`, `call_depth_mean` via trace truncation) can vary with hardware. While seed=42 controls pseudorandomness, hardware timing variance can affect truncation behavior for borderline-fast programs.

---

## Summary Table

| ID | Failure | Class | Severity | Status |
|---|---|---|---|---|
| A1 | Exception dominance | Algorithmic | CRITICAL | UNRESOLVED |
| A2 | Structural-semantic inversion | Algorithmic | CRITICAL | PARTIAL |
| A3 | SC-3 near-invisibility | Algorithmic | HIGH | PARTIAL |
| A4 | SP-2 rename sensitivity | Algorithmic | HIGH | V5 FIX UNINTEGRATED |
| A5 | Coarse exception causality hash | Algorithmic | MEDIUM | KNOWN |
| A6 | O(n²) causal precedence | Algorithmic | MEDIUM | LOW RISK |
| A7 | Regression oracle uses outputs | Algorithmic | HIGH | CRITICAL FINDING |
| B1 | DEV AUROC below chance | Empirical | HIGH | UNRESOLVED |
| B2 | No statistics for hard negatives | Empirical | MEDIUM | DESIGN LIMIT |
| B3 | Only 13 test programs | Empirical | HIGH | NEEDS EXPANSION |
| B4 | Weights not principled | Empirical | MEDIUM | KNOWN |
| B5 | Regression not on held-out set | Empirical | HIGH | DESIGN ISSUE |
| C1 | Synthetic ground truth circularity | Oracle | HIGH | SYSTEMIC |
| C2 | Silent bug oracle uses outputs | Oracle | CRITICAL | MISATTRIBUTED |
| C3 | Hard negatives designed internally | Oracle | MEDIUM | TRANSPARENT |
| D1 | Python-only results | Generalization | HIGH | INFRA EXISTS |
| D2 | Synthetic programs only | Generalization | HIGH | SYSTEMIC |
| D3 | No Defects4J evaluation | Generalization | HIGH | ABSENT |
| D4 | Single distribution | Generalization | MEDIUM | SYSTEMIC |
| E1 | CPython-only | Infrastructure | MEDIUM | DOCUMENTED |
| E2 | Timeout truncation | Infrastructure | MEDIUM | DOCUMENTED |
| E3 | Figure placeholders | Infrastructure | LOW | KNOWN |
| E4 | Hardware timing variance | Infrastructure | LOW | DOCUMENTED |

---

*Last updated: Phase 0 Forensic Audit*

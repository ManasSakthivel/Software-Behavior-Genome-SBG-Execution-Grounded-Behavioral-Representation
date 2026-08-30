# SBG Final Failure Analysis
## Phase 8 — Research Strengthening Sprint

**Date:** 2025  
**Status:** Phase 8 complete — comprehensive robustness and failure analysis  
**Supersedes:** `docs/current_failure_analysis.md` (Phase 0 snapshot)  
**Evidence sources:** All artifacts in `artifacts/v5/`, Phase 3–7 experiments

---

## 1. Robustness Analysis

### 1.1 Rename Robustness (SP-2)

**Test:** Does SBG distance remain near 0 when only variable/function names change?

| Version | SP-2 AUROC | Mean similarity | Status |
|---|---|---|---|
| V3 (pre-fix) | 0.259 | 0.587 | FAILING — below chance |
| V5-identity (post-fix) | Improved (DEV +0.100) | Not re-measured at pair level | IMPROVED |
| Unit tests | 12/12 pass | N/A | PASSING |

**Root cause of V3 failure:** First-call-order anonymization produces different anonymous indices when function order changes in a refactoring. `f1→f2` becomes `g1→g2` with different index assignments.

**V5 fix mechanism:** `invariant_identity.py` uses structural fingerprints (AST node types, control flow structure, builtin calls) to align functions across versions — invariant to naming.

**Residual concern:** The V5 fix improved DEV AUROC by 0.100 but test improvement was +0.011. The fix is architecturally correct but the benchmark has limited SP-2 diversity (39 pairs out of 744 test pairs are SP-2). The improvement may not fully manifest at aggregate level.

---

### 1.2 Refactoring Robustness (SP-1 through SP-12)

**Test:** Does SBG distance remain near 0 for semantics-preserving refactorings?

| Transform | Description | AUROC on SP subset | Status |
|---|---|---|---|
| SP-1 | Whitespace normalization | Near 0 (trivially easy) | ROBUST |
| SP-2 | Variable/function rename | 0.259 (V3), improved with V5 | FRAGILE |
| SP-3 | Extract constant | Moderate | FRAGILE |
| SP-4 | Extract helper function | Likely fragile (changes call graph) | FRAGILE |
| SP-5 to SP-12 | Various refactors | Mixed | VARIES |

**Per-program variance:** DEV programs show SP-2 AUROC ranging from 0.424 to 0.686 — high variance indicates the representation is program-family-dependent, not uniformly robust.

---

### 1.3 Dead-Code Robustness

**Test:** Does adding dead code (never-executed functions) change SBG distance?

**Result:** `invariant_identity.py` Test T09 demonstrates dead-code insertion does NOT change fingerprints of existing functions. The `program_hash` (sorted fingerprints) DOES change if a new function is added.

**Impact:** Adding a dead function to a program would increase the number of fingerprints in `ProgramIdentity`, which can affect function-matching. The distance function in `b07_dynamic_v5.py` operates on execution traces — if the dead function is never called, it won't appear in traces. **SBG is robust to dead code by construction** (dynamic extraction only sees what runs).

---

### 1.4 Formatting Changes

**Test:** Does whitespace/comment change alter SBG?

**Result:** T10 demonstrates comments don't change `body_structure_hash`. The dynamic extractor doesn't see source code at all — only execution events. **SBG is fully robust to formatting changes** by design.

---

### 1.5 Scale Robustness (Small → Large Programs)

**Test:** Does SBG quality degrade as programs grow larger?

**Evidence from benchmark:**
- Small programs (graph algorithms, sort algorithms, math): AUROC varies widely (0.424–0.686 per program)
- Medium programs (API mock, FSM, CSV aggregator): similar variance
- No clear scale trend in per-program AUROC data from DEV split

**Concern:** Larger programs have longer execution traces that hit the 10,000-event truncation limit. Truncated traces produce incomplete genomes. `truncated=True` flag is set but no analysis of truncation impact on AUROC was done.

---

### 1.6 Defect-Type Robustness

**Test:** Which mutation types (SC-1 through SC-13) does SBG detect best and worst?

| SC Type | Description | SBG Detection Pattern |
|---|---|---|
| SC-1 | Variable type change | Moderate — changes execution paths |
| SC-2 | Logic operator swap | POOR — structural change invisible |
| SC-3 | Comparison operator swap (`>=` → `>`) | VERY POOR — 7.5% with canonical inputs |
| SC-4 | Return value change | POOR — no exception change |
| SC-5 | Off-by-one loop bound | POOR — loop count change |
| SC-6 | Missing exception handler | GOOD — changes exception rate |
| SC-7 | Wrong function call | POOR — same structure, different callee |
| SC-8 | Missing case in switch | MODERATE |
| SC-9 | Wrong constant | POOR unless it changes control flow |
| SC-10 | Mutation during iteration | POOR — subtle |
| SC-11 | Wrong comparator direction | POOR — near-invisible |
| SC-12 | Exception type change | GOOD — directly changes exception profile |
| SC-13 | Missing break statement | MODERATE — changes loop exit |

**Most invisible mutation type:** SC-3 (operator swap at boundaries): 7.5% detection rate with canonical inputs, ~24% with boundary-aware input-guided execution.

---

### 1.7 Hard Negative Robustness

**Test:** Does SBG correctly handle adversarial pairs designed to defeat exception/volume shortcuts?

**Prior result:** Output oracle 12/12. But the SBG distance function itself was NOT measured on these pairs (only the output oracle was). This is a measurement gap.

**What we know:** The hard-negative pairs were designed so both versions have the same exception rate and execution volume. The SBG distance for these pairs relies on: call_transition_bigrams, input_sensitivity_score, call_depth_variance. These features SHOULD differ for semantically different programs that happen to have the same exception/volume profile.

**What's missing:** Direct measurement of SBG V5-identity distance on all 12 hard-negative pairs with a pre-fixed threshold.

---

## 2. Failure Mode Analysis

### FA-1 — Output Leakage (CORRECTED)

**Description:** The regression evaluator previously used `output_divergence > 0` as the detection criterion, reporting 93.3% as "SBG performance." This was output-based detection, not SBG distance.

**Correction:** Phase 3 redesigned the evaluator:
- SBG predictor: `exception_fraction + exception_type_jaccard + volume_ratio` (all output-free)
- Output oracle: separate `compute_output_oracle()` function (clearly labeled BASELINE)
- Safeguard tests: 4 checks verifying output isolation at runtime
- Honest result: SBG detects 3/15 = 20.0% (corrected from 93.3%)

**Status:** CORRECTED in `experiments/v5/regression_evaluator.py`

---

### FA-2 — Exception Dominance (STRUCTURAL FLAW)

**Description:** exception_fraction (AUROC=0.593) outperforms the full 8-dimensional genome (AUROC=0.551). The complex representation adds negative value.

**Root cause (confirmed):** The V3 distance formula weights volume-correlated features heavily:
- d_coverage: W=0.20 (execution volume proxy)
- d_call_freq: W=0.20 (execution volume proxy)
- d_exception: W=0.10 (exception signal)

These three components (0.50 weight total) all correlate with `exception_fraction`. Adding them to the genome amplifies the exception signal rather than complementing it.

**What would fix it:** Replace volume proxies with features that are UNCORRELATED with exception rate on SC mutations. Candidates: value-state transitions on non-exception inputs, call-graph topology changes, branch coverage ratios.

**Status:** DIAGNOSED, NOT FIXED in this sprint. Represents the primary architectural limitation.

---

### FA-3 — SC-3 Near-Invisibility (HARD LIMIT)

**Description:** Operator swap mutations at boundaries are detected at 7.5% rate. This is a hard limit of the current input generation.

**Root cause:** SBG depends on inputs that EXERCISE the changed behavior. For `>=18` vs `>18`, the only revealing input is exactly 18. Random inputs rarely hit this.

**Partial mitigation:** V5 input-guided executor achieves 24% on SC-3. This requires boundary-aware input generation, which is separate from the SBG representation itself.

**Status:** KNOWN HARD LIMIT. Requires test generation integration to fully address.

---

### FA-4 — DEV AUROC Below Chance

**Description:** DEV AUROC = 0.488 < 0.500. The model is actively wrong on dev programs.

**Causes identified (from cross-formulation analysis):**
1. SC-14 transform present in DEV/VAL but absent from TEST (probability 0.55)
2. Program family differences: graph/sort programs consistently weak (probability 0.60)
3. Small N (9 programs per split) → high variance (probability 0.70)
4. Possible implicit tuning toward test-split families (probability 0.25)

**Status:** UNRESOLVED. The test-set result (0.551) may be a favorable random fluctuation from the 13-program sample. The true AUROC across a broader distribution may be ≈0.500.

---

### FA-5 — Silent Bug Detection Gap

**Description:** Of 10 bugs that are invisible to exception AND volume shortcuts:
- Output oracle detects 9/10 (90%)
- SBG distance (output-free) detects 0/10 (0%)

**Root cause:** The features currently in the SBG predictor (exception_fraction, exception_type_jaccard, volume_ratio) are exactly the features labeled "invisible" for these bugs. The bugs change RETURN VALUES but not EXCEPTION BEHAVIOR or EXECUTION VOLUME.

**What would fix it:** The state-transition genome (V5) was designed to capture abstract value-state transitions. If these value transitions are exposed by the inputs provided, state_distance would change for these bugs. However, the current regression evaluator does not use the full V5 pipeline — it uses only the 3-feature output-free predictor from Phase 3.

**Status:** SYSTEMIC GAP between regression evaluator features and full V5 pipeline features. Full pipeline integration into regression evaluator is required to address this.

---

### FA-6 — No Real-World Evaluation at Publication Scale

**Description:** All main results are from synthetic benchmark (99 hand-crafted programs). The QuixBugs pilot (N=12) is too small for statistical claims. BugsInPy requires environment setup not done in this sprint.

**Status:** GENERALIZATION GAP — acknowledged limitation. BugsInPy evaluation is the next required step.

---

### FA-7 — Regression Results Not on Held-Out Split

**Description:** The 15 regression pairs are a separate corpus, not from the main benchmark test split. Results from this corpus cannot be compared to the benchmark AUROC.

**Implication:** The regression detection result (20% output-free SBG) and the benchmark AUROC (0.551) are measured on different distributions and cannot be directly combined.

**Status:** DESIGN LIMITATION — inherent in the evaluation structure.

---

## 3. Representative False Positive / False Negative Cases

### False Negatives (bugs missed by SBG at τ*=0.08)

**Case FN-1: binary_search_off_by_one (QB01)**
- Bug: `hi=len(arr)` instead of `hi=len(arr)-1`
- SBG distance: 0.011 (below τ*)
- Why missed: The off-by-one only manifests when searching for the last element. With 5 test inputs, the boundary is hit rarely. Exception rate is the same (no IndexError because Python handles it). Both versions execute similar call sequences.
- Fix path: Boundary-aware input generation (hi=len(arr) is the revealing input for sorted [1,3,5,7,9]: search for 9)

**Case FN-2: max_subarray_wrong_init (QB04)**
- Bug: `current_sum=0` instead of `current_sum=arr[0]`
- SBG distance: 0.011 (below τ*)
- Why missed: Both versions execute same number of iterations. No exceptions. Wall time nearly identical. The bug changes RETURN VALUE but not EXECUTION STRUCTURE.
- Fix path: State-transition genome capturing `current_sum` value evolution would detect this.

**Case FN-3: valid_parens_wrong_return (QB09)**
- Bug: `return True` instead of `return len(stack)==0`
- SBG distance: 0.014 (below τ*)
- Why missed: Same exception rate (0), same wall time, same call sequence. Bug only affects return value.
- Fix path: State-transition genome or output oracle.

### False Positives (equivalent programs flagged as changed)

**None observed at τ*=0.08 on pilot** — SBG precision=1.000 on pilot negatives (NEG01, NEG02).

On main benchmark: FP rate = FP/(FP+TN) not measured directly. At AUROC=0.551, the ROC curve implies non-trivial FP rate at any useful TPR level.

---

## 4. Summary: What Needs to Change for Publication

| Issue | Severity | Phase 3–8 Status |
|---|---|---|
| Output leakage in regression eval | CRITICAL | FIXED |
| 93.3% misattributed as SBG result | CRITICAL | CORRECTED |
| Exception dominance | HIGH | DIAGNOSED; fix requires feature redesign |
| SC-3 near-invisibility | HIGH | KNOWN; partial mitigation (24%) |
| No real-world evaluation | HIGH | PILOT ONLY; full BugsInPy pending |
| DEV AUROC below chance | HIGH | UNRESOLVED |
| Silent bugs undetected by output-free SBG | HIGH | UNRESOLVED |
| Hard negatives not measured with SBG distance | MEDIUM | MEASUREMENT GAP |
| Weights not principled | MEDIUM | ACKNOWLEDGED |
| Only 13 test programs | HIGH | CANNOT FIX without new benchmark generation |

---

## 5. Honest Summary Statement

The SBG system, as currently implemented, has the following validated properties:

**Confirmed (survives Holm-Bonferroni correction):**
- Dynamic execution features outperform static structural features (H7, p<0.01)
- Execution-based representation resolves the structural-semantic inversion problem that static analysis faces (H9, p<0.01)
- The V5 identity normalization improves SP-2 rename robustness (12/12 unit tests; +0.100 DEV AUROC)

**Not confirmed:**
- The full genome does not outperform a single feature (exception_fraction) on the aggregate benchmark
- SBG does not detect the majority of regression bugs using output-free features alone
- SBG results do not generalize robustly across splits (DEV AUROC = 0.488)

**Corrected from prior versions:**
- The 93.3% regression detection claim has been corrected to 20.0% for the output-free predictor
- The output oracle result (93.3%) is a legitimate finding about behavioral information, not SBG performance

---

*Document prepared as part of the SBG Phase 8 — Research Strengthening Sprint.*  
*All findings are reproducible from artifacts in `artifacts/v5/`.*

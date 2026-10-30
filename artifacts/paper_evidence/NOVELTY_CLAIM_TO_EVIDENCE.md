# NOVELTY CLAIM TO EVIDENCE
**Branch:** `remediation/sbg-v4`  
**Commit:** `401d16ee006702bd2911e81c6386398d35116f45`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)

---

## Purpose and Scope

This document provides a concise, claim-by-claim assessment of SBG's novelty relative to verified prior work. It is derived from RELATED_WORK_NOVELTY_AUDIT.md and adds a table format that the manuscript author can use directly.

**Important caveats on this literature review:**
- Only papers whose abstracts or full texts were retrieved from arXiv or publisher pages during this session are cited.
- No exhaustive conference-proceedings search was performed.
- The Kessel & Atkinson (2019) paper was identified from its IEEE Xplore listing and Scholar abstract. Its detailed methods were not accessible (server returned 502). The characterisation below is based on the abstract and citation context only.
- No references, DOI values, or venues have been invented.

---

## 1. Closest Prior Work and Actual Contributions

### Paper 1: Danglot et al., "DCI: Detecting Behavioral Changes in CI"

**Full citation:** B. Danglot, M. Monperrus, W. Rudametkin, B. Baudry. "An Approach and Benchmark to Detect Behavioral Changes of Commits in Continuous Integration." *Empirical Software Engineering*, Springer, 2020. DOI: 10.1007/s10664-019-09794-7. arXiv:1902.08482.

**Verified from:** arXiv abstract and HTML. Retrieved 2026-10-30.

**What DCI actually does:**  
- Proposes test-case generation (assertion amplification + input-space search) to detect whether a commit changes observable program behaviour.  
- Constructs a curated benchmark of 60 real commits from 6 Java projects.  
- Measures whether generated tests distinguish pre-commit from post-commit behaviour.  
- Does not produce a continuous similarity score; does not analyse edit-size as a confound; requires existing test suites; Java only.

**What DCI does NOT do:**  
- Does not quantify edit-size confounding in a synthetic benchmark.  
- Does not produce a distance function for ranking pairs.  
- Does not evaluate against edit-size or execution-statistic baselines.

---

### Paper 2: Kessel & Atkinson, "On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence"

**Full citation:** M. Kessel, C. Atkinson. "On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence." *IEEE SCAM 2019*. DOI: 10.1109/SCAM.2019.00019.

**Verified from:** IEEE Xplore title/abstract (server returned 502 on full text); Scholar abstract and citation count (15 citations). Retrieved 2026-10-30.

**What Kessel & Atkinson actually do (based on abstract):**  
- Study whether comparing dynamic execution behaviours can determine if two software systems are functionally equivalent.  
- Examine the question empirically but do not propose a specific multi-component genome representation.  
- Do not evaluate against edit-size baselines; do not address confounding from transformation families.

**Limitation on this characterisation:** Full methodology not independently verified due to access failure. The claimed distinction (SBG adds a structured multi-component representation and edit-size baseline comparison) is plausible but cannot be fully confirmed from abstract alone.

**Risk:** A reviewer familiar with this paper may find the distinction less clear. Manuscript should acknowledge this paper early and explicitly describe what SBG adds that this paper does not.

---

### Paper 3: Krinke & Ragkhitwetsagul, "How the Misuse of a Dataset Harmed Semantic Clone Detection"

**Full citation:** J. Krinke, C. Ragkhitwetsagul. "How the Misuse of a Dataset Harmed Semantic Clone Detection." arXiv:2505.04311. Submitted 7 May 2025.

**Verified from:** arXiv full abstract. Retrieved 2026-10-30.

**What this paper actually does:**  
- Demonstrates that 93% of BigCloneBench Weak Type-3/4 clone pairs do not have similar functionality, making papers that used this dataset for semantic clone detection report inflated F1 scores.  
- Literature review of 179 papers.  
- Does not propose a new behaviour-change detection method.  
- Does not address edit-size confounding in mutation-based datasets.

**Relevance to SBG:** Validates the *motivation* for careful benchmark construction and label validation. Does not compete with SBG's contribution.

---

### Paper 4: Wei et al., "EquiBench: Benchmarking LLMs' Understanding of Program Semantics via Equivalence Checking"

**Full citation:** A. Wei, J. Cao, R. Li, H. Chen, Y. Zhang. "EquiBench: Benchmarking Large Language Models' Understanding of Program Semantics via Equivalence Checking." NeurIPS 2025 Workshop, OpenReview. (openreview.net/forum?id=T6xzZvtEAv, 14 citations as of 2026-10-30.)

**Verified from:** OpenReview page title and abstract excerpt (from Scholar result). Full text not retrieved.

**What EquiBench actually does (from abstract excerpt):**  
- Benchmark for testing whether LLMs can judge program equivalence across four programming tasks.  
- Identifies biases in LLM-based equivalence checking.  
- Does not use execution traces; does not propose a distance function; does not address edit-size confounding.

**Relevance to SBG:** Different approach (LLM vs. execution trace). Not a direct competitor.

---

### Paper 5: Ding et al., "TRACED: Execution-Aware Pre-Training for Source Code"

**Full citation:** Y. Ding, B. Steenhoek, K. Pei, G. Kaiser, W. Le, B. Ray. "TRACED: Execution-Aware Pre-Training for Source Code." *ICSE 2024*. DOI: 10.1145/3597503.3608140. (94 citations as of 2026-10-30.)

**Verified from:** ACM DL abstract. Full text not retrieved.

**What TRACED actually does:**  
- Pre-trains code models on execution state information to improve downstream code intelligence tasks (summarisation, defect detection, etc.).  
- Uses execution traces for neural representation learning.  
- Does not propose an edit-size confound analysis; does not evaluate a distance function for behaviour-change detection on a controlled benchmark.

**Relevance to SBG:** Shares the use of execution traces but is a neural pre-training approach for general code intelligence, not a non-neural distance function for behaviour-change discrimination. Not a direct competitor.

---

## 2. Claim-to-Evidence Table

| SBG claimed contribution | Supported? | Evidence | Prior work that overlaps | Precise distinction | Risk for reviewers |
|---|---|---|---|---|---|
| **Identifies edit-size confounding as a validity threat in transformation-family benchmarks** | ✅ Supported | `LABEL_GENERATION_AUDIT.json`; reversed edit AUROC 0.876 on V8; forward edit AUROC 0.616 on V9/V10 | Krinke & Ragkhitwetsagul (syntactic shortcuts in clone benchmarks, different domain) | SBG identifies the specific mechanism (label bound to transformation family) and quantifies it for behaviour-change detection | Low — this is a concrete, quantified finding |
| **Proposes a composed design that partially decouples edit size from label** | ✅ Supported | `docs/current/EVALUATION_PLAN_V9.md`; V9c/V10 evaluation results | None found in reviewed literature | Specific construction protocol (SC(p) + same SP rewrite against original p); verified reduction in edit AUROC from 0.876 to 0.616 | Low |
| **Demonstrates SBG V5 discriminates above chance on size-decoupled pairs with oracle-validated labels** | ✅ Supported | V9c val AUROC 0.751 (Holm p = 0.002); V10 AUROC 0.897 (Holm p = 0.003) | Kessel & Atkinson (qualitative, no AUROC comparison); DCI (different mechanism) | Quantitative AUROC with pre-registered hypotheses and Holm correction; controlled benchmark | Medium — Kessel & Atkinson overlap; full methods of that paper not verified |
| **SBG V5 outperforms edit-size baselines on size-decoupled pairs** | ✅ Supported | H3: ΔAUROC +0.281 [+0.244, +0.308] (Holm p = 0.005); stratified AUROC 0.875 | None in reviewed literature directly address this comparison | Paired comparison with Holm correction; edit-size-stratified analysis confirming discrimination is not explained by residual edit imbalance | Low |
| **Edit + SBG V5 outperforms edit alone** | ✅ Supported | H2: ΔAUROC +0.254 [+0.218, +0.285] (Holm p = 0.005) | None | Paired comparison with Holm correction | Low |
| **SBG V5 adds incremental value beyond edit + execution statistics** | ❌ Not supported | H4 ΔAUROC +0.006 [−0.069, +0.068], Holm p = 1.0 (V10); +0.021 p = 0.117 (V9c) | — | Null result, documented and preregistered | This is a negative result the paper must report honestly |
| **First use of execution traces for program equivalence / behaviour-change detection** | ❌ Overly broad; do not make this claim | Kessel & Atkinson (2019) and DCI (2020) predate this work | Kessel & Atkinson 2019; DCI 2020 | SBG contributes a specific multi-component representation and controlled benchmark; it is not the first dynamic approach | High — reviewers will find these papers |
| **V10 demonstrates generalisation to independently authored programs** | ❌ Too broad | V10 programs are generated by the same author and generator | — | V10 = withheld programs from same procedure; not independently authored | Medium — if manuscript overstates this |
| **SBG detects real bugs** | ❌ Not supported | BugsInPy 0.497; QuixBugs 0.444 (near chance after correction) | — | Negative result; must be reported | High — this would be a central claim in any application paper |
| **V6 graded abstraction is superior to V5** | ❌ Not supported | H5 Holm p = 0.090 (not rejected); dev ΔAUROC +0.0001 p = 0.918 | — | V6 is experimental; V5 is primary | Low |

---

## 3. Broadness Flags: Claims That Are Too Broad

The following formulations, if used in the manuscript, would be inaccurate or unsupported:

1. **"SBG is the first execution-trace-based approach to program equivalence detection"** — False. Kessel & Atkinson (2019) and DCI (2020) use dynamic execution for equivalence/change detection. Do not make this claim.

2. **"SBG generalises to independently sourced programs"** — Not demonstrated. V10 uses the same generation procedure. Use: "SBG generalises to withheld programs within the same benchmark procedure."

3. **"SBG provides information beyond execution statistics"** — Not supported by H4. Use: "SBG provides information beyond edit size but does not demonstrate additional value beyond edit + execution statistics."

4. **"The zero-score issue has been resolved"** — Incorrect. The zero rate is explained and shown not to be a scorer defect, but the representation limitation (fixed inputs, output-free, coarse abstraction) remains. Use: "The zero-score rate is explained as a combination of correct EQUIVALENT responses and representation limitations; it is not a scorer defect."

5. **"SBG is validated for practical use"** — Not demonstrated. The benchmark is synthetic; real-bug generalisation is not established.

---

## 4. Recommendation for Related Work Section

The manuscript must explicitly position SBG against:

1. **Danglot et al. (DCI, 2020)** — "complementary mechanism (test amplification vs. trace distance); DCI requires existing test suites and produces test cases, not a continuous score; DCI does not address edit-size confounding in synthetic benchmarks."

2. **Kessel & Atkinson (2019)** — "shares the motivation of using dynamic behaviour comparison for equivalence judgement; SBG contributes a specific structured multi-component representation, a controlled benchmark with oracle-validated labels and edit-size decoupling, and a quantitative AUROC evaluation with pre-registered hypotheses." [Note: if full access to that paper is available, the manuscript author should verify this distinction against its actual methods.]

3. **Krinke & Ragkhitwetsagul (2025)** — "independently identifies the problem of benchmark label quality in code similarity; motivates SBG's oracle-validation approach; different domain (clone detection vs. behaviour-change detection)."

4. **The benchmark validity literature broadly** (Yu et al. 2022 on clone benchmarks; Croft et al. 2023 on vulnerability datasets) — positions SBG's confound analysis within a known class of dataset validity threats.

The related work section should not claim exhaustive coverage of execution semantics literature; it should claim precise coverage of the directly relevant comparison points.

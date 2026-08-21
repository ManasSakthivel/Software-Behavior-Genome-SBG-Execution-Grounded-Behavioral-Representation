# Research Question — Software Behavior Genome (SBG)

**Agent:** 0-INTEGRATION  
**Date:** 2025  
**Status:** Phase 0 synthesis — incorporates all six Phase 0 research agent outputs  
**Depends on:** FORMAL_MODEL.md (0B), PRIOR_ART_MATRIX.md (0A), NOVELTY_ANALYSIS.md (0C), THREATS_TO_VALIDITY.md (0D), RESEARCH_HYPOTHESES.md (0E), BENCHMARK_DESIGN.md (0F)

---

## 1. The Precise Research Question (Post-Adversarial-Review)

### 1.1 Primary Research Question

> **Can a formally specified, multi-dimensional, execution-trace-derived behavioral pseudometric detect semantic regressions in software version histories at high recall (≥ 0.80) and acceptable precision (≥ 0.70), without requiring a test suite or formal specification, and generalizing across programming languages by construction?**

This is the sharpened form produced after adversarial review by Agent 0C. It replaces the broader "does a behavioral genome characterize a program?" framing with the specific, falsifiable, and most novel claim the project can defend. See §4 for the full claims/non-claims boundary.

### 1.2 Secondary Research Questions

| ID | Question | Maps to | Nature |
|---|---|---|---|
| RQ1 | Does the behavioral genome remain stable (D < 0.05) under semantics-preserving transformations and sensitive (D > 0.25) under semantics-changing mutations? | H1, H3, SH-1 | Confirmatory |
| RQ2 | Does the structured 8-dimensional SBG outperform single-signal and static-code baselines in regression detection? | H2, H5 | Confirmatory |
| RQ3 | Which refactoring transformation types stress which genome dimensions, and which dimensions are most/least stable? | H3, SH-1 | Confirmatory |
| RQ4 | Can SBG identify semantically equivalent programs across programming languages using language-portable genome dimensions (g_D, g_X, partial g_C)? | H4 (FORMAL_MODEL H3) | Confirmatory-exploratory |
| RQ5 | Does richer input sampling (coverage-guided) improve regression recall, especially for rare-trigger bugs? | H5, SH-2 | Confirmatory |
| RQ6 | Does each genome dimension contribute independent, non-redundant behavioral signal? | H6, SH-1, SH-5 | Confirmatory |
| RQ7 | What is the minimum sample size N* for reliable genome estimation, and does convergence follow O(1/√N)? | SH-3 | Exploratory (addresses OP-1) |
| RQ8 | Do specific dimensions provide dominant signal for specific task categories? | SH-5 | Exploratory |
| RQ9 | Is genome distance locally monotone in syntactic change magnitude? | SH-4, H4 | Exploratory |
| RQ10 | What is the genome collision rate for unrelated programs? | H6-uniqueness | Exploratory |

---

## 2. Irreducible Scientific Contribution

After stripping the "genome" metaphor and accounting for all adversarial attacks (Agent 0C, Attacks 1–10), the irreducible scientific contribution — what no prior work claims or demonstrates — is:

> **A formally specified execution-behavioral pseudometric that detects semantic regressions in software version histories at high recall, without requiring test suites or formal specifications, and that is language-agnostic by construction.**

This rests on **two surviving high-confidence novelty claims** and **two conditional claims**:

### S1 — Formal Behavioral Pseudometric (HIGH CONFIDENCE)
No prior work defines a multi-dimensional, normalized pseudometric on execution-trace-derived behavioral features with formally stated metric properties (Proposition 1: D is a pseudometric), dimension-specific distance justifications (JSD for DATA, Wasserstein for TEMPORAL, GED for CONTROL call graph, etc.), and explicit assumptions (A1–A10). The closest works — TTAnalyze (informal similarity), SYMDIFF (SMT solver, not a pseudometric), Joern/ProGraML (static, no distance function) — do not provide this structure. The formal specification (Definitions 17–18) survives all 10 adversarial attacks.

### S2 — Longitudinal Behavioral Genome Tracking (HIGH CONFIDENCE)
No prior work defines or implements a versioned, queryable record of how a program's full behavioral profile evolves across its entire release history — `{G(P⁽⁰⁾), G(P⁽¹⁾), ..., G(P⁽ⁿ⁾)}` with formal distance tracking. All regression testing compares pairs; no system maintains a cumulative behavioral history (coverage gap CG-1). This claim survives all 10 adversarial attacks without qualification.

### S3 — Test-Suite-Free Regression Oracle (MODERATE — EMPIRICALLY UNPROVEN)
No prior work demonstrates test-suite-free regression detection using unsupervised behavioral distance at the specified recall/precision targets. This is the primary falsifiable hypothesis (H5). Its novelty is acknowledged but contingent on empirical validation. If H5 fails, S1 and S2 remain; the practical impact of SBG is reduced but the formal contribution persists.

### S4 — Cross-Language Behavioral Equivalence Without Shared IR (MODERATE — NARROWER THAN CLAIMED)
All prior cross-language similarity work (CLCDSA, code2vec cross-language) is either static or requires a shared compilation target. SBG's g_X and g_D can detect cross-language behavioral equivalence through observed runtime behavior without a shared IR. **However**, Attack 4 (Agent 0C) established that with g_U excluded, g_T and g_R requiring unsolved normalization (OP-6), and g_C requiring an unsolved procedure alignment mapping (OP-4), the effective cross-language genome is 3–5 dimensions. The claim is credible but must be stated as: *"SBG provides behavioral equivalence evidence on 3–5 dimensions across language families, which is novel; full 8-dimension cross-language comparison is blocked by OP-4 and OP-6."*

---

## 3. Scope Boundaries — Explicit

The following scope restrictions are **mandatory** in any publication and in any Phase 1 experimental design. Violations would undermine the validity of H1–H6.

### In scope
- Single-process, non-interactive programs
- Execution time bounded by T_max = 30 seconds (Assumption A5)
- Deterministic execution under fixed inputs, seeds, and environment (Assumption A6)
- Imperative and object-oriented programming paradigms (C, Java, Python, Go, Rust, C++)
- Programs with no external stateful dependencies (no database, no live network)
- Programs that can be run with shared inputs in a controlled environment

### Out of scope (unmitigable, must be stated as limitations — see §7)
- Long-running servers and daemons (EV-02: trace truncation makes genome incomplete)
- Interactive programs requiring simulated users (EV-02)
- Distributed / microservice programs (violate Definition 2's single-program model)
- Functionally or logically-paradigmed programs — Haskell, Erlang, Prolog (EV-03: g_C call graph is undefined or unstable for HOF/lazy evaluation)
- Programs relying on unseeded randomness, hardware randomness, or network timing without canonical policy enforcement (IV-05: violates A6)
- Full 8-dimension cross-language comparison until OP-4 and OP-6 are resolved (CV-05)

---

## 4. What SBG Claims vs. Does Not Claim

### SBG Claims
1. **The behavioral genome G(P) = (g_C, g_D, g_S, g_R, g_T, g_E, g_X, g_U) is formally defined** as a tuple of 8 dimension-specific feature spaces with a formally specified pseudometric D on the product space. (Definitions 8, 17, 18; Proposition 1.)
2. **D is an empirical approximation to semantic equivalence**, not a decision procedure. D(G₁,G₂) < ε implies *probable* semantic equivalence; it does not prove it. (Remark R7, Rice's theorem, Definition 19.)
3. **The genome is stable under semantics-preserving transformations** for deterministic programs under controlled execution: E[D | equiv_S] < 0.05. (H1, empirically to be validated.)
4. **The genome is sensitive to semantic changes** when the input sample covers regression-triggering inputs: D(Gᵏ, Gᵏ⁺¹) > ε_detect for known-buggy version pairs. (H2/H5, empirically to be validated.)
5. **The 8-dimensional structured distance outperforms single-signal baselines** (coverage alone, syscall-distance alone, static code embeddings) on regression detection. (H2, ablation study required.)
6. **Longitudinal genome tracking constitutes a novel behavioral record** with no prior equivalent.
7. **Cross-language behavioral equivalence evidence is available on g_D, g_X, and partially g_C** without a shared compilation target. (H4, restricted to 3–5 dimensions.)

### SBG Does Not Claim
1. **Does not claim to prove semantic equivalence.** D(G₁,G₂) = 0 does not imply P₁ ≡_S P₂. Full semantic equivalence is undecidable (Rice's theorem).
2. **Does not claim completeness.** Rare-trigger bugs (μ_I(Δ) ≈ 0) may be undetectable under production input distributions regardless of D. There is no guarantee of detecting regressions triggered by adversarially rare inputs under I_prod.
3. **Does not claim full 8-dimension cross-language comparison.** The EXECUTION dimension is explicitly excluded; TEMPORAL and RESOURCE require unresolved normalization (OP-6); CONTROL requires unresolved procedure alignment (OP-4).
4. **Does not claim applicability to non-deterministic programs without a canonical policy.** Concurrent programs, programs using time-seeded RNGs, or programs depending on hardware entropy require additional policy specification (see A6 and IV-05).
5. **Does not claim scalability to large programs without further work.** Graph edit distance for CONTROL is NP-hard; heap graph isomorphism for STATE is GI-hard. Approximate algorithms are required for programs beyond benchmark scale (EV-04).
6. **Does not claim the "genome" metaphor is technically precise.** The word "genome" is used as a motivating analogy only. The technical object is a multi-dimensional behavioral fingerprint with a formally defined pseudometric.
7. **Does not claim generality beyond imperative/OO programs.** Functional and logic paradigms are explicitly out of scope.
8. **Does not claim the 8-dimensional decomposition is optimal.** The ablation study (H6/RQ6) may find that a subset of dimensions suffices for specific tasks; the architecture may be justified on interpretability grounds rather than discriminability grounds.

---

## 5. Hypothesis-to-Experiment-to-Metric Map

The following table is the complete cross-reference between formal model hypotheses, operational research hypotheses, experiments, corpora, and success metrics.

| Formal (FORMAL_MODEL.md) | Operational (RESEARCH_HYPOTHESES.md) | Primary Corpus | Primary Metric | Success Threshold | Falsification Condition |
|---|---|---|---|---|---|
| H1 — Behavioral Genome Stability | H1 — Behavioral Genome Stability | Custom benchmark: 50 programs × 5 SP transforms | E[D \| equiv_S] | < 0.05 | E[D_sp] > 0.10 OR Cliff's delta < 0.4 OR >10% of SP pairs exceed D = 0.05 |
| H2 — Behavioral Genome Sensitivity | H5 — Genome as Regression Oracle | Defects4J v2.0 (395+ pairs) | AUC-ROC, Recall@θ*, Precision@θ* | AUC ≥ 0.80; Recall ≥ 0.80; Precision ≥ 0.70 | AUC < 0.80 OR no θ achieves recall/precision simultaneously OR F1 < 0.70 |
| H3 — Cross-Language Behavioral Equivalence | H4 — Cross-Language Generalization | RosettaCode / OJ dataset: 5 algo classes × 5 language pairs | D_portable (g_D, g_X, partial g_C) vs. CLCDSA AUC | AUC ≥ 0.80; E[D_equiv] < 0.15 | E[D_equiv] > 0.20 OR Mann-Whitney fails at α = 0.0017 |
| H4 — Behavioral Genome Versioning | SH-4 — Monotonicity in Code Change | 10 GitHub projects, ≥ 100 commits each | Spearman ρ(|Δcode|, D) | Median ρ ≥ 0.30, positive on ≥ 7/10 projects | Median ρ < 0.20 OR any project has ρ < 0 |
| H5 — Genome as Regression Oracle | H2 — Structured SBG Outperforms Baselines | Defects4J v2.0 + BigCloneBench | ΔAUC-ROC vs. best static baseline | ΔAUC ≥ 0.05 over CodeBERT/GraphCodeBERT | Any baseline achieves F1 ≥ F1(SBG-8D) at α = 0.0017 |
| H6 — Behavioral Genome Uniqueness | H6 — Multi-Dimensional Value | Defects4J + BigCloneBench + H4 corpus | AUC drop per omitted dimension; collision rate | ΔAUC ≥ 0.03 per omitted dim; collision rate ≤ 1% | Any 6-dim subset achieves equal AUC OR LASSO selects ≤ 5 dims OR any dims have \|r\| > 0.85 |
| — (OP-1) | SH-3 — Genome Convergence Rate | 20 programs; N ∈ {10,25,50,100,200,500,1000} | Convergence exponent α in O(N^α) | α ≤ −0.3; N = 200 sufficient for 80% of programs | α > −0.3 (N = 200 insufficient) |
| — (H2 input dependency) | SH-2 — Input Coverage Governs Sensitivity | Defects4J, stratified by μ_I(Δ) | Recall per stratum: rare/medium/common | Recall(I_cov) > Recall(I_prod) on rare triggers | Recall(I_prod) ≥ Recall(I_cov) on rare-trigger regressions |
| — (H3 refactoring) | H3 — Robustness Under Refactoring | 50 programs × 9 refactoring types × 3 magnitudes | E[D \| refactoring type] per type | All types: E[D] < 0.10; no type indistinguishable from mutation | Any type: E[D] > 0.10 OR any type overlaps with mutation distribution |
| — (SH-5 specialization) | SH-5 — Dimension-Task Specialization | 4 task types across joint benchmark | Standalone AUC per dimension per task | Predicted dominant dim in top-2 on ≥ 3/4 tasks | No dim has standalone AUC ≥ 0.65 on any task |

**Execution order (per prerequisite graph in RESEARCH_HYPOTHESES.md §III):**
SH-3 → SH-2 → H1 → (H3 + SH-1 + SH-4) → H4 → H5 → H2 → H6

---

## 6. Novelty Verdict from Agent 0C

**Verdict: MODERATE**

Agent 0C's adversarial review produced 0 fatal attacks, 3 serious attacks (A1, A3, A4), 5 moderate attacks (A2, A5, A6, A7, A9), and 1 weak attack (A8) across 10 total attacks.

**Surviving claims (from NOVELTY_ANALYSIS.md):**

| Claim | Confidence | Status |
|---|---|---|
| S1: Formal behavioral pseudometric | HIGH | Survives all 10 attacks |
| S2: Longitudinal behavioral genome | HIGH | Survives all 10 attacks |
| S3: Test-suite-free regression oracle (H5) | MODERATE | Novel as claim; empirically unvalidated |
| S4: Cross-language equivalence without shared IR | MODERATE | Credible but narrower than originally claimed |
| S5: Behavioral genome as supply-chain artifact | WEAK | Vision claim; not technical novelty |

**Recommended abstract statement (from Agent 0C Attack 10):**
> *"We propose and validate a test-suite-free, language-agnostic behavioral regression detector based on a formally specified execution-trace pseudometric. The detector tracks a program's behavioral genome — a formally defined 8-dimensional feature vector with dimension-specific distance functions — across version histories and detects semantic regressions without requiring test suites or formal specifications."*

**Path to STRONG verdict:** Empirical validation of H5 (recall ≥ 0.80, precision ≥ 0.70 on Defects4J) and the ablation study showing the multi-dimensional structure outperforms all single-dimension baselines (H6/RQ6). If both are confirmed, S3 rises to HIGH confidence and the overall verdict upgrades to STRONG.

---

## 7. Unresolved Questions and Open Problems

The following are unresolved after Phase 0. They are not blocking for Phase 1 to start (except where noted), but they must be tracked.

| ID | Question | Source | Phase 1 Blocking? | Resolution Strategy |
|---|---|---|---|---|
| OP-1 | What is the minimum N for reliable genome estimation? | FORMAL_MODEL OP-1 | YES — N used in all experiments | SH-3 experiment; assume N = 200 pending empirical validation |
| OP-2 | Is ε-semantic equivalence decidable for finite programs? | FORMAL_MODEL OP-2 | NO | Theoretical investigation; note as limitation |
| OP-3 | Should D be confidence-weighted (Welch t-statistic analog)? | FORMAL_MODEL OP-3 | NO | Future work; use standard D in Phase 1 |
| OP-4 | How do we align g_C (call graph) procedures cross-language? | FORMAL_MODEL OP-4 | YES for H4 full claim | Use manual procedure correspondence table for H4; restrict H4 to g_D, g_X, partial g_C; do not claim cross-language CONTROL without resolution |
| OP-5 | How do we select the heap abstraction for g_S? | FORMAL_MODEL OP-5 | NO | Use summary abstraction by default; study in H3 STATE dimension analysis |
| OP-6 | How do we normalize g_T and g_R cross-architecture? | FORMAL_MODEL OP-6 | YES for H4 g_T/g_R claim | Exclude g_T and g_R from cross-language comparison; use SPECint normalization within-language only |
| — | Does the 8-dimensional architecture outperform a learned behavioral embedding? | NOVELTY Attack 7 | NO — Phase 2 | Run neural embedding comparison; report interpretability/discriminability trade-off |
| — | How large is the intra-version genome variance (noise floor)? | Threats IV-05 | YES — must be measured before inter-version claims | First experiment: compute Var[G(P)] for fixed P before H1 |
| — | What fraction of regressions in Defects4J are rare-trigger? | Threats IV-04 | NO | Measure μ_I(Δ) as part of SH-2 stratification |
| A6 policy | What canonical policy governs non-deterministic programs in the benchmark? | Threats IV-05, A6 | YES | Defined: fixed PRNG seed = 42, serialized scheduling for C7 programs (BENCHMARK_DESIGN.md §8.1) |

---

## 8. Cross-Document Consistency Findings

The following inconsistencies were identified during integration review. None is blocking, but all must be resolved before Phase 1 experiments are executed.

### Inconsistency 1 — Hypothesis Numbering Mismatch (CRITICAL — must resolve)

**Finding:** The FORMAL_MODEL.md (Agent 0B) and RESEARCH_HYPOTHESES.md (Agent 0E) use the same H1–H6 labels but assign different content to H2, H3, and H4.

| Label | FORMAL_MODEL.md | RESEARCH_HYPOTHESES.md |
|---|---|---|
| H1 | Behavioral Genome Stability (same) | Behavioral Genome Stability (same) ✓ |
| H2 | Behavioral Genome **Sensitivity** | Structured SBG **Outperforms Baselines** |
| H3 | **Cross-Language Behavioral Equivalence** | **Robustness Under Refactoring** |
| H4 | **Behavioral Genome Versioning** | **Cross-Language Generalization** |
| H5 | Genome as Regression Oracle (same) | Genome as Regression Oracle (same) ✓ |
| H6 | Behavioral Genome Uniqueness (same) | **Multi-Dimensional Value** (different framing) |

FORMAL_MODEL.md H2 (sensitivity) corresponds to RESEARCH_HYPOTHESES.md H5 (oracle). FORMAL_MODEL.md H3 (cross-language) corresponds to RESEARCH_HYPOTHESES.md H4. FORMAL_MODEL.md H4 (versioning) is operationalized as sub-hypothesis SH-4 (monotonicity) in RESEARCH_HYPOTHESES.md. RESEARCH_HYPOTHESES.md H6 (multi-dimensional value) has no direct equivalent in FORMAL_MODEL.md H6 (uniqueness). This is a systemic remapping, not a few typos.

**Resolution required:** Adopt a single canonical H-numbering. This document adopts the FORMAL_MODEL.md numbering as authoritative (it is the source document), and calls out the RESEARCH_HYPOTHESES.md labels as operational labels. The hypothesis-to-experiment table in §5 uses FORMAL_MODEL.md numbering as left column and RESEARCH_HYPOTHESES.md as operational mapping.

### Inconsistency 2 — H4/RQ4 Scope Mismatch (SERIOUS)

**Finding:** RESEARCH_HYPOTHESES.md §H4 (Cross-Language Generalization) restricts the comparison to dimensions `{g_C, g_D, g_X}` (correctly acknowledging EXECUTION must be excluded). However, NOVELTY_ANALYSIS.md (Attack 4) and THREATS_TO_VALIDITY.md (CV-05) both establish that g_C is also problematic cross-language without resolving OP-4. The effective cross-language set in RESEARCH_HYPOTHESES.md should be `{g_D, g_X}` with g_C as a partial/exploratory addition, not listed as a primary dimension alongside g_D and g_X.

**Resolution required:** RESEARCH_HYPOTHESES.md H4 should be updated to list `{g_D, g_X}` as confirmed cross-language portable dimensions, with g_C marked as exploratory pending OP-4 resolution. The benchmark H4 experiment should explicitly test all three separately.

### Inconsistency 3 — Benchmark Missing H4 Evaluation Design (MODERATE)

**Finding:** BENCHMARK_DESIGN.md §Overview states: *"The benchmark also provides evaluation ground for H3 (cross-language equivalence), H5 (genome as regression oracle), and H6 (genome uniqueness)."* Using FORMAL_MODEL.md numbering, this says H3 (cross-language) is covered. But examining BENCHMARK_DESIGN.md in detail, the cross-language pairs (language_pairs_for_h3, §8) are listed as: Python-Java, Python-C, Java-C, Python-Go, Java-Rust, C-Go. RESEARCH_HYPOTHESES.md H4 (cross-language) specifies 5 algorithm classes × 5 language pairs, requiring **at least 35 equivalent pairs per language pair.** The minimum viable benchmark in BENCHMARK_DESIGN.md does not specify how many cross-language equivalent pairs are required, only that ≥ 6 languages must be represented. The cross-language pair counts are unspecified in the benchmark minimum viable table.

**Resolution required:** BENCHMARK_DESIGN.md minimum viable table must add a cross-language pair count row: at minimum 35 equivalent pairs per language pair per RESEARCH_HYPOTHESES.md H4's power analysis.

### Inconsistency 4 — BENCHMARK_DESIGN.md Missing H4 (Versioning/SH-4) Corpus (MODERATE)

**Finding:** FORMAL_MODEL.md H4 (versioning monotonicity) is operationalized in RESEARCH_HYPOTHESES.md as SH-4, requiring 10 GitHub projects with ≥ 100 commits each. BENCHMARK_DESIGN.md does not specify a real-repository version history corpus. The benchmark is exclusively a controlled pair-construction benchmark; the GitHub commit history corpus for SH-4 is not described.

**Resolution required:** Either add a separate SH-4 corpus specification to BENCHMARK_DESIGN.md or document it as a separate Phase 1 corpus preparation task outside the controlled benchmark.

### Inconsistency 5 — Statistical Significance Threshold Mismatch (MINOR)

**Finding:** RESEARCH_HYPOTHESES.md consistently applies Bonferroni-corrected α = 0.0017 across H1–H6 (for n = 6 primary hypotheses). BENCHMARK_DESIGN.md §7.1 uses α = 0.05 in its McNemar power analysis for system comparison. The statistical justification table in the benchmark summary uses α = 0.05 for the sample size calculation, while the hypotheses require α = 0.0017. This means the benchmark is powered for α = 0.05, but the hypotheses will be tested at α = 0.0017.

**Impact:** The minimum viable benchmark (400 test pairs) was justified using α = 0.05. At α = 0.0017, the required sample size for equivalent power is larger. The recommended benchmark (640 test pairs) likely remains sufficient for the primary metrics given Defects4J's 395+ pairs supplement, but the discrepancy must be acknowledged.

**Resolution required:** BENCHMARK_DESIGN.md must re-run the power analysis at α = 0.0017 and confirm whether 400 or 640 test pairs is sufficient. If not, either increase the target or explicitly accept reduced power.

### Inconsistency 6 — threats_summary.json Severity vs. Document Severity (MINOR)

**Finding:** threats_summary.json reports `"severity_counts": {"HIGH": 14, "MEDIUM": 14, "LOW": 4}` but the THREATS_TO_VALIDITY.md document lists 32 threats total across 5 categories. The explicit "HIGH" severity classification appears only in the high_severity_threats array (14 entries). Medium and low severity entries are not consistently labeled "MEDIUM" vs. "HIGH" within the document text — some entries in the high_severity array have `"residual_risk": "MEDIUM"` while being listed under high_severity. The severity classification conflates "initial severity" with "residual severity after mitigation."

**Resolution required:** Clarify in any downstream use that the 14 "high severity" threats are HIGH *before* mitigation; residual risk varies. Use residual risk for Phase 1 prioritization.

### Inconsistency 7 — FORMAL_MODEL H6 vs. RESEARCH_HYPOTHESES H6 (MODERATE)

**Finding:** FORMAL_MODEL.md H6 is "Behavioral Genome Uniqueness" — the claim that unrelated programs have collision probability ≤ δ_collision. RESEARCH_HYPOTHESES.md H6 is "Multi-Dimensional Value" — the claim that all 8 dimensions contribute non-redundant signal. These are different hypotheses with the same label. RESEARCH_HYPOTHESES.md §H6 operationalization does not test uniqueness/collision rate at all; this is addressed separately in RQ10. The JSON summaries (hypotheses_summary.json and formal_model_summary.json) both use "H6" to mean different things.

**Resolution required:** Rename RESEARCH_HYPOTHESES.md H6 to H6-MV (multi-dimensional value) and add H6-U (uniqueness/collision) as a separate hypothesis mapped to RQ10. Align with FORMAL_MODEL.md H6 as the canonical uniqueness claim.

---

## 9. Recommendations for Phase 1 Prerequisites

The following must be true before Phase 1 experiments start:

1. **Hypothesis numbering must be canonicalized.** Either adopt FORMAL_MODEL.md H-numbering throughout or update FORMAL_MODEL.md to match RESEARCH_HYPOTHESES.md. The current mismatch will cause experimental protocol errors.

2. **Intra-version genome variance must be characterized first** (noise floor measurement before any inter-version distance claim). This is Priority 2 in the threats_summary.json recommendations and is not currently in the experimental sequence in RESEARCH_HYPOTHESES.md.

3. **SH-3 (N sufficiency)** must be executed and confirm N = 200 is sufficient before any other hypothesis is tested. This is already in the prerequisite graph and is not a new finding — it is restated here as a gate condition.

4. **Cross-language H4 scope must be restricted** to g_D + g_X + exploratory g_C. Do not plan Phase 1 H4 experiments claiming full 8-dimension cross-language comparison.

5. **BENCHMARK_DESIGN.md minimum viable cross-language pair count** must be specified and confirmed before corpus construction begins.

6. **BENCHMARK_DESIGN.md McNemar power analysis must be re-run at α = 0.0017** to confirm test-set size.

7. **Pre-registration** of primary hypotheses H1, H5 (regression oracle) before any evaluation data is seen. Pre-registration at OSF or AsPredicted before genome extraction begins. (Priority 1 in threats_summary.json.)

8. **Containerized reproducibility environment** must be defined (OS, compiler, runtime, PRNG policy) before any genome is extracted. Failure to fix the environment means all results are unreproducible (RL-01 threat).

9. **A canonical non-determinism policy** must be documented and applied uniformly across all C7 programs (concurrent category). The current policy (seed = 42, fixed thread count, round-robin scheduling) in BENCHMARK_DESIGN.md §8.1 is adequate; it must be enforced from day one.

10. **H3 (cross-language, FORMAL_MODEL numbering)** must be formally marked as exploratory/preliminary in all Phase 1 documentation. It should not be a primary confirmatory hypothesis until OP-4 is resolved.

---

*This document was produced by Agent 0-INTEGRATION as the Phase 0 synthesis. All findings are grounded in the six Phase 0 agent documents and their JSON summaries. Inconsistencies reported in §8 are based on direct cross-document comparison. No claim in this document extends beyond what the source documents support.*

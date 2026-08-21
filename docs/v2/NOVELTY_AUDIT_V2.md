# SBG V2 — Novelty Audit

**Agent:** K (Prior Art and Novelty Audit)  
**Date:** 2025  
**Scope:** Audit of novelty claims for SBG V2 against related work, grounded in evidence from v1 experiments and v2 Phase 2 gate results  
**Principle:** Honest assessment — no inflation of novelty. Where prior art exists, it is named.

---

## 1. Audit Basis

This audit incorporates all prior analysis:

- `docs/research/NOVELTY_ANALYSIS.md` (Agent 0C adversarial review, 10 attacks)
- `docs/research/PRIOR_ART_MATRIX.md` (40 surveyed works across 10 domains)
- `docs/v2/agents/0E_prior_art_audit.json` (Agent 0E gap analysis, 7 gaps, 6 new works)
- `docs/v2/agents/0F_adversarial_review.json` (Agent 0F, P0/P1/P2/P3 risks)
- `docs/CLAIMS_REGISTRY.yaml` (C001–C015, v1 experiment verdicts)
- `artifacts/v2/PHASE_2_GATE.json` (v2 Phase 2 results: H7 SUPPORTED, H9 SUPPORTED)
- `artifacts/v2/E1_statistical_analysis.json`

**V2 key results at time of audit:**
- B07 Dynamic V2 AUROC = **0.5310** (CI [0.4991, 0.5806])
- V1 Static SBG AUROC = 0.4237 (baseline)
- V1 best static baseline AST AUROC = 0.5528
- Inversion delta v1 static: **+0.0335** (inverted)
- Inversion delta v2 dynamic: **−0.0453** (resolved)
- H7: SUPPORTED; H9: SUPPORTED; H8: NOT SUPPORTED

---

## 2. Prior Art Audit by Research Area

### 2a. Dynamic Program Analysis for Similarity (IODINE, DyPDG, TTAnalyze)

**Closest prior works:**
- **Bayer et al. TTAnalyze (NDSS 2009):** Dynamic behavioral fingerprinting using syscall n-gram sequences for malware clustering. This is a direct prior for SBG's INTERACTION dimension (`g_X`).
- **Kinable & Kostakis (2011):** Malware classification via call-graph clustering. Direct prior for the structural call-graph component of `g_C`.
- **Moser et al. (2007):** Taint-guided multi-path execution for malware signature generation. Direct prior for `g_X` extension.

**SBG V2 delta:** TTAnalyze targets malware triage (classify an unknown sample into a threat family — one-shot task). SBG V2 targets semantic regression detection (is this version of a known program behaviorally equivalent to a prior version — longitudinal task). No TTAnalyze-style system maintains a versioned behavioral history or applies behavioral distance as a regression oracle. Domain, task, and operational framing are different.

**Honest assessment:** The `g_X` dimension has real prior art overlap. SBG V2's novelty here is in the domain inversion, the multi-dimensional structure, and the regression-detection framing — not in the individual dimension.

---

### 2b. Behavioral Execution Traces for Clone Detection

**Closest prior works:**
- **Jiang & Su (ISSTA 2009) — MISSING FROM PRIOR ART MATRIX:** "Automatic Mining of Functionally Equivalent Code Fragments via Random Testing." Executes code fragments on random inputs, clusters by I/O behavior to find functional equivalents. **This is the most direct prior work for SBG V2's behavioral equivalence detection.** Its core mechanism — run program, observe behavior, cluster equivalents — is the operational primitive of SBG V2's H7/H9 evaluation.
- **Walenstein et al. (EICAR 2007):** Instruction-trace n-gram similarity for malware. Defines "behavioral distance" via trace comparison — an independent definition of the concept SBG V2 formalizes.

**SBG V2 delta over Jiang & Su:** Jiang & Su use I/O comparison (output values match → programs are equivalent). SBG V2 explicitly excludes output values from the DynamicGenome (SAFEGUARD-2, verified in 19-test PHASE_2_GATE suite). SBG captures *internal* behavioral patterns — branch coverage consistency, exception type sets, anonymized call-frequency rank vectors — that are output-free. Two programs can match on I/O while diverging in error handling, control flow, or resource consumption; SBG V2 is sensitive to these dimensions. Jiang & Su are not.

**Honest assessment:** Jiang & Su (2009) is genuine prior art for the concept of execution-based clone/equivalence detection. This citation is currently **missing from the prior art matrix** and constitutes a vulnerability if SBG V2 claims to be the first execution-based behavioral similarity system. The delta is defensible but must be explicitly stated.

---

### 2c. Test Coverage Similarity for Program Equivalence

**Closest prior works:**
- **Ohmann et al. (ICSE 2014) — Efficient Profile-Guided Test Selection:** Uses coverage profiles across test suites as a proxy for behavioral similarity.
- **Standard `gcov`/`lcov` coverage tools:** Branch coverage vectors are SBG's `g_U` (EXECUTION) dimension — entirely standard since the 1980s.

**SBG V2 delta:** SBG V2 uses *coverage consistency* as one feature among many, not as the sole signal. More importantly, SBG V2 evaluates coverage under automatically-generated inputs rather than hand-written test suites — the "test-suite-free" property. Coverage-based test selection requires an existing test suite; SBG V2 requires only executable programs and a shared input distribution.

**Honest assessment:** Coverage as a feature is not novel. The novelty is the combination with other execution-derived dimensions and the test-suite-free evaluation regime.

---

### 2d. Semantic Similarity via Test Suites (Roped, Randoop-style)

**Closest prior works:**
- **Roped and test-suite-driven equivalence detection:** Systems that run programs against shared test suites and declare equivalence based on test passage.
- **McKeeman (1998) — Differential Testing — MISSING FROM PRIOR ART MATRIX:** Runs multiple implementations on the same inputs and flags divergence as a bug. This is the canonical prior art for "run two programs, compare." Any reviewer of SBG V2 will ask why McKeeman 1998 is not cited.
- **Yang et al. (PLDI 2011) — CSmith:** Differential testing applied to C compilers.

**SBG V2 delta over differential testing:** Differential testing produces a binary divergence signal (programs agree or disagree on this input). SBG V2 produces a continuous-valued, multi-dimensional distance vector. The key distinctions: (1) SBG V2 is **output-free** — it detects behavioral divergence through *how* programs execute, not *what* they output; (2) SBG V2 produces a pseudometric with formal properties (symmetry, self-zero, bounded range — all verified in v2 test suite); (3) SBG V2 enables dimension-specific diagnosis (is this a control-flow divergence, an error-handling divergence, or a call-pattern divergence?). Differential testing cannot answer this.

**Honest assessment:** Differential testing (McKeeman 1998) is **SERIOUS prior art** that is missing from the matrix. It is the direct predecessor for the execution-comparison mechanism. SBG V2's scientifically novel delta is the output-free structural execution features + formal pseudometric + inversion-resolution finding — not the comparison mechanism itself.

---

### 2e. Runtime Behavior for Code Search (CodeBERT, GraphCodeBERT)

**Closest prior works:**
- **CodeBERT (Feng et al., 2020):** Pre-trained model on source code + docstrings; similarity via cosine distance on learned embeddings.
- **GraphCodeBERT (Guo et al., 2021):** Incorporates data-flow graphs into CodeBERT architecture.
- **code2vec (Alon et al., 2019):** Path-based AST embeddings for code similarity.

**Assessment:** These are **static** methods — they encode code structure, not runtime behavior. None of them use execution. The v1 CLAIMS_REGISTRY notes B05 uses "subword n-gram fallback (not CodeBERT)" — if CodeBERT were properly evaluated, it might outperform AST's 0.5528 AUROC. This is an honest gap: a properly tuned neural baseline using CodeBERT embeddings has not been run. Its absence means the claim that "dynamic features are more informative than static embeddings" cannot be made — only the claim that "dynamic features outperform static SBG" (which is what H7 actually says).

**Honest assessment:** The neural embedding comparison is absent. SBG V2 should not claim superiority over neural embeddings without running them. H7 is validated only against the v1 static SBG baseline (AUROC=0.4237) and the v1 AST baseline (AUROC=0.5528), not against a trained neural baseline.

---

### 2f. Mutation Testing with Execution Features

**Closest prior works:**
- **Jia & Harman (2011) — Mutation Testing Survey:** Comprehensive review of mutation operators.
- **Just et al. (2014) — Defects4J:** The standard regression bug benchmark for Java.
- **Chen et al. (1998/2018) — Metamorphic Testing — MISSING FROM PRIOR ART MATRIX:** Verifies programs by checking that metamorphic relations (input-output invariants) hold across program executions. This is the dominant oracle-free testing paradigm and directly competes with SBG V2's "specification-free detection" claim.

**SBG V2 delta over metamorphic testing:** MT requires explicit metamorphic relation authorship (a user must specify *which* property to verify). SBG V2 requires no specification — the behavioral signature captures any execution-level change across its feature dimensions. MT tests specific pre-authored properties; SBG V2 is sensitive to any behavioral change, including those for which no metamorphic relation has been written. The inverse: MT provides a precise diagnostic (which invariant was violated); SBG V2 provides a distance score without naming the violated property.

**Honest assessment:** Metamorphic testing (Chen 1998) is **missing from the matrix** and must be cited. The delta is real and defensible, but omitting this citation is a credibility gap.

---

## 3. V2-Specific Novelty Assessment

### 3a. Is "structural-semantic inversion" a known phenomenon?

**Finding:** No prior work names, quantifies, or empirically characterizes this phenomenon. The adversarial review (Agent 0C), prior art audit (Agent 0E), and claims registry (C009) all confirm: the finding that semantics-preserving transforms (rename, refactor, extract) cause *larger* structural change than semantics-changing mutations (off-by-one, operator swap) is **absent from all 40 surveyed works**.

**Evidence:** C009 status = SUPPORTED across all 8 baselines on 744 test pairs. EQUIV_mean < CHANGED_mean for every representation including dynamic trace (B06, v1). The inversion is reproducible, statistically characterized, and mechanistically explained (structural change magnitude asymmetry between SP and SC transforms).

**Prior art gap reference:** Agent 0E GAP-06: "This is a SBG-specific empirical discovery... No prior work quantifies this inversion phenomenon."

**Novelty status: NOVEL.** This is the strongest and most defensible novelty claim in the entire SBG project.

**Caveat:** The phenomenon is novel in the *software similarity* literature. Whether a related observation exists in the *mutation analysis* literature (where it might appear as "mutation score inflation from refactoring") has not been systematically checked. A thorough literature sweep of mutation adequacy and refactoring impact is the remaining uncertainty.

---

### 3b. Is execution-grounded behavioral genome a novel representation?

**Finding: INCREMENTAL.** The individual dimensions of the behavioral genome are all standard metrics (coverage, syscall counts, call frequencies, branch patterns, error rates). Their combination in a single formal object with a unified pseudometric is architecturally novel, but this architectural novelty is analogous to Joern's Code Property Graph (Yamaguchi et al., 2014) in the static domain — the principle of "unify multiple known representations" has prior instantiation.

**What is novel within the genome:**
- The **anonymized call-frequency rank vector** (replacing name-based hot-path hash, which was invalidated by SP-2 rename in v1) — this specific design choice is a v2 technical contribution motivated by the v1 inversion finding.
- The **output-free structural execution features** (verified by SAFEGUARD-2 in v2 test suite) — the deliberate architectural choice to capture *how* programs execute without capturing *what* they output differentiates SBG V2 from differential testing and Jiang & Su.
- The **formal pseudometric properties** (symmetry, self-zero, bounded range — all verified in 19-test v2 suite) — no prior behavioral fingerprinting system specifies these formally.

**What is not novel:** Any individual dimension (coverage, error patterns, call counts). The concept of execution-derived features for code similarity (Jiang & Su 2009, TTAnalyze 2009, Walenstein 2007).

---

### 3c. Is Holm-Bonferroni for behavioral hypothesis testing novel?

**Finding: NOT NOVEL.** Holm-Bonferroni correction is a standard statistical method (Holm 1979) applied to multiple comparisons in countless empirical studies. Its application to a 12-hypothesis behavioral testing family is good statistical practice, not a scientific contribution.

**What is worth noting:** The *explicit pre-registration architecture* — pre-registering H7–H12 with a git commit hash before any dynamic execution (SAFEGUARD-1, documented in HYPOTHESES_V2.md with commit 35b614c) — is not standard practice in software engineering research. This methodological rigor is a distinguishing feature of the project but is a process contribution, not a scientific novelty claim.

**Novelty status: NOT NOVEL as a statistical method. NOTABLE as a methodological practice.**

---

### 3d. Closest prior work and how SBG differs

| Dimension | Closest Prior Work | Year | SBG V2 Delta |
|---|---|---|---|
| Execution-based equivalence | Jiang & Su (ISSTA 2009) | 2009 | SBG is output-free; Jiang & Su use I/O comparison |
| Binary divergence detection | McKeeman Differential Testing | 1998 | SBG is continuous-valued, multi-dimensional, output-free |
| Specification-free testing | Chen et al. Metamorphic Testing | 1998 | SBG requires no metamorphic relation authorship |
| Behavioral fingerprinting | Bayer et al. TTAnalyze | 2009 | SBG targets regression (longitudinal); TTAnalyze targets malware (one-shot) |
| Unified code representation | Joern / CPG (Yamaguchi 2014) | 2014 | SBG is dynamic; Joern is static |
| Semantic equivalence (sound) | Ramos & Engler (USENIX Sec 2015) | 2015 | SBG scales where symbolic execution explodes |
| Inversion phenomenon | **None found** | — | **Novel: first quantification** |

---

## 4. What Is Genuinely Novel

Listed in decreasing confidence:

### N1 — The structural-semantic inversion finding (HIGH CONFIDENCE)

The empirical observation that semantics-preserving transforms cause larger structural change than semantics-changing mutations, causing all structural and hybrid representations to produce inverted similarity signals, is not documented in any prior work. The phenomenon is reproducible (N=744, all 8 representations, EQUIV_mean < CHANGED_mean for all baselines), statistically characterized (CI, bootstrap), and mechanistically explained. This is SBG's primary scientific contribution.

### N2 — V2 execution-based resolution of the inversion (HIGH CONFIDENCE, partial)

The finding that execution-derived features (B07 AUROC=0.5310, inversion delta=−0.0453) resolve the v1 inversion (delta=+0.0335) is a novel empirical result. No prior work: (a) documented the inversion, (b) tested whether execution features resolve it, or (c) produced this specific quantitative result. The resolution is partial (AUROC=0.5310 still below AST=0.5528 and far below practical utility threshold), but the directional finding — execution features correct an inversion that static features cannot — is scientifically meaningful.

### N3 — Output-free behavioral genome (MODERATE CONFIDENCE)

The deliberate architectural separation between output-proximate features (excluded) and output-free structural execution features (the DynamicGenome) is a novel design choice relative to differential testing and I/O-based clone detection. This separation allows SBG V2 to make a behavioral genome claim that is distinct from "just run differential testing." The design is verified by SAFEGUARD-2 in the v2 test suite.

### N4 — Formal pseudometric on execution-derived features (MODERATE CONFIDENCE)

The formal specification of a pseudometric (symmetry, self-zero, bounded range) on execution-trace-derived behavioral features, verified by test, is not present in TTAnalyze, Jiang & Su, or McKeeman's differential testing. The contribution is the formalization, not the individual features.

---

## 5. What Is Incremental

### I1 — 8-dimensional behavioral genome architecture

The individual dimensions (coverage, syscall counts, call patterns, error rates, branch histograms, resource metrics) are all standard metrics with dedicated tools. The unification into a single object is architecturally analogous to Joern's CPG in the static domain. Contribution is in the application to the dynamic/behavioral domain and in the specific formal structure, not in the dimensional content.

### I2 — Dynamic features outperform static SBG (C013, C014)

The finding that dynamic features (AUROC=0.505 in v1, 0.531 in v2) outperform static SBG (AUROC=0.4237) is directionally consistent with the hypothesis that runtime behavior provides more signal than code structure for semantic change. However, this is also consistent with dozens of prior works claiming dynamic > static for bug detection. The incremental contribution is the specific benchmark quantification, not the directional finding.

### I3 — ERROR dimension dominance (C014)

ERROR_only AUROC=0.477 outperforms CONTROL+DATA+ERROR=0.349. This is a concrete ablation finding, but it is benchmark-specific and may not generalize. It is an interesting negative result about dimension interaction, not a novel theoretical claim.

### I4 — Longitudinal behavioral genome tracking (CG-1)

The concept of maintaining a versioned behavioral history is not implemented by any surveyed academic system. However, industrial APM tools (Datadog, NewRelic) collect longitudinal multi-dimensional execution metrics for deployed services. The formal pseudometric framework is absent from APM tools, but the longitudinal tracking concept is present in industrial practice. This is incremental over industrial practice, novel within academic research.

---

## 6. What Is Known (Not Novel)

### K1 — Individual genome dimensions

Every dimension of the SBG genome — branch coverage, syscall counts, call-graph metrics, error rates, memory profiling, latency distributions — is a standard metric with existing tools (gcov, perf, Valgrind, Massif, strace). These are not novel.

### K2 — Execution-based equivalence detection concept

Jiang & Su (2009), McKeeman (1998), and the differential testing literature establish execution-based equivalence detection as a known approach. SBG V2 is a specific instantiation, not the first.

### K3 — "Behavioral fingerprint" for program characterization

Bayer et al. (2009), Walenstein et al. (2007), and Christodorescu et al. (2005) all define behavioral fingerprints from execution traces for program similarity. The concept is known; SBG V2's contribution is the specific formalization and the regression/inversion application.

### K4 — Holm-Bonferroni for multiple hypothesis correction

Standard statistical method. Not a contribution.

---

## 7. Strongest Novelty Claim (Supported by Evidence)

> **"We identify and quantify a structural-semantic inversion in software behavioral similarity benchmarks — a phenomenon in which semantics-preserving transforms produce systematically larger structural change than semantics-altering mutations, causing all structural and hybrid representations to produce inverted similarity signals — and demonstrate empirically that execution-derived behavioral features resolve this inversion."**

**Evidence:** C009 SUPPORTED (all 8 representations inverted, N=744); H7 SUPPORTED (AUROC 0.4237→0.5310); H9 SUPPORTED (delta +0.0335→−0.0453). Pre-registered in git commit 35b614c before any v2 dynamic execution.

This claim is:
- Falsifiable and falsified (v1) then resolved (v2) — a proper scientific structure
- Not present in any of the 40 prior works in the matrix
- Reproducible on the frozen benchmark
- Pre-registered, protecting against post-hoc inflation

---

## 8. Weakest Novelty Claim (Over-Reaches)

> **The cross-language behavioral equivalence claim (H11)**

H11 is pre-registered as PILOT/EXPLORATORY with an explicitly acknowledged power of ~25% at Bonferroni-corrected α. The cross-language evaluation in v1 used N=5 illustrative Python-only pairs, not true cross-language pairs (C008: NOT_EVALUABLE). The v2 plan is N=15 pairs, which remains severely underpowered. The CONTROL, TEMPORAL, and EXECUTION genome dimensions cannot be compared cross-language without solving open problems OP-4 and OP-6 (explicitly deferred). Any positive result from H11 would have CI too wide to be interpretable as confirmation.

**Additionally:** Jiang & Su (2009) apply I/O-based equivalence detection across language families on the OJ dataset. The SBG V2 cross-language claim must be differentiated from this prior work. The delta (output-free features vs. I/O comparison) is real, but the empirical evidence base for it is not yet established.

**Recommendation:** Frame H11 explicitly as pilot/exploratory in any publication. Do not claim cross-language novelty until a properly powered study (N≥100 cross-language pairs, true Python↔Java benchmark) is run.

---

## 9. Prior Art That Weakens Novelty Claims

| Risk ID | Work | Weakens | Severity | Status in Matrix |
|---|---|---|---|---|
| GAP-01 | McKeeman (1998) Differential Testing | Execution-comparison mechanism | SERIOUS | MISSING |
| GAP-01 | Chen et al. (1998/2018) Metamorphic Testing | Specification-free testing claim | HIGH | MISSING |
| GAP-02 | Jiang & Su (ISSTA 2009) | Execution-based clone detection | HIGH | MISSING |
| GAP-04 | Ramos & Engler (USENIX Sec 2015) | Behavioral equivalence via symbolic execution | HIGH | MISSING |
| GAP-05 | Christodorescu et al. (S&P 2005) | "First formal behavioral distance" claim | MEDIUM | MISSING |
| Attack 1 | Bayer et al. TTAnalyze (2009) | g_X dimension novelty | SERIOUS | COVERED |
| Attack 3 | All profiler tools | Individual dimension novelty | SERIOUS | IMPLICIT |

**Critical action:** The four MISSING citations (GAP-01, GAP-02, GAP-04) must be added to `docs/research/PRIOR_ART_MATRIX.md` before any publication submission. Their absence will be the first question from any competent reviewer.

---

## 10. Summary Table

| Component | Novelty Status | Confidence | Closest Prior | SBG Delta |
|---|---|---|---|---|
| Structural-semantic inversion finding | NOVEL | HIGH | None found | First quantification |
| Dynamic inversion resolution | NOVEL | HIGH (partial) | None for this specific question | H7+H9 empirical evidence |
| Output-free behavioral genome design | NOVEL (design choice) | MODERATE | Jiang & Su (I/O-based) | No output values in genome |
| Formal pseudometric on exec features | NOVEL (formalization) | MODERATE | Walenstein 2007 (informal) | Formal properties verified |
| 8-dimensional genome architecture | INCREMENTAL | HIGH | Joern/CPG (static analog) | Dynamic domain; unified |
| Longitudinal behavioral tracking | INCREMENTAL (academic) | MODERATE | APM tools (industrial) | Formal pseudometric absent in APM |
| Individual genome dimensions (g_C–g_U) | KNOWN | HIGH | gcov, perf, Valgrind, strace | Not novel individually |
| Execution-based equivalence detection | KNOWN concept, INCREMENTAL | MODERATE | Jiang & Su, McKeeman | Specific inversion application |
| Cross-language behavioral equivalence | INCREMENTAL, UNDERPOWERED | LOW | Jiang & Su (I/O cross-language) | Output-free; underpowered N=15 |
| Holm-Bonferroni framework | NOT NOVEL | HIGH | Holm 1979 | Good practice, not contribution |

---

## 11. Recommendations

1. **Lead with the inversion finding.** The structural-semantic inversion (C009) is the strongest, most defensible, and most interesting scientific contribution. All other findings are framed relative to it.

2. **Add GAP-01 through GAP-04 citations to PRIOR_ART_MATRIX.md immediately.** Their absence is the single most actionable risk before any external review.

3. **Clearly separate B09 differential testing from B07 dynamic SBG** in any experimental report. SAFEGUARD-2 is architecturally enforced; it must also be narratively clear.

4. **Do not claim H11 (cross-language) as confirmed.** Label it exploratory, report the power calculation, and plan a properly powered follow-up.

5. **Run the Jiang & Su comparison explicitly.** Execute Jiang & Su's I/O-based clone detection on the SBG benchmark. Measure AUROC. If SBG's output-free features achieve comparable or better AUROC than I/O comparison on the same benchmark, that is strong empirical evidence for the output-free architecture's value.

6. **Complete H10, H11, H12 evaluation** before claiming any final verdict on SBG V2's novelty. Currently only H7 and H9 are evaluated; the cross-language and regression-detection claims remain empirically unvalidated.

---

*Audit completed by Agent K. This document is not adversarial — it is honest. The structural-semantic inversion finding is a genuine, reproducible, novel scientific contribution. The representation-building approach is incremental over prior art. The project must cite the missing works and frame its contribution precisely.*

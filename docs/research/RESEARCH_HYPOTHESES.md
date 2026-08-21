# Research Hypotheses — Software Behavior Genome (SBG)

> **Agent:** 0E  
> **Depends on:** `FORMAL_MODEL.md` (Agent 0B), `PRIOR_ART_MATRIX.md` (Agent 0C)  
> **Status:** Draft v1.0

---

## Preamble

This document translates the formal mathematical claims of `FORMAL_MODEL.md` into
fully operationalized research hypotheses ready for experimental design. For each
hypothesis H1–H6 we state:

1. Null and alternative hypotheses in inferential-statistics form  
2. Independent and dependent variables  
3. Experimental controls  
4. Operationalization (precise measurement protocol)  
5. Expected effect direction and magnitude  
6. Minimum meaningful effect size (MMES)  
7. Statistical test  
8. Required sample size (power analysis)  
9. Falsification condition  

We then state sub-hypotheses SH-1 through SH-5 for mechanistic insight, establish
a prerequisite order among all hypotheses, and present the full research-question
hierarchy RQ1–RQ10 with evaluation criteria.

---

## Part I — Primary and Secondary Hypotheses

---

### H1 — Behavioral Genome Stability

**Formal summary (from FORMAL_MODEL.md §H1):**
> P ≡_S P' ⟹ D(G(P), G(P')) < ε_stable, where ε_stable ≤ 0.05 on standard
> benchmarks under the production input distribution I_prod.

#### 1. Null and Alternative Hypotheses

| | Statement |
|---|---|
| **H1₀** | The mean behavioral distance between semantics-preserving program pairs is equal to the mean behavioral distance between semantics-changing pairs. Formally: E[D(G(P), G(P')) \| P ≡_S P'] = E[D(G(P), G(P'')) \| P ≢_S P'']. |
| **H1_A** | The mean behavioral distance under semantics-preserving transformation is substantially less than under semantics-changing transformation. Formally: E[D \| ≡_S] < E[D \| ≢_S] with effect size Δ ≥ MMES. |

#### 2. Independent Variables

| Variable | Values | Operationalization |
|---|---|---|
| Transformation type | {semantics-preserving, semantics-changing} | Preserving: automated refactoring (rename, extract-method, inline, dead-code elimination, loop hoisting). Changing: mutation operators from Defects4J [28] (statement deletion, operator swap, boundary shift). |
| Program identity | Program corpus | 50 open-source Java/Python programs sampled from Defects4J [28] and RosettaCode |
| Input distribution | {I_prod, I_unif, I_cov} | Production trace replay; uniform random; coverage-guided (KLEE [8]) |

#### 3. Dependent Variables

| Variable | Symbol | Range |
|---|---|---|
| Behavioral distance | D(G(P), G(P')) | [0, 1] |
| Per-dimension distance | d_C, d_D, d_S, d_R, d_T, d_E, d_X, d_U | [0, 1] each |
| Variance of D within group | σ²_group | ≥ 0 |

#### 4. Controls

- **Environment:** Fixed hardware (same machine), fixed JVM/CPython version, fixed
  clock seed (A6: determinism).
- **Input distribution:** Held constant across both transformation groups for any
  given program.
- **Sample size N:** Minimum N = 200 traces per genome estimate (see OP-1; validated
  by bootstrap convergence check).
- **Transformation oracle:** Semantics-equivalence of "preserving" pairs confirmed by
  passing a shared regression test suite (≥ 90% branch coverage required).
- **Mutation oracle:** Semantics-change confirmed by at least one test in the
  gold-standard suite failing.

#### 5. Operationalization

```
FOR each program P in corpus:
  FOR each semantics-preserving transform T_sp:
    P' := T_sp(P)
    G_P  := Phi(P,  S_N)   # N=200 traces, I=I_prod
    G_P' := Phi(P', S_N)
    record D_sp := D(G_P, G_P')
  FOR each semantics-changing mutation M:
    P'' := M(P)
    G_P'' := Phi(P'', S_N)
    record D_sc := D(G_P, G_P'')
COMPARE distributions {D_sp} vs {D_sc}
```

- Genome extraction follows Definition 7 of FORMAL_MODEL.md.
- Behavioral distance follows Definition 18 with uniform weights w_k = 1/8.
- TEMPORAL (g_T) and RESOURCE (g_R) dimensions are additionally analyzed in
  isolation to test the dimension-specific stability caveat from H1.

#### 6. Expected Effect Direction and Magnitude

- **Direction:** D_sp ≪ D_sc.
- **Magnitude:** E[D_sp] ≤ 0.05; E[D_sc] ≥ 0.30. Cohen's d ≥ 1.5 (large effect).
- **Per-dimension:** CONTROL, DATA, INTERACTION dimensions expected most stable
  (mean d_C, d_D, d_X < 0.03 under refactoring). TEMPORAL and RESOURCE expected
  to show moderate change (mean d_T, d_R < 0.15 under style-only refactoring but
  potentially > 0.15 under loop unrolling).

#### 7. Minimum Meaningful Effect Size (MMES)

Cohen's d = 0.8 (medium-large) between D_sp and D_sc distributions.  
Equivalently: E[D_sc] − E[D_sp] ≥ 0.10 in absolute distance units.

#### 8. Statistical Test

- **Primary:** Two-sided Mann-Whitney U test (D values are non-normal, bounded [0,1]).
  Significance threshold α = 0.01 (Bonferroni-corrected for 6 hypotheses: α_adj = 0.0017).
- **Effect size:** Rank-biserial correlation r_rb and Cliff's delta δ.
- **Secondary:** Bootstrap 95% CI on E[D_sp] to confirm it is entirely below ε_stable = 0.05.

#### 9. Required Sample Size (Power Analysis)

Using G*Power for Mann-Whitney U, two-sided, α = 0.0017, power 1−β = 0.95,
assuming Cohen's d = 0.8:

- **n per group ≈ 60 program-pair observations** (conservative; accounts for
  non-normality by inflating by factor 1.15).
- With 50 programs × ≥ 5 preserving transforms × ≥ 5 mutations each = 250 pairs
  per group — well above minimum.

#### 10. Falsification Condition

H1 is **falsified** if any of the following hold:

- The Mann-Whitney U test fails to reject H1₀ at α_adj = 0.0017, OR
- E[D_sp] > 0.10 (semantics-preserving pairs are not near-zero distance), OR
- More than 10% of semantics-preserving pairs have D > ε_stable = 0.05, OR
- Cliff's delta < 0.4 between D_sp and D_sc distributions.

---

### H2 — Structured SBG Outperforms Baselines

**Formal summary:** SBG's 8-dimensional genome achieves higher precision and recall
for behavioral change detection than single-dimension or non-behavioral baselines
(code embeddings, syntactic diff, code2vec, CodeBERT).

#### 1. Null and Alternative Hypotheses

| | Statement |
|---|---|
| **H2₀** | There is no statistically significant difference in F1 score (regression detection) between the full 8-dimensional SBG and the best single-signal baseline. |
| **H2_A** | The full SBG achieves a higher F1 score (at optimal threshold θ*) than every evaluated baseline. |

#### 2. Independent Variables

| Variable | Values |
|---|---|
| Representation method | {SBG-8D, SBG-CONTROL-only, SBG-DATA-only, code2vec [20], CodeBERT [22], GraphCodeBERT [23], syntactic diff (lines changed), test-suite pass/fail oracle} |
| Program corpus | Defects4J v2.0 (395+ bugs across 17 Java projects) |
| Input distribution | I_prod (existing test inputs); I_cov (coverage-guided) |

#### 3. Dependent Variables

| Variable | Definition |
|---|---|
| Precision(θ) | TP / (TP + FP) for regression prediction at threshold θ |
| Recall(θ) | TP / (TP + FN) |
| F1(θ) | Harmonic mean of Precision and Recall |
| AUC-ROC | Area under ROC curve across all θ |
| AUC-PR | Area under precision-recall curve |

#### 4. Controls

- Gold standard: Defects4J bug-fixing commits define ground-truth regressions.
- Same input distribution applied to SBG and all baselines where applicable.
- Hyperparameters for learned baselines (code2vec, CodeBERT) tuned on a separate
  validation split; SBG threshold θ tuned on the same split.
- Evaluation on held-out test split only (60/20/20 train/val/test split by project).

#### 5. Operationalization

- For each consecutive version pair (P^k, P^{k+1}) in Defects4J:
  - Compute D(G^k, G^{k+1}) using full SBG-8D and each ablated variant.
  - Compute baseline similarity scores (cosine distance for embeddings; edit
    distance for syntactic diff).
  - Label pair as "regression" iff the Defects4J gold standard marks a bug fix.
  - Sweep θ from 0 to 1 in steps of 0.01; compute Precision/Recall/F1 at each.
  - Report F1 at optimal θ* (maximizes F1 on validation split).

#### 6. Expected Effect Direction and Magnitude

- **Direction:** F1(SBG-8D) > F1(best baseline).
- **Magnitude:** ΔAUC-ROC ≥ 0.08 over CodeBERT; ΔAUC-PR ≥ 0.10.
- **Mechanism:** SBG adds runtime behavioral signals invisible to static baselines.

#### 7. Minimum Meaningful Effect Size

ΔAUC-ROC ≥ 0.05 over the best static baseline (CodeBERT or GraphCodeBERT).
This threshold is operationally meaningful: a 5-point AUC gain corresponds to
~10% reduction in missed regressions at fixed false-positive rate.

#### 8. Statistical Test

- McNemar's test on paired classification outcomes (per version pair, SBG vs.
  each baseline). α = 0.0017.
- DeLong's test for AUC-ROC comparison.
- Bootstrap 95% CI on ΔAUC-ROC (10 000 resamples).

#### 9. Required Sample Size

DeLong test, ΔAUC = 0.08, baseline AUC = 0.75, α = 0.0017, power = 0.90:
**n ≈ 150 regression-labeled pairs** (Defects4J provides 395; well-powered).

#### 10. Falsification Condition

H2 is **falsified** if:

- Any single baseline achieves F1 ≥ F1(SBG-8D) with statistical significance, OR
- DeLong test shows AUC(SBG-8D) is not significantly greater than AUC(CodeBERT)
  at α_adj = 0.0017, OR
- SBG-8D achieves F1 < 0.70 on the held-out Defects4J test split regardless of
  threshold θ.

---

### H3 — Robustness Under Refactoring

**Formal summary:** The behavioral genome is robust to refactoring-class
transformations (rename, extract, inline, reorder, dead-code elimination):
D(G(P), G(T_refactor(P))) < ε_refactor for all transformations in a defined
refactoring taxonomy.

#### 1. Null and Alternative Hypotheses

| | Statement |
|---|---|
| **H3₀** | Mean behavioral distance after refactoring equals mean behavioral distance after semantics-changing mutation: E[D \| refactoring] = E[D \| mutation]. |
| **H3_A** | Mean behavioral distance after refactoring is significantly smaller than after mutation, with effect size ≥ MMES. |

#### 2. Independent Variables

| Variable | Values |
|---|---|
| Refactoring type | Rename-method, Extract-method, Inline-method, Move-method, Reorder-parameters, Dead-code elimination, Loop hoisting, Constant folding, Inlining of constants (9 types) |
| Transformation magnitude | Small (1–5 locations changed), Medium (6–20), Large (21+ locations) |
| Program domain | Data structures, algorithms, I/O-heavy, computation-heavy (4 categories) |

#### 3. Dependent Variables

- D(G(P), G(P_refactored)) for each refactoring type and magnitude.
- Per-dimension stability profile: which of the 8 dimensions are most/least robust.
- Fraction of pairs with D < ε_stable = 0.05 ("stable" rate).

#### 4. Controls

- Refactoring correctness verified by test-suite oracle (same as H1).
- Transformation performed by automated tool (IntelliJ IDEA refactoring engine for
  Java; rope for Python) to eliminate human error.
- Sample size N = 200 traces held constant.
- Input distribution fixed to I_prod.

#### 5. Operationalization

- Apply each of 9 refactoring types at each of 3 magnitudes to 50 programs (×3 =
  1350 refactored pairs total).
- Compute D(G(P), G(P_ref)) for each pair.
- Compute per-dimension distances d_k for each genome dimension k ∈ {C, D, S, R, T,
  E, X, U}.
- Fit a linear model: d_k ~ refactoring_type + magnitude + program_domain to
  identify dimension-specific sensitivity factors.

#### 6. Expected Effect Direction and Magnitude

- **Overall:** E[D \| refactoring] ≤ 0.05 across all 9 refactoring types.
- **Dimension-specific:**
  - CONTROL (g_C): robust under all renaming/extract/inline (E[d_C] < 0.02).
  - DATA (g_D): robust; only constant folding may shift value histograms slightly.
  - TEMPORAL (g_T): may increase under loop hoisting (E[d_T] < 0.15).
  - RESOURCE (g_R): may increase under dead-code elimination (E[d_R] < 0.10).
  - EXECUTION (g_U): sensitive to dead-code elimination (E[d_U] < 0.15).

#### 7. Minimum Meaningful Effect Size

Cohen's d = 0.8 between D_refactoring and D_mutation distributions.
Per-dimension: MMES for each d_k is 0.05 (absolute) vs. the semantics-changing baseline.

#### 8. Statistical Test

- Kruskal-Wallis test across 9 refactoring types (are they all stable?); post-hoc
  Dunn test with Holm correction.
- Paired Mann-Whitney U: D_refactoring vs D_mutation for each refactoring type.
- Linear mixed-effects model for per-dimension analysis (program as random effect).

#### 9. Required Sample Size

Kruskal-Wallis, 9 groups, MMES d=0.8, α=0.0017, power=0.90:
**n ≈ 15 per refactoring type** (actual: 50×3 = 150 per type — well-powered).

#### 10. Falsification Condition

H3 is **falsified** if:

- Any refactoring type produces E[D] > 0.10 (2× the stability threshold), OR
- More than 20% of any refactoring-type's pairs exceed D = 0.05, OR
- The Kruskal-Wallis test reveals that any refactoring type is indistinguishable
  from semantics-changing mutation at α_adj = 0.0017.

---

### H4 — Cross-Language Generalization

**Formal summary (from FORMAL_MODEL.md §H3):** After environment canonicalization
C_E, semantically equivalent programs in different languages receive behavioral
genomes with D < ε_xlang for the language-portable dimensions (CONTROL, DATA,
INTERACTION). Language-specific dimensions (EXECUTION) are excluded from this test.

#### 1. Null and Alternative Hypotheses

| | Statement |
|---|---|
| **H4₀** | Behavioral distance between cross-language equivalent pairs is not significantly smaller than distance between random non-equivalent cross-language pairs. |
| **H4_A** | D(C_E(G(P_lang1)), C_E(G(P_lang2))) is significantly smaller for equivalent pairs than for non-equivalent pairs, with ΔMEAN ≥ MMES, restricted to confirmed portable dimensions {g_D, g_X}. |

#### 2. Independent Variables

| Variable | Values |
|---|---|
| Language pair | Python↔Java, Python↔Go, Java↔C++, Java↔Rust, Python↔JavaScript (5 pairs) |
| Algorithm class | Sorting, searching, graph traversal, dynamic programming, string processing (5 classes) |
| Equivalence label | Same algorithm (equivalent) vs. different algorithm (non-equivalent) |

#### 3. Dependent Variables

- D_xlang: behavioral distance restricted to confirmed portable dimensions {g_D, g_X}
  after applying C_E canonicalization. g_C is measured separately as an exploratory
  secondary outcome (see §5 note below).
- Per-language-pair distance distribution.
- Dimension separability: which dimensions carry the most discriminative cross-
  language signal.

#### 4. Controls

- Equivalence oracle: both implementations pass a shared language-agnostic test
  oracle with identical I/O on ≥ 1000 test cases.
- Environment normalization C_E applied per Definition 22c of FORMAL_MODEL.md
  (SPECint normalization for RESOURCE).
- CONTROL dimension (g_C) is **excluded from the primary confirmatory D_xlang**
  because cross-language procedure alignment for g_C is an unresolved open problem
  (OP-4: no formal cross-language procedure correspondence map exists). g_C results
  are reported as EXPLORATORY/PRELIMINARY only.
- EXECUTION dimension (g_U) is explicitly excluded from cross-language D_xlang
  as documented in H4 caveat of FORMAL_MODEL.md.
- TEMPORAL (g_T) and RESOURCE (g_R) dimensions are excluded from cross-language
  D_xlang due to architecture-dependent normalization requirements (OP-6).
- Sample size N = 200 traces per genome under shared input distribution I_shared
  (language-agnostic inputs serialized as JSON).

#### 5. Operationalization

```
FOR each algorithm class A in 5 classes:
  FOR each language pair (L1, L2) in 5 pairs:
    P_L1 := implementation of A in L1
    P_L2 := implementation of A in L2
    P_L2_other := implementation of DIFFERENT algorithm in L2
    G1 := Phi(P_L1, S_N) with C_E canonicalization
    G2 := Phi(P_L2, S_N) with C_E canonicalization
    G3 := Phi(P_L2_other, S_N) with C_E canonicalization
    D_equiv := D_portable(G1, G2)   # equivalent pair
    D_nonequiv := D_portable(G1, G3) # non-equivalent pair
COMPARE distributions {D_equiv} vs {D_nonequiv}
```

where D_portable (PRIMARY) uses only confirmed portable dimensions {g_D, g_X}
with weights w_D = w_X = 1/2, w_others = 0.

NOTE: g_C (CONTROL) is measured as an EXPLORATORY secondary outcome using a
manually verified procedure correspondence table for the 5 algorithm classes.
This is not part of the primary H4 confirmatory test. Cross-language g_C results
must be explicitly labelled EXPLORATORY/PRELIMINARY in all reports until OP-4
(cross-language procedure alignment) is formally resolved.

#### 6. Expected Effect Direction and Magnitude

- **Direction:** E[D_equiv] ≪ E[D_nonequiv].
- **Magnitude:** E[D_equiv] < 0.15 (ε_xlang); E[D_nonequiv] > 0.40.
- **Strongest confirmed signal:** g_X (syscall/interaction sequences) expected
  to be most stable cross-language.
- **Second confirmed signal:** g_D (value distributions; may show some variation
  due to language-specific numeric representations).
- **Exploratory only:** g_C (control-flow topology) — results reported separately
  with EXPLORATORY label; not used in primary H4 test statistic.

#### 7. Minimum Meaningful Effect Size

Cliff's delta δ ≥ 0.5 between D_equiv and D_nonequiv distributions.
Absolute: E[D_nonequiv] − E[D_equiv] ≥ 0.20.

#### 8. Statistical Test

- Mann-Whitney U test: D_equiv vs D_nonequiv, α = 0.0017.
- Linear mixed model: D_equiv ~ language_pair + algorithm_class (random effects)
  to assess generalization across language pairs.
- Bootstrap 95% CI on ε_xlang estimate from the D_equiv distribution.

#### 9. Required Sample Size

Mann-Whitney U, Cliff's delta = 0.5, α = 0.0017, power = 0.90:
**n ≈ 35 pairs per language pair** (actual: 5 algorithm classes × multiple
implementations ≥ 3 per class = 15+ equivalent pairs per language pair — borderline;
augment with RosettaCode implementations to reach n = 35+).

#### 10. Falsification Condition

H4 is **falsified** if:

- E[D_equiv] > ε_xlang = 0.20 (cross-language equivalent pairs are not near each
  other in genome space), OR
- Mann-Whitney test fails to reject H4₀ at α_adj = 0.0017, OR
- The 95% CI for E[D_equiv] entirely exceeds 0.15 on any of the 5 language pairs.

---

### H5 — Regression Detection (Genome as Oracle)

**Formal summary (from FORMAL_MODEL.md §H5):** There exists a threshold θ* such
that SBG achieves Recall(θ*) ≥ 0.80 and Precision(θ*) ≥ 0.70 on a held-out
regression corpus.

#### 1. Null and Alternative Hypotheses

| | Statement |
|---|---|
| **H5₀** | At all thresholds θ, AUC-ROC(SBG) ≤ 0.70 on the held-out regression corpus (equivalent to: SBG is not better than a moderately informed classifier). |
| **H5_A** | AUC-ROC(SBG) > 0.80 and there exists θ* with Recall(θ*) ≥ 0.80, Precision(θ*) ≥ 0.70 on the held-out corpus. |

#### 2. Independent Variables

| Variable | Values |
|---|---|
| SBG threshold θ | Swept 0.0 → 1.0 in steps of 0.01 |
| Input distribution | {I_prod, I_cov, I_adv} |
| Program corpus split | Train (60%) / Validation (20%) / Test (20%) — by project, not version |

#### 3. Dependent Variables

- Precision(θ), Recall(θ), F1(θ) over Defects4J regression labels.
- AUC-ROC, AUC-PR.
- θ* (optimal threshold, tuned on validation split).
- Per-regression-type performance: null dereference, off-by-one, logic error,
  resource leak, concurrency (5 regression categories from Defects4J taxonomy).

#### 4. Controls

- Gold standard: Defects4J [28] confirmed bug-fixing commits with at least one
  failing test case.
- θ* is selected exclusively on validation split; test-set evaluation is one-shot.
- Same N = 200 traces per genome, I = I_prod (baseline) and I = I_cov (extended).
- Baselines from H2 are reproduced under identical conditions for comparison.

#### 5. Operationalization

- Extract all consecutive-version pairs from Defects4J (project × version).
- For each pair, compute D(G^k, G^{k+1}).
- Label each pair: regression (1) if Defects4J marks it as a bug-fix commit, else 0.
- Sweep θ on validation split to find θ* = argmax F1(θ).
- Evaluate Precision(θ*), Recall(θ*), AUC-ROC, AUC-PR on held-out test split.
- Repeat under I_cov and I_adv to measure recall improvement from richer sampling.

#### 6. Expected Effect Direction and Magnitude

- **AUC-ROC:** ≥ 0.82 under I_prod; ≥ 0.88 under I_cov.
- **At θ*:** Precision ≥ 0.70, Recall ≥ 0.80, F1 ≥ 0.74.
- **Per-category:** Null-dereference regressions expected highest recall (strongly
  manifests in ERROR dimension g_E). Concurrency regressions expected lowest recall
  (non-deterministic; require I_adv).

#### 7. Minimum Meaningful Effect Size

AUC-ROC ≥ 0.80 (vs. H5₀ baseline of 0.70). This represents a 10-point AUC gain,
corresponding operationally to a 15–20% reduction in missed regressions at fixed
false-positive rate.

#### 8. Statistical Test

- DeLong's test: AUC(SBG) vs. AUC(best baseline from H2), α = 0.0017.
- Bootstrap 95% CI on AUC-ROC (10 000 resamples).
- McNemar test on per-pair classification (SBG vs. best baseline).

#### 9. Required Sample Size

DeLong test, ΔAUC = 0.10, α = 0.0017, power = 0.90:
**n ≈ 100 labeled regression pairs.** Defects4J provides 395+ — adequate.

#### 10. Falsification Condition

H5 is **falsified** if:

- AUC-ROC < 0.80 on held-out test split under any input distribution tried, OR
- No threshold θ achieves both Recall ≥ 0.80 AND Precision ≥ 0.70 simultaneously,
  OR  
- The F1 at optimal θ* falls below 0.70 on the held-out test split.

---

### H6 — Multi-Dimensional Value

**Formal summary:** The full 8-dimensional SBG provides strictly more information
than any strict subset of dimensions; each dimension contributes unique,
non-redundant behavioral signal that improves at least one downstream task.

#### 1. Null and Alternative Hypotheses

| | Statement |
|---|---|
| **H6₀** | For every task (regression detection, clone detection, cross-language matching), there exists a strict subset S ⊂ {C,D,S,R,T,E,X,U} with |S| ≤ 6 such that D_S achieves the same performance as D_full-8D (no statistically significant difference). |
| **H6_A** | For at least one task, adding each of the 8 dimensions individually provides a statistically significant improvement over the 7-dimensional ablation that omits it. |

#### 2. Independent Variables

| Variable | Values |
|---|---|
| Dimension subset | All 2^8 = 256 subsets (full ablation study); focus on 8 leave-one-out subsets and 8 single-dimension variants |
| Task | Regression detection (Defects4J), semantic clone detection (BigCloneBench), cross-language matching (H4 corpus) |

#### 3. Dependent Variables

- AUC-ROC for each task × dimension-subset.
- Mutual information I(d_k; task_label) for each individual dimension k.
- Correlation matrix between per-dimension distances (to assess redundancy).

#### 4. Controls

- All ablations use the same N = 200 traces, I = I_prod, corpus.
- Dimension weights in ablated SBG renormalized to uniform over included dimensions.
- Task evaluation protocols identical to H2 and H5.

#### 5. Operationalization

- For each of 8 leave-one-out ablations (omit dimension k), compute AUC-ROC on
  each of 3 tasks.
- For each individual dimension k, compute AUC-ROC as a standalone predictor.
- Compute Pearson correlation matrix of {d_C, d_D, d_S, d_R, d_T, d_E, d_X, d_U}
  over the version-pair corpus.
- Fit a LASSO regression model: task_label ~ d_C + d_D + ... + d_U to identify
  dimensions with non-zero coefficients (non-redundant contributors).

#### 6. Expected Effect Direction and Magnitude

- **All 8 dimensions contribute:** Each leave-one-out ablation shows ΔAUC-ROC ≥ 0.03
  drop vs. full model.
- **Least individually powerful:** TEMPORAL (g_T) and ERROR (g_E) have lowest
  standalone AUC, but both contribute non-redundant signal to the full model.
- **Low inter-dimension correlation:** All |r(d_j, d_k)| < 0.5 for j ≠ k (each
  dimension captures a distinct behavioral facet).

#### 7. Minimum Meaningful Effect Size

ΔAUC-ROC ≥ 0.03 per omitted dimension (operationally: loss of 3+ points AUC when
any one dimension is removed).

#### 8. Statistical Test

- Friedman test across 9 model variants (8 ablations + full) on AUC-ROC; post-hoc
  Nemenyi test with Holm correction.
- Paired DeLong test: full model vs. each leave-one-out ablation.
- LASSO path analysis with cross-validated λ selection.

#### 9. Required Sample Size

Friedman test, 9 groups, MMES Cohen's f = 0.25, α = 0.0017, power = 0.90:
**n ≈ 60 version pairs.** Actual corpus provides 395+ — well-powered.

#### 10. Falsification Condition

H6 is **falsified** if:

- Any strict subset of ≤ 6 dimensions achieves equal AUC-ROC as the 8-dimensional
  model (DeLong p > 0.0017) on all 3 tasks, OR
- LASSO selects ≤ 5 dimensions with non-zero coefficients on any task at 5-fold
  cross-validation, OR
- Any two dimensions have |r(d_j, d_k)| > 0.85 (near-perfect redundancy).

---

## Part II — Mechanistic Sub-Hypotheses

These hypotheses provide insight into *why* the primary hypotheses hold (or fail),
and are prerequisite to designing effective SBG implementations.

---

### SH-1 — Dimension-Wise Stability Ordering

**Informal statement:** Under semantics-preserving transformations, the 8 genome
dimensions exhibit a consistent stability ordering: CONTROL ≈ DATA ≈ INTERACTION >
STATE > ERROR > RESOURCE > TEMPORAL > EXECUTION.

**Formal statement:**

Let σ_k = E[d_k \| ≡_S] be the mean per-dimension distance under semantics-
preserving transformations. We hypothesize:

  σ_C ≤ σ_D ≤ σ_X ≤ σ_S ≤ σ_E ≤ σ_R ≤ σ_T ≤ σ_U

with each adjacent inequality strict (non-trivially ordered).

**Operationalization:** Extract per-dimension distances d_k from the H1/H3
experiments. Compute E[d_k] per dimension. Test ordering with a one-sided
Mann-Whitney U between each adjacent pair.

**Mechanistic insight:** If this ordering holds, it justifies the FORMAL_MODEL.md
caveat (TEMPORAL and RESOURCE may change under semantics-preserving optimization),
and guides which dimensions to use for which comparison tasks.

**Falsification:** Any inversion of an adjacent pair with |E[d_j] − E[d_k]| > 0.03.

---

### SH-2 — Input Coverage Governs Sensitivity

**Informal statement:** The sensitivity of SBG (ability to detect semantic changes)
is monotonically increasing in the coverage of regression-triggering inputs.
Formally: Recall(SBG, I_cov) > Recall(SBG, I_prod) > Recall(SBG, I_unif).

**Operationalization:** For each regression in Defects4J, compute the probability
μ_prod(Δ) where Δ = {inputs that witness the behavioral difference}. Stratify
regressions into rare-trigger (μ_prod(Δ) < 0.01), medium (0.01–0.1), and
common (> 0.1). Compare Recall under I_prod, I_unif, I_cov for each stratum.

**Mechanistic insight:** This hypothesis directly tests the formal dependency of H2
on input coverage (FORMAL_MODEL.md §H2: "H2 depends on S covering inputs in Δ").
It motivates when to use coverage-guided inputs vs. production inputs.

**Falsification:** Recall(I_prod) ≥ Recall(I_cov) on rare-trigger regressions, or
Recall(I_unif) ≥ Recall(I_prod) on common regressions.

---

### SH-3 — Genome Convergence Rate

**Informal statement:** The error ||G_N(P) − G_∞(P)||_G decreases as O(1/√N) in
trace sample size N, and convergence is faster for programs with lower behavioral
variance across inputs.

**Operationalization (addressing Open Problem OP-1 from FORMAL_MODEL.md):**
- For N ∈ {10, 25, 50, 100, 200, 500, 1000}:
  - Compute G_N(P) for 20 programs.
  - Estimate G_∞(P) using N = 10 000 traces as reference.
  - Compute ||G_N − G_∞||_G.
- Fit a log-log regression: log||error|| ~ α·log(N) + β.
- Test H0: α = −0.5 (O(1/√N) convergence) vs. H_A: α ≠ −0.5.
- Also compute behavioral variance σ²_P (variance of per-trace genome components
  across inputs) and test correlation with convergence rate.

**Mechanistic insight:** Establishes the practical minimum N for reliable genome
extraction (addresses OP-1). If α ≈ −0.5, then N = 200 traces gives ~14× smaller
error than N = 10, justifying the protocol used in H1–H6.

**Falsification:** α > −0.3 (convergence slower than O(N^{-0.3})), implying that
even N = 1000 traces is insufficient for reliable genome estimation on high-variance
programs.

---

### SH-4 — Behavioral Distance is Locally Monotone in Code Change Size

**Informal statement:** Within a single project's history, genome distance D(G^k,
G^{k+1}) is positively correlated with syntactic change magnitude |Δ_code|, at
least in expectation across typical (non-adversarial) commits.

**Operationalization (tests H4 from FORMAL_MODEL.md §H4):**
- Extract all consecutive version pairs from 10 GitHub projects (≥ 100 commits each).
- Compute |Δ_code| as the number of lines changed (git diff --stat).
- Compute D(G^k, G^{k+1}) for each pair.
- Compute Spearman correlation ρ(|Δ_code|, D) per project.
- Test H0: ρ = 0; H_A: ρ > 0.
- Separately analyze: commits labeled as refactoring (commit message contains
  "refactor", "rename", "cleanup") vs. feature commits vs. bug fixes.

**Mechanistic insight:** Confirms the O(|Δ_code|^α) claim of FORMAL_MODEL.md §H4
and identifies the α exponent. Also identifies the breakdown cases (adversarial
small changes with large behavioral impact).

**Falsification:** Median ρ < 0.2 across projects (near-zero correlation), or
ρ < 0 on any project (inverse relationship — larger changes produce smaller
genome distance).

---

### SH-5 — Dimension-Task Specialization

**Informal statement:** Different SBG dimensions provide primary signal for
different downstream tasks: g_C and g_D dominate for algorithm-equivalence
detection; g_E and g_R dominate for resource-regression detection; g_X and g_S
dominate for security-behavioral analysis.

**Operationalization:**
- Define 4 tasks: (T1) algorithm equivalence, (T2) performance regression,
  (T3) null-dereference bug detection, (T4) output-behavior regression.
- For each task and each dimension k, compute AUC-ROC of d_k as a standalone
  predictor (as per H6 operationalization).
- For each task, identify the dimension k* with highest standalone AUC.
- Test whether k* matches the above prediction using a Friedman test across
  dimensions within each task (α = 0.01).

**Mechanistic insight:** If confirmed, this hypothesis justifies task-specific
dimension weighting (non-uniform w_k in Definition 18 of FORMAL_MODEL.md) as
a principled improvement over uniform weights. It also guides practitioners: for
performance regression detection, focus on g_R and g_T; for behavioral equivalence,
focus on g_C and g_D.

**Falsification:** No single dimension has AUC ≥ 0.65 as a standalone predictor
for any of the 4 tasks (all dimensions are weak individually), or the predicted
dominant dimension for any task is not in the top 2 dimensions by AUC.

---

## Part III — Prerequisite Order

The following dependency graph defines which hypotheses must hold before others
can be meaningfully interpreted.

```
SH-3 (convergence)
  └─► H1 (stability)   ← must establish that D is small for equiv pairs
        └─► H2 (baselines outperformed)   ← needs H1 to define "small D"
        └─► H3 (robustness under refactoring)  ← H1 specialized to refactoring
        └─► H5 (regression oracle)   ← needs D to be small for equiv pairs
              └─► H2 (confirms H5 is better than alternatives)

SH-2 (input coverage)
  └─► H5 (regression oracle)  ← recall depends on input coverage
  └─► H4 (cross-language)     ← shared inputs required

SH-4 (monotonicity)
  └─► H4 (cross-language) ← monotonicity underpins versioning claim

SH-1 (dimension stability ordering)
  └─► H6 (multi-dimensional value)  ← need to know which dims contribute

H1 + H3 + SH-1
  └─► H6 (multi-dimensional value)  ← full picture of dimension contributions
```

**Summary table:**

| Hypothesis | Prerequisites |
|---|---|
| SH-3 | None (can be tested with any single program) |
| SH-2 | None (independent of other hypotheses) |
| H1 | SH-3 (to validate N sufficiency) |
| H3 | H1 (stability is the broader claim; H3 specializes it) |
| SH-1 | H1 (needs per-dimension data from H1 experiments) |
| SH-4 | H1 (needs D to be validated before testing monotonicity) |
| H2 | H1, H5 (baselines comparison meaningful only if SBG signal exists) |
| H4 | SH-2, SH-3 (needs sufficient N and appropriate input distribution) |
| H5 | H1, SH-2 (recall requires sensitivity; input coverage matters) |
| H6 | H1, H3, SH-1 (need all dimension stability data) |

**Recommended experimental sequence:**
1. SH-3 → establish N = 200 as sufficient
2. SH-2 → characterize input distributions
3. H1 → establish stability claim
4. H3 + SH-1 → characterize per-dimension robustness
5. SH-4 → test monotonicity
6. H4 → cross-language (needs input protocol from SH-2)
7. H5 → regression oracle (needs H1 and SH-2)
8. H2 → baseline comparison (needs H5 results)
9. H6 → multi-dimensional value (needs all prior results)

---

## Part IV — Research Question Hierarchy

### RQ1 (Primary): Behavioral Genome Invariance

**Question:** Does the Software Behavior Genome remain stable under semantics-
preserving transformations while being sensitive to semantics-changing
transformations?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| Mean D under semantics-preserving pairs | < 0.05 |
| Mean D under semantics-changing pairs | > 0.25 |
| Mann-Whitney p-value (D_sp vs D_sc) | < 0.0017 |
| Cliff's delta | ≥ 0.5 |
| Fraction of preserving pairs with D < 0.05 | ≥ 85% |
| Fraction of changing pairs with D > 0.10 | ≥ 90% |

**Covered hypotheses:** H1 (primary), H3 (robustness), SH-1 (dimension ordering).

---

### RQ2 (Secondary): Discriminative Power Over Baselines

**Question:** Does the structured 8-dimensional SBG outperform single-signal
baselines (code embeddings, syntactic diff, test-suite oracle) in detecting
behavioral regressions?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| AUC-ROC (SBG-8D) on Defects4J test split | ≥ 0.80 |
| ΔAUC-ROC over best static baseline | ≥ 0.05 |
| DeLong test p-value vs. CodeBERT | < 0.0017 |
| F1 at optimal θ* | ≥ 0.74 |
| Precision at θ* | ≥ 0.70 |
| Recall at θ* | ≥ 0.80 |

**Covered hypotheses:** H2, H5.

---

### RQ3 (Secondary): Refactoring Robustness Profile

**Question:** Which refactoring transformations are most/least challenging for
SBG stability, and which genome dimensions drive the instability?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| E[D] for each of 9 refactoring types | < 0.10 |
| E[D] for rename/extract/inline | < 0.03 |
| E[d_T], E[d_R] under loop hoisting | < 0.15 |
| Fraction of all refactoring pairs with D < 0.05 | ≥ 80% |
| Linear model R² (D ~ refactoring_type + magnitude) | Report as-is (descriptive) |

**Covered hypotheses:** H3, SH-1.

---

### RQ4 (Secondary): Cross-Language Behavioral Equivalence

**Question:** Can SBG identify semantically equivalent programs across programming
languages using language-portable genome dimensions?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| E[D_xlang] for equivalent cross-language pairs | < 0.15 |
| E[D_xlang] for non-equivalent pairs | > 0.35 |
| Cliff's delta (equiv vs non-equiv) | ≥ 0.5 |
| AUC-ROC for cross-language equivalence detection | ≥ 0.80 |
| Generalization across all 5 language pairs | All 5 pass at α = 0.01 |

**Covered hypotheses:** H4, SH-2.

---

### RQ5 (Secondary): Regression Detection Without Test Suite

**Question:** Can genome distance serve as a test-suite-free regression oracle
on real-world bug corpora, and does richer input sampling improve detection?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| AUC-ROC (I_prod) | ≥ 0.80 |
| AUC-ROC (I_cov) | ≥ 0.85 |
| Recall at θ* (I_prod) | ≥ 0.80 |
| Recall at θ* (I_cov) | ≥ 0.88 |
| Recall improvement I_cov vs I_prod (rare-trigger bugs) | ≥ 0.15 |

**Covered hypotheses:** H5, SH-2.

---

### RQ6 (Secondary): Multi-Dimensional Complementarity

**Question:** Does each of the 8 genome dimensions contribute independent,
non-redundant behavioral signal across tasks?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| ΔAUC-ROC when any dimension omitted | ≥ 0.03 drop |
| Max pairwise dimension correlation max|r(d_j, d_k)| | < 0.70 |
| LASSO non-zero coefficients (at best λ) | ≥ 6 of 8 dimensions |
| Friedman test p-value (9 model variants) | < 0.0017 |

**Covered hypotheses:** H6, SH-1, SH-5.

---

### RQ7 (Exploratory): Genome Convergence and Minimum Sample Size

**Question:** What is the minimum number of execution traces N* required to
produce a reliable behavioral genome estimate, and how does it depend on program
behavioral variance?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| Convergence exponent α in ||G_N − G_∞|| = O(N^α) | Report α; pass if α < −0.3 |
| N at which ||G_N − G_∞|| < 0.01 | Report per program; pass if ≤ 500 for 80% of programs |
| Correlation between behavioral variance σ²_P and N* | Report ρ (descriptive) |

**Covered hypotheses:** SH-3, addresses OP-1 of FORMAL_MODEL.md.

---

### RQ8 (Exploratory): Dimension-Task Specialization

**Question:** Do specific genome dimensions provide dominant signal for specific
task categories (algorithm equivalence, performance regression, bug class detection)?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| Predicted dominant dimension is top-2 by AUC for ≥ 3 of 4 tasks | Must achieve |
| Standalone AUC of predicted dominant dimension | ≥ 0.65 per task |
| Improvement from task-specific weights vs. uniform | ΔAUC-ROC ≥ 0.03 |

**Covered hypotheses:** SH-5.

---

### RQ9 (Exploratory): Monotonicity of Genome Distance in Code Change Size

**Question:** Is genome distance monotonically increasing in syntactic change
magnitude across a real project's commit history, and where does this relationship
break down?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| Spearman ρ(|Δ_code|, D) median across 10 projects | ≥ 0.30 |
| ρ > 0 in ≥ 7 of 10 projects | Must achieve |
| Fraction of commits where small |Δ_code| produces large D (adversarial pattern) | Report as breakdown rate |

**Covered hypotheses:** SH-4.

---

### RQ10 (Exploratory): Genome Collision Rate (Uniqueness)

**Question:** What fraction of unrelated program pairs have genome distance below
ε_collision = 0.05, confirming that the genome space has low collision rate?

**Evaluation Criteria:**

| Criterion | Pass Threshold |
|---|---|
| Fraction of random unrelated pairs with D < 0.05 | ≤ 0.01 (1%) |
| Mean D for random unrelated pairs | ≥ 0.40 |
| Fraction of pairs with D < 0.10 | ≤ 0.05 |

**Covered hypotheses:** FORMAL_MODEL.md H6 (Behavioral Genome Uniqueness, not in
the primary H1–H6 taxonomy of this document but logically adjacent to H6 here).

---

## Summary

| ID | Type | Covered by RQ | Prerequisites | Status |
|---|---|---|---|---|
| H1 | Primary | RQ1 | SH-3 | Core claim |
| H2 | Secondary | RQ2 | H1, H5 | Validation |
| H3 | Secondary | RQ3 | H1 | Robustness |
| H4 | Secondary | RQ4 | SH-2, SH-3 | Generalization |
| H5 | Secondary | RQ5 | H1, SH-2 | Application |
| H6 | Secondary | RQ6 | H1, H3, SH-1 | Design |
| SH-1 | Mechanistic | RQ3, RQ6 | H1 | Explanatory |
| SH-2 | Mechanistic | RQ5, RQ4 | None | Explanatory |
| SH-3 | Mechanistic | RQ7 | None | Foundational |
| SH-4 | Mechanistic | RQ9 | H1 | Explanatory |
| SH-5 | Mechanistic | RQ8 | H6 | Design guidance |

---

*This document was produced by Agent 0E for the SBG project. All operationalizations
reference Definitions and Hypotheses from FORMAL_MODEL.md (Agent 0B). Statistical
thresholds apply Bonferroni correction (6 primary hypotheses, α = 0.01 → α_adj =
0.0017). Power analyses use standard G*Power parameters (power = 0.90, two-sided)
unless noted otherwise.*

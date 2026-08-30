# Research Questions — Software Behavior Genome (SBG)
## Phase 2 — Locked Scientific Questions

**Date:** 2025  
**Status:** LOCKED — Phase 2 gate. Do not modify after experiments begin.  
**Basis:** Phase 1 literature audit, Phase 0 failure ledger, V5 experimental results.

---

## Preamble: What Phase 0 Taught Us

Before locking research questions, the Phase 0 forensic audit established three critical boundary conditions:

1. **The 93.3% regression detection number must not be used as an SBG metric** — it is an output oracle result.
2. **DEV AUROC = 0.488 (below chance)** — the test-set result (0.546) may reflect small-sample variance.
3. **exception_fraction beats the full genome** — the current feature design has a structural flaw (exception dominance).

These facts constrain the research questions: the RQs cannot assume SBG works well. They must test whether and under what conditions SBG provides signal above baselines.

---

## Hard Rules Governing All RQs

- **NO test-set contamination**: Every threshold, weight, or design decision is fixed before examining test-set labels.
- **NO output use in predictor**: The SBG distance function must not access program return values.
- **BOTH YES and NO are valid scientific results**: A null result is publishable if the methodology is sound.
- **Ground truth and predictor are independent systems**: The oracle may use outputs; the predictor must not.
- **Multiple-comparison correction**: All family-wise tests use Holm-Bonferroni (α = 0.05 family-wise).

---

## RQ1 — Does output-free behavioral distance distinguish semantic change from semantic preservation above the exception-fraction baseline?

### Full Specification

| Field | Value |
|---|---|
| **Hypothesis (H₀)** | AUROC(SBG-V5-identity) ≤ AUROC(exception_fraction) |
| **Hypothesis (H₁)** | AUROC(SBG-V5-identity) > AUROC(exception_fraction) |
| **Independent variable** | Behavioral representation: SBG-V5-identity vs. exception_fraction |
| **Dependent variable** | AUROC on the frozen test split |
| **Dataset** | Main synthetic benchmark — frozen test split (N=744 pairs, 13 programs) |
| **Ground truth** | Programmatic mutation labels (SP = semantics-preserving transform; SC = semantics-changing mutation) — generated before experiments |
| **Baseline** | exception_fraction standalone (AUROC=0.593, from artifacts/v5) |
| **Metric** | AUROC (Wilcoxon-Mann-Whitney, tie-aware); 95% CI via bootstrap (1000 resamples, seed=42, clustered by program) |
| **Statistical test** | One-tailed Mann-Whitney U test comparing score distributions; ΔCI construction via paired bootstrap |
| **Effect size** | Cliff's delta between SBG-V5-identity and exception_fraction score distributions |
| **Multiple comparisons** | This is RQ1 (family member 1 of 6); correction applied jointly |
| **Success criterion** | AUROC(SBG-V5-identity) > 0.593 AND CI lower bound > 0.500 AND p < 0.05 (one-tailed, Holm-corrected) |
| **Failure interpretation** | If SBG-V5-identity ≤ exception_fraction: the multi-dimensional genome does not add behavioral signal beyond the simplest exception statistic on the current benchmark. This is a valid result — it means the representation needs redesign, not that the research question is wrong. |
| **PRE-REGISTRATION NOTE** | This threshold (0.593) is fixed from prior experiments. It must NOT be adjusted after seeing test-set scores. |

---

## RQ2 — Does the V5 rename-invariant identity normalization improve robustness on SP-2 pairs?

### Full Specification

| Field | Value |
|---|---|
| **Hypothesis (H₀)** | AUROC(V5-identity, SP-2 subset) ≤ AUROC(V3-baseline, SP-2 subset) |
| **Hypothesis (H₁)** | AUROC(V5-identity, SP-2 subset) > AUROC(V3-baseline, SP-2 subset) |
| **Independent variable** | Normalizer: V3 (first-call-order anonymization) vs. V5 (invariant_identity.py) |
| **Dependent variable** | AUROC on SP-2 (rename) subset of test split |
| **Dataset** | SP-2 pairs only from the test split (rename transforms; exact N to be confirmed from test split) |
| **Ground truth** | SP label (all SP-2 pairs are semantics-preserving → should be scored as low distance) |
| **Baseline** | V3 baseline SP-2 AUROC (known: 0.259 from artifacts) |
| **Metric** | AUROC; mean_similarity on SP-2 pairs (should approach 1.0 if invariant) |
| **Statistical test** | Paired bootstrap for ΔAUROC on SP-2 subset; Wilcoxon signed-rank on per-pair distances |
| **Effect size** | Cohen's d on distance distributions (V3 vs. V5) for SP-2 pairs |
| **Success criterion** | V5 AUROC(SP-2) > 0.500 (i.e., no longer below chance) AND mean_sim(SP-2) > 0.750 |
| **Failure interpretation** | If V5-identity does not improve SP-2 AUROC: the unit-test-passing implementation does not generalize to the full benchmark pair population. The 12/12 unit tests are not sufficient evidence of generalization. |

---

## RQ3 — What is the honest SBG detection rate on the regression corpus when the predictor is SBG distance (not output comparison)?

### Full Specification

| Field | Value |
|---|---|
| **Hypothesis (H₀)** | SBG-distance detection rate (at threshold τ*) ≤ 0.600 on the 15-pair regression corpus |
| **Hypothesis (H₁)** | SBG-distance detection rate (at threshold τ*) > 0.600 |
| **Independent variable** | Predictor: SBG-V5 distance vs. output_divergence oracle |
| **Dependent variable** | Detection rate on the 15 regression pairs (fraction of bugs correctly flagged as CHANGED) |
| **Dataset** | 15-pair regression corpus (`experiments/v5/regression_evaluator.py`) |
| **Ground truth** | Manual labels: each pair has a known bug type (off_by_one, wrong_operator, etc.); label is CHANGED |
| **Oracle independence** | Ground truth: bug label. Predictor: SBG distance. Output comparison is a SEPARATE BASELINE (not the predictor). |
| **Threshold** | τ* = median SBG distance on SP pairs from DEV set — fixed BEFORE running on regression corpus |
| **Metric** | Detection rate (recall at τ*); Precision, F1 at τ*; compare to output oracle (93.3%) and exception_fraction (20.0%) |
| **Statistical test** | Exact binomial test: H₀: p(detection) ≤ 0.60; N=15; one-tailed |
| **Effect size** | Cohen's h (difference between proportions) vs. exception_fraction detection rate |
| **Success criterion** | Detection rate > 0.600 (9/15 or more) at τ*; lower than 93.3% is expected and acceptable |
| **Failure interpretation** | If SBG distance detects < 9/15: the output-free SBG predictor does not reliably detect real-world bug patterns. This is the honest answer to whether SBG works for regression detection. |
| **CRITICAL NOTE** | The previous 93.3% figure MUST be retired as an SBG detection rate. It may be cited only as "output oracle baseline." |

---

## RQ4 — On real Python bugs (BugsInPy), does SBG distance separate buggy from fixed versions above chance?

### Full Specification

| Field | Value |
|---|---|
| **Hypothesis (H₀)** | AUROC(SBG-V5-identity, BugsInPy) ≤ 0.500 |
| **Hypothesis (H₁)** | AUROC(SBG-V5-identity, BugsInPy) > 0.500 |
| **Independent variable** | Behavioral representation (SBG-V5-identity) vs. random baseline |
| **Dependent variable** | AUROC on BugsInPy pairs |
| **Dataset** | BugsInPy Python bugs — pilot on accessible projects (targets: pandas, requests, scrapy) |
| **Ground truth** | BugsInPy bug labels: buggy_version + fixed_version for each bug ID. Label: CHANGED (bug exists). Negatives: semantics-preserving refactoring commits in same project if available; otherwise test-set SP pairs. |
| **Baseline** | Random (0.500); exception_fraction on same pairs; AST edit distance on same pairs |
| **Metric** | AUROC; bootstrap CI (1000 resamples, seed=42) |
| **Statistical test** | One-tailed bootstrap test; permutation test (1000 permutations, seed=42) |
| **Effect size** | Cliff's delta vs. random baseline |
| **Success criterion** | AUROC > 0.550 AND permutation p < 0.05 |
| **Failure interpretation** | If AUROC ≈ 0.500 on BugsInPy: SBG does not generalize from synthetic mutations to real Python bugs. This would be a major negative finding — the synthetic benchmark does not predict real-world performance. |
| **Feasibility gate** | If fewer than 20 BugsInPy pairs can be executed successfully (dependency/environment failures), pivot to QuixBugs Python (40 pairs). Document pivot decision explicitly. |

---

## RQ5 — Does the multi-dimensional SBG genome add incremental information beyond the strongest single-feature baseline?

### Full Specification

| Field | Value |
|---|---|
| **Hypothesis (H₀)** | Incremental AUROC delta (full SBG − best single feature) ≤ 0 |
| **Hypothesis (H₁)** | Incremental delta > 0 |
| **Independent variable** | Feature set: single-feature ablations vs. full genome |
| **Dependent variable** | Incremental AUROC delta (full model minus each single feature) |
| **Dataset** | Frozen test split (N=744) |
| **Ground truth** | Mutation labels |
| **Features tested** | exception_fraction, call_bigrams, coverage_size, call_count, temporal_trigrams, state_transitions |
| **Metric** | Per-feature AUROC; incremental delta; CI on delta |
| **Statistical test** | Paired bootstrap on ΔAU ROC for each ablation; Holm-Bonferroni over all comparisons |
| **Effect size** | Cohen's d on score distributions (full vs. ablation) |
| **Success criterion** | Incremental delta > +0.020 for at least one ablation AND statistically significant (p < 0.05 Holm-corrected) |
| **Failure interpretation** | If incremental delta ≤ 0 for all single-feature comparisons: the multi-dimensional design adds no measurable value. Current evidence (V5) shows delta = -0.043. This RQ tests whether V5-identity integration changes this. |

---

## RQ6 — On the adversarial hard-negative benchmark, what is SBG-V5-identity distance performance (not the output oracle)?

### Full Specification

| Field | Value |
|---|---|
| **Hypothesis (H₀)** | SBG-V5-identity accuracy on hard-negative pairs ≤ 0.500 |
| **Hypothesis (H₁)** | SBG-V5-identity accuracy > 0.500 |
| **Independent variable** | Predictor: SBG-V5-identity distance vs. exception_fraction vs. output oracle |
| **Dependent variable** | Accuracy (fraction correct) on 12 hard-negative pairs |
| **Dataset** | 12 hard-negative pairs (`benchmark/v5/hard_negatives/`) |
| **Ground truth** | Manual labels (known for each pair) |
| **Baseline** | exception_fraction (5/12 = 41.7%); output oracle (12/12 = 100%) |
| **Threshold** | Same τ* as RQ3 (pre-fixed before running) |
| **Metric** | Accuracy; per-category breakdown |
| **Statistical test** | Exact binomial test (N=12, H₀: p≤0.5) |
| **Success criterion** | SBG-V5-identity accuracy > 8/12 (66.7%) AND exceeds exception_fraction (5/12) |
| **Failure interpretation** | If SBG-V5-identity ≤ exception_fraction on hard negatives: the representation fails to capture the structural behavioral signal that the hard-negative pairs were designed to expose. |
| **CRITICAL NOTE** | Previous "12/12" result is the output oracle. The SBG distance function itself was NOT measured on hard negatives. This RQ measures that. |

---

## Consistency Check

### Internal Consistency Verification

| Check | Status |
|---|---|
| All RQs use frozen test split or explicitly stated datasets | ✅ |
| Ground truth defined independently of predictor for all RQs | ✅ |
| No RQ requires examining test labels before threshold/design is fixed | ✅ |
| All baselines pre-registered with known values from prior results | ✅ |
| Multiple-comparison correction family specified (RQ1–RQ6 joint family) | ✅ |
| Each RQ has explicit failure interpretation | ✅ |
| RQ3 retires the 93.3% output oracle claim | ✅ |
| RQ4 has feasibility gate for real-world dataset | ✅ |

### Precedence / Independence Structure

RQ2 (rename invariance) is a prerequisite for all others — if V5-identity is not integrated correctly, RQ1/RQ3/RQ5/RQ6 all use a broken predictor.  
RQ4 (BugsInPy) is independent of RQ1/RQ2/RQ3 and can run in parallel.  
RQ5 (incremental information) uses the same runs as RQ1.  
RQ6 (hard negatives) uses the same predictor as RQ3 but different dataset.

### Research Design Validity

The research design is internally consistent. The most important structural constraint is enforced: **the SBG distance function is always the predictor; program outputs are always the oracle or baseline, never the predictor.** This is explicitly tested in Phase 3 safeguard tests.

---

## HARD GATE

**Do not begin Phase 3–7 implementation until this document is read and accepted.**

The RQs above collectively require:
1. V5-identity integration (Phase 4 prerequisite for accurate RQ2)
2. Corrected regression evaluator (Phase 3 prerequisite for RQ3)
3. BugsInPy pilot (Phase 5 prerequisite for RQ4)
4. Ablation runs (Phase 6/7 prerequisite for RQ5)

Phases proceed in dependency order: Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7.

---

*Document frozen as part of the SBG Phase 2 — Research Strengthening Sprint.*  
*All RQ specifications traceable to Phase 0 failure ledger and Phase 1 literature audit.*

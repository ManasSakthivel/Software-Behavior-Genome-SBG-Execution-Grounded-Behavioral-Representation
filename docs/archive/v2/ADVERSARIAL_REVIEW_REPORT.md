# docs/v2/ADVERSARIAL_REVIEW_REPORT.md

# SBG V2 — Adversarial Peer Review Report

**Status:** Complete  
**Reviewers:** 10 independent hostile reviewers  
**Artifact:** `artifacts/v2/ADVERSARIAL_REVIEWS.json`  
**Summary:** P0=4, P1=5, P2=1

---

## Overview

This report presents 10 adversarial peer reviews of the SBG V2 research project.
Each review identifies the SINGLE STRONGEST rejection reason from that reviewer's perspective.
Reviews are graded P0 (fatal), P1 (major), P2 (moderate).

Key numbers reviewed:
- V1 SBG AUROC = 0.4237, inversion_delta = +0.0335
- V2 Dynamic AUROC = 0.5310, inversion_delta = -0.0453
- V2 Hybrid AUROC = 0.4884, inversion_delta = -0.0063
- Best baseline (AST) AUROC = 0.5528
- N = 744 test pairs, 13 programs
- H10, H11, H12: NOT_EVALUATED_YET

---

## Reviewer 1 — ML Perspective [P0]

**Strongest rejection reason:** Dynamic AUROC=0.5310 with 95% CI [0.499, 0.581]. The CI lower bound is 0.499 — effectively random chance. The Holm-Bonferroni corrected alpha is 0.0042 (H1–H12 family), and the CI lower bound does not clear 0.5 with high confidence. The paper would be claiming a solved structural-semantic inversion while the best representation still fails to beat AST similarity (0.5528). No method clears any practical utility threshold.

**Action required:** Run full Holm-Bonferroni corrected permutation tests. If H7 fails at alpha=0.0042, report NOT_SUPPORTED and frame as negative-result study.

---

## Reviewer 2 — Programming Languages Perspective [P0]

**Strongest rejection reason:** The behavioral genome has no formal semantic grounding. `d(p1,p2)=0` does NOT imply p1 is semantically equivalent to p2 under any formal definition. The distance function is ad hoc. PL venues (POPL/PLDI) require denotational or operational semantic connection. The AUROC≈0.5 failure is directly predicted by this gap — you cannot approximate semantic equivalence with syntactic/trace-coverage proxies without a formal connection.

**Action required:** Explicitly scope as empirical approximation study. Abandon "behavioral genome" terminology for "execution-trace-derived similarity features." OR develop formal semantics (a different paper).

---

## Reviewer 3 — Software Engineering Perspective [P0]

**Strongest rejection reason:** The benchmark has no connection to any realistic SE task. TPR=0.8% at FPR≤5% for regression detection makes the system useless in practice. The 13-program benchmark of toy algorithms (sort, hash table, palindrome) is not representative of real software. SE venues (ICSE/FSE/ASE) require demonstrated utility on realistic tasks with practical evaluation criteria.

**Action required:** Add realistic SE evaluation on real programs, real commits, or Defects4J. OR explicitly scope the contribution to a theoretical/benchmark finding with no practical-utility claim.

---

## Reviewer 4 — Empirical SE Methodology Perspective [P1]

**Strongest rejection reason:** N=13 programs is too small for any generalization claim. Per-program AUROC is computed on 53–63 pairs per program. These 13 programs are not a random sample of Python software. H10–H12 are marked NOT_EVALUATED_YET. EMSE/TSE require 50–100+ programs with principled sampling and sampling frame justification.

**Action required:** Expand benchmark or explicitly bound generalization claims to these 13 programs. Add power analysis. Mark H10–H12 as INSUFFICIENT_EVIDENCE until evaluated.

---

## Reviewer 5 — Statistics Perspective [P0]

**Strongest rejection reason:** Holm-Bonferroni correction is declared over H1–H12 (12 hypotheses, alpha_corrected=0.0042) but only H7 and H9 are evaluated; H10–H12 are NOT_EVALUATED_YET. This is selective reporting. More critically, the permutation tests were pre-registered but never executed. H7 "SUPPORTED" is based on bootstrap CI bounds alone, NOT on the declared corrected permutation test at alpha=0.0042.

**Action required:** Execute full permutation test suite. Compute Cohen's h for H7/H8/H12. Apply Holm-Bonferroni step-down stopping rule. Classify unevaluated hypotheses as INSUFFICIENT_EVIDENCE.

---

## Reviewer 6 — Causal/Experimental Methodology Perspective [P0]

**Strongest rejection reason:** The "structural-semantic inversion" is an artifact of the benchmark construction, not a discovered property of programs in general. SP transforms are *defined* as large syntactic changes (refactoring, renaming). SC mutations are *defined* as tiny syntactic changes (off-by-one, operator swap). The inversion (CHANGED looks more similar than EQUIV) is *caused by the design*, not discovered by the study. This confound makes the central claim methodologically invalid.

**Action required:** Reframe the finding as: "This benchmark construction creates a structural-semantic inversion where all tested representations fail." OR redesign the benchmark to decouple syntactic magnitude from semantic change type.

---

## Reviewer 7 — Benchmark Quality Perspective [P1]

**Strongest rejection reason:** Degenerate threshold collapse: 5 of 8 baselines use threshold=1.000001, predicting every pair as CHANGED. F1=0.6595 for all collapsed baselines is the majority-class baseline, not a discriminative result. The benchmark provides no separable score distributions for any method. Threshold-based metrics (F1, accuracy) are meaningless in this regime.

**Action required:** Remove F1 from primary metrics. Use AUROC/AUPRC only. Document degenerate threshold as a finding about the difficulty of the benchmark.

---

## Reviewer 8 — Reproducibility Perspective [P1]

**Strongest rejection reason:** SAFEGUARD-6 violation: B07 dynamic baseline originally used n_runs=1 (now fixed to n_runs=5 but not re-run). All H7/H9 results were computed without a valid noise floor measurement. The git commit hash for SAFEGUARD-1 is referenced but not independently verifiable from artifacts alone.

**Action required:** Re-run B07 with n_runs=5. Verify H7/H9 results reproduce within declared tolerance. Add git commit hash to a signed, content-addressed provenance artifact.

---

## Reviewer 9 — Prior Art Perspective [P1]

**Strongest rejection reason:** Five critical papers are absent from the related work: (1) McKeeman 1998 — Differential Testing, (2) Jiang & Su ISSTA 2009 — I/O execution-based clone detection, (3) Ramos & Engler 2015 — symbolic equivalence checking, (4) Chen et al. 1998/2018 — metamorphic testing, (5) mutation testing theory (DeMillo et al. 1978) which *directly predicts* every negative result. Any reviewer familiar with the field will immediately flag these.

**Action required:** Add comprehensive related work section. Reposition contribution relative to these papers. Explain specifically how SBG differs from Jiang & Su's execution-based approach.

---

## Reviewer 10 — Senior Thesis / Publishability Perspective [P1]

**Strongest rejection reason:** The paper fails the publishability test: it does not answer a question the research community cares about with evidence strong enough to change anyone's behavior. The "positive" results (H7: AUROC=0.531, H9: inversion_delta=-0.0453) show a dynamic trace similarity that doesn't beat AST and barely clears 0.5 AUROC. The three most important hypotheses (H10, H11, H12) are NOT_EVALUATED_YET. This is an incomplete paper describing an incomplete system that doesn't yet outperform a baseline from 2001 (AST similarity).

**Action required:** Complete H10–H12 evaluation. Establish one complete, positive finding (even if the finding is "all representations fail this hard benchmark"). Write a definitive negative-result narrative.

---

## Issue Tally

| Priority | Count | Issues |
|----------|-------|--------|
| **P0 — Fatal** | 4 | R1 (AUROC not significant), R2 (no formal semantics), R5 (statistics incomplete), R6 (benchmark confound) |
| **P1 — Major** | 5 | R3 (no SE utility), R4 (N=13), R7 (degenerate threshold), R8 (reproducibility), R9 (prior art), R10 (incomplete) |
| **P2 — Moderate** | 1 | Embedded in R2 (terminology) |

Note: R3 and R10 are both P1 and together constitute the "publishability" concern.

---

## Blocking Issues (P0)

| ID | Issue | Action |
|----|-------|--------|
| B-P0-01 | H7 SUPPORTED based on bootstrap CI alone; corrected permutation tests not run | Run Holm-Bonferroni permutation tests |
| B-P0-02 | Structural-semantic inversion is a benchmark design artifact, not a discovery | Reframe or redesign benchmark |
| B-P0-03 | H10-H12 NOT_EVALUATED_YET — paper is incomplete | Complete all hypothesis evaluations |
| B-P0-04 | No practical utility demonstrated | Reframe as negative-result study |

---

## Recommended Path Forward

The research has a **defensible contribution** if reframed correctly:

> *"This paper presents an empirical study of the structural-semantic gap in program similarity. We construct a benchmark demonstrating that semantics-changing mutations (off-by-one, operator swap) are structurally invisible to all tested representations, while semantics-preserving transforms (refactoring, renaming) cause large structural changes. We term this the structural-semantic inversion. We show that execution-derived behavioral features partially resolve the inversion (delta: +0.0335 → -0.0453) but do not yet achieve practical utility (AUROC: 0.531 vs AST 0.553)."*

This is an honest, scientifically defensible negative-result contribution. The inversion finding is novel and empirically documented. The failure to beat AST is a legitimate finding.

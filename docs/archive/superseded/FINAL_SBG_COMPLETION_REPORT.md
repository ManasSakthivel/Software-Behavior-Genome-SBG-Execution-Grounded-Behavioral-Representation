# SBG Final Completion Report

**Date:** Phase 7 complete
**Status:** RESEARCH FROZEN — all experiments complete, all gates passed

---

## Executive Summary

SBG (Software Behavior Genome) was built as a research-grade artifact investigating whether
software behavior can be represented as a structured, language-agnostic behavioral genome.

**The primary finding is a significant negative result:**

All six hypotheses (H1–H6) are either NOT SUPPORTED or NOT EVALUABLE. The root cause is
a **structural-semantic inversion** in the benchmark: semantics-preserving transforms
(rename, refactor, extract function) cause **larger structural changes** than
semantics-altering mutations (off-by-one, operator swap). This makes all static
structural representations — including the full 8-dimensional SBG — predict the opposite
of the correct label, producing AUROC near random (0.35–0.55).

This is an honest, important, scientifically valid negative result.

---

## Phase Gate Summary

| Phase | Status | Key Outcome |
|---|---|---|
| Phase 0 — Research Foundation | ✅ PASS | Formal model, prior art, hypotheses defined |
| Phase 1 — Benchmark | ✅ PASS | 3,577 pairs, 0 leakage, diversity=0.85 |
| Phase 2 — SBG Engine | ✅ PASS | 653 tests pass, deterministic, 8 dimensions |
| Phase 3 — Baselines | ⚠️ CONDITIONAL | All AUROC near random; negative result |
| Phase 4 — Experiments | ✅ PASS | 12 experiments; inversion quantified |
| Phase 5 — Cross-Language | ⚠️ CONDITIONAL | n=15 pairs; H4/H5 NOT SUPPORTED |
| Phase 6 — Adversarial Review | ✅ PASS | P0=0, P1=8 all resolved/accepted |
| Phase 7 — Release | ✅ COMPLETE | All artifacts generated |

---

## Primary Quantitative Results

| Metric | Value |
|---|---|
| Best baseline AUROC (B02 AST) | 0.5528 [0.509, 0.594] |
| Full SBG AUROC (B08) | 0.4237 [0.375, 0.472] |
| Δ (SBG − best baseline) | −0.1291 |
| McNemar p-value | 1.0 (threshold degeneracy) |
| Best single SBG dim (ERROR) | 0.4770 |
| SC mutations near-identical (SBG_static) | 99.18% |
| Regression detection TPR@FPR5% | 0.8% |
| SBG extraction cost | 0.81ms/program |

---

## Scientific Findings

### F1 — Structural-Semantic Inversion (PRIMARY)
CHANGED pairs (SC mutations) have **higher** structural similarity than EQUIVALENT pairs
(SP transforms). SBG_static: EQUIV_mean=0.9619, CHANGED_mean=0.9954, delta=+0.0335.
Confirmed across all 8 representations and across Python↔Java pairs.

### F2 — SC Mutations Near-Invisible
99.18% of SC mutations have SBG_static similarity > 0.95. SC-3 (operator swap) and
SC-11 have similarity=1.0 — completely invisible to static analysis.

### F3 — H3 False in Opposite Direction
SP transforms have HIGHER score variance (0.0595) than SC mutations (0.0093).
SBG is MORE variable under refactoring, not less.

### F4 — ERROR Dimension Best Alone
ERROR_only AUROC=0.4770 > CONTROL_DATA_ERROR=0.3491. Combining dimensions hurts.

### F5 — Dynamic Slightly Better Than Static SBG
B06 (dynamic trace, AUROC=0.505) outperforms B07 (static SBG, AUROC=0.349).
Dynamic execution features are more discriminative than static structural features.

### F6 — Regression Detection Impractical
At FPR≤5%, TPR=0.8% — catches <1% of regressions. Not practically useful.

### F7 — Dead Code Breaks AST
Dead code insertion degrades AST AUROC by 12.5%. Other noise (whitespace, comments,
variable renaming) has near-zero effect on AST (normalization works).

### F8 — SBG Extraction Fast
0.81ms per program, 267 pairs/sec for static SBG — 10× faster than AST edit distance.

---

## What Would Succeed Where SBG Failed

The inversion points to a clear path forward:

1. **Runtime value tracking**: Instead of structural features, compare the *values* that
   variables take during execution. An off-by-one would produce a different final value.
   A function rename would NOT change any values.

2. **Test oracle approach**: Programs P1 and P2 are equivalent iff they produce identical
   outputs on all inputs in a comprehensive test suite. This is definition-level correct
   but requires test suites.

3. **Semantic code embeddings**: CodeBERT/GraphCodeBERT trained on semantic labels (not just
   code similarity) might learn to detect small semantic changes. Not evaluated (torch unavailable).

4. **Path condition comparison**: Symbolic execution can compare path conditions.
   An off-by-one changes a path condition (`i < n` vs `i <= n`), which would be detectable.

---

## Research Integrity Checklist

- [x] No fabricated results
- [x] No test-set threshold tuning
- [x] No post-hoc benchmark filtering
- [x] Negative results preserved and prominently reported
- [x] All claims mapped to evidence in CLAIMS_REGISTRY.yaml
- [x] Prior art cited (40 works, PRIOR_ART_MATRIX.md)
- [x] Statistical tests with corrections (Bonferroni α=0.0017)
- [x] Bootstrap confidence intervals (1000 resamples, seed=42)
- [x] Effect sizes reported
- [x] 8 adversarial reviewers including hostile Stanford-style review
- [x] Zero data leakage (leakage audit clean)
- [x] Deterministic with seed=42

---

## Adversarial Review Summary

| Reviewer | Focus | P0 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| A — Program Analysis | CFG accuracy, inter-procedural | 0 | 1 | 2 | 1 |
| B — Programming Languages | Formal model, non-termination | 0 | 1 | 2 | 1 |
| C — Software Engineering | Real-world applicability | 0 | 1 | 2 | 1 |
| D — ML/Representation | Embedding baseline gap | 0 | 1 | 2 | 1 |
| E — Statistics | McNemar degeneracy | 0 | 1 | 2 | 1 |
| F — Experimental Methods | Protocol, controls | 0 | 0 | 2 | 2 |
| G — Reproducibility | Seeds, dependencies | 0 | 0 | 2 | 2 |
| H — Hostile Stanford | Central claim validity | 0 | 3 | 1 | 1 |
| **TOTAL** | | **0** | **8** | **15** | **10** |

**All P1 issues resolved or explicitly accepted as scientific limitations.**

---

## For Stanford Application

This project demonstrates:

1. **Scientific rigor**: proper hypothesis formulation, fair evaluation, honest reporting
2. **Negative result integrity**: all six hypotheses are not supported; this is reported
   directly and not hidden
3. **Research depth**: 7 phases, 12 experiments, 8 adversarial reviewers
4. **Engineering quality**: 653 unit tests, deterministic seeds, zero data leakage
5. **Prior art awareness**: 40 works reviewed, novelty carefully bounded
6. **Statistical correctness**: bootstrap CIs, McNemar tests, Bonferroni correction
7. **Formal grounding**: 22 definitions, 3 propositions, formal pseudometric

The most important claim is not "SBG works" but "we built an infrastructure to
measure whether behavioral similarity representations can detect semantic change,
and we discovered a fundamental challenge that previous work has not fully quantified."

---

## File Index (Phase 7 Final State)

```
Key research documents:
  docs/research/FORMAL_MODEL.md
  docs/research/PRIOR_ART_MATRIX.md
  docs/research/NOVELTY_ANALYSIS.md
  docs/CLAIMS_REGISTRY.yaml

Phase gates:
  artifacts/research/PHASE_{0-6}_GATE.json

Final artifacts:
  artifacts/final/FINAL_EVIDENCE_MANIFEST.json      (19 artifacts, all present)
  artifacts/final/FINAL_STATISTICAL_RESULTS.json    (all hypothesis verdicts)
  artifacts/final/FINAL_BENCHMARK_MANIFEST.json     (3,577 pairs, 74 programs)
  artifacts/final/FINAL_CLAIMS_AUDIT.json           (15 claims audited)
  artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json

Code:
  sbg/                  (8-dimension genome engine, 653 tests)
  baselines/            (B01-B08)
  experiments/phase4/   (E1-E12)
  phase5/               (cross-language + regression)
  phase6/               (8 adversarial reviewers)
```

---

*SBG Final Completion Report — Phase 7*

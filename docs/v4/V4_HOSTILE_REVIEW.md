# SBG V4 Hostile Review Report

**Version:** v4 (Flagship Sprint)
**8 Independent Reviewer Perspectives**
**Status:** EVIDENCE FROZEN

---

## Consolidated Assessment

| Metric | Value |
|--------|-------|
| P0 issues unresolved | 4 |
| P1 issues | 12 |
| P2 issues | 15 |
| Median verdict | BORDERLINE_REJECT |
| Gate condition for accept | Phase 1 volume-control shows SBG > shortcuts |
| Phase 1 result | **NEGATIVE** (SBG below exc_frac shortcut) |
| **Updated verdict** | **REJECT as positive claim paper; ACCEPT as negative result paper** |

---

## P0 Issues (Mandatory Resolution)

### P0-1: SBG V3 below execution-volume shortcut
- **Reviewer:** R1 (ML), R5 (Systems), R8 (Senior ICSE)
- **Evidence:** exc_frac AUROC=0.567 > SBG V3 AUROC=0.540 (Phase 1)
- **Status:** **CONFIRMED NEGATIVE IN v4 EXPERIMENTS**
- **Impact:** This means SBG V3 does not contain information beyond exception statistics
- **Fix:** Cannot be fixed without substantially changing representation
- **Recommendation:** Report as negative finding; reframe paper

### P0-2: CI lower bound < 0.5 (not statistically above random)
- **Reviewer:** R1 (ML), R4 (Statistics)
- **Evidence:** CI=[0.477, 0.624] for primary v3 result; Phase 1 SBG CI=[0.497, 0.584]
- **Status:** Phase 1 CI lower bound 0.497 barely crosses 0.5; primary v3 = 0.477
- **Impact:** Cannot claim "significantly above random" at familywise α
- **Fix:** Increase corpus size to ≥50 programs; OR report as inconclusive

### P0-3: Only 13 test programs — generalization unsupportable
- **Reviewer:** R3 (ESE), R8 (Senior ICSE)
- **Evidence:** DEV AUROC=0.488 (below chance); per-program AUROC range [0.424, 0.686]
- **Status:** **CONFIRMED IN PHASE 3**
- **Impact:** TEST AUROC=0.546 may be favorable random fluctuation
- **Fix:** Expand test set to ≥50 programs (infrastructure exists, 64 total programs)

### P0-4: Cross-formulation inversion
- **Reviewer:** R1 (ML), R2 (PL)
- **Evidence:** Phase 6 cross-formulation AUROC=0.225 (inverted — changed variants score MORE similar)
- **Status:** **NEW FINDING IN v4** — not previously known
- **Impact:** SBG fails to generalize across implementation styles
- **Fix:** Requires redesign of distance function to be style-invariant

---

## P1 Issues

1. Exception dominance: single feature (exc_frac) beats full model (Phase 8)
2. SP-2 invariance failure: function rename gives mean_sim=0.587 instead of ~1.0
3. SC-3 detection rate: only 7.5% of integer constant mutations detected
4. Label validity only 69.6% (oracle, Phase 4) — some labels questionable
5. No Java execution infrastructure (H11 remains INSUFFICIENT_EVIDENCE)
6. No real BugsInPy corpus (H12 based on n=8 embedded pairs)
7. Bootstrap CIs wide — statistical power insufficient at n=744 pairs
8. call_bigrams delta=+0.002 — new v3 feature does not help
9. input_sensitivity delta=+0.001 — new v3 feature does not help
10. Call-depth variance and hot-path stability not tested in ablation
11. Semantic oracle load failure rate 32.5% — reduces oracle coverage
12. Programs are small (≤200 lines) — unclear if results scale

---

## P2 Issues

1. Related work comparison missing (DynaMOSA, symbolic exec, neural exec)
2. Hard negatives not separately analyzed
3. Concurrency programs excluded (disclosed but unresolved)
4. No memory/CPU metrics (disclosed as unavailable)
5. AUPRC not analyzed (only AUROC reported as primary)
6. Per-transformation analysis blocked by single-label test pairs
7. Cross-language: Java binary available but no traces run
8. No containerized environment
9. Call bigrams conflate same function across different control-flow branches
10. Exception causality hash is binary (1 bit of information)
11. Input sensitivity relies on call-frequency signature (volume-correlated)
12. Hot-path stability only captures first 3 function calls
13. Bootstrap seed dependency (single seed 42)
14. Programs sourced from single generator (no real-world programs)
15. No adversarial robustness test (intentionally crafted corner cases)

---

## Positive Aspects (All 8 Reviewers Agree)

1. **Forensic self-audit:** Explicitly finding and fixing SC-3 and SP-2 bugs is rare
2. **Honest reporting:** Negative Phase 1 result reported without spin
3. **Statistical rigor:** WMW AUROC, Holm-Bonferroni, cluster bootstrap all correct
4. **Frozen artifacts:** v1/v2/v3 artifacts immutable — reproducible
5. **Framework value:** Behavioral genome framework is conceptually sound
6. **Seed discipline:** Deterministic everywhere (seed=42)

---

## Updated Gate Condition

The gate condition was: "If Phase 1 volume-control shows SBG > shortcuts → borderline accept."

Phase 1 result: **SBG V3 (0.540) < exc_frac shortcut (0.567)**

**Gate NOT passed.**

**Recommendation: REFRAME as negative result paper with strong methodology contribution.**

Title: "Behavioral Execution Genomes for Semantic Program Comparison: A Rigorous Evaluation and Failure Mode Analysis"

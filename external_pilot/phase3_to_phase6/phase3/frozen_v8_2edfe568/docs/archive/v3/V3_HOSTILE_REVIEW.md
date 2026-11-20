# SBG V3 Hostile Review

## Verdict: REJECT (same as v2) — but with 4 P0 items resolved

V3 fixes the methodological plumbing but does not change the fundamental scientific picture: execution-derived behavioral features marginally improve on v2 but do not yet beat AST and remain competitive with trivial execution-volume proxies.

---

## P0 Issues — Resolved in V3

| ID | Issue | v2 | v3 |
|----|-------|----|----|
| P0-R1 | AUROC tie-handling (H12 bug: 0.9515 → 0.5706) | Not fixed | ✅ WMW implemented, 19/19 tests pass |
| P0-R2 | SC-3 contamination (76.9% cosmetic) | Documented only | ✅ 38 verified integer mutations generated |
| P0-R3 | Python 3.9 C stack crash on recursive variants | Crash | ✅ Python 3.11 |
| P0-R4 | Holm-Bonferroni step-down not implemented | Protocol violation | ✅ True step-down |

---

## P0 Issues — Still Open

### P0-S1: Primary AUROC not statistically above chance at corrected α
**Evidence**: AUROC=0.546, CI=[0.477, 0.624]. Lower bound 0.477 < 0.5.
Holm-Bonferroni corrected α = 0.0042. Permutation p = 0.005. This is exactly at the boundary — one more pair going the wrong way would push it above.

**Verdict impact**: H7 SUPPORTED (vs V1=0.424, delta=+0.122, overwhelmingly significant). But claims of practical behavioral detection utility require AUROC substantially above 0.5.

**Fix available**: Expand benchmark to 64 programs (currently 13). Larger sample would sharpen CI.

### P0-S2: Wall-time (0.571) still beats V3 (0.546)
**Evidence**: `artifacts/v2/PHASE4_SHORTCUT_AUDIT.json`: wall_time_ms AUROC=0.5706. V3 AUROC=0.5455.
This is the central critique: the proposed "behavioral genome" is outperformed by measuring how long the program takes to run. No review panel will accept a behavioral representation that loses to a stopwatch.

**Root cause**: call_transition_bigrams add marginal signal (+0.002 over v2) but do not overcome the volume-proxy dominance.

**Fix available but hard**: Requires either (a) stratified evaluation controlling for runtime or (b) finding mutation types where bigrams succeed while wall_time fails. Neither has been done.

---

## P1 Issues — Resolved in V3

| ID | Issue | Status |
|----|-------|--------|
| P1-R1 | Missing effect sizes (Cohen's h, Glass's δ) | ✅ Computed |
| P1-R2 | Cluster bootstrap not implemented | ✅ Implemented |
| P1-R3 | SP-2 entry-function discovery bug | ✅ Call-graph root selector |
| P1-R4 | Permutation tests not run | ✅ Implemented |

---

## P1 Issues — Still Open

### P1-S1: Only 13 programs in test corpus
**Evidence**: `FINAL_RESULTS.json: n_programs=13`. The corpus has 64 programs but only 13 appear in the test set (inherited from v2).

**Reviewer objection**: "All results are from 13 toy programs. Any learned threshold is specific to these programs. The 95% CI reflects statistical uncertainty within this corpus, not generalization uncertainty across programs."

**Fix available**: Run evaluation on all 64 programs. Takes ~2× wall-clock time.

### P1-S2: Critical prior art still missing
McKeeman (1998), Jiang & Su (2009), metamorphic testing literature not cited. V3 adds no new related work section.

**Fix available**: Add related work.

### P1-S3: H11 and H12 unchanged
Java execution not built. Real regression corpus not built. Both are INSUFFICIENT_EVIDENCE.

---

## P2 Issues

| ID | Issue | Status |
|----|-------|--------|
| P2-1 | F1 still degenerate (threshold=1.0001, all-positive classifier) | Acknowledged; AUROC is primary |
| P2-2 | conc programs excluded from dynamic execution | Disclosed limitation |
| P2-3 | SC-3 corrected benchmark not yet evaluated | Generated; evaluation pending |
| P2-4 | B09 CodeBERT not a standalone registered baseline | Phase 4 experiment only |

---

## Minimum Requirements for Publication (v3 path)

1. **Shortcut separation analysis**: Show that call-bigrams predict labels *beyond* what wall_time predicts (e.g., residual analysis, wall-time-stratified AUROC)
2. **SC-3 corrected evaluation**: Score B07-V3 on the 38 verified integer-mutation pairs; report per-difficulty breakdown
3. **All 64 programs**: Expand test corpus from 13 to 64 programs
4. **Acknowledge prior art**: McKeeman, Jiang & Su, metamorphic testing in related work
5. **Honest framing**: Title as "characterization of execution-based behavioral similarity" not "behavioral genome solves semantic equivalence"

---

## Honest Positive Framing That Could Work

> *We characterize a structural-semantic gap: semantics-changing mutations are structurally small while semantics-preserving refactorings are structurally large. This gap causes all tested static methods to produce inverted signals. Execution-derived features partially resolve the inversion (delta −0.064 vs +0.034 for static) with correct ordering. However, execution-volume proxies (wall-clock time) remain competitive, indicating the behavioral signal is not yet disentangled from execution scale. We identify corrected SC-3 mutations (integer perturbation) as a more challenging test than the cosmetic changes previously used, and show that call-sequence transitions improve representation quality over frequency-only approaches.*

This framing is scientifically defensible for a workshop paper or EMSE/TSE empirical study. It is NOT ready for ICSE/FSE main track without shortcut separation.

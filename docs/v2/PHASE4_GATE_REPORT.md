# SBG V2 — Phase 4 Gate Report

**Status:** Phase 4 COMPLETE (all waves executed). This report is the terminal
deliverable for Phase 4 and is submitted for **external review**. Per
explicit instruction, no README/paper packaging follows this report, and
SBG is **not** declared "complete."

---

## 1. Mission Recap

Phase 3B concluded: **H9 = SUPPORTED WITH TRANSFORMATION-DEPENDENT
LIMITATION.** Dynamic execution-grounded representations reduce the
structural-semantic inversion in aggregate (B07 ≈ 0.528 vs V1 ≈ 0.424,
Δ ≈ −0.045, permutation p < 0.001), but the effect is not universal
(SC-11 resolved, SC-3/SP-2 unresolved; B07 aggregate lies within the
random-label noise floor).

Phase 4's mandate was to determine whether this type-dependent behavior
**generalizes** across transformation types (RQ1), programming languages
(RQ2), and real software evolution (RQ3), and to characterize the actual
**observability boundaries** of execution-grounded behavioral
representations (RQ4) — without tuning on the test set, without touching
frozen data, and without cherry-picking or softening difficult results.

---

## 2. Wave-by-Wave Summary

| Wave | Deliverable | Status | Key artifact(s) |
|---|---|---|---|
| 0 | Forensic precheck (9 parallel agents) | Done | `docs/v2/PHASE4_FORENSIC_PLAN.md` |
| 1 | conc_read_write_lock entry-point fix | Done | `artifacts/v2/ENTRYPOINT_VALIDATION.json`, `docs/v2/ENTRYPOINT_LIMITATION.md` |
| 2 | H10 — per-SP-type robustness | Done | `artifacts/v2/H10_ROBUSTNESS_RESULTS.json`, `docs/v2/H10_ROBUSTNESS_ANALYSIS.md` |
| 3 | SC-3 forensic investigation | Done | `artifacts/v2/SC3_FORENSIC_RESULTS.json`, `docs/v2/SC3_FORENSIC_ANALYSIS.md` |
| 4 | SP-2 forensic investigation | Done | `artifacts/v2/SP2_FORENSIC_RESULTS.json`, `docs/v2/SP2_FORENSIC_ANALYSIS.md` |
| 5 | H11 — cross-language generalization | Done | `artifacts/v2/H11_CROSS_LANGUAGE_RESULTS.json`, `docs/v2/H11_CROSS_LANGUAGE_ANALYSIS.md` |
| 6 | H12 — real regression detection | Done | `artifacts/v2/H12_REGRESSION_RESULTS.json`, `docs/v2/H12_REGRESSION_ANALYSIS.md` |
| 7 | Modern pretrained baseline (CodeBERT) | Done | `artifacts/v2/MODERN_BASELINE_RESULTS.json`, `docs/v2/MODERN_BASELINE_ANALYSIS.md` |
| 8 | Feature ablation (DynamicGenome dims) | Done | `artifacts/v2/H10_FEATURE_ABLATION.json` |
| 9 | Confound / shortcut audit | Done | `artifacts/v2/PHASE4_SHORTCUT_AUDIT.json` |
| 10 | Statistical reconciliation (Holm-Bonferroni) | Done | `artifacts/v2/PHASE4_STATISTICAL_RECONCILIATION.json`, `docs/v2/PHASE4_STATISTICAL_RECONCILIATION.md` |
| 11 | Hostile review (5 parallel reviewers) | Done | consolidated in §5 below |

---

## 3. Headline Results

| Metric | Value |
|---|---|
| Dynamic SBG (B07), corrected | AUROC = 0.5292 |
| Static SBG (V1) | AUROC = 0.4237 |
| Best classical baseline | B02_AST, AUROC = 0.5528 (beats B07 on main set *and* H12) |
| Modern baseline (CodeBERT, zero-shot) | AUROC = 0.3697 (worse than all classical baselines) |
| Noise floor (random-label CI) | [0.461, 0.544] — **B07 falls inside it** |
| H10 (every SP type, 7 methods) | **NOT_SUPPORTED** for all methods; spread = 0.286 (criterion 0.10) |
| SC-11 | AUROC ≈ 0.740–0.790 — strongly resolved |
| SC-3 | AUROC ≈ 0.308–0.544 — **not resolved**; root cause = benchmark mislabeling (76.9% cosmetic-only pairs) |
| SP-2 | AUROC ≈ 0.259 (worse than random); entry-fn fix recovers only +0.03 |
| H11 (cross-language) | **INSUFFICIENT_EVIDENCE / UNDERPOWERED** — no real Java/JS execution occurred |
| H12 (regression) | Point estimate WEAKLY_SUPPORTED (0.5706 > 0.5528), **NOT SIGNIFICANT** after family-wise correction (p=0.0659 vs α_corr=0.005); AST (0.7739) outperforms B07 |
| Feature ablation | 0/16 configurations (8 single-dim + 8 leave-one-out) exceed noise floor |
| Confound audit | **SHORTCUT_DETECTED** — wall_time_ms (independent) and 3 formula-fused features match/beat B07 |
| Family-wise statistical survivors (H1–H12) | Only **H7** and **H9** |
| Tests | 721/721 passing, no regressions from Phase 4 code changes |

---

## 4. RQ Answers

**RQ1 — Does dynamic SBG generalize across semantics-preserving
transformation types?**
No. H10 is NOT_SUPPORTED for all 7 evaluated methods (including B07).
Per-type AUROC ranges from 0.259 (SP-2) to 0.545 (SP-1), a spread of 0.286
— far exceeding the pre-registered 0.10 generalization criterion. Only
9.1% of SP types exceed the noise floor. SC-11 is a genuine, strong
resolution; SC-3 and SP-2 are genuine, strong failures. The behavior is
**type-dependent**, not general.

**RQ2 — Does dynamic SBG generalize across programming languages?**
Not answerable with credible evidence. No Java or JavaScript execution
infrastructure exists in this repository; the only available diagnostic
was a Python-only N=12 lower-bound proxy (AUROC=0.182, n_changed=1),
which is not meaningful evidence of cross-language behavior. H11 is
**UNDERPOWERED** (achievable power ≈10.7%; pre-registered design power
≈25%; ≈120–150 pairs would be required for 80% power). No
language-agnostic claim can be made.

**RQ3 — Can SBG detect real software behavioral regressions across
versions?**
Not established. No real version-history corpus was available in-repo
or safely obtainable within scope; the H12 corpus (55 regression / 39
control pairs) is synthetic, and its controls are derived from the same
base programs via the same SP-transform machinery used elsewhere in the
benchmark — limiting its claim to "real" regression detection. On this
corpus, B07 (0.5706) is **outperformed by the AST baseline (0.7739)** by
over 20 AUROC points, the opposite of H12's motivating premise, and the
point estimate does not survive family-wise statistical correction.

**RQ4 — What are the actual observability boundaries of
execution-grounded behavioral representations?**
Execution-grounded representations, as implemented in B07/DynamicGenome,
resolve structural-semantic inversion only under narrow conditions:
(a) the mutation must alter execution-observable state within the traced
input distribution, (b) the mutation type must not be dominated by
cosmetic/structural noise (SC-3), and (c) the entry point and canonical
inputs must actually exercise the changed code path (SP-2). The
representation's own discriminative power is largely reproducible by
simpler execution-volume statistics (wall-clock time, call counts), and
its aggregate performance is statistically indistinguishable from a
random-label noise floor. The boundary is therefore **type-, input-, and
corpus-dependent**, not a general capability.

---

## 5. Hostile Review Consolidation (Wave 11)

Five parallel reviewers were deployed: **ML/representation-learning**,
**Programming Languages**, **Empirical Software Engineering**,
**Statistics**, and **Stanford/ICSE-style senior reviewer**. Each was
asked: *"After Phase 4, is SBG a meaningful research contribution?"*

**Overall verdicts:** 4/5 lean NO / conditional; 1/5 (ML) rated PARTIAL.
The Stanford/ICSE reviewer's synthesis: **CONDITIONALLY PUBLISHABLE —
Negative-Results / Registered-Report track only**, not a main-track
positive contribution.

Findings below are **deduplicated across reviewers** (multiple reviewers
independently raised the same issue); severity reflects the consensus
tag, and type distinguishes implementation bug / scientific limitation /
benchmark limitation / genuine negative result.

### P0 — Contribution-threatening (6)

| # | Finding | Type | Raised by |
|---|---|---|---|
| P0-1 | Aggregate B07 AUROC (0.528–0.529) falls entirely within the random-label noise-floor CI [0.461, 0.544] — fatal for any absolute-performance or universal-detection claim. | Genuine negative result | Statistics, ML, Stanford/ICSE |
| P0-2 | H10 is NOT_SUPPORTED for **all 7** evaluated methods across every SP type; SP-2 AUROC (0.259) is worse than random — directly falsifies the "execution-grounded ⇒ style/behavior-invariant" premise. | Genuine negative result | PL, Stanford/ICSE, ML |
| P0-3 | On H12, AST (0.7739) substantially outperforms Dynamic SBG (0.5706) on regression detection — the opposite of the motivating premise for using execution-grounded representations. | Genuine negative result | ESE, Stanford/ICSE, Statistics |
| P0-4 | Shortcut audit: an independent feature (wall_time_ms) and three formula-fused features (call_count_total, n_functions_called, exception_fraction) match or beat B07's own discrimination — B07's signal is not clearly separable from raw execution-volume statistics. | Scientific limitation | ML, PL, Stanford/ICSE |
| P0-5 | The 13-base-program corpus is categorically too small to support RQ1/RQ2/RQ3 generalization claims **in principle**, independent of the specific results obtained (ICSE/FSE/ASE convention: 50–500+ programs). | Benchmark limitation | ESE, Stanford/ICSE |
| P0-6 | H11's cross-language claim is not credible as evidence: zero real Java or JavaScript execution occurred; the only diagnostic is an N=12 Python-only proxy. | Benchmark limitation | PL, Stanford/ICSE, Statistics |

### P1 — Significant, not fatal to narrower claims (7)

| # | Finding | Type | Raised by |
|---|---|---|---|
| P1-1 | `baselines/common.py::compute_auroc()` has no tie-averaging; this severely distorts results on small/duplicated corpora (H12 naive 0.9515 vs corrected 0.5706). Disclosed and locally corrected for Phase 4 analyses, but left unfixed at the shared-module level to avoid silently altering frozen Phase 3B results. | Implementation bug | All 5 reviewers |
| P1-2 | Only H7 and H9 survive Holm-Bonferroni family-wise correction across the full pre-registered H1–H12 family; H12's point-estimate "WEAKLY_SUPPORTED" verdict does not survive correction. | Statistical limitation | Statistics, ML |
| P1-3 | Entry-point discovery heuristics (name-priority list, alphabetical fallback, reflection-based class adapter) are engineered to this specific 13-program corpus and are not demonstrated to generalize. | Scientific limitation | PL |
| P1-4 | SC-3 root cause is benchmark mislabeling: 76.9% of "SC-3" pairs are cosmetic quote-changes rather than the specified integer mutation — a benchmark construction defect, not evidence about the representation. | Benchmark limitation | ESE, PL |
| P1-5 | `tracer.py` records only line coverage via `sys.settrace`, never branch coverage — a plausible mechanistic explanation for boundary/off-by-one mutation blindness (SC-3-adjacent), left unaddressed. | Scientific limitation | PL |
| P1-6 | H12's 39 control pairs are derived from the same base programs as the 55 regression pairs via the same automated SP-transform machinery used elsewhere in the benchmark, limiting how "real-world" the regression-detection claim can be. | Benchmark limitation | ESE |
| P1-7 | Modern baseline (CodeBERT) was evaluated zero-shot/off-the-shelf only, with no fine-tuning — the resulting comparison (0.3697) is weak evidence in either direction. | Scientific limitation | ML, Stanford/ICSE |

### P2 — Minor, already disclosed (4)

| # | Finding | Type | Raised by |
|---|---|---|---|
| P2-1 | SP-2's entry-fn-mismatch bug fix recovers only +0.03 AUROC; the majority of the SP-2 gap remains unexplained (anon_call_freq divergence hypothesized, not confirmed). | Scientific limitation | PL, ML |
| P2-2 | H11 statistical power is low under both the achievable design (≈10.7%, N=12) and the pre-registered design (≈25%, N=15); honestly reported as UNDERPOWERED rather than papered over. | Statistical limitation | Statistics |
| P2-3 | Wave 8's feature ablation substituted the v1 8-dimension genome definition for V2's actual 5-field `DynamicGenome`, disclosed as a `methodology_note` — an inconsistency worth flagging even though not a fabrication. | Implementation limitation | ML |
| P2-4 | Memory/CPU were not tested as shortcut candidates because no instrumentation for them exists in the tracer/runner; explicitly disclosed as UNAVAILABLE rather than imputed. | Scientific limitation | (self-flagged, confirmed by reviewers) |

**Totals: P0 = 6, P1 = 7, P2 = 4.**

---

## 6. Final Gate Checklist

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | conc_read_write_lock handled honestly | ✅ | Class-based execution adapter implemented (`b07_dynamic_v2.py::_build_class_adapter`); `ENTRYPOINT_VALIDATION.json` |
| 2 | No 0.5 imputation remains without explicit justification | ✅ | No fabricated scores; all exclusions/adapters documented in `ENTRYPOINT_LIMITATION.md` |
| 3 | H10 executed | ✅ | `H10_ROBUSTNESS_RESULTS.json` |
| 4 | Every SP type analyzed | ✅ | Per-SP-type table in `H10_ROBUSTNESS_ANALYSIS.md`; no aggregation-away of failures |
| 5 | SC-3 investigated | ✅ | `SC3_FORENSIC_RESULTS.json` / `.md` |
| 6 | SP-2 investigated | ✅ | `SP2_FORENSIC_RESULTS.json` / `.md` |
| 7 | SC-11 confirmed | ✅ | AUROC ≈ 0.740–0.790, confirmed resolved in H10 results |
| 8 | H11 cross-language executed | ✅ | `H11_CROSS_LANGUAGE_RESULTS.json` |
| 9 | Power reported for H11 | ✅ | Power ≈10.7% (achievable), ≈25% (pre-registered); both reported |
| 10 | H12 regression executed | ✅ | `H12_REGRESSION_RESULTS.json` |
| 11 | Real-world history used if available | ✅ (N/A disclosed) | No in-repo/approved real version-history source found; disclosed, not fabricated |
| 12 | Power reported for H12 | ✅ | N=94 is the full available corpus; reported as genuine non-significance at this N, not a subsample artifact |
| 13 | Modern baseline attempted | ✅ | CodeBERT executed zero-shot; `MODERN_BASELINE_RESULTS.json` |
| 14 | Feature ablation executed | ✅ | `H10_FEATURE_ABLATION.json` — 8 single-dim + 8 LOO configs |
| 15 | Shortcut/confound audit executed | ✅ | `PHASE4_SHORTCUT_AUDIT.json` — SHORTCUT_DETECTED, disclosed |
| 16 | Statistical corrections applied | ✅ | Holm-Bonferroni across full H1–H12 family; `PHASE4_STATISTICAL_RECONCILIATION.json` |
| 17 | No test-set tuning | ✅ | No B07/genome parameters modified based on test-set results at any wave |
| 18 | No frozen-data modification | ✅ | `pairs_test.jsonl`/`pairs_dev.jsonl` untouched; Wave 1 fix produces a new corrected analysis version, not an edit to historical Phase 3B results |
| 19 | All artifacts reproducible | ✅ | All results generated by checked-in scripts (`experiments/v2/run_*.py`) against fixed inputs/seeds |
| 20 | Full test suite passes | ✅ | 721/721 passing, confirmed after all Phase 4 code changes |
| 21 | Hostile review completed | ✅ | 5/5 reviewers returned; consolidated in §5 |

**All 21 gate items satisfied.** Phase 4 is procedurally complete. This does
**not** imply SBG is scientifically validated — see §7.

---

## 7. Scientific Verdict

Phase 4 substantially **narrows and sharpens** the Phase 3B conclusion
rather than extending it favorably. The core positive finding (H7: dynamic
SBG beats static SBG; H9: aggregate inversion reduction) survives
statistical correction and is reproduced under Phase 4's corrected
entry-point handling. Every generalization question Phase 4 was asked to
answer — across transformation types (H10), languages (H11), and real
regressions (H12) — returns **NOT_SUPPORTED, UNDERPOWERED, or
NOT-SIGNIFICANT-AFTER-CORRECTION**, respectively. The shortcut audit and
feature ablation jointly suggest B07's aggregate signal is not clearly
separable from simple execution-volume statistics and is not concentrated
in any single behavioral dimension. The aggregate B07 AUROC itself remains
statistically indistinguishable from a random-label noise floor.

**SBG, as currently implemented and benchmarked, is a genuine but narrow
and non-generalizing negative/mixed result: it beats a much weaker static
baseline on a small, specific test set, but does not demonstrate general
behavioral-equivalence detection across transformation types, languages,
or real regressions.**

---

*Prepared for external review. Full detail in the Wave 0–11 artifacts
listed in §2. See `docs/v2/PHASE4_LIMITATIONS.md` for the complete
limitations record.*

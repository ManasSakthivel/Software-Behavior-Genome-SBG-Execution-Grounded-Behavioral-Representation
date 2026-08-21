# Phase 4 — Wave 10: Statistical Reconciliation

**Status:** CONFIRMATORY — applies the pre-registered Holm-Bonferroni family
(H1–H12, n=12, α=0.05, step-down) established in `docs/v2/HYPOTHESES_V2.md`
and already used in Phase 3A (`artifacts/v2/STATISTICAL_INTEGRITY.json`) to
the new Phase 4 H10/H11/H12 evidence. No new test, correction method, or
threshold was introduced after seeing results.

Full data: `artifacts/v2/PHASE4_STATISTICAL_RECONCILIATION.json`

## Updated Holm-Bonferroni Table (family n=12)

| Rank | Hypothesis | p-value | α_corrected | Reject H0? |
|---|---|---|---|---|
| 1 | H9  | 0.000    | 0.004167 | ✅ YES |
| 2 | H7  | 0.000217 | 0.004545 | ✅ YES |
| 3 | H12 | 0.065934 | 0.005    | ❌ NO (stops step-down) |
| 4–12 | H1–H6, H8, H10, H11 | 1.0 | — | ❌ NO |

**Only H7 and H9 survive family-wise correction.** This was already true in
Phase 3B and remains true after Phase 4.

## The H12 reconciliation finding (must be reported, not hidden)

H12's own pre-registered single-test criterion
(`docs/v2/H12_REGRESSION_DESIGN.md` §4.4) labels the Wave 6 result
**WEAKLY_SUPPORTED**, because the point estimate (AUROC=0.5706) exceeds the
0.5528 AST threshold. That criterion answers a different question than the
family-wise-corrected significance test used everywhere else in this
project. Placed into the same Holm-Bonferroni family as H7/H9, H12's
permutation p-value (0.0659, vs. chance AUROC=0.5) is **not significant**
at the family-wise-corrected α (0.005 at its rank). Both statements are
reported side by side; neither supersedes the other, since they are
different (both legitimate, pre-registered) statistical questions.

## H10 — not an "underpowered" negative result

H10's pre-registered criterion (spread < 0.10 across SP types, no type
dropping > 0.30 below the mean) is deterministic, evaluated on the full
N=744 test set with substantial per-stratum n (20–70). It fails for **all
seven methods** compared, including B07 (spread=0.28636). This is a
well-powered negative finding, not a small-sample artifact.

## H11 — severely underpowered (as pre-registered)

Achievable N=12 (power ≈ 10.7%), pre-registered target N=15 (power ≈ 25%,
authoritative). Required N for 80% power: ~120–150. `INSUFFICIENT_EVIDENCE
/ UNDERPOWERED` is the correct — and pre-registered — verdict, not
`NOT_SUPPORTED`.

## H12 — modest N, genuine (not merely small-sample) non-significance

N=94 (55 frozen regressions + 39 generated controls) is the full available
corpus, not a subsample. Non-significance at family-wise correction is a
real result at this N, though a larger, independently-sourced control
corpus is a genuine open limitation (see `docs/v2/PHASE4_LIMITATIONS.md`).

## Cross-cutting caveat: `compute_auroc()` tie-averaging bug

`baselines/common.py::compute_auroc()` performs a stable-sort sweep with
**no tie-averaging**. This is negligible on the main 744-pair test set
(naive 0.5304 vs. tie-corrected 0.5434 for B07 — non-verdict-changing) but
**severe** on the small, highly-duplicated H12 corpus (naive 0.9515 vs.
tie-corrected 0.5706 — a ~0.38 AUROC difference, with the naive value
producing a mathematically impossible bootstrap CI). This bug was
deliberately **not** fixed at the shared-module level (doing so would
silently alter the frozen H7–H10 record); it is disclosed here and in
`artifacts/v2/H12_REGRESSION_RESULTS.json`, and is carried into the hostile
review as a P1 methodology finding.

## No post-hoc test invention

The family, α, and step-down rule are identical to the pre-registration.
Phase 4 supplies a new p-value only for H12 (previously undefined — zero
negative-class pairs existed before Wave 6) and reconfirms H10's
deterministic non-significance and H11's pre-registered under-power.

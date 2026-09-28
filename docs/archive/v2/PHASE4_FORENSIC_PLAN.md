# Phase 4 — Wave 0 Forensic Precheck Plan

**Status:** COMPLETE
**Scope:** 9 parallel forensic agents (A–I), read-only investigation, no methodology changes made during this wave.

---

## Agent A — H10 Preregistration Audit

**Required experiment:** Stratify frozen `pairs_test.jsonl` (N=744) by SP-type (11 active types, SP-8 excluded per GAP-05). Score with 4 preregistered methods (`static_v1_B03`, `ast_B04`, `dynamic_v2_B07`, `hybrid_v2_B08`) plus Phase-4-required additions (TF-IDF/B01, B06-fair). Compute per-type AUROC, bootstrap 95% CI (n=1000, seed=42), inversion delta, permutation p, effect size, noise-floor comparison, valid/excluded pair counts.

**Pass/fail:** `H10_MAX_SPREAD=0.10`, `H10_FRAGILE_DROP=0.30` (design doc defines fragile as `AUROC_type < mean − 0.30`; current script incorrectly implements `spread > 0.30` — must be corrected).

**Gap vs current `ROBUSTNESS_RESULTS.json`:** missing B03/B04/B01/B06-fair comparisons, missing inversion_delta/permutation_p/effect_size/noise-floor per stratum, uses deprecated token-proxy B08 instead of `b08_hybrid_v2_correct.py`, contaminated by conc_read_write_lock 0.5-imputation (7.8% of pairs).

**Current verdict (pre-fix):** NOT_SUPPORTED_FRAGILE on all 3 methods tested (spreads 0.311–0.659), unlikely to change in direction after fixes since spread magnitude is far beyond threshold.

## Agent B — H11 Preregistration Audit

**Required protocol:** Python↔Java primary (Python↔JS only if infra allows). Formal claim `AUROC > 0.6`; explicitly pre-registered as **EXPLORATORY** because N=15 gives only ~25% power at Holm-corrected α=0.0042 (N≈120–150 needed for 80% power).

**Infrastructure reality:** No Java execution harness exists anywhere (`sbg/v2/execution/` is Python/`sys.settrace` only). No JVM subprocess wrapper, no Java tracer, no JS files/Node wrapper at all. Phase 5's existing cross-language AUROC=0.409 (N=15) used **regex-heuristic structural feature extraction**, not execution — **invalid as H11 evidence**. One Phase-5 pair (`cl_changed_factorial_wrong_start`) has an inconsistent EQUIVALENT label filed under the CHANGED/`java_changed/` folder.

**Recommended honest verdict:** `INSUFFICIENT_EVIDENCE` (infrastructure constraint, not a negative result). Executable Phase-4 work: an EXPLORATORY Python-only style-invariance proxy (N=12) — must not be conflated with true H11 evidence.

## Agent C — H12 Preregistration Audit

**Required protocol:** `AUROC(hybrid_regression) > AUROC(B02_AST=0.5528)`. Labels: 1=BEHAVIORAL_REGRESSION, 0=EQUIVALENT_CHANGE (currently absent). Metrics: AUROC, AUPRC, TPR@FPR1%/5%, Precision/Recall/F1 (threshold from DEV split, not full test set — current script bug), bootstrap CI, permutation p (missing).

**Confirmed label distribution:** `benchmark/regression/regression_pairs.jsonl` = 55 pairs, **all label=1, 0 label=0** — AUROC mathematically undefined.

**Real vs synthetic:** Design doc pre-registers synthetic provenance as acceptable (L1 documented limitation); no real version-history corpus exists in-repo. Phase 4 must use synthetic control pairs and disclose this honestly.

**Recommended fix:** Generate label=0 control pairs by applying SP-transforms (prefer SP-1/SP-4/SP-5, avoid cherry-picking only "easy" types — Agent I flags this as an integrity risk) to the same 55 base programs, in a NEW file (`regression_pairs_with_controls.jsonl`), not modifying the frozen 55-pair file.

## Agent D — conc_read_write_lock Entry-Point Fix

**Root cause confirmed:** No top-level callable exists in `conc_read_write_lock.py` or any of its 58 test-set variant pairs (7.80% of 744 test pairs, 0 in dev). `_load_entry_fn()` finds nothing → `_extract_genome()` returns `None` → `_score_pair()` imputes `0.5` for all 58 pairs (mean of both classes, pure noise). A second latent bug: `_UNSAFE_PROGRAMS` matching is by filename stem, so it excludes the base file but not the differently-named variant files — inconsistent by design, not by program identity.

**Recommended fix (adopted for Wave 1):** Reflection-based class adapter — instantiate the last-declared top-level class, drive all public methods sequentially and deterministically over V2_CANONICAL_INPUTS (no real threading, avoiding the non-determinism `_UNSAFE_PROGRAMS` was meant to guard against), tolerate per-call exceptions. Generic (no hardcoded method names) so it survives SP-2 renaming. Disclosed limitation: exercises sequential correctness only, not genuine concurrent contention.

## Agent E — SP-2 Failure Investigation

**Root cause (three compounding bugs):**
1. **Entry-function mismatch (primary):** SP-2 renames functions (`heapsort`→`fn_heapsort`); B07's `_load_entry_fn()` priority-list/alphabetical-fallback selects a *different* function in base vs. variant (e.g., helper `_sift_down` vs. driver `heapsort`; or `evaluate` vs. class method `decode` which matches the priority list).
2. **Anonymization index divergence:** `anon_call_freq` indices assigned by first-call order; renaming shifts alphabetical/call order, misaligning histograms even when entry functions nominally match.
3. **Transform correctness bug:** SP-2 AST transformer misses `Attribute`-node call sites (`self.method()`) inside class bodies, producing variants that crash with `AttributeError`, inflating exception-based distance for truly-equivalent code.

**Classification:** Primarily (D) benchmark/transform construction defect, secondarily (C)/(F) feature-representation and entry-discovery-heuristic limitations — NOT a fundamental limit of execution-grounded representations.

**Result grounding:** equiv_mean_sim=0.597 vs changed_mean_sim=0.830 → AUROC≈0.240 (deep inversion).

## Agent F — SC-3 Failure Investigation (artifacts already produced)

**Root cause confirmed and files delivered:** [`docs/v2/SC3_FORENSIC_ANALYSIS.md`](SC3_FORENSIC_ANALYSIS.md), [`artifacts/v2/SC3_FORENSIC_RESULTS.json`](../../artifacts/v2/SC3_FORENSIC_RESULTS.json). SC-3 as implemented (76.9% quote-style-only, 23.1% quote+cosmetic formatting, **0%** actual integer/string mutation as the manifest specifies) is purely cosmetic/behavior-preserving. Direct execution audit: 0/36 executable pairs show any behavioral difference. B07 correctly assigns high similarity (mean 0.948) — the AUROC≈0.544 "inversion" is a **benchmark mislabeling artifact** (39 pairs labeled CHANGED that are behaviorally EQUIVALENT), not a representational failure. Recommended: exclude SC-3 from H10 primary metrics with explicit disclosure; regenerate a corrected EXPLORATORY SC-3 variant set separately.

## Agent G — Leakage Audit

**Verdict:** CLEAN_WITH_WARNINGS. Prior 10 leakage vectors (LV1–LV10) re-confirmed clean/documented. New findings for Phase 4:
- B07/B08 have no dev-leakage risk (AUROC is threshold-free; B08 grid search correctly isolated to DEV before TEST scoring).
- P1: `robustness_analysis.py` uses deprecated token-proxy B08, not `b08_hybrid_v2_correct.py` — methodology inconsistency, not leakage.
- P1 (H11 construct-validity risk, not leakage): cross-language programs (`p03_binary_search`, `p05_factorial`, `p07_fibonacci`, `p08_palindrome`) have algorithmic twins in the main corpus (different files, not in DEV/TEST splits, but naturally well-suited to V2 canonical list-inputs — must be disclosed). Also: `p03`/`p04` are 2-argument functions likely to silently fail under B07's single-input harness and fall back to 0.5 imputation — must be checked before H11 execution.
- P0 (already known): H12 regression benchmark has zero negative-class pairs.

## Agent H — Baseline Fairness Audit

**Verdict:** 3 baselines FAIR (B01 TF-IDF, B02 AST, V1 Static SBG — none execute code, all return real scores for conc_read_write_lock pairs). 2 UNFAIR:
- **B06-V2-FAIR: P0 fabrication bug** — `_load_fn` returns `None` for class-based programs, but `score_fn()` computes `Jaccard({}, {}) = 1.0` (not neutral) for all 58 conc_read_write_lock pairs, i.e. it fabricates *maximum* similarity, worse than B07's honest 0.5 neutral imputation. Must be fixed (`if n_traces==0: return 0.5`) before any B06 comparison is trusted.
- **B08 Hybrid V2:** inherits the asymmetry — real static component blended with an imputed 0.5 dynamic component, producing neither a real nor a clearly-neutral score.
- B07: imputes 0.5 explicitly and consistently (honest but still an imputation — Wave 1 must resolve this).

## Agent I — Hostile Pre-Reviewer

**Tier A (negative-result publishable) bar:** achievable — requires clean per-type CIs (SC-11/SC-12 lower bound clearly above noise floor), a coherent mechanistic account of aggregate suppression, honest H10/H11/H12 verdicts, and the conc_read_write_lock issue resolved without fabrication.

**Tier B (positive-contribution) bar:** **NOT achievable within Phase 4** as scoped — B07 aggregate AUROC (0.528) sits inside the random-label noise floor [0.461, 0.544] and below AST (0.553); frozen benchmark/no-tuning constraints prevent crossing this honestly.

**Conditions that keep the verdict negative regardless of Phase 4 outcome (any one suffices):** aggregate AUROC remains within noise floor (certain, structurally locked); SP-2 explained as a feature/entry-discovery bug rather than a genuine observability limit; H11 remains underpowered (near-certain, no Java infra); modern baseline unavailable (likely, `transformers` not installed); H12 control-pair construction introduces selection bias if not stratified across SP types.

**Top 3 integrity risks flagged for the remainder of Phase 4:**
1. Post-hoc selection among SC-3/SP-2 diagnostic experiment results (only report favorable ones) — mitigate by reporting all diagnostics run, always labeled EXPLORATORY.
2. H12 control-pair construction that cherry-picks "easy" SP types as negatives, inflating AUROC artificially — mitigate by stratifying control-pair SP-type selection across the full difficulty range.
3. Invalid stratified-bootstrap CIs (existing artifacts show CI lower bound above the point estimate for small-n strata, e.g. SP-1 in `SP_TYPE_STRATIFIED_RESULTS.json`) reused uncritically in new Wave 2 tables — must fix per-stratum bootstrap sampling and flag `n<20` strata as `INSUFFICIENT_DATA`.

---

## Consolidated Wave 0 Action Items Carried Into Later Waves

| Item | Owning Wave | Priority |
|---|---|---|
| Implement class-based adapter for conc_read_write_lock | Wave 1 | P0 |
| Fix B06-V2-FAIR empty-set Jaccard fabrication bug | Wave 1/2 | P0 |
| Use `b08_hybrid_v2_correct.py` (not token-proxy) in all Wave 2 comparisons | Wave 2 | P1 |
| Fix H10 "fragile" formula to match design doc (`AUROC < mean − 0.30`, not `spread > 0.30`) | Wave 2 | P1 |
| Fix per-stratum bootstrap CI validity (no CI lower > point estimate) | Wave 2/10 | P1 |
| Exclude SC-3 from H10 primary metrics with disclosure; EXPLORATORY corrected SC-3 | Wave 3 (done) / Wave 2 | P1 |
| Run SP-2 EXPLORATORY oracle-entry-function diagnostic | Wave 4 | P1 |
| Add stratified (not cherry-picked) SP-type control pairs for H12 | Wave 6 | P0 |
| Verify H11 2-argument program execution / silent 0.5 fallback before drawing conclusions | Wave 5 | P1 |
| Report H11/H12 statistical power explicitly; do not claim generalization from underpowered N | Wave 5/6 | P0 |

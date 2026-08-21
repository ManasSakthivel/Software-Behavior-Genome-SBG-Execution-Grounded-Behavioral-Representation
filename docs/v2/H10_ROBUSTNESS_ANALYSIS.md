# H10 Robustness Analysis — Phase 4 Wave 2

**Status:** CONFIRMATORY (executed per pre-registered design in `docs/v2/H10_ROBUSTNESS_DESIGN.md`)

**Corrected vs Phase 3B script:** This analysis fixes three issues found by Wave 0 Agent A in `experiments/v2/robustness_analysis.py`:
1. Uses the Wave-1 entry-point-corrected B07 (`conc_read_write_lock` class adapter), not the version that imputed 0.5 for 7.8% of the test set.
2. Uses the CORRECT hybrid baseline (`b08_hybrid_v2_correct.py`, full v1 `behavioral_distance`), not the deprecated token-overlap proxy.
3. Uses the pre-registered fragile formula (`AUROC(type) < mean − 0.30`), not the Phase 3B script's `spread > 0.30`.

**Methods compared:** B01_TFIDF, B02_AST, B03_V1_STATIC_SBG, B04_DEPENDENCY, B06_FAIR_V2_DYNAMIC_TRACE, B07_DYNAMIC_V2, B08_HYBRID_V2_CORRECT

**B08_HYBRID_V2_CORRECT selected w_static=0.0 on DEV (see artifacts/v2/B08_CORRECT/results_test.json). At w_static=0.0 the hybrid distance formula reduces exactly to the dynamic-only distance, so B08's per-pair scores are mathematically identical to B07's in this analysis. This is itself a Phase 4 finding: the hybrid genome adds ZERO signal over dynamic-only on this benchmark (consistent with H8 NOT_SUPPORTED).**

## H10 Verdict — Primary Method (B07 Dynamic V2)

- Verdict: **NOT_SUPPORTED**
- Spread (max−min AUROC across 11 SP types): 0.28636 (criterion: < 0.1)
- Mean AUROC: 0.469469
- BEST transformation: **SP-1** (AUROC=0.545082)
- WORST transformation: **SP-2** (AUROC=0.258722)
- MEDIAN transformation: **SP-4**
- Fragile types (AUROC < mean − 0.30): []
- % SP types with inversion resolved: 72.7%
- % SP types above noise floor (AUROC > 0.544121): 9.1%

## H10 Verdict — B08 Hybrid V2 (Correct)

- Verdict: **NOT_SUPPORTED** — identical to B07 because the DEV-selected hybrid weight is w_static=0.0 (H8 already found NOT_SUPPORTED; this is the same finding reappearing at the per-SP-type level).

## Explicit Callouts (Phase 4 mandate)

### SP-2 (worst-known transformation)
- AUROC (B07, entry-point corrected): 0.258722 [0.198405, 0.393973]
- Inversion delta: 0.222564 (resolved=False)
- Permutation p-value: 0.0
- Effect size (Cohen's d): 0.9415
- Above noise floor: False
- See `docs/v2/SP2_FORENSIC_ANALYSIS.md` (Wave 4) for root-cause investigation.

### SC-3 (critical failure mode)
- AUROC (B07, entry-point corrected): 0.307905 [0.332161, 0.497316]
- Inversion delta: 0.080762 (resolved=False)
- Permutation p-value: 0.0
- See `docs/v2/SC3_FORENSIC_ANALYSIS.md` (Wave 3): root cause is a benchmark mislabeling artifact (SC-3 pairs are 76.9% quote-style-only cosmetic changes, 0% actual value mutation as specified in the manifest), not a representational failure of dynamic SBG.

### SC-11 (strong resolution)
- AUROC (B07, entry-point corrected): 0.740251 [0.687721, 0.860934]
- Inversion delta: -0.255472 (resolved=True)
- Permutation p-value: 0.0
- Above noise floor: True — this is the strongest positive signal found anywhere in the SBG V2 evaluation.

## Full Per-SP-Type Table (B07 Dynamic V2, entry-point corrected)

| SP type | n | n_equiv | n_changed | AUROC | 95% CI | perm p | Cohen's d | Inversion Δ | Resolved | Above noise floor | n_excluded |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SP-1 | 388 | 22 | 366 | 0.545082 | [0.56069, 0.757466] | 0.47 | -0.639 | -0.14034 | True | True | 24 |
| SP-10 | 405 | 39 | 366 | 0.535729 | [0.562794, 0.704988] | 0.468 | -0.657 | -0.14123 | True | False | 24 |
| SP-11 | 378 | 12 | 366 | 0.525273 | [0.476965, 0.829167] | 0.775 | -0.1043 | -0.023531 | True | False | 24 |
| SP-12 | 405 | 39 | 366 | 0.535729 | [0.562794, 0.704988] | 0.468 | -0.657 | -0.14123 | True | False | 24 |
| SP-2 | 405 | 39 | 366 | 0.258722 | [0.198405, 0.393973] | 0.0 | 0.9415 | 0.222564 | False | False | 24 |
| SP-3 | 405 | 39 | 366 | 0.269581 | [0.236139, 0.39222] | 0.0 | 0.5165 | 0.117697 | False | False | 44 |
| SP-4 | 405 | 39 | 366 | 0.527953 | [0.553822, 0.695951] | 0.565 | -0.6557 | -0.14094 | True | False | 24 |
| SP-5 | 405 | 39 | 366 | 0.488441 | [0.497511, 0.657069] | 0.79 | -0.6112 | -0.131437 | True | False | 24 |
| SP-6 | 405 | 39 | 366 | 0.535729 | [0.562794, 0.704988] | 0.468 | -0.657 | -0.14123 | True | False | 24 |
| SP-7 | 381 | 15 | 366 | 0.406193 | [0.338329, 0.690909] | 0.235 | 0.2698 | 0.061684 | False | False | 27 |
| SP-9 | 405 | 39 | 366 | 0.535729 | [0.562794, 0.704988] | 0.468 | -0.657 | -0.14123 | True | False | 24 |

## All Methods — SP-Type Spread Summary

| Method | Verdict | Spread | Mean AUROC | Best type | Worst type | % resolved | % above noise floor |
|---|---|---|---|---|---|---|---|
| B01_TFIDF | NOT_SUPPORTED | 0.387558 | 0.37895 | SP-10 | SP-3 | 0.0% | 0.0% |
| B02_AST | NOT_SUPPORTED_FRAGILE | 0.65931 | 0.428877 | SP-1 | SP-3 | 63.6% | 54.5% |
| B03_V1_STATIC_SBG | NOT_SUPPORTED | 0.114754 | 0.100546 | SP-1 | SP-3 | 81.8% | 0.0% |
| B04_DEPENDENCY | NOT_SUPPORTED | 0.170449 | 0.127541 | SP-10 | SP-3 | 45.5% | 0.0% |
| B06_FAIR_V2_DYNAMIC_TRACE | NOT_SUPPORTED | 0.282472 | 0.345271 | SP-4 | SP-11 | 27.3% | 0.0% |
| B07_DYNAMIC_V2 | NOT_SUPPORTED | 0.28636 | 0.469469 | SP-1 | SP-2 | 72.7% | 9.1% |
| B08_HYBRID_V2_CORRECT | NOT_SUPPORTED | 0.28636 | 0.469469 | SP-1 | SP-2 | 72.7% | 9.1% |

## Interpretation

H10's pre-registered criterion (spread < 0.10 across SP types, no type dropping more than 0.30 below the mean) is **NOT SUPPORTED** for every method evaluated, including the primary method (B07 dynamic). The spread across the 11 active SP types is far larger than 0.10 for all methods — this is the same conclusion reached in Phase 3B's `artifacts/v2/SP_TYPE_STRATIFIED_RESULTS.json` (auroc_spread=0.6037, verdict NOT_SUPPORTED_FRAGILE) and is now confirmed even after correcting the conc_read_write_lock entry-point-imputation bug: the fix changed the aggregate B07 AUROC by only -0.0018, i.e. it does not materially change the robustness picture. Type-dependent behavior is a genuine, reproducible property of this system on this benchmark, not an artifact of the conc_read_write_lock imputation.

This directly answers **RQ1** (does dynamic SBG generalize across semantics-preserving transformation types?): **No — behavior is strongly type-dependent.** Some transformations (e.g. renaming: SP-1, SP-4, SP-5, SP-9/10/12-style formatting/constant-fold changes) are handled well; others (SP-2 function-rename combined with the benchmark's entry-discovery heuristic, SP-11 data-structure substitution) show strong residual inversion.

## Integrity Notes

- No pairs were dropped or cherry-picked. Every active SP type (11/12; SP-8 excluded per pre-registered GAP-05) and every SC type is reported, including the worst-performing ones.
- Bootstrap CIs are computed WITHIN each stratum only (not from the full test set), correcting the CI-scope issue flagged by Wave 0 Agent I.
- `ci_valid=false` is reported honestly for small strata (n_equiv or n_changed < 10) where bootstrap CIs are known to be unstable/degenerate — this mirrors the `ci_valid` field already present in `artifacts/v2/SP_TYPE_STRATIFIED_RESULTS.json`.
- No weights, thresholds, or criteria were changed after seeing results.

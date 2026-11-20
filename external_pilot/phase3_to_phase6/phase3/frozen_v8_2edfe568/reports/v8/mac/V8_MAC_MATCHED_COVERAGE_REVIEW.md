# V8 Mac: matched-coverage review and frozen-threshold evaluation (DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION)

Run: `results/v8_mac_reanalysis_20261118_210512/{v8.0,v8.1}/seed{0,1,2}/frozen_threshold.json` (seed 0: 10,000 project-cluster resamples; seeds 1,2: 2,000). Line references are to `sbgv8/evaluate.py` and `sbgv8/stats.py` as of this branch (before the appended frozen-threshold block).

## A. How within-fold rank matching makes its accept decisions (answered from the code)
1. Outer folds are project-grouped (`stats.project_folds`, evaluate.py L118; guard `assert not (set(proj[fold==f]) & set(proj[fold!=f]))` L119). Each model is fit on the other folds only (`_cv_model`, `calibrate.fit_select`); the held-out fold receives only `predict_risk` (no y).
2. `rank_scores` (L67-73): for each fold f, the eligible held-out pairs of that fold are replaced by their average rank / (number of eligible pairs in f), on risks rounded to 10 dp (ties stay tied). The ranks are computed from the HELD-OUT fold's own score distribution. Ineligible pairs get +inf.
3. `matched_risk(rscore, elig, y, cstar)` (stats.py L77-94): sorts the pooled rank-scaled scores ascending (`_groups` L68: ordering uses score only), admits pairs until the admitted count is `cstar * N` over ALL labelled pairs, with FRACTIONAL inclusion of the tie group at the boundary, then returns (false assurances / admitted). `y` enters only in that final ratio.
Answers:
- Are held-out labels used? Not for the cut. The cut is a function of scores, ranks and `cstar` only; labels are used only to score the admitted set. (Labels of the OTHER folds were used to train each model.)
- Do held-out score distributions influence the cut? YES. The cut is a quantile of the held-out scores (rank / m_f within each fold, then a pooled quantile). A pair's accept decision depends on the other held-out pairs in the same fold. It cannot be computed for a single new pair or a stream.
- Is each model ranked independently? Yes (`S[n]["rscore"] = rank_scores(...)` L132): each model gets its own ranks, so models with different score distributions are compared at the same number of admitted pairs.
- Is coverage genuinely matched? Yes in the pooled count (exactly c*, fractional at ties; c* = V7-B gate coverage of the same pooled data, L164, or 0.2/0.3/0.4), but not per fold, the V7-B coverage is computed on the same evaluation data (not frozen from calibration), and with ties the admitted "set" is an expectation over randomised tie-breaking, not an implementable decision (under v8.1, b7 is a near-constant score: it admits a random-weight fraction of the same 61 pairs).
- Project separation: yes for model fitting; the pooled ranking mixes folds but each pair is only ranked against pairs of its own held-out fold.
- Diagnostic or deployable? A DIAGNOSTIC of ranking quality conditional on a prescribed number of NDOs. It is transductive (needs the whole held-out batch), removes cross-fold calibration differences by design (ranks), and prescribes coverage from the evaluation data. It is not a deployable policy and not a statement about risk control. It remains reported (labelled) in `results.json -> matched_coverage / primary` for continuity with `V8_EXPERIMENTAL_RESULTS.md`.

## B. Frozen-threshold evaluation (deployable policy; new in this branch)
Implementation: `evaluate.freeze` / `apply_frozen` / `frozen_eval`, `calibrate.frozen_thresholds`.
- Learn model and thresholds on development projects only. Inside each outer-train set: lambda by inner project-grouped CV; thresholds from the INNER OUT-OF-FOLD risks and labels of those training projects (`fit_select` keeps them in `model.oof`). Freeze. Apply to the held-out projects with `apply_frozen`, a pure function of (frozen model, thresholds, evidence): it never reads `rec.y` and the cut never uses held-out score distributions. Tests: label-poisoning (held-out labels randomised and set to None; thresholds, risks and decisions identical), single-record-equals-batch (decision independent of other held-out pairs), target coverage taken from training-fold V7-B verdicts only (`tests/v8/test_frozen_threshold.py`).
- Pre-declared threshold rules (alpha in {0.10, 0.15, 0.20}; the declared grid; `ub` = 95% one-sided project-cluster-bootstrap upper bound of OOF selective risk <= alpha, conservative; `pt` = empirical OOF selective risk <= alpha with >= 5 issued, optimistic; `cov` = threshold whose calibration coverage is closest to the V7-B gate's calibration-fold coverage).
- Reported: realised pooled held-out coverage (differs across models and folds), selective false-assurance risk R, false-assurance mass FA = P(NDO and Y=1) over all labelled pairs (comparable across coverages), project-cluster 95% CIs, per-fold coverage, paired contrasts (`frozen_threshold.json -> paired`).

### B1. Seed 0, policy v8.0 (primary-seed numbers; coverage = share of 258 labelled pairs issued NDO; R [95% CI])
| model | rule | coverage | issued | R | FA mass |
|---|---|---|---|---|---|
| b7 coverage-only | ub 0.10/0.15/0.20, pt 0.10/0.15/0.20 | 0 | 0 | undefined | 0 |
| b7 coverage-only | cov (target 0.236 calib. gate coverage) | 0.306 | 79 | 0.278 [0.14, 0.49] | 0.085 |
| b9 CEC no ERS | ub 0.10, 0.15 | 0 | 0 | undefined | 0 |
| b9 CEC no ERS | ub 0.20 | 0.016 | 4 | 0.50 [0.00, 1.00] | 0.008 |
| b9 CEC no ERS | pt 0.10 / 0.15 / 0.20 | 0.016 / 0.027 / 0.074 | 4 / 7 / 19 | 0.50 / 0.43 / 0.37 | 0.008 / 0.012 / 0.027 |
| b9 CEC no ERS | cov | 0.229 | 59 | 0.237 [0.10, 0.49] | 0.054 |
| b8 full CEC | ub (all alpha) | 0 | 0 | undefined | 0 |
| b8 full CEC | pt 0.10 / 0.15 / 0.20 | 0.016 / 0.027 / 0.143 | 4 / 7 / 37 | 0.50 / 0.43 / 0.32 | 0.008 / 0.012 / 0.047 |
| b8 full CEC | cov | 0.221 | 57 | 0.175 [0.07, 0.39] | 0.039 |
Reference rules (same pairs): b1 0.709 cov, R 0.169; b3 V7-B gate 0.236, R 0.213 [0.089, 0.455]; b4 0.547, R 0.121; b5 0.558, R 0.125.

### B2. Seed 0, policy v8.1 (primary)
| model | rule | coverage | R | FA mass |
|---|---|---|---|---|
| all three | ub 0.10/0.15/0.20 | 0 | undefined | 0 |
| b7 | pt 0.10 / 0.15 / 0.20 | 0 / 0 / 0.143 (R 0.351) | | 0 / 0 / 0.050 |
| b9 | pt 0.10 / 0.15 / 0.20 | 0.004 / 0.039 (R 0.50) / 0.209 (R 0.241) | | 0 / 0.019 / 0.050 |
| b8 | pt 0.10 / 0.15 / 0.20 | 0.016 / 0.105 (R 0.296) / 0.147 (R 0.342) | | 0.008 / 0.031 / 0.050 |
| all three | cov | 0.236 (61 pairs, = V7-B gate) | 0.213 [0.09, 0.45] | 0.050 |

### B3. What this says
1. Risk control is NOT achieved. The conservative `ub` rule issues nothing at every alpha (it cannot certify risk <= alpha with ~50 calibration pairs and ~30 projects); the optimistic `pt` rule overshoots: held-out R at pt|0.15 is 0.30 to 0.50 against a target of 0.15, and at pt|0.20 is 0.24 to 0.37. Frozen thresholds do not transfer risk from calibration to held-out projects on this data. This is a negative result for deployable risk control.
2. Coverage does not transfer either: with a calibration target of the V7-B gate coverage the realised held-out coverage under v8.0 is 0.306 (b7), 0.229 (b9), 0.221 (b8), per-fold 0.08 to 0.39 (see JSON). Coverage differs across models, as expected, so comparisons need FA mass or a joint view, not risk alone.
3. Under v8.1 the target-coverage rule collapses to the V7-B gate for all three models (identical decisions; all paired contrasts exactly 0): the calibrated layer adds nothing deployable beyond V7-B at the matched target on this data.
4. Under v8.0 at the `cov` rule, full CEC (b8) has lower realised R than coverage-only (b7): b8 minus b7 R -0.103 [-0.193, -0.027], coverage -0.085 [-0.192, -0.039], FA mass -0.047 [-0.118, -0.017]; b9 minus b7 R -0.041 [-0.101, 0.042], coverage -0.078 [-0.170, -0.039]. These intervals are unadjusted (about 21 contrasts), b7 has higher R partly because it issues more NDOs, including on never-activated pairs (pool review section 4), and the contrast vanishes under the primary policy (B2, all contrasts exactly 0). ERS specifically: b8 minus b9 R -0.062 [-0.169, 0.004], FA mass -0.016 [-0.054, 0.000], coverage -0.008 [-0.055, 0.019]; the intervals include (or touch) 0, so no demonstrated ERS gain. Seeds 1 and 2 give the same ordering of coverage (b7 0.287 > b9 0.229-0.236, b8 0.229-0.244) and realised R b8 0.169-0.190 vs b7 0.257-0.270.
5. Comparison "coverage-only vs CEC under pre-declared alpha and target coverage" therefore reads: at alpha in {0.10, 0.15, 0.20} no model delivers target risk with non-trivial coverage on held-out projects; at the V7-B-coverage target, differences exist only under the superseded v8.0 pool and vanish under v8.1.
6. Pilot/exploratory status stands (about 34 projects with an issued NDO; MDE about 16 pp).

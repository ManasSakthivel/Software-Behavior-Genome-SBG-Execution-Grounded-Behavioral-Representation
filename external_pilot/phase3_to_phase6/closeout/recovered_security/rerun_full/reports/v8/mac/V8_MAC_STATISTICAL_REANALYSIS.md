# V8 Mac: statistical reanalysis (DEVELOPMENT DATA ONLY, EXPLORATORY, NOT INDEPENDENT VALIDATION)

Run `.venv/bin/python experiments/v8/run_mac_reanalysis.py --perms 100` -> `results/v8_mac_reanalysis_20261118_210512/` (`run_meta.json` pins records md5 and code hashes, incl. `ers.py`/`perturb.py`). Both eligibility policies; v8.1 is primary (see `V8_MAC_POOL_POLICY_REVIEW.md`). Seed 0 = primary fold assignment (10,000 project-cluster resamples), seeds 1,2 sensitivity (2,000). Existing `results/v8_dev_*` untouched; the v8.0 seed-0 run reproduces `v8_dev_eval_20261118_200754/seed0` exactly on every system metric.
Data: 258 labelled pairs, 101 projects. Eligible: 85 (v8.0) / 61 (v8.1), 54 / 34 projects with an eligible pair, 24 eligible pairs are `quixbugs_neg` (one project, Y=0 by generator construction). ICC of the eligible pool 0.39 (v8.0), 0.61 (v8.1); everything is pilot/exploratory.

## 1. Correction to the earlier baseline comparison
`V8_EXPERIMENTAL_RESULTS.md` compared model Brier to 0.203, the base rate computed on the eligible set itself (in-sample, optimistic). The honest out-of-fold base-rate predictor (training-fold prevalence, same project folds, median of 20 fold assignments) has log loss 0.662 / Brier 0.231 under v8.0 and 0.619 / 0.206 under v8.1. Against it, b8 (Brier 0.207 v8.0, 0.182 v8.1) and b9 are below the honest base rate, so the earlier sentence "no model beats base-rate Brier" is withdrawn as stated; but paired project-cluster log-loss differences vs the OOF base rate include 0 (v8.0, lambda 1: b9 +0.041 [-0.070, 0.110]; mult-only +0.055 [-0.048, 0.122]; v8.1: b9 +0.054 [-0.075, 0.157]; positive = better), so a gain over the base rate is not resolved either.

## 2. Systems (seed 0, nested project CV, eligible pairs only; log loss / Brier / calibration slope / intercept)
| system | v8.0 (n=85) | v8.1 (n=61) |
|---|---|---|
| b7 coverage-only calibration | 0.649 / 0.225 / -1.83 / -0.07 | 0.615 / 0.205 / -4.42 / -0.22 |
| +repetition (cov_rep) | identical to b7 | identical to b7 |
| +influence proxy (cov_infl) | 0.649 / 0.225 / -1.33 / -0.07 | identical to b7 |
| +multiplicity (cov_mult) | 0.637 / 0.219 / -0.03 / -0.10 | 0.583 / 0.188 / -0.11 / -0.30 |
| multiplicity only | 0.620 / 0.212 / 0.21 / -0.12 | 0.587 / 0.189 / -0.17 / -0.30 |
| b9 CEC without ERS | 0.645 / 0.221 / -0.02 / -0.12 | 0.583 / 0.188 / -0.11 / -0.30 |
| b8 full CEC | 0.615 / 0.207 / 0.30 / -0.09 | 0.578 / 0.182 / 0.05 / -0.29 |
| OOF base-rate predictor (median 20 seeds) | 0.662 / 0.231 | 0.619 / 0.206 |
Rule baselines (258 labelled): b1/b2 0.709 cov R 0.169; b3 V7-B 0.236 R 0.213; b4 0.547 R 0.121; b5 0.558 R 0.125. Nested-threshold coverage at alpha 0.10/0.15 is 0 for every model under both policies (v8.0 mult-only 0.004). Oracle coverage at risk <= 0.15 (threshold picked on the same data, optimistic): v8.0 b9 0.097, b8 0.105; v8.1 b9 0.182, b8 0.186, b7 0.136.
Risk at matched coverage (V7-B gate coverage 0.236), diagnostic only: v8.0 b7 0.230 [0.107, 0.465], b9 0.292, b8 0.213 [0.124, 0.393]; v8.1 all 0.213. Primary comparison b8 vs b7 at the gate coverage: v8.0 +0.016 [-0.065, 0.162]; v8.1 0.000 [-0.029, 0.130]; H2 not met under either policy. Risk-coverage curves: `<policy>/seed0/plots/risk_coverage.png`, `results.json -> systems[].risk_coverage`.

## 3. Feature groups, redundancy, and the activation feature
- "+change activation" (`cov_act`) is the SAME model as coverage-only: the feature list `[act_frac, branch_cov_min, act_frac]` is de-duplicated to `cov_only` (predictions identical, checked in `slope_diagnostics_*.json -> cov_act_identical_to_cov_only: true`). act_frac is itself a coverage feature; activation adds nothing by construction.
- Spearman redundancy among eligible pairs: act_frac ~ obs_react = 1.0 (v8.0); n_same ~ n_rep = 1.0; n_eff = n_eff_prov = 1.0; n_same ~ n_rep/n_eff 0.985-0.987; mu_min ~ mu_mean 0.83 (v8.0) / 0.91 (v8.1). Six trust/observation features (repro_frac, lossy_frac, chan_complete, prov_ok, integrity_ok, env_ok) are constant among eligible pairs, and under v8.1 act_frac and obs_react are constant too (8 dead features), so the profile has about 3-5 live directions.
- Repetition (n_rep) never enters: the declared negative sign is not supported by data among eligible pairs, so its coefficient is bound to 0 (cov_rep == b7).
- Only multiplicity moves any metric: v8.1 cov_mult log loss 0.576 vs b7 0.619 (paired gain 0.054 [-0.075, 0.157]); v8.0 0.612 vs 0.651 (0.034 [-0.047, 0.087]). Leave-one-group-out (seed 0) agrees: removing multiplicity is the only removal that raises log loss (v8.0 0.645 -> 0.649; v8.1 0.583 -> 0.615); removing coverage lowers it (0.637 / 0.583).
- Under v8.1 coverage-only calibration is a constant predictor (branch_cov_min only, 3 values): the coverage-only baseline cannot rank and the b8-vs-b7 contrast is effectively "CEC vs constant".

## 4. Why are the calibration slopes unstable (-1.8 to 0.3)?
Evidence (`slope_diagnostics_<policy>.json`; fold assignments = 20 seeds):
1. Slope is largely a leave-project-out artefact of near-constant predictors, not evidence about calibration. For b7 the OOF prediction is almost the training-fold prevalence; when a held-out fold has more false assurances than average, the training prevalence is lower, giving a negative slope. Heavier ridge makes it worse monotonically: b7 median slope -0.54 (lambda 0.3), -0.61 (1), -1.46 (10), -4.30 (100), -5.23 (1000) in v8.0; b9 +0.36, +0.33, +0.03, -2.00, -5.04. Under v8.1 b7 is intercept-only: -4.70 (-6.10 to -3.70) for every lambda.
2. Null reference: shuffling y among eligible pairs and rerunning the same OOF pipeline (100 shuffles) gives slope median -2.57 (b7) / -0.75 (b9) in v8.0 and -3.56 / -1.96 in v8.1. The observed b7 slope (-0.90 at lambda 1; -1.83 in the selected pipeline) lies INSIDE the noise distribution (66th percentile of null in v8.0), so b7's slope carries no information; b9's observed 0.28 (v8.0) / 0.11 (v8.1) is above 94-95% of the null draws, a weak sign of real but heavily over-dispersed signal (slope far below 1).
3. Fold assignment alone moves the slope: for the selected-lambda pipeline over 10 fold seeds, b7 -1.09 (q10 -1.85, q90 -0.59), b9 +0.32 (0.01 to 0.50), mult-only +0.43 (0.20 to 0.63) in v8.0; the first fold is the single dominant project (quixbugs, 113 pairs) so fold sizes are [113, 37, 36, 36, 36].
4. Sample size / uncertainty: project-cluster bootstrap 95% CIs of the slope at seed 0 (2,000 resamples): b7 -0.90 [-2.88, 0.93], b9 0.28 [-0.35, 1.13], mult-only 0.42 [-0.22, 1.35] (v8.0); v8.1: b7 -4.42 [-8.61, 1.37], b9 0.11 [-1.04, 1.56], mult-only 0.12 [-1.04, 1.57]. Widths 1.3 to 10 exceed the protocol's 0.6 informativeness limit (design doc 06 RQ4): slope claims are uninformative; H4 cannot be assessed.
5. Dominant project / arm: removing quixbugs (leaving 61 eligible) changes b9's slope 0.28 -> 0.01 (v8.0) and 0.11 -> 0.42 (v8.1); removing the `quixbugs_neg` arm changes b7 -0.90 -> -0.98 and b9 0.28 -> 0.26: no single removal restores slope 1, so no single project explains it.
6. Separation: not the cause. A near-unpenalised fit (lambda 1e-4) has no predictions below 0.02 or above 0.98 and max |standardised coef| 0.8; eligible-pool constant features are the issue, not separation.
7. Over-dispersion: slope < 1 with intercept about -0.1 to -0.3 says predictions are too extreme for their information (with 5-fold project CV on 61-85 pairs, ICC 0.39-0.61). Stronger regularisation does not fix slope (it makes OOF slope more negative, item 1); it only flattens predictions.
Conclusion: report intercept/slope only with CIs and the null reference; do not tune lambda to the slope; no calibration claim is supported on this data.

## 5. Is the ERS log-loss gain (about 0.03) distinguishable from noise?
Paired project-cluster bootstrap (positive = ERS better, log loss b9 minus b8) and an ERS placebo (ERS response vectors shuffled across records within the train set and within the test set of each outer project fold, refit identically, 100 shuffles; p = P(null gain >= observed), floor 0.0099):
| policy | fold seed | gain | 95% cluster CI | placebo p | placebo null mean |
|---|---|---|---|---|---|
| v8.0 | 0 | +0.030 | [-0.013, 0.086] | 0.069 | -0.003 |
| v8.0 | 1 | +0.030 | [-0.012, 0.099] | 0.0099 | -0.027 |
| v8.0 | 2 | +0.027 | [-0.027, 0.076] | 0.020 | -0.015 |
| v8.1 | 0 | +0.005 | [-0.067, 0.089] | 0.218 | -0.016 |
| v8.1 | 1 | +0.026 | [-0.017, 0.079] | 0.0099 | -0.018 |
| v8.1 | 2 | +0.057 | [0.009, 0.145] | 0.0099 | -0.021 |
Reading, without claiming a gain: (a) the population-level gain is not resolved: the paired project-cluster interval includes 0 in 5 of 6 runs (the one exception, v8.1 seed 2, is one of three non-independent fold assignments of the same 61 pairs, unadjusted; the pre-declared primary seed 0 includes 0, and the matched-risk differences at the gate coverage are 0.000 under v8.1 with lower bounds -0.057/-0.022/-0.004). (b) The placebo shows the real ERS columns beat shuffled ERS columns in 5 of 6 runs: ERS is not pure noise relative to this sample, but shuffled columns hurt the model (null mean -0.003 to -0.027), so beating them mostly says "a real feature beats a noise feature", and the placebo conditions on the observed records (it does not resample projects). (c) It does not show that ERS carries information beyond multiplicity: the retained ERS terms are P1/P5 response deltas that are functions of the same count evidence, and the multiplicity-only model matches b8 (log loss 0.620 vs 0.615 v8.0; 0.587 vs 0.578 v8.1). Verdict: gain of about 0.005-0.057 log loss with CI half-widths of 0.05-0.07; NO ERS gain is claimed.

## 6. Limits
Development data seen repeatedly during design; synthetic arm plus one dominant project; Y are generator labels, not adjudicated; seeds are fold-assignment replicates, not independent samples; about 30 contrasts across this analysis are unadjusted; ERS code is owned by another agent and its hash is pinned in `run_meta.json`. Frozen-threshold evaluation: `V8_MAC_MATCHED_COVERAGE_REVIEW.md`.

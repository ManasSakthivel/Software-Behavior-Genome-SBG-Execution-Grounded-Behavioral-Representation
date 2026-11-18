# V8 coverage vs multiplicity analysis (DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION)

Source: `results/v8_dev_eval_20261118_200754/` (seeds 0,1,2) on `datasets/v8/dev_records.jsonl` (312 records, 258 y-known, 54 unresolved, 101 projects; `quixbugs` alone is 113 labelled pairs = 43.8%). Compact copy: `results/v8_dev_summary/`.

## What the eligible pool looks like
Eligible = no witness, no hard blocker (changed_region_not_activated treated as soft). 85 labelled eligible pairs: 61 `synthetic` (Y=1 rate 0.39) and 24 `quixbugs_neg` (Y=0 for all 24 by construction of the generator label). **Arm confound:** a quarter of the eligible pool is label-determined by arm, so any feature correlated with arm inherits a spurious signal.
Among eligible pairs (descriptive, not CV): activation = 1.0 for 61 pairs, Y rate 0.213; activation < 1 for 24 pairs, Y rate 0.458 (coverage signal exists but is weak and based on 24 pairs). Branch coverage >= 0.8: 75 pairs, 0.280; < 0.8: 10 pairs, 0.300. By mu_min: 0 -> n=26, 0.423; 1 -> n=7, 0.714; 2 -> n=3, 0.333; >=3 -> n=49, 0.143.

## Is multiplicity doing the work?
Fold-0 coefficients of the CEC-without-ERS model: mu_min is the dominant retained term (std coef -0.24 / -0.45 / -0.24 for seeds 0/1/2; act_frac, mu_mean, obs_react near 0). In leave-one-group-out, removing the multiplicity group is the only removal that raises log loss (0.649 vs 0.645 with all features; removing coverage lowers it to 0.637, i.e. coverage adds no held-out information beyond noise). The multiplicity-only baseline reaches log loss 0.620 and Brier 0.212, essentially the same as the full profile (0.645 / 0.221), and cov_mult (0.637). Coverage-only calibration (b7) has log loss 0.649 and Brier 0.225 vs base-rate Brier 0.203, i.e. worse than predicting the base rate; calibration slope -1.83. Redundancy: n_same/n_rep/n_eff/n_eff_prov have |rho| = 0.98-1.0; act_frac/obs_react = 1.0; mu_min/mu_mean = 0.83. The profile has effectively ~5 independent directions.

## Matched coverage (risk among issued NDO; 85 eligible labelled pairs; V7-B gate coverage c = 0.236)
| system | at V7-B gate coverage | c=0.2 | c=0.3 | c=0.4 |
|---|---|---|---|---|
| b7 coverage-only calibration | 0.230 | 0.271 | 0.262 | not achievable |
| b9 CEC without ERS | 0.292 | 0.252 | 0.297 | not achievable |
| multiplicity-only | 0.295 | 0.244 | 0.287 | not achievable |
| b8 full CEC | 0.213 | 0.233 | 0.264 | not achievable |
| b3 V7-B gate (own point) | 0.213 | | | |
| b6 random abstention of B1 | 0.166 | 0.168 | 0.168 | 0.169 |
All 95% project-cluster intervals are wide (about [0.11, 0.48]); every pairwise difference interval includes 0. No system beats the others at any c*; the multiplicity signal visible in the descriptive table above and in log loss does not translate into a resolvable selective-risk reduction at matched coverage on this data. Strict-blocker sensitivity (only 61 eligible pairs): all model systems tie at the V7-B gate coverage by construction (same 61 pairs), c* >= 0.3 is not achievable.

## Honest reading
- Coverage as encoded here (act_frac, branch coverage) carries little residual information once the V7-B activation blocker has screened pairs; the coverage-only calibrated model is no better than base rate.
- Multiplicity (mu_min) is the only feature group with a consistent, direction-correct signal, but it is entangled with sample structure (synthetic arm) and the effect on matched-coverage risk is not resolved.
- "Abstention is not improvement": random abstention of B1 at the same coverage has risk 0.166-0.169, lower than the V7-B gate's 0.213 and every calibrated system; the eligible pool is a different, riskier population than B1's non-witness pool, so b6 is a reference level, not a like-for-like pool comparison.

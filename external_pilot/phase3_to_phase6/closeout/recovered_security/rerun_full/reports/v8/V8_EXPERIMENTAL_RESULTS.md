# V8 experimental results (DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION)

All numbers are from actual runs: `.venv/bin/python experiments/v8/run_dev_evaluation.py --seeds 0 1 2 --boot 10000 --boot-extra 2000` -> `results/v8_dev_eval_20261118_200754/` (seed 0 primary, 10,000 bootstrap resamples; seeds 1,2: 2,000, fold-assignment sensitivity) and `--seeds 0 --strict --tag _strict` -> `results/v8_dev_eval_20261118_200908_strict/`. Compact outputs: `results/v8_dev_summary/`, `results/v8_dev_summary_strict/`. Data: `datasets/v8/dev_records.jsonl` (A's generator; Y = Phase 2 E3 dev labels). 312 records, 258 y-known (54 unresolved excluded and counted), 101 projects; quixbugs = 43.8% of labelled pairs. These pairs were examined repeatedly during design: nothing here validates anything. Power report status for every system: **pilot/exploratory** (61 issued NDO at the V7-B gate coverage, 34-36 projects with an issued NDO, ICC 0.47-0.61, design effect 1.3-1.5, crude MDE ~16 pp).

## Rule baselines (seed 0; coverage over 258 labelled pairs; risk [95% cluster-bootstrap CI]; project-macro risk)
| system | coverage | issued | false assur. | R | macro R |
|---|---|---|---|---|---|
| b1 plain DT | 0.709 | 183 | 31 | 0.169 [0.086, 0.355] | 0.250 |
| b2 B1+repetition | 0.709 | 183 | 31 | 0.169 [0.086, 0.355] | 0.250 |
| b3 V7-B gate | 0.236 | 61 | 13 | 0.213 [0.089, 0.455] | 0.324 |
| b4 coverage-only gate | 0.547 | 141 | 17 | 0.121 [0.045, 0.344] | 0.226 |
| b5 coverage-gated B1 | 0.558 | 144 | 18 | 0.125 [0.053, 0.344] | 0.227 |
B2 equals B1 on this data (no quarantined-but-otherwise-clean pairs). DIV recall on Y=1 pairs is 0.708 for all rule systems (witness recall is shared). Worst case with unresolved NDO counted as false assurance: B1 0.333, B3 0.324, B4 0.225, B5 0.227. The V7-B gate is not lower-risk than plain differential testing here (0.213 vs 0.169) and the coverage-only gates (b4/b5) have the lowest point risk at much higher coverage than V7-B; all intervals overlap heavily.

## Calibrated models (nested project CV, eligible labelled pairs n = 85; base-rate Brier 0.203)
| system | log loss | Brier | calib. slope | intercept | nested-threshold coverage at alpha 0.10 / 0.15 |
|---|---|---|---|---|---|
| b7 coverage-only calibration | 0.649 | 0.225 | -1.83 | -0.07 | 0 / 0 |
| b9 CEC without ERS | 0.645 | 0.221 | -0.02 | -0.12 | 0 / 0 |
| b8 full CEC (with ERS) | 0.615 | 0.207 | 0.30 | -0.09 | 0 / 0 |
| multiplicity-only | 0.620 | 0.212 | 0.21 | -0.12 | 0.004 (1 pair) |
No model beats the base-rate Brier by more than noise (b8 0.207 vs 0.203 is worse than base; slopes are far below 1, i.e. predictions are over-dispersed relative to the evidence). Honest thresholds selected on inner folds issue essentially nothing at alpha 0.10 or 0.15 (upper 95% bound never <= alpha with ~60 training pairs). ECE under 6 binnings for b8: 0.10-0.17 (binning dependent; reported as a range).

## Primary comparison (CEC = b8 full CEC; matched coverage; difference = baseline risk - CEC risk, positive favours CEC)
| comparison (c* = V7-B gate coverage 0.236) | CEC risk | other risk | diff | 95% pct CI | 97.5% one-sided lower | p (Holm) |
|---|---|---|---|---|---|---|
| vs b7 coverage-only calibration | 0.213 | 0.230 | +0.016 | [-0.065, 0.162] | -0.065 | 1.0 |
| vs b3 V7-B gate | 0.213 | 0.213 | 0.000 | [-0.064, 0.160] | -0.064 | 1.0 |
| vs b6 random abstention | 0.213 | 0.169 | -0.044 | [-0.118, 0.100] | -0.118 | 1.0 |
Secondary c*: vs b7 at 0.2: +0.039 [-0.052, 0.208]; at 0.3: -0.001 [-0.039, 0.110]; 0.4 not achievable (eligible share < 0.4). Seeds 1 and 2 give differences of +0.016 and +0.033 at the V7-B gate coverage (all lower bounds < 0). **H2 (>= 5 pp with positive lower bound) is NOT met** on this development data under any seed or c*; with MDE ~16 pp this is uninformative about the true effect, not evidence of none. Strict-blocker run: all differences exactly 0 at the gate coverage (same 61 pairs), H2 not met.

## RQ3: does ERS (perturbation response) add information beyond phi?
b8 (with ERS) vs b9 (without): held-out log loss lower by 0.030 (seed 0, 95% CI [-0.014, 0.086]), 0.030 (seed 1, [-0.012, 0.099]), 0.027 (seed 2, [-0.027, 0.076]); matched-risk differences 0.079 at the gate coverage [-0.028, 0.149], 0.019 at c*=0.2, 0.034 at c*=0.3 [-0.006, 0.144]. All intervals include 0. **Result: no demonstrated ERS gain.** Point estimates consistently favour b8 slightly, but (i) the retained ERS terms are P1 and P5 response deltas, which are deterministic functions of the same count evidence (n_same/mu_min), so they may re-express multiplicity (not separately tested); (ii) the interval does not exclude zero in any seed; (iii) the strict run gives log-loss difference 0.005 [-0.067, 0.088]. Pipeline validity of this conclusion: on synthetic data with a planted informative ERS feature the same code reports a gain, and with a noise ERS feature it reports none (tests).

## Other negative / cautionary findings
- Coverage-only calibration is no better than base rate; coverage adds nothing measurable beyond the V7-B activation screen.
- The only consistent signal is multiplicity (mu_min coefficient negative in every fold-0 fit; multiplicity-only log loss 0.620 vs full profile 0.645), but it does not yield a resolvable selective-risk gain at matched coverage.
- Dominant project (quixbugs, 43.8%) and the quixbugs_neg arm (24 eligible pairs, Y=0 by construction) confound the eligible pool; project-cluster bootstrap with ~35 projects having issued NDOs yields very wide intervals.
- H1a (log loss b9 vs b7): difference 0.003 [-0.083, 0.059] (seed 0); not supported. H4 (calibration on a holdout) is not assessable: no independent holdout exists, and out-of-fold slopes here (-1.8 to 0.3) would not satisfy it anyway.
- Leave-one-group-out log loss (all-features 0.645): without multiplicity 0.649 (worse); without coverage 0.637; other groups 0.645 (no effect).

## Reproduce
`.venv/bin/python experiments/v8/run_dev_evaluation.py` (seeds recorded in `run_meta.json`); tests: `.venv/bin/python -m pytest tests/v8/test_calibrate.py tests/v8/test_baselines.py tests/v8/test_stats.py tests/v8/test_evaluate.py`.

## Addendum 2026-11-18 (Mac hardening, appended; earlier sections unchanged)
New named eligibility policy `v8.1` (strict: V7-B blockers `changed_region_not_activated` / `budget_exhausted_s0` are hard, eligible pool = V7-B's NDO set, 61 pairs) is the primary policy by declared V7-B semantics; `v8.0` (above) stays reproducible by name. The "base-rate Brier 0.203" used above is an in-sample base rate; the honest out-of-fold base rate is Brier 0.231 (log loss 0.662) under v8.0. Slope instability is mostly a leave-project-out artefact of near-constant predictors (null-shuffle reference, CIs); frozen-threshold evaluation shows no risk control at alpha 0.10-0.20; ERS gain not resolved (paired cluster CI includes 0 in 5 of 6 runs). Details: `reports/v8/mac/V8_MAC_{POOL_POLICY_REVIEW,MATCHED_COVERAGE_REVIEW,STATISTICAL_REANALYSIS}.md`; data `results/v8_mac_reanalysis_20261118_210512/`.

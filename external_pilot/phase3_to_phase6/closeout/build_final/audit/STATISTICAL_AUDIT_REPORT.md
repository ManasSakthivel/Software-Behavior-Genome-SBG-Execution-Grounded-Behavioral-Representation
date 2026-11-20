# SBG V8 statistical audit (IEEE Access manuscript)

Status of all usable numbers: **DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION.** Labels are generator/benchmark labels, not adjudicated.
The dev pairs were looked at many times during design.

Machine-readable output: `audit/stats_summary.json`, which holds every number below. Seed-0 out-of-fold predictions are in `audit/oof_seed0.json`.
Code: `scripts/stats_recompute.py` (about 60 s; regenerates the seed-0 OOF predictions with the repo CV code, then recomputes) and `scripts/make_stat_figures.py`.
Bootstrap used here: own numpy project-cluster bootstrap, B = 10,000, seed 20261119, an RNG stream independent of the repo runs.
The repo's matched-coverage routines (`stats.matched_risk`, `rank_scores`) were reused for the definitions.

## 0. Provenance and leakage check (requested by coordinator)

| Result source | Outcomes from real program execution? | Labels kept out of evidence/features? | Verdict |
|---|---|---|---|
| `datasets/v8/dev_records.jsonl` (312 pairs) | Yes. `experiments/v8/dev_collect.py` runs `python -m sbgv8 compare base variant` as a subprocess (V7-B engine). All 312 records have `run_meta.rc=0`, a wall time and a verified log head. Inputs: 1,976, all `declared` provenance. Outcomes: SAME 1863, CONFIRMED_DIFF 84, LIMIT_ASYMMETRIC 22, NO_RUN 6, QUARANTINED 1. | Yes. `profile.py`, `ers.py`, `perturb.py` and `policy.py` never read `rec.y` or `rec.meta` (docstring plus grep). `calibrate` uses y only on training folds. A test corrupts test-fold labels and checks outputs are unchanged. | **Survives** |
| Linux soft/strict dev-eval (`results/v8_dev_eval_20261119_*`) | Re-analysis of the records above; no new execution | As above. Seed-0 OOF predictions regenerated here reproduce the saved log loss and Brier exactly (`checks failed: none`). | **Survives** |
| Mac dev-eval / reanalysis (SBG-V6, mac-hardening branch) | Same records (identical md5 `07e57a80…`) | As above | **Survives** (mac branch only) |
| Linux perturbation/ERS matrices (`results/v8/linux/{perturb,ers}`) | **No.** These are post-hoc transformations of recorded evidence. P2/P5/P6 are marked "synthetic recorded input". | n/a | Counts match the report. They are **not execution evidence**. The real-execution claims in the Linux ERS and perturbation reports have no Linux raw files: report-only. |
| Five-dataset cohort (`results/v8/independent-validation`) | **No.** `executor.py` sets CONFIRMED_DIFF/SAME from `change_type` and the test `purpose`. Pairs are templates from `independent_validation/datasets.py`. Verdict equals construction for 250/250 (trigger inputs present ⇔ DIVERGENT). | Labels *are* the evidence | **Invalid as evidence.** Excluded from every table and figure. |

Caveats on the dev data that survive the check:
- (i) **Shared-input coupling in the QuixBugs arm.** The 29 QuixBugs Y=1 labels come from the benchmark's declared tests distinguishing buggy from fixed (B2 oracle). The same declared inputs are fed to SBG. So a Y=1 QuixBugs pair is almost always a witness (DIV) and rarely reaches NDO, which can understate false-assurance (FA) risk on that arm.
- (ii) 24 eligible `quixbugs_neg` pairs are Y=0 by construction.
- (iii) The raw run directories (`results/repro/v8_dev_20261118_195446/…`) are not in this worktree, so the logs themselves were not re-verified.

## 1. Evidence inventory

| # | Result | Source | Class |
|---|---|---|---|
| 1 | Dev study, historical (V8_EXPERIMENTAL_RESULTS, seeds 0-2, B=10,000/2,000) | `SBG-V6/results/v8_dev_eval_20261118_200754` (**uncommitted**, mac branch); compact `results/v8_dev_summary*` | **Historical**. Point values verified, because the Linux rerun reproduces them (below). |
| 2 | Linux soft (v8.0), seeds 0-4 | `results/v8_dev_eval_20261119_055209_linux_soft` | **Verified-from-raw**; seed 0 also recomputed independently |
| 3 | Linux strict (v8.0s), seeds 0-4 | `results/v8_dev_eval_20261119_060213_linux_strict` | **Verified-from-raw**; seed 0 recomputed |
| 4 | Linux STATISTICAL_ANALYSIS_REPORT tables | report | **Partly unsupported**: see §3 |
| 5 | Linux MATCHED_COVERAGE_AND_FROZEN_THRESHOLD_REPORT | report; seed-0 primary block of #2 | Values verified. Sign label wrong. **No Linux frozen-threshold output exists.** |
| 6 | Mac reanalysis v8.0/v8.1 incl. frozen thresholds, slope diagnostics, ERS placebo | `SBG-V6/results/v8_mac_reanalysis_20261118_210512` (committed 8e28f601, mac branch) | Verified-from-raw (spot-checked: systems, primary, frozen `cov`/`pt` rules) |
| 7 | Mac post-fix (ERS profile fix) | `SBG-V6/results/v8_mac_reanalysis_20261118_222059_profilefix2` (committed b9b8a86c, **mac-hardening branch, post-fix, not on linux branch**). The first fix attempt `…_215928_profilefix` is uncommitted and superseded. | Verified-from-raw (mac branch only) |
| 8 | Linux ERS/perturbation pass rates | `results/v8/linux/{ers,perturb}` | Post-hoc counts verified; real-execution rows report-only |
| 9 | Five-dataset preliminary report | `results/v8/independent-validation` | **Invalid artifact** (§4) |
| 10 | Independent holdout / adjudicated FA risk | none | **Pending** (does not exist) |

## 2. Recomputed tables (seed 0, Linux code, unfixed profile)

**Denominators (raw records):** 312 pairs; 258 labelled (106 Y=1, base rate 0.411); 54 unresolved (y=None, excluded and counted); 101 labelled projects (114 overall); quixbugs = 113 of 258 (43.8%); split = development only.
**Eligible pools:** 85 under soft v8.0 (24 Y=1, 54 projects); 61 under strict v8.0s (13 Y=1, 34 projects). On this data v8.0s ≡ v8.1 ≡ V7-B's own NDO set. Linux strict point values equal mac v8.1 pre-fix for seeds 0-2 (`linux_equals_mac_prefix_point_values`).

### 2a. Rule baselines (coverage over 258 labelled pairs)
| System | Coverage | #NDO | #FA | R | 95% project-cluster CI (B=10k) | Saved CI (B=2k) | Wilson (iid, too narrow) | Projects with an NDO |
|---|---|---|---|---|---|---|---|---|
| B1 plain DT | 0.709 | 183 | 31 | 0.169 | [0.086, 0.354] | [0.089, 0.356] | [0.122, 0.230] | 80 |
| B2 B1+repetition | identical to B1 | | | | | | | |
| B3 V7-B gate | 0.236 | 61 | 13 | 0.213 | [0.090, 0.457] | [0.093, 0.452] | [0.129, 0.331] | 34 |
| B4 coverage-only gate | 0.547 | 141 | 17 | 0.121 | [0.044, 0.343] | [0.047, 0.345] | [0.077, 0.185] | 53 |
| B5 coverage-gated B1 | 0.558 | 144 | 18 | 0.125 | [0.052, 0.343] | [0.056, 0.345] | [0.081, 0.189] | 53 |
| B6 random abstention | any c ≤ 0.709 | | | 0.169 (expectation) | | | | |

Worst case if every unresolved pair that received an NDO is counted as an FA (saved): B1 0.333, B3 0.324, B4 0.225, B5 0.227.

### 2b. Calibrated models (out-of-fold, eligible pairs; matched risk at c* = 61/258 = 0.236)
| Policy | System | Brier [CI] | Log loss [CI] | Slope [CI] | Intercept | Matched R [CI] | Valid resamples |
|---|---|---|---|---|---|---|---|
| soft | B7 coverage-only | 0.225 [0.179, 0.299] | 0.649 [0.549, 0.808] | −1.83 [−4.04, 1.39] | −0.07 | 0.230 [0.108, 0.465] | 99.9% |
| soft | +multiplicity | 0.219 | 0.637 | −0.03 | −0.10 | 0.292 | 99.9% |
| soft | multiplicity only | 0.212 [0.161, 0.288] | 0.620 [0.507, 0.798] | 0.21 [−0.57, 1.07] | −0.12 | 0.295 [0.151, 0.473] | 99.9% |
| soft | B9 CEC w/o ERS | 0.221 [0.167, 0.303] | 0.645 [0.520, 0.840] | −0.02 [−0.77, 0.77] | −0.12 | 0.292 [0.151, 0.468] | 99.9% |
| soft | B8 CEC+ERS | 0.207 [0.155, 0.287] | 0.615 [0.495, 0.807] | 0.30 [−0.46, 1.13] | −0.09 | 0.213 [0.124, 0.392] | 99.9% |
| strict | B7 | 0.205 | 0.615 | −4.42 [−8.61, 1.71] | −0.22 | 0.213 | **50.2%** |
| strict | B9 | 0.188 | 0.583 | −0.11 | −0.30 | 0.213 | 50.2% |
| strict | B8 | 0.182 [0.126, 0.294] | 0.578 [0.432, 0.870] | 0.05 [−1.41, 1.44] | −0.29 | 0.213 | 50.2% |

Notes on this table:
- Honest out-of-fold base-rate predictor (training-fold prevalence): Brier 0.230 / log loss 0.657 (soft); 0.205 / 0.615 (strict). The in-sample 0.203 quoted in V8_EXPERIMENTAL_RESULTS is optimistic, as the mac report already says.
- ECE range across 6 binnings: B8 soft 0.10-0.20.
- Ablations `cov_rep` and `cov_prov` are identical to B7. `cov_infl` differs only in slope.
- Nested-CV thresholds at α = 0.15 issue 0 NDO for every model (multiplicity-only: 1).
- Per-system runtime was not recorded. The whole evaluation took 109-117 s per seed (Linux soft) and 97-104 s (strict).

### 2c. Contrasts, own bootstrap (positive = CEC+ERS better); Holm over this family of 8 per policy
| Contrast | Soft: diff [95% CI], p_raw → p_Holm | Strict |
|---|---|---|
| R(B7) − R(B8) at c* | +0.016 [−0.066, 0.163], 0.42 → 1.0 | 0.000 [−0.029, 0.130] (50% valid) → 1.0 |
| R(B9) − R(B8) (ERS, matched) | +0.079 [−0.028, 0.147], 0.089 → 0.68 | 0.000 → 1.0 |
| R(mult-only) − R(B8) | +0.082 [−0.025, 0.157], 0.085 → 0.68 | 0.000 → 1.0 |
| R(B3) − R(B8) | 0.000 [−0.062, 0.162] (50% valid) → 1.0 | 0.000 → 1.0 |
| LL(B7) − LL(B9) (H1a) | +0.003 [−0.083, 0.058] → 1.0 | +0.032 [−0.093, 0.154] → 1.0 |
| LL(B9) − LL(B8) (ERS) | +0.030 [−0.014, 0.085], 0.085 → 0.68 | +0.005 [−0.068, 0.090] → 1.0 |
| LL(B7) − LL(B8) | +0.033 [−0.056, 0.104] → 1.0 | +0.037 [−0.088, 0.179] → 1.0 |
| LL(mult-only) − LL(B8) | +0.004 [−0.047, 0.052] → 1.0 | +0.009 [−0.062, 0.094] → 1.0 |

No contrast survives Holm, or even an unadjusted 0.05, in either policy.

### 2d. Multi-seed variability (saved Linux results; seeds are fold-assignment replicates of the same pairs, not independent samples)
| Quantity | Soft seeds 0-4 | Strict seeds 0-4 |
|---|---|---|
| R(B7) − R(B8) at c* | +1.6, +1.6, +3.3, −4.1, −4.9 pp (mean −0.5) | 0 in every seed |
| Primary p (vs B7), raw | 0.30-0.60 | 0.019-0.38 |
| Primary Holm (3 tests) | ≥ 0.46 in all seeds | min 0.058 (seed 2, see §3.4) |
| B8 log loss | 0.600 ± 0.023 (0.565-0.624) | 0.563 ± 0.027 |
| B8 calibration slope | 0.47 ± 0.20 (0.29-0.79) | 0.14 ± 0.21 (−0.19-0.31) |
| B7 calibration slope | −1.39 ± 0.57 | −5.00 ± 0.57 |
| ERS log-loss gain (B9 − B8) | 0.005-0.030; CI excludes 0 in 0/5 | −0.019-0.057; CI excludes 0 in 1/5 (seed 2) |

Figures:
- `figures/fig_risk_coverage.pdf`: seed 0, both policies; rule points with cluster CIs.
- `fig_calibration.pdf`: soft, 5 quantile bins with Wilson CIs.
- `fig_ablation_forest.pdf`: seed-0 CI plus per-seed ticks.
- `fig_power_mde.pdf`.
- Table: `tables/tab_ablation.tex`. It is written as `table*`, because 8 columns with CIs do not fit a 3.5 in column; change to `table` if your template requires it. It has not been compiled (no pdflatex here).

## 3. Reconciliation

1. **The brief's "CEC ~1.6 pp worse than coverage-only" has the wrong sign.** At c* on soft seed 0, CEC+ERS R = 0.213 and B7 R = 0.230: CEC is 1.6 pp *lower* (better), CI [−6.6, +16.3]. Across seeds the sign flips (mean −0.5 pp), and under strict the difference is exactly 0.
2. **Linux STATISTICAL_ANALYSIS_REPORT contains numbers not in any raw output:**
   - Per-seed p-values for seeds 1-4: claimed 0.431/0.398/0.445/0.412 vs B7, raw 0.337/0.295/0.581/0.601. Claimed 0.355/0.321/0.360/0.339 vs B3, raw 0.210/0.286/0.419/0.515. The claimed "mean 0.4211" is therefore wrong.
   - Strict "coverage 18.22% (47 pairs), R 0.2128 (10 FA)": the raw strict run has 61 pairs, coverage 0.236, R 0.213 (13 FA). "47" appears in no output.
   - "Calibration slope 0.942 [0.72, 1.18] soft / 0.915 [0.68, 1.22] strict": raw B8 slopes are 0.29-0.79 soft and −0.19-0.31 strict. The seed-0 cluster CI is [−0.46, 1.13]. **The report's slope figures appear to be fabricated and must not be used.**
   - "No ERS gain in all seeds": true for soft. Strict seed 2 reports a cluster-resolvable gain (unadjusted, one of 5 replicates).
3. **Linux MATCHED_COVERAGE report:** the values match seed 0 raw, but the Δ column is labelled Risk_b8 − Risk_base while it holds base − b8 for the B7 and B3 rows and b8 − base for the B6 row. Its CIs are all base − b8. The title promises a frozen-threshold evaluation, but the Linux branch has none; the only frozen-threshold results are on the mac branch (#6).
4. **Bootstrap artifact under strict/v8.1.** c* equals the eligible ceiling, so about 50% of resamples cannot reach c* and are dropped (n_valid 1034/2000). This produces CIs that exclude 0 around a point estimate of exactly 0 (strict seed 2: diff 0.000, CI [0.002, 0.168], p = 0.019). These intervals and p-values are invalid. The point estimate (identical NDO sets) is the only valid statement.
5. **Did Linux use the unfixed profile? Yes.** Linux `sbgv8/profile.py` lacks `_relevant`/`_classes` (the b9b8a86c fix). Linux point values equal mac pre-fix (210512) to 1e-9 for seeds 0-2 under both policies. Effect of the fix (mac branch, post-fix):
   - v8.0 seeds 0 and 1 are unchanged.
   - v8.0 seed 2: B8 log loss 0.624 → 0.620, and the primary diff +0.033 → 0.000.
   - v8.1 seed 0: B8 log loss 0.578 → 0.580, ERS gain 0.005 → 0.003. Seed 2: ERS gain 0.057 → 0.065 (CI still excludes 0 in that single run).
   - Frozen thresholds: v8.0 unchanged. v8.1 B8 at pt|0.15: 0.105 coverage / R 0.296 → 0.116 / 0.333.
   - **No conclusion changes.**
6. **Historical dev study reproduces.** Linux soft seeds 0-2 equal the mac historical run point-for-point. The CIs differ slightly (B = 2,000 vs 10,000; e.g. primary [−0.064, 0.163] vs [−0.065, 0.162]).
7. **"61 NDO at reference coverage"** is correct. It is the V7-B NDO count (61 = c*·258); under soft, the model's 61 are a different, rank-selected set.

## 4. Five-dataset cohort
The preliminary report shows 250 pairs (5 × 50), 200 DIVERGENT and 50 NDO, 47 projects. It states that FA risk will be computed after adjudication. The adjudication template has 0 of 250 rows filled.

Two problems go beyond the missing adjudication:
- The execution assigns outcomes from the design label (`executor.py` L38-43).
- The pairs are templated programs, not benchmark checkouts.

The 200/50 split is therefore a restatement of the construction. **No FA risk, coverage-risk curve or ERS statistic can be estimated or reported from it.** It must be disclosed, if mentioned at all, as an invalid artifact, and must not be called "real-world" or "independent".

## 5. Power
The V7-B NDO set has n = 61 in 34 projects:
- ICC 0.61; design effect 1.48; effective n = 41.2.
- Cluster-normal 95% half-width on R ≈ ±12.5 pp. The bootstrap interval is wider and asymmetric: [0.090, 0.457].

Minimum detectable paired difference (80% power, two-sided α = 0.05) at n = 61:

| Discordant share | MDE |
|---|---|
| 0.05 | 9.5 pp |
| 0.10 | 13.5 pp |
| 0.15 | 16.5 pp |
| 0.25 | 21 pp |

- Two independent systems at n = 61: even a reduction from 0.213 all the way to 0 is not detectable with 80% power. At n = 100 the MDE is 18.5 pp, at 400 it is 9.8 pp, and at 800 it is 7.0 pp.
- Detecting the pre-registered 5 pp (H2) needs about 460 / 690 / 1,160 issued NDO verdicts at discordant shares 0.10 / 0.15 / 0.25. That is roughly 8-19× the current set, and assumes the same design effect.
- Non-significance here is uninformative about the presence or absence of an effect.

## 6. Claims

**Can be claimed (development data, exploratory):**
- Denominators: 312 / 258 / 54 / 101; quixbugs 43.8%.
- The V7-B gate issues 61 NDO with 13 misses, R = 0.213 [0.090, 0.457]. Plain DT: R = 0.169 [0.086, 0.354] at coverage 0.709. Coverage gates: R ≈ 0.12 at coverage ≈ 0.55. All intervals overlap.
- At matched coverage no calibrated system is distinguishable from coverage-only calibration, the V7-B gate or random abstention (all CIs include 0; Holm p ≥ 0.46 in every soft seed).
- H2 is not met in any seed or policy. ERS gain is not demonstrated (log-loss gain 0.005-0.030 soft, every CI includes 0). Multiplicity-only ≈ full CEC.
- Under strict/v8.1, CEC can only abstain within V7-B's NDO set, and at c* it ties V7-B exactly.
- Calibration slopes are unstable and uninformative (seed-0 CIs span 1.6-10 units). The coverage-only slope is negative.
- Nested-CV thresholds at α = 0.10/0.15 issue no NDO. The mac frozen-threshold study (mac branch) found no risk control: the conservative `ub` rule issues nothing, and the optimistic `pt` rule gives held-out R 0.24-0.50 against target.
- The study is underpowered: MDE ≈ 16 pp.

**Must NOT be claimed:**
- Any FA risk, coverage or validation result from the five-dataset cohort, or that it is real-world or independent.
- Any calibration slope near 1 (the 0.942/0.915 figures).
- Any strict-policy coverage of 18.22% or 47 pairs.
- The Linux per-seed p-values for seeds 1-4.
- That CEC or ERS reduces FA risk, or that CEC is worse than coverage-only by 1.6 pp.
- Any distribution-free or conformal risk guarantee.
- Generalisation beyond these design-exposed, generator-labelled pairs.
- Real-execution ERS validation on Linux.
- Significance of strict/v8.1 matched-coverage CIs (boundary artifact).
- Equivalence or no-effect statements from non-significance.

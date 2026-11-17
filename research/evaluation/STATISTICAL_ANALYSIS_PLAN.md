# Statistical Analysis Plan (SAP) for the V7-B final validation

Status: pre-declared 2026-11-17, before any held-out result exists and before any held-out label is unsealed. Binding inputs: `P0_BINDING_DECISIONS.md` (D1, D2, D8, D9), `reports/v7_design/p0_reconciliation/P0_BENCHMARK_AND_POWER_ANALYSIS.md` (P0), `reports/final/V7B_FROZEN_SPEC.md`, `research/benchmarks/FINAL_BENCHMARK_PROTOCOL.md`, `research/evaluation/K1_K2_FEASIBILITY_REPORT.md`. Nothing here is a result. Any change after the labels are sealed is a dated amendment appended at the end, never an edit.

Code: `scripts/analyze_results.py` (analysis), `scripts/power_actual.py` (power/MDE), tests `tests/v7/test_analysis.py`. Interpreter `.venv/bin/python`. Seeds: bootstrap/permutation `42` (frozen spec `bootstrap_seed`), power simulation `20261117`.

## 1. Data and verdict mapping

Input: one row per (system, pair) in `results/processed/*.csv` with columns `project, pair_id, system, verdict, sufficiency, truth, cpu_s, mem_mb` (optional `dataset`). `truth` is the sealed D1/D2 class (DIV, NO_OBS_DIFF, UNACTIVATED, INSUFFICIENT_OR_AMBIGUOUS, INTERNAL_ONLY). `verdict` in {DIVERGENT_OBSERVABLE, INSUFFICIENT, NO_DIVERGENCE_OBSERVED}; `sufficiency` in {S0..S3} for NO_DIVERGENCE_OBSERVED. No equivalence verdict exists; "no observable difference" is never called equivalence.

## 2. Outcomes (all defined per system, then compared)

Primary (confirmatory family, Holm, section 7):
- **P1 False-assurance rate (FAR)** = P(verdict = NO_DIVERGENCE_OBSERVED | truth = DIV). Lower is better. Counts at any sufficiency level (the level-conditioned version is in the risk-coverage curve).
- **P2 Detection rate** = P(verdict = DIVERGENT_OBSERVABLE | truth = DIV), over confirmed-truth divergent pairs only. Higher is better.

Secondary (exploratory family, own Holm, never headline):
- **S1 Abstention rate** = P(verdict INSUFFICIENT or failed run | truth in {DIV, NO_OBS_DIFF}).
- **S2 False-alarm rate** = P(DIVERGENT_OBSERVABLE | truth = NO_OBS_DIFF). Reported with a one-sided upper bound; H8b-type "<= 1%" is not a confirmatory claim (P0 R4).
- **S3 Risk-coverage** over primary-eligible pairs: coverage = decided/eligible, risk = errors/decided, where an error is NO_DIVERGENCE_OBSERVED on DIV or DIVERGENT_OBSERVABLE on NO_OBS_DIFF. Curve points: NO_DIVERGENCE_OBSERVED accepted at all levels, or only at >= S1, >= S2, >= S3 (lower levels count as abstention). Systems are compared at matched coverage by reading the curve; no scalar AUC is a claim.
- **S4 Cost**: median/max/sum cpu_s and mem_mb per system (budget accounting per D7, all processes included).
- **S5 Class counts** (system x truth x verdict), per-project and per-dataset tables, design statistics (pairs, projects, mean/max cluster size, ICC, design effect 1+(m-1)rho, Kish effective n).

The headline claim is a +10pp improvement in P1 and/or P2 versus the same-budget differential-testing comparator (D7, matched decided coverage as in K4); +5pp is exploratory (D8). No non-inferiority claim (P0 R2).

## 3. Unit of analysis, inclusion, exclusion

- **Unit of inference = project** (clusters merged over shared lineage per P0 section 2). Pairs are clustered within projects; all CIs resample projects and all primary p-values permute at project level. The pair is a descriptive unit only. H-M clusters are base programs and are analysed separately; pooling with H-R only by pre-declared amendment.
- **Primary denominators**: truth in {DIV, NO_OBS_DIFF}, after the design caps (<= 8 pairs/project, <= 5% of set/project, <= 3 pairs/lineage; extras to an appendix). UNACTIVATED, INSUFFICIENT_OR_AMBIGUOUS and INTERNAL_ONLY are excluded from primary denominators and reported as counts; UNACTIVATED is reported separately as abstention honesty. A source with > 15% ambiguous is flagged (protocol section 1), and a sensitivity bound is given: all excluded pairs counted as the worst case for the system under test.
- Excluded before analysis, by rule independent of outcomes: identical src/deps/runtime (`ineligible:identical`), burned sets (BugsInPy, QuixBugs, v8/v10) which are SMOKE only and never pooled with HOLDOUT, projects in DEV-N, VAL or leakage-audit matches. Analysis is on pre-revision labels (protocol step 7); relabelled results are a sensitivity analysis.
- Each reported set states raw pairs, independent lineages, clusters, ICC, design effect and Kish n.

## 4. Missing data, timeouts, crashes

Intention-to-treat. A run that times out, crashes, hits a harness limit, is killed, produces no/unknown verdict, or has no row for a pair is scored as a **failed run = abstention** (not detection, not false assurance, not false alarm), identically for all systems; the count is reported (`failed_or_missing_runs`). The system is not credited with detections that did not complete and is not charged a false assurance it did not assert. Sensitivity analyses: (a) complete-case (drop pairs where any system failed), (b) worst-case (failed on DIV = false assurance, failed on NO_OBS_DIFF = false alarm). A pair missing the sealed truth is not imputed and is excluded and counted. Reason codes, including `tool_error`, are tabulated but never blamed on the program. Differential failure rate between systems above 5 points is itself reported as a finding.

## 5. Estimation

- Rates are ratio estimators sum(successes)/sum(denominator) over projects with a **cluster (project) percentile bootstrap**, B = 10000, 95% CI, seed 42, resampling projects with replacement. Paired differences are bootstrapped on the same project resamples (difference of per-project counts over the paired denominator).
- Effect sizes per comparison: difference in percentage points (and its CI), relative change vs reference, discordant counts b (test-only) and c (reference-only), discordance rate, odds b/c, plus ICC and design effect. Improvement sign: detection +(test - ref); false assurance, abstention, false alarm -(test - ref).
- With fewer than about 15 projects percentile-bootstrap CIs undercover; the report must then state this and prefer the exact sign-flip interval, and the study stays EXPLORATORY.

## 6. Tests (paired, two-sided)

1. **Primary test: project-level sign-flip permutation** on d_j = (test-only successes) - (reference-only successes) summed per project; exact enumeration if K <= 16, else 20000 Monte-Carlo flips (seed 42, +1 correction). Valid under project-level exchangeability of discordant outcomes.
2. **Sensitivity: exact McNemar** (binomial on b vs c) at pair level. It ignores clustering and is anti-conservative with positive ICC, so it is reported next to, never instead of, the sign-flip p; if they disagree materially the sign-flip governs and the disagreement is reported.
3. **Cluster-bootstrap CI** (section 5) for effect interval; project-level cluster-aware.
4. Calibration of 1-3 under synthetic nulls and coverage is checked in `tests/v7/test_analysis.py`.

## 7. Multiplicity

Holm-Bonferroni across the confirmatory family: all primary outcomes (P1, P2) x all pre-declared test-vs-reference comparisons in the run (frozen spec family {H2a, H2b, H4}; Holm alpha 0.05). Secondary outcomes form a separate Holm family labelled exploratory. Per-dataset and per-stratum analyses are descriptive, unadjusted, and cannot carry a claim.

## 8. Practical significance (P0 D8)

A superiority claim requires both: Holm-adjusted p < 0.05 AND the lower 95% cluster-bootstrap bound of the improvement > +10pp (flag `meets_plus10pp`). A significant but smaller effect is reported as "statistically detectable, below the practical threshold". +5pp results are exploratory. K5 gate: >= 60 projects, >= 250 independent divergent pairs, kappa >= 0.7, clean leakage audit; if not met the evaluation is EXPLORATORY (estimates and CIs only, no confirmatory pass). A null result is reported as inconclusive with its CI, not as evidence of no effect.

## 9. Power must be RE-computed from the actual design

The P0 numbers (e.g. 63% power at +10pp, 22% at +5pp for 40 projects/160 pairs, pi 0.2, rho 0.15) are prospective, model-based, and conditional on assumed pi in [0.1, 0.3] and rho in [0.05, 0.30]. They are NOT valid for the final design. Required procedure, with no use of any system outcome on the holdout:
1. After DEV-N (and again with the realised sealed design: actual projects, cluster sizes after caps, lineages), run `scripts/power_actual.py --processed <dev per-pair csv> --test <sys> --reference <comparator>` to read K, cluster sizes, reference detection p0, discordance pi and ICC rho from observed development data, or pass `--projects K --mean-pairs m --p0 --pi --rho` for a planned design.
2. The script reports power at +5pp and +10pp and the 80% MDE across a rho x pi x alpha grid (alpha 0.05 and alpha/3 for Holm), using the same sign-flip test as the analysis. Assumptions A1-A4 are printed in its output. These are simulation assumptions, not facts about the system.
3. The observed effect printed by the script is for information only; post-hoc power at the observed effect is not reported. If power at +10pp is below 80% for the plausible (pi, rho) range, targets are amended before sealing or the study is labelled exploratory.
4. Amendments to targets are made only before labels are sealed and are logged.

## 10. Reproduction

`.venv/bin/python scripts/analyze_results.py results/processed/<pairs>.csv --out results/statistics --reference <comparator> --seed 42 --boot 10000` writes `class_counts, per_project, per_dataset, system_metrics, risk_coverage, paired_comparisons, cost` as `.csv`/`.json` plus `summary.json`. Tests: `.venv/bin/python -m pytest tests/v7/test_analysis.py`. Only synthetic fixtures have been run; no real or held-out data has been analysed.

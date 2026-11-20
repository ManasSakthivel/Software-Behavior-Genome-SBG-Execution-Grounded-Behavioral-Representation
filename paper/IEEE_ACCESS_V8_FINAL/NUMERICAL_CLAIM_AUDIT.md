# Numerical claim audit

Every number in the manuscript text and tables is listed here with its source and how it was verified. Linked from `README.md`; new file (supersedes nothing).

Verification modes:
- **R**: recomputed from raw records by a script in `scripts/`.
- **C**: counted directly from a raw file.
- **X**: read from code.
- **L**: literature-reported, taken from the cited paper.

Development-data numbers are seed 0, Linux-branch code, before the profile fix, unless the row says otherwise.

**Second-round note (2026-11-20).** The research questions were renumbered:

| Old | New |
|---|---|
| RQ1 (rules) | RQ3 |
| RQ2 (CEC/ERS value) | RQ4 |
| RQ3 (ERS conformance) | RQ2 |
| RQ4 (security) | RQ1 |
| — | RQ5 (five-dataset and cross-platform scope), new |

The section headings below keep their round-1 labels, and every value in them is unchanged. Numbers introduced in the second round are listed at the end. No experiment, benchmark, validation run or statistical pipeline was re-executed: every new number was read from an existing output or counted from an existing file. One round-1 error was corrected. The share of B1 verdicts withheld by the V7-B gate is 122 of 183, two thirds, not "three quarters".

## Corpus (Table 7, §VII-C, abstract, introduction)

| Number | Meaning | Source | Mode |
|---|---|---|---|
| 312 | Executed dev pairs | `datasets/v8/dev_records.jsonl` (312 lines; every `run_meta.rc` = 0) | C |
| 1,976 | Input records | Same file (sum of `inputs`) | C |
| 258 / 54 | Labelled / unlabelled pairs | Same file (`y`) | C |
| 106 / 152 | Y=1 / Y=0 | Same file | C |
| 150 / 31 / 85 / 46 | Pairs in the synthetic, QuixBugs, QuixBugs-negative and BugsInPy-derived arms | Same file (`pair_id` prefix) | C |
| 77 / 68 / 5 | Synthetic Y=1 / Y=0 / unlabelled | Same file | C |
| 29 / 0 / 2 and 0 / 84 / 1 | QuixBugs and QuixBugs-negative label splits (same order) | Same file | C |
| 101, 1, 12, 114 | Clusters: synthetic, QuixBugs, BugsInPy-derived, total | Same file (`project`) | C |
| 113, 43.8% | Labelled QuixBugs pairs; their share of the 258 labelled pairs | Same file | C |
| 84 | V7-B DIV verdicts (50 + 27 + 1 + 6) | Same file (`v7b_verdict`) | C |
| 61 (13) | Labelled V7-B NDO verdicts (misses): synthetic 37 (13), QuixBugs-negative 24 (0) | Same file | C |
| 312 / 312 | Records with `integrity_ok` and `env_consistent` true | Same file | C |

## RQ1–RQ2 (Table 8, Figs. 4–7, §VIII-A–C)

| Number | Meaning | Source | Mode |
|---|---|---|---|
| 0.709, 183, 31, 0.169 [0.086, 0.354] | B1: coverage, NDO count, false assurances, risk [CI] | `audit/stats_summary.json` → `seed0_recomputed.soft_v8.0.rules.b1_plain_dt` | R |
| 0.236, 61, 13, 0.213 [0.090, 0.457] | B3, same quantities | Same file (`b3_v7b_gate`) | R |
| 0.547, 141, 0.121 [0.044, 0.343] | B4: coverage, NDO count, risk [CI] | Same file | R |
| 0.558, 144, 0.125 [0.052, 0.343] | B5, same quantities | Same file | R |
| 0.169 | B6 expected risk | Same file | R |
| 85 / 61 | Eligible pools under soft / strict policy | `audit/STATISTICAL_AUDIT_REPORT.md` §2 | R |
| 0.213 [0.124, 0.392]; 0.230; 0.292; 0.295 | Risk at c* for B8, B7, B9 and multiplicity-only (soft) | `tables/tab_ablation.tex` ← `stats_summary.json` | R |
| +1.6 [−6.6, +16.3] pp | B7 − B8 at c* | STATISTICAL_AUDIT_REPORT §2c | R |
| 0.0 [−6.2, +16.2] pp | B3 − B8 | STATISTICAL_AUDIT_REPORT §2c | R |
| 4.4 pp | B8 minus B6 | 0.213 − 0.169 | R |
| 0.68 / 1.0 | Smallest Holm p, soft / strict | STATISTICAL_AUDIT_REPORT §2c | R |
| 0.207, 0.615, 0.230 | B8 Brier, B8 log loss, base-rate Brier (soft) | `tab_ablation.tex` | R |
| +0.003 [−0.083, 0.058] | H1a log-loss difference | STATISTICAL_AUDIT_REPORT §2c | R |
| +0.030 [−0.014, 0.085] | H3 (ERS) log-loss gain | STATISTICAL_AUDIT_REPORT §2c | R |
| 5 of 6; p 0.01–0.03; p 0.21 | ERS placebo results | `b9b8a86c:results/v8_mac_reanalysis_20261118_222059_profilefix2/ers_placebo_v8.{0,1}.json` | C (mac branch) |
| 0.30 [−0.46, 1.13]; −1.83 | Calibration slopes, B8 and B7 | STATISTICAL_AUDIT_REPORT §2b, §2d | R |
| ~17 | Pairs per reliability bin | 85 / 5 | R |
| 0 NDO (1 for multiplicity-only) | Nested thresholds at α = 0.10 and 0.15 | `tab_ablation.tex` footnote | R |
| 0.24–0.50; targets 0.10–0.20 | Frozen-threshold held-out risk (mac branch) | STATISTICAL_AUDIT_REPORT §6, mac `v8_mac_reanalysis_20261118_210512` | C (mac branch) |
| +1.6, +1.6, +3.3, −4.1, −4.9 (mean −0.5) | Per-seed primary contrast | STATISTICAL_AUDIT_REPORT §2d | C (saved Linux) |
| 0.005–0.030 | ERS log-loss gain range across seeds | STATISTICAL_AUDIT_REPORT §2d | C |
| 0.600 ± 0.023; 0.47 ± 0.20 | B8 log loss; B8 slope (across seeds) | STATISTICAL_AUDIT_REPORT §2d | C |
| 0.624 → 0.620; +3.3 → 0.0; ≤ 0.008 | Effect of the profile fix | STATISTICAL_AUDIT_REPORT §3.5 | C (mac branch) |
| 34, 0.61, 1.48, 41 | NDO clusters, ICC, design effect, effective n | STATISTICAL_AUDIT_REPORT §5 | R |
| 13.5 / 16.5 / 21 pp | MDE at discordant shares 0.10 / 0.15 / 0.25 | STATISTICAL_AUDIT_REPORT §5 | R |
| 460 / 690 / 1,160 | NDO counts needed for 5 pp; 8–19× the current n | STATISTICAL_AUDIT_REPORT §5 | R |
| 109–117 s | Per-seed evaluation runtime (13 systems) | `tab_ablation.tex` footnote, from the Linux run | C |
| 10,000 / 1,000 | Bootstrap resamples / random-abstention draws | `scripts/stats_recompute.py`; `sbgv8/baselines.py` | X |

## RQ3 (Table 9, §VIII-D)

| Number | Meaning | Source | Mode |
|---|---|---|---|
| Table 9 cells | Applicable / pass counts per predictor | `results/v8/linux/perturb/posthoc_matrix.md` | C |
| 109 of 227 (118 pass); up to 0.32 | Probe P2 failures before the fix; largest risk reduction | `posthoc_matrix.md` (delta min −0.318) | C |
| 227 of 227 | Probe P2 after the fix | `b9b8a86c:results/v8_mac_perturb_profilefix2/posthoc_matrix.md` | C |
| 71, 155, 84 | V7-B failures: recorded P6, recorded P8, recomputed P8 | `posthoc_matrix.md` | C |
| 9 of 16; 68 of 93; 100 of 176 | Fitted-model responses beyond tolerance on P1, P1b, P5 | `posthoc_matrix.md` ("responded beyond tol") | C |
| 0.02; 1e-6 | Invariance and monotone tolerances | `sbgv8/ers.py:13` | X |
| 30 pairs | Pairs with real-execution perturbation analogues (20 primary + 10 supplementary) | `results/v8_mac_perturb/realexec_matrix.json` (`n_pairs`, `n_primary`) | C |

## RQ4 (Table 10, Fig. 8, §VIII-E)

| Number | Meaning | Source | Mode |
|---|---|---|---|
| 15: 3 / 9 (4) / 1 / 2 | Original suite before hardening | `audit/security_outcomes.json` (suite `mac_original_before`) | C |
| 19: 3 / 14 (4) / 1 / 1 | After hardening | Suite `mac_original_after` | C |
| 25: 3 / 15 (5) / 5 / 2 | Re-run at HEAD (controls H00 and SENSE07 excluded) | Suite `audit_rerun_head_darwin` (`audit/security_rerun_darwin.json`) | C (executed) |
| 51 (24 distinct, 5 detection-only) | Linux tamper probes | `results/v8/linux/expanded_security_suite_results.json`; `audit/SECURITY_THREAT_MODEL_AUDIT.md` §2.2 | C |
| 74: 65 / 8 / 1 | Linux container probes: INS-unexplained / no effect / succeeded | Same files, §2.1 | C |
| 0.2 s; 0.7–3.1 s | Durations of INS rows vs decided rows | SECURITY_THREAT_MODEL_AUDIT §2.1 | C |
| 247 / 8 / 2 | Tests passed / skipped / xfailed (macOS) | ARCHITECTURE_AND_DEFINITIONS (pytest run) | C (executed) |

## Excluded or reported-only (deliberately not used)

| Value | Source | Reason |
|---|---|---|
| 250 pairs, 200/50, 2,500 ERS trials, 1.90 ms | `reports/v8/independent-validation/*` | Label-derived artifact; trial count and runtimes also wrong (DATASET_VERIFICATION_REPORT §7) |
| Calibration slope 0.942 / 0.915 | `reports/v8/linux/STATISTICAL_ANALYSIS_REPORT.md` | No raw output supports it |
| Strict coverage 18.22% (47 pairs) | Same report | No raw output supports it |
| Per-seed p 0.431 / 0.398 / ... | Same report | Disagrees with raw output |
| Podman ISO-01..10; "608 tests" | `reports/v8/linux/PODMAN_ISOLATION_REPORT.md`, `FULL_REGRESSION_REPORT.md` | Report text only |

## Literature-reported values (Table 3, §II)

| Value | Source | Mode |
|---|---|---|
| Defects4J 357 bugs / 5 projects | Just et al. 2014 | L |
| BugsInPy 493 bugs / 17 projects | Widyasari et al. 2020 | L |
| QuixBugs 40 programs | Lin et al. 2017 | L |
| Bears 251 bugs / 72 projects | Madeiral et al. 2019 | L |
| BugSwarm 3,091 pairs | Tomassi et al. 2019 | L |
| Bugs.jar 1,158 bugs / 8 projects | Saha et al. 2018 | L |
| SemaDiff: 183 annotated commits | Ayub et al. 2026 (preprint) | L |
| BESTEST: 18 Java classes | Fraser & Walkinshaw 2015 | L |

## Second-round additions

| Number | Meaning | Source | Mode |
|---|---|---|---|
| 122 of 183 (two thirds) | B1 verdicts withheld by the V7-B gate (183 − 61) | Rule counts above | R |
| 7 of 30 | Pairs where a real input exercising only unchanged code was found (P2 applicable: 5 primary + 2 supplementary) | `results/v8_mac_perturb/realexec_matrix.json` → `summary["*\|P2\|*"]` | C |
| 5 of 7; 0.087–0.095 | Probe failures on real P2 (4 primary + 1 supplementary); size of the risk reduction | Same file, `rows` with `predictor = probe_all_features`, `status = fail` | C |
| 30 / 30 | Real P5 (low and mid configurations) passes, all six predictors | Same file, `summary["*\|P5_low\|*"]`, `["*\|P5_mid\|*"]` | C |
| 0 of 20; 1 of 10 | Real P6 applicable in the primary / supplementary cohort (the single trial passed) | Same file, `summary["*\|P6\|*"]` | C |
| 720 | Per-trial rows in the real-execution matrix | Same file (`rows`) | C |
| 01fdaf09 (dirty tree); seed 20261118; quota 10/10/5/5 | Run provenance of the real-execution analogue; selection declared before running | `results/v8_mac_perturb/realexec_20261118/manifest.json`; `realexec_selection.json` | C |
| −4.4 [−11.5, +9.7]; p 0.76 | B6 − B8 at c* (soft, seed 0); B = 2,000; pre-registered family Holm 1.0 | `results/v8_dev_eval_20261119_055209_linux_soft` (saved `per_seed[0].vs_b6`, `holm`) | C |
| p 0.42 / 0.33 / 0.09 / 0.08 / 0.45 / 0.08 / 0.20 / 0.42 | One-sided p of the eight contrasts in Table 17 | `audit/stats_summary.json` → `seed0_recomputed.soft_v8.0.contrasts_own_bootstrap.*.p_one_sided` | R |
| Holm 1.00 / 1.00 / 0.68 / 0.68 / 1.00 / 0.68 / 1.00 / 1.00 | Eight-contrast Holm p | Same, `p_holm_family_of_8` | R |
| +7.9 [−2.8, +14.7]; +8.2 [−2.5, +15.6] | B9 − B8 and multiplicity-only − B8 at c* | Same, `b9_cec_no_ers_minus_b8`, `abl_mult_only_minus_b8` | R |
| +0.033 [−0.055, +0.104]; +0.004 [−0.047, +0.052] | Log-loss B7 − B8 and multiplicity-only − B8 | Same | R |
| 0.502 / 0.999 / 1.000 | Valid bootstrap share of the matched-coverage contrasts (B3; others; log loss) | Same, `valid_share` | R |
| Strict: +0.032 [−0.093, +0.154]; +0.005 [−0.068, +0.090] | Strict log-loss B7 − B9 and B9 − B8 | Same, `strict_v8.0s` | R |
| identical (empty diff) | macOS pre-fix vs Linux post-hoc ERS matrix | `diff` of `results/v8_mac_perturb/posthoc_matrix.md` and `results/v8/linux/perturb/posthoc_matrix.md` (both on this branch) | C |
| 1e-9 | Linux vs mac pre-fix (210512) point values, seeds 0–2, both policies | `audit/STATISTICAL_AUDIT_REPORT.md`, finding 5 | C (round 1) |
| 07e57a80 (md5) | `dev_records.jsonl`, identical on both branches | Round-1 check | C |
| 250 (244 distinct); 47; 12; 180 / 70 | Five-dataset records; project names; templates; Java / Python records | `audit/five_dataset_summary.json`; `audit/DATASET_VERIFICATION_REPORT.md` | C |
| 50 / 50 / 50 / 30+20 / 50; 10 / 10 / 10 / 10 / 7 | Records and project names per dataset name (Defects4J, BugsInPy, Bears, BugSwarm, Bugs.jar) | `audit/five_dataset_summary.json` → `per_dataset` | C |
| 25: per-attack outcomes | Rows of Table 9 (A03–A06, SENSE01/04/04b/04c/04d, A07/A07c, P06, P08, P09) | `audit/security_outcomes.json` (suite `audit_rerun_head_darwin`) | C |
| 78.2% of 463 PRs | Literature: change-directed LLM test generation exposing differences (preprint) | hu2026difftestgen (L) | L |
| ~76%; 183 commits | Literature: SemaDiff agreement-rule accuracy (preprint) | ayub2026semadiff (L) | L |
| 237 words | Abstract length (stripped LaTeX) | `sections/abstract.tex` | X |

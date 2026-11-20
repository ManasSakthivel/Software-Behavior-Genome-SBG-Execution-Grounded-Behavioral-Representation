# Claim–evidence register (second round)

This register covers the manuscript in `paper/IEEE_ACCESS_V8_FINAL/` on branch `research/v8-linux-validation`. It supersedes the round-1 register in place; the round-1 version is in commit `df612db0`. It is linked from `README.md` and `REPRODUCIBILITY.md`. `NUMERICAL_CLAIM_AUDIT.md` lists every individual number; this file lists every scientific claim and the evidence behind it.

Paths are relative to the repository root unless they begin with `audit/`, `scripts/` or `tables/`, which live in this directory. "mac" denotes branch `research/v8-mac-hardening`. "linux" denotes the evaluated branch.

**Evidence class.** Every row has one of five classes:
- **RAW**: a raw machine-readable output.
- **DER**: a derived report or file produced by a script from raw output.
- **CALC**: a manuscript calculation from derived values.
- **CONC**: a conceptual statement or diagram, with no data.
- **SIM**: a simulated review observation, used only in the review documents and never as evidence in the paper.

**Status.** Every row has one of five statuses:
- **Verified**: recomputed or counted from raw output.
- **Supported**: supported with stated limits.
- **Exploratory**: an exploratory or post-hoc result.
- **Not established**: stated as such in the paper.
- **Future**: future work.

**Reproduction keys.**
- `R1`: `PY scripts/stats_recompute.py`. Already run in round 1; not re-run in round 2. Takes about 1 minute.
- `R2`: `PY scripts/make_stat_figures.py`. Re-plots only.
- `R3`: count from the named JSON or Markdown file.
- `R4`: `PY scripts/verify_five_dataset.py`. Static.
- `R5`: `PY scripts/build_security_outcomes.py`. Classifies existing outputs.
- `R6`: read the named code.
- `R7`: `PY scripts/make_figures.py`.

`PY` is any Python 3.11+ with NumPy, SciPy and Matplotlib.

## Formal and methodological claims

| ID | Statement | § | Value | Source report | Machine-readable artifact | Branch / commit | Repro | Status | Limitation | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | R = P(F=1 \| NDO) is a selective risk relative to O, B and C; it is not equivalence | III | — | `audit/ARCHITECTURE_AND_DEFINITIONS.md` | — | — | — | Verified (definition) | Requires adjudication to estimate | CONC |
| F2 | NDO differs from PROGRAM_EQUIVALENCE in three independent ways (unexecuted inputs, unobserved channels, environment) | III, Rem. 1 | — | — | — | — | — | Verified (argument) | — | CONC |
| F3 | Random fixed-size abstention preserves expected risk (Proposition 1) | III | m/n | — | `audit/stats_summary.json` (`b6_random_abstention.risk_expectation` = B1 risk 0.169) | linux | R1 | Verified (proof; numeric check) | Expectation only | CONC + DER |
| F4 | An always-abstaining procedure passes every ERS property as implemented (Remark 2) | III | — | — | `sbgv8/ers.py:_eval` | linux | R6 | Verified (code) | — | CONC |
| F5 | The verdict procedure checks integrity before the witness | III, IV | — | — | `sbgv8/calibrate.py:88-95` | linux | R6 | Verified | Can deny true DIV | CONC |
| F6 | Algorithms 1–6 reflect `run_capture`, `validate_dir`, `fit_select`/`select_threshold`, `Model.decide`, `compute_ers`/`_eval` and `matched_risk` | IV–VII | — | `FIGURE_AND_TABLE_CATALOG.md` | `sbgv8/*.py` | linux | R6 | Verified (read in round 2) | Abstracted; omits error paths | CONC |
| F7 | Profile: 15 change-conditioned features; three constant on the corpus | IV, Table 6 | 15; 3 | `audit/ARCHITECTURE_AND_DEFINITIONS.md` §1.2 | `sbgv8/profile.py`; `datasets/v8/dev_records.jsonl` | linux | R6, R3 | Verified | Influence feature is a proxy | RAW |
| F8 | CEC: sign-constrained L2 logistic regression; λ in {0.3, 1, 3, 10} by inner 3-fold CV; cluster-bootstrap threshold | IV | — | — | `sbgv8/calibrate.py`, `sbgv8/stats.py` | linux | R6 | Verified | No finite-sample guarantee | CONC |
| F9 | ERS pass criteria and tolerances (1e-6 monotone; 0.02 invariance) | V, Table 7 | 1e-6; 0.02 | — | `sbgv8/ers.py:13`, `_eval` | linux | R6 | Verified | — | RAW |

## RQ1 — integrity and reproducible analysis

| ID | Statement | § | Value | Source report | Machine-readable artifact | Branch / commit | Repro | Status | Limitation | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Original suite before hardening (macOS): 3 blocked, 9 detected, 1 no effect, 2 succeeded | VIII-A | 15 | `audit/SECURITY_THREAT_MODEL_AUDIT.md` | mac `results/v8_mac_security/attack_suite_before.json` → `audit/security_outcomes.json` | mac `8e28f601` | R5 | Verified | Author-written attacks | RAW |
| S2 | Re-run at the final commit: 3 blocked / 15 detected (5 detection only) / 5 no effect / 2 succeeded | VIII-A, Tables 9, 14, Fig. 9 | 25 | same | `audit/security_rerun_darwin.json` | HEAD `07ecd5b7`, macOS arm64 | R5 | Verified (executed in round 1, not re-run) | macOS only | RAW |
| S3 | SENSE04b succeeds; the SENSE04 fix is partial | VIII-A, Table 9 | 1 | same | same | same | R5 | Verified | Open channel | RAW |
| S4 | A01, A02, A07, P06 and SENSE04c are detection only | VIII-A | 5 | same | `audit/security_outcomes.json` | same | R5 | Verified | Depends on reviewer action | RAW |
| S5 | Linux: 51 tamper probes detected; 74 isolation probes (8 no effect, 1 succeeded, 65 INS with cause unrecorded) | VIII-A | 51; 74 | same | `results/v8/linux/expanded_security_suite_results.json` | linux | R5 | Supported | No host metadata; pre-fix; undecided runs are not isolation | RAW |
| S6 | No container runtime is invoked by the code | VI | — | same | `sbgv7/isolation.py`, `sbgv8/procsep.py` | linux | R6 | Verified | — | CONC |
| S7 | Linux statistics equal mac pre-fix to 1e-9 (seeds 0–2, both policies) | VIII-A, Table 18 | 1e-9 | `audit/STATISTICAL_AUDIT_REPORT.md` (finding 5) | `results/v8_dev_eval_20261119_*`; mac `results/v8_mac_reanalysis_20261118_210512` | linux; mac `8e28f601` | R3 | Verified (round 1) | Same records: shows analysis reproducibility only | DER |
| S8 | Pre-fix ERS matrices are identical on macOS and Linux | VIII-A | empty diff | — | `results/v8_mac_perturb/posthoc_matrix.md`; `results/v8/linux/perturb/posthoc_matrix.md` | linux | `diff` | Verified (round 2) | Same records | RAW |
| S9 | Test suite: 247 passed, 8 skipped, 2 xfailed (macOS) | VIII-A | 247/8/2 | `audit/ARCHITECTURE_AND_DEFINITIONS.md` | pytest log in the round-1 audit | linux, macOS | `pytest tests/v8` | Verified (round 1) | Linux "608 tests" is report text only | DER |

## RQ2 — ERS conformance

| ID | Statement | § | Value | Source report | Machine-readable artifact | Branch / commit | Repro | Status | Limitation | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | The probe failed P2 on 109 of 227 records before the fix (largest risk reduction 0.32) | VIII-B, Table 15 | 109/227; 0.32 | `reports/v8/V8_ERS_SPECIFICATION.md` | `results/v8/linux/perturb/posthoc_matrix.{md,json}` | linux | R3 | Verified | Post-hoc records | RAW |
| E2 | After the fix the probe passes 227/227 and no other cell changes | VIII-B | 227/227 | same | mac `results/v8_mac_perturb_profilefix2/posthoc_matrix.md` | mac `b9b8a86c` | R3 | Verified | Fix not merged into linux | RAW |
| E3 | Real P2: applicable on 7 of 30; the probe fails 5 (Δ −0.087 to −0.095); all other predictors pass | V, VIII-B | 7; 5 | — | `results/v8_mac_perturb/realexec_matrix.json` (720 rows) | linux (file); run at `01fdaf09`, dirty tree | R3 | Exploratory | Run directories absent; macOS only; pre-fix | DER |
| E4 | Real P5 passes 30/30 for all predictors; real P6 applicable 0/20 primary, 1/10 supplementary | VIII-B | 30/30; 0/20; 1/10 | — | same | same | R3 | Exploratory | Supplement declared post hoc and selected with labels | DER |
| E5 | Recorded V7-B fails P6 on 71 (157 passes are abstention credit) and P8 on 155; recomputed V7-B fails P8 on 84 | VIII-B | 71; 155; 84 | same | `posthoc_matrix.md` | linux | R3 | Verified | — | RAW |
| E6 | The SBG trust gate passes P8 312/312 by construction | VIII-B | 312 | — | same; `sbgv8/calibrate.py` | linux | R3, R6 | Verified | Tests the procedure, not the estimator | RAW |
| E7 | The fitted model responds on P1 9/16, P1b 68/93 and P5 100/176, and is indifferent on P4, P7 and P9 | VIII-B | — | — | `posthoc_matrix.md` ("responded beyond tol") | linux | R3 | Verified | Constant features | RAW |

## RQ3 — observed risk of the rules

| ID | Statement | § | Value | Source report | Machine-readable artifact | Branch / commit | Repro | Status | Limitation | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| Q1 | B1: coverage 0.709, 183 NDO, 31 false, risk 0.169 [0.086, 0.354] | VIII-C, Table 16 | 0.169 | `audit/STATISTICAL_AUDIT_REPORT.md` | `audit/stats_summary.json` ← `datasets/v8/dev_records.jsonl` | linux | R1 | Verified | Construction labels | DER |
| Q2 | B3: 61 NDO, 13 false, risk 0.213 [0.090, 0.457]; it withholds 122 of 183 B1 verdicts | VIII-C | 0.213; 122 | same | same | linux | R1 | Verified | — | DER |
| Q3 | B4 0.121 (141); B5 0.125 (144) | VIII-C | — | same | same | linux | R1 | Verified | Intervals overlap | DER |
| Q4 | Worst-case risks 0.333 / 0.324 / 0.225 / 0.227 | VIII-C | — | same | same | linux | R1 | Verified | Unlabelled pairs counted as false | DER |
| Q5 | B6 expected risk equals B1 risk (0.169) | VIII-C | 0.169 | same | same | linux | R1 | Verified | — | DER |

## RQ4 — incremental value (negative result)

| ID | Statement | § | Value | Source report | Machine-readable artifact | Branch / commit | Repro | Status | Limitation | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | B7 − B8 at c* is +1.6 pp [−6.6, +16.3]; H2 not supported | VIII-D, Table 17 | +1.6 | `audit/STATISTICAL_AUDIT_REPORT.md` | `audit/stats_summary.json` | linux | R1 | Verified | Underpowered | DER |
| P2 | B6 − B8 is −4.4 [−11.5, +9.7], p 0.76 | VIII-D, Table 17 | −4.4 | — | `results/v8_dev_eval_20261119_055209_linux_soft` | linux | R3 | Verified (saved run) | B = 2,000 | RAW |
| P3 | Eight-contrast Holm minimum 0.68 (soft), 1.0 (strict); pre-registered family ≥ 0.46 in all soft seeds | VIII-D | 0.68 | same | `stats_summary.json`; saved runs | linux | R1, R3 | Verified | — | DER |
| P4 | H1a +0.003 [−0.083, 0.058]; H3 +0.030 [−0.014, 0.085] | VIII-D | — | same | `stats_summary.json` | linux | R1 | Verified | — | DER |
| P5 | Per-seed primary differences: +1.6, +1.6, +3.3, −4.1, −4.9 | VIII-D | mean −0.5 | same | saved Linux runs | linux | R3 | Verified | Seeds are replicates | RAW |
| P6 | Placebo: 5 of 6 runs with p 0.01–0.03 | VIII-D | 5/6 | same | mac `results/v8_mac_reanalysis_20261118_222059_profilefix2/ers_placebo_*.json` | mac `b9b8a86c` | R3 | Exploratory | Unadjusted | RAW |
| P7 | No calibrated model issues NDO at α ∈ {0.10, 0.15} (multiplicity-only issues 1); frozen-threshold held-out risk 0.24–0.50 | VIII-D | — | same | `tables/tab_ablation.tex`; mac `210512` | linux; mac | R1, R3 | Verified | — | DER |
| P8 | MDE 13.5 / 16.5 / 21 pp; 460–1,160 NDO needed; ICC 0.61; design effect 1.48 | VIII-D | — | same | `stats_summary.json` → `power` | linux | R1 | Verified | Normal approximation | DER |
| P9 | Profile fix: seed 2 primary +3.3 → 0.0; ERS gains change ≤ 0.008 | VIII-D | — | same | mac `222059_profilefix2` | mac `b9b8a86c` | R3 | Verified | — | RAW |

## RQ5 — scope of the supporting evidence

| ID | Statement | § | Value | Source report | Machine-readable artifact | Branch / commit | Repro | Status | Limitation | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 | The five-dataset artifact: 250 records (244 distinct) from 12 templates; SHA-1 digests of literal strings; 0/180 Java records compiled or run; outcomes set from labels; integrity and environment hard-coded; stub predictor | VII-B, VIII-E, Table 11 | 250; 12 | `audit/DATASET_VERIFICATION_REPORT.md` | `audit/five_dataset_summary.json`; generator code under `datasets/`, `experiments/` | linux | R4 | Verified | — | DER |
| V2 | No external multi-dataset benchmark was executed | Abstract, VII-B, VIII-E | — | same | — | — | R4 | Verified | — | CALC |
| V3 | Cross-platform status grid (Table 18, Fig. 14) | VIII-E | — | this register (S5–S9) | as in S5–S9 | both | R3 | Verified | Curated from saved outputs | CALC |
| V4 | The 312 records carry a single env id; collection platform not recorded | VIII-E | 1 | — | `datasets/v8/dev_records.jsonl` (`env_id`) | linux | R3 | Verified | — | RAW |

## Literature claims

| ID | Statement | § | Source | Status | Class |
|---|---|---|---|---|---|
| L1 | SemaDiff: about 76% accuracy on 183 commits (preprint) | II-A, Table 2 | `LITERATURE_COMPARISON_REGISTER.md` | Verified (register) | CONC |
| L2 | DiffTestGen: differences exposed in 78.2% of 463 PRs (preprint) | II-A | same | Verified (register) | CONC |
| L3 | Each cell of Tables 2 and 3 stays within the register's "Supports" scope and avoids its "Must NOT be cited for" uses | II | same | Checked in round 2 | CONC |
| L4 | Benchmark sizes in Table 11 | VII-B | same (round-1 L rows) | Verified (register) | CONC |

## Excluded values (not used anywhere in the paper)

| Value | Source | Reason |
|---|---|---|
| 250-pair "independent validation", 200/50 split, 2,500 ERS trials, 1.90 ms | `reports/v8/independent-validation/*` | Label-derived; no benchmark executed |
| Calibration slopes 0.942 / 0.915; strict coverage 18.22%; per-seed p 0.431 / 0.398 | `reports/v8/linux/STATISTICAL_ANALYSIS_REPORT.md` | No raw support, or contradicted by raw output |
| Podman ISO-01..10; "608 tests" | `reports/v8/linux/PODMAN_ISOLATION_REPORT.md`, `FULL_REGRESSION_REPORT.md` | Report text only |

## Simulated review observations (SIM)

Scores and comments in `audit/SIMULATED_PEER_REVIEW.md` (round 1) and in the round-2 red-team section of `SECOND_ROUND_SCIENTIFIC_REVISION.md` are **simulated reviewer judgments**. They are not evidence, and the paper cites neither.

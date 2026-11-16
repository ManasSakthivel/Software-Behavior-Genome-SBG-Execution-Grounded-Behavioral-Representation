# SBG V6 — Experimental Protocol (FROZEN before any V6 held-out run; commit order is the proof)

## Populations (labels never modified)
| Name | Source | Role | Status |
|---|---|---|---|
| DEV | v8 train + val pairs (`pairs_v8{train,val}_output_free_v8.jsonl`), stale math_* programs excluded exactly as in `LABEL_GENERATION_AUDIT.json` | all design, selection, hyper-parameter and fusion decisions | usable |
| H1 | v8 test (967 scored pairs) | single post-freeze run | **observed previously (burned for V5); NON-PRISTINE** |
| H2 | v10 independent (19 programs, 638 pairs) | single post-freeze run | **observed; NON-PRISTINE** |
| X1 | QuixBugs Python (declared `json_testcases` inputs) | real-bug external via real pipeline | small (40 programs), exploratory |
| X2 | BugsInPy units via real pipeline | real-bug external | exploratory; inputs largely unactivated |
No pristine confirmatory holdout exists. Every H1/H2/X result is labelled exploratory-post-freeze.

## Pair universe
Pairs = all rows of the V5 scored files (evaluated or not). V6 is run on every pair; V5 failures remain in the denominator and are reported as abstentions, never dropped.

## Primary question and metric
Oracle-free (R1) ranking of CHANGED(1) vs EQUIVALENT(0): AUROC with 95% **program-cluster bootstrap** CI (resample base programs, 2000 reps, seed 42, all pairs of a program together). Secondary: AP, Brier, ECE(10 bins) after Platt calibration inside training folds, abstention rate.
Abstention handling (pre-declared): headline = **all pairs**, abstained pairs scored at the median score of non-abstained training pairs; also report **evaluable-only** AUROC.

## Model families compared (same folds, same families)
Feature sets: EDIT = {static_token, static_ast, line-edit count}; EXECVOL = {call_count, coverage_size, n_functions, exception_fraction, n_events delta}; CONV = EDIT ∪ EXECVOL; V5 = {sbg_v3, sbg_temporal, sbg_state}; V5raw = sbg_v5; V6 = {d_A,d_B,d_C,cfg_size,g,alpha,c,status}; V6raw = mean(d_A,d_B,d_C); combinations CONV+V5, CONV+V6.
Models: LR(L2) and HistGradientBoosting. An SBG-LR is compared only with a CONV-LR; SBG-GBM only with CONV-GBM. Raw (unsupervised) scores are compared with raw baselines (forward and **reversed** edit size, forward/reversed token/AST); AUROC is reported in both orientations; the orientation is never chosen on held-out data.
R2: adds d_R and delta_out; the differential-testing baseline (delta_out alone, and CONV+delta_out) is mandatory.

## Splits and tuning
DEV: 5-fold GroupKFold by base program, repeated with 3 seeds (42,43,44); inner 3-fold grouped CV for hyper-parameters (LR C in {0.1,1,10}; GBM depth in {2,3}, iters in {50,100}) and Platt calibration. No data-driven feature selection beyond the pre-declared sets. Leave-one-transformation-family-out (LOFO) on DEV, and edit-size-stratified AUROC (tertiles of canonical edit size within DEV).
Freeze: after DEV decisions, `sbgv6/config.py` and the model recipe are hashed into `artifacts/v6/FREEZE_V6.json` and committed **before** any H1/H2/X run. Models for H1/H2/X are fit on all of DEV with the frozen recipe.

## Statistics
Paired comparisons (model A vs B on identical pairs): delta-AUROC with paired program-cluster bootstrap CI and cluster permutation p (`sbg.statistics.cluster_permutation_p`); Holm over the pre-declared family: {V6raw>0.5, V6raw>V5raw, V6raw>best raw baseline, CONV+V6>CONV (LR), CONV+V6>CONV (GBM), CONV+V5>CONV}. Effect size = delta-AUROC and 2*AUROC-1. Distribution shift: standardised feature-mean shift DEV to H1/H2 and AUROC change.

## Ablations (DEV grouped-CV and post-freeze)
-A, -B, -C, -R, -E/evidence, -fusion (raw mean), +/-temporal (V5 temporal added), +/-normalisation, incomplete traces (events truncated to 50%/25%), unactivated tests (25% of inputs).

## Robustness (base programs of DEV, deterministic generation)
Variable rename, function rename, comment/blank insertion, formatting (AST unparse), alternate input seed, incomplete traces, injected instrumentation failure (must give UNKNOWN), nondeterminism (random/time-dependent function must set the flag). Invariance = distance <= 1e-9 or reported; sensitivity measured on SC mutants.

## Integrity rules (binding)
No label edits; no removal of hard pairs; no feature/threshold selection on H1/H2/X; all configs and seeds stored; per-pair vectors and predictions stored in `artifacts/v6/`; every negative result reported; no generalisation claim from X1/X2 sizes.

# SBG V6 — Risk Register
| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Edit-size confound makes any "amount of change" feature look good | H | H | reversed-edit baseline in every table; size-stratified + LOFO |
| R2 | Label noise in EQUIVALENT (8.7% train) and unobservable mutants | H | M | keep labels; secondary oracle-confirmed stratum; report both |
| R3 | No pristine holdout | H | H | declare H1/H2 non-pristine; no confirmatory claims |
| R4 | Differential testing dominates in R2 | H | M | report honestly; SBG value only in R1/complementarity |
| R5 | Block alignment across versions is brittle | M | M | robustness suite; ablation |
| R6 | Tracer cost/timeouts bias the evaluable set | M | M | abstention reported; all-pairs headline |
| R7 | Overfitting in fusion with ~50 programs | H | M | grouped CV, small models, inner tuning |
| R8 | Python-only generalisation | H | M | no cross-language claim; adapter interface only |
| R9 | Hash-seed / Python-version nondeterminism | M | L | PYTHONHASHSEED=0, 3.13.15 pinned, determinism test |
| R10 | Mutants are not real faults (Just et al. 2014) | H | M | synthetic claims limited; QuixBugs/BugsInPy exploratory |

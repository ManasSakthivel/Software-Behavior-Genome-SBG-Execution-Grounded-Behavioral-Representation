# Phase 2 experiment protocol (summary of the pre-registration)

This is a summary. The binding text is [`reports/phase2/E3_E7_PROTOCOLS.md`](../reports/phase2/E3_E7_PROTOCOLS.md) (E3-E7) and [`reports/phase2/LOCAL_EXPERIMENT_RERUN_MATRIX.md`](../reports/phase2/LOCAL_EXPERIMENT_RERUN_MATRIX.md) (matrix and E1 hypothesis). Both were committed before the corresponding experiments ran (`a6afa639`, `aea4202c`); the E1 decision rule was fixed in `scripts/e1_analyze.py` before the run. Results: [`reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md`](../reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md). All of it is exploratory: the data are the 321 non-pristine development pairs (see [`DATASET_PROVENANCE.md`](DATASET_PROVENANCE.md)).

## Common design
- Engine config: `{"budget": {"cpu_seconds": 60, "per_run": {"cpu_s": 2, "wall_s": 5}}}`, other keys at `sbgv7/config.py` defaults (`r_det=3`, `r_replay=5`, `k_alt=3`, `s2_branch_floor=0.80`); 4 workers; `OMP_NUM_THREADS=1`; child `PYTHONHASHSEED=0`; inputs exactly as built by `experiments/v7b/k1_spike.py`.
- Systems: V7-B; baselines B1 (plain differential), B1+rep, B3 (mutation loop), B4 (edit-size threshold). B2 and B5 exist but are not primary.
- Labels: QuixBugs buggy/fixed = declared tests; QuixBugs-neg and synthetic = generator label; BugsInPy units have none. 57 UNLABELLED and 6 SUSPECT_LABEL pairs are excluded from primary denominators (258 remain: 106 divergent, 152 other).
- Statistics: project-level cluster bootstrap (10,000 resamples, seed 42), paired sign-flip primary test, exact McNemar sensitivity, Holm correction within each pre-registered family. All p-values are descriptive because pairs cluster by project.
- Run conditions: sequential runs, `RUN_RECORD.md` per output directory, new directories only, raw evidence preserved, only the exclusions listed in the protocol, deviations disclosed.

## Experiments
| ID | Question | Pre-registered rule | Outcome |
|---|---|---|---|
| E1 | Does the QUARANTINED rate rise after the hash-seed and environment fix (old engine versus current)? | primary metric: pairs with at least one QUARANTINED input among pairs driven in both runs; NOT SUPPORTED if new-only discordant pairs significantly exceed old-only (one-sided exact test, alpha 0.05), SUPPORTED if new count <= old count and the test is not significant | SUPPORTED (weak): 1 versus 2 pairs, 1 versus 3 inputs of 3,044; confounded |
| E2 | Hash-order sensitivity across seeds | not specified (needs a diagnostic seed switch) | **not run** (deferred) |
| E3 | Detection, false assurance, abstention, false alarm versus baselines | reproducible only if at most 3 pairs differ from E1 at verdict level; +10pp false-assurance rule from the statistical analysis plan | V7-B false assurance 0.123 versus 0.226 (+10pp rule not met); detection 0.708 versus 0.774 (not significant after Holm); abstention 0.473; reduction attributable to abstention |
| E4 | Which components change verdicts (V1 `r_det=1`, V2 `r_replay=1`, V3 `k_alt=0`, V4 all three, V5 `FOLD_FD1=False`)? | components classified NO_EFFECT_OBSERVED / SMALL / DETECTABLE; "largely abstention" only if the lower bound of the abstention share exceeds 0.5 | no verdict change; cannot show component value (no nondeterminism in the data) |
| E5 | Sensitivity to `s2_branch_floor` 0.6/0.8/0.9 | "headline stable" iff the sign and `meets_plus10pp` flags equal those at 0.8; S2 share monotone | stable; S2 share 71/55/43; only the label changes |
| E6 | Runtime cost (40-pair fixed subset, 5 reps, 1 worker, seed 20261118) | "costs more" only if the cluster-bootstrap CI of the median ratio excludes 1; repeat once if load > 1.5 | V7-B about 1.6x B1 wall, about 1.02x B1+rep; load rule tripped, repeated, both reported |
| E7 | Does `sbgv7 verify` recompute every verdict, and detect exactly the documented corruptions? | every directory exit 0; 42-case table of expected exit codes fixed in advance | 828/828 verified; 42/42 as expected |

## What the pre-registration does not allow
No threshold was tuned or chosen retrospectively; no exclusion beyond those listed; no change to engine code during the experiments; no claim of significance across the campaign (Holm is per family); no statement of independent generalisation. Anticipated limitations (cluster dominance, load sensitivity, macOS only, fixed hash seed, derived gate counterfactual, tuned B3/B4) are listed in section 8 of the protocol file.

## Not part of Phase 2 (Phase 3)
Linux/Docker isolation verification, K1 (>= 100 runnable real pairs, >= 8 projects), K5 (>= 60 projects, >= 250 adjudicated divergent pairs, kappa >= 0.7), independent sealed holdout, comparison with published tools, hash-order E2, trust anchor for the evidence log. See [`reports/phase2/K1_K5_READINESS_AND_DECISION.md`](../reports/phase2/K1_K5_READINESS_AND_DECISION.md).

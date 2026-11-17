# Figure and table register (initial manuscript)

All data are EXPLORATORY DEVELOPMENT data (321 non-pristine pairs; V7-B shaped by them). Numbers trace to `results/statistics/*` and `research/evaluation/EXPLORATORY_RESULTS.md`. Diagrams are Graphviz `.dot` sources; **no renderer (`dot`, `mmdc`) is installed, so diagrams are NOT RENDERED**. Render with `dot -Tpdf X.dot -o X.pdf` when available. Unimplemented controls (Linux isolation, S3, explorer, module E, Merkle/Supersession) are drawn dashed grey with the words NOT IMPLEMENTED.

## Data figures (results/figures/, PDF + PNG, from `scripts/generate_figures.py`)
| ID | File | Content | Notes |
|---|---|---|---|
| F-D1 | fig_verdict_sufficiency_by_dataset | V7-B verdict and sufficiency per dataset (321 pairs) | counts only |
| F-D2 | fig_insufficient_reasons | primary INSUFFICIENT reason by dataset (117 pairs) | most reasons are harness gaps |
| F-D3 | fig_risk_coverage | coverage vs error risk, V7-B at none/S1/S2/S3 vs baselines | descriptive; generator labels; baselines have no S-levels |
| F-D4 | fig_detection_quixbugs_vs_baselines | detection on QuixBugs (27/29 V7-B; K=1, no cluster CI) and on all DIV pairs with 95% cluster CI (K=78) | no superiority claim |
| F-D5 | fig_runtime | CPU s per pair per system, log scale | V7-B child CPU only (lower bound); memory not recorded |

## Diagrams (paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures/, source only)
| ID | File | Depicts |
|---|---|---|
| F-A1 | architecture.dot | sbgv7 modules and flow; explorer, module E, Linux isolation as not implemented |
| F-A2 | workflow.dot | single `compare` run: repeats, replay, activation, decision |
| F-A3 | evidence_witness_model.dot | evidence record classes, witness and sufficiency chains; Merkle/Supersession not implemented |
| F-A4 | sufficiency_levels.dot | S0-S2; S3 not implemented (refused in config) |
| F-A5 | verdict_flowchart.dot | three verdicts, first match wins, no equivalence verdict |
| F-A6 | isolation.dot | macOS sandbox-exec child per run, `policy_below_minimum`; Linux container not implemented |
| F-A7 | benchmark_provenance.dot | QuixBugs, BugsInPy, synthetic into 321 non-pristine pairs; no holdout |
| F-A8 | split_pipeline.dot | development (current) vs DEV-N, sealing, holdout, confirmatory (all not yet existing) |
| F-A9 | baseline_framework.dot | B1-B5 under common runner/inputs/budget; published tools not implemented |

## Tables
| ID | Content | Source |
|---|---|---|
| T1 | Dataset, pair counts and truth rule per arm | EXPLORATORY_RESULTS.md, `results/processed/dev_pairs_per_system.csv` |
| T2 | System metrics with cluster CIs (detection, false assurance, abstention, false alarm, CPU) | `results/statistics/system_metrics.csv`, `cost.csv` |
| T3 | Paired comparisons vs B1 (sign-flip, Holm, +10pp flag) | `results/statistics/paired_comparisons.csv` |
| T4 | Risk-coverage | `results/statistics/risk_coverage.csv` |
| T5 | Class counts (system x truth x verdict) | `results/statistics/class_counts.csv` |
| T6 | Power on observed design (+5pp at most 0.27; +10pp not reachable) | `results/statistics/power_actual.json` |
| T7 | NOT EVALUATED register | EXPLORATORY_RESULTS.md |
| T8 | Baseline fairness and non-implemented tools | `research/evaluation/BASELINE_IMPLEMENTATION_AND_FAIRNESS.md` |

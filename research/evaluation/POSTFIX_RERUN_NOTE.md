# Post-fix rerun note (commit 700532b8: NO_RUN blocks NO_DIVERGENCE_OBSERVED as resource_limit)

Date 2026-11-17. Full rerun of the K1 spike (321 pairs, run1) on the fixed engine, rebuilt CSV, `analyze_results.py` (B=10000, seed 42, ref B1), `power_actual.py`, figures. Nothing earlier was overwritten.
Outputs: raw `results/raw/k1_spike_postfix/`; processed/statistics/figures under `results/postfix/` (`processed/`, `statistics/` incl. `sensitivity_excluding_SP2_renamed/`, `figures/`). Run with OMP_NUM_THREADS=1, 4 workers. Small tooling change: `k1_spike.py`, `build_dev_pairs_csv.py`, `generate_figures.py` accept env overrides `K1_RAW`, `K1_PROC`, `POSTFIX_DIR` (defaults unchanged).

## Result: 3 of 321 V7-B verdicts changed; headline detection / false-assurance / false-alarm numbers did NOT change; abstention and risk-coverage changed slightly.

Changed pairs (all `quixbugs_neg`, label NO_OBS_DIFF, SP-1/SP-3 variants), NO_DIVERGENCE_OBSERVED/S2 -> INSUFFICIENT (primary `resource_limit`):
- quixbugs_neg:knapsack__sp-1_s0
- quixbugs_neg:knapsack__sp-3_s0
- quixbugs_neg:levenshtein__sp-3_s0
No other pair changed verdict, level, primary, secondary or witness. (One synthetic pair, train__graph_center_finder__sp-11_s1, shows inputs_same 10->9 / quarantined 1->2 with the same verdict; SUSPECT_LABEL pair, excluded from primary denominators.) Baselines (B1, B1+rep, B3, B4) are unaffected.

| Quantity | Original | Post-fix |
|---|---|---|
| V7-B abstention (n=258) | 0.349 [0.300, 0.435] | 0.360 [0.306, 0.435] |
| V7-B on NO_OBS_DIFF (n=152) | 72 INSUFFICIENT, 80 NO_DIV | 75 INSUFFICIENT, 77 NO_DIV |
| quixbugs_neg verdicts (n=85) | DIV 1, S1 3, S2 47, INSUFF 34 | DIV 1, S1 3, S2 44, INSUFF 37 |
| quixbugs_neg INSUFFICIENT fraction | 40% | 43.5% |
| INSUFFICIENT reasons overall | resource_limit 4 | resource_limit 7 |
| Abstention excl. SP-2 (sensitivity, n=207) | 0.188 [0.116, 0.336] | 0.203 [0.140, 0.336] |
| Risk-coverage, all levels | coverage 0.651, risk 0.077 | 0.640, 0.079 |
| Risk-coverage, >= S2 | 0.589, 0.053 | 0.578, 0.054 |
| Paired V7-B vs B1 abstention row | 90 test-only discordant | 93 |

Unchanged (identical in both runs): V7-B detection 0.708 [0.545, 0.816] (75 DIVERGENT / 13 NDO / 18 INSUFFICIENT on DIV), false assurance 0.123, false alarm 0.000, all baseline rows, detection and false-assurance paired comparisons and Holm values, power_actual.json (byte-identical), K1/K2 conclusions (not met / not assessable), QuixBugs buggy/fixed and BugsInPy and synthetic arm counts, determinism for quixbugs/bugsinpy_units/quixbugs_neg (31/31, 46/46, 25/25 identical).

Caveat: the postfix run2 (determinism) subset did not include the synthetic arm (the `--rerun` default of 25 is consumed by quixbugs_neg), so synthetic determinism (37/37 originally) was not re-checked; the only synthetic difference seen is the quarantine count noted above. Statistics files also differ in CPU/timing columns (cost.*), which is wall-clock noise, not a verdict change.

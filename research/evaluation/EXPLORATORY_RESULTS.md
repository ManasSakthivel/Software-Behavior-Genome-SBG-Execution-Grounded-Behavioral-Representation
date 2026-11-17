# V7-B exploratory development results

Date 2026-11-17, branch research/v7b-final-validation. **EXPLORATORY DEVELOPMENT ANALYSIS. All 321 pairs are non-pristine (QuixBugs and BugsInPy are burned; v8/v10 synthetic pairs were scored by V5/V6) and V7-B was shaped by seeing this data. Nothing here is a confirmatory, held-out or generalisable result, and no claim is made about any detection rate in the field.** No sealed or holdout split exists yet; the K5 gate (>= 60 projects, >= 250 independent divergent pairs, kappa >= 0.7, clean leakage audit) is not met, so per SAP section 8 the study is exploratory.

Reproduce: `.venv/bin/python scripts/build_dev_pairs_csv.py`, then `scripts/analyze_results.py results/processed/dev_pairs_per_system.csv --out results/statistics --reference B1 --seed 42 --boot 10000`, `scripts/power_actual.py --processed ... --test V7-B --reference B1 --out results/statistics/power_actual.json`, `scripts/generate_figures.py`. Inputs are read-only copies of `results/processed/{k1_spike,baselines}_per_pair*.jsonl`; V5/V6 and raw results were not modified. matplotlib was installed into `.venv` for the figures.

## Data and truth (what is and is not defensible)
`results/processed/dev_pairs_per_system.csv`: 1605 rows = 321 pairs x {V7-B, B1, B1+rep, B3, B4} (extra columns `dataset`, `flag`). V7-B = K1 spike run 1; baselines = `baselines_per_pair*.jsonl`, B4 from the `_final` file. DIVERGE maps to DIVERGENT_OBSERVABLE, NO_DIFF to NO_DIVERGENCE_OBSERVED; baselines have no sufficiency level. B2 (QuixBugs only) and B5 (237/321, V6 lookup) are not in the CSV. `mem_mb` is empty: memory was not recorded in any run.

| dataset | pairs | truth used |
|---|---|---|
| quixbugs_buggy_fixed | 31 | DIV for 29: the benchmark's declared tests fail on buggy and pass on fixed (B2 oracle, independent of V7-B/B1/B3). 2 UNLABELLED (no declared test witness). Truth is therefore only "a declared input distinguishes them". |
| quixbugs_sp_negatives | 85 | generator label NO_OBS_DIFF for 84; 1 SUSPECT (levenshtein SP-6) |
| synthetic_changed | 78 | generator label CHANGED = DIV for 77; 1 SUSPECT (SC-1+SP-11). Divergence may lie outside the sampled inputs, so detection here conflates input sufficiency with the system |
| synthetic_equivalent | 72 | generator label, "equivalent under looser equality", NO_OBS_DIFF for 68; 4 SUSPECT (SP-8 x2, SP-11 x2) |
| bugsinpy_units | 55 | none: real bugfix on synthetic-battery inputs, regression not reproduced; 9 not driven (class units) |

Suspect labels (6 pairs, K1 report finding 3 plus SP-8/SP-11) are tagged `SUSPECT_LABEL`, excluded from primary denominators, still counted; no label was changed. Primary denominators: 106 DIV, 152 NO_OBS_DIFF, 258 total; 57 UNLABELLED + 6 SUSPECT excluded. 51 pairs carry an SP-2 renamed-entry flag (V7-B returns `unsupported_signature`; baselines see a missing entry as a difference, which inflates their false-alarm count). A sensitivity run without them is in `results/statistics/sensitivity_excluding_SP2_renamed/`.

## Design (must be read before any number)
- DIV pairs: 106 pairs in 78 "projects"; 29 of them sit in one cluster (QuixBugs counted as one project, as the K1 report does). Synthetic "projects" are generator base programs (101 of them), not independent real projects. Real independent projects with project-level runs: 0. K=78 or 101 is nominal; effective independence is much lower and not assessable (no lineage audit).
- NO_OBS_DIFF pairs: 152 in 69 projects, 84 of them in the single QuixBugs cluster.
- ICC for the paired detection difference was estimated 0.0 (design effect 1.0), which reflects the one large cluster having no discordance, not low clustering in general.

## Results (descriptive; 95% project-cluster percentile bootstrap, B=10000, seed 42)
| System | Detection on DIV (n=106) | False assurance on DIV | Abstention (n=258) | False alarm on NO_OBS_DIFF (n=152) | Median CPU s (sum) |
|---|---|---|---|---|---|
| V7-B | 0.708 [0.545, 0.816] | 0.123 [0.054, 0.236] | 0.349 [0.300, 0.435] | 0.000 [0, 0] | 1.28 (455)* |
| B1 | 0.774 [0.609, 0.881] | 0.226 [0.119, 0.392] | 0 | 0.303 [0.149, 0.352] | 0.40 (151) |
| B1+rep | 0.774 [0.610, 0.880] | 0.226 [0.120, 0.390] | 0 | 0.303 [0.148, 0.352] | 1.27 (543) |
| B3 | 0.811 [0.662, 0.904] | 0.189 [0.097, 0.337] | 0 | 0.309 [0.147, 0.361] | 3.77 (1424) |
| B4 | 0.009 [0, 0.019] | 0.991 [0.981, 1] | 0 | 0.007 [0, 0.010] | 0 |

*V7-B CPU is child-process only; parent overhead was not measured, so this is a lower bound. Baseline CPU includes the calling thread's overhead. Counts: V7-B on DIV: 75 DIVERGENT, 13 NO_DIVERGENCE_OBSERVED, 18 INSUFFICIENT. B1: 82 / 24 / 0. On NO_OBS_DIFF V7-B: 0 false alarms, 72 INSUFFICIENT, 80 NO_DIVERGENCE_OBSERVED. Bootstrap CIs with a very skewed cluster structure (one cluster of 113 eligible pairs) are not trustworthy and percentile CIs undercover when K is small; all 46 B1 false alarms (31 QuixBugs SP negatives, 15 synthetic) are SP-2 renamed-entry pairs, i.e. a harness artefact rather than a behavioural false alarm (B3: 47, 46 of them SP-2). Without SP-2 pairs (sensitivity run): B1 false alarm 0.000, V7-B abstention 0.188, detection 0.767 (B1) vs 0.728 (V7-B).

By dataset (counts, V7-B): QuixBugs buggy/fixed DIVERGENT 27, INSUFFICIENT 4 (V7-B detected 27 of the 29 test-witnessed pairs; B1, B1+rep and B3 detected 29/29; B4 1/29; no cluster CI because K=1). SP negatives: DIVERGENT 1, S1 3, S2 47, INSUFFICIENT 34. Synthetic CHANGED: DIVERGENT 49, S1 5, S2 8, INSUFFICIENT 16. Synthetic EQUIVALENT: DIVERGENT 1, S1 8, S2 24, INSUFFICIENT 39. BugsInPy units: DIVERGENT 6, S1 1, S2 15, INSUFFICIENT 24, not driven 9. INSUFFICIENT primary reasons overall: changed_region_not_activated 60, unsupported_signature 49 (renamed entries), resource_limit 4, nondeterministic 2, import_error 1, unobservable_outcome 1.

Paired comparisons against B1 (unadjusted exploratory; sign-flip over projects, Holm within the family of the comparisons in this run):
| Comparison | Outcome | Diff | Improvement [95% CI] | b (test-only) / c (ref-only) | p sign-flip | Holm |
|---|---|---|---|---|---|---|
| V7-B vs B1 | false assurance | -10.4pp | +10.4pp [4.3, 20.5] | 0 / 11 | 0.001 | 0.006 |
| V7-B vs B1 | detection | -6.6pp | -6.6pp [-11.5, -2.6] | 0 / 7 | 0.031 | 0.156 |
| B3 vs B1 | detection | +3.8pp | +3.8pp [0.7, 9.0] | 4 / 0 | 0.125 | 0.500 |
| B1+rep vs B1 | any | 0 | 0 | 0 / 0 | 1.0 | 1.0 |
No row satisfies the `meets_plus10pp` rule (lower bound must exceed +10pp). The V7-B false-assurance reduction is mostly relocation of outcomes to INSUFFICIENT (V7-B abstains on 18 DIV pairs), not matched-coverage superiority; K4 matched-coverage FAR is NOT computed here. B1 detected every pair V7-B detected. These are descriptions of the development set, not evidence that V7-B beats any comparator.

Risk-coverage (error risk = errors / decided; `results/statistics/risk_coverage.csv`): V7-B at all levels coverage 0.651, risk 0.077; at >= S2 coverage 0.589, risk 0.053; at >= S3 (never emitted) 0.291 risk 0. Baselines decide every pair (coverage 1.0) with risk 0.26-0.27 (B4 0.41). Baselines carry no sufficiency level so their S-level rows are not comparable. Risk is measured against generator labels with known defects.

## Power on the observed design (`results/statistics/power_actual.json`)
From development data: K=78, 106 pairs, p0 (B1 detection) 0.774, discordance pi 0.066, rho 0.0. Power at +5pp is 0.27 (alpha 0.05) / 0.12 (alpha 0.0167) at best; at +10pp it is not reachable (discordance 6.6% cannot carry a 10pp difference; MDE for 80% power not reachable below pi) across the rho x pi grid. Simulation assumptions A1-A4 are printed in the file, they are not facts about V7-B. This design cannot support a confirmatory +10pp claim, and the observed effect (negative for detection) is not used to compute post-hoc power.

## NOT EVALUATED, with reasons
| Item | Status | Reason |
|---|---|---|
| Confirmatory family (P1/P2; H2a, H2b, H4), Holm claims | NOT EVALUATED | no sealed holdout; data non-pristine; K5 not met; few independent projects (QuixBugs = 1; synthetic projects are generator programs) |
| +10pp superiority, K3/K4 gates, matched-coverage FAR vs like-for-like comparators | NOT EVALUATED | only raw counts; no matched-coverage computation; replay+structure baselines not part of this run |
| RQ4 generalisation (across projects, domains, unseen code) | NOT ASSESSABLE | all data development-tuned; 0 independent real project-level runs |
| RQ5 overhead | LOWER BOUND ONLY | V7-B CPU is child-only, parent overhead unmeasured; memory not recorded; macOS, 4 workers, 12 inputs/pair max |
| Truth for BugsInPy, 2 QuixBugs pairs, 6 suspect labels | NOT EVALUATED | no defensible label; never relabelled |
| ICC / design effect, Kish n | UNRELIABLE | one 113-pair cluster dominates; estimated 0.0 |
| K1 (>= 100 runnable real pairs, >= 8 projects), K2 isolation-based determinism | NOT MET / NOT ASSESSABLE | K1 report: 74 runnable real pairs, 0 project-level runs; Linux isolation not implemented |
| B2, B5 | partial | B2 QuixBugs only (used as QuixBugs truth); B5 237/321, V6 artifact lookup, excluded from CSV |
| Published tools (shadow SE, Testora, Mokav, AFL etc.) | NOT IMPLEMENTED | no comparison; no superiority claim over them |
| S3, explorer, Linux container isolation, declared renames, generator entries | NOT IMPLEMENTED | `docs/architecture/V7B_IMPLEMENTATION.md`; they cause most INSUFFICIENT outcomes (SP-2 renames, generators) |

# Abstention and coverage
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.
Rule (frozen P1): NOT_ACTIVATED and UNKNOWN pairs abstain. ALL-PAIRS AUROC/AUPRC give them the DEV median fill (ties); EVALUABLE metrics drop them. The two are never combined. Coverage = ACTIVATED pairs / all pairs. V5 evaluability and V6 activation coincide in the INTERSECT view (identical to EVALUABLE on every benchmark).

| Benchmark | ACTIVATED | NOT_ACTIVATED | UNKNOWN | abstained positives / abstained | coverage |
|---|---|---|---|---|---|
| v8 test | 887 | 69 | 11 | 41/80 | 91.7% |
| v10 | 632 | 9 | 3 | 3/12 | 98.1% |
| QuixBugs declared | 93 | 0 | 59 (36 ineligible program, 23 execution failures) | 19/59 | 61.2% |
| QuixBugs canonical | 106 | 30 | 16 | 24/46 | 69.7% |
| BugsInPy | 57 | 26 | 117 | 42/143 | 28.5% |

Causes of UNKNOWN: BugsInPy: nondeterministic base 60, unsupported signature 49, import error 4; QuixBugs: nondeterminism, non-termination, low usable traces. Abstention is concentrated in SP-4 negatives on v8 test (36%) and in BugsInPy (76% of real fixes). On v8 test abstained pairs are 51% positive vs 58% overall, so abstention is not label-leaking. On BugsInPy the evaluable-only AUROC (0.505) equals the all-pairs one, so the low coverage hides no better performance. On QuixBugs the evaluable AUROC is higher (0.75 vs 0.67), but that subset is selected by executability, so it cannot be read as the true performance.

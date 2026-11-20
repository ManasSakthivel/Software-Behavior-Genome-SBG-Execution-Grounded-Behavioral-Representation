# C0g vs C1 (secondary sensitivity; C1 is not promoted regardless of results)
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.

| Benchmark | C0g LR | C1 LR | Δ(C0g−C1) LR [95% CI] | p (unadj.) | Δ GBM [CI] |
|---|---|---|---|---|---|
| v8 test | 0.768 | 0.758 | +0.010 [−0.002,+0.023] | 0.29 | +0.038 [+0.024,+0.056] |
| v10 | 0.851 | 0.878 | −0.027 [−0.045,−0.013] | 0.0045 | +0.001 [−0.019,+0.024] |
| QuixBugs declared | 0.666 | 0.631 | +0.035 [−0.038,+0.108] | 0.37 | +0.014 [−0.010,+0.042] |
| QuixBugs canonical | 0.691 | 0.615 | +0.076 [+0.022,+0.135] | 0.021 | +0.038 [−0.008,+0.090] |
| BugsInPy | 0.505 | 0.557 | −0.052 [−0.109,−0.002] | 0.13 | +0.003 [−0.003,+0.011] |

Reading: the sign of the E-columns' effect flips between benchmarks (helps v8 GBM and QuixBugs, hurts v10 LR). This matches the DEV finding that E acts as a moderator and not a detector. Nothing here supports calling E an independent behavioural signal, and nothing justifies switching to C1. All p-values are exploratory and unadjusted.

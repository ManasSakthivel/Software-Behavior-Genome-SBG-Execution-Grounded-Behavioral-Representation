# Claim–evidence matrix
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.

| Claim | Evidence | Verdict |
|---|---|---|
| V6 detects behavioural change above chance, oracle-free | AUROC 0.77 v8, 0.85 v10, 0.67/0.69 QuixBugs, CIs exclude 0.5; BugsInPy 0.505 | Supported on synthetic and QuixBugs; NOT on BugsInPy |
| V6 beats V5 | +0.014 to +0.092 everywhere; none survives Holm (v8 p=0.060) | Direction consistent, not statistically established |
| V6 adds independent information beyond conventional features | pre-declared criterion failed; losses on BugsInPy (LR) and QB canonical (GBM) | **NOT SUPPORTED** |
| V6 is better than conventional features alone | worse on v8 test and BugsInPy; better on v10 and QuixBugs | Not supported in general; context-dependent |
| E is an independent detector | alpha alone 0.46 on DEV; C0g vs C1 flips sign across sets | Not supported (moderator only) |
| Abstention is safe | coverage 28-98%; abstained sets not label-skewed on v8 | Supported as a policy; low coverage limits usefulness on real code |
| Return-state/differential testing | 0.775 v8, 0.995 v10, 0.750 QB declared, 0.502 BugsInPy; separate regime | Strong when outputs are observable; no SBG claim |
| Results generalise to real bugs | QuixBugs weak positive, BugsInPy none | NOT supported |
| Research-ready | | **No** |

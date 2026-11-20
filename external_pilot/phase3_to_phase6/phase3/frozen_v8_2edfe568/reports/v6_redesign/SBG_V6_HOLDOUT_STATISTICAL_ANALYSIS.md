# Statistical analysis
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.
Method: program/bug-cluster bootstrap CI (B=2000, seed 42); paired deltas on identical pairs; cluster sign-swap permutation test (B=2000, two-sided). All benchmarks passed the pre-declared inference gate (>=15 clusters, >=10 mixed-class clusters), so inferential claims are permitted, but 19-51 clusters is small and these sets were observed before.
Holm family (declared contrasts a, b, c, all benchmarks, 15 tests):

| Contrast | v8 test Δ (Holm p) | v10 | QB declared | QB canonical | BugsInPy |
|---|---|---|---|---|---|
| a: CONV+C0g − CONV, LR | +0.040 (0.030) | +0.072 (0.144) | +0.089 (0.080) | +0.007 (1.0) | −0.103 (0.013) |
| b: CONV+C0g − CONV, GBM | +0.006 (1.0) | +0.162 (0.0075) | +0.056 (0.31) | −0.123 (0.0075) | −0.009 (1.0) |
| c: C0g − V5, LR | +0.060 (0.060) | +0.014 (1.0) | +0.052 (1.0) | +0.092 (0.14) | +0.030 (1.0) |

Pre-declared claim criterion ("independent information beyond conventional features"): SUPPORTED needs a AND b with Holm p<0.05 and positive on v8 test AND v10 AND one external set; PARTIAL needs it on v8 and v10. Result: v8 test passes a but fails b; v10 passes b but fails a. **NOT SUPPORTED** (not even PARTIAL).
Descriptive: point deltas for a are positive on 4 of 5 benchmarks and for b on 3 of 5; the two significant external results (a on BugsInPy, b on QB canonical) are losses. C0g vs V5: positive on all 5 (+0.014 to +0.092), but no contrast survives Holm. Unadjusted contrasts marked 'x' in the JSON are exploratory.
Caveat: v10 conventional baselines collapse (0.69) because v10 composes SC+SP edits, which breaks the edit-size shortcut; that is where V6 helps most (+0.16 GBM).

# Failure analysis (follow-up diagnosis; the primary numbers are not altered)
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.
Raw lists: results/failures_<bench>_{FN,FP}.csv (15 worst each).
1. **SC-6 return mutations** still fail: v8 C0g 0.54 (V5 0.34, V6raw 0.32), v10 0.32. Consistent with the DEV diagnosis (the trace channel never sees return values). Differential output comparison gets 0.86 and 1.0 on them.
2. **Small point edits**: lowest-scored v8 positives are SC-1 / SC-3 with 2 edited lines (C0g SC-1 0.55, SC-3 0.64 vs CONV 0.84, 0.86). Identical feature vectors give identical scores (0.3299 for many SC-1 pairs): there is no signal to rank them.
3. **BugsInPy**: 76% of real fixes abstain; ranked ones sit at a common value (0.3659 = the abstention fill). The units are tiny, often nondeterministic or non-drivable, so the oracle-free channel has little to observe. Edit size alone does better (0.847) than any SBG variant.
4. **QuixBugs**: 47% of real bugs abstain in the declared regime; the remainder rank above chance.
5. **False positives**: SP-5 (loop rewrite) and SP-8 (extract function) negatives score highest (mean 0.60-0.64 vs about 0.40 for others), because they genuinely change traces; SP-8 labels were found defective in DEV.
6. v8 test: CONV GBM 0.981 beats C0g (0.877) by 0.10 (generator fingerprinting, as in DEV); this must not be read as better bug detection.
Not investigated further: the BugsInPy nondeterminism source and whether richer inputs would activate more pairs.

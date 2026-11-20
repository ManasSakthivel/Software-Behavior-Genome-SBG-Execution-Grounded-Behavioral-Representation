# External generalisation (QuixBugs, BugsInPy)
Source: artifacts/v6/holdout/results/HOLDOUT_RESULTS.json (single frozen run, 114 s; plan committed beforehand in artifacts/v6/holdout/HOLDOUT_ANALYSIS_PLAN.md). Architecture C0g (primary), C1 (secondary), per FINAL_MANIFEST_V6_candidate1.json. All five benchmarks were previously seen with V5 and are NOT pristine or entirely unseen.
Both were also used by earlier V5 work and QuixBugs is public; they are not unseen.

QuixBugs (40 programs, 1 real bug each, 112 SP negatives): C0g 0.666 (declared), 0.691 (canonical), above CONV (0.484/0.506), by +0.18 (CI [0.08,0.29] / [0.11,0.26]). The gain over V5 is not significant (declared +0.052 [−0.049,+0.150]; canonical +0.092 [+0.030,+0.152], Holm p=0.14). Conventional features are at chance here, and reversed edit size is below chance (0.325): in real bugs the buggy file is NOT the smaller edit, unlike the synthetic benchmark. This supports the DEV conclusion that the edit-size signal is a synthetic artifact. CONV+C0g vs CONV (LR): +0.089 declared (Holm p=0.08), +0.007 canonical (n.s.); GBM: +0.056 declared (Holm 0.31), −0.123 canonical (Holm 0.007, a significant LOSS).
Differential output comparison (separate regime) reaches 0.750 declared (0.976 on evaluable pairs); canonical 0.575.

BugsInPy (51 bugs, 55 positives, 145 negatives): coverage 28.5%; C0g 0.505, i.e. chance, AUPRC 0.281 vs prevalence 0.275. Conventional features reach 0.731 (LR) / 0.793 (GBM) and reversed edit size 0.847. CONV+C0g is significantly WORSE than CONV (LR −0.103 [−0.148,−0.054], Holm p=0.013). 143 of 200 pairs abstain (nondeterministic or unsupported-signature units). No SBG V6 claim holds on this benchmark.

Verdict: weak positive evidence on QuixBugs, none on BugsInPy. Not external validation.

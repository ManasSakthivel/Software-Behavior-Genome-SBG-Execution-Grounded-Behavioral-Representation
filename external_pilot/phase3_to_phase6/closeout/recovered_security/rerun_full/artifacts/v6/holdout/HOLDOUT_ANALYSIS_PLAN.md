# SBG V6 holdout analysis plan (written and committed BEFORE any holdout feature was extracted or scored)

Frozen architecture: artifacts/v6/FINAL_MANIFEST_V6_candidate1.json (C0g primary, C1 secondary sensitivity). Nothing below may be changed after results are seen.

## Benchmarks (all NON-PRISTINE or non-held-out in some sense; none is "entirely unseen")
- H1 v8 test (22 programs after the stale-program exclusion; 956 evaluated + 11 V5-unevaluated pairs). Previously scored with V5 and its result observed.
- H2 v10 independent (19 programs, 638 pairs after stale exclusion; composed SC+SP mutants). Previously scored with V5.
- X1 QuixBugs Python, DECLARED regime = primary (V6 protocol: declared json_testcases inputs, outputs discarded); CANONICAL regime reported as a pre-existing secondary regime, never chosen by result. 40 programs, 1 real bug each + SP negatives. Previously evaluated with V5 (below chance) and publicly known.
- X2 BugsInPy units, same extraction protocol as V5 (output_free_v7). Previously evaluated with V5.
Protocols: v8/v10 use output_free_v8; QuixBugs/BugsInPy use output_free_v7 exactly as the V5 external runs. Labels are never modified.

## Fitting
Final models fit once on ALL DEV pairs (re-extracted v8 train+val, 2392 pairs) with the frozen recipe; no seeds vary (fit is deterministic; seeds 42-44 were for DEV CV). No thresholds are used. Systems: C0g, C1 (P1 policy), CONV, CONV+C0g, CONV+C1, V5 (frozen indicator recipe), each LR (primary) and GBM (secondary); R2 regime (separate): DIFF, C1+R, CONV+DIFF, CONV+DIFF+C1. Raw baselines: sbg_v5, d_v6, d_A, d_B, d_C, g, alpha, static_token, static_ast, edit_lines (BOTH orientations reported, none selected), call_count, coverage_size.

## Abstention handling (stated per metric)
- P1: NOT_ACTIVATED / UNKNOWN pairs abstain; for the "ALL-PAIRS" view their score is the median inner-OOF score of activated DEV training pairs. Never read as equivalence.
- ALL-PAIRS view: every pair is in the denominator; abstained pairs carry the median score (so they are uninformative ties).
- EVALUABLE view: only ACTIVATED pairs (for V5: pairs V5 evaluated; for INTERSECT: both). Reported separately and never mixed with ALL-PAIRS.
- Coverage = evaluable pairs / all pairs. AUPRC is computed on the same views; its chance level is the positive prevalence.
- Non-SBG baselines (CONV, statics) never abstain in ALL-PAIRS; their evaluable-view AUROC is computed on the same activated subset for a like-for-like comparison.

## Inference
Clusters = base programs (v8/v10/QuixBugs) and bug ids (BugsInPy). Cluster bootstrap B=2000, seed 42 for AUROC and AUPRC CIs. Paired deltas (same pairs): cluster-bootstrap CI + cluster permutation p (B=2000, two-sided). Inferential claims only when clusters >= 15 with both classes present in >= 10 clusters; otherwise descriptive only and labelled so. Holm family over inference contrasts (3 per benchmark x 4 benchmarks = 12): (a) CONV+C0g - CONV, LR; (b) CONV+C0g - CONV, GBM; (c) C0g - V5, LR. Secondary (unadjusted, labelled exploratory): C0g - C1, C0g vs 0.5, GBM versions, EVALUABLE views.

## Claim criteria (declared before the run)
"SBG V6 adds independent behavioural information beyond conventional features" is
- SUPPORTED if contrasts (a) AND (b) have Holm p < 0.05 with positive deltas on both H1 and H2 AND on at least one of X1/X2;
- PARTIALLY SUPPORTED (synthetic only) if that holds on H1 and H2 only;
- NOT SUPPORTED otherwise.
Even SUPPORTED does not imply research readiness (synthetic labels, non-pristine sets, small external clusters). Failure is reported as failure; the primary holdout numbers are never altered by follow-up investigation.

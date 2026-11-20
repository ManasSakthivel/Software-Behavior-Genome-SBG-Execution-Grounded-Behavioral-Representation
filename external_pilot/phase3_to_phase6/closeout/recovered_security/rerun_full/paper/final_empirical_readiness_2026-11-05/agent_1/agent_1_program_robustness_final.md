# Agent 1 — Program Robustness Report (V10, final sprint)

**Status:** exploratory, post-hoc. Nothing here replaces the frozen V10 primary result.
**Inputs (read-only):** frozen V10 scored pairs, `V10_MODELS_FROZEN.json`, the V10 manifest and the previous-sprint tables in `paper/empirical_sprint_2026-11-04/agent_2/`.
**Independent check:** [`verify_program_robustness.py`](verify_program_robustness.py) re-derives the numbers with its own AUROC, win/loss, leave-one-program-out (LOPO), within/between and bootstrap code. It reuses only the frozen loaders and the frozen M_EX model. Results are in [`verification_v10.json`](verification_v10.json) and [`verification_v10_checks.csv`](verification_v10_checks.csv).
**Verification outcome:** 79 numeric checks against the previous-sprint `results_v10.json`, **0 mismatches** (tolerance 1.5e-6, exact for counts).

## 1. Population
19 programs, 638 evaluated pairs (319 CHANGED, 319 EQUIVALENT), 319 matched sets.
Three V10 pairs were unevaluated because they did not terminate (two `math_fib_matrix`, one `sort_stooge_sort`). The frozen matched-complete rule drops their partners. The dataset therefore has 641 evaluated rows and the analysed population has 638.
Pooled AUROC: V5 0.896768, edit size 0.616046, M_EX 0.790789. All three match the frozen headline to 1e-6.

## 2. Per-program AUROC and sample sizes
Each program has equal numbers of CHANGED and EQUIVALENT pairs (n_chg/n_eq).

| Program | n | chg/eq | V5 | edit | M_EX | V5−edit | V5−M_EX |
|---|--:|---|--:|--:|--:|--:|--:|
| ds_min_heap_array | 32 | 16/16 | 0.9277 | 0.6465 | 0.6680 | +0.281 | +0.260 |
| ds_ranked_set | 38 | 19/19 | 0.9086 | 0.6371 | 0.6427 | +0.271 | +0.266 |
| ds_union_find | 30 | 15/15 | 0.9467 | 0.6067 | 0.7844 | +0.340 | +0.162 |
| graph_alien_dict | 14 | 7/7 | 0.8776 | 0.6122 | 1.0000 | +0.265 | −0.122 |
| graph_cycle_detection_dfs | 34 | 17/17 | 0.9377 | 0.5900 | 0.8166 | +0.348 | +0.121 |
| graph_network_delay | 36 | 18/18 | 0.9630 | 0.6559 | 0.9599 | +0.307 | +0.003 |
| graph_topological_kahn | 36 | 18/18 | 0.7052 | 0.6327 | 0.7994 | +0.073 | −0.094 |
| math_coin_change | 38 | 19/19 | 0.9280 | 0.6773 | 0.8975 | +0.251 | +0.030 |
| math_fib_matrix | 26 | 13/13 | 0.9704 | 0.6065 | 0.5148 | +0.364 | +0.456 |
| math_knapsack_01 | 48 | 24/24 | 0.8811 | 0.6354 | 0.8420 | +0.246 | +0.039 |
| sort_bitonic_sort | 38 | 19/19 | 0.9072 | 0.6413 | 0.9460 | +0.266 | −0.039 |
| sort_gnome_sort | 32 | 16/16 | 0.8125 | 0.6758 | 0.8027 | +0.137 | +0.010 |
| sort_gravity_bead | 38 | 19/19 | 0.9086 | 0.6053 | 0.6773 | +0.303 | +0.231 |
| sort_pancake | 38 | 19/19 | 0.9169 | 0.6427 | 0.3961 | +0.274 | +0.521 |
| sort_radix_sort_lsd | 36 | 18/18 | 0.7454 | 0.6451 | 0.8781 | +0.100 | −0.133 |
| sort_stooge_sort | 28 | 14/14 | 0.9413 | 0.6301 | 0.8444 | +0.311 | +0.097 |
| sort_tree_sort | 36 | 18/18 | 0.9537 | 0.6466 | 0.8272 | +0.307 | +0.127 |
| str_decode_run_length | 30 | 15/15 | 0.9467 | 0.6156 | 0.9200 | +0.331 | +0.027 |
| str_group_anagrams | 30 | 15/15 | 0.7889 | 0.6400 | 0.9467 | +0.149 | −0.158 |

Per-program V5 AUROC: range 0.705–0.970, unweighted mean 0.8930, median 0.917. Three programs are below 0.80 (`graph_topological_kahn`, `sort_radix_sort_lsd`, `str_group_anagrams`). Per-program n is small (14–48 pairs; 7–24 per class), so individual program AUROCs are imprecise. Treat them as descriptive.

## 3. V5 versus edit size and versus M_EX (program as the unit)

| Comparison | Wins | Losses | Ties | Mean per-program diff | Median | Exact sign-test p (two-sided) | Program-bootstrap 95% CI of mean diff |
|---|--:|--:|--:|--:|--:|--:|---|
| V5 vs edit | **19** | 0 | 0 | +0.2592 | +0.2742 | 3.8e−6 | [0.220, 0.294] |
| V5 vs M_EX | **14** | 5 | 0 | +0.0949 | +0.0391 | 0.064 | [0.015, 0.181] |

- **Verified.** V5 beats edit size in 19 of 19 programs, with a mean gain of +0.259. The smallest gain is +0.073 (`graph_topological_kahn`) and the largest is +0.364 (`math_fib_matrix`).
- **V5 vs M_EX is not a decisive win.** V5 wins 14 of 19 and loses 5 (`graph_alien_dict`, `graph_topological_kahn`, `sort_bitonic_sort`, `sort_radix_sort_lsd`, `str_group_anagrams`). The sign test is not significant at 0.05 (p = 0.064). The median gain (+0.039) is far below the mean (+0.095), so the mean is driven by a few large wins (`sort_pancake` +0.52, `math_fib_matrix` +0.46, `ds_min_heap_array` and `ds_ranked_set` +0.26).
- M_EX has high variance across programs (0.396–1.000). It is a frozen logistic model with several features (edit, exception fraction, call count, coverage size), fitted on V9c train (46 programs), so V5 and M_EX differ in flexibility.
- The pooled V5−M_EX delta is +0.106 with a cluster CI of [0.033, 0.186]. This contrast is **exploratory**: it is not in the frozen V10 Holm family (H1–H6), and the figure comes from the previous sprint and Agent 4's recomputation ([0.035, 0.184]). V5 vs M_EX+V5 is 12 wins and 7 losses (p = 0.36), and the pooled delta CI includes 0. The pooled M_EX+V5 − M_EX delta (H4) is +0.006, CI [−0.069, 0.068]. **H4 is not established.**
- These are exploratory per-program contrasts. The pre-declared confirmatory family used the pooled cluster bootstrap with Holm correction and is not replaced here.

## 4. Leave-one-program-out (LOPO)

| Predictor | LOPO min | LOPO max | Width |
|---|---|---|--:|
| V5 | 0.8922 (drop `ds_union_find`) | 0.9062 (drop `graph_topological_kahn`) | 0.014 |
| edit | 0.6133 (drop `math_coin_change`) | 0.6193 (drop `graph_cycle_detection_dfs`) | 0.006 |
| M_EX | 0.7812 (drop `sort_bitonic_sort`) | 0.8146 (drop `sort_pancake`) | 0.033 |

- Verified: V5 LOPO range is 0.8922–0.9062.
- V5−edit stays within +0.275 to +0.289 in every LOPO subset. V5−M_EX stays within +0.082 to +0.118 and is positive in all 19 subsets.
- Leave-two-out (171 subsets, previous sprint): V5 stays within 0.888–0.913. V5−M_EX is positive in 171 of 171 subsets.
- **What this shows:** no single program drives the pooled V5 AUROC or the V5−edit and V5−M_EX deltas. **What it does not show:** that the programs themselves are representative. LOPO is sensitivity to membership within one sample, not a generalisation test.

## 5. Within-program versus between-program concordance
A pooled AUROC compares every CHANGED pair with every EQUIVALENT pair. There are 101,761 such comparisons.

| Predictor | Within-program (n = 5,567; 5.47%) | Between-program (n = 96,194; 94.53%) | Pooled |
|---|--:|--:|--:|
| V5 | 0.8909 | 0.8971 | 0.8968 |
| edit | 0.6363 | 0.6149 | 0.6160 |
| M_EX | 0.7909 | 0.7908 | 0.7908 |

All three pooled values were recomputed as (within contribution + between contribution) and equal the frozen values. For V5, within-program comparisons contribute 0.0487 and between-program comparisons contribute 0.8480.

**Interpretation.**
1. V5's within-program concordance (0.891) and between-program concordance (0.897) are close, so the score is not working only because programs differ from each other in baseline level.
2. About 94.5% of the comparisons are cross-program, so the pooled AUROC is dominated by them. It is mostly a measure of whether a CHANGED variant of program A scores above an EQUIVALENT variant of program B. Those comparisons are largely correlated through shared programs and shared transformation families.
3. The pooled AUROC is therefore **not** 101,761 independent observations. The effective sample is closer to the 19 programs, or 319 matched sets, and certainly not the number of cross-label pairs.
4. The cleanest per-program estimate is the within-program AUROC. The unweighted mean of per-program AUROCs is 0.893 and the pair-weighted mean is 0.891.
5. Program-level attribution of V5's excess over chance is fairly even. The inverse-HHI effective number is 18.2 of 19, and the top three programs hold 19.8% of the excess.

## 6. Matched-set view and the edit-size caveat
Matched-set concordance compares a CHANGED variant with its own EQUIVALENT partner (319 sets), with ties counted as half:

| Predictor | Correct | Ties | Wrong | Concordance | 95% cluster CI |
|---|--:|--:|--:|--:|---|
| V5 | 284 | 26 | 9 | 0.931 | [0.897, 0.957] |
| edit | 292 | 25 | 2 | **0.955** | [0.934, 0.972] |
| M_EX | 271 | 3 | 45 | 0.854 | [0.748, 0.938] |

**Edit size scores higher than V5 in the matched-set metric.** In V10 the CHANGED variant is built by stacking a semantic change on a preserving transformation, so within a set it nearly always has the larger edit. The mean edit difference is 1.93, and the median and 75th percentile are 2. Pooled AUROC for edit size is only 0.616 because edit sizes are not comparable across sets and programs. When the comparison is restricted to equal edit size (8,605 comparisons), edit size is exactly 0.5 and V5 is 0.875. This is the right control and it is already frozen in `V10_INDEPENDENT_EVALUATION.json`. Any statement that V5 "beats edit size" must say which metric is meant: pooled AUROC (V5 0.897 vs 0.616), edit-size-controlled AUROC (V5 0.875 vs 0.5), or matched-set concordance, where edit size wins. The V8 negative result shows that edit-size confounding can reverse conclusions.

## 7. Where V5 is weak (descriptive)
- 34.6% of all pairs score exactly 0: 63.6% of EQUIVALENT pairs and 5.6% of CHANGED pairs. V5 is largely a sparse "any behavioural change seen" signal.
- SC-6 (value-only changes): 17 of 23 CHANGED variants (73.9%) score 0, with AUROC 0.451. This is the output-free design limit.
- SP-2 (rename) CHANGED-set partners: 32% score 0.
- Weakest programs are `graph_topological_kahn` (0.705), `sort_radix_sort_lsd` (0.745) and `str_group_anagrams` (0.789). The previous-sprint program-level Spearman correlation of V5 AUROC with the maximum V5 score among EQUIVALENT variants is −0.76 (n = 19). Programs where some preserving rewrite produces a large V5 value are the ones that fail. This is descriptive and not causal.

## 8. Limits of inference with 19 programs
1. **Independent units = 19 programs**, not 638 pairs, 319 sets or 101,761 comparisons. All uncertainty must be program-clustered. The frozen pooled V5 cluster-bootstrap CI is [0.8629, 0.9216] (half-width about 0.03; my 1,500-resample check gives [0.865, 0.922]). Deltas are wider: V5−edit [0.244, 0.308] and V5−M_EX [0.033, 0.186], so the V5−M_EX interval is about ±0.07.
2. **Programs are not a random sample of software.** They are author-selected, small algorithm implementations in five categories (ds/graph/math/sort/str). The 'single-function' and 'deterministic' properties were not verified here. Generalisation to a broader program population is an assumption, not a result.
3. **Same generator and author.** V10 uses the same variant generators and the same author as development (V8/V9). It is a held-out *program* test, not an independent benchmark. Transformations and labelling were also designed by the SBG authors.
4. **19/0 and 14/5 win counts are descriptive.** Sign tests treat programs as exchangeable. With 19 units, a p of 3.8e−6 for 19/19 is meaningful for the V5-over-edit comparison only because the effect is large and uniform. It does not license population claims.
5. **Category sub-groups are tiny** (ds 3, math 3, str 2, graph 4, sort 7), so no per-category inference is justified.
6. **Heterogeneity is real.** The per-program V5 AUROC ranges from 0.705 to 0.970. A random-effects reading puts the typical program at about 0.89 with a wide spread. The bootstrap resamples programs and so captures this spread, but 19 clusters make the percentile intervals themselves approximate.
7. **LOPO and leave-two-out** show stability to membership within this sample. They are not external validation.
8. **Multiple comparisons.** Per-program, LOPO, SC/SP-family and sub-group tables are exploratory and are not Holm-corrected. Only the pre-declared hypotheses H1–H6 (Holm over six) form the confirmatory family; H1, H2 and H3 are rejected, and H4, H5 and H6 are not.

## 9. Claim verification checklist

| Claim | Verified value | Source of verification |
|---|---|---|
| V5 beats edit in 19/19 programs | 19/0/0 | recomputed |
| Mean per-program gain ≈ +0.259 | +0.2592 | recomputed |
| V5 vs M_EX win/loss | 14/5 (p = 0.064) | recomputed |
| LOPO V5 0.8922–0.9062 | 0.892167–0.906182 | recomputed |
| Within-program concordance ≈ 0.891 | 0.890875 | recomputed |
| Between-program concordance ≈ 0.897 | 0.897109 | recomputed |
| ≈ 94.5% of cross-label comparisons are between programs | 96,194 / 101,761 = 94.53% | recomputed |
| V5 pooled 0.896768, edit 0.616046, M_EX 0.790789 | exact to 6 dp | recomputed |

Not independently recomputed here and taken from previous-sprint output files: leave-two-out ranges, program-level Spearman correlations, effective-n (inverse HHI) and the SC/SP-family tables. The H4 result comes from the frozen V10 JSON. The V5−M_EX pooled delta is not in the frozen JSON and is exploratory (see §3).

## 10. Bottom line
The V10 result is stable to dropping any one or any two programs, and V5's advantage over edit size holds in every program. V5's advantage over M_EX is positive on average but not uniform (14/5, sign test p = 0.064), and the incremental value of V5 over M_EX is not established. Because inference rests on 19 same-author programs, V10 supports a "held-out programs, same generator" claim. It does not support a claim of independent external validity.

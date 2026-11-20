# Agent 1 — Formal component ablation of SBG V5 (POST-HOC, EXPLORATORY)

Repo `SBG` @ `93ef3f3` (branch `remediation/sbg-v4`). Python 3.13.5, `PYTHONDONTWRITEBYTECODE=1`. Nothing was rescored, refit, or tuned. All inputs are frozen files read read-only; all outputs are in this directory.

**Status of every number below: exploratory, post-hoc.** The V10 and V9c-val results were already seen before this analysis, and the earlier forensic audit had already noted "state-only beats V5". These contrasts therefore cannot be treated as pre-declared. **No multiplicity-corrected confirmatory claim is made.** Holm adjustments across the three leave-one-out (LOO) contrasts are given as description only.

---

## 0. Bottom line (no spin)

1. **Provenance holds.** `0.50·V3 + 0.25·temporal + 0.25·state` reproduces stored `sbg_v5` on all 641 evaluated V10 rows and all 434 evaluated V9c-val/v8-val rows. Max |diff| = 7.5e-10, which is consistent with 9-decimal rounding of the stored values. There are no fallback, neutral-0.5, or clamped rows. The recomputed V10 AUROC is **0.896768 = the stored value, bit-identical**.
2. **State is the only component whose removal hurts V5 consistently in sign.**
   - Removing state lowers AUROC on V10 by 0.0146 (full − ablation = +0.0146, CI [+0.0059, +0.0237]).
   - Removing state also lowers AUROC on V9c-val by 0.0152 (full − ablation = +0.0152, CI [+0.0021, +0.0261]).
   - It lowers per-program AUROC in 11/19 programs (V10) and 9/11 (V9c-val).
3. **Removing temporal never lowers pooled AUROC.** It raises it by 0.0068 on V10 (CI of full − ablation [−0.0186, +0.0008], includes 0, raw p = 0.089) and by 0.0057 on V9c-val (CI of full − ablation [−0.0133, −0.0002], raw p = 0.045). In V10, temporal changes the per-program AUROC in only 7/19 programs.
4. **Removing V3 gives inconsistent results.** It raises AUROC on V10 by 0.0085 (raw p = 0.003) and is a null on V9c-val (AUROC falls by 0.0009; CI of full − ablation [−0.0227, +0.0289]). The per-program direction is heterogeneous.
5. **State alone is ≥ the composite on both populations.** The difference is clearly different from 0 on V10 (+0.0203, CI [+0.0069, +0.0387]). It is not distinguishable from 0 on V9c-val (+0.0110, CI [−0.0240, +0.0404]). I do **not** promote `sbg_state` or any ablation as a method. The weights were fixed a priori and were not tuned.
6. **The components are strongly redundant and zero-inflated.**
   - Pooled Spearman among components is 0.77–0.90 on V10.
   - Within a single class it falls to 0.52–0.83.
   - The zero patterns are almost nested. Temporal-nonzero implies V3-nonzero and state-nonzero on every one of the 638 V10 pairs.
7. **The effect sizes are small.** Every pooled AUROC difference between V5 and any LOO variant is ≤ 0.015 on V10 and ≤ 0.016 on V9c-val. The cluster counts are 19 and 11, so inference is thin (see §8).

---

## 1. Inputs, populations, provenance

### 1.1 Populations (reproduced exactly from the frozen evaluators)

| Population | Source of scores | Labels / groups | Filter | n pairs | programs | CH / EQ | matched sets |
|---|---|---|---|---|---|---|---|
| **V10 test** | `artifacts/final/pairs_v10_test_v6exp.jsonl` (644 rows, 641 evaluated, 3 unevaluated) | `benchmark/datasets/v10_independent/pairs_test.jsonl` (`semantic_relation`; EQ group = own `pair_id`, CH group = `matched_pair_id`) | replica of `evaluate_v10.py::stage_run`: evaluated rows; keep groups with exactly 2 members and both labels | **638** | 19 | 319 / 319 | 319 |
| **V9c val** | `pairs_v9c_val_output_free_v8.jsonl` (218 rows, 216 evaluated) plus the matched EQ rows from `pairs_v8val_output_free_v8.jsonl` | `v9_composed/pairs_val.jsonl` plus `v8/pairs_val.jsonl`; validity from `BENCHMARK_VALIDITY_AUDIT_V9C.json` and `..._V7ENTRY_ON_V8.json`; stale programs from `DIAGNOSTIC_V8_STALE_VARIANTS.json` | replica of `evaluate_v9.load` and `matched_complete` | **432** | 11 | 216 / 216 | 216 |

Both populations match the stored evaluation artifacts: V10 n = 638 / 319 sets / 19 programs; V9c-val n = 432 / 216 sets / 11 programs.

V10 has 644 dataset rows, of which 3 are unevaluated (`math_fib_matrix__sc4+sp2_s0`, `math_fib_matrix__sc5+sp2_s1`, `sort_stooge_sort__sc3+sp1_s2`). That leaves 641 evaluated rows, and 638 are in the matched-complete population. The 3 evaluated rows that drop out are, by the matching rule, the partners of the 3 unevaluated pairs (I checked the counts, not the individual ids).

### 1.2 Provenance check (task step 1) — PASSED

| Check | V10 (641 evaluated rows) | V9c val (434 evaluated rows in the union) |
|---|---|---|
| max abs diff, recomputed vs stored `sbg_v5` | **7.50e-10** | **7.50e-10** |
| rows with diff > 1e-9 | 0 | 0 |
| `v5_full` flag values | 1.0 on all 641 | 1.0 on all 434 |
| rows with any component outside [0, 1] | 0 | 0 |
| rows where the recomputed sum > 1 (clamp could bind) | 0 | 0 |
| rows with stored `sbg_v5` = 0.5 (neutral-failure value) | 0 | 0 |
| rows where "stored v5 = 0" and "all three components = 0" disagree | 0 | 0 |
| rows with all components = 0 | 222 | 162 |
| population AUROC, stored `sbg_v5` | 0.896768 | 0.751372 |
| population AUROC, recomputed from components | **0.896768** (unrounded 0.8967679169819479 for both; diff 0.0) | 0.751372 (unrounded 0.7513717421124828 for both) |
| cluster-bootstrap 95% CI (B = 2000, seed 42), library | [0.862918, 0.921553] | [0.706258, 0.793560] |
| stored value in `V10_INDEPENDENT_EVALUATION.json` / `V9_VAL_EVALUATION.json` | 0.896768 [0.862918, 0.921553] ✔ | 0.751372 [0.706258, 0.79356] ✔ |

In `experiments/final/extraction.py:523-524`, `v5_full` is `temporal_ok and state_ok`. When it is false, V5 falls back to `d_v3`. It is 1.0 on every row used, so **no V3-only fallback rows exist** in either population, and the three components are all genuinely available.

Frozen-file integrity: the sha256 of `pairs_v10_test_v6exp.jsonl` equals the one pinned in `FREEZE_V10_SCORED.json`. The sha256 values of `pairs_v9c_val_output_free_v8.jsonl` and `pairs_v8val_output_free_v8.jsonl` equal those pinned in `FREEZE_V9.json`.

The reimplementation also matches the library:
- My bootstrap CI for stored V5 equals `sbg.statistics.cluster_bootstrap_ci` to 6 decimals on both populations.
- My paired Δ (full − V3-only) equals `paired_cluster_bootstrap_delta` on both populations. For V9c-val this is 0.011456 [−0.00017, 0.021852], p = 0.055972, which is also the value stored in `V9_VAL_EVALUATION.json`.
- V9c-val component AUROCs and CIs equal the stored V3 = 0.739916, temporal = 0.618849 and state = 0.762367.
- V10 state-only equals the stored 0.9171 [0.893309, 0.937922].
- `V10_INDEPENDENT_EVALUATION.json` does not store V3 or temporal AUROCs. My V10 V3-only and temporal-only values **cannot be cross-checked against a stored value**. They come from the same code path as the cross-checked quantities.

---

## 2. Method

**Formulas.** The stored components are `d3` = `sbg_v3`, `dt` = `sbg_temporal` and `ds` = `sbg_state`. `S_w = w3·d3 + wt·dt + ws·ds`.

| Variant | (w3, wt, ws) | Same ranking as |
|---|---|---|
| full V5 | (0.50, 0.25, 0.25) | stored `sbg_v5` (verified) |
| V5 − V3 | (0, 0.25, 0.25) | the temporal+state pair |
| V5 − temporal | (0.50, 0, 0.25) | the V3+state pair |
| V5 − state | (0.50, 0.25, 0) | the V3+temporal pair |
| V3 only / temporal only / state only | (1,0,0), (0,1,0), (0,0,1) | the raw component |

**Normalisation rule.**
- **(a) Drop-term:** remove the term and keep the other weights unchanged. This is the primary form reported.
- **(b) Renormalised:** divide by the surviving weight sum. AUROC depends only on rank order, and multiplying by a positive constant preserves it. (a) and (b) are therefore rank-identical. I verified this numerically: |AUROC(a) − AUROC(b)| = 0.0 exactly, with the same number of distinct values, for all three LOO variants on both populations (`agent1_results.json → renormalisation_equivalence`). Renormalised weights would be (0, ½, ½), (⅔, 0, ⅓) and (⅔, ⅓, 0).
- **(c) Nothing is re-weighted or optimised.** The "2-component combinations" are exactly the three LOO variants, because 3 choose 2 = 3. They are not listed twice.

**Statistics.**
- AUROC is tie-aware (mid-rank Mann–Whitney), as in `sbg.statistics.auroc`. This matters because 35–58% of V10 scores are exactly 0.
- The CI is a percentile cluster bootstrap resampling base programs with replacement. B = 2000, seed 42, the same resample stream as the library.
- All variants are evaluated on the same resamples, so the Δ values are paired.
- Δ = AUROC(full) − AUROC(ablation).
- The two-sided bootstrap p is `min(1, 2·min(#Δ≤0, #Δ≥0 +1)/(B+1))` as in the library. Its floor is 0.000999.
- Holm over the 3 LOO contrasts is descriptive only.

---

## 3. Ablation AUROCs (task step 2)

95% CI = program-cluster bootstrap. ZR = exact-zero rate.

### V10 test (638 pairs, 19 programs)

| Variant | AUROC | 95% CI | ZR all / CH / EQ |
|---|---|---|---|
| **full V5** | **0.8968** | [0.8629, 0.9216] | 0.346 / 0.056 / 0.636 |
| V5 − V3 (temporal+state) | 0.9053 | [0.8691, 0.9331] | 0.447 / 0.072 / 0.821 |
| V5 − temporal (V3+state) | 0.9036 | [0.8774, 0.9241] | 0.346 / 0.056 / 0.636 |
| V5 − state (V3+temporal) | 0.8821 | [0.8401, 0.9129] | 0.356 / 0.066 / 0.646 |
| V3 only | 0.8817 | [0.8433, 0.9112] | 0.356 / 0.066 / 0.646 |
| temporal only | 0.8070 | [0.7246, 0.8805] | 0.583 / 0.273 / 0.893 |
| state only | **0.9171** | [0.8933, 0.9379] | 0.447 / 0.072 / 0.821 |

### V9c val (432 pairs, 11 programs)

| Variant | AUROC | 95% CI | ZR all / CH / EQ |
|---|---|---|---|
| **full V5** | **0.7514** | [0.7063, 0.7936] | 0.370 / 0.153 / 0.588 |
| V5 − V3 (temporal+state) | 0.7505 | [0.6893, 0.7979] | 0.498 / 0.255 / 0.741 |
| V5 − temporal (V3+state) | 0.7571 | [0.7133, 0.7962] | 0.370 / 0.153 / 0.588 |
| V5 − state (V3+temporal) | 0.7362 | [0.6939, 0.7776] | 0.407 / 0.171 / 0.644 |
| V3 only | 0.7399 | [0.6984, 0.7793] | 0.407 / 0.171 / 0.644 |
| temporal only | 0.6188 | [0.5551, 0.6972] | 0.736 / 0.607 / 0.866 |
| state only | 0.7624 | [0.6977, 0.8079] | 0.498 / 0.255 / 0.741 |

Observations:
- Every CI overlaps heavily with V5's, so the marginal CIs cannot separate the variants. Only the paired deltas in §4 are informative.
- Dropping temporal leaves the zero-pattern and distinct-value count of V5 unchanged on both populations (262 and 168 distinct values). The V5 − temporal zero rates are identical to V5's.
- This happens because **every pair with a nonzero temporal score also has nonzero V3 and state scores** in both populations.

---

## 4. Paired ΔAUROC (task step 3) — EXPLORATORY

Δ = AUROC(full V5) − AUROC(ablation). **Positive Δ means the removed component helps; negative Δ means removing it would have improved AUROC.**

| Pop. | Contrast | Δ | 95% CI | raw p (2-sided) | Holm over 3 LOO (descriptive) |
|---|---|---|---|---|---|
| V10 | full − (V5 − V3) | **−0.0085** | [−0.0158, −0.0027] | 0.0030 | 0.0060 |
| V10 | full − (V5 − temporal) | −0.0068 | [−0.0186, +0.0008] | 0.0890 | 0.0890 |
| V10 | full − (V5 − state) | **+0.0146** | [+0.0059, +0.0237] | 0.0010* | 0.0030 |
| V10 | full − V3 only | +0.0150 | [+0.0053, +0.0268] | 0.0010* | — |
| V10 | full − temporal only | +0.0898 | [+0.0318, +0.1539] | 0.0020 | — |
| V10 | full − state only | **−0.0203** | [−0.0387, −0.0069] | 0.0020 | — |
| V9c | full − (V5 − V3) | +0.0009 | [−0.0227, +0.0289] | 0.9985 | 0.9985 |
| V9c | full − (V5 − temporal) | −0.0057 | [−0.0133, −0.0002] | 0.0450 | 0.0900 |
| V9c | full − (V5 − state) | **+0.0152** | [+0.0021, +0.0261] | 0.0270 | 0.0810 |
| V9c | full − V3 only | +0.0115 | [−0.0002, +0.0219] | 0.0560 | — |
| V9c | full − temporal only | +0.1325 | [+0.0802, +0.1766] | 0.0010* | — |
| V9c | full − state only | −0.0110 | [−0.0404, +0.0240] | 0.4928 | — |

\* Equals the bootstrap p-value floor (≈ 0.001 with B = 2000). It is not a precise p-value.

Component-to-component Δ (`ablation_paired_deltas.csv`):

| Pop. | Contrast | Δ | 95% CI |
|---|---|---|---|
| V10 | state − V3 | +0.0354 | [+0.0168, +0.0592] |
| V10 | state − temporal | +0.1101 | [+0.0416, +0.1891] |
| V10 | V3 − temporal | +0.0747 | [+0.0180, +0.1369] |
| V9c | state − V3 | +0.0225 | [−0.0210, +0.0589] |
| V9c | state − temporal | +0.1435 | [+0.0694, +0.2051] |
| V9c | V3 − temporal | +0.1211 | [+0.0670, +0.1665] |

**Reading.**
- The only sign-consistent structural facts across the two populations are:
  - (i) removing state lowers AUROC;
  - (ii) removing temporal does not lower pooled AUROC;
  - (iii) temporal alone is clearly the weakest component.
- Fact (i) has raw p = 0.001 (V10) and 0.027 (V9c). Its Holm-adjusted p in V9c is 0.081, so it is **not** significant after adjustment there.
- Fact (ii) is borderline in both populations: raw p = 0.089 (V10) and 0.045 (V9c).
- Removing V3 improves V10 (raw p = 0.003, Holm-adjusted 0.006) and does nothing on V9c-val. Neither population gives support for "V3 is necessary".
- The best-V5-variant gain from dropping temporal and/or V3 is ≤ 0.016 AUROC in absolute terms.

---

## 5. Per-program effects (task step 4)

Programs are included where both classes are present: 19/19 for V10 and 11/11 for V9c. Δ_prog = AUROC_prog(full) − AUROC_prog(ablation). "Raises" means the ablation has a higher per-program AUROC than full V5. The sign-test p is descriptive only (ties dropped).

### V10 (19 programs)

| Ablation | raises | lowers | tied | mean Δ_prog (macro) | median | range | sd | sign-test p |
|---|---|---|---|---|---|---|---|---|
| V5 − V3 | 13 | 5 | 1 | −0.0098 | −0.0051 | [−0.0485, +0.0166] | 0.017 | 0.096 |
| V5 − temporal | 4 | 3 | **12** | −0.0083 | 0.0000 | [−0.0772, +0.0156] | 0.024 | 1.000 |
| V5 − state | 2 | **11** | 6 | +0.0127 | +0.0089 | [−0.0156, +0.0586] | 0.019 | 0.022 |
| V3 only | 2 | 11 | 6 | +0.0152 | +0.0055 | [−0.0178, +0.0886] | 0.026 | 0.022 |
| temporal only | 7 | 11 | 1 | +0.0795 | +0.0089 | [−0.0512, +0.4133] | 0.134 | 0.481 |
| state only | 13 | 5 | 1 | −0.0200 | −0.0051 | [−0.1559, +0.0269] | 0.043 | 0.096 |

Macro-mean per-program AUROC: full 0.8930; V5 − V3 0.9028; V5 − temporal 0.9013; V5 − state 0.8803; state only 0.9130.

### V9c val (11 programs)

| Ablation | raises | lowers | tied | mean Δ_prog | median | range | sd | sign-test p |
|---|---|---|---|---|---|---|---|---|
| V5 − V3 | 6 | 3 | 2 | +0.0033 | −0.0162 | [−0.0550, +0.1035] | **0.049** | 0.508 |
| V5 − temporal | 7 | 2 | 2 | −0.0119 | −0.0089 | [−0.0375, +0.0045] | 0.015 | 0.180 |
| V5 − state | 1 | **9** | 1 | +0.0158 | +0.0231 | [−0.0273, +0.0350] | 0.018 | 0.022 |
| V3 only | 3 | 7 | 1 | +0.0118 | +0.0231 | [−0.0273, +0.0320] | 0.021 | 0.344 |
| temporal only | 0 | 11 | 0 | +0.1282 | +0.1302 | [+0.0227, +0.2467] | 0.077 | 0.001 |
| state only | 6 | 4 | 1 | −0.0033 | −0.0194 | [−0.0900, +0.1230] | 0.070 | 0.754 |

Heterogeneity:
- Removing **V3** is heterogeneous on V9c-val. The per-program Δ (full − ablation) ranges from −0.055 to +0.104. Removing V3 lowers `ds_stack_min` by 0.103 and `graph_word_ladder` by 0.073, and raises `math_largest_rect_hist` by 0.055. The pooled V9c Δ of +0.0009 is a sum of opposing program-level effects, not a uniform null.
- Removing **temporal** is typically either a tie or a small improvement. On V10 it is tied in 12/19 programs, and it raises `graph_topological_kahn` by 0.077 (the largest single-program change). It lowers AUROC by at most 0.016 in any program.
- Removing **state** is the most uniform. Only 2/19 (V10) and 1/11 (V9c) programs improve.
- The per-program tables (`per_program_auroc.csv`) show the program-level mechanism. In `graph_topological_kahn` and `sort_radix_sort_lsd` (V10), V5 is clearly worse than state-only (0.705 vs 0.786, and 0.745 vs 0.901). These are the largest per-program gaps in favour of state-only. The leave-one-program-out check (below) shows the pooled sign does not depend on any single program.

**Leave-one-program-out sensitivity of the pooled Δ** (`lopo_sensitivity.csv`, `agent1_lopo.py`). Each program is dropped in turn, giving 19 and 11 values per contrast.

| Pop. | Contrast | pooled Δ | LOPO min | LOPO max | sign stable? |
|---|---|---|---|---|---|
| V10 | full − (V5 − V3) | −0.0085 | −0.0103 | −0.0074 | yes |
| V10 | full − (V5 − temporal) | −0.0068 | −0.0081 | −0.0036 | yes |
| V10 | full − (V5 − state) | +0.0146 | +0.0119 | +0.0159 | yes |
| V10 | full − state only | −0.0203 | −0.0236 | −0.0166 | yes |
| V9c | full − (V5 − V3) | +0.0009 | −0.0063 | +0.0068 | **no** |
| V9c | full − (V5 − temporal) | −0.0057 | −0.0076 | −0.0041 | yes |
| V9c | full − (V5 − state) | +0.0152 | +0.0132 | +0.0193 | yes |
| V9c | full − state only | −0.0110 | −0.0188 | −0.0035 | yes |

The LOPO range is narrower than the bootstrap CI, because it only measures sensitivity to deleting one program. It does not measure sampling error.

---

## 6. Component redundancy (task step 5)

Pooled correlations with program-cluster-bootstrap 95% CI (`redundancy_correlations.csv`):

| Pop. | Subset | V3~temporal ρ | V3~state ρ | temporal~state ρ | Pearson r (same order) |
|---|---|---|---|---|---|
| V10 | overall (n = 638) | 0.844 [0.771, 0.900] | 0.897 [0.866, 0.922] | 0.773 [0.638, 0.887] | 0.925 / 0.855 / 0.741 |
| V10 | CHANGED (319) | 0.829 [0.668, 0.903] | 0.796 [0.697, 0.867] | 0.518 [0.266, 0.734] | 0.905 / 0.749 / 0.578 |
| V10 | EQUIVALENT (319) | 0.611 [0.495, 0.709] | 0.630 [0.514, 0.734] | 0.796 [0.673, 0.899] | 0.938 / 0.896 / 0.909 |
| V9c | overall (432) | 0.749 [0.659, 0.819] | 0.781 [0.698, 0.848] | 0.682 [0.544, 0.804] | 0.902 / 0.780 / 0.647 |
| V9c | CHANGED (216) | 0.775 [0.662, 0.859] | 0.795 [0.715, 0.865] | 0.585 [0.408, 0.771] | 0.906 / 0.722 / 0.572 |
| V9c | EQUIVALENT (216) | 0.688 [0.609, 0.754] | 0.603 [0.465, 0.724] | 0.737 [0.599, 0.873] | 0.926 / 0.844 / 0.788 |

Mean of per-program Spearman ρ (a cluster-aware within-program summary). The CI is a program bootstrap of the mean. The count column is programs with a defined ρ (≥ 3 pairs and non-constant). Per-program values are in `agent1_results.json`.

| Pop. | Subset | V3~temporal | V3~state | temporal~state |
|---|---|---|---|---|
| V10 | overall | 0.828 [0.747, 0.890] (19/19) | 0.897 [0.869, 0.924] (19/19) | 0.769 [0.643, 0.877] (19/19) |
| V10 | CHANGED | 0.701 [0.588, 0.801] (19/19) | 0.770 [0.683, 0.842] (19/19) | 0.479 [0.291, 0.651] (19/19) |
| V10 | EQUIVALENT | 0.660 [0.569, 0.742] (15/19) | 0.693 [0.620, 0.769] (16/19) | 0.826 [0.726, 0.920] (15/19) |
| V9c | overall | 0.729 [0.649, 0.807] (11/11) | 0.743 [0.644, 0.823] (11/11) | 0.694 [0.584, 0.806] (11/11) |
| V9c | CHANGED | 0.736 [0.638, 0.830] | 0.770 [0.677, 0.849] | 0.628 [0.476, 0.774] |
| V9c | EQUIVALENT | 0.660 [0.588, 0.728] | 0.589 [0.436, 0.713] | 0.771 [0.635, 0.898] |

Reading: within-program correlations are similar to the pooled ones, so between-program differences are not what is driving the redundancy. Within-class ρ is clearly lower than overall ρ. Part of the overall ρ is therefore the shared CH-vs-EQ separation itself, and the class effect inflates correlation. Pearson r is much higher than Spearman ρ for V3~temporal on EQUIVALENT (0.94 vs 0.61 on V10). The large gap between the two coefficients suggests that a few large values and the many exact zeros drive Pearson; I did not test this.

Spearman ρ among pairs where both components are nonzero (V10, n = 266 / 347 / 266): V3~temporal 0.872; V3~state 0.756; temporal~state 0.693. On V9c-val (n = 114 / 201 / 114): 0.775; 0.719; 0.491.

### Exact zeros and their agreement (`zero_agreement.csv`, `zero_patterns.csv`)

| Pop. | Component | zero rate all | CHANGED | EQUIVALENT |
|---|---|---|---|---|
| V10 | V3 | 0.356 | 0.066 | 0.646 |
| V10 | temporal | **0.583** | 0.273 | 0.893 |
| V10 | state | 0.447 | 0.072 | 0.821 |
| V9c | V3 | 0.407 | 0.171 | 0.644 |
| V9c | temporal | **0.736** | 0.606 | 0.866 |
| V9c | state | 0.498 | 0.255 | 0.741 |

Zero-pattern counts (V3 zero, temporal zero, state zero), V10:

| Pattern | EQ | CH |
|---|---|---|
| none zero | 34 | 232 |
| only temporal zero | 20 | 61 |
| temporal and state zero | 59 | 5 |
| V3 and temporal zero (state nonzero) | 3 | 3 |
| all three zero | 203 | 18 |

Observations:
- The zero patterns are **almost nested**. On V10, temporal-nonzero implies V3-nonzero in 100% and state-nonzero in 100%, and state-zero implies temporal-zero. State is nonzero while V3 is zero in only 6 pairs, and V3 is nonzero while state is zero in 64 pairs (59 EQ, 5 CH).
- Agreement of V3 and state on being zero is 89% (Cohen κ = 0.77) on V10. Within CHANGED it is 97.5% (κ = 0.80). Within EQUIVALENT it is 80.6% (κ = 0.52). V9c: overall 83.6% (κ = 0.67).
- The **V3-nonzero / state-zero** group (59 EQ vs 5 CH on V10) is where V3 adds noise relative to state on V10. This is the group in which V5 assigns nonzero scores to equivalent pairs that state scores as exactly 0. It fits the observation that state-only beats V5 on V10. It is a descriptive pattern, not a causal test.
- On V9c val the same V3-nonzero / state-zero group (pattern: temporal zero, state zero, V3 nonzero) holds 22 CH vs 33 EQ, i.e. 40% CHANGED against 8% on V10 (5 of 64). In V9c-val, V3 therefore carries more CHANGED-specific signal that state misses. This is consistent with state-only not beating V5 there, but it is a descriptive contrast of two different benchmarks, not a test.

### Matched-set concordance (`matched_set_concordance.csv`)

Within each matched set, P(score of the CH member > score of the EQ member), ties counted ½, with a program-cluster bootstrap. This is the same definition as `evaluate_v9/v10.matched_concordance`, and the full-V5 value reproduces the stored values (V10 0.931034 [0.897213, 0.957295]; V9c 0.805556 [0.738208, 0.860619]).

| Variant | V10 concordance | V10 tied sets | V9c concordance | V9c tied sets |
|---|---|---|---|---|
| full V5 | 0.9310 [0.8972, 0.9573] | 8.2% | 0.8056 [0.7382, 0.8606] | 28.7% |
| V5 − V3 | 0.9326 [0.9040, 0.9563] | 8.5% | 0.7894 [0.7174, 0.8483] | 34.7% |
| V5 − temporal | 0.9467 [0.9257, 0.9632] | 8.2% | 0.8241 [0.7547, 0.8772] | 28.7% |
| V5 − state | 0.9216 [0.8857, 0.9516] | 10.0% | 0.7870 [0.7209, 0.8426] | 32.4% |
| V3 only | 0.9185 [0.8807, 0.9517] | 10.0% | 0.7778 [0.7136, 0.8333] | 32.4% |
| temporal only | 0.8307 [0.7484, 0.8997] | 27.6% | 0.6296 [0.5607, 0.7117] | 66.7% |
| state only | 0.9467 [0.9260, 0.9628] | 8.8% | 0.8032 [0.7284, 0.8604] | 34.7% |

Matched-set concordance gives the same ordering as pooled AUROC for temporal removal and state removal. The ordering for V3 removal differs between the two populations (V10: ≈ equal; V9c: lower). Each CH pair is compared with its own EQ partner here. The concordance values are directionally consistent with the AUROC findings for temporal and state removal. No paired test was run on them, so differences between variants in this table are descriptive only.

---

## 7. What cannot be established

1. **No confirmatory claim about components.** The contrasts were chosen after the V10 and V9c-val results and the "state-only" observation were known. No hypothesis of this kind was pre-declared or frozen. Holm across 3 contrasts does not repair this.
2. **Optimal or even better weights.** Dropping a term at the fixed remaining weights is not a weight search. These results say nothing about the best weights, and I do not infer that state-only, V5 − temporal or V5 − V3 is better "in general". The V10 gains of 0.007–0.020 AUROC come from choosing, after the fact, among ~6 variants; I did not quantify the resulting selection optimism.
3. **Generalisation.** The two populations have 19 and 11 clusters. V10's 19 programs are algorithmic siblings of development programs (see the independence caveat in `V10_INDEPENDENT_EVALUATION.json`). The V9c-val populations share the V9c generator design. Nothing here transfers to other languages, COBOL, or real bugs.
4. **Causal contribution of components.** An AUROC drop after removal is a statement about these frozen scores. It does not show the component's mechanism, because the components are highly correlated and nested in their zero patterns.
5. **Why the zero-pattern nesting occurs.** I only measured it empirically. I did not read or test the extraction code to find out whether it reflects a structural property, a shared trace-gating artefact, or a coincidence of these benchmarks.
6. **Effect of the weights on thresholded decisions.** AUROC is rank-only. Sensitivity/specificity at the frozen Youden thresholds were not recomputed for ablations, because the thresholds belong to V5 only. No new threshold was fit.
7. **Cross-check of the V10 V3-only and temporal-only values.** The stored V10 evaluation lacks them.
8. **Whether V9c-val's V3-removal null is real heterogeneity or noise.** The per-program Δ ranges over ±0.1, and the pooled estimate straddles 0 with sign instability in LOPO.
9. **The inference caveat on precision.** With 19 and 11 clusters, percentile bootstrap CIs are known to undercover (they are typically too narrow). Raw p-values at 0.001 are the floor, not estimates. Interpret all CIs as approximate and probably optimistic.

---

## 8. Reproduction (read-only on the repo; writes only into this directory)

```bash
cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/empirical_sprint_2026-11-04/agent_1
PYTHONDONTWRITEBYTECODE=1 /Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python agent1_ablation.py   # produces results, CSVs and input_hashes.json (about 15 s)
PYTHONDONTWRITEBYTECODE=1 /Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python agent1_lopo.py        # produces lopo_sensitivity.csv
```

The scripts use only the Python standard library plus `sbg.statistics` (a read-only import). Re-running `agent1_ablation.py` gave a byte-identical `agent1_results.json` and `ablation_auroc.csv`. No `make` target, `evaluate_*.py`, `score_*.py` or git-state-changing command was run. The scripts do not write outside this directory.

---

## 9. Input file hashes (SHA-256) — every file the scripts read

```
06840ff1c178a86acb0414e8a0abf99839e4208dfcb48c75a1c6ac2eee2792a1  artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json
e8f5cda03cea09b6e17d02e25cdfed975243440d9511cf327a9112efdda13ffc  artifacts/final/BENCHMARK_VALIDITY_AUDIT_V9C.json
169600ece7bb06c49c83b9ce7f2b60c764374e5e15d90da3f894da59f95b74a8  artifacts/final/FREEZE_V10_SCORED.json
19d4460ace0384e8892287075a9108d201a40d1c602a7f2f38ae972638968c8a  artifacts/final/FREEZE_V9.json
292233fe70000b8f60326da2e2a22b9a0613caa95d5cd5c186ee9e3f01e2d146  artifacts/final/pairs_v10_test_v6exp.jsonl
f6e1567efc60e8bd9c251511768f64510a169a0f53a1c1c9ffd382fd6b30cd0f  artifacts/final/pairs_v8val_output_free_v8.jsonl
3851fa752aef7062aa939da390509633814db5802effdb5f440d15e6555010bc  artifacts/final/pairs_v9c_val_output_free_v8.jsonl
309e06f4ee7a0b16192893e292865d0eb1eafbf200f0f4ad49e7733e3e333e81  artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json
2ea68537108c4038d9f095488bee6a92e92cbb779ced32c9a923d89093fc2cc5  artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json
7030d3a9063fa7dcdf562eb71e973a4f1ec12b2e64a29378b9dc43c1065d2f93  artifacts/paper_evidence/V9_VAL_EVALUATION.json
476c3efffcf4a20c9cf92212b932b03b29c64ca8e505742710a0da7555d53735  benchmark/datasets/v10_independent/pairs_test.jsonl
aa545bd1a86b6a452a65134769197f2f2c95e2bab26a9d46dcd46cac956e1366  benchmark/datasets/v8/pairs_val.jsonl
41f764b5ced50c4e7fe77ddf5b89a18878cd6aa5b3418cca9f54a0e1cb947b91  benchmark/datasets/v9_composed/pairs_val.jsonl
```

(Machine-readable copy: `input_hashes.json`. Paths are relative to the `SBG` repo root. I also read, but did not hash-pin in the scripts, the source files `experiments/final/evaluate_v9.py`, `experiments/final/evaluate_v10.py`, `sbg/statistics.py`, `sbg/v5/distance_v5.py` and `experiments/final/extraction.py`, for logic only.)

---

## 10. Files created (all in `.../SBG/paper/empirical_sprint_2026-11-04/agent_1/`)

| File | Content | SHA-256 |
|---|---|---|
| `agent_1_component_ablation.md` | this report | — |
| `agent1_ablation.py` | main analysis | `3b43b7460618fbf7dacdfe2423c13ce85a18f960b8232e003016ada771b36118` |
| `agent1_lopo.py` | leave-one-program-out sensitivity | `c6f69b6de6df4daed1731af1d3728ab399a04ef13cc6c54f8a2def3a84b0bb29` |
| `agent1_results.json` | full numeric results (provenance, ablations, deltas, per-program, correlations, zero patterns, concordance) | `2b97350e22448af89acd8275ee15c3ba2f8b0e33389d708f91cf2b0ea2818893` |
| `input_hashes.json` | SHA-256 of every input read | `b80a673f0b0cde237b1b56773ceb00fc77cc4457a3ec6cadaecb03e35e6a5b18` |
| `ablation_auroc.csv` | AUROC, CI and zero rates per variant and population | `f34e95c319bf0c56048bf96e882cfa93139a722fd0c1911d434043528e82f558` |
| `ablation_paired_deltas.csv` | paired ΔAUROC with CI, raw p and Holm (descriptive) | `27fad1b533fcce22d4dd76ac43b9a5fc003ed141902ad3416971f9726ad4bd3c` |
| `per_program_auroc.csv` | per-program AUROC for each variant | `78a1819971b391cfe3cbfe61a8cb8de5e365d338c56304d857be90ad9d45ccf8` |
| `per_program_effect_summary.csv` | per-program raise/lower counts and heterogeneity | `1da40740a9f373ec122f15091935bbdabfd88bcacb8dbe21acbc37f400e7b71a` |
| `redundancy_correlations.csv` | pooled and within-program correlations | `21be7910f1255cd5429fee187f0f7e898f413acd87120a326e726fd345037f4f` |
| `zero_patterns.csv` | zero-pattern counts by label | `b8dbe1cca2d740ee3fa837f2029062fdd948b1a5762bb4ebc41d322aeb3bcf36` |
| `zero_agreement.csv` | pairwise zero agreement, κ, Jaccard | `57eb1a8cdf7a79a6c9c135b97a6d8afa6135b3c20be7286dc84dece6cd48072b` |
| `matched_set_concordance.csv` | matched-set concordance per variant | `e3004d1b348c6dbc98ca2100ef1f72eae1abbbeb05f4e6b247ed3392754a33b9` |
| `lopo_sensitivity.csv` | leave-one-program-out Δ range | `1f987f63b49e4b34c34f6c323612c18b67e19aeb060e95d0f5bb494aa17584fb` |

No file outside this directory was written. The `git status` entries `?? artifacts/final/pairs_dev_output_free_v8.jsonl` (and 3 sibling untracked files) and the `?? paper/` directory existed before my work, and none of them came from my scripts.

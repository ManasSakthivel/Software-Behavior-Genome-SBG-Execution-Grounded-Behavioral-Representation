# Incremental contribution analysis (FINAL SPRINT, Part 1)

**Research question.** What does SBG contribute beyond (a) edit size and (b) edit size plus ordinary execution statistics?

**Verdict (stated first, as required).**

| Contribution | Status |
|---|---|
| SBG V5 beyond **edit size** | **Established** (V10 H2 +0.254, Holm-adjusted p = 0.005; V9c-val also supported). Caveat: V10 is same-author/same-procedure held-out data, not independent software. |
| SBG V5 beyond **edit size + execution statistics** (pre-declared H4) | **Not established** (V10 +0.006, 95 % CI [−0.069, +0.068], Holm p = 1.0; V9c-val +0.021, CI [−0.005, +0.048], p = 0.117). |
| Whether a *small* true increment (≲ 0.05–0.07 AUROC) exists | **Genuinely unresolved.** The CIs exclude increments ≥ ≈ 0.07 but not smaller ones; this is *not* evidence of equivalence. |
| SBG **alone** versus the frozen execution-statistics model `M_EX` | **Dataset- and fit-dependent** (post-hoc): V10 +0.106 [0.033, 0.186], but under an in-distribution refit the gap is +0.012 [−0.013, +0.033] (n.s.); V9c-val +0.094 [0.051, 0.131] under refit. |

Recommended framing: SBG is a *trace-derived representation that decisively out-discriminates edit size*, whose
separation from execution statistics computed from the same traces is not established; the paper should lead with this
and present the H4 null prominently, not in a footnote.

---

## 1. Frozen results (verified in this sprint)

All 42 frozen numbers (AUROCs, deltas, CIs, p-values, counts) were **re-derived independently** with
`experiments/final/sprint_incremental.py main` (seed 42, 2000 cluster bootstraps, the repository's
`sbg.statistics.paired_cluster_bootstrap_delta`) and compared against `V10_INDEPENDENT_EVALUATION.json`,
`V9_VAL_EVALUATION.json`: **42 / 42 match, 0 mismatches** (`INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json → S1_verification`).
No discrepancy with the numbers in the brief was found.

| Quantity | V9c validation (432 pairs, 11 programs) | V10 held-out (638 pairs, 319 matched sets, 19 programs) | Source |
|---|---|---|---|
| SBG V5 AUROC [95 % CI] | 0.751 [0.706, 0.794] | 0.897 [0.863, 0.922] | `V9_VAL_EVALUATION.json`, `V10_INDEPENDENT_EVALUATION.json` |
| Edit-size AUROC | – | 0.616 | V10 |
| `M_X` (exec. stats only) | – | 0.793 | V10 |
| `M_EX` (edit + exec. stats) | – | 0.791 [0.718, 0.851] | V10 |
| `M_E+V5` | – | 0.871 | V10 |
| `M_EX+V5` | – | 0.797 [0.669, 0.898] | V10 |
| H2: `M_E+V5` − `M_E` | – | **+0.254** [+0.218, +0.285], Holm p = 0.005 | V10 |
| H3: V5 − edit (forward) | – | +0.281 [+0.244, +0.308], Holm p = 0.005 | V10 |
| **H4: `M_EX+V5` − `M_EX`** | +0.021 [−0.005, +0.048], p = 0.117 | **+0.006 [−0.069, +0.068]**, Holm p = 1.0 | both |
| H5: V6 − V5 | – | +0.0029 [+0.0003, +0.0060], raw p = 0.030, Holm p = 0.090 → **not rejected** | V10 |

(The raw CI for H5 excludes 0 but Holm does not reject; V6 superiority is not established. Absolute size ≈ 0.003 AUROC.)

BugsInPy / QuixBugs were verified against `EXTERNAL_RESCORE_V8.json`: **BugsInPy 0.4159 (all pairs), 0.497 (excl. SP-2)**,
**QuixBugs canonical 0.3842 (all), 0.444 (excl. SP-2)**. The brief's 0.497 and 0.444 are the SP-2-excluded subsets;
both all-pairs values are below 0.5. They were not recomputed here (they come from the frozen external rescore).

## 2. Baseline definitions (exact) and implementation verification

Models are L2-regularised logistic regressions (`evaluate_v9.fit_logistic`, L2 = 1.0, lr 0.5, 5000 iterations, features
standardised), **fitted on v9c train only (46 programs, 1650 pairs)** and frozen in `V10_MODELS_FROZEN.json`
(`scored_v6exp_sha256 515eceee…`); the model score is the logit.

| Model | Features | Source of features |
|---|---|---|
| `M_E` | `edit` (normalised-source token edit size) | `edit_size_analysis._edit_size` |
| `M_X` | `exception_fraction`, `call_count`, `coverage_size` | `extraction.score_pair` (`_ratio_distance` of trace-derived counts) |
| `M_EX` | `edit` + the three above | – |
| `M_E+V5` | `edit`, `sbg_v5` | `sbg_v5 = 0.50·V3 + 0.25·temporal + 0.25·state` |
| `M_EX+V5` | `edit`, `sbg_v5`, the three execution statistics | – |

Standardised weights of `M_EX+V5` (frozen): edit +0.109, `sbg_v5` +1.259, `exception_fraction` −0.054, `call_count`
**−0.883**, `coverage_size` +0.192; `M_EX`: edit +0.003, exception +0.404, `call_count` −0.122, `coverage_size` +0.503.

Verification (done by reading the code and re-running, not by trusting test status):

1. **Labels/pairs compatible.** All models score the same 638 pairs (matched-complete: every group has exactly one
   CHANGED and one EQUIVALENT member), rebuilt by `sprint_common.py` exactly as `evaluate_v10.stage_run` does.
2. **Splits.** Models fitted on v9c train only; V10 programs overlap with **0** of the programs used to fit them; v9c
   val and train are disjoint; V10 shares no program with any v8/v9 split.
3. **No label-derived feature.** The five feature families are functions of the two programs' traces (or token edit
   size). The oracle label (`dynamic_oracle`: outputs on protocol inputs) enters only the `label` column.
4. **Fair baseline.** The execution statistics are derived from the *same traces* as SBG (not a handicapped subset);
   `M_EX` is fitted by the same optimiser on the same data as `M_EX+V5`; nothing was weakened or tuned to favour SBG.
5. **Paired comparison.** Differences use `paired_cluster_bootstrap_delta` (resamples programs, recomputes both AUROCs on
   the same resample), 2000 resamples, seed 42; Holm over the six pre-declared V10 hypotheses.
6. **Reproducible.** `python experiments/final/sprint_incremental.py main` regenerates the 42 checks.

Observation: the combiner `M_EX+V5` does not transfer cleanly (see §4) — a property of fitting on v9c and scoring on
a different program population, which the frozen protocol does not repair.

## 3. New analyses (all **exploratory / post-hoc**; they do not alter any frozen result)

Commands:

```bash
cd experiments/final
PYTHONHASHSEED=0 ../../../venvs/py313/bin/python sprint_incremental.py main   # -> INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json
PYTHONHASHSEED=0 ../../../venvs/py313/bin/python sprint_incremental.py lopo   # -> INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json
```

### A — Where does SBG help over edit size? (V10, 319 matched sets)

Matched-set concordance = fraction of sets in which the CHANGED variant outscores its EQUIVALENT partner (ties 0.5).

| Family (n sets) | SBG V5 | `M_EX` | edit |
|---|---|---|---|
| SC-1 (34) | 1.00 | 0.62 | 0.84 |
| SC-2 (57) | 0.965 | 0.86 | 0.92 |
| SC-5 (63) | 0.936 | 0.89 | 0.98 |
| SC-11 (67) | 0.993 | 0.94 | 0.99 |
| SC-13 (35) | 0.886 | 0.86 | 0.94 |
| **SC-6 (23)** | **0.50** | 1.00 | 1.00 |
| SP-1 (48) | 0.99 | 0.77 | 0.90 |
| SP-3 (55) | 0.973 | 0.78 | 1.00 |
| **SP-2 (53)** | **0.83** | 0.94 | 1.00 |
| **SP-8 (18)** | **0.64** | 0.89 | 0.94 |

(Full table, other SC/SP families and counts: `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json → V10_A_where_does_sbg_help`.)

* SBG's gains over `M_EX` are in families where decoration changes coverage/call statistics without changing behaviour
  (SP-1, SP-3, SC-1). SBG is **worse** than both baselines where the behaviour change does not alter the trace (SC-6) and in
  two restructuring families (SP-2 rename, where SBG is exactly 0 on 32 % of CHANGED pairs, and SP-8 extract-function); the SP-2 mechanism was not investigated.
* Edit-size bins (CHANGED vs EQUIVALENT within a bin): 3–5 [n = 133]: SBG 0.816, `M_EX` 0.761, edit 0.549; 6–10 [243]:
  0.961 / 0.802 / 0.500; 11–20 [153]: 0.878 / 0.749 / 0.412; 21–40 [43]: 0.878 / 0.630 / 0.718. (0–2 and 41+ contain a
  single class.)
* Pair 2×2 (CHANGED, n = 319): SBG non-zero & exec-stat non-zero 293; SBG only 8; exec-stat only **0**; neither 18.
  EQUIVALENT (n = 319): both non-zero 113; SBG only 3; exec-stat only 0; neither 203.
  → SBG is non-zero on a superset of the pairs where execution statistics are non-zero. Sensitivity (eight extra changed
  pairs) is small; the difference is in the *magnitude/ranking*, not in coverage of detectable changes.
* Subgroup counts are small (SP-8: 18 sets; SC-10: 16) and none is a confirmatory test.

### B — After controlling for edit size

* Frozen: V10 exact-edit-stratified AUROC (only pairs with equal edit size compared; 8605 cross-label comparisons):
  SBG V5 **0.875**, edit 0.500.
* Exploratory additions (V10 / V9c-val):

| | V10 | V9c-val |
|---|---|---|
| Stratified AUROC: SBG V5 | 0.875 | 0.7355 |
| Stratified AUROC: `M_EX` | 0.764 | 0.598 |
| Stratified AUROC: `coverage_size` | 0.736 | 0.614 |
| V5 − `M_EX`, stratified, paired | +0.111 [0.008, 0.205], p = 0.028 | +0.138 [0.078, 0.207], p = 0.001 |
| `M_EX+V5` − `M_EX`, stratified, paired | −0.021 [−0.112, 0.051] | **+0.062 [0.015, 0.112], p = 0.021** (uncorrected) |

* Window sweep (|Δedit| ≤ 0..3): V10 SBG 0.87–0.90, V9c-val 0.74–0.78: stable.
* Matched sets with equal edit size: V10 n = 25, concordance SBG 0.96, `M_EX` 0.70, edit 0.50; V9c-val n = 27, SBG 0.59, `M_EX` 0.48.
* Conclusion: SBG continues to discriminate when edit size is controlled (it was designed so: ≈ 92 % of V10 sets have a
  CHANGED variant with the larger edit, mean gap +1.9 tokens, so exact stratification is the proper control). The only
  nominally significant increment over `M_EX` anywhere in these analyses is the V9c-val stratified `M_EX+V5` − `M_EX`
  (+0.062, p = 0.021); it is one of many exploratory comparisons in this sprint, is not corrected for multiplicity, and is not replicated
  in V10 (−0.021). **It must not be reported as evidence of an increment.**

### C — Why is the incremental value small?

Evidence for and against each candidate explanation:

| Explanation | Evidence | Assessment |
|---|---|---|
| SBG captures information already in execution statistics | pooled Spearman ρ(SBG V5, `M_EX`) = 0.64 (V10), 0.68 (V9c); ρ(V5, `coverage_size`) 0.75, (V5, `call_count`) 0.70; SBG non-zero ⊇ exec-stat non-zero (2×2 above) | **Partially supported** (substantial overlap) |
| Representations overlap but each has unique content | SBG alone > `M_EX` in V10 (+0.106) and in 14 / 19 programs; `M_EX` > SBG in `graph_alien_dict` (1.0 vs 0.88) | **Supported** (neither dominates) |
| Task does not expose a distinctive SBG advantage | SC-6 / SP-2 families favour execution statistics or edit; SBG advantage is concentrated in SP-1/SP-3/SC-1 | **Partially supported** |
| CI too wide to separate small effect from none | H4 CI half-width ≈ 0.07 (V10) and ≈ 0.026 (V9c-val); V9c-val point estimate +0.021 | **Supported** |
| Combiner transfer / methodological factor | below | **Supported — strongest single factor** |

**The combiner-transfer finding (most important).** `M_EX+V5` (V10 AUROC 0.797) is *worse than SBG alone* (0.897): V5 −
`M_EX+V5` = +0.100 [−0.009, +0.235], p = 0.083. The v9c-fitted combiner puts +1.259 on `sbg_v5` and −0.883 on
`call_count`, two correlated features, a pattern that fits v9c but harms ranking on some V10 programs
(`ds_ranked_set`: M_EX+V5 − M_EX = −0.42; `sort_pancake`: −0.33; 12 programs gain > 0.02, 2 lose > 0.02, 5 within ±0.02;
mean per-program Δ = +0.0096). Matched-set transitions M_EX → M_EX+V5: 11 improve, 3 half-improve, 11 worsen, 260 stay correct,
34 stay wrong. Gains and losses cancel.

**Leave-one-program-out refit (exploratory sensitivity, 2 models only, specified before running).** Each program is
scored by a model fitted on all *other* programs of the same set, with the frozen optimiser:

| Set | LOPO `M_EX` | LOPO `M_EX+V5` | SBG alone | LOPO increment from V5 | SBG alone − LOPO `M_EX` |
|---|---|---|---|---|---|
| V10 | 0.885 [0.850, 0.917] | 0.895 [0.864, 0.921] | 0.897 | +0.0103 [−0.0017, +0.0220], p = 0.090 | +0.012 [−0.013, +0.033], p = 0.32 |
| V9c-val | 0.658 [0.613, 0.707] | 0.673 [0.617, 0.729] | 0.751 | +0.015 [−0.031, +0.058], p = 0.47 | **+0.094 [0.051, 0.131], p = 0.001** |

Interpretation: once the execution-statistics model is refit on in-distribution data its V10 AUROC rises from 0.79 to
0.885, almost equal to SBG. **SBG's V10 advantage over the *frozen* `M_EX` is therefore largely a transfer artefact of
the v9c fit**, not a feature advantage. On the harder V9c-val set SBG alone does keep a clear advantage (+0.094) over a
refit `M_EX`. The LOPO increment from adding V5 is +0.010 to +0.015 in both sets — small, positive, not significant.

### D — Redundancy

* Within-CHANGED Spearman (V10): V5 ~ `call_count` 0.66, ~ `coverage_size` 0.65, ~ `exception_fraction` 0.25, ~ edit 0.18.
* Component behaviour: V9c-val AUROCs state 0.762, V5 0.751, V3 0.740, temporal 0.619; in V10 state alone is 0.917 (> V5 0.897).
* Where adding SBG changes rankings: Cases 4a/4b in `REPRESENTATION_CASE_STUDIES.md`: mechanisms are the negative
  `call_count` weight and the dead-code-inflated `coverage_size`, not a distinct information channel.
* Correlation alone does not show equivalence; the evidence for overlap is the combination of correlations, the 2×2
  table and the LOPO result.

**What the data can and cannot distinguish.** They support "substantial overlap + a combiner that does not transfer +
wide CIs". They cannot distinguish *no true increment* from *a true increment of ≲ 0.05–0.07 AUROC*. They are **not**
evidence that SBG and execution statistics are equivalent.

## 4. Deviations from the original protocol

* No frozen artefact, label, metric, or hypothesis was altered; all frozen numbers were recomputed and agree.
* All analyses in §3 are post hoc and were run after V10 and V9c-val had been opened; they are labelled exploratory and
  are not part of the Holm family. They cannot be used as confirmation.
* One model family beyond the frozen set was fitted (LOPO `EX`, `EX+V5` — exactly two, specified in the script
  docstring before running). No feature-subset search was performed.
* The LOPO scheme fits on test-set programs (other programs of the same set, never the scored program). It measures
  *attainable* execution-statistics performance on the V10 distribution, not frozen-protocol performance.

## 5. What the paper may and may not claim

**May claim** (with the dataset caveat for V10):
* SBG V5 discriminates behaviour-changing from behaviour-preserving transformations far better than edit size
  (V10 0.897 vs 0.616; H2 +0.254, Holm-supported) and when edit size is exactly controlled (0.875 vs 0.500).
* Execution statistics from the same traces are a strong baseline (V10 0.79 frozen, 0.885 refit); adding SBG did not
  yield a statistically established improvement (+0.006, +0.021).
* SBG alone is nominally better than the frozen `M_EX` in V10 (post hoc) but this narrows to +0.012 n.s. under an in-
  distribution refit.

**May not claim:**
* That SBG "adds predictive value beyond execution statistics", or that the V10/V9c increments "approach significance".
* That the null shows SBG and execution statistics are equivalent.
* That V6 is better than V5 (Holm p = 0.090).
* That V10 is independently authored.
* Real-bug detection (BugsInPy/QuixBugs ≈ 0.5 or below).

## 6. Tables/figures for the manuscript

* **Table 1**: AUROC (with CI) for edit, `M_X`, `M_EX`, SBG V5, `M_E+V5`, `M_EX+V5` on V9c-val and V10.
* **Table 2**: pre-declared deltas H2/H3/H4/H5 with Holm-adjusted p, **including the H4 null in the main text**.
* **Figure 1**: forest plot of the paired deltas (H2, H3, H4, H5; LOPO increment) with 95 % CIs, marking frozen vs exploratory.
* **Table 3** (exploratory): LOPO sensitivity (above).
* **Table 4** (exploratory): family-level concordance (SBG vs `M_EX` vs edit) showing both wins (SP-1/SP-3) and losses (SC-6/SP-8).
* **Figure 2**: per-program `M_EX+V5` − `M_EX` (12 up, 2 down, 5 flat) to show heterogeneity.

## 7. Machine-readable results

* [`INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`](INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json)
* [`INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json`](INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json)
* Frozen sources: `V10_INDEPENDENT_EVALUATION.json`, `V10_POSTHOC_SUPPLEMENT.json`, `V9_VAL_EVALUATION.json`, `V10_MODELS_FROZEN.json`, `EXTERNAL_RESCORE_V8.json`.

# 07 — Experimental Integrity and Statistical Verification Audit (Agent A3)

Repo commit audited: `3425693b432bb774b10db1cf3185eae1a7eef095` (read-only). All code: pure stdlib, written by A3, in `experiments/statistical_verification/`.
Registry: `logs/registry/A3_stats.jsonl` (15 entries, EXP-A3-001 … 014). Python: `venvs/py313`, `PYTHONHASHSEED=0`.

---------------------------------------------------------------------------------------------------------------------------------

## 1. VERDICT

1. **Every reported V10, V9c-val and V8-test number reproduces exactly from raw data.** 522 quantities were compared (310 V10, 179 V9c-val, 33 V8-test): AUROC, PR-AUC, bootstrap CIs, sensitivity/specificity, zero-rates, H1 permutation p, all ΔAUROC with CI and p, Holm, stratified AUROC, concordance, per-program AUROC. **Maximum absolute discrepancy = 0.0** at the reported precision (EXP-A3-002). The bootstrap CIs are digit-identical because the repo's RNG call order was re-implemented. Populations (644→641→638, 436→434→432, V8-test 956/22 programs) are identical to `configs/populations/*` (EXP-A3-001). The four external AUROCs also reproduce (EXP-A3-007).
2. **Thresholds and weights have no leakage.** 21 Youden thresholds and 10 logistic combiners were recomputed/refit with my own code on V9c-train only. Max |Δ| = 0.0 (EXP-A3-006). The 34 sha256 pins in FREEZE_V9/V10/V10_SCORED all match the working tree (EXP-A3-012).
3. **V10 labels are clean (0/638 label errors).** Re-checked by observable outputs in independent trace dumps: 319/319 CHANGED differ, 322/322 EQUIVALENT are identical to base. The dumped SBG scores equal the frozen scored file (641 pairs, max diff 0.0) (EXP-A3-008).
4. **V9c-val labels are NOT clean** (PRESENT-MAJOR, EXP-A3-008/009/010):
   - 16 of 216 EQUIVALENT pairs (7.4 %: SP-8 ×10, SP-11 ×6) have *different outputs* from their base.
   - 67 of 216 CHANGED pairs (31 %) show no difference in return value, exception, stdout *or argument mutation* on the protocol inputs.
   - The V9c validity audit is static ("executes nothing"), so it cannot catch either defect.
   - The repo's own `EQUIVALENT_LABEL_AUDIT.json` lists the same 16. The reported V9c-val analysis still includes them.
   - Noise is conservative for AUROC: V5 goes from 0.751 to 0.849 on the 266-pair clean subset. No conclusion flips (H4 stays n.s.).
5. **H4 (incremental value of SBG over execution statistics) is inconclusive, not evidence of no gain.**
   - V10 H4: Δ = +0.0063, 95 % CI [−0.069, +0.068]. The minimum detectable ΔAUROC at 80 % power is about 0.10, so the CI cannot exclude a gain of +0.068 or a loss of −0.069. The tightest TOST-style equivalence bound the data support is about ±0.06.
   - V9c-val H4: Δ = +0.021, CI [−0.005, +0.048]. MDE about 0.038; supportable equivalence bound about ±0.044.
6. **Other threats (details in §3):**
   - Pooled CIs are anti-conservative if the unit is not the program. For the H4 delta the matched-set bootstrap SD is 2.6× smaller than the program-cluster SD.
   - 19 clusters is a small number for percentile-bootstrap coverage.
   - V10 has pseudo-replication: 212 rows sit in 84 groups of AST-identical variants.
   - The "size-matched" claim holds only for *pooled* AUROC. Inside matched sets CHANGED has the larger edit in 292/319 sets, and edit-size matched-set concordance (0.955) exceeds V5's (0.931).
   - V10 "independence" is weaker than a fresh-corpus claim suggests. All 19 programs failed the novelty rule for V8; 16/19 still exceed 0.10 repo-style Jaccard against some V8/V9c program (max 0.225).
   - The git chronology of "frozen before scoring" is unprovable from git alone (single commit c5bc130).
7. **Not done / limits:** see §8. The orchestrator trace cache was incomplete, so A3 dumped the missing programs into its own directory. V8-test labels were never audited by the repo and I did not re-audit them (no trace cache for V8).

---------------------------------------------------------------------------------------------------------------------------------

## 2. VERIFICATION OF REPORTED NUMBERS (EXP-A3-002; script `exp_a3_002_reconstruct.py`; comparison CSVs `results/tables/EXP-A3-002_*_comparison.csv`)

Reported source for V10 = `SBG/artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json`, V9c-val = `V9_VAL_EVALUATION.json`, V8-test = `V8_TEST_EVALUATION.json`.

| Quantity | Task-stated | Independent (A3) | Repo JSON | |Δ| |
|---|---|---|---|---|
| V10 programs / pairs / matched sets | 19 / 638 / 319 | 19 / 638 / 319 | same | 0 |
| V10 SBG V5 AUROC [CI] | 0.897 [0.863, 0.922] | 0.896768 [0.862918, 0.921553] | same | 0 |
| V10 edit (forward) | 0.616 | 0.616046 | same | 0 |
| V10 M_EX | 0.791 | 0.790789 | same | 0 |
| V10 M_EX+V5 | 0.797 | 0.797088 | same | 0 |
| V10 H1 perm p (Holm) | — | 0.0005 (0.003) | same | 0 |
| V10 H2 (M_E+V5 − M_E) | +0.254 | +0.254498 [0.2178, 0.2851] | same | 0 |
| V10 H3 (V5 − edit) | +0.281 | +0.280721 [0.2435, 0.3081] | same | 0 |
| V10 H4 (M_EX+V5 − M_EX) | +0.006, CI [−0.069, +0.068], Holm 1.0 | +0.006299 [−0.068992, +0.068029], p .8086, Holm 1.0 | same | 0 |
| V10 H5 (V6 − V5) | +0.0029, p .030, Holm .090 | +0.002889, p .029985, Holm .089955 | same | 0 |
| V10 H6 (M_EX+V6 − M_EX) | +0.0085 | +0.008481, p .7696, Holm 1.0 | same | 0 |
| V10 sbg_state / coverage / exception_fraction / call_count | 0.917 / 0.779 / 0.701 / 0.692 | 0.9171 / 0.7790 / 0.7006 / 0.6920 | same | 0 |
| V10 static AST / token | 0.591 / 0.582 | 0.5915 / 0.5816 | same | 0 |
| V9c-val: programs / pairs | 11 / 432 | 11 / 432 (216 sets) | same | 0 |
| V9c-val V5 [CI] | 0.751 [0.706, 0.794] | 0.7514 [0.706258, 0.793560] | same | 0 |
| V9c-val H2 / H3 | +0.112 / +0.140 | +0.112183 / +0.140228 | same | 0 |
| V9c-val H4 [CI], Holm p | +0.021 [−0.005, +0.048], .117 | +0.021016 [−0.005376, +0.048067], .116942 | same | 0 |
| V8-test V5 [CI] | 0.694 [0.659, 0.727] | 0.6937 [0.659291, 0.726558] | same | 0 |
| V8-test reversed edit-size | 0.876 | 0.8759 [0.858786, 0.891749] | same | 0 |
| BugsInPy committed v7 / v8-rescore SP-2-excluded | 0.410 / 0.497 | 0.4099 [0.3262, 0.4939] / 0.4970 [0.4023, 0.5956] | `EXTERNAL_RESCORE_V8.json` | 0 |
| QuixBugs committed v7 (152) / v8-rescore SP-2-excluded | 0.388 / 0.444 | 0.3877 [0.2847, 0.5034] / 0.4444 [0.3553, 0.5385] | `DIAGNOSTIC_EXTERNAL.json`, `EXTERNAL_RESCORE_V8.json` | 0 |

**Cosmetic deviations (not errors):**
- Holm-adjusted H1 = 0.003 only if the raw permutation p (0.00049975) is first rounded to 6 digits and then to 0.0005. The script does this.
- The `configs/populations` V9c files hold unrounded static scores. The repo uses 9-digit rounding. Difference ≤ 5e-10.
- Many p-values are the Monte-Carlo floor 0.001 (2/(B+1)). H1's 0.0005 is the permutation floor (1/(B+1)). "p < .001" is the only supportable statement for those.

**Statistical assumptions of the reported analysis (verified from `sbg/statistics.py`, re-implemented):**
- Resampling unit = program (base_id). Percentile CI. B=2000, seed 42.
- Paired ΔAUROC two-sided bootstrap p = 2·min(P(Δ≤0), P(Δ≥0)) with the (k+1)/(B+1) correction.
- H1 permutes labels *within* program.
- Holm over H1–H6 (V10) and H1–H4 (V9c-val).
- Ties in AUROC get half credit (important: 63.6 % of EQ and 5.6 % of CH V5 scores in V10 are exact 0).

---------------------------------------------------------------------------------------------------------------------------------

## 3. INTEGRITY THREAT REGISTER

| # | Threat | Rating | Evidence (EXP / file) |
|---|---|---|---|
| T1 | Reported numbers not reproducible | **NOT-PRESENT** | 522/522 match, max Δ 0.0 (A3-002) |
| T2 | Threshold selection on test data | **NOT-PRESENT** | 21/21 Youden thresholds and 10/10 model fits identical to V9c-train recomputation (A3-006) |
| T3 | Weights/feature-set tuned after seeing V9c-val / V10 | **NOT-PRESENT** for fitted models/V5 constants vs V9c-val/V10 data; **PRESENT-MINOR** for chronology and for provability on the older `base_programs` corpus | V5 weights 0.50/0.25/0.25 were introduced as constants in 4409652 (2026-08-21, before any fresh-program data) and are never changed; M_EX features are in `EVALUATION_PLAN_V9.md` line 46, committed with FREEZE_V9. Sub-point: FREEZE_V10 admits that the forward edit AUROC (0.616) and mean edit sizes were inspected before freezing. Sub-point: freeze + scored file + evaluation are one commit (c5bc130), so "frozen before scoring" rests on self-reported `written_at` timestamps (A3-012) |
| T4 | Pair duplication / pseudo-replication | **PRESENT-MINOR** (V10), see T6 for V9c | V10: no duplicate pair_id or (base, variant) paths; no variant == base; no cross-design variant reuse; 1–1 EQ↔CH partner bijection. But 84 variant-AST groups cover 212 rows (161 EQ, 51 CH, none mixed-label). De-duplicating on (program, label, AST) leaves 511 rows: V5 0.897→0.884, edit 0.616→0.580, M_EX 0.791→0.761, M_EX+V5 0.797→0.786. Differences lie inside the CIs (A3-004/004b) |
| T5 | V10 label errors | **NOT-PRESENT** | 0/638 (A3-008). Caveat → T5b |
| T5b | V10 oracle uses the same protocol inputs SBG executes, so every CHANGED pair is *guaranteed* output-observable on SBG's inputs | **PRESENT-MINOR** (construct validity) | A3-008. 17 SP-8 and 15 SP-11 candidates were rejected by the oracle, so the surviving EQ set is selected |
| T6 | V9c label noise | **PRESENT-MAJOR** (V9c-val and train/dev as reference) | 16/216 EQ (SP-8 ×10, SP-11 ×6) differ in output; 67/216 CH (31 %) with no observable diff and not AST-equal to base (A3-008/009). 18/216 CH have the same AST as an EQ of the same program (no-op SC composed with SP, in 6 programs; A3-004b). Effect on conclusions: conservative (A3-010) |
| T7 | Program / source leakage V9c/V8 → V10 | **NOT-PRESENT** | 0 shared base_id, byte-hash, AST-hash; 0 variant-AST overlap (A3-004, A3-011) |
| T7b | Algorithmic similarity ("independence") | **PRESENT-MINOR** | Own repo-style identifier Jaccard of each V10 program vs V8/V9c programs: median 0.13, max 0.225 (`math_coin_change` vs V9c-val `math_ways_to_change`); 16/19 > 0.10, 7/19 > 0.15. V8/V9c programs vs each other have median 0.019 / p95 0.086. All 19 were flagged ineligible by the repo's own novelty rule (vs corpus/v6 siblings, 0.101–0.146). No near-duplicates: max 5-gram shingle Jaccard 0.39 and max AST-3-gram 0.61 (V9c internal max 0.69). BugsInPy/QuixBugs max repo-style Jaccard 0.17 (A3-011). Same author/generator family (self-disclosed in FREEZE_V10) |
| T8 | Statistical dependence / wrong unit | **PRESENT-MINOR** as done in the repo (program clusters are the right unit); **PRESENT-MAJOR** if pair- or set-level CIs are quoted | A3-003: V5-state ΔCI and H4 ΔCI widths by unit: set 0.055, pair 0.063, program 0.137, two-stage 0.157. Set-level H4 p = .62 vs program-level .81. Set-concordance ICC(1) of V5 0.05 (design effect 1.78); score-difference ICC 0.40 (DE 7.3); M_EX ICC 0.31 (DE 5.96) |
| T8b | Small number of clusters (19 / 11) | **PRESENT-MINOR** | Percentile bootstrap with 19 clusters tends to under-cover; CI endpoints move ±0.002–0.004 across seeds; the H4 lower bound ranges −0.081…−0.069 (seed 42 is the narrow end); H5 raw p ranges 0.029…0.052 across 12 seeds (seed 42 gives the smallest). Holm-adjusted H5 stays > .05 in all (A3-003) |
| T9 | Power / inconclusive H4 | **PRESENT-MAJOR** for any "SBG adds nothing / adds something" wording | A3-003: MDE ≈ 0.100 (V10) and ≈ 0.038 (V9c-val). Power at true Δ = 0.02: 8.6 % (V10), 32 % (V9c-val). Programs needed for 80 % power at Δ = 0.02: about 410 (V10), about 33 (V9c-val). AUPRC disagrees with AUROC: ΔAUPRC(H4) = +0.050, program CI [+0.004, +0.092], p .036 (uncorrected). Matched-set AUROC p = .62. The pre-registered test is AUROC, so non-significance stands but the metric choice flips raw significance |
| T9b | Combiner transfer failure confounds H4 | **PRESENT-MINOR** | V10 M_EX+V5 (0.797) < V5 alone (0.897) < M_E+V5 (0.8705). Per-program AUROC of M_EX+V5 collapses to 0.22 (`ds_ranked_set`) and 0.06 (`sort_pancake`). Adding V5 helps M_EX in 14/17 non-tied programs (sign test p = .013) while the program bootstrap p = .81, so H4 is driven by two programs |
| T10 | Edit-size confound | **PRESENT-MAJOR** (interpretation); numbers verified | Pooled forward edit AUROC 0.616 (reported). Inside matched sets CH edit > EQ edit in 292/319 (V10) and 186/216 (V9c-val), ties 25/27. Matched-set concordance: edit 0.955 vs V5 0.931 (V10); edit 0.924 vs V5 0.806 (V9c-val). V5 does survive exact-edit stratification (0.875 V10 / 0.736 V9c-val; edit = 0.5 by construction) and edit terciles (V10 V5 0.845 / 0.981 / 0.874). V8-test: reversed edit 0.876 > V5 0.694 (A3-014) |
| T11 | Exclusions correlated with label | **PRESENT-MINOR** | All unevaluated rows are CHANGED (V10: 3 non-terminating + 3 EQ partners dropped; V9c-val: 1 non-terminating, 1 import error + 2 partners). Non-termination is itself an observable difference. Worst/best-case AUROC with them re-inserted: V10 V5 0.8887…0.8980 (reported 0.8968); V9c-val V5 0.7460…0.7552 (0.7514) (A3-013) |
| T12 | Timeouts become silent 0 / 0.5 scores | **NOT-PRESENT** | No unevaluated row carries a score; 0 evaluated pairs with `timeout_fraction` > 0 or `program_budget_exceeded`; no `sbg_v5` == 0.5; `v5_full` is true for all evaluated pairs (so the 0.5 "neutral" fallback in `sbg/v5/distance_v5.py:54` is never triggered). Truncated traces: 0.39 % of V10 traces (39/638 pairs touched, balanced EQ 21 / CH 18); 0.89 % in V9c-val (46/432 pairs, balanced 23 / 23). No nondeterministic runs (A3-008/012/013) |
| T13 | External generalisation | **PRESENT-MAJOR** (claim-level; numbers verified) | BugsInPy and QuixBugs AUROCs are at or below 0.5 (CIs include 0.5 or lie below) (A3-007; belongs to A5) |

---------------------------------------------------------------------------------------------------------------------------------

## 4. DETAILED FINDINGS

### 4.1 Population reconstruction (EXP-A3-001)
Matched-complete sets are built from raw `pairs_*.jsonl`, scored files and validity audits. V10: 644 rows → 641 evaluated → 638 (319 sets, 19 programs, 319 CH). V9c-val: 436 → 434 → 432 (216 sets, 11 programs). V8-test (non-stale): 967 rows → 956 evaluated, 22 programs, 547 CH. V9c train (1650 / 46 programs) and dev (464 / 13) also match. Edit size re-implemented as `ast.unparse` lines → `difflib.unified_diff(n=0)` → count of `+`/`-` lines; matches the repo exactly on every pair.

### 4.2 Resampling unit, seed stability, ICC, LOPO, power (EXP-A3-003)
*V10, V5 AUROC 95 % CI width by unit:* matched-set 0.046, pair 0.052, program-cluster 0.059, two-stage 0.074. *H4 ΔCI width:* set 0.055, pair 0.063, program 0.137, two-stage 0.157.

*Seed stability (12 seeds + B=20000), V10 program-cluster:*
- V5 CI endpoints vary by about ±0.002–0.004.
- H4 lower bound −0.081…−0.069; upper 0.066…0.069.
- H4 p .78–.81.
- H5 raw p .029–.052.

*Leave-one-program-out, V10:* V5 0.892–0.906; state 0.912–0.924; M_EX 0.781–0.815; M_EX+V5 0.787–0.843; edit 0.613–0.619.

*Per-program (19 programs; `EXP-A3-003_v10_test_per_program_auroc.csv`):*

| Comparison | V5 lower | V5 higher | tie | sign-test p |
|---|---|---|---|---|
| V5 vs state | 13 | 5 | 1 | .096 |
| V5 vs M_EX | 5 | 14 | 0 | .064 |
| V5 vs coverage | 4 | 15 | 0 | .019 |
| V5 vs edit | 0 | 19 | 0 | — |

*Pooled program-cluster comparisons (V10):*
- state beats V5 by +0.020, CI [+0.007, +0.039], p .002.
- V5 beats M_EX by +0.033…+0.186, p .003.
- V9c-val: V5 − state = −0.011 (n.s.); V5 − M_EX CI [−0.010, +0.144], p .11.

*Power for H4 (program-level SD of the delta):*

| Quantity | V10 | V9c-val |
|---|---|---|
| MDE (80 % power, α = .05) | ≈ 0.100 | ≈ 0.038 |
| 90 % CI | [−0.057, +0.060] | [−0.0009, +0.0439] |
| TOST-style equivalence bound supported | ±0.060 | ±0.044 |
| Power at true Δ = 0.02 | 8.6 % | 32 % |

**Plain statement:** H4's non-significance is an *absence of evidence*. With 19 clusters, a true incremental gain of up to +0.07 AUROC (or a loss of the same size) is compatible with the data. The test cannot support a claim of "equivalence" or "no gain" at any margin below about ±0.06.

### 4.3 Duplication (EXP-A3-004/004b)
Details in T4/T6. No duplicate or near-duplicate pair IDs across designs. CH/EQ partner token similarity is 0.979 on average (V10), so CHANGED and EQUIVALENT partners are textually very close.

### 4.4 Thresholds, weights and decision metrics (EXP-A3-006)
V10 train-Youden thresholds from `V10_MODELS_FROZEN.json` (`thresholds_youden_train`) are recomputed exactly. `fit_logistic` (L2 = 1, lr = 0.5, 5000 its, standardised) refit gives identical weights (max |Δ| = 0.0) for all 10 models, so the models depend only on `pairs_v9c_train_*` (sha256 matches the pin).

V10 at the frozen thresholds (`EXP-A3-006_prf_at_frozen_and_oracle_thresholds.csv`; the all-positive classifier has F1 0.667, since the CH rate is 50 %):

| Predictor | AUROC | Precision | Recall | F1 | Specificity | Oracle best-F1 (NON-HONEST) |
|---|---|---|---|---|---|---|
| sbg_v5 | .897 | .722 | .944 | .818 | .636 | .878 |
| sbg_state | .917 | .841 | .928 | .882 | .825 | .896 |
| edit | .616 | .558 | 1.000 | .716 | .207 | .716 |
| coverage_size | .779 | .713 | .771 | .741 | .690 | .741 |
| M_EX | .791 | .674 | .868 | .759 | .580 | .792 |
| M_EX+V5 | .797 | .656 | .799 | .720 | .580 | .799 |

The frozen V5 threshold is highly recall-oriented (7.955e-05, the smallest non-zero step). The edit threshold (3.0) marks almost everything as changed.

### 4.5 Label integrity via independent traces (EXP-A3-008/009/010)
Rule: CHANGED must differ in ret/exc/stdout on ≥ 1 of the 11 protocol inputs. EQUIVALENT must not. Traces: frozen extraction harness dumps (`dump_traces.py`), 3/19 programs from the orchestrator cache, the rest dumped by A3 (EXP-A3-005). The dumped scores equal the frozen scored files exactly.

| Design | CH differ | CH identical | EQ identical | EQ differ |
|---|---|---|---|---|
| V10 primary (638) | 319 | 0 | 319 | 0 |
| V9c-val primary (432) | 149 | **67** | 200 | **16** |

The V9c-val CH-identical pairs sit in 11 programs, concentrated in `graph_word_ladder` (18), `math_perfect_numbers` (9), `str_interleave_check` (9) and by SC family SC-4 (30) / SC-1 (15) / SC-8 (9). The mutation-aware re-execution (EXP-A3-009) found no difference via in-place argument mutation either, and none of the 67 variants is AST-identical to its base.

Clean-label sensitivity (V9c-val, post-hoc; matched sets removed as units; EXP-A3-010):

| Scenario | n | V5 | state | edit | M_EX | H3 (V5−edit) | H4 [CI] |
|---|---|---|---|---|---|---|---|
| S0 reported | 432 | .751 | .762 | .611 | .690 | +.140 | +.021 [−.005, +.048] |
| S1 drop EQ-defect sets | 400 | .772 | .782 | .616 | .703 | +.156 | +.015 [−.015, +.045] |
| S2 drop CH-no-diff sets | 298 | .816 | .840 | .621 | .737 | +.195 | +.037 [−.003, +.073] |
| S3 both | 266 | .849 | .872 | .627 | .759 | +.222 | +.031 [−.017, +.072] |

S2/S3 select on observed outputs, which favours output-sensitive methods. They are an upper bound, not a replacement result. They show that label noise lowers V9c AUROC and that H4 stays unresolved.

Invalid mutations: V10 has 3 non-terminating CH variants. V9c-val has 1 non-terminating and 1 import-error. The V8-test 11 failures (4 import, 6 non-terminating, 1 unsupported signature) are taken from the repo's scored file only. SP-8 and SP-11 EQ defects remain in V9c train (37/83 and 36/42 differ per the repo audit), dev and val. In V10 the oracle removed them: 18 SP-8 and 3 SP-11 EQ pairs survive and all are output-identical.

### 4.6 Train/test leakage (EXP-A3-011)
No identity overlap by base_id, file sha256, normalised-AST hash or variant AST hash between V10 and V9c/V8. The max-similarity table per V10 program (4 measures, 5 reference groups) is in `EXP-A3-011_v10_similarity_{compact,per_program}.csv`. The comparison to the repo's novelty report is in `EXP-A3-011_v10_novelty_claim_check.csv`.

### 4.7 Missing traces, timeouts, truncation (EXP-A3-013, A3-008)
See T11/T12. 0 timeout events, 0 silent scores, truncation is label-balanced and below 1 % of traces.

### 4.8 Chronology (EXP-A3-012, read-only git)
- V5 weights: introduced in `sbg/v5/distance_v5.py` in commit 4409652 (2026-08-21), never modified. `benchmark/corpus/fresh_programs` (all V8/V9c/V10 programs) was first committed in b54ea99 (2026-10-28), 2 months later. Git shows no tuning, but the weights were set alongside the older `base_programs` corpus (same commit) and the commit message reports AUROC 0.551 on that benchmark, so absence of tuning is not provable for that earlier corpus.
- `fit_weights.py` last changed 2026-10-03 (ad7b655); `statistics.py` 2026-09-28 (9a9104f). Both predate all fresh programs and V8–V10.
- FREEZE_V9 (commit 6dd5a0f, 2026-10-29 12:18) pins `evaluate_v9.py`, the scored val files and datasets. It states the val scores had not been opened. The val scored files are committed in the same commit as the freeze.
- FREEZE_V10: `git_head` 8386eb5 (2026-10-29 12:56), `written_at` 2026-10-30T12:15Z (≈ 17:45 IST), committed with scored file and evaluation as c5bc130 at 18:02 IST. No freeze-pinned code file changed between 8386eb5 and c5bc130 (empty diff).
- The V10 freeze discloses that forward edit AUROC 0.616 and the mean edit sizes (EQ 8.34 vs CH 10.27) were inspected pre-freeze.

---------------------------------------------------------------------------------------------------------------------------------

## 5. SENSITIVITY OF CONCLUSIONS

| Question | Result |
|---|---|
| AUROC vs AUPRC (EXP-A3-003) | H2, H3, H5 conclusions identical. **H4 differs**: ΔAUPRC +0.050 [+0.004, +0.092], p .036 raw (V10); +0.072 [+0.042, +0.106], p .001 (V9c-val) vs ΔAUROC n.s. in both. H6 ΔAUPRC +0.052 [+0.006, +0.095] |
| Matched-set as unit | V10 H4 p .62 (vs .81); H5 p .039 (vs .030); H4 CI width 0.055 (vs 0.137). Narrower in every contrast, so the unit change cannot be used to rescue a result |
| Pair-level (iid) | Narrower than program-cluster for all but V5 AUROC |
| De-duplication (V10) | V5 0.884 [0.846, 0.912]; ranking of predictors unchanged |
| Clean labels (V9c-val) | V5 0.751→0.849; H4 still n.s. |
| Within-matched-set concordance | edit ≥ V5; the SBG advantage is in the pooled design, not in discriminating within a pair |

---------------------------------------------------------------------------------------------------------------------------------

## 6. TRACEABILITY (number → file → key)

| Number | File | Key / script |
|---|---|---|
| V10 V5 0.8968 [0.8629, 0.9216] | `SBG/artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json` | `predictors.sbg_v5.{auroc, ci95_cluster_bootstrap}` |
| V10 sens .9436 / spec .6364 | same | `predictors.sbg_v5.{sensitivity, specificity, train_threshold}` |
| V10 H1–H6, Holm | same | `pre_declared_tests` |
| V10 supplementary Δ (V5−M_EX etc.) | same + `V10_POSTHOC_SUPPLEMENT.json` | `supplementary_deltas_not_in_holm_family` |
| V10 per-program AUROC | same | `per_program_auroc` |
| V10 matched-set concordance | same | `matched_set_concordance` |
| V9c-val H2/H3/H4 | `V9_VAL_EVALUATION.json` | `pre_declared_tests` |
| V8-test V5 / edit_size_reversed | `V8_TEST_EVALUATION.json` | `predictors.*` |
| Thresholds / weights | `SBG/artifacts/final/V10_MODELS_FROZEN.json` | `thresholds_youden_train`, `models.*` |
| Freeze pins | `FREEZE_V9.json`, `FREEZE_V10.json`, `FREEZE_V10_SCORED.json` | `sha256`, `code_sha256`, `scored_*_sha256` |
| External AUROCs | `EXTERNAL_RESCORE_V8.json`; `DIAGNOSTIC_EXTERNAL.json` | `corpora.*.{rescored_all, rescored_excluding_SP2, committed_v7_same_pairs}`; `quixbugs_canonical[0]` |
| SP-8/SP-11 label defects | `EQUIVALENT_LABEL_AUDIT.json` | `splits.val.output_differs_pairs` (16, same as A3's 16) |
| A3 independent values | `results/raw/EXP-A3-002/*_reconstruction.json` | `predictors`, `deltas`, `holm`, `strat`, `concordance`, `per_program` |
| A3 CSV tables | `results/tables/EXP-A3-*.csv` | see §9 |

---------------------------------------------------------------------------------------------------------------------------------

## 7. EXPLICIT DISCREPANCIES (none hidden)

1. **Statement vs evidence, V9c "observable" validity:** `BENCHMARK_VALIDITY_AUDIT_V9C.json` reports 0 unobservable CHANGED pairs (`n_changed_unobservable` = 0) but its method is "static; executes nothing". Dynamically, 67/216 val CH pairs show no output difference (EXP-A3-008/009).
2. **Statement vs evidence, "size-matched":** matched on pooled distribution only. Within sets CH has the larger edit in 91.5 % of V10 sets (EXP-A3-014).
3. **Task text vs repo:** "QuixBugs 0.388" is the committed *v7* 152-pair figure (0.3877). The v8 rescore on 151 pairs gives 0.3842 and 0.4444 only after SP-2 exclusion. "BugsInPy 0.410" is v7 (0.4099); 0.497 is v8 with SP-2 excluded (A3-007).
4. **Novelty claim:** FREEZE_V10 cites Jaccard 0.101–0.146 versus a corpus sibling (V6 base_programs). Versus V8/V9c programs, my recomputation (repo-style tokenizer) gives up to 0.225 (A3-011). Different reference sets, not a contradiction. The repo's novelty check did not cover V8/V9c programs.
5. **Orchestrator cache:** `results/raw/trace_cache/v10_test` held only 3/19 DONE programs and no V9c cache; A3's own dump (EXP-A3-005) fills the gap. Dumped scores equal frozen scores for 641 + 434 pairs.
6. **Earlier internal note corrected:** V5 is *higher* than M_EX in 14/19 programs (not lower); pooled and per-program results agree.

---------------------------------------------------------------------------------------------------------------------------------

## 8. WHAT FAILED / COULD NOT BE DONE / CONTINUATION COMMANDS

- **Orchestrator job EXP-ORCH-001** was not running (log empty). Fallback used, see 7.5.
- **V8-test label audit not performed.** The repo deliberately did not audit V8-test, and no trace cache exists for it. Continue with
  Continuation: `experiments/common/dump_traces.py` has no `v8` design (its `pair_list` only knows `v10` and `v9c`), so a small `v8` branch (pairs from `benchmark/datasets/v8/pairs_test.jsonl`, non-stale programs) must be added to a *copy* of the driver `exp_a3_005_trace_driver.py`; then reuse `exp_a3_008_label_integrity.py`.
- **Argument-mutation oracle on V10 not re-done** (only on V9c-val label-error candidates). V10 CH/EQ were checked by return/exception/stdout, which is sufficient to confirm the labels; mutation-only differences would only add CH-observability.
- **No power analysis for H5/H6 or for the matched-set unit.**
- **Percentile bootstrap with 19 clusters not compared against a wild/cluster-t or exact method.** Coverage claims are qualitative.
- **V8/V9c train/dev label audits** beyond the repo's `EQUIVALENT_LABEL_AUDIT.json` were not re-run.
- **External validation beyond AUROC recomputation** belongs to A5.
- **Time**: all runs finished; no timeouts.

Reproduce everything:
```
cd IEEE_ACCESS_PRE_SUBMISSION
PY="PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 /Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python"
for s in 001_populations 002_reconstruct 003_dependence 004_duplication 004b_dedup_sensitivity; do $PY experiments/statistical_verification/exp_a3_$s.py; done   # 002 takes arg "all"
$PY experiments/statistical_verification/exp_a3_005_trace_driver.py v10 test 2
$PY experiments/statistical_verification/exp_a3_005_trace_driver.py v9c val 2
$PY experiments/statistical_verification/exp_a3_006_thresholds.py --refit
$PY experiments/statistical_verification/recompute_external_auroc.py
for s in 008_label_integrity 009_mutation_aware 010_label_clean_sensitivity 011_leakage 012_freeze_integrity 013_missing_pairs 014_edit_strata; do $PY experiments/statistical_verification/exp_a3_$s.py; done
```

---------------------------------------------------------------------------------------------------------------------------------

## 9. DELIVERABLES

- Scripts: `experiments/statistical_verification/{a3lib.py, exp_a3_001 … 014*.py, exp_a3_005_trace_driver.py, _exec_probe.py, recompute_external_auroc.py}`
- Raw results: `results/raw/EXP-A3-001 … 014/` (including `EXP-A3-005/trace_cache`)
- Tables: `results/tables/EXP-A3-*.csv`
- Registry: `logs/registry/A3_stats.jsonl`
- Logs: `logs/EXP-A3-*.log`

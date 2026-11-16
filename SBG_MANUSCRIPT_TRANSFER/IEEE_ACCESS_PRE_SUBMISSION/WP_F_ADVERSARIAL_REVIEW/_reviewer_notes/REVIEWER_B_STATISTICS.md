# Reviewer B — Statistical Claims (adversarial review of SBG, IEEE Access)

Scope: read-only. Sources read: `HANDOFF/MASTER_HANDOFF_PROMPT.md`, `07_EXPERIMENTAL_INTEGRITY_AUDIT.md` (07), `HANDOFF/COMPLETED_WORK.md`, `configs/PROTOCOL.md`, `PROTOCOL_ADDENDUM_v1.1.md`, `results/tables/EXP-A3-*.csv`, plus (read-only) `SBG/artifacts/final/FREEZE_V10.json`, `SBG/artifacts/paper_evidence/{V10_INDEPENDENT_EVALUATION,V10_POSTHOC_SUPPLEMENT,V9_VAL_EVALUATION,EXTERNAL_RESCORE_V8}.json`. A4C held-out predictions were not touched. My own scratch code/output: `_reviewer_notes/scratch/rb_checks.{py,out}`, `rb_jackknife.{py,out}` (stdlib, py313, existing scores only). Tag **[RD]** = reviewer-derived arithmetic from existing files, not in any prior report.

## 0. Bottom line
1. The numbers are real (07 reproduced 522 quantities, max |Δ| = 0). The problem is inference, not arithmetic.
2. Only **H1, H2, H3** are confirmed (V10 and V9c-val). They are the weakest hypotheses: H1 is "better than chance" on labels that are defined by observable output change; H2/H3 are measured against *pooled* edit size, which is a near-perfect discriminator *within* matched sets.
3. **H4 (the novelty-relevant hypothesis) is inconclusive.** Neither "no gain" nor "gain" can be claimed on AUROC. An exploratory AUPRC signal exists in both held-out sets, so a "null-result" framing is also overstated.
4. **H5 is not confirmed after Holm** (and the effect is ≤ 0.006 AUROC even if real). **H6 is inconclusive.**
5. "Genome (state) 0.917 > full V5 0.897" is a post-hoc, V10-only, uncorrected finding; it does not replicate on V9c-val.
6. External results: "at or below chance" is a fair description of point estimates; "below chance" as an inference is configuration-dependent and not corrected for multiplicity.

## 1. Hypothesis definitions (the protocol files do NOT define H1–H6; source is `FREEZE_V10.json` → `hypotheses`, and `V9_VAL_EVALUATION.json` → `pre_declared_tests.*.what`)
| H | Definition | Family |
|---|---|---|
| H1 | AUROC(sbg_v5) > 0.5; one-sided cluster permutation (labels permuted within program) | Holm 6 (V10) / 4 (V9c-val) |
| H2 | AUROC(M_E+V5) − AUROC(M_E) (V9c-val: M_ES − M_E; ES = edit + sbg_v5) | same |
| H3 | AUROC(V5) − AUROC(edit, forward orientation) | same |
| H4 | AUROC(M_EX+V5) − AUROC(M_EX) (V9c-val: M_ESX − M_EX); X = exception_fraction, call_count, coverage_size | same |
| H5 | sbg_v6 − sbg_v5 (V10 only, "EXPERIMENTAL") | Holm 6 |
| H6 | M_EX+V6 − M_EX (V10 only, "EXPERIMENTAL") | Holm 6 |

Method: program = resampling unit, percentile bootstrap, B = 2000, seed 42; two-sided p = 2·min tail with (k+1)/(B+1), so **p = 0.001 is the floor, not an estimate** (07 §2). Models M_* are logistic combiners fitted on V9c-train only (verified leak-free, EXP-A3-006).

## 2. Hypothesis-by-hypothesis
| H | Estimate (V10) | CI / p / Holm | V9c-val | Verdict |
|---|---|---|---|---|
| H1 | V5 0.8968 | CI [0.863, 0.922]; perm p = 0.0005 (floor); Holm 0.003 | 0.7514 [0.706, 0.794]; Holm 0.002 | **Confirmed**, but near-trivial: label = "output differs on the 11 protocol inputs", and V10 CHANGED pairs are guaranteed observable on those inputs (07 T5b). |
| H2 | +0.2545 | [0.218, 0.285]; p = .001 floor; Holm .005 | +0.112 [0.075, 0.148]; Holm .003 | **Confirmed**; M_E ≡ edit (AUROC 0.616 both). Interpretation limited by edit-size issue (§4). |
| H3 | +0.2807 | [0.2435, 0.3081]; Holm .005 | +0.140 [0.092, 0.180]; Holm .003 | **Confirmed in the pooled design.** Not a within-pair claim (§4). |
| H4 | +0.0063 | [−0.069, +0.068]; p = .81; Holm 1.0 | +0.021 [−0.005, +0.048]; p = .117 | **Inconclusive** (§3). |
| H5 | +0.0029 | [0.0003, 0.0060]; raw p = .030; **Holm .090** | n/a | **Not confirmed.** Raw p moves .029–.052 over 12 seeds (A3-003); matched-set p .039, two-stage p .148. |
| H6 | +0.0085 | [−0.067, +0.069]; p = .77; Holm 1.0 | n/a | **Inconclusive** (same power problem as H4). |

Multiplicity: Holm is applied only within each pre-declared family and separately per dataset. All other contrasts (V5 vs M_EX, V5 vs state, AUPRC, strata, per-program sign tests) are outside any family and uncorrected; 07 does not count them. Treat every one of them as exploratory.

## 3. H4 in detail
- V10: Δ = +0.0063, 95% CI [−0.069, +0.068], p .81 (07 §2; `EXP-A3-003_v10_test_resampling_unit_comparison.csv`). 90% CI [−0.057, +0.060] → the tightest TOST-style equivalence margin the data could support is ≈ ±0.06; MDE (80% power, α .05) ≈ 0.100; power at a true Δ = 0.02 is 8.6% (`EXP-A3-003_v10_test_power_h4.csv`). Check: 2.8 × 0.0357 (program-bootstrap SD) = 0.100 ✔. Caveat: this is post-hoc power from the observed SD of 19 clusters, itself uncertain.
- V9c-val: Δ = +0.021 [−0.005, +0.048], MDE ≈ 0.038, power at 0.02 = 32%. Label noise there (§6) biases toward the null for all contrasts.
- **[RD]** Crude pooled estimate of the two independent program sets (inverse-variance on bootstrap SDs 0.0357 / 0.0136, normal approximation): +0.019, 95% CI ≈ [−0.006, +0.044], p ≈ .13. Direction is positive in both sets; it is still not significant. This is a plausibility check, not a reportable result (different designs, noisy V9c labels).
- AUPRC is discordant (07 T9; `EXP-A3-003_*_auprc_and_unit_sensitivity.csv`): V10 ΔAUPRC +0.050 [+0.004, +0.092], p = .036 uncorrected; V9c-val +0.072 [+0.042, +0.106], p = .001. Matched-set resampling gives V10 AUPRC p = .001 but AUROC p = .62. AUPRC was not pre-declared. **[RD]** Holm over the five AUPRC H-contrasts (p = .001, .001, .036, .009, .022) would give H4 .044 — i.e. it hinges on how many looks are counted and the CI lower bound is 0.004. Verdict: hypothesis-generating only.
- Why H4 is a weak test of "incremental value": V10 M_EX+V5 (0.797) < V5 alone (0.897) < M_E+V5 (0.8705) — the combiner trained on V9c-train fails to transfer; per-program AUROC collapses to 0.22 (`ds_ranked_set`) and 0.06 (`sort_pancake`) (07 T9b). H4 therefore measures combiner transfer as much as SBG's information. Adding V5 helps M_EX in 14/17 non-tied programs (sign p = .013) while the cluster bootstrap p is .81 — the pooled AUROC delta is driven by two programs.
- Honest statement: *"We could not determine whether SBG adds AUROC beyond edit size plus execution statistics: Δ = +0.006 (95% CI −0.069 to +0.068, 19 programs); the study can detect only effects ≥ ≈0.10 and cannot exclude gains or losses of ≈0.07. An exploratory AUPRC analysis was positive in both held-out sets but was not pre-declared."* Do not write "no incremental value" or "SBG adds value beyond exec statistics".

## 4. State genome vs full V5; edit-size confound
**State vs V5 (V10).** `sbg_state` 0.9171 [0.893, 0.938] vs `sbg_v5` 0.8968 [0.863, 0.922]. The difference is **not in the pre-declared family and not in the repo's own supplementary JSON**; it appears only as an "(extra)" contrast in A3 (`EXP-A3-003_v10_test_resampling_unit_comparison.csv`): +0.0204, program-cluster CI [+0.0069, +0.0387], p = .002; matched-set p .001; two-stage (program→set) CI [+0.0038, +0.0406], p .018; B = 20000 [+0.0067, +0.0377]. **[RD]** Leave-one-program-out Δ stays +0.017…+0.024 and a jackknife t(18 df) interval is [+0.004, +0.037] (`rb_jackknife.out`), so it is not driven by one program. But: per-program V5 < state in 13, > in 5, tie 1 (sign p = .096); post-hoc selection among V3/temporal/state/V5/V6 on V10; p = .002 survives a Bonferroni-type correction only for ≲ 20 looks; **V9c-val: state − V5 = +0.011, CI [−0.024, +0.040], p = .49** (not replicated; also +0.025 on the clean subset S2, no CI). De-duplicated V10: 0.9124 vs 0.8843 (no CI for the delta). Verdict: **WEAK** (exploratory, single dataset). Wording: *"On V10 the state component alone ranked higher than the fixed-weight composite (ΔAUROC +0.020, program-cluster 95% CI +0.007 to +0.039, post-hoc, uncorrected); this was not seen on V9c-val (+0.011, CI −0.024 to +0.040)."* It does not support "state genome dominates" without A5E.

**Edit-size confound.** In V10, CHANGED has the larger edit in 292/319 sets, ties 25, reverse 2 (`EXP-A3-014_matched_set_concordance.csv`) → among non-tied sets 292/294. So edit size is nearly deterministic *within* a set, and the "size-matched" design is matched only in the pooled distribution (mean edit EQ 8.34 vs CH 10.29). Within-set concordance: edit 0.955 [0.934, 0.972] vs V5 0.931 [0.897, 0.957]; difference edit − V5 = +0.0235 [−0.0105, +0.0621] (`V10_POSTHOC_SUPPLEMENT.json`) → **not distinguishable** in V10. V9c-val: edit 0.924 [0.907, 0.943] vs V5 0.806 [0.738, 0.861]: marginal CIs do not overlap, so edit is better there (paired CI not reported — **[UNVERIFIED]**). V8-test: reversed-edit 0.876 vs V5 0.694 (07 §2). Evidence that V5 carries information beyond edit size: exact-edit-stratified AUROC 0.875 (V10), 0.735 (V9c-val); terciles 0.845/0.981/0.874 — **none reported with CIs**; edit is 0.5 by construction in the strata, so the comparison is partly mechanical.
Verdict: H3 "V5 beats edit size" is SUPPORTED for pooled ranking and for exact-size-stratified ranking (point estimates), but "size-matched benchmark controls the edit-size confound" is **CONTRADICTED** at the pair level. Wording: *"SBG outperforms edit size in pooled AUROC and after stratifying on exact edit size, but does not outperform it in within-pair ranking (V10: concordance 0.931 vs 0.955; V9c-val 0.806 vs 0.924)."*

## 5. Dependence, pseudo-replication, effective sample size
- Unit: 19 programs (14–48 primary pairs each **[RD]**; V9c-val 11). Pair-/set-level CIs are anti-conservative (A3-003). Bootstrap SD ratios from A3-003 give **[RD]** design effects vs pair-iid: V5 AUROC 1.3 (≈480 pair-equivalents), M_EX AUROC 3.5, H4 Δ 5.0 (≈128 pair-equivalents; vs matched sets 6.6, ≈48 of 319 sets). The honest "n" for H4 is ~19, not 638.
- 19 clusters with a percentile bootstrap: coverage not checked (07 §8 — no cluster-t/wild/exact comparison). Seed sensitivity: CI ends move ±0.002–0.004; H4 lower bound −0.081…−0.069 (seed 42 is the narrow end); H5 p .029–.052. The reported seed-42 values are the most favourable end for H5 (smallest p).
- Pseudo-replication (84 AST-identical variant groups, 212 rows: 161 EQ/51 CH; no mixed-label groups): de-duplicated (511 rows) V5 0.8968 → 0.8843 [0.846, 0.912]; edit 0.616 → 0.580; M_EX 0.791 → 0.761; M_EX+V5 0.797 → 0.786 (`EXP-A3-004b_dedup_sensitivity.csv`). Shift −0.013 is inside the CI, but its sign is systematic: identical-AST EQ variants share the V5 = 0 tie. Primary V5 CI should be quoted with the de-dup sensitivity. Deltas after de-dup have no CIs — **[UNVERIFIED]** for H3/H4 on the de-dup set.
- Mixed design caveat: V10 "independence" is weak (16/19 programs > 0.10 Jaccard to a V8/V9c program, max 0.225; 07 T7b), so program clusters are not exchangeable draws from a wider population.

## 6. V9c-val label noise
16/216 EQUIVALENT pairs differ in output and 67/216 CHANGED show no output difference (07 §4.5; `EXP-A3-008/009/010`). Noise is non-random (SP-8/SP-11; SC-4/SC-1/SC-8; partly concentrated (graph_word_ladder 18, math_perfect_numbers 9, str_interleave_check 9 of 67 CH)), so it correlates with program clusters. V5: 0.751 reported → 0.849 on the 266-pair "clean" subset; state 0.762 → 0.872; H4 +0.021 → +0.031 [−0.017, +0.072]. The clean subsets are selected on output (favours output-sensitive methods) and are upper bounds, not replacement results. Therefore: V9c-val absolute AUROCs are attenuated by an unquantified amount, its CIs ignore label error, and its H4 power analysis is not "clean". It remains valid as a sign-consistent replication of H1–H3 only. Verdict on "V9c-val confirmatory": **WEAK**.

## 7. External validity (BugsInPy, QuixBugs; `EXP-A3-007_external_auroc.csv`; `EXTERNAL_RESCORE_V8.json`)
CIs **are** given (program/cluster bootstrap, 39–40 clusters, 39–41 positives). None of the external tests were pre-declared; EXTERNAL_RESCORE_V8 is labelled EXPLORATORY.
| Config | AUROC | 95% CI | Contains 0.5? |
|---|---|---|---|
| BugsInPy v7 committed, all (147) | 0.410 | [0.326, 0.494] | no (barely; seed 7: [0.330, 0.489]) |
| BugsInPy v8 rescore, all | 0.416 | [0.322, 0.514] | yes |
| BugsInPy v8, SP-2 excluded (107) | **0.497** | [0.402, 0.596] | yes |
| QuixBugs v7 committed, all (152) | **0.388** | [0.285, 0.503] | yes (barely) |
| QuixBugs v8 rescore, all (151) | 0.384 | [0.285, 0.490] | no (barely) |
| QuixBugs v8, SP-2 excluded (111) | **0.444** | [0.355, 0.539] | yes |
**[RD]** normal approximation from CI width: z ≈ −2.1, −1.7, −0.1, −2.0, −2.2, −1.2 → two-sided p ≈ .035, .09, .95, .044, .027, .23. So "below chance" is borderline in 3 of 6 configurations and absent in the SP-2-excluded ones; no multiplicity correction. The SP-2 exclusion (raising 0.416 → 0.497) is a post-hoc subset choice justified by 7/40 provably invalid SP-2 negatives (NameError), so both the all-pair and excluded numbers are contaminated. Ties dominate: V5 = 0 on 26/41 BugsInPy and 32/39 QuixBugs real-bug pairs (`EXTERNAL_RESCORE_V8.json`) — the result is largely "SBG is blind to these bugs on the protocol inputs and sometimes fires on equivalence-transformed negatives", not evidence of anti-correlation. `REAL_BUG_GENERALISATION_AUDIT.md` says removing the 7 invalid negatives "raises BugsInPy excl. SP-2 to ~0.445" — incoherent (the 0.497 set already has no SP-2 pairs) → **[UNVERIFIED]**.
Wording: *"On BugsInPy and QuixBugs the AUROC point estimates were 0.38–0.50 (95% CIs span 0.29–0.60); we found no evidence that SBG discriminates real bugs from equivalent rewrites on these corpora under the frozen protocol; most real-bug pairs scored exactly 0."* Do not claim "SBG performs below chance" or "does not generalise to real bugs" as a rate-level inference. The "0.497/0.410" and "0.444/0.388" pairs are different pipelines (v8 SP-2-excluded vs v7 committed), not two estimates of one quantity.

## 8. SC-6 "17/23 invisible"
Source: `V10_INDEPENDENT_EVALUATION.json` → `changed_zero_rate_by_sc_family.SC-6 = {n: 23, sbg_v5: 0.7391}`; repeated in `FINAL_SPRINT_REPORT.md:59`, `CLAIM_TO_EVIDENCE_MATRIX.md` (A12), `results/raw/repro/traceability.md` row 11. **[RD]** I recomputed from `configs/populations/v10_test.json`: 23 primary CHANGED pairs with `sc_type == SC-6`, 17 with V5 = exactly 0, from 18 programs (gnome_sort 4, kahn 2, knapsack 2, rest 1); 14 programs contribute zeros; dropping any one program leaves 13–17 of 19–22. The 17 are 17/18 of all zero-scored CHANGED pairs in V10 (the other is SC-2); the 296 CHANGED pairs of other families are essentially all non-zero.
Denominator = SC-6 CHANGED pairs only (23 of 319 CHANGED, 3.6% of 638 pairs), **not** all CHANGED pairs. Clopper–Pearson 95% CI **[RD]** [0.516, 0.898] (Wilson [0.535, 0.875]) before any clustering correction. "Invisible" means V5 score exactly 0, not "undetectable by the genome" (state/V6 not reported for SC-6). Because SC-6 is a return-value mutation family and SBG is output-free by design, the finding is expected, not an estimation result. Verdict: SUPPORTED as a descriptive count; WEAK as a generalisable rate (one family, 23 pairs); an overall recall figure is the correct headline: V5 sens 0.944 at the frozen threshold (V10, A3-006), driven by a threshold at the 7.955e-05 step. Wording: *"17 of the 23 SC-6 CHANGED pairs (74%; exact 95% CI 52–90%) scored exactly 0 under V5; these were value-only edits."*

## 9. Python-version dependence (09 §6)
Exact reproduction only on CPython 3.13.x. 3.9.6 recompute of V10 (18/19 programs, 613 pairs; `math_fib_matrix` aborts): 299 pairs differ, 3,837/93,942 orderings flip, pooled AUROC 0.8947 → 0.9226 (+0.028); V9c-val 0.7530 → 0.7815 (+0.029); 4-program subset: 3.9 0.8407 → 0.9018, 3.11 → 0.8980, 3.14 → 0.8280 (2 pairs flip hugely; only 2/140 differ). **Statistical consequence:** all bootstrap CIs condition on the 3.13 scores as fixed measurements; implementation-induced shifts of ±0.03 AUROC are not in any CI and are **larger than** H5 (0.003), H4 (0.006), and comparable to state − V5 (0.020). No full-population 3.11/3.14 result exists ([UNVERIFIED] beyond the 140-pair subset). Wording: *"Results are defined for CPython 3.13.x; on 3.9 the same code gives pooled AUROC 0.89→0.92 (V10) because tracing behaviour differs."* Conclusions about differences < ~0.03 AUROC should not be drawn.

## 10. Claim table
| # | Claim | Number | Source file | CI / test | Verdict | Honest wording |
|---|---|---|---|---|---|---|
| 1 | SBG V5 above chance (H1), V10 | 0.8968 | `V10_INDEPENDENT_EVALUATION.json`; A3-002 | [0.863, 0.922]; perm p 0.0005; Holm .003 | SUPPORTED (low bar) | "AUROC 0.90 (CI 0.86–0.92) on 19 unseen-program families; labels are protocol-observable output changes." |
| 2 | V5 above chance, V9c-val | 0.7514 | `V9_VAL_EVALUATION.json` | [0.706, 0.794]; Holm .002 | WEAK (label noise) | "0.75 on noisy labels (7% EQ and 31% CH mislabelled); 0.85 on a post-hoc clean subset." |
| 3 | H2 | +0.254 / +0.112 | same | [0.218, 0.285] / [0.075, 0.148] | SUPPORTED | "Adding V5 to edit size raises AUROC by …" |
| 4 | H3 V5 > edit | +0.281 / +0.140 | same | [0.244, 0.308] / [0.092, 0.180] | SUPPORTED (pooled); CONTRADICTED as within-pair claim | see §4 |
| 5 | H4 | +0.006 / +0.021 | same; A3-003 | [−0.069, +0.068]; [−0.005, +0.048]; p .81/.117 | NOT-ESTABLISHED (inconclusive) | §3 wording |
| 6 | H4 "MDE ≈ 0.10, margin ±0.06" | 0.100, ±0.060 | A3-003 power CSV | t-based on program SD | SUPPORTED [RD-checked] | "Underpowered; cannot exclude ±0.07." |
| 7 | ΔAUPRC(H4) | +0.050 / +0.072 | A3-003 AUPRC CSV | [+0.004, +0.092] p .036 unc.; [+0.042, +0.106] | WEAK (exploratory) | "Exploratory, not pre-declared." |
| 8 | H5 V6 > V5 | +0.0029 | `V10_INDEPENDENT_EVALUATION.json` | p .030; Holm .090 | UNSUPPORTED | "No reliable V6 improvement; ≤ 0.006." |
| 9 | H6 | +0.0085 | same | [−0.067, +0.069] | NOT-ESTABLISHED | like H4 |
| 10 | State 0.917 > V5 0.897 | +0.0204 | A3-003 CSV (not in repo JSON) | [+0.007, +0.039]; p .002 unc.; V9c-val +0.011 [−0.024, +0.040] | WEAK | §4 wording |
| 11 | V5 > M_EX (exec stats) | +0.106 / +0.061 | `V10_POSTHOC_SUPPLEMENT.json`; A3-003 | [0.033, 0.186] p .003 / [−0.010, +0.144] p .11 | WEAK (V10 only, post-hoc) | "Higher on V10, not on V9c-val." |
| 12 | "Size-matched" benchmark | 292/319 sets | A3-014; `V10_POSTHOC_SUPPLEMENT.json` | sign test trivial | CONTRADICTED (pairwise) | "Matched in pooled distribution only." |
| 13 | Edit concordance 0.955 > V5 0.931 | diff +0.0235 | `V10_POSTHOC_SUPPLEMENT.json` | [−0.011, +0.062] | NOT-ESTABLISHED (V10); edit > V5 on V9c-val (marginal CIs separate; paired CI [UNVERIFIED]) | §4 wording |
| 14 | V5 survives edit stratification | 0.875 / 0.735 | `V10_INDEPENDENT_EVALUATION.json` | no CI | WEAK (no CI) | "Point estimate only." |
| 15 | Pseudo-replication effect | 0.897 → 0.884 | A3-004b | [0.846, 0.912] | SUPPORTED (small) | "Report de-dup alongside primary." |
| 16 | CIs adequate with 19 programs | width 0.059 (V5), 0.137 (H4) | A3-003 | percentile bootstrap; coverage untested | WEAK | "Cluster bootstrap, 19 programs; coverage not validated." |
| 17 | BugsInPy 0.497 / 0.410 | | A3-007; `EXTERNAL_RESCORE_V8.json` | [0.402, 0.596] / [0.326, 0.494] | WEAK as "below chance"; SUPPORTED as "no evidence above chance" | §7 wording |
| 18 | QuixBugs 0.444 / 0.388 | | same | [0.355, 0.539] / [0.285, 0.503] | same | same |
| 19 | SC-6 17/23 invisible | 73.9% | `V10_INDEPENDENT_EVALUATION.json`; [RD] recount | exact CI [0.52, 0.90] | SUPPORTED (descriptive); WEAK (rate) | §8 wording |
| 20 | Python-version non-determinism | +0.028/+0.029 pooled AUROC on 3.9 | `09_…AUDIT.md` §6 | none | SUPPORTED (as limitation); CIs omit it | §9 wording |
| 21 | "Frozen before scoring" (V10) | single commit c5bc130 | 07 T3, 09 | self-attested `written_at` | NOT-ESTABLISHED | "Freeze declared in-repo; chronology not independently verifiable." |
| 22 | "16/19 programs > 0.10 Jaccard to a *dev* program" (COMPLETED_WORK) | 16/19 | 07 T7b says "V8/V9c programs" | | Minor inconsistency in wording | use 07's wording |

## 11. What I could not verify
- Paired CIs for edit − V5 concordance on V9c-val; CIs for exact-edit-stratified and tercile AUROCs; CIs for de-duplicated deltas.
- Bootstrap coverage with 19 clusters (never tested); number of post-hoc contrasts computed in total (not logged in one place).
- V8-test label audit (not done by A3); full-population 3.11/3.14 AUROCs.
- `REAL_BUG_GENERALISATION_AUDIT.md` "~0.445" figure.

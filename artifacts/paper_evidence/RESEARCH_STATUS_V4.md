# RESEARCH STATUS V4 — zero-score diagnosis, experimental V6, independent v10 test

Branch `remediation/sbg-v4` (base 8386eb5). Every number below is checked against its source artifact by `experiments/final/verify_trace_v4.py`.
Nothing in V3 evidence is overwritten; V3 conclusions that this session did not revisit are unchanged.

## 1. Zero scores (Phase 1) — `ZERO_SCORE_ROOT_CAUSE_V1.md`
* The "37 %" is v9c validation, matched-complete: **160 / 432 = 37.04 %** (`V9_VAL_EVALUATION.json`). It is a mixture: EQUIVALENT 58.8 % zero (correct answers), CHANGED 15.3 % zero.
* Zeros are exact (all three components exactly 0, not rounding). **No scorer defect that produces zeros was found.** Unevaluated pairs are `scores = null`, never zero; the `d_temporal/d_state := d_v3` fallback never fired (`v5_full == 1` on every evaluated row).
* Zero CHANGED pairs (train+dev, n = 178): 138 are not dynamically exercised by the 11 protocol inputs (79), have return-only differences invisible to the output-free design (27), or differ only by object addresses/renamed qualnames (32). Only **40** (after the address-artefact correction, §9 of the root-cause report) are genuine value differences lost by the abstraction.
* **New benchmark defects (labels):** SP-8 extract-method emits an undefined helper (NameError); SP-11 swaps in a `deque`. 8.7 % of train EQUIVALENT variants change program output (`EQUIVALENT_LABEL_AUDIT.json`). These are *label* errors that depress every predictor's AUROC. The v10 set excludes them by oracle.

## 2. Experimental SBG V6-graded (Phase 3–4) — development only
V6 = V5 with a graded value abstraction (rationale and predictions written before scoring: `SBG_V6_EXPERIMENTAL_RATIONALE.md`).
Dev (v9c dev, 464 pairs, 13 programs; `V4_DEV_EVALUATION.json`): ΔAUROC(V6 − V5) = +0.0001 [−0.0081, +0.0090]; only 1 of 31 zero CHANGED pairs rescued on dev (19 of 72 on train+dev with raw differences). Prediction P1 (large zero reduction) **failed**; V6 is not an improvement on dev.

## 3. Independent test v10 (Phase 5–6) — `V10_INDEPENDENT_EVALUATION.json`, frozen by `FREEZE_V10.json`
* 19 programs never in any v8/v9 split. Labels validated by a dynamic oracle (EQ == base; CH(SC) != base; CH == SC-mutant). **638 evaluated pairs, 319 matched sets, 19 programs**; 3 unevaluated (nonterminating) pairs, reported not imputed.
* Single run; hashes of script, models, dataset, scorer and scored file were frozen before any v10 metric was computed.
* **Independence caveat:** the programs are unseen but are algorithmic siblings of development programs (excluded from v8 only by token-Jaccard 0.10–0.15) and share author and generator with development data.

| predictor (v10) | AUROC | 95 % cluster CI |
|---|---|---|
| SBG V5 | 0.897 | [0.863, 0.922] |
| SBG V6 (experimental) | 0.900 | [0.867, 0.923] |
| edit size forward | 0.616 | [0.606, 0.628] |
| edit size reversed | 0.384 | [0.372, 0.394] |
| coverage_size | 0.779 | [0.721, 0.839] |
| model edit+exec | 0.791 | [0.718, 0.851] |
| model edit+SBG V5 | 0.871 | [0.836, 0.898] |
| model edit+exec+SBG V5 | 0.797 | [0.669, 0.898] |

Pre-declared tests (Holm over H1–H6): H1 SBG V5 > chance (adjusted p 0.003, supported); H2 edit+SBG − edit **+0.254** [+0.218, +0.285] (supported); H3 SBG V5 − edit(forward) **+0.281** [+0.244, +0.308] (supported); **H4 edit+exec+SBG − edit+exec +0.006 [−0.069, +0.068], adjusted p 1.0 (NOT supported)**; H5 V6 − V5 +0.003 [+0.0003, +0.006], Holm-adjusted p 0.090 (not supported); H6 +0.008 [−0.067, +0.069] (not supported).

## 4. Controls and cautions on the v10 numbers
* Design: edit size is **not eliminated**: mean edit 10.29 (CHANGED) vs 8.36 (EQUIVALENT), forward-edit AUROC 0.616. Exact-edit-size-stratified AUROC for SBG V5 is 0.875 (edit 0.500 by construction).
* **Matched-set concordance** is higher for edit (0.955) than SBG (0.931) because the CHANGED partner is the EQUIVALENT rewrite *plus* a mutation, so within a set it always has the larger edit (91.5 % of sets strictly larger). This is a property of the composed design, not evidence that edit size is a better semantic detector; pooled AUROC and stratified AUROC are the fair comparisons.
* Zero rates on v10: SBG V5 overall 34.6 %; CHANGED 5.6 %, EQUIVALENT 63.6 %; rename-style EQUIVALENT families (SP-1/2/4/6/12) ≈ 94–100 % zero (correct); SC-6 CHANGED 73.9 % zero (return-only mutations, invisible by design).
* Post-hoc (descriptive, not in Holm family; `V10_POSTHOC_SUPPLEMENT.json`): V5 − coverage_size +0.118 [+0.062, +0.175]; V5 vs M_EX +0.106 [+0.033, +0.186]; on rewrite-only EQUIVALENT families (SP-3/5/8/11, hardest negatives, 110 sets) AUROC V5 0.835 [0.760, 0.899].

## 5. Reconciling v10 with earlier results
| design | SBG V5 | note |
|---|---|---|
| v8 test (burned) | 0.694 vs reversed edit 0.876 | label bound to family; NOT DEMONSTRATED |
| v9c val (confirmatory-by-freeze) | 0.751 [0.706, 0.794]; H4 +0.021 n.s. | |
| v9c dev (exploratory) | 0.785 [0.743, 0.829] | |
| v10 independent (single run) | 0.897 [0.863, 0.922]; H4 +0.006 n.s. | oracle-validated labels, no SP-8/SP-11 defects |

v10 is higher than v9 val. Plausible, **untested** contributors: v10 removes the SP-8/SP-11 label noise; its programs may be easier. I cannot separate these from the data; the two designs also use different programs. The H4 result is consistent across v9 val and v10.

## 6. Claims
**Supported:** SBG V5 discriminates behaviour-changing from behaviour-preserving edits above chance with size-matched composed pairs (v9 val, v10), and adds information beyond edit size (H2, H3). Exact zeros are overwhelmingly correct EQUIVALENT answers plus not-exercised mutations; there is no scoring defect behind them.
**Not supported:** that SBG adds value beyond edit size *and* simple execution statistics (H4 fails in both v9 val and v10; interval ±0.07 on v10); that V6 improves on V5; that SBG detects real bugs (BugsInPy/QuixBugs unchanged from V3: below chance).
**Limitations:** composed-pair design leaves edit-size imbalance; 19 programs, 3 of them contributing 0.705–0.79 AUROC; v10 programs are siblings of development programs; benchmark labels are family-defined with dynamic validation only in v10; 30 % of CHANGED pairs in v9c are unobservable on the protocol inputs; V8 test is burned and was inspected in aggregate once for the label audit.

# DIAGNOSTIC REPORT (P1–P3) and v8 held-out outcome

Branch `remediation/sbg-v2`. Every number below is read from the artifact named beside it; scripts are listed in
`REPRODUCIBILITY.md`. Method and evaluation protocol were **not** altered to improve any metric.

## Bottom line

* Reversed edit size beating SBG is a **genuine benchmark confound plus a legitimate shortcut baseline**. It is **not** an implementation, scoring, orientation, or leakage error. SBG V5 does **not** beat it on any dataset, including the single frozen v8 test run (0.694 vs 0.876).
* There is **residual signal beyond edit size** (exact edit-size-stratified AUROC 0.776 on v8 test, 0.859 on v8 dev, both above the label-shuffle noise floor), but it does not translate into beating the shortcut.
* Frozen v6 dev drift is **root-caused** (hash-order nondeterminism + a legitimate aliasing fix). It moves AUROC by ≤ 0.011.
* Real-bug results (BugsInPy/QuixBugs) contain **no label/orientation/pairing error**, but two **harness artifacts** depress them; corrected values (0.43–0.51) are indistinguishable from chance. **No evidence of transfer.**
* **SBG is not validated.**

## P1 — Why reversed edit size outperforms SBG  (`DIAGNOSTIC_EDIT_SIZE.json`)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| Implementation / scoring error | **Rejected** | Library AUROC equals a brute-force O(n²) AUROC exactly for SBG and reversed edit size on all three datasets. |
| Orientation error | **Rejected** | Forward edit-size AUROC 0.046 / 0.043 / 0.155 (v6 train / v6 dev / v8 dev) = 1 − reversed (0.954 / 0.957 / 0.845). Same result for three size measures (canonical AST lines, raw lines, char edit). |
| Leakage / invalid comparison | **Rejected** | Edit size is computed from the two source files only; SBG never sees it; both are scored on identical pair sets. |
| Dataset / label confounding | **Confirmed** | Label is a deterministic function of transformation family: SC-* ⇒ CHANGED (median edit 2–3 lines), SP-* ⇒ EQUIVALENT (median 14–69 lines in v6). Mean edit: CHANGED 2.3 vs EQUIVALENT 24.7 (v6 train), 2.7 vs 9.2 (v8 dev), **2.13 vs 8.61 (v8 test)**. The v8 `max_names=1` redesign reduced the confound but did not remove it. |
| Genuine method limitation | **Partly** | Size-controlled SBG (exact edit-size strata): v6 train 0.650 [0.52, 0.78] (5.7 % of cross-label pairs), v6 dev 0.497 [0.27, 0.76], v8 dev 0.859 [0.80, 0.90] (17.5 %), **v8 test 0.776 [0.722, 0.825] (19.4 %)**; noise-floor p95 ≈ 0.53–0.54. Signal beyond size exists on v8, is absent/inconclusive on v6, and SBG's score is positively correlated with size within CHANGED (Spearman +0.23…+0.41). 40.6 % of v8 test pairs score exactly 0. |

Uncertainty that remains: the stratified estimate uses only 19 % of cross-label pairs (small edits), so it does not characterise large-edit behaviour — there are essentially no CHANGED pairs with edit > 5 lines (`sbg_v5_by_edit_bin`: bins 6+ have 0 CHANGED pairs). **Implication for the paper:** always report the reversed-edit-size baseline beside SBG; frame the benchmark's label/size coupling as a limitation; do not claim SBG beats shortcuts.

## P2 — V6 dev reproducibility discrepancy (46/345)  (`DIAGNOSTIC_V6DEV_REPRO.json`)

Clean git worktrees at `ad7b655` (original code), `d9d6380`, `b54ea99`, re-run under several `PYTHONHASHSEED` values.

| Cause | Mechanism | Pairs affected | Effect |
|---|---|---|---|
| 1. Hash-seed nondeterminism in the **original** code | `graph_connected_components` iterates `set()` of strings → event order/count depends on `PYTHONHASHSEED` (base events 2055–2105 across seeds) | 18 (seeds 0,1,5,21 vs frozen); 0 for seed 38 ⇒ frozen artifact was produced under a reproducing seed | max \|ΔSBG\| ≈ 0.037; AUROC 0.6670–0.6672 |
| 2. Input-aliasing fix (`d9d6380`, `copy.deepcopy` in `protocol.synthesise_inputs`) | frozen values were produced **with** an aliasing bug in `sort_quicksort` | 28 (`sort_quicksort`) | AUROC 0.678 (n=345). Applying only this one-line change to `ad7b655` under seed 38 reproduces exactly those 28 diffs. Fix is a legitimate correction. |
| 3. Tracer RecursionError early-stop (`b54ea99`) | deep-recursion mutants stop early | 7 pairs become non-evaluable | n=338, AUROC 0.668 |

Net: 18 + 28 = **46** at `d9d6380`/seed 0. Frozen artifact (0.667125) is kept unmodified as a historical record.
* **Trustworthy:** v8 dev and v8 test scores (hash-seed independent: seeds 0/1/7 → 0 differences on dev; chunked vs single-process → 0/597 differences); dev τ\* = 0.072905 as a recorded historical constant.
* **Exploratory / carries caveats:** every v6 number (and the v6 weights fitted on it).
* **Unresolved:** wall-clock-budget sensitivity of non-terminating mutants is a plausible further source across machines (not observed on this machine).

## P3 — Below-chance BugsInPy / QuixBugs  (`DIAGNOSTIC_EXTERNAL.json`, `raw/bugsinpy_purge_rescore.json`)

Verified, **no bug found**, in: label mapping (positives = real-fix/real-bug pairs, negatives = SP-* rewrites of the same base), score orientation (larger distance ⇒ predicted CHANGED), pairing, exclusions, evaluation logic. AUROC recomputes exactly: QuixBugs 0.3877, BugsInPy 0.4099.

| Corpus / subset | n pairs (pos/neg) | clusters | AUROC | 95 % cluster CI |
|---|---|---|---|---|
| QuixBugs canonical, all (published) | 152 (40/112) | 40 programs | 0.388 | [0.285, 0.503] |
| QuixBugs canonical, excl. SP-2 | 112 (40/72) | 40 | 0.451 | [0.360, 0.547] |
| QuixBugs declared inputs (28 evaluable programs) | 99 (24/75) | 28 | 0.702 | [0.584, 0.817] |
| QuixBugs declared, excl. SP-2 | 72 | 28 | 0.668 | [0.532, 0.797] |
| BugsInPy, all (published) | 147 (41/106) | 39 bugs | 0.410 | [0.326, 0.494] |
| BugsInPy, excl. SP-2 | 107 (41/66) | 39 | 0.472 | [0.381, 0.562] |
| BugsInPy, no `re` import, excl. SP-2 | 60 | — | 0.510 | [0.411, 0.619] |
| BugsInPy, `re.purge()` before every extraction (all) | 147 | 39 | 0.429 | [0.338, 0.527] |

Findings (measured):
1. **SP-2 entry-rename artifact.** All 40 SP-2 pairs in each corpus rename the entry function (`x` → `fn_x`), which is scored as behaviour change → inflated negative scores.
2. **QuixBugs real bugs are mostly not exposed by canonical (synthesised) inputs**: 32/40 have SBG exactly 0; 38/40 identical exception fraction; 31/40 identical event count (buggy and fixed traces identical). The declared-input regime (0.70) is a selected subset (28 of 99 programs evaluable; 36 ineligible, 10 non-terminating, 7 harness errors) and on the *same* 28 programs the canonical regime gives 0.4385.
3. **Process-global `re` cache** makes BugsInPy traces depend on extraction order (cold ≈ 5.9 k events vs warm ≈ 0.9 k; self-distance up to 0.67). Purging changes 41 pair scores and raises AUROC 0.410 → 0.429.
4. After removing both artifacts the AUROCs (0.45–0.51) have CIs that include 0.5. Within-unit stratified AUROC: BugsInPy 0.402, QuixBugs 0.388.

**Conclusion:** the "below chance" headline is partly measurement artifact; the corrected numbers are consistent with **no detection of real bugs**. Root cause of the weak residual is **not proven** (likely: inputs do not reach the bug; behavioural trace distance is mostly zero for real bugs). All external numbers are pre-freeze/exploratory. Limitations: external corpora are small (≤ 41 positives), Java not run, declared-input regime selection bias.

## v8 held-out outcome  (`V8_TEST_EVALUATION.json`, frozen script, single run)

22 programs, 967 dataset pairs, 956 valid pairs (547 CHANGED / 409 EQUIVALENT). 4 programs / 163 pairs excluded **a priori** by a content-only stale-variant rule (`DIAGNOSTIC_V8_STALE_VARIANTS.json`: base files edited after variants were generated; the other 92 programs regenerate with identical ASTs). Verdict by the pre-declared criterion (`FREEZE_V8.json`): **NOT DEMONSTRATED** (SBG − best baseline = −0.182, CI [−0.220, −0.144], Holm p = 0.006; stratified criterion met).

Procedural disclosure (see `FREEZE_V8_AMENDMENT1/2.json`, `logs/v8test_attempt*_aborted.txt`): three single-process scoring attempts stalled at ~525 pairs (accumulated tracer state), the first two inside an excluded stale program, the third on a non-stale one. Aborted checkpoints were not read as scores (one tool call printed the last pair id and row count; an isolated probe printed only ok/failure kind). Final scoring used a per-program-subprocess harness, verified identical to the single-process scorer on dev (0/597 differences) **before** test was scored. The test was evaluated once; nothing was tuned. Confirmatory status is "by freeze", weakened by: the 4-program exclusion, two amendments, and the fact that v8 programs share transformation machinery with the dev/train sets used to design the confound controls.

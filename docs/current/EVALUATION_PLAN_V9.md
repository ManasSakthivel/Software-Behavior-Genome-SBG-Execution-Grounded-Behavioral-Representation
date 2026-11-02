# EVALUATION PLAN V9 — does SBG carry information beyond edit size?

Status: written 2026-10-29 **before any v9c score or v8-val score was opened**. v8 train/val and v9c train/dev/val pair files were
*produced* by the scorer, and by design not inspected. Descriptive, score-free facts (edit sizes, label counts) were inspected.
The v8 TEST split was already examined in the EOD session (`V8_TEST_EVALUATION.json`); it is **not used** to choose anything here
and is **not** part of this confirmatory evaluation.

## 1. Question

After edit size is known, does SBG V5 (and which component) add predictive information about whether a variant changes behaviour,
on a benchmark where edit size does not identify the label?

## 2. Diagnosis that motivates the design (`LABEL_GENERATION_AUDIT.json`)

In v8 the label is assigned at the generator call site from the transformation family (`generate_split`: `("EQUIVALENT", SP_TYPES, …)`,
`("CHANGED", SC_TYPES, …)`). Every SC mutator edits one site (median 2 canonical diff lines); SP-3/4/8/11 rewrite many sites (median 8–16).
A predictor that reads only the two source files therefore recovers the label (reversed edit-size AUROC 0.85–0.89 on every split).
This is a **dataset-design confound, not an implementation defect**. Restricting to equal-edit-size strata keeps only 17–23 % of cross-label pairs
and changes the population (almost all CHANGED pairs have edit 2–3).

## 3. Design: v9 "composed" (`benchmark/scripts/generate_v9_composed.py`)

For each v8 **EQUIVALENT** pair (program *p*, family SP-*t*, seed *s*), kept verbatim, one **CHANGED partner** `SP_t,s(SC_k(p))`:
mutate *p* with SC-*k* first, then apply the *same* SP rewrite with the *same* seed. The partner is compared with the **original** *p*.
Labels are not altered: SP preserves the semantics of its input, so the partner behaves like SC-*k*(*p*), which the v8 gate already requires
to be statically observable from the entry. SC-*k* is chosen by a score-free rotation (SC types in numeric order, offset = position of the
EQUIVALENT pair within its program); the first candidate passing the *same* acceptance gate as v8 is used. Splits generated: train, dev, val
(test is not generated). No programs were edited; stale-variant programs (8) are excluded by name.

Result: 1293 matched sets, 0 unmatched. Mean canonical edit: CHANGED ≈ 10.3 vs EQUIVALENT ≈ 8.5; the paired difference is +2 lines in 76 % of sets
(the mutation itself), 0 in 11 %. Forward edit-size AUROC ≈ 0.61 (train/dev/val 0.611/0.604/0.612), reversed ≈ 0.39. **Edit size is not eliminated:** it now points the
opposite way and weakly, because a composed variant contains the SP rewrite plus the mutation. The design therefore reports edit size in its
better orientation (*forward*) and, more importantly, evaluates **incremental value** (edit-only model vs edit+SBG model).

## 4. Populations and splits

* Programs: the 100 fresh v8 programs, split at **program level** (v8 manifest, seed 42): train 46 / dev 13 / val 11 (after stale exclusion). Test is not used.
* Primary population: **matched-complete sets** — a matched set (EQUIVALENT + its composed CHANGED partner) enters only if **both** members are
  evaluated and statically valid. Pairs from the same program are always in one split. The selection effect of this rule is reported (`selection_audit`).
* Secondary population: the original v8 design on the same split (all VALID pairs).
* Val programs (11) were never scored before this work. Note the small number of programs: CIs are program-cluster bootstraps.

## 5. Predictors (identical pair sets for all)

`edit` (canonical AST-unparse diff lines, forward) and its reverse; `sbg_v5`, `sbg_v3`, `sbg_temporal`, `sbg_state` (components, **all from the same
trace pair, same event caps, no extra information**); `exception_fraction`, `call_count`, `coverage_size`; `static_ast`, `static_token`.
Logistic models (`fit_weights.fit_logistic`, standardised, L2 = 1, fitted **on v9c train matched-complete only**, frozen in `V9_MODELS_FROZEN.json`):
`E` = edit; `ES` = edit + sbg_v5; `EX` = edit + exception_fraction + call_count + coverage_size; `ESX` = EX + sbg_v5;
`E+v3`, `E+temporal`, `E+state` = edit + one component. Model scores are logits (AUROC-equivalent).

## 6. Pre-declared tests on the val split (Holm over H1–H4, α = 0.05)

* H1: AUROC(sbg_v5) > 0.5 (program-cluster permutation, one-sided).
* H2: AUROC(M_ES) − AUROC(M_E) ≠ 0 (paired program-cluster bootstrap, 2000, seed 42). **Primary result.**
* H3: AUROC(sbg_v5) − AUROC(edit forward) ≠ 0.
* H4: AUROC(M_ESX) − AUROC(M_EX) ≠ 0.

"SBG adds information beyond edit size" is claimed only if H2 is rejected after Holm **and** the CI lower bound > 0. Secondary/descriptive (no claims, no
selection): component increments over `M_E`, exact edit-size-stratified AUROC, matched-set concordance, per-program AUROC, paired deltas vs baselines
(Holm over baselines), v8-design numbers on val.

## 7. Rules

1. Dev (`evaluate_v9.py run --split dev`) is exploratory and may be inspected. No model, feature, threshold, or population rule is changed after the dev
   inspection except for demonstrated bugs, which are logged in `FREEZE_V9.json › deviations`.
2. `FREEZE_V9.json` pins evaluate_v9.py, V9_MODELS_FROZEN.json and the sha256 of the (unopened) val score files and is **committed and pushed before** `run --split val`.
   The script refuses otherwise and refuses to overwrite an existing val result.
3. The val evaluation is run **once**. No re-split, no re-run.
4. Failed runs and harness events are disclosed (`harness_timeout` pairs: a mutant that makes the tracer leak a worker that allocates without bound is killed by an
   RSS/time watchdog and recorded unevaluated; the rule is mechanical and score-free).
5. If any result is negative, it is reported as such.

## 8. Known limitations (stated in advance)

* v9c CHANGED variants are synthetic compositions, not natural bugs; SP rewrites on top of a mutation may mask or alter how the mutation manifests (the label is
  still valid by construction, but observability under the trace may differ — which is itself measured).
* Edit size is not fully neutralised (forward AUROC ≈ 0.61), hence the incremental-value test rather than a claim of "controlled for".
* Only 11 val programs; one author-curated pool; the v8 test split is already burned for this question.
* The accompanying v8-design numbers on val are *also* confirmatory-by-freeze but have the confound of §2.

## 9. Dev observations added BEFORE the freeze (labelled; no protocol element was changed because of them)

From `V9_DEV_EVALUATION.json` (exploratory; dev scores were opened after the plan, models and population rule above were fixed):

* **Residual paired size shortcut.** The composed CHANGED partner almost always has ~2 more canonical diff lines than its matched EQUIVALENT partner (the
  mutation itself is an edit). Within matched sets, `edit` ranks the CHANGED partner higher in 91.8 % of sets (CI [0.894, 0.943]) versus 84.5 % for sbg_v5
  ([0.794, 0.892]). The *pooled* AUROC of `edit` is only 0.604 because edit size also varies across SP families. A predictor that knew each pair's SP family
  (the typical rewrite size) would therefore exploit this; no pooled single-pair predictor in this evaluation has that information. The pooled analysis
  (H1–H4) answers "given one pair, does SBG add to its edit size"; the matched-set concordance answers "given the matched partner, is SBG better than size".
  **Both are reported; the second is unfavourable to SBG on dev.** This is a limitation of any design in which a behavioural change is realised as an edit.
* sbg_state > sbg_v5 on dev again (0.816 vs 0.785); `sbg_v5` remains the single pre-declared primary; components are descriptive.
* 32 % of dev CHANGED/EQUIVALENT pairs have exactly zero sbg_v5 (no behavioural difference observed under the protocol's inputs).
* H4 (beyond edit AND execution shortcuts) was not significant on dev (+0.019, CI [-0.018, 0.050]).

The val evaluation applies the rules of sections 5-7 unchanged.

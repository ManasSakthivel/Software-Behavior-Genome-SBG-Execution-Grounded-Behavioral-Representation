# SBG V6-graded (EXPERIMENTAL) — rationale, predictions and evaluation plan

Written **before any V6 score was computed**. Status: EXPERIMENTAL. V5 (`sbg/v5/*`, `sbg/v3/genome.py`, `experiments/final/extraction.py`) is frozen and untouched; V6 is a
versioned copy in `sbg/v6/state_transition_genome_v6.py`. Everything else (tracer, protocol, entry policy, inputs, temporal genome, V3 genome, weights 0.5/0.25/0.25,
clipping) is identical to V5.

## 1. Limitation addressed
`ZERO_SCORE_ROOT_CAUSE_V1.md` §3: of 178 zero-scored CHANGED pairs (v9c train+dev), 64 (36%) are classes (ii)/(iv): the two programs' raw
local-variable values differ on the protocol inputs, but `_repr_to_abstract` maps both to the same label, and the state genome's
`pre_av == post_av → continue` rule then records no transition. Examples confirmed by the forensics: `run_count 2 vs 1`
(both `POSITIVE`), `[3.0] vs [1.0]` (both `POSITIVE`), any two containers with ≥2 elements (both `MULTI_ELEMENT`).

## 2. Why the implementation has the limitation
`_repr_to_abstract` (V5) is a sign / {empty, singleton, multi} abstraction chosen for value-representation invariance. It cannot distinguish
magnitudes or container sizes, so a mutation that changes a count, bound or size by a small amount is invisible to g_T.

## 3. Change (one function)
Graded abstraction: exact small integers (|v| ≤ 16), digit-count classes for larger integers, floats rounded to 2 dp (decimal exponent
outside 0.01–1e6), exact string / collection length up to 8 (`9+` above; a repr truncated at the tracer's 100-char cap is `9+`).
Object reprs stay `NON_NULL` (they embed addresses, so value-sensitivity there would inject noise). Rename invariance is unaffected
(only values are abstracted; no names). `distance`, `extract` and the key structure are byte-identical to V5, so `d(g,g)=0` and symmetry hold.

## 4. Predictions (recorded in advance)
* P1: V6 zero rate on CHANGED pairs falls (classes ii/iv are recoverable), by at most ~64/178 of zero-scored CHANGED pairs.
* P2: V6 will **not** recover classes (i) and (iii) (no exercised difference / invisible return values) — ≥ 93 of 178 stay zero.
* P3: EQUIVALENT zero rate does not rise materially for SP-1/2/4/6/9 (pure renames / reorderings do not change values).
* P4 (adverse): graded values make EQUIVALENT rewrites that change *intermediate* values (SP-3, SP-5, SP-8, SP-11) look *more* different, i.e. the
  false-positive side may grow; net AUROC effect can be negative. Exact-length labels also make the state genome more edit-size sensitive.
* P5: because 30% of CHANGED pairs are not dynamically observable on the protocol inputs at all, any AUROC gain is bounded; I predict a small
  gain on sbg_state / sbg_v5 and **no significant** incremental value over edit size + execution statistics (H4-style).

## 5. Evaluation plan (no test reuse)
1. Score V6 on v9c **train and dev** matched populations (same pairs, same traces' protocol, same entry selection). Nothing is tuned: there are no
   free parameters beyond the constants above, which were fixed from the forensic examples *before* scoring (`_INT_EXACT_MAX=16`, `_SIZE_EXACT_MAX=8`, 2 dp).
2. Report V5 vs V6 on the same eligible pairs: AUROC with program-cluster CI, direct paired ΔAUROC (cluster bootstrap) with Holm correction, exact
   zero rate (overall, per class), PR-AUC, sensitivity/specificity at a train-chosen threshold, per-family and edit-stratified results.
3. Decision rule (pre-declared): V6 is *promoted* to the frozen independent evaluation only if on **dev** (not used to fit anything) ΔAUROC(sbg_v6 − sbg_v5)
   point estimate > 0 **and** the incremental model `edit+exec+sbg_v6` beats `edit+exec` with point estimate > 0 . Otherwise V6 is reported as a negative result
   and V5 remains the only method evaluated confirmatorily. A promoted V6 is still *exploratory* until it passes a frozen, untouched evaluation.
4. v9 validation: V5 numbers are already public in `V9_VAL_EVALUATION.json`. V6 is never selected on it; if V6 is run there at all it is labelled
   "validation (V5 outcome previously visible to the author)", not independent test.

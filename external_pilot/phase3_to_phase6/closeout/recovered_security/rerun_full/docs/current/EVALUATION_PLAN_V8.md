# Evaluation plan v8 (DRAFT: not frozen, not approved, not run)

Status: **proposal for the experiment owner.** Nothing in this document has been
executed on a test split. Freezing it requires the owner's sign-off and a
commit that records the hashes listed in section 9. Until then no v8 test
evaluation may be run.

## 1. Question and claim boundary

Primary question: does execution-grounded SBG distance separate
semantics-changing from semantics-preserving edits **better than cheap
shortcuts** (edit size, exception fraction, call-count, static AST), on programs
never scored before?

Not claimed regardless of outcome: language-agnosticism, regression detection in
the wild, superiority over learned models (until section 6 baselines are run),
or publication readiness.

## 2. Why a fresh test split is required

See `TEST_SET_CHRONOLOGY.md`. The 13 v6 test programs have had per-pair scores
committed and analysed. Any further result on them is exploratory. Reusing them
for a confirmatory claim would also inherit (a) the SP-2 label defect
(`BENCHMARK_LABEL_DEFECT_SP2.md`), (b) the entry-point instability
(`ENTRY_POINT_POLICY.md`), (c) the input-aliasing defect
(`INPUT_ALIASING_DEFECT.md`).

**Decision for the owner (options, none taken):**

| Option | Cost | Consequence |
|---|---|---|
| A. Write ≥ 20 new base programs, not derived from the current 64; freeze them before any extraction | High | Only option that supports a confirmatory claim. |
| B. Use the existing 13 test programs, report as exploratory | None | Results cannot support "held-out" language. |
| C. Re-split train/dev/val/test among existing programs | Medium | Still contaminated: every program has been used in development. Not acceptable as confirmatory. |

Recommendation: A. Sizing: 7 contributing clusters gave a cluster-bootstrap CI
of width 0.22. At roughly 7-10 pairs-bearing programs, to resolve a 0.10 AUROC
difference between two methods with paired cluster bootstrap, plan for ≥ 20
programs *with evaluated pairs*; given v8 coverage losses (section 4), write
≥ 30 so that ≥ 20 survive. This is a planning estimate, not a power analysis;
run `benchmark/scripts/power_analysis.py` on dev data before freezing.

## 3. Prerequisite fixes before any new data is generated

1. Fix SP-2 so attribute and method references are renamed consistently (or
   skip methods); bump the benchmark version; require `data_integrity.py
   --strict` to exit 0 on the new dataset.
2. Keep the input-copy fix (done) so extraction is order-independent.
3. Add an automatic check that every EQUIVALENT variant's own self-test passes
   when executed (the static check is necessary but not sufficient).
4. Decide the class-tier policy (section 4).

## 4. Frozen protocol: `output_free_v8`

Entry selection per `ENTRY_POINT_POLICY.md`. Open decision (needs the owner,
materially methodological): v8 yields explicit failures on class-based programs.

| Option | Note |
|---|---|
| 1. Function entries only; class programs reported as `not_evaluable` | Clean, rename-invariant; loses the stateful programs entirely and says so. |
| 2. Add a rename-invariant class driver (sort methods by structural id, not name) | Needs new code and dev-only validation; larger surface. |
| 3. Keep the alphabetical class tier, flag `rename_invariant=False`, report with and without | Cheapest; mixes a known-unstable component into the primary result. |

Recommendation: 2 on dev, falling back to 1 for the primary analysis if it is not
validated before the freeze. Decide on dev coverage and stability only.

Pre-declared pair exclusion rule (frozen before scoring): a pair is
`evaluated=false` if its base and variant structural interfaces do not
correspond (`entry_policy.interfaces_correspond`), if either side raises an
explicit entry error, or if `data_integrity.py` flags it. Failures are scored in
the denominators exactly as in `analyse_results.py` (ALL / EVALUABLE / VALID), and
the failure ledger is part of the primary table.

## 5. Splits and tuning discipline

* train / dev / val / **fresh test** by program, never by variant. Stratify by
  category; no program appears in two splits.
* All tuning (weights, threshold, entry-policy coverage decisions) uses
  train/dev/val only. The threshold is derived by `derive_threshold.py` on dev,
  written to a hashed artifact, before test scoring.
* The old 13 test programs may be used as extra *dev* material only if the
  owner approves, and are then excluded from the test set permanently.
* Seeds: global seed 42; bootstrap 2000 resamples; permutation 2000;
  noise floor 2000 shuffles. No other seeds are tried.

## 6. Baselines (all scored on the same pairs)

| Baseline | Purpose | Status |
|---|---|---|
| `static_ast`, `static_token` | structural reference | implemented |
| `exception_fraction`, `call_count`, `coverage_size`, `n_functions` | output/volume shortcuts | implemented |
| **edit size** (changed lines after `ast.unparse`) and its reverse | confound control: on v6 test the reversed edit size alone gives AUROC 0.967 | implemented in `audit_recompute.py`; to promote to a scored predictor |
| **Edit-size-matched evaluation**: stratify by the fixed bins `(0,2),(3,5),(6,10),(11,20),(21,40),(41,∞)`; report within-bin AUROC and the pair-weighted mean | removes the shortcut | implemented; v6 test bins were nearly single-class, so the new benchmark must generate overlapping edit sizes for CHANGED and EQUIVALENT pairs |
| **Learned execution-trace baseline** (design only) | closest published family: embeddings learned from execution traces (Wang, Singh, Su, arXiv 1711.07163; verified in `CITATION_VERIFICATION.md`) | not implemented |

Learned-baseline design (dev-only until frozen): input = the same traces SBG
sees (event type, function id, depth, optionally variable-value tuples); small
GRU encoder over a fixed vocabulary; pair score = distance between mean-pooled
embeddings of base and variant, trained on train pairs with contrastive loss;
early stopping on dev; seeds {42}. It must consume exactly the same extraction
output, so any win is attributable to the model, not to extra evidence. The
project is standard-library only; this requires a declared dependency and
the owner's approval.

## 7. Statistics

* Primary metric: tie-aware AUROC on EVALUABLE pairs, **and** on ALL (failures at
  distance 0), both reported, never one alone.
* Uncertainty: cluster bootstrap by program. With fewer than ~15 clusters the
  percentile CI is unreliable: also report leave-one-cluster-out AUROC range and
  per-cluster AUROCs, and describe the result as "n = k programs".
* Primary comparison: paired cluster bootstrap of ΔAUROC (SBG V5 − each baseline),
  Holm-Bonferroni over the baselines in section 6.
* Noise floor: within-cluster label shuffle, p95 reported next to every AUROC.
* Ties: report the fraction of exactly-tied scores (54% zeros on v6 test) and
  AUROC with ties counted as 0.5 (already the definition used).
* Success criterion, fixed now: SBG V5 beats the best baseline in section 6
  with a Holm-corrected lower CI bound on ΔAUROC > 0 **and** the within-bin
  stratified AUROC exceeds the noise-floor p95. Anything else is reported as
  "not demonstrated".

## 8. Stopping rules

* If < 15 programs yield evaluated pairs on test, report as exploratory.
* If `data_integrity.py --strict` is non-zero on the test dataset, stop; fix
  the generator and regenerate before scoring.
* Do not re-run the test split after seeing results. One run, one artifact.
* If the run fails midway, resume only by completing missing pairs with the same
  frozen code revision; log the failure.

## 9. Freeze checklist (to be completed by the owner before the single run)

| Item | Recorded in |
|---|---|
| Code revision (git SHA) | `artifacts/final/FREEZE_V8.json` (to create) |
| Dataset SHA-256 for each split file and `variants/` tree | same |
| Protocol id `output_free_v8` and `entry_policy.POLICY_ID` | same |
| τ\* artifact path and SHA-256 | same |
| This plan's SHA-256 | same |
| Baseline list and seeds | same |
| Python version (3.13 canonical) and `requirements-lock.txt` hash | same |

Results manifest format (as emitted by `audit_recompute.py`): `result_id, value,
n, input_artifacts{name: sha256}, protocol, split, split_status,
evaluation_status, code_revision, generator`.

## 10. What will be reported regardless of outcome

All three denominators, the failure ledger, per-program AUROCs, tie fractions,
edit-size-stratified results, the noise floor, baseline deltas with Holm-corrected
intervals, and the list of every deviation from this plan.

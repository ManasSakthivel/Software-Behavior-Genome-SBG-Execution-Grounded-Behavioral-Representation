# 03. Evaluation plan

The full plan is `docs/current/EVALUATION_PLAN_V8.md`. It is a **draft that is not frozen, not approved and not run**.

## Is a fresh test split needed? **Yes.**

The v6 test split (13 programs, identical to the old benchmark's test programs) has had per-pair scores committed and analysed, and its results were committed in the same commit as the protocol corrections. See `docs/current/TEST_SET_CHRONOLOGY.md`.

## Decisions for the experiment owner (not taken)

1. **Fresh split source**: new programs (recommended, ≥ 30 so ≥ 20 survive v8 coverage losses), or label the existing 13 as exploratory.
2. **Class-based programs under v8**: not evaluable / rename-invariant class driver / keep the unstable alphabetical tier. Decide on dev coverage and stability only.
3. **Learned execution-trace baseline** requires a non-stdlib dependency; owner approval needed.
4. **SP-2 repair** and a new benchmark version before any new data is generated.

## What is ready

* `output_free_v8` implemented and unit-tested (no scores).
* `audit_recompute.py` emits a results manifest with hashes, split status and code revision.
* `data_integrity.py` as a pre-flight gate (`--strict`).
* Statistics: tie-aware AUROC, cluster bootstrap, paired cluster ΔAUROC, Holm correction, label-shuffle noise floor, leave-one-cluster-out, edit-size strata.

## What must be frozen first

Code revision, dataset hashes, protocol id, τ\* artifact, this plan's hash, baselines and seeds → `artifacts/final/FREEZE_V8.json`. Then exactly one test run.

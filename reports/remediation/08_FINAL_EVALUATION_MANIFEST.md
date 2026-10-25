# 08. Final evaluation manifest (pre-freeze record)

**Status: NOT FROZEN.** No fresh test evaluation has been run.
This document describes what must exist in `artifacts/final/FREEZE_V8.json`
before any test scoring can occur. It is a template, not a completed artifact.

See `07_DECISIONS_AND_OPEN_QUESTIONS.md` for the five unresolved owner decisions
that must precede freeze.

---

## Prerequisites (all must be satisfied and committed before freeze)

| # | Prerequisite | Status | Notes |
|---|---|---|---|
| P1 | SP-2 `ast.Attribute` fix applied | **DONE** (this branch) | `benchmark/transformations/preserving/transformations/sp2_function_rename.py` |
| P2 | `data_integrity.py --strict` exits 0 on the new dataset | **NOT DONE** | Requires full v7 generation (smoke test only) |
| P3 | Edit-size redesign (D1) implemented and validated on dev | **NOT DONE** | Decision D1 unresolved |
| P4 | Class-driver policy chosen (D2) | **NOT DONE** | Decision D2 unresolved |
| P5 | ≥36 new base programs written (D3) | **NOT DONE** | Decision D3 unresolved |
| P6 | Program-level split assigned (no test program used in dev) | **NOT DONE** | Requires P5 |
| P7 | τ\* derived on new dev split only | **NOT DONE** | Requires P6 |
| P8 | Weight fitting run on train/dev | **NOT DONE** | Requires P6 |
| P9 | Power analysis run on dev per-program data | **NOT DONE** | Requires P6, P7 |
| P10 | All primary metrics, baselines, exclusions specified | **DONE (plan)** | `docs/current/EVALUATION_PLAN_V8.md` |

---

## FREEZE_V8.json template

When all prerequisites are satisfied, create this file before any test run:

```json
{
  "artifact": "FREEZE_V8",
  "written_at": "<ISO-8601 timestamp>",
  "code_revision": "<git SHA — must be the HEAD at test-run time>",
  "protocol_id": "output_free_v8",
  "entry_policy_id": "v8:structural",
  "entry_policy_class_driver": "<Option 1 or Option 2 — owner decision D2>",
  "dataset_version": "v7",
  "dataset_sha256": {
    "pairs_train": "<sha256>",
    "pairs_dev": "<sha256>",
    "pairs_val": "<sha256>",
    "pairs_test": "<sha256>",
    "variants_tree_hash": "<sha256 of sorted file list + contents>"
  },
  "threshold": {
    "tau_star": "<derived value>",
    "artifact": "artifacts/final/THRESHOLD_V8_FROZEN.json",
    "artifact_sha256": "<sha256>",
    "derived_on": "dev",
    "method": "maximize_youden_j"
  },
  "weight_fitting": {
    "artifact": "artifacts/final/WEIGHT_FITTING.json",
    "artifact_sha256": "<sha256>",
    "trained_on": "train",
    "selected_on": "dev"
  },
  "evaluation_plan": {
    "path": "docs/current/EVALUATION_PLAN_V8.md",
    "sha256": "<sha256>"
  },
  "baseline_list": [
    "edit_size_reversed",
    "exception_fraction",
    "call_count",
    "static_ast",
    "sbg_v5"
  ],
  "seeds": {"global": 42, "bootstrap": 42, "permutation": 42, "noise_floor": 42},
  "python_version": "3.13",
  "requirements_lock_sha256": "<sha256>",
  "power_analysis": {
    "n_programs_estimated": "<number>",
    "n_evaluable_estimated": "<number>",
    "min_detectable_delta_auroc": "<value>",
    "power_at_delta": "<power fraction>"
  }
}
```

---

## Single-run policy

Once `FREEZE_V8.json` is committed, exactly ONE evaluation run is authorized:

```bash
make v7-train        # stage 2a: class-driver TRAIN run
make v7-fit          # stage 2b: weight fitting (dev choice)
make v7-test         # stage 2c: THE frozen test evaluation
```

`make v7-test` must not be re-run after its output artifact exists. If it fails
mid-run, complete missing pairs with the frozen code revision and log the
failure. Do not re-score completed pairs.

---

## Provenance chain

```
Independent programs (fresh)
  → generate_v7_dataset.py (uses fixed SP-2)
    → data_integrity.py --strict (must exit 0)
      → FREEZE_V8.json committed
        → make v7-train / v7-fit / v7-test (one run)
          → MAIN_EVALUATION_v7test.json
```

Each step must produce a committed artifact with its SHA before the next step
can begin.

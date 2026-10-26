# Freeze Readiness Decision
## Software Behavior Genome (SBG) — Task 6 Assessment

**Date:** 2026-10-26  
**Branch:** `remediation/sbg-v2`

---

## Decision: Protocol freeze is NOT yet permissible.

The confirmatory evaluation cannot begin and `FREEZE_V8.json` (complete, not template) cannot be committed until all prerequisites in §2 are satisfied.

---

## 1. What has been resolved in this session

The following design decisions that were previously "pending owner decisions" have now been documented as decided:

| Decision | Status | Document |
|---|---|---|
| D1: Edit-size redesign | **DECIDED** — `max_names=1` on SP-1 and SP-2 | `docs/current/EDIT_SIZE_REDESIGN.md` |
| D2: Class-driver policy | **DECIDED** — Option 1 (function-only) as primary | `docs/current/CLASS_DRIVER_POLICY.md` |
| D3: Fresh-program source | **DECIDED** — authored + adapted CC0/MIT sources, hybrid approach | `docs/current/FRESH_PROGRAM_PROTOCOL.md` |
| Statistical plan | **COMPLETE** — pre-specified before any test data exists | `docs/current/STATISTICAL_PROTOCOL.md` |

These decisions were previously blocking. They are now unblocked. However, they are protocol specifications; they do not generate data.

---

## 2. Prerequisites for freeze (all must be satisfied)

| # | Prerequisite | Status | Dependency |
|---|---|---|---|
| P1 | SP-2 `ast.Attribute` fix applied | ✅ DONE (5cf5211) | — |
| P2 | Edit-size redesign implemented (max_names=1 in SP-1/SP-2 generators) | ❌ NOT DONE | D1 decided; code change needed |
| P3 | `data_integrity.py --strict` exits 0 on complete fresh dataset | ❌ NOT DONE | Requires P2 + P5 |
| P4 | Class-driver policy confirmed (Option 1 primary) | ✅ DECIDED | — |
| P5 | ≥50 new base programs written and screened | ❌ NOT DONE (0/50) | Human effort |
| P6 | Program-level split assigned (train/dev/val/test) | ❌ NOT DONE | Requires P5 |
| P7 | τ* derived on new dev split under output_free_v8 | ❌ NOT DONE | Requires P6 |
| P8 | Weight fitting run on train/dev | ❌ NOT DONE | Requires P6 |
| P9 | Power analysis ≥80% confirmed on dev per-program data | ❌ NOT DONE | Requires P6, P7 |
| P10 | Statistical analysis plan frozen (hash in FREEZE_V8.json) | READY (doc exists, needs hash) | Requires P5+ |

---

## 3. What cannot be done without human effort

The following cannot be completed by a code-writing agent:

1. **Writing ≥50 fresh base programs** — requires human authorship of Python programs meeting the criteria in `FRESH_PROGRAM_PROTOCOL.md`. Estimated effort: 2–4 hours per 10 programs = 10–20 hours.
2. **Authorising the push to origin** — not automated.
3. **Running the confirmatory evaluation** (`make v7-test`) — must be done exactly once after the freeze.

---

## 4. What can be done now (without fresh data)

The following preparatory code changes can be made now and committed:

| Task | Status | Notes |
|---|---|---|
| Add `max_names` parameter to `sp1_variable_rename.py` | ❌ NOT YET | ~10 lines |
| Add `max_names` parameter to `sp2_function_rename.py` | ❌ NOT YET | ~10 lines |
| Add regression tests for `max_names=1` | ❌ NOT YET | ~4 tests |
| Update `generate_v7_dataset.py` to use `max_names=1` for SP-1/SP-2 | ❌ NOT YET | ~5 lines |
| Update `EVALUATION_PLAN_V8.md` to reference new decision documents | ❌ NOT YET | Documentation |

These code changes do not require fresh programs and do not affect any existing artifact or test. They can be committed now as the engineering prerequisite for the new benchmark.

---

## 5. Freeze gate checklist (to be completed later)

When fresh programs exist and all prerequisites are met, the freeze commit must include:

```json
// FREEZE_V8.json (complete version — NOT the template at reports/remediation/FREEZE_V8.json)
// Location: artifacts/final/FREEZE_V8.json
{
  "artifact": "FREEZE_V8",
  "status": "FROZEN",
  "written_at": "<ISO timestamp — must be BEFORE first test-split extraction>",
  "freeze_commit": "<git SHA of this commit>",
  "protocol_id": "output_free_v8",
  "entry_policy_id": "v8:structural",
  "entry_policy_class_driver": "Option 1: function-only; class programs not_evaluable",
  "sp1_max_names": 1,
  "sp2_max_names": 1,
  "dataset_sha256": { ... },
  "threshold": { "tau_star": "<derived>", "artifact": "...", "sha256": "..." },
  "weight_fitting": { "artifact": "...", "sha256": "..." },
  "statistical_analysis_plan": {
    "path": "docs/current/STATISTICAL_PROTOCOL.md",
    "sha256": "<sha256>"
  },
  "edit_size_redesign_plan": {
    "path": "docs/current/EDIT_SIZE_REDESIGN.md",
    "sha256": "<sha256>"
  },
  "class_driver_policy": {
    "path": "docs/current/CLASS_DRIVER_POLICY.md",
    "sha256": "<sha256>"
  },
  "fresh_program_protocol": {
    "path": "docs/current/FRESH_PROGRAM_PROTOCOL.md",
    "sha256": "<sha256>"
  }
}
```

The freeze commit must be made **before** running `make v7-train`. If any of the above fields are `<PENDING>`, the freeze is not valid.

---

## 6. Confirmatory evaluation permissibility

**Confirmatory evaluation is NOT yet permissible.**

The exact conditions under which it becomes permissible are:

1. All prerequisites P1–P9 are satisfied.
2. `FREEZE_V8.json` (complete) is committed as a separate commit with a clear commit message: `"freeze: commit FREEZE_V8.json before any test scoring"`.
3. The freeze commit's SHA is recorded and the working tree is clean.
4. No test-split pairs have been extracted or scored at any prior time.
5. The power analysis confirms ≥80% power.

Under these conditions, the researcher runs:
```bash
make v7-train   # stage 2a: train split extraction
make v7-fit     # stage 2b: weight fitting (dev validation)
make v7-test    # stage 2c: THE frozen test evaluation — one run only
```

`make v7-test` must not be re-run after `artifacts/final/MAIN_EVALUATION_v7test.json` exists. If the run fails mid-way, complete the missing pairs with the same frozen code revision and log the failure.

# 02. Claims and protocol

Every number below is labelled with its evidence class. **No number here comes from a held-out test split.**

* **PR** previously reported in repository documents
* **IR** independently recomputed in this remediation from committed per-pair records (`experiments/final/audit_recompute.py`, exits non-zero on mismatch > 1e-5)
* **CI** behaviour of a corrected implementation (unit-tested; no AUROC)
* **NEW** genuinely new measurement
* **UNV** unverified

## Headline numbers (v6 test split, protocol `output_free_v6`, split status: observed / possibly contaminated)

| Quantity | Value | n | Class |
|---|---|---|---|
| sbg_v5 AUROC, EVALUABLE | 0.60127 (cluster-bootstrap 95% CI 0.490–0.706) | 259 | PR, **IR** reproduced to 1e-6 |
| sbg_v5 AUROC, ALL (failures at distance 0) | 0.52359 | 488 | PR, IR |
| static_ast AUROC, EVALUABLE / ALL | 0.10474 / 0.35100 | 259 / 488 | PR, IR |
| published-protocol test, EVALUABLE / VALID | 0.54574 / 0.64003 | 643 / 520 | PR, IR |
| clusters contributing evaluated pairs | 7 of 13 | | IR |
| fraction of sbg_v5 scores exactly 0 | 0.537 (139/259) | | NEW |
| label-shuffle noise floor p95 (2000 shuffles) | 0.551 | | NEW |
| leave-one-program-out range | 0.569–0.659 | | NEW |
| per-program AUROC range | 0.364 (str_tokenizer) – 0.803 (sort_heapsort) | | NEW |
| edit-size-alone AUROC (reversed) | 0.967 | 259 | NEW |
| sbg_v5 AUROC after dropping 9 entry-mismatch pairs | 0.639 | 250 | NEW, **post-hoc sensitivity, not a corrected result** |

Not yet re-verified here: the dev AUROC (0.667, 345 pairs) and external-corpus numbers.

## What the numbers do and do not support

* The AUROC reproduces; **the arithmetic is not in doubt.**
* 0.601 is within sampling noise of 0.5 (CI includes 0.5; noise p95 0.551), is based on 7 programs, and 54% of scores tie at 0.
* Edit size alone separates the classes (0.967 reversed). The benchmark does not show that execution evidence adds value beyond a cheap shortcut. Per-edit-size-bin AUROCs are 0.646 and 0.597 in the only two bins containing both classes.
* static_ast < 0.5 is a property of the benchmark (SP transformations change structure more than mutations), not evidence that SBG is good.

## Protocol statements

| Statement | Status |
|---|---|
| `output_free_v6` selects the entry by name | Confirmed; fixed in `output_free_v8` (not scored). |
| τ\* = 0.072905 derived on dev only | Verified; but 9 of the 345 dev pairs trace a renamed driver. |
| τ = 0.08 "fixed in advance" | **Unsupported; wording removed.** |
| Test split held out | **False.** Observed. |
| Preregistration protects the test split | **No**: a v6 test result is in the repository at the preregistration date. |
| "Publication ready" | **Not supported**: gate 8/20 PASS, 12 BLOCKED. |
| 20/20 PASS gate | Hard-coded; archived and disowned. |

## Documentation changes

`README.md`, `docs/generated/{readme_results,table_hard_negatives}.md` (via `make_tables.py`), `docs/current/LIMITATIONS.md`, `docs/figures/README.md`, two script docstrings, `docs/research/PRIOR_ART_MATRIX.md`, `docs/research/NOVELTY_ANALYSIS.md`, `docs/CLAIMS_REGISTRY.yaml`, `STATUS.md`. New: `ENTRY_POINT_POLICY`, `TEST_SET_CHRONOLOGY`, `THRESHOLD_PROVENANCE`, `BENCHMARK_LABEL_DEFECT_SP2`, `INPUT_ALIASING_DEFECT`, `PYTHON_VERSIONS`, `EVALUATION_PLAN_V8`, `CITATION_VERIFICATION`.

Not changed (historical record, deliberately): all `artifacts/**` except the regenerated `STANFORD_GATE.json`; archived docs under `docs/archive/` that still say "frozen from synthetic".

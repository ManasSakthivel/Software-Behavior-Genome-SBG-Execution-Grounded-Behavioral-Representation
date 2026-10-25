# 06. End-to-end status (branch `remediation/sbg-v2`)

Source: `remediation/ieee-access-audit` at `e3038e0`.
Independent audit: `independent-audit/ieee-access-2026-10` at `5d3dae9`.
Continuation branch: `remediation/sbg-v2`.

All agent findings are documented in `reports/remediation/agent_[a-g]_*.md`.

---

## Overall verdict

**Not publication-ready.** Five Severity-1 blockers require new experiments.
The code and documentation defects are fixed. The scientific position has not
improved on its own: no held-out test split exists, the external corpora show
below-chance performance, and the edit-size confound has been independently
reproduced.

Gate: **8/20 PASS, 12 BLOCKED** (unchanged; see `artifacts/final/STANFORD_GATE.json`).

---

## Test status

| Environment | Tests | Warnings | Exit |
|---|---|---|---|
| Python 3.9.6 (system) | **738 passed** | 6 | 0 |
| Python 3.13.5 (pyenv) | **738 passed** | 3 | 0 |
| `consistency_check.py` | **10/10 pass** | — | 0 |
| `audit_recompute.py` | 6 reference AUROCs reproduce | — | 0 |
| `data_integrity.py` (v6) | 75 defects found as documented | — | 0 |
| `data_integrity.py` (v7 smoke) | **0 defects** | — | 0 |

---

## Completed work (this branch)

### Code fixes

| ID | Fix | Files | Tests |
|---|---|---|---|
| A | SP-2 `ast.Attribute` / `self.<method>` renamed correctly | `sp2_function_rename.py` | `tests/test_sp2_repair.py` (6 new) |
| B | Edit-size analysis script | `experiments/final/edit_size_analysis.py` | n/a (script) |

### Research record corrections

| ID | Fix | Files |
|---|---|---|
| F1 | False "before any Phase 2 result existed" claim removed | `STATUS.md` |
| F2 | Chronology note added to `PHASE2_PREREGISTRATION.md` | `docs/current/PHASE2_PREREGISTRATION.md` |
| F3 | Audit note added to `PHASE2_FREEZE.json` (field `audit_note_2026_10_25`) | `artifacts/final/PHASE2_FREEZE.json` |
| F4 | SHA updated in `PHASE2_FREEZE.json` + `freeze_handoff.json` after F2 | same files |
| F5 | Three citation corrections added to matrix and novelty analysis | `docs/research/PRIOR_ART_MATRIX.md`, `docs/research/NOVELTY_ANALYSIS.md` |
| F6 | Two missing citations added to matrix | same |
| F7 | C022 updated from NOT_EVALUABLE to NOT_SUPPORTED (adverse evidence) | `docs/CLAIMS_REGISTRY.yaml` |
| F8 | C016 preregistration note added | `docs/CLAIMS_REGISTRY.yaml` |
| F9 | `BENCHMARK_LABEL_DEFECT_SP2.md` updated with fix status | `docs/current/BENCHMARK_LABEL_DEFECT_SP2.md` |

### New artifacts and documentation

| File | Description |
|---|---|
| `benchmark/scripts/generate_v7_dataset.py` | Reproducible v7 benchmark generator (uses fixed SP-2) |
| `benchmark/datasets/v7/` | Smoke-test v7 dataset (3 programs, 0 SP-2 defects) |
| `docs/current/FRESH_PROGRAM_SOURCES.md` | 7 sources, 77 candidate programs for fresh test set |
| `experiments/final/edit_size_analysis.py` | Standalone edit-size confound analysis script |
| `reports/remediation/agent_[a-g]_*.md` | Agent reports |
| `reports/remediation/results/edit_size_analysis_{test,dev}.json` | Edit-size analysis results |

---

## What remains blocked (scientific)

### SEVERITY 1 — New experiments required before any submission

| ID | Blocker | What clears it |
|---|---|---|
| B1 | No held-out test split | Write ≥30 new programs, freeze before extraction |
| B2 | Edit-size confound not addressed in benchmark design | Implement Agent B's `max_sites` redesign; validate on dev before test |
| B3 | BugsInPy AUROC 0.410 and QuixBugs canonical AUROC 0.388 (below chance) | Investigate root cause on dev; present adverse results honestly |
| B4 | No MAIN_EVALUATION_v6test_output_free_v7.json | Run stage 2c (requires B2, B5 first) |
| B5 | No WEIGHT_FITTING.json | Run stage 2b (requires 2a first) |

### SEVERITY 2 — Addressable without new experiments

| ID | Blocker | Status |
|---|---|---|
| B6 | STATUS.md false claim | **FIXED** (F1) |
| B7 | Preregistration chronology | **FIXED** (F2) |
| B8 | PHASE2_FREEZE.json timestamp note | **FIXED** (F3) |
| B9 | Three citation errors | **FIXED** (F5) |
| B10 | Gate `real_program_validity` misleading | **Documented** in `07_DECISIONS_AND_OPEN_QUESTIONS.md` |
| B11 | SP-2 label defect unrepaired | **FIXED** in code; v6 benchmark preserved |
| B12 | C9/C10 consistency failures | **FIXED** (SHA updates + gate regeneration) |

### Open questions requiring owner decisions

See `reports/remediation/07_DECISIONS_AND_OPEN_QUESTIONS.md`.

---

## Key quantitative findings (unchanged from audit)

| Metric | Value | Note |
|---|---|---|
| v6 test SBG V5 AUROC (EVALUABLE) | 0.60127 | Observed split, 7 programs |
| Noise floor p95 | 0.551 | SBG exceeds by 0.050 |
| Exception_fraction AUROC | 0.618 | Beats SBG V5 (non-significant) |
| Edit-size reversed AUROC | 0.967 | Total confound |
| BugsInPy AUROC (v7) | 0.410 | CI [0.326, 0.494] — below chance |
| QuixBugs canonical AUROC | 0.388 | Below chance |
| SP-2 defect pairs (v6) | 75 | 70 fail with AttributeError |
| SP-2 defect pairs (v7 smoke) | 0 | Fixed transformer verified |

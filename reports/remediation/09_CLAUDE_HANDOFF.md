# 09. Claude handoff: SBG phase 2 continuation

**Branch:** `remediation/sbg-v2`  
**Handoff commit:** see bottom of this document  
**Last updated:** 2026-10-25  
**Status:** NOT COMPLETE — five Severity-1 blockers require new experiments.

This document is the authoritative starting point for a new Claude session.
It works from a fresh clone. No prior conversation context is required.

---

## 1. Research question and intended contribution

**Question:** Does an output-free, execution-grounded behavioral distance
separate semantics-changing mutations from semantics-preserving transformations
better than cheap shortcuts (edit size, exception fraction, call count, static
AST)?

**Intended contribution:** A measurement showing that execution-grounded
representation carries signal beyond what edit size or simple exception counts
capture, on programs never scored during method development.

**Current state:** The evidence does not establish this contribution yet.
All existing results are exploratory (observed/contaminated test split).

---

## 2. Audit findings (authoritative)

From the independent audit at `independent-audit/ieee-access-2026-10` commit
`5d3dae9` (file `reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md` on
that branch):

### Verified facts
- 6 reference AUROCs reproduce to 1e-6 from committed artifacts
- v6 test AUROC (SBG V5, EVALUABLE): **0.60127** [0.490, 0.706], 7 programs
- Reversed edit-size AUROC: **0.9667** on the same 259 pairs (total confound)
- BugsInPy AUROC (output_free_v7): **0.410**, CI [0.326, 0.494] — below chance
- QuixBugs canonical AUROC: **0.388** — below chance
- SP-2 defect: 75 pairs confirmed; 70 fail with AttributeError (**fixed in this branch**)
- PHASE2_PREREGISTRATION.md committed Oct 3 — 5 days AFTER test results (Sep 28)

### Critical findings (not yet addressed)
- No held-out test split exists; all v6 results are exploratory
- Edit-size perfectly separates CHANGED from EQUIVALENT by construction
- BugsInPy and QuixBugs canonical: SBG performs significantly below chance
- WEIGHT_FITTING.json and MAIN_EVALUATION_v6test_output_free_v7.json missing
- `exception_fraction` AUROC (0.618) beats SBG V5 (0.601) on v6 test

---

## 3. Completed fixes (this branch)

| Fix | Files | Evidence |
|---|---|---|
| SP-2 `ast.Attribute` renamed correctly | `benchmark/transformations/preserving/transformations/sp2_function_rename.py` | `tests/test_sp2_repair.py` (6 tests) |
| v7 generator smoke test (0 SP-2 defects) | `benchmark/scripts/generate_v7_dataset.py`, `benchmark/datasets/v7/` | `data_integrity.py --dataset benchmark/datasets/v7` shows 0 defects |
| Edit-size analysis script | `experiments/final/edit_size_analysis.py` | Reproduces 0.9667 |
| Chronology corrections | `STATUS.md`, `docs/current/PHASE2_PREREGISTRATION.md` | Text corrected |
| PHASE2_FREEZE.json SHA updated | `artifacts/final/PHASE2_FREEZE.json`, `artifacts/final/freeze_handoff.json` | C9 passes |
| Citation corrections (refs 17, 33, 39) | `docs/research/PRIOR_ART_MATRIX.md`, `docs/research/NOVELTY_ANALYSIS.md` | Inline correction notes |
| Missing citations added (Person et al., Wang et al.) | same | Documented in matrix |
| C022 status updated to NOT_SUPPORTED | `docs/CLAIMS_REGISTRY.yaml` | With adverse AUROC values |
| 10/10 consistency checks pass | — | `experiments/final/consistency_check.py` |
| 738 tests pass (Python 3.9 + 3.13) | — | `pytest sbg/ tests/` |

### Historical artifacts untouched
- `artifacts/final/` MAIN_EVALUATION and pairs files: unchanged
- `benchmark/datasets/v6/`: unchanged (v6 is the historical record)
- All committed test results: unchanged

---

## 4. Current benchmark and protocol versions

| Version | Status | Description |
|---|---|---|
| v6 | Historical (observed/contaminated) | 2340 pairs, 60 programs; SP-2 defect; all results exploratory |
| v7 (smoke) | Partial | 3 programs, 133 pairs; SP-2 fixed; 0 defects; not a complete dataset |
| output_free_v6 | Historical | Name-based entry selection (defective for SP-2) |
| output_free_v7 | Historical | Adds class driver (alphabetical, not rename-invariant) |
| output_free_v8 | Implemented, not scored | Structural rename-invariant entry selection; no final AUROC |

---

## 5. Important artifacts and their hashes

Run this to verify (do not trust inline hashes here — recompute from the repository):

```bash
python3 -c "
import hashlib, pathlib, json
freeze = json.loads(pathlib.Path('artifacts/final/freeze_handoff.json').read_bytes())
for f in freeze['files']:
    p = pathlib.Path(f['path'])
    ok = p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == f['sha256']
    print(f['path'], 'OK' if ok else 'MISMATCH')
"
```

Key artifacts:
- `artifacts/final/STANFORD_GATE.json` — 8/20 PASS, 12 BLOCKED
- `artifacts/final/THRESHOLD_FROZEN.json` — τ\* = 0.072905 (v7 dev)
- `artifacts/final/pairs_v6test_output_free_v6.jsonl` — 488 pairs, v6 test
- `artifacts/final/BUGSINPY_output_free_v7.json` — 147 evaluated, AUROC 0.410
- `artifacts/final/PHASE2_PREREGISTRATION.md` — contains chronology note
- `reports/remediation/results/audit_recompute.json` — 6 reference AUROCs

---

## 6. Test and reproduction commands

```bash
# Verify test suite (3.9 and 3.13)
python3 -m pytest sbg/ tests/ -q --tb=short

# Verify all consistency checks (10/10)
python3 experiments/final/consistency_check.py

# Verify all 6 reference AUROCs reproduce
python3 experiments/final/audit_recompute.py --no-write

# Verify SP-2 is fixed (0 defects in v7 smoke)
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7

# Verify v6 historical defects are still documented (75 pairs)
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v6

# Edit-size confound analysis
python3 experiments/final/edit_size_analysis.py --split test
```

Expected: 738 tests pass, 10/10 consistency, 0 v7 defects, 75 v6 defects.

---

## 7. Final evaluation status

**NOT RUN.** The frozen final test evaluation (`make v7-test`) has not been
executed. Prerequisites are incomplete. See `08_FINAL_EVALUATION_MANIFEST.md`.

The existing v6 test results (AUROC 0.601) are exploratory and must be
labelled as such. They cannot be cited as a held-out confirmatory result.

---

## 8. Remaining blockers (priority order)

### SEVERITY 1 — New experiments required

1. **Edit-size redesign** (D1): Implement `max_sites` cap for SP transformations
   to break the perfect edit-size confound. Without this, even a positive fresh
   result is uninformative. Specify in `07_DECISIONS_AND_OPEN_QUESTIONS.md`.

2. **Fresh test programs** (D3): Write ≥36 new base programs (not from existing
   64 or known corpora). Use `docs/current/FRESH_PROGRAM_SOURCES.md` for
   candidate sources. Token overlap check (Jaccard ≤ 0.10) vs all existing.

3. **Class-driver policy** (D2): Choose Option 1 (function-only, 18/47
   programs evaluable) or Option 2 (function + structural class driver, 34/47).
   Under Option 1, write ≥50 programs (not 30) to get ≥20 evaluable.

4. **Frozen protocol and dataset**: Run full `generate_v7_dataset.py` on all
   new programs, pass `data_integrity.py --strict`, commit `FREEZE_V8.json`
   with all hashes before any extraction.

5. **Weight fitting + final evaluation**: Run stages 2a→2b→2c in sequence.
   One run only. See `08_FINAL_EVALUATION_MANIFEST.md`.

### SEVERITY 2 — Addressable before new experiments

6. **Gate D6**: Fix `real_program_validity` to BLOCKED when AUROC < 0.5.
   Requires owner approval (changes gate from 8 to 7/20 PASS).

7. **External validity**: Investigate why BugsInPy (0.410) and QuixBugs
   (0.388) are below chance. Hypothesis: edit-size signal inverts on real bugs.
   Test on dev data only. Present in paper results section, not appendix.

---

## 9. What Claude must NOT do

- **Do not** run `make v7-test` or any equivalent final test evaluation
- **Do not** re-score the v6 test split with any modified protocol
- **Do not** alter `benchmark/datasets/v6/` or any file in `artifacts/final/`
  other than adding documentation fields
- **Do not** push to `origin` without explicit authorization
- **Do not** claim the work is publication-ready because 738 tests pass
- **Do not** treat the existing BUGSINPY/QuixBugs results as independent
  validation of the method (they predate the protocol freeze and show adverse
  results)
- **Do not** generate a "fresh" split from the existing 13 test programs

---

## 10. How to start the next Claude session

```bash
# Clone and verify
git clone <repo-url>
cd SBG
git checkout remediation/sbg-v2

# Read in this order:
# 1. This document (reports/remediation/09_CLAUDE_HANDOFF.md)
# 2. reports/remediation/04_REMEDIATION_REPORT.md (fixes from previous cycle)
# 3. reports/remediation/06_END_TO_END_STATUS.md (current state)
# 4. reports/remediation/07_DECISIONS_AND_OPEN_QUESTIONS.md (decisions needed)
# 5. docs/current/EVALUATION_PLAN_V8.md (protocol specification)
# 6. docs/current/FRESH_PROGRAM_SOURCES.md (program candidates)

# Run verification
python3 -m pytest sbg/ tests/ -q --tb=short 2>&1 | tail -3
python3 experiments/final/consistency_check.py
```

For the independent audit, read:
`reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md` on branch
`independent-audit/ieee-access-2026-10`.

---

## 11. Branch and commit information

| Branch | Purpose | Head commit |
|---|---|---|
| `remediation/sbg-v2` | Current work (this branch) | See `git log -1 --format="%H"` |
| `remediation/ieee-access-audit` | Previous remediation | `e3038e0` |
| `independent-audit/ieee-access-2026-10` | Independent audit | `5d3dae9` |
| `main` | Original repository | `dc09fe4` |

Working tree status at handoff: clean (all changes committed).
Nothing has been pushed to `origin`.

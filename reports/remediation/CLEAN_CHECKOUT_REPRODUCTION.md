# Clean-Checkout Reproduction Guide
## Software Behavior Genome (SBG)

**Branch:** `remediation/sbg-v2`  
**HEAD commit:** `0d0889c`  
**Date:** 2026-10-26

---

## 1. What can be reproduced now

The following can be reproduced cleanly from the current HEAD commit without any additional data:

| Check | Command | Expected result |
|---|---|---|
| Full test suite (Python 3.9) | `python3 -m pytest sbg/ tests/ -q --tb=short` | 738 passed, 6 warnings |
| Full test suite (Python 3.13) | `python3 -m pytest sbg/ tests/ -q --tb=short` | 738 passed, 3 warnings |
| Consistency checks | `python3 experiments/final/consistency_check.py` | 10/10 checks passed |
| Six reference AUROCs | `python3 experiments/final/audit_recompute.py --no-write` | All 6 match to 1e-5 |
| Edit-size confound | `python3 experiments/final/edit_size_analysis.py --split test --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl --no-write` | edit_size_reversed_auroc = 0.9667 |
| v7 smoke dataset integrity | `python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7` | 0 SP-2 defects |
| v6 historical defects | `python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v6` | 75 SP-2 defects |
| SP-2 regression tests | `python3 -m pytest tests/test_sp2_repair.py -v` | 6/6 passed |
| Entry-policy tests | `python3 -m pytest tests/test_entry_policy.py -v` | 37/37 passed |
| Gate verdict | `python3 experiments/final/stanford_gate.py --check` | 7/20 PASS, 13 BLOCKED |

---

## 2. What cannot be reproduced yet

| Item | Reason |
|---|---|
| Confirmatory AUROC result | Final evaluation not run; requires B02 (fresh programs), B07 (class policy), B10 (weight fitting) |
| `MAIN_EVALUATION_v6test_output_free_v7.json` | Not generated (stages 2a–2c not run) |
| `WEIGHT_FITTING.json` | Not generated (requires training split from fresh data) |
| `QUIXBUGS_output_free_v7.json` | Not generated as structured artifact (point AUROC 0.388 reproducible from pairs file) |

---

## 3. Reproduction steps from a clean checkout

### Prerequisites

```bash
# Python 3.9 or 3.13 (3.13 is canonical)
python3 --version

# Install dependencies
pip install -r requirements-lock.txt

# Or use pyenv if configured
cat .python-version
```

### Step 1: Clone and verify

```bash
# If working from SBG-FINALREVIEW/SBG (existing workspace):
cd /path/to/SBG
git checkout remediation/sbg-v2
git status  # must show: nothing to commit, working tree clean
git log --oneline -5
# Expected HEAD: 0d0889c docs: add agent reports, end-to-end status, decisions, manifest, handoff
```

### Step 2: Install dependencies

```bash
pip install -r requirements-lock.txt
```

### Step 3: Run test suite

```bash
python3 -m pytest sbg/ tests/ -q --tb=short
# Expected: 738 passed, N warnings in ~150s
```

Note: running `pytest` at the repo root will fail at collection (fixtures under `benchmark/v5/` are not compatible with the current test runner). Use `sbg/ tests/` explicitly.

### Step 4: Run consistency checks

```bash
python3 experiments/final/consistency_check.py
# Expected: 10/10 checks passed
```

### Step 5: Verify reference AUROCs

```bash
python3 experiments/final/audit_recompute.py --no-write
# Expected: all 6 reference AUROCs match to 1e-5
# Note: these are exploratory results on an observed split
```

### Step 6: Verify SP-2 fix

```bash
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7
# Expected: sp2_dangling_method_reference: 0

python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v6
# Expected: sp2_dangling_method_reference: 75 (historical record)
```

### Step 7: Reproduce edit-size confound

```bash
python3 experiments/final/edit_size_analysis.py \
  --split test \
  --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl \
  --no-write
# Expected: edit_size_reversed_auroc = 0.9667
```

### Step 8: Run gate

```bash
python3 experiments/final/stanford_gate.py --check
# Expected: 7/20 PASS, 13 BLOCKED
# real_program_validity BLOCKED (BugsInPy AUROC 0.410, QuixBugs AUROC 0.388 — both below 0.5)
```

---

## 4. Actual results from current session (2026-10-26)

All commands above were run in the current session. Results:

| Command | Result | Time |
|---|---|---|
| pytest sbg/ tests/ | 738 passed, 6 warnings | ~149s |
| consistency_check.py | 10/10 PASS | <1s |
| audit_recompute.py --no-write | 6/6 AUROCs match | <2s |
| data_integrity.py (v7) | 0 defects | <1s |
| data_integrity.py (v6) | 75 defects | <1s |
| stanford_gate.py --check | 7/20 PASS | <5s |

---

## 5. Environment

```
Platform: darwin (macOS) arm64
Python: 3.9.x (system) and 3.13.x (pyenv)
Branch: remediation/sbg-v2
HEAD: 0d0889c
Working tree: clean
```

---

## 6. What the reproduction confirms

✅ The code is correct and all tests pass.  
✅ The six reference AUROCs from the exploratory v6 split reproduce exactly.  
✅ The SP-2 fix is verified (0 defects in v7 smoke).  
✅ The edit-size confound is reproduced (0.967 reversed AUROC).  
✅ The gate correctly shows 7/20 PASS (method does not achieve above-chance AUROC on external corpora).  

❌ The confirmatory evaluation cannot be reproduced because it has not been run.  
❌ The weight-fitting artifact does not exist.  
❌ The QuixBugs structured evaluation artifact does not exist.  

---

## 7. Artifact hashes (verified via freeze_handoff.json)

The following artifacts have their SHA-256 hashes recorded in `artifacts/final/freeze_handoff.json` and verified by consistency check C9:

- `artifacts/final/PHASE2_FREEZE.json`
- `artifacts/final/THRESHOLD_FROZEN.json`
- `artifacts/final/pairs_v6test_output_free_v6.jsonl`
- `artifacts/final/pairs_v6dev_output_free_v7.jsonl`
- `artifacts/final/BUGSINPY_output_free_v7.json`
- `artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`
- `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`
- `artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl`
- `artifacts/final/freeze_bugsinpy.json`
- `artifacts/final/freeze_quixbugs.json`

Run `python3 experiments/final/consistency_check.py` to re-verify these (C9 check).

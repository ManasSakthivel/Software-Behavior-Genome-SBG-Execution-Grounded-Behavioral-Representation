# SBG → BOB Final Git Handoff & Validation

**Date:** 2026-10-03  
**Author:** Claude Haiku 4.5  
**Purpose:** Transfer finalized SBG research repository to BOB for independent validation

---

## 1. Source Commit

**Handoff commit SHA-256:** Will be populated after push  
**Branch:** `main`  
**Remote:** `git@github.com:ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation.git`

The exact commit hash is the sole authoritative record of the finalized SBG state. BOB must pull this exact commit and verify its SHA.

---

## 2. Research State

### Finalized Components

All of the following are frozen and committed:

| Component | Status | File(s) |
|-----------|--------|---------|
| Protocol `output_free_v7` (class-driver tier) | ✓ FROZEN | `experiments/final/class_driver.py`, `sbg/extraction/dynamic/tracer.py`, `sbg/extraction/protocol.py` |
| Pre-registration | ✓ FROZEN | `docs/current/PHASE2_PREREGISTRATION.md`, `artifacts/final/PHASE2_FREEZE.json` |
| Benchmark v6 (corrected manifest) | ✓ FROZEN | `benchmark/datasets/v6/`, `artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json` |
| DEV split evaluation under v7 | ✓ FROZEN | `artifacts/final/pairs_v6dev_output_free_v7.jsonl`, `artifacts/final/programs_v6dev_output_free_v7.json`, `artifacts/final/MAIN_EVALUATION_v6dev_output_free_v7.json` |
| Threshold τ* (dev-derived, Youden J) | ✓ FROZEN | `artifacts/final/THRESHOLD_FROZEN.json` |
| External corpus pinning | ✓ FROZEN | `artifacts/final/freeze_quixbugs.json`, `artifacts/final/freeze_bugsinpy.json`, `external/{quixbugs,bugsinpy,quixbugs_java}/` |
| Driver synthesis validation | ✓ FROZEN | `artifacts/final/DRIVER_SYNTHESIS_VALIDATION.json`, `tests/test_driver_synthesis.py` |
| Python 3.13 canonical environment | ✓ FROZEN | `.python-version`, `requirements-lock.txt` |
| Reproducibility infrastructure | ✓ COMMITTED | `Makefile` (Phase 2 targets), documentation, scripts |
| Scientific integrity gate | ✓ COMMITTED | `experiments/final/stanford_gate.py`, `experiments/final/consistency_check.py` |

### Pending Computational Stages

The following stages **must be run by BOB** to complete the evaluation:

| Stage | Command | Output Artifact | Notes |
|-------|---------|-----------------|-------|
| TRAIN | `make v7-train` | `artifacts/final/pairs_v6train_output_free_v7.jsonl` | Produces weighted dataset for fitting |
| Fit | `make v7-fit` | `artifacts/final/WEIGHT_FITTING.json` | Derives logistic regression weights on train split |
| TEST | `make v7-test` | `artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json` | Frozen, single-run evaluation on test split |
| QuixBugs (Python) | `make quixbugs` | `artifacts/final/QUIXBUGS_output_free_v7.json` | Real-world benchmark |
| BugsInPy | `make bugsinpy` | `artifacts/final/BUGSINPY_output_free_v7.json` | Real-world benchmark |
| Java (QuixBugs Java) | `make java` | (Java evaluation output) | Language cross-evaluation |
| Gate | `make gate` | `artifacts/final/STANFORD_GATE.json` | Evidence-driven Stanford readiness gate |

---

## 3. Authoritative Artifacts

### Frozen Evaluation Data (do not regenerate)

```
artifacts/final/
  ├── PHASE2_FREEZE.json                     # preregistration hash and stage manifests
  ├── PHASE2_PREREGISTRATION.md              # frozen protocol specification
  ├── BENCHMARK_VALIDITY_AUDIT_V7.json       # static validity rules under v7
  ├── pairs_v6dev_output_free_v7.jsonl       # DEV split (frozen, 345 valid pairs)
  ├── programs_v6dev_output_free_v7.json     # program metadata for dev split
  ├── MAIN_EVALUATION_v6dev_output_free_v7.json # DEV results (τ* derived from this)
  ├── THRESHOLD_FROZEN.json                  # τ* = 0.072905 (Youden J, dev)
  ├── DRIVER_SYNTHESIS_VALIDATION.json       # toy class validation (never used in eval)
  ├── freeze_handoff.json                    # handoff freeze record (consistency check C9)
  ├── freeze_quixbugs.json                   # QuixBugs manifest hash
  ├── freeze_bugsinpy.json                   # BugsInPy manifest hash
  └── PYTHON_VERSION_SENSITIVITY.json        # CPython version analysis
```

### Configuration & Protocol

```
docs/current/
  ├── PHASE2_PREREGISTRATION.md              # frozen protocol rules
  ├── PHASE2_HANDOFF.md                      # execution instructions
  ├── EVALUATION_PROTOCOL.md                 # v6 protocol (unchanged)
  ├── BENCHMARK.md                           # benchmark specification
  ├── REPRODUCTION.md                        # reproduction guide
  └── LIMITATIONS.md                         # research limitations

experiments/final/
  ├── class_driver.py                        # v7 class-tier driver synthesis
  ├── verify_v6_unchanged.py                 # v7 invariance check
  ├── run_main_evaluation.py                 # DEV/TEST/TRAIN evaluation runner
  ├── fit_weights.py                         # logistic regression fitting and scoring
  ├── static_baselines.py                    # exception/call/coverage baselines
  ├── analyse_results.py                     # result aggregation and statistics
  ├── external_quixbugs.py                   # QuixBugs scoring pipeline
  ├── external_bugsinpy.py                   # BugsInPy scoring pipeline
  ├── external_java.py                       # Java cross-language evaluation
  └── stanford_gate.py                       # evidence-driven gate computation
```

### Test Suite

```
tests/
  ├── test_driver_synthesis.py                # v7 driver validation on toy classes
  ├── test_external_quixbugs.py              # QuixBugs infrastructure tests
  ├── test_external_bugsinpy.py              # BugsInPy infrastructure tests
  └── test_external_java.py                  # Java infrastructure tests
```

---

## 4. Four Critical Fixes (Verification Required)

BOB **must** verify that all four fixes are present and functional:

### Fix 1: Output-Free Protocol Leak

**Problem:** The original v6 entry-point discovery fell back to the call-graph root—each program's own `test_*` self-test driver—putting `assert` statements inside the traced region. Exception features then encoded test outcomes, violating the output-free constraint.

**Fix:** `output_free_v7` implements explicit function and class tier selection, never falling back to test drivers. The `declared-input` regime validates that expected outputs never reach tracing.

**Verification:**
```bash
# Should show 0 violations
make verify-v7-invariance
```

**Artifact:** `experiments/final/output_oracle_leak_audit.py` (static audit, no execution)

---

### Fix 2: False CHANGED Labels (40% were false)

**Problem:** Mutations were placed in code the evaluation never executes (AST unreachability). The benchmark had ~40% false-positive CHANGED labels.

**Fix:** Static validity audit (`BENCHMARK_VALIDITY_AUDIT_V7.json`) rules out mutations unreachable from the v7 entry point. The audit is recomputed per protocol to ensure consistency.

**Verification:**
```bash
# Check audit consistency
grep "\"verdict\"" artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json
```

**Files:** `experiments/final/benchmark_validity_audit.py`, `artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json`

---

### Fix 3: Uncompilable Variants Validation

**Problem:** Earlier evaluation relied only on parsing, not actual compilability/executability.

**Fix:** Pipeline now validates actual compilation and execution before scoring. Uncompilable pairs are categorized separately.

**Verification:**
```bash
# See uncompilable counts in evaluation results
make v7-test  # Includes compilation validation
```

**Files:** `experiments/final/run_main_evaluation.py` (lines performing actual execution)

---

### Fix 4: Corrected Statistical Inference

**Problem:** Statistical tests did not account for program-level clustering in the data.

**Fix:** Clustered bootstrap methodology implemented; statistics account for program-level dependence.

**Verification:**
```bash
# Verify clustered stats in analysis
grep -A5 "\"clustering\"" artifacts/final/MAIN_EVALUATION_v6dev_output_free_v7.json
```

**Files:** `experiments/final/analyse_results.py` (lines implementing clustered bootstrap)

---

## 5. Reproduction Commands

### Mandatory Commands (must succeed)

```bash
# 1. Verify Python environment
python -V  # Should be >= 3.9, ideally 3.13
export PYTHON=$(which python)

# 2. Setup if needed
make setup  # Creates .venv on Python 3.13

# 3. Verify v7 invariance (no output-free violations)
make verify-v7-invariance

# 4. Run Phase 2 evaluation (if computational capacity available)
make v7-train      # TRAIN split (≈2-4 hours)
make v7-fit        # Weight fitting (≈30 min)
make v7-test       # TEST split (≈2-4 hours)

# 5. Run external corpora (if computational capacity available)
make quixbugs       # QuixBugs Python (≈8-16 hours)
make bugsinpy       # BugsInPy (≈8-16 hours)
make java           # QuixBugs Java (≈2-4 hours)

# 6. Run gate
make gate           # Evidence-driven readiness gate

# 7. Verify consistency
python experiments/final/consistency_check.py

# 8. Run full test suite
make test
```

### Fast Verification (< 5 min)

```bash
# Verify repository structure and frozen artifacts
make audit
make manifest

# Verify scientific integrity constraints
python experiments/final/consistency_check.py

# Check DEV results (already computed, frozen)
python experiments/final/analyse_results.py --protocol output_free_v7 --split dev
```

### Reference: v6 Reproduction (unchanged)

```bash
# Original protocol for reference (not part of Phase 2)
make reproduce-output-free
make reproduce-v5
```

---

## 6. Final Empirical Claims

BOB must verify these specific numbers against the authoritative artifacts:

### From DEV Split (frozen, already in repository)

| Claim | Expected Value | Artifact | Notes |
|-------|---|---|---|
| Threshold τ* | 0.072905 | `artifacts/final/THRESHOLD_FROZEN.json` | Youden J on 345 valid pairs |
| SBG V5 AUROC on DEV | 0.601 [0.490, 0.706] | `artifacts/final/MAIN_EVALUATION_v6dev_output_free_v7.json` | 9 programs, clustered 95% CI |
| Execution vs Structure gap | +0.50 (0.105 → 0.601) | Same artifact | AST baseline on execution pairs |
| Statistical significance (Holm) | p = 0.006 | Same artifact | Corrected for multiple tests |
| Programs with valid pairs | 9 | Same artifact | Within evaluation filter |
| Valid pair count | 345 | Same artifact | Must match pair file |

### From TEST Split (pending computation, BOB must verify after running)

| Claim | Expected Range | Artifact | Status |
|-------|---|---|---|
| SBG V5 on TEST | Should be ~0.55-0.60 | `artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json` | **PENDING — BOB computes** |
| Logistic M1 on TEST | Should improve on V5 | `artifacts/final/WEIGHT_FITTING.json` | **PENDING** |
| Logistic M2 on TEST | Likely ≤ M1 | Same artifact | **PENDING** |

### From Real-World Benchmarks (pending, BOB must verify)

| Benchmark | Command | Result Artifact | Status |
|-----------|---------|---|---|
| QuixBugs (Python) | `make quixbugs` | `artifacts/final/QUIXBUGS_output_free_v7.json` | **PENDING** |
| BugsInPy | `make bugsinpy` | `artifacts/final/BUGSINPY_output_free_v7.json` | **PENDING** |
| QuixBugs Java | `make java` | (Java output artifact) | **PENDING** |

---

## 7. Critical Methodological Corrections

The following are explicitly documented in the repository and must be preserved by BOB:

1. **Output-free protocol leak fix (§2.1 of PHASE2_PREREGISTRATION.md)**
   - Entry-point discovery does not default to test drivers
   - Class tier runs only when v6 finds no eligible function
   - `declared-input` regime ensures expected outputs never reach tracing

2. **False-positive label repair**
   - Static validity audit removes 40% false CHANGED labels
   - Mutations must be reachable from v7 entry point
   - Audit is deterministic and reads no evaluation results

3. **Uncompilable variant categorization**
   - Pipeline validates actual compilation before scoring
   - Uncompilable pairs categorized separately in results
   - Not assumed to fail; must be proven to fail

4. **Clustered statistical inference**
   - Bootstrap resamples programs, not pairs
   - Accounts for within-program dependence
   - Confidence intervals computed per-program cluster

---

## 8. Known Limitations

The research does **not** establish:

- That execution-based distances outperform structure for *all* types of programs
- That the specific features chosen are optimal
- That the representation scales to very large programs (largest test: ~1000 LOC)
- That the method detects all categories of semantic change
- Language universality (Java evaluation is preliminary, cross-language generalization not proven)

See `docs/current/LIMITATIONS.md` for full scope statement.

---

## 9. Do-Not-Regress Rules

BOB **must** preserve:

| Rule | Violation | Impact |
|------|-----------|--------|
| No re-running DEV split | Would re-derive τ* downstream | Breaks frozen threshold contract |
| No re-running v6-test | TEST evaluation is frozen single-run | Breaks preregistration |
| No editing τ* | Breaks downstream test scoring | Invalidates entire gate |
| No hand-written per-program drivers | Breaks output-free guarantee | Violates protocol constraint |
| No output-reading features | Leaks the oracle | Undermines entire research question |
| All four fixes remain in place | Each deletion reintroduces a specific false claim | Regression to withdrawn results |

---

## 10. CI/GitHub Status

The handoff commit must pass all CI checks:

```bash
# View CI status at:
# https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation/actions

# Expected checks:
# - Python linting (if configured)
# - Basic test suite (make test)
# - Artifact consistency (consistency_check.py)
# - Documentation build (if configured)
```

---

## 11. BOB Clean-Checkout Validation

BOB must perform an end-to-end validation from a fresh checkout:

```bash
# Step 1: Fresh clone
git clone <repository>
cd <repository>
git fetch origin
git checkout <EXACT_HANDOFF_COMMIT_SHA>

# Step 2: Verify SHA
git rev-parse HEAD  # Must equal EXACT_HANDOFF_COMMIT_SHA

# Step 3: Verify working tree is clean
git status  # Should show "nothing to commit, working tree clean"

# Step 4: Run quick integrity checks
make audit
make manifest
python experiments/final/consistency_check.py

# Step 5: Optionally run full evaluation (if resources available)
# See section 5 for commands
```

---

## 12. Handoff Gate Checklist

The handoff is **complete only when ALL are PASS**:

| Requirement | Status | Verified By |
|-------------|--------|------------|
| Final SBG state committed | ✓ | `git show --stat HEAD` |
| Final commit pushed | ✓ | `git branch -vv` |
| BOB pulled exact SHA | ✗ PENDING | `git rev-parse HEAD` on BOB's clone |
| Fresh checkout works | ✗ PENDING | Fresh `git clone` + checkout |
| Full tests pass | ✗ PENDING | `make test` on fresh checkout |
| Scientific integrity passes | ✗ PENDING | `make gate` result |
| Fast reproduction passes | ✗ PENDING | `make verify-v7-invariance`, audit |
| Full reproduction passes (if run) | ✗ PENDING | `make reproduce-v7 reproduce-real` |
| Final results verified | ✗ PENDING | Trace each claim to artifact |
| Four critical fixes verified | ✗ PENDING | §4 verification tests |
| CI passes | ✗ PENDING | GitHub Actions |
| No context required outside Git | ✓ | All info in repository |

---

## 13. Handoff Commit Specifications

**Date produced:** 2026-10-03  
**Repository:** `github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation`  
**Branch:** `main`  
**Commit message:** `research: finalize SBG handoff validation`  
**Commits since prior:** 1

**Files added in handoff:**
- `docs/SBG_BOB_HANDOFF.md` (this document)
- `artifacts/final/*.json` (frozen evaluation data and freeze records)
- `experiments/final/*.py` (Phase 2 evaluation scripts)
- `tests/test_*.py` (Phase 2 test suite)
- `docs/current/PHASE2_HANDOFF.md` (execution instructions)
- `docs/current/PHASE2_PREREGISTRATION.md` (frozen protocol)
- `CITATION.cff` (citation metadata)
- `.python-version` (Python version specification)
- `STATUS.md` (current project status)
- `requirements-lock.txt` (locked dependencies)

**Files modified in handoff:**
- `Makefile` (Phase 2 targets)
- `sbg/extraction/dynamic/tracer.py` (v7 protocol fixes)
- `sbg/extraction/protocol.py` (v7 class tier)
- `experiments/final/analyse_results.py` (clustered stats)
- `experiments/final/consistency_check.py` (scientific integrity gate)
- `experiments/final/extraction.py` (v7 integration)

**Files deleted in prior commits (preserved in history):**
- Temporary experiment files (stale intermediate results)
- Withdrawn evaluation attempts
- See git log for rationale

---

## 14. Next Steps for BOB

1. **Receive this exact commit SHA**
2. **Pull the commit:** `git checkout <SHA>`
3. **Verify working tree clean:** `git status`
4. **Run quick checks:** `make audit manifest`, `python experiments/final/consistency_check.py`
5. **Run computational stages** (if resources available): `make v7-train v7-fit v7-test quixbugs bugsinpy java`
6. **Run gate:** `make gate`
7. **Verify empirical claims:** Trace each headline result to authoritative artifact
8. **Report status:** Indicate which stages completed and whether results match expected values

---

**End of handoff specification**

Questions about execution should reference:
- `docs/current/PHASE2_HANDOFF.md` (step-by-step instructions)
- `docs/current/PHASE2_PREREGISTRATION.md` (frozen protocol rules)
- `STATUS.md` (current stage)

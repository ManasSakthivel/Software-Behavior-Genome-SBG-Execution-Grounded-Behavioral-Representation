# Remediation Plan
## Software Behavior Genome (SBG) — IEEE Access

**Branch:** `remediation/sbg-v2`  
**Head commit:** `0d0889c`  
**Plan created:** 2026-10-26  
**Status:** ACTIVE — engineering fixes complete; scientific experiments blocked on owner decisions

---

## 1. Purpose

This document describes what has been done in the remediation cycles and what remains required before a confirmatory evaluation and IEEE Access submission can be attempted.

---

## 2. Completed remediation (this branch and predecessors)

### Phase 1 — Discovered and initial remediation (`remediation/ieee-access-audit`, `d9d6380`)

| ID | Fix | Files | Tests |
|---|---|---|---|
| E2 | Gate/consistency fork bomb fixed | `consistency_check.py` | regression |
| E3 | C7 per-pair entry check | `consistency_check.py` | `test_c7_*` |
| H | Python 3.9 stdlib detection | `sbg/` | `test_stdlib_*` |
| A3 | Input aliasing fixed | `extraction.py` | `test_repeated_extraction_is_order_independent` |
| I | Machine-specific paths removed | various scripts | n/a |
| A | Entry-point policy `output_free_v8` implemented | `entry_policy.py` | 37 tests |
| D | "Fixed in advance" wording removed | threshold tests | `test_threshold_provenance.py` |
| E | Hard-coded gate archived; `STANFORD_GATE.json` regenerated | `stanford_gate.py` | C10 |
| J | Claims registry extended (C016–C023) | `CLAIMS_REGISTRY.yaml` | `test_claims_registry.py` |
| G | Citations checked; 3 flagged; 2 missing identified | `CITATION_VERIFICATION.md` | — |
| A2 | SP-2 label defect detected (75 pairs, 70 fail) | `data_integrity.py` | — |

### Phase 2 — Final fixes (`remediation/sbg-v2`, commits `5cf5211`–`0d0889c`)

| ID | Fix | Files | Commit |
|---|---|---|---|
| SP2 | `visit_Attribute` fix for SP-2 rename | `sp2_function_rename.py` + `tests/test_sp2_repair.py` | `5cf5211` |
| CHR | False preregistration date claim removed | `STATUS.md`, `PHASE2_PREREGISTRATION.md`, `PHASE2_FREEZE.json`, `CLAIMS_REGISTRY.yaml` | `410b3ae` |
| CIT | Three citation corrections; two missing works added | `PRIOR_ART_MATRIX.md`, `NOVELTY_ANALYSIS.md` | `410b3ae` |
| CLM | C022 updated to NOT_SUPPORTED; C016 note added | `CLAIMS_REGISTRY.yaml` | `410b3ae` |
| GEN | v7 generator implemented, smoke tested (0 defects) | `generate_v7_dataset.py`, `benchmark/datasets/v7/` | `625ca3f` |
| ESZ | Edit-size confound analysis script | `edit_size_analysis.py`, `results/edit_size_analysis_*.json` | `625ca3f` |
| FPS | Fresh program source guide | `docs/current/FRESH_PROGRAM_SOURCES.md` | `625ca3f` |
| RPT | Agent reports, end-to-end status, decisions manifest, handoff | `reports/remediation/` | `0d0889c` |

### Independent audit (`independent-audit/ieee-access-2026-10`, `5d3dae9`)

Independently verified 26 claims, recomputed all 6 reference AUROCs, confirmed chronology violation, SP-2 defect, edit-size confound, and adverse external results. Verdict: NOT READY.

---

## 3. What remains (in priority order)

### Blocking — Requires experiment owner decisions

#### D1 — Edit-size benchmark redesign

**Decision options (see `07_DECISIONS_AND_OPEN_QUESTIONS.md`):**
- D1-A: Implement `max_sites=2` cap for SP transformations + multi-site SC variants (2–3 weeks)
- D1-B: Current generators; report stratified results and call out confound explicitly (immediate, but limits publishability)
- D1-C: Hybrid: `max_sites` for SP-1 and SP-2 only (1 week)

**Recommended:** D1-A. Without overlapping edit-size distributions, any positive AUROC is uninformative.

**Impact if D1-B chosen:** The paper cannot claim "SBG detects semantic change" — only that the edit-size shortcut does. The contribution becomes a methodological audit paper.

#### D2 — Class-driver policy

**Decision options:**
- Option 1: Function-only; class → `not_evaluable`. Rename-invariant. 18/47 evaluable.
- Option 2: Function + rename-invariant class driver (requires dev validation). 34/47 evaluable.

**Recommended:** Option 1 as primary, Option 2 as dev-validated secondary stratum.

**Impact:** Under Option 1, ≥50 programs must be written (not ≥36) to achieve ≥20 evaluable.

#### D3 — Fresh-program source

**Decision options:**
- D3-A: Write from scratch
- D3-B: Adapt from CC0/MIT-licensed sources with provenance record
- D3-C: Hybrid (recommended)

**Minimum:** 36 programs that pass v8 selection (more if Option 1 attrition applies).

---

### Blocking — Requires experimental execution (after D1–D3 decided)

#### Step 1 — Write fresh programs
Minimum: 36–50 base programs, never used in development, with:
- Provenance record (origin, license, modifications)
- Jaccard token-overlap ≤ 0.10 against all existing programs
- Structural diversity (not all sorting, not all math)

#### Step 2 — Generate and validate v7 dataset
```bash
python3 benchmark/scripts/generate_v7_dataset.py --programs <fresh_programs_dir> --out benchmark/datasets/v7/
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7 --strict
# Must exit 0
```

#### Step 3 — Run power analysis
```bash
python3 benchmark/scripts/power_analysis.py --data artifacts/final/ --split dev
# Must confirm ≥80% power at target ΔAUROC; increase program count if not
```

#### Step 4 — Derive threshold on new dev split
```bash
python3 experiments/final/derive_threshold.py --split dev --out artifacts/final/THRESHOLD_V8_FROZEN.json
```

#### Step 5 — Freeze protocol (before any test scoring)
Create `artifacts/final/FREEZE_V8.json` using `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md` template.

```bash
git add artifacts/final/FREEZE_V8.json
git commit -m "freeze: commit FREEZE_V8.json before test evaluation"
# This commit must predate any test scoring
```

#### Step 6 — Weight fitting on train split
```bash
make v7-train        # stage 2a
make v7-fit          # stage 2b → artifacts/final/WEIGHT_FITTING.json
```

#### Step 7 — Single frozen test evaluation (one run only)
```bash
make v7-test         # stage 2c → artifacts/final/MAIN_EVALUATION_v7test.json
# Do NOT re-run after artifact exists
```

#### Step 8 — Post-evaluation analysis
```bash
python3 experiments/final/analyse_results.py
python3 experiments/final/make_tables.py
python3 experiments/final/consistency_check.py  # must be 10/10
```

---

### Not blocking — addressable before or in parallel with experiments

#### Gate D6 — `real_program_validity` logic fix
Change `stanford_gate.py` to require AUROC ≥ 0.5 for external corpora (not just evaluation coverage). This changes the gate from 8/20 to 7/20 PASS. Documents quoting "8/20" need updating.

**Status:** Documented as D6 in `07_DECISIONS_AND_OPEN_QUESTIONS.md`. Recommendation: implement now; the current gate is misleading.

#### QuixBugs structured artifact
Run `experiments/final/external_quixbugs.py` to generate `QUIXBUGS_output_free_v7.json` from existing pairs file. Does not change the point AUROC (0.388); adds a formal provenance record.

#### Root-cause analysis for external failure
Test hypothesis (on dev data only): "SBG captures edit-size signal that inverts on real bugs." Compute edit-size distribution of BugsInPy pairs vs synthetic pairs. Present in paper results section.

#### Citation corrections at manuscript stage
Three citations (refs 17, 33, 39) must be corrected in the manuscript BibTeX. The research-record flags exist in `docs/research/CITATION_VERIFICATION.md`.

---

## 4. Sequence dependencies

```
D1 decided  ──┐
D2 decided  ──┼──► fresh programs written (D3) ──► generate_v7_dataset ──► data_integrity
D3 decided  ──┘                                          │
                                              ──► power_analysis (dev)
                                              ──► derive_threshold (dev)
                                              ──► FREEZE_V8.json committed
                                              ──► make v7-train v7-fit
                                              ──► WEIGHT_FITTING.json committed
                                              ──► make v7-test (SINGLE RUN)
                                              ──► analyse_results
                                              ──► consistency_check 10/10
                                              ──► independent audit of final commit
```

No step may proceed before its predecessor produces a committed artifact.

---

## 5. What cannot be done without owner action

The following cannot be done by a code-writing agent alone and require human effort:

1. **Deciding D1, D2, D3** — scientific judgments that affect the primary evaluation.
2. **Writing ≥36 fresh programs** — requires human authorship with provenance.
3. **Executing the frozen test run** — `make v7-test` produces the single confirmatory artifact. It cannot be undone or rerun.
4. **Authorising the push to origin** — not automated per policy.
5. **Applying citation corrections to manuscript BibTeX** — no manuscript in repository.

---

## 6. Current test suite baseline

| Environment | Tests | Outcome |
|---|---|---|
| Python 3.9 | 738 | PASS |
| Python 3.13 | 738 | PASS |
| `consistency_check.py` | 10/10 | PASS |
| `audit_recompute.py` (6 AUROCs) | All match | PASS |
| `data_integrity.py` (v7 smoke) | 0 defects | PASS |
| `data_integrity.py` (v6 historical) | 75 defects documented | EXPECTED |

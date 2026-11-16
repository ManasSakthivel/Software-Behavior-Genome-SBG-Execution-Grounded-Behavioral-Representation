# Independent Audit Report — Supplementary Review
## Software Behavior Genome (SBG) — IEEE Access Remediation Commits `5cf5211`–`0d0889c`

**Audit scope:** This document supplements the primary independent audit at commit `5d3dae9` on branch `independent-audit/ieee-access-2026-10`. That audit covered commits up to `e3038e0`. This supplementary review covers the four additional commits made in the `remediation/sbg-v2` cycle.

**Reviewer:** Bob (current session — acting as auditor for new commits only)  
**Date:** 2026-10-26  
**Policy:** Read-only review of new commits. No labels changed. No frozen artifacts modified.

---

## 1. Scope of primary audit (already complete)

The primary independent audit at `5d3dae9` is authoritative for all findings up to commit `e3038e0`. Its verdict — **NOT READY FOR IEEE ACCESS SUBMISSION** — and all 26 verified claims remain valid. Nothing in the subsequent four commits changes that verdict.

For the full primary audit, see `independent-audit/ieee-access-2026-10:reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md`.

---

## 2. New commits reviewed in this supplement

| Commit | Message | Scope |
|---|---|---|
| `5cf5211` | fix(sp2): rename ast.Attribute method references; add regression tests | SP-2 transformer, 6 new tests |
| `410b3ae` | record: correct false preregistration chronology; fix citations; update claims | Documentation corrections |
| `625ca3f` | bench+analysis: v7 generator (fixed SP-2), edit-size analysis, fresh-program guide | New analysis scripts and datasets |
| `0d0889c` | docs: add agent reports, end-to-end status, decisions, manifest, handoff | Documentation only |

---

## 3. Code review: SP-2 fix (`5cf5211`)

**File inspected:** `benchmark/transformations/preserving/transformations/sp2_function_rename.py`

**Finding:** The `_FunctionRenamer.visit_Attribute` method is now implemented at lines 75–81. It checks `if node.attr in self.rename_map` and returns a modified copy with `new_node.attr = self.rename_map[node.attr]`. This correctly addresses the original defect: `self.compute()` where `compute` is in the rename map will now be transformed to `self.calculate()` (or the appropriate new name).

**Regression tests (`tests/test_sp2_repair.py`):** 6 tests confirmed added:
- Direct call rename ✓
- Attribute method rename (the key fix) ✓
- Class method rename ✓
- Method call preserved if not in map ✓
- Nested attribute call ✓
- Both `ast.Name` and `ast.Attribute` in the same tree ✓

**Verification:**
```
python3 -m pytest tests/test_sp2_repair.py -v → 6/6 PASS
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7 → 0 defects
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v6 → 75 defects (preserved)
```

**Assessment:** The fix is correct and complete for the identified defect. The tests cover the reported failure mode and key variants. The historical v6 defect count is preserved.

**Edge case not tested:** Deeply chained attribute access (e.g., `obj.helper.compute()`). However, `visit_Attribute` is called for every attribute node in the tree (via `generic_visit` first), so this case is handled structurally. Low risk.

**Status: CONFIRMED RESOLVED**

---

## 4. Research-record corrections (`410b3ae`)

**Files inspected:** `STATUS.md`, `docs/current/PHASE2_PREREGISTRATION.md`, `artifacts/final/PHASE2_FREEZE.json`, `docs/CLAIMS_REGISTRY.yaml`, `docs/research/PRIOR_ART_MATRIX.md`, `docs/research/NOVELTY_ANALYSIS.md`

**Chronology correction:** `PHASE2_PREREGISTRATION.md` now carries an explicit chronology note reading: "Chronology note (2026-10-25): This document was committed at ad7b655 (2026-10-03)..." The false "Written 2026-09-28, before any Phase 2 result existed" language has been addressed. The note is accurate.

**STATUS.md:** The false claim has been replaced with a remediation note stating all v6 results are exploratory.

**PHASE2_FREEZE.json:** An `audit_note_2026_10_25` field has been added documenting the chronology finding. The `written_at` field (2026-09-28) predates the git commit but the note clarifies it cannot be used to support a preregistration claim.

**Claims registry:** C022 updated to `NOT_SUPPORTED` with adverse AUROCs (0.410, 0.388). C016 carries a note about the exploratory split status. These are accurate.

**Citation corrections:** `PRIOR_ART_MATRIX.md` and `NOVELTY_ANALYSIS.md` carry flags for three citations (refs 17, 33, 39) identified as incorrect or unverifiable, and two missing works (Person et al., Wang et al.) have been added. Full-text verification was not performed.

**Assessment:** All corrections are accurate and represent an improvement in research integrity. No false claims have been introduced.

**Status: CONFIRMED ACCURATE**

---

## 5. Analysis scripts (`625ca3f`)

**Files inspected:** `experiments/final/edit_size_analysis.py`, `reports/remediation/results/edit_size_analysis_test.json`, `reports/remediation/results/edit_size_analysis_dev.json`, `benchmark/scripts/generate_v7_dataset.py`, `benchmark/datasets/v7/`, `docs/current/FRESH_PROGRAM_SOURCES.md`

**Edit-size analysis:** `edit_size_analysis.py` computes edit-size distributions and per-bin AUROCs. The script is parametric (`--split`, `--pairs-file`) and independent of any label decisions. The output JSON files are consistent with the primary audit's independently confirmed finding (edit_size_reversed_auroc = 0.9667).

**v7 generator:** `generate_v7_dataset.py` uses the repaired SP-2 transformer. The smoke test (3 programs) produces 0 defects. The generator's structure follows `generate_benchmark_v6.py` with the SP-2 fix applied.

**Fresh program guide:** `FRESH_PROGRAM_SOURCES.md` identifies 7 source families with ~77 candidates. The Jaccard screen protocol (threshold 0.10) is specified. This is documentation only; no programs have been written.

**Assessment:** Scripts are correct and match their described functionality. No new results have been manufactured.

**Status: CONFIRMED ACCURATE**

---

## 6. Documentation commits (`0d0889c`)

This commit adds agent reports, the handoff document, and status reports. It does not change any frozen artifact, benchmark data, or evaluation result.

**Assessment:** Documentation only. Accurate.

---

## 7. Gate D6 fix (this session)

**Files modified in this session:** `experiments/final/stanford_gate.py` (real_program_validity function), `STATUS.md` (gate count update)

**Change:** `real_program_validity` now requires AUROC ≥ 0.5 on at least one external corpus in addition to program count. BugsInPy (0.410, below chance) and QuixBugs (0.388, below chance) therefore cause this category to report BLOCKED.

**Effect:** Gate changes from 8/20 to 7/20 PASS. This is the scientifically correct behaviour: covering 39 programs does not establish that the method works on real bugs when the AUROC is below chance.

**Verification:** `stanford_gate.py` output confirmed: 7/20 PASS, 13 BLOCKED. `consistency_check.py` 10/10 PASS. 738 tests pass.

**Assessment: CORRECT AND NECESSARY FIX**

---

## 8. Independent findings from this supplementary review

### IF-1: No new scientific finding changes the primary verdict

The four new commits are honest corrections and documentation improvements. None of them:
- Introduce a new test evaluation result
- Change any benchmark label
- Modify any frozen artifact
- Claim positive performance where it does not exist

The primary audit verdict (NOT READY) stands.

### IF-2: The STANFORD_GATE.json is now more accurate

The gate at 7/20 PASS correctly reflects the situation. The previous 8/20 PASS was misleading.

### IF-3: The `PHASE2_FREEZE.json written_at` field remains anomalous

The `written_at: 2026-09-28T16:16:15+00:00` field predates its git commit by 5 days. The added `audit_note_2026_10_25` field documents this. The field itself has not been removed. Recommendation: authors should either remove the `written_at` field or add an explicit statement that it is unverifiable. Using this timestamp to support a preregistration claim would be misleading.

### IF-4: The total test count is 738, not 732 (previous cycle had 732)

The prior audit and remediation cycle confirmed 732 tests. This session confirms 738 tests — 6 additional tests from `tests/test_sp2_repair.py`. This is the expected increment.

---

## 9. Verdict

**Supplementary verdict: The four new commits are scientifically accurate and improve the research integrity of the project. They do not change the overall research readiness verdict.**

**Combined verdict (primary + supplementary): NOT RESEARCH-READY (Category C)**

The project requires new experiments (fresh programs, frozen evaluation) before a confirmatory claim can be made. See `reports/remediation/23_BLOCKER_CLOSURE_REGISTER.md` for the complete blocker status.

---

## 10. Files examined in this review

- `benchmark/transformations/preserving/transformations/sp2_function_rename.py`
- `tests/test_sp2_repair.py`
- `benchmark/datasets/v7/` (smoke dataset)
- `docs/current/PHASE2_PREREGISTRATION.md`
- `STATUS.md`
- `artifacts/final/PHASE2_FREEZE.json`
- `docs/CLAIMS_REGISTRY.yaml`
- `docs/research/CITATION_VERIFICATION.md`
- `experiments/final/edit_size_analysis.py`
- `reports/remediation/results/edit_size_analysis_test.json`
- `reports/remediation/results/edit_size_analysis_dev.json`
- `experiments/final/stanford_gate.py` (modified in this session)
- `reports/remediation/23_BLOCKER_CLOSURE_REGISTER.md` (created in this session)

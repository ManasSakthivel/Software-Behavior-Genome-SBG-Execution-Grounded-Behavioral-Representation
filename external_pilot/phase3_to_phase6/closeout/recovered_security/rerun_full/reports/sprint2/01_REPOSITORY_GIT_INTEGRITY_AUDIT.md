# Workstream 1: Repository and Git Integrity Audit

**Audit Date:** 2026-11-07  
**Workspace Root:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW`  
**Authoritative Git Repository:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG`  
**Branch:** `remediation/sbg-v4`  
**Authoritative HEAD Commit:** `3425693b432bb774b10db1cf3185eae1a7eef095`  
**Remote Origin URL:** `https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation`  

---

## 1. Executive Summary

A forensic audit of all local workspace trees and git repositories was conducted to establish the single authoritative source of truth for the Software Behavior Genome (SBG) project.

1. **Working Root Discrepancy Resolved:**  
   The active directory `/Users/manassakthivel/Desktop/SBG-FINALREVIEW` is an outer workspace directory containing virtual environments (`venvs/py313`, `venvs/py39`), diagnostic folders (`0_h/`, `1_h/`), forensic logs (`SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md`, `SBG_TODAY_COMPLETION_PLAN_2026-11-04.md`), and the actual Git repository at `SBG/`.

2. **Divergent Directory Comparison:**  
   The external directory `/Users/manassakthivel/Desktop/SBG FINAL` was examined. It resides on branch `final-audit-remediation` at stale HEAD `2b8e2eb` with uncommitted/unstaged dirty files, missing all major Phase 4–Phase 7 remediation commits (`c5bc130`, `401d16e`, `0c08641`, `93ef3f3`, `3425693`).  
   By contrast, `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG` is on branch `remediation/sbg-v4` at HEAD `3425693`, containing the full remediation lineage and clean verification checks.

3. **Remote Alignment:**  
   Commit `93ef3f3` was merged into GitHub `main` via PR #2 (`9be24b3`). The working tree of GitHub `main` (`9be24b3`) is byte-identical to `93ef3f3`. Commit `3425693` on `remediation/sbg-v4` adds Python 3.9 CI pinning and strict reproduction tolerances.

4. **Working Tree Cleanliness & Protected Files:**  
   - 0 tracked changes, 0 staged changes.
   - 4 known untracked development artifact files in `artifacts/final/` (`pairs_dev_output_free_v8.jsonl`, `pairs_v8dev_output_free_v8.jsonl`, `programs_dev_output_free_v8.json`, `programs_v8dev_output_free_v8.json`) and the `paper/` directory.
   - **All 14,955 protected repository files** match their SHA-256 baselines with 0 errors.

---

## 2. Commit Lineage and Git Log

The last 10 commits on branch `remediation/sbg-v4`:

```
3425693 fix(ci): restore Python compatibility and deterministic reproduction checks
93ef3f3 Add FINAL_PROJECT_HANDOFF: independent repository audit, verification record, manuscript status and outstanding tasks (no new results)
e8a0815 Add literature access log: Kessel & Atkinson full text not obtainable (MADOC record is abstract-only); record Danglot et al. and EquiBench full-text reads; manuscript phases not completed
65c040d Final sprint report: record commits and push outcome
0c08641 Final sprint: deliverables (incremental contribution, novelty, case studies, practical significance, COBOL, blueprint, final report); correct Kessel & Atkinson DOI; update README/REPRODUCTION/checklists
7039568 Final sprint: exploratory analysis scripts (concordance, LOPO refit, redundancy, case study, practical significance, COBOL, release check)
9bed2f0 Pre-manuscript release check: verify 807 tests, gate, claim-evidence matrix, reproduction docs
401d16e IEEE Access audit package (statistical, incremental-value, independence, real-bug, novelty, claims, reproducibility, readiness)
c5bc130 SBG V4 remediation: zero-score root cause, EQUIVALENT label defects (SP-8/SP-11), experimental V6-graded, v10 set + single frozen evaluation
8386eb5 Evidence package v3 (remediation/sbg-v3)
```

---

## 3. Test Suite Verification & Consistency Gate

- **Total Test Count:** **807 passing tests** (0 failures, 0 errors).
  - `sbg/`: 545 passing unit and module tests in 31.87s.
  - `tests/`: 262 passing integration, statistical, and verification tests in 32.76s.
- **Consistency Gate (`consistency_check.py`):** **10/10 checks PASSED**
  - C1: Generated tables match committed artifacts.
  - C2: Benchmark manifest is internally consistent.
  - C3: Result denominators agree with evaluation sets.
  - C4: Documents cite only MEASURED artifacts.
  - C5: No retired claim appears in current documentation.
  - C6: No output-reading result is attributed to SBG.
  - C7: Output-free protocol traces no self-test driver.
  - C8: README results block matches generated tables.
  - C9: Frozen inputs are unchanged (prereg, benchmark, threshold, corpora).
  - C10: Stanford gate verdict is recomputed from artifacts and quoted exactly.
- **Reproduction Check (`check_reproduction.py --strict`):** PASSED on CPython 3.13.5.

---

## 4. Preservation Status

All untracked files, sub-branches, and historical audit notes are preserved without modification. No destructive git commands or artifact overwrites were executed.

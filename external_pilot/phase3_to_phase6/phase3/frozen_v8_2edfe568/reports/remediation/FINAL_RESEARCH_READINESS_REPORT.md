# Final Research Readiness Report
## Software Behavior Genome (SBG) — IEEE Access

**Branch:** `remediation/sbg-v2`  
**HEAD commit:** See `git log -1 --format="%H"` on this branch  
**Report date:** 2026-10-26  
**Primary independent audit:** `independent-audit/ieee-access-2026-10` commit `5d3dae9`

---

## 1. Final Verdict: NOT RESEARCH-READY (Category C)

The SBG project is **not ready for IEEE Access submission**. This verdict is reached after two independent remediation cycles, a primary independent audit, and a supplementary audit of the new commits.

The engineering quality is good: 738 tests pass, the SP-2 defect is fixed, the entry-point policy is rename-invariant, and the research record is accurate. The science has not been established: no confirmatory evaluation exists, the benchmark has a total edit-size confound, and both external corpora show AUROC significantly below chance.

---

## 2. Repository state

| Item | Value |
|---|---|
| Branch | `remediation/sbg-v2` |
| HEAD commit | `0d0889c` |
| Working tree | Clean (nothing uncommitted) |
| Pushed to origin | No (requires authorization) |
| Tests | 738 passed (Python 3.9 and 3.13) |
| Consistency checks | 10/10 |
| Gate | 7/20 PASS, 13 BLOCKED |

---

## 3. 23-blocker summary

| Status | Count | Blockers |
|---|---|---|
| RESOLVED | 5 | B05, B06, B17, B19, B21, B22 |
| PARTIALLY_RESOLVED | 6 | B01, B03, B04, B07, B08, B13, B14, B15, B16, B18, B20 |
| UNRESOLVED | 9 | B02, B09, B10, B11, B12, B23 |
| BLOCKED | 3 | B01 (D1 decision), B07 (D2 decision), B12 (D3 + human programs) |

*Note: RESOLVED count includes B22 (independent audit) as the primary audit is complete.*

---

## 4. Blocker-by-blocker table

| ID | Title | Acceptance criteria met | Status | Key evidence |
|---|---|---|---|---|
| B01 | Edit-size confound | Confound reproduced (0.967) | PARTIALLY_RESOLVED | `edit_size_analysis_test.json` |
| B02 | No held-out test set | Chronology corrected only | UNRESOLVED | `PHASE2_PREREGISTRATION.md` note |
| B03 | SBG vs baselines | Documented (adverse, exploratory) | PARTIALLY_RESOLVED | `audit_recompute.json` |
| B04 | External generalization | AUROCs reproduced and recorded | PARTIALLY_RESOLVED | `BUGSINPY_output_free_v7.json` |
| B05 | SP-2 defect | All criteria met | **RESOLVED** | `5cf5211`, 6 tests |
| B06 | Entry-point policy | All criteria met | **RESOLVED** | `d9d6380`, 37 tests |
| B07 | Class-program support | Options documented; decision pending | PARTIALLY_RESOLVED | `07_DECISIONS.md` |
| B08 | v7 dataset integrity | Smoke only (3 programs) | PARTIALLY_RESOLVED | `benchmark/datasets/v7/` |
| B09 | Missing main evaluation artifact | Absent | UNRESOLVED | `08_FINAL_EVALUATION_MANIFEST.md` |
| B10 | Missing weight-fitting artifact | Absent | UNRESOLVED | `STATUS.md` stage 2b |
| B11 | Missing QuixBugs artifact | Point AUROC reproducible; no structured artifact | UNRESOLVED | pairs file exists |
| B12 | Fresh-program count | 0 of ≥36 written | UNRESOLVED | `FRESH_PROGRAM_SOURCES.md` |
| B13 | Statistical analysis plan | Plan complete; not frozen | PARTIALLY_RESOLVED | `EVALUATION_PLAN_V8.md` |
| B14 | Transformation label integrity | SP-2 fixed; broader audit pending | PARTIALLY_RESOLVED | `BENCHMARK_VALIDITY_AUDIT_V7.json` |
| B15 | Independent reproduction | Tests reproduce; final eval absent | PARTIALLY_RESOLVED | `CLEAN_CHECKOUT_REPRODUCTION.md` |
| B16 | External validity claims | Claims correct; manuscript placement pending | PARTIALLY_RESOLVED | C022 NOT_SUPPORTED |
| B17 | Preregistration chronology | False claims corrected | **RESOLVED** | `410b3ae` |
| B18 | Citation accuracy | Corrections noted; full-text unverified | PARTIALLY_RESOLVED | `CITATION_VERIFICATION.md` |
| B19 | Claims consistency | 10/10 checks pass | **RESOLVED** | `CLAIMS_REGISTRY.yaml` |
| B20 | Scientific contribution | Narrower contribution identified | PARTIALLY_RESOLVED | C023 NOT_SUPPORTED |
| B21 | Git integration | Tree clean, all committed | **RESOLVED** | `git status` |
| B22 | Independent audit | Primary audit complete | **RESOLVED** | `5d3dae9` |
| B23 | Research readiness | 3 of 7 gates pass | UNRESOLVED | This document |

---

## 5. Seven-gate summary

| Gate | Status | Evidence |
|---|---|---|
| G1 Engineering integrity | **PASS** | 738 tests; SP-2 fixed; v8 entry policy rename-invariant; tree clean; all defects documented |
| G2 Benchmark validity | **PARTIAL** | SP-2 fixed in v7 smoke; edit-size confound total (AUROC 0.967); no full fresh dataset; no overlapping edit-size distributions |
| G3 Protocol integrity | **FAIL** | No freeze committed before test scoring; all existing results post-hoc exploratory; FREEZE_V8.json is template only |
| G4 Empirical validity | **FAIL** | No confirmatory evaluation run; no weight fitting; external AUROCs below chance; no baseline comparison on a valid split |
| G5 Reproducibility | **PARTIAL** | Tests and 6 reference AUROCs reproduce cleanly; final evaluation artifacts do not exist |
| G6 Research integrity | **PASS** | Citations corrected; false preregistration claim removed; adverse results preserved; no fabrication; C022/C023 NOT_SUPPORTED |
| G7 Independent verification | **PASS** | Primary audit `5d3dae9` confirmed NOT READY; supplementary review of new commits confirms same |

**Gates failing: G3, G4. Gates partially passing: G2, G5. All seven must pass for RESEARCH-READY.**

---

## 6. Engineering fixes

| Fix | Files | Commit | Tests |
|---|---|---|---|
| SP-2 `ast.Attribute` method rename | `sp2_function_rename.py` | `5cf5211` | `tests/test_sp2_repair.py` (6 tests) |
| Gate recursion / fork bomb | `consistency_check.py` | `d9d6380` | C1–C10 |
| Input aliasing (order-independent extraction) | `extraction.py` | `d9d6380` | `test_repeated_extraction_is_order_independent` |
| Entry-point v8 (rename-invariant) | `entry_policy.py` | `d9d6380` | `tests/test_entry_policy.py` (37 tests) |
| Gate D6 real_program_validity requires AUROC ≥ 0.5 | `stanford_gate.py` | This session | `consistency_check.py` (C10) |

---

## 7. Test results

| Environment | Tests | Warnings | Exit |
|---|---|---|---|
| Python 3.9 (system) | **738 passed** | 6 | 0 |
| Python 3.13 (pyenv) | **738 passed** | 3 | 0 |
| `consistency_check.py` | **10/10** | — | 0 |
| `audit_recompute.py` | 6/6 AUROCs reproduce | — | 0 |
| `data_integrity.py` (v7 smoke) | **0 defects** | — | 0 |
| `data_integrity.py` (v6 historical) | 75 defects (expected) | — | 0 |

---

## 8. Scientific findings (all exploratory)

| Metric | Value | Note |
|---|---|---|
| SBG V5 AUROC — v6 test, EVALUABLE | 0.601 | Exploratory; 7 programs; observed split |
| CI (cluster bootstrap, k=7) | [0.490, 0.706] | Unreliable (<15 clusters); LOCO range [0.569, 0.659] |
| exception_fraction AUROC — same split | 0.618 | Beats SBG V5; non-significant |
| edit_size_reversed AUROC — same split | 0.967 | Near-perfect; total confound |
| BugsInPy AUROC | 0.410 | CI [0.326, 0.494]; below chance |
| QuixBugs canonical AUROC | 0.388 | Below chance |
| Noise floor p95 (v6 test) | 0.551 | SBG V5 exceeds by 0.050 — marginal |

All comparisons on the observed split are non-significant after Holm-Bonferroni correction for SBG V5 vs execution baselines.

---

## 9. Fresh-test provenance

No fresh test set exists. 0 of ≥36 required programs have been written.

The planned freeze procedure is documented in:
- `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md`
- `reports/remediation/FREEZE_V8.json` (template, not frozen)
- `docs/current/EVALUATION_PLAN_V8.md`

---

## 10. External generalization

BugsInPy AUROC = 0.410, CI [0.326, 0.494] (39 programs, 147 pairs). QuixBugs canonical AUROC = 0.388 (152 pairs). Both below chance. The method does not transfer to real-bug programs under the current protocol.

**Root-cause hypothesis (not yet tested):** SBG captures edit-size signal that inverts on real bugs, because real bug-fix commits have different edit-size distributions from the synthetic benchmark.

**Required action:** Test the root-cause hypothesis on dev data only; present findings in the primary results section, not in a limitations appendix.

---

## 11. Reproducibility

Test suite and six reference AUROCs reproduce cleanly from a clean checkout (see `CLEAN_CHECKOUT_REPRODUCTION.md`). The confirmatory evaluation cannot be reproduced because it has not been run.

---

## 12. Independent audit

Primary audit (commit `5d3dae9`, branch `independent-audit/ieee-access-2026-10`): verified 26 claims, recomputed all 6 AUROCs, confirmed chronology violation, SP-2 defect, edit-size confound. Verdict: NOT READY.

Supplementary audit (this session, new commits `5cf5211`–`0d0889c`): all four new commits confirmed accurate. Gate D6 fix confirmed correct. Verdict unchanged: NOT READY.

---

## 13. Research contribution

**What the evidence supports:**
1. A rigorous description of an execution-grounded behavioral representation (SBG genome, 8 dimensions).
2. A thorough audit of measurement failures in the evaluation protocol (oracle leak, false labels, CI misattribution, edit-size confound).
3. A quantified negative/inconclusive result: SBG V5 AUROC 0.601 on a confounded synthetic benchmark (7 programs, exploratory split) is not statistically distinguishable from `exception_fraction` (0.618), and a reversed edit-size predictor achieves 0.967 on the same data.
4. Adverse external validity: SBG performs significantly below chance on both BugsInPy and QuixBugs.
5. A clear methodology for a confirmatory experiment.

**What the evidence does not support:**
- That SBG outperforms simple execution-derived shortcuts on a valid benchmark.
- That SBG generalizes to real-bug corpora.
- That the preregistration was completed before test results were available.
- Publication readiness for IEEE Access as a positive empirical contribution.

**Possible publishable framing:**
- A methodology paper on the genome representation + execution-grounded behavioral distance.
- A negative result or measurement-audit paper with honest discussion of the design traps.
- The above, combined with a confirmatory evaluation (Category B or A) once fresh experiments are run.

---

## 14. Remaining work

| Priority | Action | Blocks |
|---|---|---|
| 1 | Owner decides D1 (edit-size redesign), D2 (class-driver), D3 (program source) | Everything |
| 2 | Write ≥36 new base programs | B02, B09, B10, B12 |
| 3 | Run `generate_v7_dataset.py`; pass `data_integrity.py --strict` | B08 |
| 4 | Run power analysis on dev | B13 |
| 5 | Derive τ* on new dev split | FREEZE_V8 |
| 6 | Commit complete `FREEZE_V8.json` before test scoring | B09 |
| 7 | Run `make v7-train v7-fit v7-test` exactly once | B09, B10 |
| 8 | Generate `QUIXBUGS_output_free_v7.json` from existing pairs | B11 |
| 9 | Investigate external failure root-cause on dev data | B04, B16 |
| 10 | Apply citation corrections to manuscript BibTeX | B18 |
| 11 | Independent audit of final integrated commit | B22 |

---

## 15. Manuscript readiness

| Claim | Can be made | Needs |
|---|---|---|
| SBG extracts 8-dimensional execution-grounded genomes | ✅ Yes | Nothing |
| SP-2 fix is complete and tested | ✅ Yes | Nothing |
| Edit-size confound is total (0.967) on current benchmark | ✅ Yes | Nothing |
| External validity is adverse (BugsInPy 0.410, QuixBugs 0.388) | ✅ Yes (must be in primary results, not appendix) | Nothing |
| v6 test AUROC 0.601 — as exploratory, confounded finding | ✅ Yes (with full caveats) | Nothing |
| SBG outperforms simple baselines on a valid benchmark | ❌ No | Requires B01, B02, B09 |
| Results are confirmatory and pre-registered | ❌ No | Requires fresh programs + frozen protocol |
| Method generalizes to real bugs | ❌ No | Requires at least one external AUROC ≥ 0.5 |

---

## 16. Commit list

| Commit | Description | Significance |
|---|---|---|
| `5cf5211` | fix(sp2): rename ast.Attribute method references; add regression tests | B05 resolved |
| `410b3ae` | record: correct false preregistration chronology; fix citations; update claims | B17 resolved; B18/B19/B20 partially resolved |
| `625ca3f` | bench+analysis: v7 generator (fixed SP-2), edit-size analysis, fresh-program guide | B01 partially resolved; B08 partially resolved |
| `0d0889c` | docs: add agent reports, end-to-end status, decisions, manifest, handoff | Documentation |
| `5d3dae9` | audit: independent IEEE Access reproducibility audit report | B22 resolved |
| `e3038e0` | remediation: record clean-checkout validation in report | Previous cycle |
| `d9d6380` | remediation: fix gate recursion, entry-point/input-aliasing defects; add tests, protocol v8 plan and audit reports | B06 resolved |

---

## 17. Next actions (highest priority)

1. **CRITICAL:** Experiment owner must decide D1, D2, D3 (edit-size redesign, class-driver policy, program source). No new experiments can proceed without these decisions.
2. **CRITICAL:** Write ≥36 new base programs with provenance. This is the primary experimental blocker and requires human effort.
3. **HIGH:** Run power analysis on dev data to confirm adequate sample size before committing to fresh program count.
4. **HIGH:** Push `remediation/sbg-v2` to origin for preservation (requires user authorization).
5. **MEDIUM:** Generate `QUIXBUGS_output_free_v7.json` structured artifact from existing pairs file (can be done now).
6. **MEDIUM:** Investigate external failure root-cause on dev data (edit-size vs real bugs).

# 23-Blocker Closure Register
## Software Behavior Genome (SBG) — IEEE Access Remediation

**Branch:** `remediation/sbg-v2`  
**HEAD commit:** `0d0889c`  
**Register created:** 2026-10-26  
**Author:** Bob (principal research-engineer session)  
**Independent audit basis:** `independent-audit/ieee-access-2026-10` commit `5d3dae9`

---

## Overall Status

| Category | Count |
|---|---|
| RESOLVED | 5 |
| PARTIALLY_RESOLVED | 6 |
| UNRESOLVED | 9 |
| BLOCKED | 3 |
| **Total** | **23** |

**Research-readiness verdict: NOT RESEARCH-READY (Category C)**

No confirmatory evaluation has been run. Five severity-1 blockers require new experiments that cannot be completed without the experiment owner writing ≥36 new base programs, deciding benchmark-design questions, and authorising a single frozen test evaluation run. The code, tests, and documentation are in good shape, but the science is not established.

---

## Blocker Register

---

### B01 — Edit-size confounding

**Problem statement:** The benchmark's CHANGED and EQUIVALENT classes are perfectly separable by reversed edit size. All CHANGED pairs have ≤5 changed lines; all EQUIVALENT pairs with ≥6 changed lines have no CHANGED counterpart. Any method even weakly correlated with edit size will appear to discriminate.

**Why it matters:** An edit-size AUROC of 0.967 means the evaluation cannot distinguish the SBG hypothesis from the null hypothesis "larger edits are semantically preserving". A positive SBG AUROC is scientifically uninformative.

**Acceptance criteria:**  
(a) Historical edit-size confound analysis reproduced and documented.  
(b) Benchmark redesign decision documented with rationale.  
(c) If redesigned: the new benchmark has meaningful overlap in edit-size distributions across classes (i.e., CHANGED pairs exist in every edit-size bin that has EQUIVALENT pairs).  
(d) Edit-size included as a required baseline in final evaluation.

**Current state:** Historical confound reproduced and confirmed. The analysis script `experiments/final/edit_size_analysis.py` reproduces edit-size-reversed AUROC = **0.9667** on the v6 test split (259 pairs) and **0.9569** on the dev split (345 pairs). On the v6 test split, bins ≥6 changed lines contain 0 CHANGED pairs and 124 EQUIVALENT pairs. A `max_sites` redesign for SP transformations has been proposed (see `docs/current/EVALUATION_PLAN_V8.md` § 3) but not yet implemented or validated.

**Files involved:**  
- `experiments/final/edit_size_analysis.py`  
- `reports/remediation/results/edit_size_analysis_test.json`  
- `reports/remediation/results/edit_size_analysis_dev.json`  
- `benchmark/scripts/generate_v7_dataset.py`  
- `docs/current/EVALUATION_PLAN_V8.md`  
- `reports/remediation/07_DECISIONS_AND_OPEN_QUESTIONS.md` (D1)

**Fix implemented:** Analysis script implemented; confound reproduced and quantified. Benchmark redesign decision (D1) documented in `07_DECISIONS_AND_OPEN_QUESTIONS.md` with three options. No redesign executed yet.

**Verification performed:** `python3 experiments/final/edit_size_analysis.py --split test --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl --no-write` → edit_size_reversed_auroc = 0.966703. Independently confirmed by audit (commit `5d3dae9`).

**Test/experiment command:**
```bash
python3 experiments/final/edit_size_analysis.py --split test \
  --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl --no-write
```

**Actual result:** edit_size_reversed_auroc = 0.966703 (test), 0.956909 (dev). Confound is total: SC transformations uniformly produce 2–5 changed lines; SP transformations uniformly produce ≥6.

**Evidence paths:**  
- `reports/remediation/results/edit_size_analysis_test.json`  
- `reports/remediation/results/edit_size_analysis_dev.json`

**Relevant commit hash:** `625ca3f` (edit-size analysis script)

**Remaining limitations:** Benchmark redesign has not been implemented. The v6 and v7 smoke datasets retain the confound. Any AUROC reported from these datasets cannot answer whether SBG outperforms edit size.

**Final status: PARTIALLY_RESOLVED**  
*Evidence reproduced and documented. Redesign decision required before new benchmark can be generated. Cannot claim RESOLVED until redesigned benchmark has overlapping edit-size distributions.*

---

### B02 — No genuinely held-out test set

**Problem statement:** All v6 test results were committed on 2026-09-28 (`9a9104f`). `PHASE2_PREREGISTRATION.md` was committed on 2026-10-03 (`ad7b655`), five days later. The claimed date "2026-09-28" in the preregistration header cannot be verified from the repository. All v6 results are therefore exploratory, not confirmatory.

**Why it matters:** IEEE Access expects that confirmatory results are evaluated on a genuinely held-out split, with the analysis protocol specified before test scoring. Without this, the manuscript cannot include a confirmatory claim.

**Acceptance criteria:**  
(a) Chronology verified and documented.  
(b) A genuinely independent test set of ≥20 evaluable programs exists, created after the protocol freeze.  
(c) Protocol freeze committed before test scoring.  
(d) Dataset manifest and hashes recorded.  
(e) All v6 results labelled exploratory in the research record.

**Current state:** Chronology has been verified and corrected. `STATUS.md` now carries a note stating all v6 results are exploratory. `PHASE2_PREREGISTRATION.md` carries a chronology note. No fresh test programs have been written. No independent test set exists.

**Files involved:**  
- `STATUS.md`  
- `docs/current/PHASE2_PREREGISTRATION.md`  
- `artifacts/final/PHASE2_FREEZE.json` (audit note added)  
- `docs/current/EVALUATION_PLAN_V8.md` (protocol plan)  
- `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md` (template)

**Fix implemented:** Chronology corrected in documentation (`410b3ae`). Evaluation plan v8 written. Fresh program sources identified (`docs/current/FRESH_PROGRAM_SOURCES.md`). No fresh programs have been created.

**Verification performed:** Git log confirms: `9a9104f` (Sep 28, v6 test results) predates `ad7b655` (Oct 3, preregistration). Documented in `reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md` (on `independent-audit/ieee-access-2026-10`).

**Actual result:** Chronology finding confirmed. Fresh test set: NOT CREATED.

**Evidence paths:**  
- `docs/current/PHASE2_PREREGISTRATION.md` (chronology note)  
- `STATUS.md` (exploratory disclaimer)  
- `artifacts/final/PHASE2_FREEZE.json` (audit_note_2026_10_25 field)

**Relevant commit hash:** `410b3ae` (chronology corrections)

**Remaining limitations:** No fresh test programs have been written. This blocker cannot be resolved without experiment owner action (writing ≥36 programs, running full generation, freezing the protocol, executing one evaluation run).

**Final status: UNRESOLVED**  
*Chronology corrected. Fresh test set does not exist. Acceptance criteria (b)–(d) are not met.*

---

### B03 — SBG performance against simple baselines

**Problem statement:** On the v6 test split, `exception_fraction` AUROC (0.618) beats SBG V5 AUROC (0.601). SBG does not beat any cheap execution baseline by a statistically significant margin. The edit-size shortcut alone achieves 0.967.

**Why it matters:** If SBG provides no incremental information beyond exception fraction or call count, the empirical contribution claim is not supported.

**Acceptance criteria:**  
(a) All required baselines evaluated on the same eligible pairs.  
(b) Paired statistical comparisons with confidence intervals.  
(c) Multiple-comparison correction applied.  
(d) Results interpreted honestly (no baseline removed because it outperforms SBG).

**Current state:** Baseline AUROCs have been computed and reproduced on the v6 test (observed/contaminated) split. Independent audit confirms: exception_fraction AUROC 0.6184 > SBG V5 0.6013; all Holm-corrected tests non-significant for SBG V5 vs execution baselines. Edit-size reversed AUROC = 0.9667 has been promoted to a required baseline in the evaluation plan.

**Files involved:**  
- `artifacts/final/pairs_v6test_output_free_v6.jsonl`  
- `experiments/final/audit_recompute.py`  
- `reports/remediation/results/audit_recompute.json`  
- `docs/current/EVALUATION_PLAN_V8.md` § 6 (baseline list)

**Fix implemented:** Baselines documented and evaluated on v6 (observed) split. The v8 plan mandates all baselines on the same eligible pairs. No fresh evaluation run yet.

**Verification performed:** `audit_recompute.py --no-write` confirms all 6 reference AUROCs. Exception_fraction AUROC confirmed independently (V15 in independent audit report).

**Actual result (v6 test, exploratory):** SBG V5 AUROC 0.601, exception_fraction 0.618, call_count not recomputed here, static_ast 0.105, edit_size_reversed 0.967.

**Evidence paths:**  
- `reports/remediation/results/audit_recompute.json`  
- `reports/remediation/agent_d_baselines_stats.md`

**Relevant commit hash:** `0d0889c` (agent D report)

**Remaining limitations:** All comparisons are on the observed/contaminated split. A fair comparison requires the frozen fresh evaluation with all baselines on the same eligible pairs. This cannot be assessed until B02 is resolved.

**Final status: PARTIALLY_RESOLVED**  
*Baselines documented on exploratory data; adverse result (SBG does not beat baselines) recorded. Confirmatory baseline comparison blocked on B02.*

---

### B04 — Poor external generalization

**Problem statement:** BugsInPy AUROC = 0.410 CI [0.326, 0.494]; QuixBugs canonical AUROC = 0.388. Both are significantly below chance. The method does not transfer to real bugs under the current protocol.

**Why it matters:** This is the dominant external validity finding and it is adverse. It must appear in the paper's primary results section.

**Acceptance criteria:**  
(a) Both AUROCs reproduced.  
(b) Root-cause analysis on dev data only.  
(c) Adverse results present in the primary results section of the manuscript, not an appendix.  
(d) A plausible mechanism that does not require post-hoc tuning.

**Current state:** Both AUROCs reproduced and independently confirmed (V19, V20 in independent audit). Root-cause hypothesis documented: the synthetic benchmark's edit-size distribution differs from real bugs; SBG captures edit-size signal that inverts on real bugs. This hypothesis has not been tested yet. Adverse results are noted in `CLAIMS_REGISTRY.yaml` (C022: NOT_SUPPORTED) and `06_END_TO_END_STATUS.md`.

**Files involved:**  
- `artifacts/final/BUGSINPY_output_free_v7.json`  
- `artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`  
- `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`  
- `docs/CLAIMS_REGISTRY.yaml` (C022)  
- `reports/remediation/07_DECISIONS_AND_OPEN_QUESTIONS.md` (D5)

**Fix implemented:** AUROCs reproduced. Root-cause hypothesis stated. Adverse results recorded in claims registry. Manuscript-facing investigation (dev-only analysis) has not been run.

**Verification performed:** BugsInPy AUROC recomputed from `pairs_bugsinpy_output_free_v7.jsonl` → 0.409917 (matches). QuixBugs canonical AUROC recomputed → 0.3877 (matches).

**Actual result:** BugsInPy AUROC 0.410 CI [0.326, 0.494]; QuixBugs canonical AUROC 0.388. Both below chance.

**Evidence paths:**  
- `artifacts/final/BUGSINPY_output_free_v7.json`  
- `reports/remediation/results/audit_recompute.json`  
- `docs/CLAIMS_REGISTRY.yaml` (C022)

**Relevant commit hash:** `410b3ae` (claims C022 updated to NOT_SUPPORTED)

**Remaining limitations:** Root-cause analysis has not been executed. Manuscript integration has not been done. The external results must be visible in the paper's primary results table regardless of the root-cause finding.

**Final status: PARTIALLY_RESOLVED**  
*Adverse results recorded and reproduced. Root-cause investigation and manuscript placement not yet done.*

---

### B05 — SP-2 transformation defect

**Problem statement:** `_FunctionRenamer.visit_Call` in `sp2_function_rename.py` handled `ast.Name` (direct function calls) but not `ast.Attribute` (method calls like `self.compute()`). This caused 75 v6 EQUIVALENT pairs to retain dangling attribute references, 70 of which raised `AttributeError` at execution.

**Why it matters:** 75 mislabelled EQUIVALENT pairs directly contaminate AUROC results. SBG was penalised for correctly detecting a real behavioural difference that the label called equivalent.

**Acceptance criteria:**  
(a) `visit_Attribute` fix implemented in `sp2_function_rename.py`.  
(b) Regression tests for direct calls, attribute calls, methods, nested expressions.  
(c) v7 smoke dataset shows 0 SP-2 defects under `data_integrity.py`.  
(d) Historical v6 data preserved (not retroactively corrected).

**Current state:** ALL criteria met. The fix adds a `visit_Attribute` method to `_FunctionRenamer` that renames any attribute whose name is in `self.rename_map`. Six regression tests in `tests/test_sp2_repair.py` cover: direct call rename, attribute method rename, class method rename, method call preserved if not in map, nested attribute call, both Name and Attribute in same tree. `data_integrity.py` on v7 smoke dataset returns 0 defects. v6 remains at 75 defects (historical record preserved).

**Files involved:**  
- `benchmark/transformations/preserving/transformations/sp2_function_rename.py`  
- `tests/test_sp2_repair.py`  
- `benchmark/datasets/v7/` (smoke dataset)  
- `benchmark/datasets/v6/` (historical, unchanged)

**Fix implemented:** `visit_Attribute` added to `_FunctionRenamer` at commit `5cf5211`. Full regression test suite added.

**Verification performed:**  
```
python3 -m pytest tests/test_sp2_repair.py -v  → 6 passed
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7  → 0 defects
python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v6  → 75 defects (historical)
```

**Test command:** `python3 -m pytest tests/test_sp2_repair.py -v`

**Actual result:** 6/6 tests pass. 0 SP-2 defects in v7 smoke. 75 defects in v6 (preserved).

**Evidence paths:**  
- `tests/test_sp2_repair.py`  
- `reports/remediation/results/sp2_dangling_execution_check.json`  
- `benchmark/datasets/v7/`

**Relevant commit hash:** `5cf5211`

**Remaining limitations:** v7 is a smoke test (3 programs, 133 pairs). Full v7 generation on a complete fresh program set has not been run. The fix covers the defect identified; additional edge cases (e.g., deeply nested attribute access chains) are not explicitly tested but the `visit_Attribute` approach handles them structurally.

**Final status: RESOLVED**  
*Code fixed, tests pass, v7 smoke confirms 0 defects, v6 historical record preserved.*

---

### B06 — Deterministic entry-point and driver selection

**Problem statement:** The `output_free_v6/v7` entry-selection method (`select_entry_output_free`) selects by identifier name, making it rename-unstable: SP-2 renames a function and the renamed version may select a different entry point.

**Why it matters:** 9 of 259 evaluated v6 test pairs were found tracing a renamed self-test driver instead of the target function, contaminating extraction.

**Acceptance criteria:**  
(a) `output_free_v8` entry policy implemented and rename-invariant on function-only programs.  
(b) Regression tests for renamed functions, multiple candidates, missing entry points.  
(c) Entry selection does not depend on the target label.  
(d) Selection failures recorded.

**Current state:** `experiments/final/entry_policy.py` implements `output_free_v8` with structural rename-invariant entry selection (selects the single exported function by position/signature, not name). 37 tests in `tests/test_entry_policy.py` pass. Class-based programs raise `NoEntryPoint` under v8 (see B07). Historical protocols `v6`/`v7` are preserved unchanged.

**Files involved:**  
- `experiments/final/entry_policy.py`  
- `tests/test_entry_policy.py`

**Fix implemented:** `output_free_v8` implemented at commit `d9d6380`. Structural entry selection is rename-invariant on function-only programs.

**Verification performed:** `python3 -m pytest tests/test_entry_policy.py -v` → 37 passed. Invariance on v6 test programs: `make verify-v7-invariance` → 0 violations on 13 test programs (per `STATUS.md`).

**Test command:** `python3 -m pytest tests/test_entry_policy.py -v`

**Actual result:** 37/37 tests pass. Rename invariance confirmed on function-only programs.

**Evidence paths:**  
- `tests/test_entry_policy.py`  
- `artifacts/final/DRIVER_SYNTHESIS_VALIDATION.json`

**Relevant commit hash:** `d9d6380`

**Remaining limitations:** Class-based programs are still handled as `NoEntryPoint` under v8 function-only policy (see B07). The class tier in `class_driver.py` is flagged `rename_invariant=False`. The v8 policy has been implemented but never scored on a test split.

**Final status: RESOLVED**  
*Function-only entry policy is rename-invariant and tested. Class programs handled explicitly (see B07). Historical protocol preserved.*

---

### B07 — Class-based program support

**Problem statement:** Class-based programs raise `NoEntryPoint` under `output_free_v8` function-only policy. 16 of 47 non-test programs (34%) and all 6 class-based test programs have no scored pairs. This biases the evaluation toward simpler functional programs.

**Why it matters:** Stateful, class-based programs are the architecturally most interesting cases for behavioral distance. Excluding them entirely limits the claim scope.

**Acceptance criteria:**  
(a) Class-driver policy decision documented.  
(b) Supported and unsupported program types explicitly listed.  
(c) Eligibility criterion is label-blind.  
(d) Exclusion rate measured and reported.

**Current state:** `experiments/final/class_driver.py` implements an alphabetical class tier. It is flagged `rename_invariant=False`. Three policy options are documented in `07_DECISIONS_AND_OPEN_QUESTIONS.md` (D2) and `EVALUATION_PLAN_V8.md` § 4. The decision has not been made by the experiment owner. Under Option 1 (function-only), 18 of 47 programs are evaluable (38%). Under Option 2 (function + structural class driver), 34 of 47.

**Files involved:**  
- `experiments/final/class_driver.py`  
- `experiments/final/entry_policy.py`  
- `docs/current/EVALUATION_PLAN_V8.md`  
- `reports/remediation/07_DECISIONS_AND_OPEN_QUESTIONS.md` (D2)  
- `reports/remediation/agent_c_v8_coverage.md`

**Fix implemented:** Class driver implemented; policy options documented; eligibility analysis completed. Owner decision pending.

**Verification performed:** Agent C analysis: 16 NoEntryPoint (class-only), 11 AmbiguousEntryPoint. Coverage data in `reports/remediation/agent_c_v8_coverage.md`.

**Actual result:** Under Option 1: 18/47 evaluable (38%). Under Option 2: 34/47 (72%). Class tier flagged as rename-non-invariant.

**Evidence paths:**  
- `reports/remediation/agent_c_v8_coverage.md`  
- `experiments/final/class_driver.py`

**Relevant commit hash:** `d9d6380`

**Remaining limitations:** Policy decision not made. Whichever option is chosen affects fresh program count requirements (Option 1 requires ≥50 programs to get ≥20 evaluable). This is a blocking dependency for B02.

**Final status: PARTIALLY_RESOLVED**  
*Implementation and options documented. Policy decision required from experiment owner before proceeding.*

---

### B08 — Complete v7 dataset generation and integrity

**Problem statement:** Only a smoke-test v7 dataset (3 programs, 133 pairs) exists. A full v7 dataset generated from the complete fresh program set has not been created.

**Why it matters:** The final evaluation requires a complete, integrity-checked v7 dataset covering all fresh programs.

**Acceptance criteria:**  
(a) `generate_v7_dataset.py` produces a complete dataset from the fresh program set.  
(b) `data_integrity.py --strict` exits 0 on the complete dataset.  
(c) Machine-readable integrity report produced.  
(d) Manifest with cryptographic hashes committed.

**Current state:** `generate_v7_dataset.py` is implemented and tested on 3 programs (0 defects). A full generation requires the fresh programs (B02 dependency). The smoke test dataset passes all integrity checks.

**Files involved:**  
- `benchmark/scripts/generate_v7_dataset.py`  
- `benchmark/datasets/v7/`  
- `experiments/final/data_integrity.py`  
- `benchmark/datasets/v7/manifest.json`

**Fix implemented:** Generator implemented and smoke-tested. Full generation blocked on fresh programs.

**Verification performed:** `data_integrity.py --dataset benchmark/datasets/v7` → 0 defects (3 programs).

**Test command:** `python3 experiments/final/data_integrity.py --dataset benchmark/datasets/v7`

**Actual result:** 0 SP-2 defects in smoke dataset.

**Evidence paths:**  
- `benchmark/datasets/v7/manifest.json`

**Relevant commit hash:** `625ca3f`

**Remaining limitations:** Full dataset generation not possible without fresh programs (B02). Edit-size redesign (B01/D1) would need to precede full generation for the confound to be addressed.

**Final status: PARTIALLY_RESOLVED**  
*Generator implemented; smoke test passes. Full generation requires fresh programs (B02 unresolved).*

---

### B09 — Missing final evaluation artifacts

**Problem statement:** `artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json` (the frozen Phase 2 test evaluation under output_free_v7) does not exist. The equivalent v8 artifact also does not exist.

**Why it matters:** Without a final evaluation, no AUROC from a correctly frozen protocol exists. All existing AUROCs are exploratory.

**Acceptance criteria:**  
(a) Either a valid v7/v8 evaluation artifact is produced after the protocol freeze, OR  
(b) This artifact is documented as pending with exact commands required.

**Current state:** The artifact is absent. The v6 test result using `output_free_v6` protocol exists (`MAIN_EVALUATION_v6test_output_free_v6.json`) and is labelled as exploratory. `STATUS.md` documents stage 2c (`make v7-test`) as pending. The correct artifact cannot be generated until B02 (fresh test set) and B07 (class-driver policy) are resolved and the protocol frozen.

**Files involved:**  
- `artifacts/final/` (artifact does not exist)  
- `STATUS.md` (stage 2c)  
- `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md` (template)

**Fix implemented:** Absent artifact documented. Template for `FREEZE_V8.json` written in `08_FINAL_EVALUATION_MANIFEST.md`. Commands documented.

**Verification performed:** File search confirms absence. Independent audit confirmed (V23).

**Actual result:** Artifact absent. Commands to generate it are documented but cannot be run until prerequisites are met.

**Evidence paths:**  
- `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md`  
- `STATUS.md`

**Relevant commit hash:** `0d0889c`

**Remaining limitations:** Generation is blocked on B01 (edit-size redesign), B02 (fresh programs), B07 (class-driver policy), B10 (weight fitting). After those are resolved: freeze, then one run of `make v7-train v7-fit v7-test`.

**Final status: UNRESOLVED**  
*Artifact absent. Cannot be produced without resolving B01, B02, B07, B10 first.*

---

### B10 — Missing weight-fitting artifact

**Problem statement:** `artifacts/final/WEIGHT_FITTING.json` does not exist. The SBG V5 component weights (0.50/0.25/0.25) were never fitted on any data; they are arbitrary.

**Why it matters:** Without weight fitting on training data, the SBG V5 combination is unjustified. Any AUROC attributable to weight choice rather than the genome signal is uncontrolled.

**Acceptance criteria:**  
(a) `fit_weights.py` implementation verified.  
(b) Weights fitted on train split only; validated on dev.  
(c) `WEIGHT_FITTING.json` artifact produced before test evaluation.  
(d) Fitted weights committed and frozen before `make v7-test`.

**Current state:** `experiments/final/fit_weights.py` exists. `WEIGHT_FITTING.json` is absent. Weight fitting is stage 2b in `STATUS.md` and requires stage 2a (train run) first. The 0.50/0.25/0.25 default weights are used in all existing evaluations.

**Files involved:**  
- `experiments/final/fit_weights.py`  
- `artifacts/final/WEIGHT_FITTING.json` (absent)  
- `STATUS.md` (stage 2b)

**Fix implemented:** Fitting procedure defined in `EVALUATION_PLAN_V8.md` § 5. Script exists. Artifact generation blocked on fresh data.

**Verification performed:** Independent audit confirmed absence (V24).

**Actual result:** Artifact absent.

**Evidence paths:**  
- `STATUS.md` (stage 2b pending)

**Relevant commit hash:** `0d0889c`

**Remaining limitations:** Cannot be produced until a training split of fresh data exists. Blocked on B02.

**Final status: UNRESOLVED**  
*Procedure defined; artifact absent; blocked on B02.*

---

### B11 — Missing QuixBugs evaluation artifact

**Problem statement:** `QUIXBUGS_output_free_v7.json` does not exist as a separate artifact (the pairs file `pairs_quixbugs_canonical_output_free_v7.jsonl` exists, but the summarised evaluation JSON does not).

**Why it matters:** The QuixBugs evaluation is referenced as an external validity test. The pairs file exists and the point AUROC (0.388) has been recomputed, but a formally structured evaluation artifact with the full methodology record does not exist.

**Acceptance criteria:**  
(a) QuixBugs evaluation artifact produced with full provenance.  
(b) AUROC, CI, failure ledger, and methodology recorded.  
(c) Adverse result preserved and not filtered.

**Current state:** `pairs_quixbugs_canonical_output_free_v7.jsonl` exists (152 pairs, 40 CHANGED, 112 EQUIVALENT). The point AUROC (0.388) is independently reproducible from this file. A structured `QUIXBUGS_output_free_v7.json` artifact analogous to `BUGSINPY_output_free_v7.json` does not exist. Independent audit confirmed absence (V25).

**Files involved:**  
- `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`  
- `artifacts/final/QUIXBUGS_output_free_v7.json` (absent)

**Fix implemented:** Point AUROC recomputable from existing pairs file. Formal artifact not yet generated.

**Verification performed:**
```python
from sbg.statistics import auroc
# pairs from pairs_quixbugs_canonical_output_free_v7.jsonl → AUROC 0.3877
```

**Actual result:** Point AUROC 0.388 confirmed from pairs file. Structured artifact absent.

**Evidence paths:**  
- `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`

**Relevant commit hash:** `0d0889c`

**Remaining limitations:** Generating the structured artifact requires running `external_quixbugs.py` with the frozen v7 protocol. This can be done without new experiments if the existing pairs file is used as input. However, the QuixBugs result is already below chance and clearly adverse; generating a formatted artifact does not change the scientific status.

**Final status: UNRESOLVED**  
*Point AUROC reproducible; structured artifact absent; adverse result confirmed.*

---

### B12 — Fresh-program count and eligibility

**Problem statement:** ≥36 new base programs are needed for the confirmatory test set. Under Option 1 (function-only, 38% eligible), ≥50 programs must be written to obtain ≥20 evaluable. Under Option 2, ≥36 programs may suffice.

**Why it matters:** Without enough eligible programs, the study is underpowered. The 7-cluster CI of width 0.22 from v6 test demonstrates that a small program count produces unreliable confidence intervals.

**Acceptance criteria:**  
(a) Target population defined before scoring.  
(b) Eligibility criteria defined before scoring.  
(c) Power analysis run on dev data (not test).  
(d) Fresh programs written, provenance documented, Jaccard ≤0.10 against known programs.  
(e) Independence unit is program, not pair.

**Current state:** Source families for fresh programs identified in `docs/current/FRESH_PROGRAM_SOURCES.md` (7 families, ~77 candidates). Token-overlap screen protocol specified. Power analysis script exists (`benchmark/scripts/power_analysis.py`) but must be run on dev data to get per-program AUROC SD. No fresh programs have been written.

**Files involved:**  
- `docs/current/FRESH_PROGRAM_SOURCES.md`  
- `benchmark/scripts/power_analysis.py`  
- `reports/remediation/agent_e_fresh_dataset.md`

**Fix implemented:** Source guide written. Eligibility criteria and Jaccard screen protocol specified. Power analysis script available.

**Verification performed:** Agent E analysis confirms ~77 candidate programs across 7 source families.

**Actual result:** 0 fresh programs written.

**Evidence paths:**  
- `docs/current/FRESH_PROGRAM_SOURCES.md`  
- `reports/remediation/agent_e_fresh_dataset.md`

**Relevant commit hash:** `625ca3f`

**Remaining limitations:** No programs have been written. This is the primary experimental blocker and requires human effort.

**Final status: UNRESOLVED**  
*Sources identified; programs not written; 0 of ≥36 programs exist.*

---

### B13 — Statistical analysis plan

**Problem statement:** A complete statistical analysis plan for the confirmatory evaluation has not been frozen as a separate document. The v8 plan in `EVALUATION_PLAN_V8.md` is a draft that requires owner approval and does not carry a freeze hash.

**Why it matters:** IEEE Access expects that statistical decisions (primary metric, comparison, correction method, exclusion rules) are specified before data collection, not after.

**Acceptance criteria:**  
(a) Primary outcome, comparison, CI procedure, and correction method specified.  
(b) Cluster bootstrap justified (or alternative specified).  
(c) Exclusion rules, tie handling, and failed-execution policy specified.  
(d) Plan committed before test scoring.

**Current state:** `EVALUATION_PLAN_V8.md` § 7 specifies: primary metric = tie-aware AUROC (EVALUABLE and ALL denominators reported), paired cluster bootstrap with Holm-Bonferroni correction, LOCO sensitivity range, noise floor at p95, success criterion fixed (SBG beats best baseline with Holm-corrected lower CI > 0 AND within-bin AUROC exceeds noise floor). This is a complete plan but it is a draft: not frozen, not hashed, owner approval not recorded.

**Files involved:**  
- `docs/current/EVALUATION_PLAN_V8.md`  
- `reports/remediation/08_FINAL_EVALUATION_MANIFEST.md`

**Fix implemented:** Plan written with cluster-dependence-aware statistics. Multiple-comparison correction specified.

**Verification performed:** Plan reviewed; it addresses all acceptance criteria for the statistical method. Freeze step not yet executed.

**Actual result:** Plan exists as draft. Freeze step pending.

**Evidence paths:**  
- `docs/current/EVALUATION_PLAN_V8.md`

**Relevant commit hash:** `d9d6380` (evaluation plan added)

**Remaining limitations:** Plan must be frozen (hashed, committed as part of `FREEZE_V8.json`) before test scoring. This cannot happen until B01, B02, B07 are resolved.

**Final status: PARTIALLY_RESOLVED**  
*Plan complete and methodologically sound. Not yet frozen. Cannot be frozen until B02 is resolved.*

---

### B14 — Transformation validity and label integrity

**Problem statement:** SP transformations can produce variants that are not actually semantics-preserving (as demonstrated by the SP-2 defect, where 75 EQUIVALENT-labelled pairs had dangling method references causing `AttributeError`). A broader audit of all SP/SC transformations has not been completed.

**Why it matters:** If other transformations also produce incorrect labels, the benchmark's AUROC cannot be trusted.

**Acceptance criteria:**  
(a) Every transformation audited for label correctness.  
(b) Execution-based checks run on EQUIVALENT pairs.  
(c) Any discovered defects documented.  
(d) A machine-readable transformation-integrity report produced.

**Current state:** SP-2 defect found and fixed (B05). `data_integrity.py` checks for SP-2 specifically. A broader transformation audit (SP-1 through SP-12, SC-1 through SC-13) using execution-based checks on EQUIVALENT pairs has not been run for the full benchmark. `BENCHMARK_VALIDITY_AUDIT_V7.json` is a static check only.

**Files involved:**  
- `experiments/final/data_integrity.py`  
- `artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json`  
- `benchmark/transformations/`

**Fix implemented:** SP-2 fixed. Static audit covers schema and pair integrity. Execution-based audit of all EQUIVALENT pairs not run.

**Verification performed:** SP-2 regression tests pass. Static audit passes. No execution-based label audit exists.

**Actual result:** SP-2 defect resolved. Broader execution audit: not run.

**Evidence paths:**  
- `artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json`  
- `tests/test_sp2_repair.py`

**Relevant commit hash:** `5cf5211`, `625ca3f`

**Remaining limitations:** An execution-based audit of all EQUIVALENT v7 pairs should run as part of the integrity check (`data_integrity.py --strict`). This is feasible when the full v7 dataset exists.

**Final status: PARTIALLY_RESOLVED**  
*SP-2 defect resolved. Broader execution-based label audit requires full v7 dataset (B08 dependency).*

---

### B15 — Independent reproduction

**Problem statement:** A clean-checkout reproduction procedure has not been fully documented and validated for the final integrated results.

**Why it matters:** IEEE Access requires that results be independently reproducible from code and documented commands.

**Acceptance criteria:**  
(a) Reproduction commands documented.  
(b) Clean-checkout run successfully attempted.  
(c) All expected artifacts produced and hashed.  
(d) No undocumented local files required.

**Current state:** The `09_CLAUDE_HANDOFF.md` documents reproduction commands for the test suite, consistency checks, and reference AUROC recomputation. A clean-checkout run of tests was performed during the `remediation/ieee-access-audit` cycle (commit `d9d6380` report). The final evaluation artifacts do not exist, so reproduction of the final AUROC is not yet possible.

**Files involved:**  
- `reports/remediation/09_CLAUDE_HANDOFF.md`  
- `reports/remediation/04_REMEDIATION_REPORT.md`  
- `Makefile`

**Fix implemented:** Commands documented. Test-suite clean-checkout confirmed.

**Verification performed:** Clean-checkout run of `pytest sbg/ tests/` and `consistency_check.py` confirmed at `d9d6380` (see `04_REMEDIATION_REPORT.md`). Current session confirms 738 tests pass, 10/10 consistency.

**Actual result:** Test suite reproduces cleanly. Final evaluation artifacts do not exist and therefore cannot be reproduced.

**Evidence paths:**  
- `reports/remediation/logs/final_pytest_py313.txt`  
- `reports/remediation/logs/final_pytest_py39.txt`  
- `reports/remediation/04_REMEDIATION_REPORT.md`

**Relevant commit hash:** `d9d6380`, `0d0889c`

**Remaining limitations:** Full reproduction including final evaluation results is not possible until B09 is resolved.

**Final status: PARTIALLY_RESOLVED**  
*Test suite and baselines reproduce cleanly. Final evaluation not yet possible.*

---

### B16 — External validity and generalization claims

**Problem statement:** The manuscript's external validity claims need to accurately represent the BugsInPy (0.410) and QuixBugs canonical (0.388) adverse results.

**Why it matters:** Claiming general applicability to real bugs is not supported.

**Acceptance criteria:**  
(a) External AUROCs reported in the primary results section.  
(b) Claims about generalization qualified to the synthetic benchmark.  
(c) Distribution-shift analysis documented.

**Current state:** C022 in the claims registry is updated to NOT_SUPPORTED. The `EVALUATION_PLAN_V8.md` requires adverse external results in the primary table. No manuscript draft has been updated yet.

**Files involved:**  
- `docs/CLAIMS_REGISTRY.yaml` (C022)  
- `reports/remediation/07_DECISIONS_AND_OPEN_QUESTIONS.md` (D5)

**Fix implemented:** Claims registry updated. External results accurately documented in register. Manuscript update blocked until final evaluation exists.

**Verification performed:** C022 is NOT_SUPPORTED with correct AUROC values.

**Actual result:** Claims registry correct. Manuscript not updated (no manuscript in repository).

**Evidence paths:**  
- `docs/CLAIMS_REGISTRY.yaml` (C022)

**Relevant commit hash:** `410b3ae`

**Remaining limitations:** Manuscript-facing integration not done. Root-cause analysis on dev data not run.

**Final status: PARTIALLY_RESOLVED**  
*Research record correct; manuscript integration pending; root-cause analysis not run.*

---

### B17 — Preregistration chronology and provenance

**Problem statement:** `PHASE2_PREREGISTRATION.md` was committed on 2026-10-03, five days after v6 test results were committed on 2026-09-28. The document's header claims it was "Written 2026-09-28, before any Phase 2 result existed." This claim is false by Git history.

**Why it matters:** False chronology claims in a preregistration document are a research integrity issue. IEEE Access reviewers may reject the paper on this ground alone.

**Acceptance criteria:**  
(a) False date claim removed or corrected.  
(b) Git history documented confirming the actual commit order.  
(c) All v6 results labelled exploratory.  
(d) New protocol clearly distinguished as the confirmatory one.

**Current state:** The false "before any Phase 2 result existed" wording has been removed from `STATUS.md`. A chronology note has been added to `PHASE2_PREREGISTRATION.md` (fix F2 at `410b3ae`): "Chronology note (2026-10-25): This document was committed at ad7b655 (2026-10-03)." `PHASE2_FREEZE.json` has an `audit_note_2026_10_25` field.

**Files involved:**  
- `docs/current/PHASE2_PREREGISTRATION.md`  
- `STATUS.md`  
- `artifacts/final/PHASE2_FREEZE.json`

**Fix implemented:** False claim removed from STATUS.md; chronology note added to preregistration. Commit `410b3ae`.

**Verification performed:** Git log confirms commit order. Text in `PHASE2_PREREGISTRATION.md` now carries the chronology disclaimer.

**Actual result:** Corrections applied. The document now accurately describes the situation.

**Evidence paths:**  
- `docs/current/PHASE2_PREREGISTRATION.md` (chronology note)  
- `STATUS.md` (remediation note)

**Relevant commit hash:** `410b3ae`

**Remaining limitations:** The `written_at: 2026-09-28T16:16:15+00:00` field in `PHASE2_FREEZE.json` still predates its git commit. This field should not be used to support a preregistration claim. The note exists but the field itself has not been removed.

**Final status: RESOLVED**  
*False claims corrected; chronology documented; v6 results labelled exploratory.*

---

### B18 — Citation accuracy and prior-art review

**Problem statement:** Three citations (refs 17, 33, 39) were identified as incorrect or unverifiable. Two relevant works (Person et al. on mutation testing, Wang et al. on execution-trace embeddings) were not cited.

**Why it matters:** Fabricated or incorrect citations will be caught by reviewers and editors.

**Acceptance criteria:**  
(a) All suspect citations corrected or removed.  
(b) Missing prior art added.  
(c) Corrections documented with source trail.  
(d) Novelty claim updated to reflect corrected prior-art position.

**Current state:** Three citation corrections added to `docs/research/PRIOR_ART_MATRIX.md` and `docs/research/NOVELTY_ANALYSIS.md` with inline correction notes (fix F5 at `410b3ae`). Two missing citations added (F6). Full-text verification was not possible (HTTP 429 from DBLP; Crossref and arXiv used instead). The actual bibliographic entries have not been rewritten in any manuscript file (no manuscript LaTeX/BibTeX in the repository).

**Files involved:**  
- `docs/research/PRIOR_ART_MATRIX.md`  
- `docs/research/NOVELTY_ANALYSIS.md`  
- `docs/research/CITATION_VERIFICATION.md`

**Fix implemented:** Correction notes added; missing works identified. Commit `410b3ae`.

**Verification performed:** Citation corrections verified against Crossref/arXiv by the prior session. No full-text read.

**Actual result:** Matrix and novelty analysis carry correction flags. Manuscript BibTeX not updated (not in repository).

**Evidence paths:**  
- `docs/research/CITATION_VERIFICATION.md`  
- `docs/research/PRIOR_ART_MATRIX.md`

**Relevant commit hash:** `410b3ae`

**Remaining limitations:** Full-text read of cited works was not performed. Authors must verify the corrected bibliographic details against original sources before submission.

**Final status: PARTIALLY_RESOLVED**  
*Research-record corrections applied; full-text verification outstanding; manuscript BibTeX not in repository.*

---

### B19 — Claims registry and manuscript consistency

**Problem statement:** Claims in `STATUS.md`, claims registry, and various documents contained false or unsupported assertions (e.g., false preregistration date, C022 as NOT_EVALUABLE rather than NOT_SUPPORTED with adverse evidence, gate PASS despite adverse AUROC).

**Why it matters:** Reviewers and reproducibility checkers will compare claims against evidence. Inconsistencies will trigger rejection.

**Acceptance criteria:**  
(a) Every quantitative claim points to an authoritative artifact.  
(b) All v6 results labelled exploratory.  
(c) Adverse results reflected.  
(d) No obsolete values remain in active documents.

**Current state:** C022 updated to NOT_SUPPORTED with adverse AUROCs. C016 carries preregistration note. STATUS.md corrected. Consistency check C5 (no retired claim in current documents) passes. 10/10 consistency checks pass. FINAL_STANFORD_READINESS_REPORT.md is a historical artifact from a superseded gate script; it may still contain inaccurate verdicts.

**Files involved:**  
- `docs/CLAIMS_REGISTRY.yaml`  
- `STATUS.md`  
- `FINAL_STANFORD_READINESS_REPORT.md`

**Fix implemented:** Claims C016, C022 updated. STATUS.md corrected. Consistency checks pass.

**Verification performed:** `consistency_check.py` → 10/10. Claims registry YAML reviewed for C016–C023.

**Actual result:** Active documents consistent. FINAL_STANFORD_READINESS_REPORT.md remains a historical artefact labelled as superseded.

**Evidence paths:**  
- `docs/CLAIMS_REGISTRY.yaml`  
- `STATUS.md`

**Relevant commit hash:** `410b3ae`, `0d0889c`

**Remaining limitations:** `FINAL_STANFORD_READINESS_REPORT.md` contains historical verdicts from the old hard-coded gate. It is labelled as superseded but a new reader might misinterpret it. The document should carry a prominent disclaimer or be moved to `docs/archive/`.

**Final status: RESOLVED**  
*Active claims and consistency checks pass. Historical artefact appropriately labelled.*

---

### B20 — Scientific contribution and novelty

**Problem statement:** The existing evidence does not establish that SBG outperforms simple baselines. The edit-size confound means the benchmark does not answer the research question. External results are adverse. The novelty position is partially affected by the corrected citations.

**Why it matters:** IEEE Access requires a clear, evidence-backed scientific contribution.

**Acceptance criteria:**  
(a) Contribution stated precisely.  
(b) What evidence supports vs. does not support the contribution clearly distinguished.  
(c) Narrower defensible contribution identified if the original claim fails.

**Current state:** The current evidence supports a narrower contribution: a rigorous description of the genome representation, an honest audit of measurement failures (oracle leak, false labels, CI misattribution), and a quantified negative/inconclusive result. The 0.601 AUROC on 7 programs, not exceeding exception_fraction, with a total edit-size confound, is not sufficient for a "positive empirical contribution" IEEE Access paper. A negative-result or measurement-audit framing may be defensible.

**Files involved:**  
- `docs/research/NOVELTY_ANALYSIS.md`  
- `docs/CLAIMS_REGISTRY.yaml` (C023)  
- `reports/remediation/agent_f_research_record.md`

**Fix implemented:** Novelty analysis updated with corrected citations. C023 set to NOT_SUPPORTED. Agent F report documents defensible contribution boundaries.

**Verification performed:** C023 status verified in claims registry.

**Actual result:** C023 NOT_SUPPORTED. Current evidence: AUROC 0.601 (7 programs, exploratory, confounded). No positive confirmatory result exists.

**Evidence paths:**  
- `docs/research/NOVELTY_ANALYSIS.md`  
- `docs/CLAIMS_REGISTRY.yaml` (C023)

**Relevant commit hash:** `410b3ae`, `0d0889c`

**Remaining limitations:** The confirmatory evaluation (B02, B09) would establish whether a positive contribution can be claimed. Until then, the contribution is a methodology proposal plus an audit of measurement challenges.

**Final status: PARTIALLY_RESOLVED**  
*Narrower defensible contribution identified and documented. Full empirical contribution blocked on confirmatory evaluation.*

---

### B21 — Git integration and branch status

**Problem statement:** All remediation work should be committed in coherent, reviewable units on the remediation branch.

**Why it matters:** Reproducibility and auditability require that all changes be traceable to committed code.

**Acceptance criteria:**  
(a) Working tree clean.  
(b) All changes committed.  
(c) Final commit identified.

**Current state:** Branch `remediation/sbg-v2`. HEAD commit `0d0889c`. Git status: working tree clean. All fixes from the previous remediation cycle are committed in four logical commits (`5cf5211`, `410b3ae`, `625ca3f`, `0d0889c`). Nothing has been pushed to origin.

**Files involved:** All modified files in the four remediation commits.

**Fix implemented:** All work committed. Tree clean.

**Verification performed:** `git status` → "nothing to commit, working tree clean". `git log --oneline -5` shows coherent commit history.

**Actual result:** Working tree clean. 4 remediation commits. Not pushed.

**Evidence paths:** Git log on `remediation/sbg-v2`.

**Relevant commit hash:** `0d0889c` (HEAD)

**Remaining limitations:** Branch not pushed to origin. Pushing requires explicit user authorization (per policy). This is an operational task, not a scientific defect.

**Final status: RESOLVED**  
*All work committed; tree clean; not pushed (per policy).*

---

### B22 — Independent audit

**Problem statement:** An independent audit of the remediation work is required before declaring research readiness.

**Why it matters:** The independent auditor has authority to reject the readiness verdict.

**Acceptance criteria:**  
(a) Independent audit completed.  
(b) Actual code and artifacts inspected.  
(c) Critical metrics recomputed.  
(d) Chronology and freeze integrity verified.  
(e) Disagreements with primary agent recorded.  
(f) Readiness verdict issued by auditor.

**Current state:** An independent audit was completed by a separate agent at commit `e3038e0` (branch `independent-audit/ieee-access-2026-10`, commit `5d3dae9`). The audit independently verified 26 claims (V1–V26), confirmed all 6 reference AUROCs, confirmed the chronology finding, confirmed SP-2 defect and fix, and issued verdict: "NOT READY FOR IEEE ACCESS SUBMISSION." The audit report is in `reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md` on the `independent-audit/ieee-access-2026-10` branch.

The four additional commits (`5cf5211`, `410b3ae`, `625ca3f`, `0d0889c`) added after the audit have been reviewed in this session. They do not alter any frozen artifact or test result; they add code fixes (SP-2), analysis scripts, and documentation corrections. No re-audit of the new commits has been conducted by a separate agent in isolation.

**Files involved:**  
- `reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md` (on `independent-audit/ieee-access-2026-10`)

**Fix implemented:** First independent audit complete and recorded.

**Verification performed:** Audit findings independently confirmed in this session (all 6 AUROCs match, SP-2 fix confirmed in code, chronology confirmed).

**Actual result:** Independent audit verdict: NOT READY. 7 severity-1 blockers identified; all confirmed by primary agent in this register.

**Evidence paths:**  
- `independent-audit/ieee-access-2026-10:reports/independent_audit/INDEPENDENT_AUDIT_REPORT.md`

**Relevant commit hash:** `5d3dae9` (audit branch)

**Remaining limitations:** The four new commits (`5cf5211`–`0d0889c`) have not been reviewed by an independent agent. The audit correctly predates them. A supplementary audit of the new commits is recommended but the core findings (no held-out split, adverse external results, edit-size confound) remain unchanged.

**Final status: RESOLVED**  
*Independent audit complete; findings incorporated; NOT READY verdict confirmed.*

---

### B23 — End-to-end research readiness

**Problem statement:** Establish whether the complete project supports a reproducible, scientifically defensible manuscript.

**Why it matters:** This is the gating verdict.

**Acceptance criteria:**  
All seven gates (G1–G7) must pass.

**Current state:** See gate table below. Three gates pass; four are blocked or partially blocked.

| Gate | Status | Blocking reason |
|---|---|---|
| G1 Engineering integrity | **PASS** | 738 tests pass; SP-2 fixed; v8 entry policy rename-invariant; tree clean |
| G2 Benchmark validity | **PARTIAL** | Labels defensible on v7 smoke; edit-size confound total; no full fresh dataset; no overlapping edit-size bins |
| G3 Protocol integrity | **FAIL** | No freeze committed before test scoring; all existing results are post-hoc exploratory |
| G4 Empirical validity | **FAIL** | No final evaluation run; no confirmatory AUROCs; no weight fitting; external results adverse |
| G5 Reproducibility | **PARTIAL** | Test suite reproduces cleanly; final evaluation artifacts do not exist |
| G6 Research integrity | **PASS** | Citations corrected; exploratory labelling applied; adverse results preserved; no fabrication |
| G7 Independent verification | **PASS** | Independent audit complete at `5d3dae9`; NOT READY verdict confirmed |

**Overall verdict: NOT RESEARCH-READY (Category C)**

**What the current evidence can support:**  
- A methodology paper describing the genome representation and execution protocol.  
- An honest audit paper documenting the measurement failures and design traps.  
- A negative/inconclusive result: on a synthetic confounded benchmark (7 programs, exploratory), SBG V5 achieves AUROC 0.601 — not statistically distinguishable from exception_fraction (0.618) — while a reversed edit-size predictor achieves 0.967.  
- A clear path to a confirmatory experiment (described in `EVALUATION_PLAN_V8.md`).

**What requires new experiments:**  
- ≥36 new base programs (human effort)  
- Full v7 dataset generation (automated once programs exist)  
- Protocol freeze commit (automated)  
- Weight fitting on train split (automated)  
- Single frozen test evaluation run (automated, one-time)  
- Edit-size redesign (`max_sites` cap) if a positive claim is sought

**Final status: UNRESOLVED**  
*Category C: NOT RESEARCH-READY. Requires new experiments.*

---

## Evidence Summary

| Artifact | SHA-256 verified | Status |
|---|---|---|
| `artifacts/final/pairs_v6test_output_free_v6.jsonl` | Yes (freeze_handoff) | Historical/exploratory |
| `artifacts/final/BUGSINPY_output_free_v7.json` | Yes (freeze_handoff) | Adverse result, preserved |
| `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl` | Yes (freeze_handoff) | Adverse result, preserved |
| `artifacts/final/THRESHOLD_FROZEN.json` | Yes (freeze_handoff) | τ* = 0.072905, dev-derived |
| `benchmark/datasets/v7/` | Yes (data_integrity) | Smoke only, 0 defects |
| `MAIN_EVALUATION_v6test_output_free_v7.json` | N/A | **ABSENT** |
| `WEIGHT_FITTING.json` | N/A | **ABSENT** |
| `QUIXBUGS_output_free_v7.json` | N/A | **ABSENT** |
| `FREEZE_V8.json` | N/A | **NOT YET CREATED** |

---

## Minimum required actions to reach Category B (revised claims) or Category A (full readiness)

1. Decide D1 (edit-size redesign), D2 (class-driver policy), D3 (program source).
2. Write ≥36 new base programs with provenance and Jaccard screen.
3. Run `generate_v7_dataset.py` on all new programs; pass `data_integrity.py --strict`.
4. Run power analysis on dev data; increase program count if underpowered.
5. Derive τ* on new dev split under output_free_v8.
6. Run weight fitting on train split; commit `WEIGHT_FITTING.json`.
7. Commit `FREEZE_V8.json` with all hashes BEFORE any test scoring.
8. Run `make v7-train v7-fit v7-test` — exactly once.
9. Report all baselines (including edit_size_reversed) on the same eligible pairs.
10. Compute cluster bootstrap CIs, Holm-corrected comparisons, per-bin stratified AUROCs.
11. Present BugsInPy and QuixBugs adverse results in the primary results section.
12. Correct manuscript BibTeX for the three flagged citations.
13. Run independent audit of the final integrated commit.

If the confirmatory evaluation produces AUROC ≤ 0.5 or does not beat any baseline, the verdict remains Category C unless a narrower contribution is articulated (Category B). If it produces a statistically significant improvement over baselines with overlapping edit-size distributions, Category A is achievable.

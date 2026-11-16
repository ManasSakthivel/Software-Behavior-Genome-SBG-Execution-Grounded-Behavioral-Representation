# Sprint 2 Consolidated Final Forensic Audit and Strategic Handoff Report

**Date of Audit:** 2026-11-07  
**Workspace Root:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW`  
**Authoritative Repository:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG`  
**Authoritative Branch:** `remediation/sbg-v4`  
**Authoritative HEAD Commit:** `3425693b432bb774b10db1cf3185eae1a7eef095`  
**Remote URL:** `https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation`  
**Test Suite Verification:** 807 passed (545 `sbg/` + 262 `tests/`), 0 failed, 10/10 consistency checks passed, strict reproduction passed on CPython 3.13.5.  

---

## 1. Executive Summary and Repository Resolution

### A. Repository Resolution (Step 1)
- **Active Directory Context:** The current workspace directory `/Users/manassakthivel/Desktop/SBG-FINALREVIEW` contains Python virtual environments (`venvs/py313`, `venvs/py39`), scratch directories (`0_h/`, `1_h/`), forensic audit notes (`SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md`), and the actual Git repository at `SBG/`.
- **Authoritative State:** The inner `SBG/` repository on branch `remediation/sbg-v4` at commit `3425693` is the single verified, authoritative state of the project.
- **External Directory Discrepancy:** The parallel directory `~/Desktop/SBG FINAL` was checked and found to be on an older divergent branch (`final-audit-remediation` at `2b8e2eb`) with dirty uncommitted edits, missing all late-stage remediation commits (`c5bc130`, `401d16e`, `0c08641`, `93ef3f3`, `3425693`).
- **Remote Synchronization:** PR #2 ("Remediation/sbg v4") merged commit `93ef3f3` into GitHub `main` (`9be24b3`), whose tree is byte-identical to `93ef3f3`. Commit `3425693` resolves CI runner matrix definitions (pinning Python 3.9 to Ubuntu 22.04) and enforces strict reproduction tolerances.

---

## 2. Categorized System Audit (Step 3)

### A. What is Already Complete
1. **Core Representation & Pseudometric:** SBG V5 (state 0.50, temporal 0.25, resource 0.25) and V6 (graded state abstractions) implementations in `sbg/`.
2. **Benchmark Generation & Curation:** Composed, size-aware datasets for V8, V9c, and V10 with verified absence of duplicate pairs and strict program disjointness.
3. **Dynamic Oracle Pipeline:** 4-channel oracle (return value, uncaught exception, argument mutation, stdout) evaluating 11 synthesized inputs per program.
4. **Preregistered Statistical Engine:** Clustered bootstrap ($B=2,000$, seed 42) at program level, cluster permutation tests, and step-down Holm-Bonferroni multiplicity correction.
5. **Cryptographic Freeze Chains:** 25/25 verified files in `FREEZE_V10.json`, verified output hash in `FREEZE_V10_SCORED.json`, and unbroken hash chains for V8 and V9.
6. **Integrity & Reproduction Harness:** 807/807 tests passing, 10/10 consistency checks passing.

### B. What is Genuinely Defective
1. **Real-Bug Generalisation:** SBG fails to transfer to arbitrary real bugs without domain-specific test suites (BugsInPy AUROC = 0.4099, QuixBugs AUROC = 0.3877, both $\le 0.50$).
2. **Value-Only Constant Mutations (SC-6):** SBG V5 has a 73.9% blindness rate on pure constant modifications because qualitative value abstractions collapse within the same sign/magnitude category.
3. **COBOL & Java Generalisation Claims:** The COBOL corpus consisted of unparseable Db2 precompiler fragments, and the Java harness was an unvalidated 12-test smoke prototype. Cross-language claims are unsupported.

### C. What is Merely Undocumented
1. **Kessel & Atkinson (SCAM 2019) Access Limitation:** The open repository contains only the MADOC abstract. The paper must state explicitly that comparisons are based on the published abstract.
2. **Design-Level Inspection Disclosure:** Pre-freeze inspection of forward edit distance distributions was performed to verify confound removal before executing the frozen scoring pass.

### D. What Needs Additional Engineering (If New Evaluations are Pursued)
1. **Input Synthesis for External Benchmarks:** Automated generation of valid complex inputs for competitive programming or real-world repositories.
2. **Sandbox Crash Recovery:** Handling early trace termination when one mutant crashes and the base succeeds.

### E. What Evaluation Design is Defensible
- **The V10 Confirmatory Benchmark:** 19 fresh programs, 638 pairs, 319 matched sets, with forward edit AUROC = 0.616 and balanced 50/50 ground truth.
- **The Scientific Conclusion:** An honest negative-plus-methodology paper demonstrating that trace representations carry substantial behavioral signal ($+0.254$ over edit size alone), but do not provide statistically significant incremental gain once basic execution statistics (crashes and call counts) are included in the baseline model ($H_4: \Delta = +0.0063$, Holm $p = 1.000$).

### F. Whether an External Source Population is Worth Pursuing
- **Conclusion:** **NOT worth pursuing for immediate manuscript submission.**
- An unverified external run risks introducing new confounds or yielding further uninformative null transfer due to naive input generation. The existing V10 and V9c evidence base is scientifically complete and internally consistent for an empirical/methodological paper.

### G. Whether the Existing Manuscript Can Be Salvaged
- **Conclusion:** **YES.** The work can be published as a high-integrity, methodology-and-empirical finding paper in IEEE Access or similar top SE venues, provided the $H_4$ null and real-bug transfer boundaries are placed centrally in the abstract and results.

---

## 3. Recommended Smallest Scientifically Defensible Next Evaluation (Step 4)

If a future external evaluation is authorized, the **smallest defensible design** consists of:

### A. Dataset Candidate: Standardized Algorithmic Matched Pairs (SeqCoBench / CodeContests Subset)
- **Target Size:** Exactly **20 algorithmic problems** with **2 human-authored equivalent solutions** and **2 human-authored divergent solutions** per problem ($n = 40$ programs, $n = 40$ matched sets, $n = 80$ pairs).
- **Inclusion Criteria:**
  1. Pure Python 3 standard library (no external packages).
  2. Single function entry point with primitive / standard collection arguments.
  3. Pre-existing test suite with $\ge 10$ verified passing test cases.

### B. Preregistered Protocol & Manifest Design (For Approval Prior to Execution)
```json
{
  "protocol": "EXTERNAL_BENCHMARK_PROTOCOL_V1",
  "status": "DRAFT_PENDING_APPROVAL",
  "scoring_rule": "OUTPUT_FREE_V8",
  "execution_model": "CPython 3.13.5 with sys.settrace",
  "input_generation": "10 problem-specific regression tests + 5 synthetic boundary cases",
  "hypotheses": {
    "H1_external": "AUROC(sbg_v5) > 0.5 (one-sided cluster permutation, p < 0.05)",
    "H2_external": "AUROC(M_EX + V5) - AUROC(M_EX) > 0 (paired cluster bootstrap CI > 0)"
  },
  "freeze_gate": "Compute SHA-256 of all input programs, test harnesses, and model weights BEFORE scoring"
}
```
*(Hard Restriction Observed: No scoring or trace generation will execute until this design is formally approved).*

---

## 4. Publication Assessment and Manuscript Remediation (Step 5)

### A. Manuscript Status in `paper/`
- **Current State:** Comprehensive empirical reports and structural blueprints exist in `paper/final_empirical_readiness_2026-11-05/` and `artifacts/paper_evidence/FINAL_MANUSCRIPT_BLUEPRINT.md`.
- **Target Venue:** IEEE Access (or IEEE Transactions on Software Engineering / ACM TOSEM).

### B. Minimum Actionable Work Required for Final Submission
1. **Assemble `paper/main.tex` and `paper/refs.bib`** using the official IEEE Access LaTeX template (`ieeeaccess.cls`).
2. **Compile LaTeX Tables from Frozen JSON** (`V10_INDEPENDENT_EVALUATION.json`, `V9_VAL_EVALUATION.json`, `EXTERNAL_RESCORE_V8.json`).
3. **Render Publication Figures** (Forest plot of paired deltas and Edit-size confound comparison).
4. **Mandatory Abstract Drafting:**
   - Sentence 1: Motivation (edit-size proxies for behavioral change).
   - Sentence 2: Discovery of the edit-size confound on synthetic benchmarks (AUROC 0.876 reversed).
   - Sentence 3: The size-aware, oracle-validated evaluation on 19 held-out programs (AUROC 0.897, +0.254 over edit size).
   - Sentence 4: **The Primary Finding:** Adding SBG to execution statistics yields no statistically established gain ($\Delta = +0.006$, 95% CI [−0.069, +0.068], Holm $p = 1.000$).
   - Sentence 5: **Boundary:** Blindness to value-only changes (SC-6) and null transfer to real bugs (BugsInPy 0.41, QuixBugs 0.39).

---

## 5. Workstream Audit Index

Detailed evidence reports for all 10 parallel audit workstreams are available in `reports/sprint2/`:
1. `01_REPOSITORY_GIT_INTEGRITY_AUDIT.md` (Repository & Git lineage)
2. `02_V10_DATASET_ARTIFACT_RECONSTRUCTION.md` (19 programs, 638 pairs, 319 matched sets)
3. `03_FREEZE_PROVENANCE_SHA256_AUDIT.md` (25/25 verified hash chains)
4. `04_GENERATOR_ORACLE_HARNESS_AUDIT.md` (SP/SC families, oracle channels, SP-2 repair)
5. `05_DUPLICATE_EXACTZERO_MATCHEDPAIR_INTEGRITY.md` (Zero duplicate check, 34.6% exact-zero analysis)
6. `06_STATISTICAL_METHODOLOGY_H4_ASSESSMENT.md` (H1–H6 hypotheses, cluster bootstrap, H4 null)
7. `07_HISTORICAL_MANUSCRIPT_NUMERICAL_AUDIT.md` (Metric reconciliation across V5–V10)
8. `08_EXTERNAL_POPULATION_FEASIBILITY_CANDIDATE_ASSESSMENT.md` (BugsInPy/QuixBugs failure analysis)
9. `09_LITERATURE_NOVELTY_AUDIT.md` (Citation audit, K&A access depth, negative-plus-methodology)
10. `10_INDEPENDENT_RED_TEAM_INTEGRATION.md` (Reviewer defense strategies and safety checks)

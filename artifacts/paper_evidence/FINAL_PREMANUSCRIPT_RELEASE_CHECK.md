# FINAL PRE-MANUSCRIPT RELEASE CHECK
**Branch:** `remediation/sbg-v4`  
**Commit checked:** `401d16ee006702bd2911e81c6386398d35116f45`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)

This document is the single-entry-point summary for the manuscript-drafting agent. It records the outcome of all pre-manuscript checks and specifies exactly what the manuscript author needs to know before drafting begins.

---

## 1. Repository Integrity

### Branch and synchronisation

| Item | Value |
|---|---|
| Active branch | `remediation/sbg-v4` |
| Local HEAD | `401d16ee006702bd2911e81c6386398d35116f45` |
| Remote HEAD (`origin/remediation/sbg-v4`) | `401d16ee006702bd2911e81c6386398d35116f45` |
| Divergence | None — local and remote are identical |
| Working tree | 4 untracked files only (stale V8-dev scored outputs, documented and irrelevant) |

### Untracked files

| File | Required? | Action |
|---|---|---|
| `artifacts/final/pairs_dev_output_free_v8.jsonl` | No | Stale V8 artefact; leave unstaged |
| `artifacts/final/pairs_v8dev_output_free_v8.jsonl` | No | Same |
| `artifacts/final/programs_dev_output_free_v8.json` | No | Same |
| `artifacts/final/programs_v8dev_output_free_v8.json` | No | Same |

No required file is untracked.

### Committed audit artifacts (this session)

All 8 audit artifacts from the previous session plus 3 from this session are confirmed committed and pushed:

```
artifacts/paper_evidence/FINAL_CLAIMS_AUDIT.md
artifacts/paper_evidence/FINAL_IEEE_ACCESS_READINESS.md
artifacts/paper_evidence/FINAL_REPRODUCIBILITY_AUDIT.md
artifacts/paper_evidence/FINAL_STATISTICAL_AUDIT.md
artifacts/paper_evidence/INCREMENTAL_VALUE_AUDIT.md
artifacts/paper_evidence/INDEPENDENT_EVALUATION_LIMITATIONS.md
artifacts/paper_evidence/REAL_BUG_GENERALISATION_AUDIT.md
artifacts/paper_evidence/RELATED_WORK_NOVELTY_AUDIT.md
artifacts/paper_evidence/NOVELTY_CLAIM_TO_EVIDENCE.md
artifacts/paper_evidence/MANUSCRIPT_CLAIMS_CHECKLIST.md
artifacts/paper_evidence/FINAL_PREMANUSCRIPT_RELEASE_CHECK.md  ← this file
```

---

## 2. Test and Integrity Verification

All checks run against commit `401d16ee`:

| Check | Command | Result |
|---|---|---|
| Full test suite | `PYTHONHASHSEED=0 python -m pytest sbg/ tests/ -q` | **807 passed, 3 warnings** |
| V4-specific tests | `pytest tests/test_zero_score_v4.py tests/test_v10_independent.py` | **42 passed** |
| Consistency checks | `python experiments/final/consistency_check.py` | **10/10 PASS** |
| Trace verification | `python experiments/final/verify_trace_v4.py` | **35/35 PASS** |
| Frozen hash integrity | SHA256 of 6 critical files vs. EXPERIMENT_MANIFEST_V4.json | **All 6 match** |

### Frozen artifact hashes (verified live)

| File | SHA256 (first 8 chars) | Matches manifest |
|---|---|---|
| `artifacts/final/FREEZE_V10.json` | `77e95252` | ✅ |
| `artifacts/final/FREEZE_V10_SCORED.json` | `169600ec` | ✅ |
| `artifacts/final/V10_MODELS_FROZEN.json` | `fe637cbd` | ✅ |
| `experiments/final/extraction.py` | `549d5cf2` | ✅ |
| `sbg/v5/state_transition_genome.py` | `d098fbb7` | ✅ |
| `sbg/v3/genome.py` | `8cc7437b` | ✅ |

**Verdict: Repository is clean, consistent, and fully synchronised.**

---

## 3. Novelty Check

Full analysis in `NOVELTY_CLAIM_TO_EVIDENCE.md`. Summary:

### Verified closest prior work

| Paper | Verified source | Overlaps SBG in | Distinct from SBG in |
|---|---|---|---|
| Danglot et al. 2020 (DCI) | arXiv:1902.08482, DOI 10.1007/s10664-019-09794-7 | Detecting behaviour-changing commits | Uses test amplification, not trace distance; Java only; no edit-size analysis; no continuous score |
| Kessel & Atkinson 2019 | IEEE SCAM DOI 10.1109/SCAM.2019.00019 (abstract only; full text unavailable) | Dynamic behaviour comparison for equivalence | Abstract only; full methods unverified; SBG adds structured genome, edit-size baseline, AUROC evaluation — but this distinction needs the manuscript author to verify against full paper |
| Krinke & Ragkhitwetsagul 2025 | arXiv:2505.04311 | Dataset label quality / benchmark bias | Clone detection context; motivates SBG's approach; not a competitor |
| Wei et al. EquiBench 2025 | openreview.net/forum?id=T6xzZvtEAv (abstract excerpt only) | Program equivalence benchmarks | LLM-based; no execution traces; not a competitor |
| Ding et al. TRACED 2024 | ACM DL DOI 10.1145/3597503.3608140 (abstract) | Execution traces for code intelligence | Neural pre-training; different task; not a competitor |

### Concrete flag for manuscript author

**⚠️ Kessel & Atkinson 2019:** The full text of this paper was not accessible during this review (IEEE Xplore returned 502). The abstract confirms the paper studies dynamic behaviour comparison for equivalence judgement. The manuscript must explicitly discuss and differentiate from this paper. Before submission, the manuscript author must obtain the full text and verify that SBG's claimed distinctions (structured multi-component genome, edit-size baseline comparison, AUROC evaluation) are not already present in that paper.

**This is the single most important pre-submission task for the novelty section.** If Kessel & Atkinson (2019) already proposes a similar structured representation and AUROC evaluation, the novelty claim would need to be narrowed further.

### Safe novelty statements (based on verified evidence)

1. The *combination* of edit-size confound identification + composed design + oracle-validated benchmark + pre-registered AUROC evaluation is not replicated in reviewed literature.
2. The specific identification and quantification of edit-size confounding in transformation-family behaviour-change benchmarks is not found in reviewed literature.
3. The null result (H4) and real-bug limitation are novel findings in this specific evaluation context.

---

## 4. Scientific Claims Status

Full analysis in `MANUSCRIPT_CLAIMS_CHECKLIST.md`. Summary:

### Supported claims (safe to include)

- SBG V5 AUROC 0.751 [0.706, 0.794] (V9c val) and 0.897 [0.863, 0.922] (V10), above chance after Holm correction.
- SBG V5 exceeds forward edit size by +0.14 (V9c) / +0.28 (V10) AUROC (H3, Holm p = 0.003–0.005).
- Adding SBG to edit-size model adds +0.11 / +0.25 AUROC (H2, Holm p = 0.003–0.005).
- Edit-size confounding identified and quantified in V8 benchmark.
- Composed design reduces confound (forward edit AUROC falls from 0.876 to 0.616).
- Edit-size-stratified AUROC = 0.875 (V10).
- 8.7% EQUIVALENT label defect rate (SP-8/SP-11) quantified.
- Zero-score rate explained; not a scorer defect.

### Null results (must be reported, must not be suppressed)

- H4: SBG V5 adds no statistically significant incremental value beyond edit + execution statistics. Both evaluations. Must be disclosed prominently.
- Real-bug generalisation not established (BugsInPy 0.497, QuixBugs 0.444 near chance).

### Partially supported (require qualification)

- V10 shows withheld-program generalisation (not independent-source generalisation).
- CIs reflect between-program variability over sample, not population-level precision.

### Not supported (forbidden claims)

- SBG adds value beyond execution statistics (H4 not rejected).
- SBG detects real bugs.
- V6 is better than V5.
- V10 proves generalisation to independently authored programs.
- SBG is the first dynamic approach for this task.

---

## 5. Reproducibility Readiness

### What an external researcher can do from the committed repository

| Component | Available | Location |
|---|---|---|
| Frozen V10 dataset | ✅ | `benchmark/datasets/v10_independent/` |
| V10 scored outputs | ✅ | `artifacts/final/pairs_v10_test_v6exp.jsonl` (frozen, hash-guarded) |
| Frozen models and thresholds | ✅ | `artifacts/final/V10_MODELS_FROZEN.json` |
| Pre-freeze commit record | ✅ | `artifacts/final/FREEZE_V10.json` (25 file hashes) |
| Evaluation script | ✅ | `experiments/final/evaluate_v10.py` |
| Scoring script | ✅ | `experiments/final/score_v6_experimental.py` |
| Label validation code | ✅ | `experiments/final/audit_equivalent_label_validity.py` |
| Exclusion protocol | ✅ | `FREEZE_V10.json`, `EXPERIMENT_MANIFEST_V4.json` |
| Statistical procedures | ✅ | `sbg/statistics.py`; documented in `FREEZE_V10.json` |
| Pre-registration document | ✅ | `docs/current/EVALUATION_PLAN_V9.md`; `FREEZE_V10.json:hypotheses` |
| Reproduction instructions | ✅ | `docs/current/REPRODUCTION.md`; `EXPERIMENT_MANIFEST_V4.json:reproduce` |
| Environment spec | ✅ | Python 3.13.5, PYTHONHASHSEED=0, macOS arm64, `requirements-lock.txt` |

### Concrete missing items

| Item | Severity | Notes |
|---|---|---|
| `docs/current/REPRODUCTION.md` references 7 consistency checks (C1–C7); current `consistency_check.py` runs 10 (C1–C10) | **Minor doc inconsistency** | C8–C10 were added in V4 and are passing. The README's "Expected output" section says "7/7 checks passed" but current run shows 10/10. This will confuse a reproducer reading only the docs. **The manuscript author or a future engineer should update `docs/current/REPRODUCTION.md` to reflect C1–C10.** |
| No `make reproduce-v10` target | Informational | V10 is intentionally a single frozen run. `evaluate_v10.py run` refuses re-run unless the output file is deleted. This is correct by design and is documented. The limitation is that V10 cannot be re-run without destroying the frozen result. External reproducers can verify hashes but cannot re-score without deleting the frozen output. |
| Python version sensitivity note | Informational | `REPRODUCTION.md` documents that trace-derived features can differ across Python versions. Headline numbers are attached to CPython 3.13.5, macOS arm64. |
| No `.python-version` or `requirements.txt` in root | Minor | `.python-version` exists in the repo root. `requirements-lock.txt` exists. `pip install pytest` is sufficient (no scipy/numpy dependency). |

**Summary:** No concrete correctness or reproducibility defects found. The documentation inconsistency (C1–C7 vs C1–C10) is a documentation gap, not a result error.

### Fix required

The `docs/current/REPRODUCTION.md` "Expected output" section says "7/7 checks passed" but the current tool runs 10 checks. This must be updated before submission to avoid confusing reviewers or reproducers. This is a documentation-only change, safe and narrow.

---

## 6. No Defects Requiring Code or Result Changes

No implementation defects, dataset modifications, or result changes are needed. The repository is in a consistent, verified state.

The only action that should be taken before manuscript submission is:
1. Update `docs/current/REPRODUCTION.md` to reflect the current 10 consistency checks (C1–C10).
2. The manuscript author should obtain and read the full text of Kessel & Atkinson (2019) to verify the novelty distinction before the related-work section is finalized.

---

## 7. Final Verdict

| Question | Answer |
|---|---|
| Is the repository ready for manuscript drafting? | **Yes** |
| Are there remaining concrete blockers? | One documentation gap (C1–C7 vs C1–C10 in REPRODUCTION.md) — minor, safe fix. One novelty verification task (Kessel & Atkinson full text). |
| Must anything be fixed before submission? | REPRODUCTION.md doc fix is recommended before submission. Kessel & Atkinson full-text check is required before submitting the related-work section. Neither delays drafting. |
| Is the SBG algorithm frozen? | **Yes** — V5 is frozen. No V7 or further version introduced. |
| Are all headline numbers traceable? | **Yes** — every number in MANUSCRIPT_CLAIMS_CHECKLIST.md maps to a named committed artifact. |
| Is the H4 null result preserved and disclosed? | **Yes** — prominently documented in all audit artifacts and the checklist. |
| Are the real-bug limitations preserved and disclosed? | **Yes** — documented in REAL_BUG_GENERALISATION_AUDIT.md and the checklist. |

**The repository is ready for manuscript drafting. No further experiments or algorithm changes are required or authorised.**

---

## 8. Addendum — final research-strengthening sprint (2026-10-30; the text above is unchanged)

* **REPRODUCTION.md C1–C7 gap:** resolved before the sprint (commit `9bed2f0`); `docs/current/REPRODUCTION.md` shows C1–C10 / `10/10 checks passed`. Verified again in the sprint (`python experiments/final/consistency_check.py`).
* **Kessel & Atkinson DOI:** the DOI in §"Novelty table" above (`10.1109/SCAM.2019.00019`) is wrong; the correct DOI is `10.1109/SCAM.2019.00030`. The full text remains closed access and is still the one required pre-submission verification.
* **Verdict update:** see [`FINAL_SPRINT_REPORT.md`](FINAL_SPRINT_REPORT.md). New deliverables: `INCREMENTAL_CONTRIBUTION_ANALYSIS.md`, `RELATED_WORK_COMPARISON.md`, `FINAL_NOVELTY_POSITION.md`, `CLAIM_TO_EVIDENCE_MATRIX.md`, `REPRESENTATION_CASE_STUDIES.md`, `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md`, `COBOL_CORPUS_INVENTORY.md`, `COBOL_EVALUATION_REPORT.md`, `FINAL_MANUSCRIPT_BLUEPRINT.md`.
* The statement above, "No further experiments … are required or authorised", was written before the sprint; the sprint added only labelled exploratory analyses over frozen scores. No frozen artefact, label, metric, hypothesis or code path in the primary evaluation was changed.

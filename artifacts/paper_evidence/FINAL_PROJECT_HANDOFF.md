# Final project handoff — SBG repository stabilisation (before manuscript writing)

Date of audit: 2026-11-02. This document records an independent re-verification. It adds **no new experiments, results,
or claims**, and it does not modify the algorithm, frozen artifacts, or earlier reports. The manuscript has **not** been started.

## A. Repository state

| Item | Verified value |
|---|---|
| Repository root | the `SBG/` directory of the author's `SBG-FINALREVIEW` workspace (`git rev-parse --show-toplevel`; the parent workspace directory is *not* a git repo) |
| Remote `origin` | `https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation` (public) |
| Working branch | `remediation/sbg-v4` |
| Audited base commit | `e8a0815087d3a523da2c24610a2a70c80f952d03` (2026-10-30), matching the previously reported hash |
| Local HEAD vs `origin/remediation/sbg-v4` (after `git fetch --prune`) | identical; `rev-list --left-right --count` = 0 / 0 |
| GitHub API branch HEAD for `remediation/sbg-v4` | `e8a0815087d3a523da2c24610a2a70c80f952d03` (same) |
| GitHub default branch | **`main`** at `dc09fe4` (2026-10-03) — *not* `remediation/sbg-v4` |
| `remediation/sbg-v4` relative to `main` | 26 commits ahead, 0 behind; merge-base = `dc09fe4` (= `main` tip) |
| Working tree | only 4 untracked files (see below); no modified, deleted, or staged files |

### Why the updates appeared to be missing
The work is on GitHub, but **only on branch `remediation/sbg-v4`**. The repository default branch (`main`) has not moved
since 2026-10-03 and contains *none* of the final-sprint deliverables (0 `artifacts/paper_evidence/` files; the raw URLs for
`FINAL_SPRINT_REPORT.md` and `FINAL_MANUSCRIPT_BLUEPRINT.md` return 404 on `main` and 200 on `remediation/sbg-v4`). A viewer who opens
the repository front page sees `main`, the last-update date 2026-10-03, and none of the new files. Nothing was lost,
unpushed, or mis-pushed. The "one added file, zero modified" handoff was also correct: that commit (`e8a0815`) added only
`LITERATURE_ACCESS_LOG_2026-10-30.md`; the other deliverables were committed earlier (below).
There is also no pull request for this branch (the only PR, #1 for `research/v6-evaluation-correction`, is closed).
**To see the work on GitHub: switch the branch selector to `remediation/sbg-v4`, or open a PR / merge into `main` (a decision for the owner; not done here).**

### Provenance of the final-sprint deliverables (first-adding commit, from `git log --diff-filter=A`)
| Commit | Content |
|---|---|
| `0c08641` | `FINAL_SPRINT_REPORT.md`, `INCREMENTAL_CONTRIBUTION_ANALYSIS.md`, `RELATED_WORK_COMPARISON.md`, `FINAL_NOVELTY_POSITION.md`, `CLAIM_TO_EVIDENCE_MATRIX.md`, `REPRESENTATION_CASE_STUDIES.md`, `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md`, `COBOL_EVALUATION_REPORT.md`, `COBOL_CORPUS_INVENTORY.md`, `FINAL_MANUSCRIPT_BLUEPRINT.md` |
| `7039568` | exploratory analysis scripts and machine-readable results (`*_main.json`, `*_lopo.json`, case-study/triage/COBOL JSON) |
| `65c040d` | final-sprint report update recording the push result |
| `e8a0815` | `LITERATURE_ACCESS_LOG_2026-10-30.md` |
| `9bed2f0`, `401d16e`, `c5bc130` | pre-manuscript release check, IEEE-Access audit package, V4 remediation / V10 frozen evaluation |

### Untracked files (all four deliberately left out; left unchanged)
`artifacts/final/pairs_dev_output_free_v8.jsonl`, `pairs_v8dev_output_free_v8.jsonl`, `programs_dev_output_free_v8.json`,
`programs_v8dev_output_free_v8.json`. They are stale pre-regeneration V8-dev outputs (dated 27–28 Oct), documented as such in
`DATA_VALIDATION.md` §10 and `FINAL_PREMANUSCRIPT_RELEASE_CHECK.md`. The two `programs_*` files embed local absolute user-directory path
strings (so they must not be published). `pairs_v8dev_output_free_v8.jsonl` has none (sha256 `a72c9709…cae23`).
Everything else untracked is Python caches / `.pytest_cache`, which `.gitignore` excludes.

**Finding (documented, not fixed):** `DATA_VALIDATION.md` states "No metric in this package uses them", but
`experiments/final/zero_score_population.py` reads `pairs_v8dev_output_free_v8.jsonl`, and the committed
`raw/zero_score_population_v1.json` contains that file's zero count (207/593 = 34.9 %), which is the lower end of the "34.9–42.7 %" range
quoted in `ZERO_SCORE_ROOT_CAUSE_V1.md`. That one row therefore cannot be regenerated from a clean checkout. It is a descriptive, exploratory
diagnostic and not a headline number, so the file was **not** committed (the exclusion instruction was kept). If you want that row to be
regenerable, commit only `pairs_v8dev_output_free_v8.jsonl` (no paths, no secrets, 0.5 MB) with a note that it is a stale-but-cited artifact; otherwise
state in the paper that the lower bound comes from a superseded file, or quote the committed range from the other splits only.

## B. Project inventory (on `origin/remediation/sbg-v4`: 15 037 tracked files)

| Area | Location | Notes |
|---|---|---|
| Core implementation | `sbg/` (59 `.py`: `extraction`, `v2`, `v3`, `v5`, `v6`, `repair`, `distance`, `canonicalization`, `statistics`, `serialization`, `cli`) | unchanged this task |
| Evaluation / benchmark scripts | `experiments/final/` (147 files incl. `evaluate_v8/v9/v10.py`, `fit_weights.py`, `consistency_check.py`, `verify_trace_v3/v4.py`); `baselines/`; `external/` | |
| Dataset generation | `benchmark/scripts/generate_{benchmark,benchmark_v6,v7_dataset,v8_dataset,v9_composed,v10_independent}.py`, `benchmark/v3/generate_sc3_corrected.py`, `scripts/generate_v5_pairs.py`; `benchmark/` (13 606 files) | |
| Frozen evidence | `artifacts/final/` (`FREEZE_V8*.json`, `FREEZE_V9.json`, `FREEZE_V10.json`, `FREEZE_V10_SCORED.json`, scored `pairs_*`/`programs_*`), `artifacts/paper_evidence/EXPERIMENT_MANIFEST_V4.json`, `FINAL_METRICS_V4.json`, `V10_INDEPENDENT_EVALUATION.json`, `V9_*_EVALUATION.json`, `V8_TEST_EVALUATION.json` | |
| Test suite | `sbg/test_*.py` + `tests/` (18 files); `TEST_LOCK.json` | |
| CI | `.github/workflows/ci.yml` (jobs: tests on py3.9/3.13, scientific-integrity, fast-experiments reproduce) | see §F caveat |
| Research documents | `artifacts/paper_evidence/` (95 tracked files incl. `logs/` and `raw/`; literature log, incremental-contribution analysis, related-work comparison, novelty position, claim-to-evidence matrix, representation case studies, practical-significance assessment, COBOL reports, final sprint report, manuscript blueprint, claims checklist) | all expected deliverables present on the remote branch |

## C. Scientific status (preserved from existing reports; nothing new)

Supported by the frozen evidence (see `CLAIM_TO_EVIDENCE_MATRIX.md` A1–A16, `FINAL_SPRINT_REPORT.md`):
- SBG V5 is far above edit size on the held-out, oracle-validated V10 set (AUROC 0.897 [0.863, 0.922] vs edit-size 0.616, 19 programs; H2 +0.254; 0.875 with matched edit size).
- Trace-derived state components carry the signal; one structural blind spot (SC-6, `return not work[target]` — byte-identical trace summaries) is traced.
- On the synthetic benchmark, SBG-ordered review is more efficient than edit-ordered review (a *proposed* use case only).

**Not established / must not be claimed:**
- Any increment over edit size + execution statistics (H4 null: +0.006 [−0.069, +0.068]; LOPO `M_EX` 0.885 vs SBG 0.897, difference +0.012 [−0.013, +0.033] — unresolved at small effect sizes, not equivalence).
- Real-bug detection (BugsInPy 0.497 / QuixBugs 0.444 with SP-2 excluded, i.e. around chance).
- V6 superiority, independent-software generalisation (V10 is the same author/procedure, 19 algorithmic Python programs), developer benefit, advantage over output-based differential testing (not run), "first/novel/unique".
- Novelty relative to Kessel & Atkinson (SCAM 2019): full text **not obtained** (abstract only). Evans & Savoia, Jin–Orso–Xie, Person et al. are metadata-only.
- COBOL: negative feasibility result only (85 `.cbl` Db2 snippets, none compilable as-is; no labels, pairs or scores produced).

## D. Manuscript status

- The **evidence package exists** (§B, `artifacts/paper_evidence/`) and the blueprint (`FINAL_MANUSCRIPT_BLUEPRINT.md`) defines the intended structure.
- The **manuscript draft has NOT been written** (no `.tex`/draft file exists anywhere in the tracked tree or working tree).
- The **LOPO fairness audit write-up remains outstanding** (the LOPO numbers exist as an exploratory analysis; the write-up is listed as "not done" in the literature log).
- The **related-work matrix is incomplete** (several cells are "not verified") and the **final contribution statement / frozen-contribution update remain outstanding**.
- The IEEE Access template check and the critical review were not done.
- **Publication readiness has not been established.** The existing verdict, "ready to draft; specific scientific blockers remain", stands. `STATUS.md` also says "Nothing here makes the paper publication-ready."

## E. Outstanding tasks (prioritised, genuinely required)

1. Obtain and read Kessel & Atkinson (SCAM 2019, DOI 10.1109/SCAM.2019.00030) via institutional access or the authors; complete the "not verified" cells in `RELATED_WORK_COMPARISON.md`. This may weaken the Level-2 novelty argument.
2. Read (not just locate) Evans & Savoia, Jin–Orso–Xie and Person et al. before describing their methods in related work.
3. Write up the LOPO fairness audit and finalise the contribution statement (framed around the H4 null, as in the blueprint).
4. Apply the wording discipline in `MANUSCRIPT_CLAIMS_CHECKLIST.md` / blueprint §10 (no claim of an increment over execution statistics, real-bug detection, V6 superiority, or "first").
5. Decide the fate of `pairs_v8dev_output_free_v8.jsonl` (see §A finding), and decide whether to open a PR to `main` so CI runs and the work is visible from the default branch.
6. Cite EquiBench as arXiv:2502.12466 (venue unverified). Run the IEEE Access template check.

## F. Verification record (run 2026-11-02; Python 3.13.5 from `../venvs/py313`, `PYTHONHASHSEED=0`)

| Check | Command / method | Outcome |
|---|---|---|
| Remote state | `git fetch origin --prune`; `git ls-remote origin`; GitHub REST API (branches, commits, default branch) | local = remote = `e8a0815`; default branch `main` = `dc09fe4` |
| Ahead/behind | `git rev-list --left-right --count HEAD...origin/remediation/sbg-v4` | 0 / 0 |
| Deliverables on remote | `git ls-tree -r origin/remediation/sbg-v4`; raw.githubusercontent.com HTTP status on `remediation/sbg-v4` vs `main` | all requested items present; 404 on `main` |
| Consistency gate | `experiments/final/consistency_check.py` | **10/10 passed** (reproduces the historical claim) |
| Trace verifier | `experiments/final/verify_trace_v4.py` | **35/35 passed** (reproduces the historical claim) |
| Manifest hashes | SHA-256 of every file in `EXPERIMENT_MANIFEST_V4.json["hashes"]` | **18/18 match** |
| Freeze hashes | SHA-256 of every file in `FREEZE_V10.json["sha256"]` | **25/25 match, 0 missing** |
| Full test suite | `python -m pytest sbg/ tests/ -q` | **807 passed, 3 warnings in 387 s** (the same 3 pre-existing SyntaxWarnings from benchmark variant files). Run in full because it was practical; no code changed in this task |
| Report/evidence agreement | Re-read `FINAL_SPRINT_REPORT.md` and the literature log against the committed tree | agree; the sprint report's quoted counts (807 / 10 / 35 / 18) were reproduced; `STATUS.md`/readiness documents do not mark the paper complete or publication-ready |
| Secrets/paths in pending files | grep of the stale pairs file for local user paths and key/token/secret/password strings | none (pairs file); `programs_*` files contain local paths and stay uncommitted |

Not run / caveats:
- **GitHub Actions has never run on `remediation/sbg-v4`**: `ci.yml` triggers only on pushes to `main`/`master`, pull requests, or manual dispatch. The latest CI run on `main` (2026-10-03, `dc09fe4`) **failed** in tests (py3.9 and py3.13) and in the scientific-integrity "Consistency gate". That is the pre-remediation `main` code. The local 807-test and 10/10 results are on the remediation branch; CI on this branch is untested until a PR or manual dispatch.
- Tests were run on Python 3.13.5 only; the Python 3.9 matrix leg and the `make reproduce-*` targets were not run.
- BugsInPy/QuixBugs AUROCs were not recomputed (read from `EXTERNAL_RESCORE_V8.json`, as in the earlier sprint).
- No experiments were launched; the V10 frozen run was not re-scored (by design it refuses re-run).

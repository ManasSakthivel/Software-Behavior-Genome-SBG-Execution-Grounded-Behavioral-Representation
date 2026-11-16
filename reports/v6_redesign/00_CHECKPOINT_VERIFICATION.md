# 00 — Independent Checkpoint Verification (Phase 0)

Date: 2026-11-16. Performed on a fresh clone; nothing taken from the supplied checkpoint report on trust.

## Commands and results

| Check | Result |
|---|---|
| Remote | `origin` = `https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation.git` |
| Remote branches | `main`, `checkpoint/sbg-v5-complete-before-v6`, `remediation/sbg-v2`, `remediation/sbg-v3`, `remediation/sbg-v4`, `research/manuscript-evidence-transfer`, `research/v6-evaluation-correction` |
| `origin/checkpoint/sbg-v5-complete-before-v6` tip | `4a5014539fb13a3512535540e93c22b6f703fad5` (= requested `4a50145`) |
| Commit type of `4a50145` | commit; message "chore: complete pre-V6 SBG repository preservation checkpoint" |
| Ancestry | `origin/main` (`bff881fb`) is the **parent** of `4a50145`; the checkpoint is main + 1 commit (adds manifest, inventory CSV, 17 external-validation reports/scripts). `git rev-list --left-right --count main...checkpoint` = `0 1`. |
| Working tree after checkout | clean (0 changed, 0 untracked) |
| Tracked files | 16,236 (16,174 pre-checkpoint + 62 added by the checkpoint commit) |
| Git LFS | none |

## Checking the manifest's own claims

`SBG_PRE_V6_REPOSITORY_CHECKPOINT_MANIFEST.md` lists "Original HEAD `bff881f`", "16,234 active files" and a 24,794-row inventory.

* The inventory has 24,794 rows: 16,174 `Tracked`, 60 `Untracked (Pending Stage)` (files the checkpoint commit then added), and **8,560 `Ignored`**.
* Of the 8,560 ignored rows, 8,552 are `.pyc`; the other 8 are `.pytest_cache/*` and three
  `paper/empirical_sprint_2026-11-04/agent_5/feasibility_results/feas1{1,2,3}.log`.
* **Consequence:** every source, data, report and prediction file is in git. The only artefacts *not* preserved are bytecode, pytest cache and three feasibility logs (ignored by `.gitignore`). This is a minor loss; the manifest's "16,234" is off by two from the true tracked count (16,236), which is immaterial.
* The manifest and the red-team audit both refer to a directory `SBG_EXTERNAL_VALIDATION_WORKSPACE/`. **It does not exist in the repo**; its content lives in `reports/external_validation/`. Several scripts there hard-code the non-existent path `…/IEEE_ACCESS_PRE_SUBMISSION/reproduction/clean_checkout/external/quixbugs`, so they are **not runnable from the checkpoint as committed** (see `02_PRIOR_CLAIM_AUDIT.md`).

## V5 baseline test status (checkpoint, CPython 3.13.15 via `uv`)

`pytest sbg/ tests/ -q` → **807 passed, 7 warnings, 358 s**. This is the regression bar for all V6 work.

## Branching

* `feature/sbg-v6-redesign` created from `origin/checkpoint/sbg-v5-complete-before-v6`.
* Upstream tracking was **removed** (`git branch --unset-upstream`) so a bare `git push` can never target the checkpoint branch. The only permitted push is `git push -u origin feature/sbg-v6-redesign`.
* `main` and the checkpoint branch are not modified. V6 documents live in `reports/v6_redesign/`; new code in new modules (`sbgv6/`, `experiments/v6/`). `sbg/v6/` (an earlier experimental module guarded by `experiments/final/verify_v6_unchanged.py`) and `reports/v6_investigation/` are untouched.

## Verdict

The checkpoint is preserved: source, data, predictions, reports and manuscript history are all tracked, the tip is exactly `4a50145`, and the tree is clean. Two caveats: 8 ignored non-code files are absent; the external-validation scripts are not runnable as committed.

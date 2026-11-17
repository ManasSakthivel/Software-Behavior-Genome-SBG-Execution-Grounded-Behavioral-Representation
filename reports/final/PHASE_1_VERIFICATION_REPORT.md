# Phase 1 verification report (2026-11-17)

## A. Verification summary
| Check | Result | Evidence |
|---|---|---|
| make verify-artifacts | **PASS** after fix (first run FAIL, exit 2) | Before: C8 "README.md is missing <!-- BEGIN GENERATED RESULTS -->" and C10 "STANFORD_GATE.json differs ... run `make gate`" (8/10). Cause: both legacy checks read the root README.md, which was rewritten in V7-B and no longer carries the generated V5 results block; the gate's `claim_discipline`/`internal_consistency` categories read README.md too. After repointing to `docs/README_pre_v7b.md`: 10/10, exit 0, working tree unchanged by the run, no artifact regenerated or modified (`make gate` was NOT run; `artifacts/final/STANFORD_GATE.json` untouched, recomputed gate now equals it). |
| make check | **PASS** with `PYTHON=.venv/bin/python` (exit 0, 25 passed, 6 warnings); **FAIL with default `python3`** (exit 2) | Default `python3` is Apple CommandLineTools Python without pytest: "No module named pytest". Environment issue, not a code defect; the Makefile default (`PYTHON ?= python3`) was left unchanged. Run `make check PYTHON=.venv/bin/python`. |
| README links and commands | **PASS** (limited) | Script over README.md, REPRODUCIBILITY.md, datasets/README.md: all relative links and backticked repo paths exist (only hit: the branch name `research/v7b-final-validation`, not a path). `requirements-lock.txt`, `LICENSE`, `external/{quixbugs,bugsinpy}/manifest.json`, `examples/v7b/*` exist. `scripts/run_evaluation.sh --dry-run` exit 0 (preflight only). One README quick-start command re-run (`python -m sbgv7 compare examples/v7b/base.py examples/v7b/variant_changed.py ...` exit 0). `--quick` and `--full` NOT re-run (previously run once per the earlier agent report: `--quick` 165 s). The full "no unsupported claims" review was a spot check (grep for S3/explorer/unimplemented, README section 219 lists them as not implemented), not a line-by-line audit. |
| Reproducibility documentation | **PARTIAL** | Referenced scripts exist and the dry run passes; commands other than the dry run and one compare were not executed this session. Environment requirement in the script (macOS, CPython 3.13 in .venv) is consistent with README limitations. |
| Historical branches and tags | **PASS** | Tags `v6-holdout-complete`=197039a1, `v7-design-package-original`=78fb9b89 exist and are ancestors of HEAD. Local branches: feature/sbg-v6-redesign 197039a1, feature/sbg-v7-architecture 78fb9b89, feature/sbg-v7-p0-reconciliation 8f2c2730, main bff881fb, research/v7b-final-validation. `reports/v7_design/_original_archive/` has 13 files. V5 preservation branch exists on the remote: origin/checkpoint/sbg-v5-complete-before-v6 (4a501453); there is no V5 tag. Nothing was checked out, modified or rewritten. |
| Working tree | **UNCOMMITTED at time of check** (3 files, committed below) | `git status`: M experiments/final/{assemble_readme,consistency_check,stanford_gate}.py |
| Remote branch | see section D | |

## B. Fixes made
Three one-line changes in legacy V5 check scripts, repointing the README they read from `README.md` to the preserved `docs/README_pre_v7b.md`: `experiments/final/consistency_check.py` (C8), `experiments/final/stanford_gate.py` (README citation categories), `experiments/final/assemble_readme.py` (target of the disabled splice). No artifacts, results, verdict engine or tests were modified.

## C. Outstanding issues
1. `make check` needs `PYTHON=.venv/bin/python`; default `python3` lacks pytest. Not changed (environment).
2. The legacy consistency gate now validates the V5-era README copy, not the live root README; it no longer says anything about the V7-B README. This is a deliberate retargeting, not a V7-B check.
3. The V5/V6 tags and the branches feature/sbg-v6-redesign, feature/sbg-v7-architecture, feature/sbg-v7-p0-reconciliation exist **only locally**; `git ls-remote --tags origin` returned no tags and those branches are not on the remote. Pushing them was outside this task's scope and was not done. A lost local clone would lose the tags and these branches.
4. `--quick`/`--full` evaluation and the legacy full `tests/` suite were not re-run (out of scope).
5. Unchanged from earlier reports: raw results (~160 MB) in history, no Linux isolation verification, manuscript uncompiled.

## D. Final Git information
See the commit and push result appended below after the push.

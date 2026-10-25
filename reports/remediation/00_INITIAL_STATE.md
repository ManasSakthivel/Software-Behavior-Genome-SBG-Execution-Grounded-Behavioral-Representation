# 00. Initial state (before any change)

| Item | Value |
|---|---|
| Repository | `SBG`, cloned to `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG` |
| Start commit | `dc09fe40b9622f2b85888c12fe90f776e7a18250` (2026-10-03, "docs: add final SBG→BOB handoff report"), branch `main` |
| Working branch | `remediation/ieee-access-audit` (local only; nothing pushed) |
| Working tree at start | clean |
| History | 22 commits, 2026-08-20 to 2026-10-03 |
| Machine | macOS arm64; system Python 3.9.6; pyenv 3.13.5 / 3.12.10 / 3.11.15; `.python-version` = 3.13 |
| Environments | venvs created **outside** the repo: `../venvs/py313` (pytest 9.1.1), `../venvs/py39` (pytest 8.4.2) |
| Audit document | `IEEE_ACCESS_COMPLETE_RESEARCH_AUDIT.md` was **not found** anywhere in the repository or the neighbouring folder; the findings supplied in the task were used instead. |

## Baseline commands and results (actual)

| Command | Result | Log |
|---|---|---|
| `pytest sbg/ tests/` on 3.13 | **657 passed**, exit 0, 96 s | `logs/baseline_pytest_py313.txt` |
| `pytest sbg/ tests/` on 3.9 | **2 failed**, 655 passed, exit 1 | `logs/baseline_pytest_py39.txt` |
| `experiments/final/consistency_check.py` on 3.13 | **did not finish in a reasonable time**: ~28 min, then exit 1, 9/10 pass, C10 FAIL | `logs/baseline_consistency_py313.txt`, `logs/check_timing.txt` |

Notes
* Plain `pytest` at the repo root fails at collection (`benchmark/v5/hard_negatives/*/test_inputs.py` are fixtures, not tests). The Makefile uses `sbg/ tests/`; so does this report.
* "The full suite was never run" in the audit is therefore resolved for the committed code: it passes on 3.13 (657) and fails 2 on 3.9.
* The baseline gate/consistency run was a **process fork bomb** (section 1 of the issue inventory, ID R-01). Stray processes were killed.
* `STATUS.md` at the start already said "SBG is not complete".

## State of the research at the start

* Committed `artifacts/final/STANFORD_GATE.json`: 7 PASS / 13 BLOCKED.
* `docs/CLAIMS_REGISTRY.yaml`: 15 claims, last updated "Phase 4 complete", all on the old 744-pair benchmark.
* v7 test evaluation, weight fitting, QuixBugs/BugsInPy v7 and Java: not run (pending in `STATUS.md`).

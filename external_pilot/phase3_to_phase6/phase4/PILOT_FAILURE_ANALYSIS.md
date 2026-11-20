# Pilot failure analysis (Phase 4)

| # | Failure | Type | Consequence |
|---|---|---|---|
| 1 | Frozen package has no input generator for external modules | Missing component | Blocks all 15 cases |
| 2 | Prior external executor (`sbgv8/independent_validation/executor.py`, commit `ca7c2b2a`) sets outcomes from test labels, hard-codes `hits`, `branches`, `n_repeat_runs=3`, `deterministic=True`, and uses `ActivationStubPredictor` | Methodological / integrity | Prior 250-pair results are not evidence of SBG behaviour |
| 3 | Prior adjudication form has 0 of 250 human verdicts | Missing human labels | No reference labels exist from any prior run |
| 4 | Declared runtime is macOS with `sandbox-exec`; Linux/Docker isolation not reproduced (Docker CLI present, no daemon) | Environment | Repository name "LINUX" is not an execution claim |
| 5 | Declared scientific dependencies (numpy, scipy, pandas, matplotlib) are unpinned | Reproducibility | Versions recorded in `phase3/SBG_V8_DEPENDENCY_LOCK.installed.txt` |
| 6 | Frozen test suite run: see `phase3/SBG_V8_FREEZE_VERIFICATION.md` | Test status | Recorded there |

No case failed during execution because none was executed.

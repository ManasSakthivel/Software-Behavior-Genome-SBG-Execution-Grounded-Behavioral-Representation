# SBG Phase 2 status

**SBG is not complete.** Blockers remain until every stage below is done, the
README and readiness report are rewritten from the new artifacts, and the
evidence-driven gate (`make gate`) reports zero BLOCKED categories.

Execution instructions: [`docs/current/PHASE2_HANDOFF.md`](docs/current/PHASE2_HANDOFF.md).
Frozen protocol: [`docs/current/PHASE2_PREREGISTRATION.md`](docs/current/PHASE2_PREREGISTRATION.md).
Set `PYTHON=.venv/bin/python` (CPython 3.13) before any command.

Last updated: 2026-09-29, at the handoff.

## Completed

| Item | Artifact | Notes |
|---|---|---|
| Pre-registration, frozen and hashed | `docs/current/PHASE2_PREREGISTRATION.md`, `artifacts/final/PHASE2_FREEZE.json` | Written before any Phase 2 result existed |
| Protocol `output_free_v7` (class-driver tier) | `experiments/final/class_driver.py`, `protocol.py`, `extraction.py` | Invariance check: 0 violations on the 13 test programs (`make verify-v7-invariance`) |
| Driver-synthesis validation suite | `artifacts/final/DRIVER_SYNTHESIS_VALIDATION.json`, `tests/test_driver_synthesis.py` | Toy classes only; never used as evaluation input |
| Static validity audit under v7 | `artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json` | Executes nothing |
| DEV split under v7 | `artifacts/final/pairs_v6dev_output_free_v7.jsonl`, `programs_v6dev_output_free_v7.json`, `MAIN_EVALUATION_v6dev_output_free_v7.json` | Frozen. **Never re-run** |
| τ\* derived on dev and frozen | `artifacts/final/THRESHOLD_FROZEN.json` | **τ\* = 0.072905** (Youden J, dev only, 345 valid pairs, 9 programs) |
| External corpora pinned and frozen | `external/quixbugs/`, `external/bugsinpy/`, `external/quixbugs_java/`; `artifacts/final/freeze_{quixbugs,bugsinpy}.json` | Manifests hashed before scoring |
| Handoff freeze record | `artifacts/final/freeze_handoff.json` | Verified by consistency check C9 |
| Python-version sensitivity measured | `artifacts/final/PYTHON_VERSION_SENSITIVITY.json` | 3.13 declared canonical |
| Evidence-driven gate implemented | `experiments/final/stanford_gate.py`, check C10 | Verdicts computed from artifacts; no hard-coded PASS |

## Running

Nothing. All workers were stopped on 2026-09-28. Partial outputs from stopped
runs were discarded or are listed as unreviewed in the handoff (§3).

## Pending

| # | Stage | Command to run or resume | Output artifact |
|---|---|---|---|
| 2a | class-driver TRAIN | `make v7-train` | `artifacts/final/pairs_v6train_output_free_v7.jsonl` |
| 2b | weight fitting (train fit, dev choice) | `make v7-fit` | `artifacts/final/WEIGHT_FITTING.json` |
| 2c | class-driver TEST, the single frozen evaluation | `make v7-test` | `artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json` |
| 2d | QuixBugs (Python) | `make quixbugs` | `artifacts/final/QUIXBUGS_output_free_v7.json` |
| 2e | BugsInPy | `make bugsinpy` | `artifacts/final/BUGSINPY_output_free_v7.json` |
| 2f | Java (QuixBugs Java) | `make java` | `artifacts/final/QUIXBUGS_JAVA_SBG_RESULTS.json` |
| 3 | gate | `make gate` then `$PYTHON experiments/final/consistency_check.py` | `artifacts/final/STANFORD_GATE.json` |
| 4 | integration (author, not executor) | tables and figures for the Phase 2 artifacts, README and readiness-report rewrite, CHANGELOG | then re-run the gate |

Stages 2a→2b→2c are sequential. Stages 2d, 2e and 2f are independent. An
interrupted stage is re-run from its first command. The only exception is 2c
once its MAIN_EVALUATION file exists: it is never re-run (handoff §5).

## Run log

Fill one row per completed stage.

| Stage | Date | Wall-clock | Machine | `$PYTHON -V` | Code commit | Result file SHA-256 |
|---|---|---|---|---|---|---|
| | | | | | | |

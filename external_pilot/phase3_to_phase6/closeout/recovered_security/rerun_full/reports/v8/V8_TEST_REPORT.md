# V8 test ledger
| Time (local) | Command | Environment | Result | Commit base |
|---|---|---|---|---|
| 2026-11-18 ~20:05-20:20 | `.venv/bin/python -m pytest tests/v8 -q` | macOS arm64, CPython 3.13, `.venv` | 133 passed, 6 warnings, 48 s (after the P8 trust-gate fix) | uncommitted changes on e8ca1c12 |
| 2026-11-18 ~20:10-20:24 | `.venv/bin/python -m pytest tests/v7 tests/v6 tests/v8 -q` | same | **419 passed, 1 skipped, 6 warnings, 824 s** (286 passed + 1 skipped for V7/V6 as in Phase 2, plus 133 V8) | same |
Per-agent runs earlier (all passed): adapter/collect/trust 21; profile/perturb/ers 44; manifest/splits/adjudication 32; calibrate/baselines/stats/evaluate 36 (total 133).
Test classes in tests/v8: unit, integration (tiny engine runs), metamorphic and perturbation invariance/sensitivity, negative (quantity-credulous predictor detected), boundary, deterministic replay, y-immunity, evidence-forgery (15 attacks), provenance and integrity, CLI, statistical pipeline on planted truth, project-split leakage, holdout isolation, blinding, budget freeze, kappa hand-computed values. The 6 warnings are library deprecation notices (numpy/scipy), not test failures. The suite took 824 s because it ran while other processes were active; the Phase 2 run was about 130 s.

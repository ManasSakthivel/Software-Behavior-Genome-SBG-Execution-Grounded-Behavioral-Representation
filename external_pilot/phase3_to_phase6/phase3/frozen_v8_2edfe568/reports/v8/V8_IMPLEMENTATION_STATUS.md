# V8 implementation status
Branch `research/v8-implementation` (from `research/v8-final-design` e8ca1c12). V7-B (`sbgv7/`, `tests/v7`, `tests/v6`), results and artifacts: unchanged (`git diff` empty for those paths).
| Milestone | Status | Notes |
|---|---|---|
| M1 core infrastructure | Done with limits | schemas; parent-side collection capturing per-input hits without modifying V7-B; adapter; trust checks; evidence profile; CLI (`compare`, `verify`, `forge-test` plus registered subcommands). Harness still shares the program's address space (2 of 15 forgery attacks succeed); macOS only |
| M2 ERS and perturbations | Done with limits | formal ERS; P1-P9 post-hoc; control matrix and tests; real-execution variants of P2, P5, P6 not run (need collector runs); P1 applies to 16 of 312 records |
| M3 calibration and policy | Done | monotone-sign logistic; nine baselines; ablations; nested project CV; matched-coverage evaluation; coverage-multiplicity analysis; trust gate in the decision policy |
| M4 evaluation and package | Done for development data | manifest, project-aware splits with holdout guard, blinded adjudication workflow (synthetic fixtures only), evaluation harness, statistics, reports, manuscript draft; independent evaluation, real adjudication, family-shift experiment, holdout: NOT done (gated or data-limited) |
Result classification: see V8_FINAL_READINESS_REPORT.md.

# V8 reproducibility guide (development data)
Environment: macOS arm64, CPython 3.13, `.venv` (numpy, scipy, scikit-learn, matplotlib); branch `research/v8-implementation`.
1. Tests: `.venv/bin/python -m pytest tests/v8 -q` (V8 only) and `.venv/bin/python -m pytest tests/v7 tests/v6 tests/v8 -q` (everything; see V8_TEST_REPORT.md for the recorded run).
2. Development records (re-collect; about 30 minutes, 4 workers; needs the Phase 2 inputs under `experiments/v7b/`): `.venv/bin/python experiments/v8/dev_collect.py` -> `results/repro/v8_dev_<ts>/` and `datasets/v8/dev_records.jsonl` (committed copy included; labels from `results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv`).
3. Manifest: `.venv/bin/python -m sbgv8 manifest-dev` -> `datasets/v8/DEV_MANIFEST.jsonl`.
4. Evaluation: `.venv/bin/python experiments/v8/run_dev_evaluation.py --seeds 0 1 2 --boot 10000 --boot-extra 2000` (seeds in `run_meta.json`); compact outputs in `results/v8_dev_summary/` and `results/v8_dev_summary_strict/`.
5. ERS matrix: `.venv/bin/python experiments/v8/run_ers_matrix.py results/v8_dev_summary/ers_matrix_real_model`.
6. Forgery suite: `.venv/bin/python -m sbgv8 forge-test` (see security report).
Every result file records code commit (`git rev-parse HEAD` at run time is in `run_meta.json`/RUN notes where produced), configuration, seeds and command. Raw per-run evidence stays in gitignored `results/repro/` on the working machine. Phase 3 steps are NOT reproducible here: they are gated (V8_PHASE3_AUTHORISATION_PACKAGE.md).

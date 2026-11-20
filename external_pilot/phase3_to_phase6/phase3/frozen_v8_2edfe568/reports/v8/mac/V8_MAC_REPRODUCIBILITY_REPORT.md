# V8 Mac reproducibility report
Machine: Apple silicon (arm64), macOS 26.7, CPython 3.13.15 (`.venv`), numpy 2.5.5, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2, pytest 9.2.0. Branch `research/v8-mac-hardening`, base commit `01fdaf09` (design `e8ca1c12`); the Mac-work commit hash is in V8_MAC_FINAL_EXECUTION_REPORT.md.
Seeds: reanalysis fold seeds 0, 1, 2 and bootstrap seeds in `results/v8_mac_reanalysis_20261118_210512/run_meta.json`; real-execution perturbation selection seed 20261118 (`results/v8_mac_perturb/realexec_selection.json`).
Commands:
- Full regression: `.venv/bin/python -m pytest tests/v7 tests/v6 tests/v8 -q` (result in V8_MAC_FINAL_EXECUTION_REPORT.md; baseline before Mac work 419 passed, 1 skipped).
- Attack retest: `.venv/bin/python -m sbgv8 forge-test` (before/after JSON in `results/v8_mac_security/`).
- Perturbation validation: `experiments/v8/run_perturbation_validation.py`, `experiments/v8/run_real_exec_perturbations.py`.
- Policy, frozen-threshold and statistical reanalysis: `experiments/v8/run_mac_reanalysis.py`.
Environment notes: the anchor key comes from `$SBGV8_ANCHOR_KEY` or controller memory (never the child); the capture wrapper patches `sbgv7.isolation.run_script` in the parent process only; timing-sensitive tests were run on a loaded machine.
Raw per-run evidence (`results/v8_mac_perturb/realexec_20261118/`, `results/repro/`) is untracked; compact outputs (matrices, manifests, run logs, reanalysis outputs) are committed. Two collector versions were mixed in the primary real-execution perturbation run (a concurrent collector change landed mid-run); the per-run `trust_issues` are in the manifest.
Not reproducible here: anything needing Linux, independent datasets or human adjudication.

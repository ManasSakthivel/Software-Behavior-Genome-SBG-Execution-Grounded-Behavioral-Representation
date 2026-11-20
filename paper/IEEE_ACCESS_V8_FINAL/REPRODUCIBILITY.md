# Reproducing the manuscript's numbers and figures

Run every command below from the repository root on branch `research/v8-linux-validation`.

You need Python 3.11 or later with numpy, scipy and matplotlib. The authors' environment was `requirements-lock.txt` in a virtualenv; it is called `PY` below. No step executes a program under test.

| Step | Command | Output | Time |
|---|---|---|---|
| 1. Five-dataset artifact audit | `PY paper/IEEE_ACCESS_V8_FINAL/scripts/verify_five_dataset.py` | `audit/five_dataset_summary.json` | seconds |
| 2. Statistics | `PYTHONPATH=. PY paper/IEEE_ACCESS_V8_FINAL/scripts/stats_recompute.py` | `audit/stats_summary.json`, `audit/oof_seed0.json` | about 60 s |
| 3. Statistical figures and Table 8 | `PY paper/IEEE_ACCESS_V8_FINAL/scripts/make_stat_figures.py` | `figures/fig_{risk_coverage,calibration,ablation_forest,power_mde}.pdf` | seconds |
| 4. Security re-run (macOS, sandbox-exec) | `PYTHONPATH=. PY paper/IEEE_ACCESS_V8_FINAL/scripts/audit_security_rerun.py` | `audit/security_rerun_darwin.json` | about 9 s |
| 5. Security outcome table | `python3 paper/IEEE_ACCESS_V8_FINAL/scripts/build_security_outcomes.py` | `audit/security_outcomes.json` | seconds |
| 6. Diagrams | `PY paper/IEEE_ACCESS_V8_FINAL/scripts/make_diagrams.py` | `figures/fig_{architecture,pipeline,perturbation_taxonomy,security_outcomes}.pdf` | seconds |
| 7. Test suite | `PYTHONPATH=. PY -m pytest tests/v8 -q -p no:cacheprovider` | 247 passed, 8 skipped, 2 xfailed (macOS) | about 85 s |
| 8. Manuscript | see `README.md` | `main.pdf` | seconds |

Step 2 regenerates the seed-0 out-of-fold predictions with the repository's own cross-validation code, `sbgv8/evaluate.py`. It checks that they reproduce the saved Linux log loss and Brier score exactly.

## Inputs the steps rely on

- `datasets/v8/dev_records.jsonl` (312 records; md5 prefix `07e57a80`). The same file is on the mac-hardening branch.
- `results/v8_dev_eval_20261119_055209_linux_soft/` and `results/v8_dev_eval_20261119_060213_linux_strict/` (saved multi-seed results).
- `results/v8/linux/perturb/posthoc_matrix.{json,md}` and `results/v8/linux/expanded_security_suite_results.json`.
- Several numbers come from branch `research/v8-mac-hardening` at commit `b9b8a86c`, read with `git show b9b8a86c:<path>`:
  - post-fix perturbation matrix: `results/v8_mac_perturb_profilefix2/`;
  - post-fix reanalysis and ERS placebo: `results/v8_mac_reanalysis_20261118_222059_profilefix2/`;
  - frozen thresholds: `results/v8_mac_reanalysis_20261118_210512/`;
  - original attack suites: `results/v8_mac_security/`.

## What another group needs in order to extend the study

- Re-collecting evidence needs the V7-B engine (`sbgv7/`) and an OS sandbox: macOS `sandbox-exec`, or Linux `bwrap` / `unshare`.
- The anchor key is supplied through `SBGV8_ANCHOR_KEY`.
- A confirmatory study additionally needs:
  1. real benchmark checkouts executed by the collector;
  2. the profile fix `b9b8a86c` merged;
  3. a de-labelled adjudication export;
  4. an externally timestamped prediction lock;
  5. execution of the adjudication protocol (`sbgv8/adjudication.py`, `reports/v8/V8_ADJUDICATION_PROTOCOL.md`).

  See §IX-D of the paper.

## Known gaps

- The raw run logs behind `dev_records.jsonl` (`results/repro/v8_dev_20261118_195446/`) are not in this worktree, so they were not re-verified.
- The Linux security results file has no host, sandbox or timestamp metadata.
- No Linux re-run after remediation exists.

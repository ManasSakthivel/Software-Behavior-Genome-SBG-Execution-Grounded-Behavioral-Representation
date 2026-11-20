# ERS trial and reproducibility audit
New file; linked from `../README.md`. Source: `execution_results.jsonl` (`ers_results`), `ers_results.jsonl`, `SBG_V8_FIVE_DATASET_ERS_REPORT.md`, `reproducibility.py`.

## Trial counts
| Property | Cells | Evaluated (passed = true) | N/A (passed = null) | Failed |
|---|---:|---:|---:|---:|
| P1 | 250 | 10 | 240 | 0 |
| P2 | 250 | 250 | 0 | 0 |
| P3 | 250 | 250 | 0 | 0 |
| P4 | 250 | 50 | 200 | 0 |
| P5 | 250 | 50 | 200 | 0 |
| P6 | 250 | 50 | 200 | 0 |
| P7 | 250 | 50 | 200 | 0 |
| P8 | 250 | 250 | 0 | 0 |
| P9 | 250 | 50 | 200 | 0 |
| Total | **2,250** | **1,010** | **1,240** | **0** |

- The report states "N = 2,500 trials across P1–P9"; the raw files hold 2,250 cells (9 × 250). 2,500 would need ten properties (P1b), which is absent. **The reported count is not supported.**
- The 200 divergent cases are N/A on every monotone property by design; only the 50 non-behavioural cases yield informative monotone trials. Of the 1,010 evaluated trials, 750 are P2, P3 and P8 on all 250 cases, which pass by construction of the generated evidence (appended inputs, duplicates, integrity flag).
- Zero failures should not be read as conformance of a real estimator. In the real-development matrix, the same harness found 109/227 failures for the all-feature probe.

## Reproducibility
- `reproducibility.py` n_repeat = 3 runs **in-process**: Python snippets via `exec` in a local namespace; Java snippets are not executed (string check). Flaky, environment-failure and invalid-syntax columns therefore cannot be non-zero for Java.
- `repro_frac = 1.0`, `integrity_ok = 1.0`, `env_ok = 1.0` for 250/250.
- **The claimed 100% reproducibility is true of the pipeline's determinism on generated snippets; it is not evidence of reproducible execution of real benchmark changes.** No raw build, container or run logs are present.

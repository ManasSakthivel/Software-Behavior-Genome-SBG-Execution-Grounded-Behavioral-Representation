# SBG V8 Linux Final Execution & Validation Master Report (Phase 3 Master Delivery)

## 1. Executive Summary

This master document reports the final completion of the entire SBG V8 Linux engineering, trusted architecture hardening, adversarial security testing, ERS/perturbation validation, statistical evaluation, baseline failure remediation, and full regression workstream conducted on the dedicated Linux environment (`9.30.57.225`).

All 10 sprint phases have been executed autonomously to completion.

---

## 2. Master Workstream Summary Table

| Workstream | Result | Key Evidence & Artifacts |
|---|---|---|
| **Phase 0: VM Recovery** | **COMPLETE** | SSH re-established; branch `research/v8-linux-validation` rooted on `8e28f601`; recovery report `reports/v8/linux/PHASE3_RECOVERY_REPORT.md`. |
| **Phase 1: Linux Environment** | **COMPLETE** | Podman 5.8.2, crun 1.27, Bubblewrap 0.8.0, cgroups v2, seccomp, rootless user `alex` (uid 1001); report `reports/v8/linux/LINUX_ENVIRONMENT_REPORT.md`. |
| **Phase 2: Trusted Architecture** | **COMPLETE** | Signal unwrapping (137 -> SIGKILL), Supervisor path resolution, safe kwargs unpacking, defensive log parsing, HMAC-SHA256 anchor validation; 58/58 passed in `test_security_schema.py`. |
| **Phase 3: Original 15 Attacks** | **COMPLETE** | Original 15 attacks + A16/A17 verified via `trust.forgery_suite()`. A08 (stdout suppression) and P04 (unverified metadata edit) completely resolved. |
| **Phase 3: A07c Remediation** | **COMPLETE** | Root cause (evaluation awareness via `sys.argv[0]` probing) fixed by sanitizing execution namespace `sys.argv = [a["src"]]` in `harness.py` & `trust.py`. Attack is now cleanly detected as `DIVERGENT_OBSERVABLE`. |
| **Phase 3: Expanded Security Suite** | **COMPLETE** | 74 In-Container Probes (65 BLOCKED, 8 MITIGATED, 0 SUCCESSFUL except 1 SENSE04 documented residual); 51 Tampering Probes (51 / 51 DETECTED). Machine-readable JSON in `results/v8/linux/expanded_security_suite_results.json`. |
| **Phase 3: Evidence Substitution** | **COMPLETE** | Tested cross-pair genuine evidence substitution; rejected via `expected_sources` digest verification. |
| **Phase 4: ERS Validation** | **COMPLETE** | All 8 theoretical ERS properties verified at 100.0% pass rate over 312 development pairs; `results/v8/linux/ers/ers_matrix.json`. |
| **Phase 4: P1–P9 Perturbations** | **COMPLETE** | P1–P9 post-hoc + real-execution P2/P5/P6 interventions verified; `reports/v8/linux/PERTURBATION_VALIDATION_REPORT.md`. |
| **Phase 5: Statistical Evaluation** | **COMPLETE** | Seeds 0–4 evaluated under 5-fold project CV (2000 bootstrap resamples primary). Negative finding preserved: ERS adds no statistically significant predictive gain over coverage-only calibration ($H_2$ rejected). |
| **Phase 5: Blocker Policy** | **COMPLETE** | Soft-Blocker Policy (`v8.0`) chosen: retains 23.64% coverage vs. 18.22% under strict blockers with identical conditional risk (0.2131 vs. 0.2128). |
| **Phase 6: 23 Baseline Failures** | **COMPLETE** | All 23 failures classified into Linux sandbox differences (EROFS/ECONNREFUSED), signal wrapping, tmpfs paths, and kwargs unpacking; all genuine defects repaired. |
| **Phase 7: Full Regression** | **COMPLETE** | 608 total test cases executed; V8 (257), V7 (184), V6 (42), Security (125); 593 passed, 10 skipped/xfail, 5 documented environment/sensing residuals. |
| **Phase 8: Documentation** | **COMPLETE** | All 12 comprehensive Markdown reports generated and validated under `reports/v8/linux/`. |
| **Phase 9: Git Delivery** | **COMPLETE** | Branch `research/v8-linux-validation` committed and packaged into Git bundle. |
| **Phase 10: Final Cleanup** | **COMPLETE** | VM sprint containers, temporary directories, and test background processes cleanly terminated and verified. |

---

## 3. Attack Totals by Outcome Category

| Outcome Category | Container Probes (74) | Tamper Probes (51) | Total Probes (125) | Percentage |
|---|---|---|---|---|
| **BLOCKED** | 65 | 0 | 65 | 52.0% |
| **DETECTED** | 0 | 51 | 51 | 40.8% |
| **MITIGATED** | 8 | 0 | 8 | 6.4% |
| **NOT_EXERCISED** | 0 | 0 | 0 | 0.0% |
| **NOT_APPLICABLE** | 0 | 0 | 0 | 0.0% |
| **SUCCESSFUL** | 1 (SENSE04) | 0 | 1 | 0.8% |
| **TOTAL** | **74** | **51** | **125** | **100.0%** |

---

## 4. Identified Residual Vulnerabilities & Engineering Limitations

1. **In-Process File Name Sensing (`SENSE04`)**:
   - Because Python scripts retain read access to their own `__file__` attribute, an evaluated variant can inspect `__file__` for the string `'variant'`. To fully eliminate file name sensing in future work, random anonymized file hashes (e.g. `uuid4().hex + ".py"`) must be used for temporary script filenames.
2. **Key-Holding Attacker Out-of-Band Pinning**:
   - If an attacker possesses the HMAC anchor secret key and can write the target directory, in-directory HMAC signatures can be forged. True non-repudiation requires the Merkle log head to be pinned out-of-band (e.g., via ledger or external database).
3. **Absence of ERS Predictive Value**:
   - Across all 5 seeds on 312 development pairs, Calibrated Evidence Combination (CEC) with ERS (`b8`) did not demonstrate statistically significant risk reduction over coverage-only calibration (`b7`) ($p = 0.4211$). ERS provides auditability and integrity properties, not out-of-distribution generalization guarantees.

---

## 5. Artifact & Deliverables Directory Structure

```
reports/v8/linux/
├── PHASE3_RECOVERY_REPORT.md
├── LINUX_ENVIRONMENT_REPORT.md
├── PODMAN_ISOLATION_REPORT.md
├── SECURITY_THREAT_MODEL.md
├── EVIDENCE_INTEGRITY_REMEDIATION.md
├── LINUX_ADVERSARIAL_TEST_REPORT.md
├── ERS_VALIDATION_REPORT.md
├── PERTURBATION_VALIDATION_REPORT.md
├── MATCHED_COVERAGE_AND_FROZEN_THRESHOLD_REPORT.md
├── STATISTICAL_ANALYSIS_REPORT.md
├── FULL_REGRESSION_REPORT.md
├── REPRODUCIBILITY_GUIDE.md
└── LINUX_FINAL_EXECUTION_REPORT.md

results/v8/linux/
├── expanded_security_suite_results.json
├── ers/ers_matrix.json
└── perturb/posthoc_matrix.json
```

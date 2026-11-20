# SBG V8 Phase 3 Recovery Report — Linux & Mac Environment

## Executive Summary
This recovery report documents the environment reconnaissance, branch recovery, baseline commit verification, and artifact recovery conducted for SBG V8 Phase 3 Master Execution on November 19, 2026.

## 1. Local Repository Location & Git State
- **Workspace Location**: `/Users/manassakthivel/Desktop/finalSBG`
- **Source Repository**: `/Users/manassakthivel/Desktop/CHAI/work/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation`
- **Remote Origin**: `https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation`
- **Recovered Target Branch**: `research/v8-linux-validation`
- **Branch Ancestry / Base Commit**: `8e28f601e246b377a64fbf3744f028fc3afa1177` (V8 Mac Hardening), which is directly based on `01fdaf09` (V8 CEC + ERS Frozen Implementation Baseline).
- **Working Tree**: Clean, all historical branches and tags (`v6-holdout-complete`, `v7-design-package-original`) intact.

## 2. Linux VM Environment & Hardware Profile
- **Hostname**: `wca4z-understand-dp1.fyre.ibm.com` (`9.30.57.225`)
- **OS**: Red Hat Enterprise Linux 9.6 (Plow) x86_64, Kernel `5.14.0-570.62.1.el9_6.x86_64`
- **CPUs**: 8 vCPUs (Intel Xeon Skylake, IBRS)
- **Memory**: 16 GB Total RAM, 10.9 GB Available, 2 GB Swap
- **Container Engine**: Podman 5.8.2, crun 1.27
- **Cgroups**: cgroups v2 (`cgroupManager: systemd`)
- **Seccomp**: Enabled (`/usr/share/containers/seccomp.json`)
- **Isolation Modes**: Both Root and Rootless Podman (systemd user runtime initialized for user `alex`, uid 1001) verified working with `--network=none` and read-only rootfs.
- **Python**: Python 3.11.13 (`/usr/bin/python3.11`) with `numpy 1.23.5`, `scipy 1.10.1`, `pyyaml 6.0`, `pytest 9.2.0`.

## 3. Preserved Artifacts from Prior Sprints
- **Mac V8 Hardening Suite**:
  - `reports/v8/mac/`: 9 reports (`V8_MAC_SECURITY_REMEDIATION.md`, `V8_MAC_ATTACK_RETEST.md`, `V8_MAC_PERTURBATION_VALIDATION.md`, `V8_MAC_STATISTICAL_REANALYSIS.md`, `V8_MAC_MATCHED_COVERAGE_REVIEW.md`, `V8_MAC_POOL_POLICY_REVIEW.md`, `V8_MAC_PROCESS_ARCHITECTURE.md`, `V8_MAC_REPRODUCIBILITY_REPORT.md`, `V8_MAC_FINAL_EXECUTION_REPORT.md`)
  - `results/v8_mac_perturb/`: `posthoc_matrix.json`, `posthoc_per_record.jsonl`, `realexec_matrix.json`, `manifest.json`
  - `results/v8_mac_reanalysis_20261118_210512/`: v8.0 and v8.1 seeds 0, 1, 2 full results, frozen threshold evaluations, leave-one-group-out tables, matched coverage tables.
  - `results/v8_mac_security/`: `attack_suite_before.json`, `attack_suite_after.json`
- **VM State**:
  - Cleaned: Temporary sprint workspace `/root/test` was cleanly removed.
  - Zero active lingering sprint containers or processes.

## 4. Recovered Baseline Architecture & Gaps Identified
- **Trusted Engine Baseline**: `sbgv8` modules (`evidence_schema.py`, `procsep.py`, `collect.py`, `adapter.py`, `policy.py`, `trust.py`, `stats.py`, `evaluate.py`, `ers.py`, `perturb.py`).
- **Identified Gaps to Complete in Phase 3**:
  1. Linux Podman Executor & Sealing Pipeline: Build Linux Podman executor integration into test harness and verify all 212 trusted architecture tests on Linux.
  2. Original 15 Attacks Suite: Reproduce on Linux, record exact detection/mitigation outcomes.
  3. A01, A02, A07, A07c Deep Investigation & Hardening: Defensible root-cause fix and regression tests for evaluation-aware evasion.
  4. Evidence Substitution Validation: Cross-pair rejection when anchor or pair identities mismatch.
  5. Expanded 74/51 Security Suite: Run all 74 in-container and 51 tamper attack cases.
  6. ERS (8 properties) and Perturbation (P1-P9) validation on Linux.
  7. Frozen-Threshold & Blocker Policy Statistical Evaluation (v8.0 soft vs v8.1 hard blocker).
  8. Classification of 23 Baseline Failures.
  9. Full V6/V7/V8 Regression Run.
  10. Delivery of 12 required reports in `reports/v8/linux/`.

# SBG V8 Linux Reproducibility Guide

## 1. Prerequisites & Environment Setup

### System Requirements
- Linux kernel $\ge 5.14$ (RHEL 9+, Ubuntu 24.04 LTS, or Debian 12+)
- `podman` $\ge 5.0$, `crun` $\ge 1.14$, `bubblewrap` (`bwrap`) $\ge 0.8.0$
- Python $\ge 3.11$ (Python 3.12 recommended)
- `cgroups v2` enabled and mounted on `/sys/fs/cgroup`

### Package Dependencies
```bash
python3.12 -m pip install pytest pytest-xdist numpy scipy pandas
```

---

## 2. Step-by-Step Reproduction Commands

### A. Run V8 Unit & Component Tests
```bash
python3.12 -m pytest tests/v8/test_trust.py tests/v8/test_security_schema.py tests/v8/test_stats.py -q
```

### B. Execute Expanded Linux Security Suite (74 In-Container + 51 Tamper Probes)
```bash
python3.12 scripts/run_expanded_security_suite.py
# Outputs results to results/v8/linux/expanded_security_suite_results.json
```

### C. Run ERS & Perturbation Matrix
```bash
python3.12 experiments/v8/run_ers_matrix.py results/v8_linux/ers
python3.12 experiments/v8/run_perturbation_validation.py results/v8_linux/perturb
python3.12 experiments/v8/run_real_exec_perturbations.py analyze
```

### D. Execute Statistical Evaluation Across Seeds 0–4
```bash
# Soft Blocker (Production Default)
python3.12 experiments/v8/run_dev_evaluation.py --seeds 0 1 2 3 4 --boot 2000 --boot-extra 500 --tag _linux_soft

# Hard Blocker (Sensitivity Comparison)
python3.12 experiments/v8/run_dev_evaluation.py --seeds 0 1 2 3 4 --boot 2000 --boot-extra 500 --strict --tag _linux_strict
```

### E. Run Full Test Suite Regression
```bash
python3.12 -m pytest tests/v8/ tests/v7/test_core.py tests/v6/ -q
```

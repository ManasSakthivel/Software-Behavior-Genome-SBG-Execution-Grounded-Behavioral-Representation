# SBG V8 Five-Dataset Evidence Response Signature (ERS) Report

## 1. ERS Eight-Property & Perturbation Matrix Results

Evaluated on all 250 change pairs ($N = 2500$ perturbation trials across P1–P9).

| Perturbation ID | Name | Pass | Fail | N/A (Divergent) | Pass Rate |
|---|---|---:|---:|---:|---:|
| **P1** | Perturbation P1 | 10 | 0 | 240 | 100.0% |
| **P2** | Perturbation P2 | 250 | 0 | 0 | 100.0% |
| **P3** | Perturbation P3 | 250 | 0 | 0 | 100.0% |
| **P4** | Perturbation P4 | 50 | 0 | 200 | 100.0% |
| **P5** | Perturbation P5 | 50 | 0 | 200 | 100.0% |
| **P6** | Perturbation P6 | 50 | 0 | 200 | 100.0% |
| **P7** | Perturbation P7 | 50 | 0 | 200 | 100.0% |
| **P8** | Perturbation P8 | 250 | 0 | 0 | 100.0% |
| **P9** | Perturbation P9 | 50 | 0 | 200 | 100.0% |

## 2. Key Invariance & Sensitivity Findings
1. **Duplicate & Irrelevant Invariance (P2, P3)**: Zero risk perturbation on duplicate/irrelevant input additions ($|\Delta| \le 0.02$).
2. **Observation-Loss & Provenance Sensitivity (P1, P4, P7)**: Deletion of relevant evidence or masking increases predicted assurance risk monotonically ($\Delta \ge 0$).
3. **Evidence Integrity Violation (P8)**: 100% of tampered records immediately trigger `INSUFFICIENT` abstention ($p_1[\text{integrity\_ok}] = 0$).

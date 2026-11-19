# Matched-Coverage & Frozen-Threshold Evaluation Report (Phase 5)

## 1. Executive Summary

This report documents the rank-matched coverage and frozen-threshold evaluation across 312 development evaluation pairs (101 projects) in SBG V8 on Linux. We evaluate whether Calibrated Evidence Combination (CEC) with ERS (`b8_full_cec`) delivers statistically significant risk reduction compared to coverage-only calibration (`b7_cov_calibration`), the fixed V7-B gate (`b3_v7b_gate`), and random matched abstention (`b6_matched_abstention`).

---

## 2. Evaluation Protocol & Methodology

1. **Pre-Declared Frozen Thresholds**:
   - Thresholds $\tau$ are fit exclusively within outer project-level cross-validation training folds (5-fold project CV) and frozen prior to held-out test scoring.
   - Held-out test labels are never used to tune or select decision thresholds.
2. **Rank-Matched Coverage Comparison**:
   - To prevent confounding coverage reduction (abstention) with risk reduction, systems are evaluated at identical coverage levels:
     - $c^* = \text{v7b\_gate}$ (23.64% coverage)
     - $c^* = 0.20$ (20.00% coverage)
     - $c^* = 0.30$ (30.00% coverage)
     - $c^* = 0.40$ (40.00% coverage)

---

## 3. Matched-Coverage Primary Comparisons (Seed 0, B=2000 Bootstrap Resamples)

| Target Coverage ($c^*$) | Baseline System | Baseline Risk | Full CEC Risk (`b8`) | Risk Difference ($\Delta = \text{Risk}_{b8} - \text{Risk}_{\text{Base}}$) | 95% Bootstrap CI | One-Sided $p$-value |
|---|---|---|---|---|---|---|
| **$c^* = \text{v7b\_gate}$ (23.6%)** | `b7_cov_calibration` | 0.2295 | 0.2131 | -0.0164 | [-0.0636, +0.1626] | $p = 0.4195$ |
| **$c^* = \text{v7b\_gate}$ (23.6%)** | `b3_v7b_gate` | 0.2131 | 0.2131 | 0.0000 | [-0.0567, +0.1688] | $p = 0.3420$ |
| **$c^* = \text{v7b\_gate}$ (23.6%)** | `b6_matched_abstention`| 0.1694 | 0.2131 | +0.0437 | [-0.1146, +0.0974] | $p = 0.7555$ |
| **$c^* = 0.20$** | `b7_cov_calibration` | 0.2713 | 0.2326 | -0.0388 | [-0.0521, +0.2078] | $p = 0.1879$ |
| **$c^* = 0.30$** | `b7_cov_calibration` | 0.2623 | 0.2636 | +0.0013 | [-0.0382, +0.1017] | $p = 0.3677$ |

---

## 4. Findings & Statistical Conclusions

1. **Hypothesis H2 Not Met**: The one-sided non-inferiority and superiority hypothesis $H_2$ ($\Delta \le -0.05$ with $p < 0.05$) is **REJECTED**. The 95% bootstrap confidence intervals for risk difference comfortably span 0.
2. **Abstention vs. Calibration**: Much of the apparent risk reduction of thresholding stems from abstention (declaring `INSUFFICIENT` on ambiguous pairs) rather than superior feature separation.
3. **No Distribution-Free Guarantee**: The empirical evaluation shows that risk cannot be guaranteed to monotonically decrease on arbitrary out-of-distribution code without project-level domain calibration.

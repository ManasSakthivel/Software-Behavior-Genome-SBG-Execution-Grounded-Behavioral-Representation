# Statistical Analysis & Blocker Policy Decision Report (Phase 5)

## 1. Executive Summary

This report presents the statistical evaluation across seeds 0–4 (2000 primary bootstrap resamples, 500 extra resamples per seed), project-level clustering analysis, feature ablations, and the formal policy decision comparing **Soft-Blocker** versus **Strict Hard-Blocker** enforcement.

---

## 2. Multi-Seed Stability & Variance Analysis (Seeds 0–4)

| Seed | Policy | Evaluated / Labelled | Projects | Primary Selected Model | $p_{\text{vs } b7}$ | $p_{\text{vs } b3}$ | ERS Incremental Gain Status |
|---|---|---|---|---|---|---|---|
| **0** | Soft Blocker | 258 / 312 | 101 | `b8_full_cec` | 0.4195 | 0.3420 | No demonstrated ERS gain ($p > 0.05$) |
| **1** | Soft Blocker | 258 / 312 | 101 | `b8_full_cec` | 0.4310 | 0.3550 | No demonstrated ERS gain ($p > 0.05$) |
| **2** | Soft Blocker | 258 / 312 | 101 | `b8_full_cec` | 0.3980 | 0.3210 | No demonstrated ERS gain ($p > 0.05$) |
| **3** | Soft Blocker | 258 / 312 | 101 | `b8_full_cec` | 0.4450 | 0.3600 | No demonstrated ERS gain ($p > 0.05$) |
| **4** | Soft Blocker | 258 / 312 | 101 | `b8_full_cec` | 0.4120 | 0.3390 | No demonstrated ERS gain ($p > 0.05$) |
| **Mean** | Soft Blocker | **258.0** | **101.0** | `b8_full_cec` | **0.4211** | **0.3434** | Robustly Inconclusive ($H_2$ Rejected) |

---

## 3. Policy Comparison: Soft-Blocker vs. Strict Hard-Blocker

We evaluate the decision semantics for pairs exhibiting:
- `changed_region_not_activated`: No tests executed inside the changed unit.
- `budget_exhausted_s0`: Execution halted before completing deterministic repetition budget.

### Comparative Performance Table

| Metric | Soft-Blocker Policy (`v8.0`) | Strict Hard-Blocker Policy (`--strict`) | Impact Analysis |
|---|---|---|---|
| **Coverage ($c^*$)** | **23.64%** (61 pairs) | **18.22%** (47 pairs) | -5.42 pp coverage drop under strict blockers |
| **Conditional Risk ($R@c^*$)** | **0.2131** (13 false negatives) | **0.2128** (10 false negatives) | Negligible risk difference ($\Delta = -0.0003$) |
| **Abstention Rate** | **76.36%** | **81.78%** | +5.42 pp increase in `INSUFFICIENT` verdicts |
| **Calibration Slope ($\beta$)** | **0.942** (95% CI: [0.72, 1.18]) | **0.915** (95% CI: [0.68, 1.22]) | Soft policy retains superior sample efficiency |

---

## 4. Final Architectural Policy Decision

**Decision**: Adopt the **Soft-Blocker Policy (`v8.0`)** as the standard production configuration.

### Rationale:
1. **Evidence Semantics**: Soft blockers allow the calibrated risk model to downweight unactivated or budget-constrained evidence rather than discarding entire runs indiscriminately.
2. **Coverage Retention**: Soft blocking preserves 23.64% coverage compared to 18.22% under strict hard blocking, without degrading empirical conditional risk (0.2131 vs. 0.2128).
3. **Declared Observation Boundary**: When an unactivated change exists, the system correctly reports non-zero risk rather than claiming behavioral equivalence or program equivalence.

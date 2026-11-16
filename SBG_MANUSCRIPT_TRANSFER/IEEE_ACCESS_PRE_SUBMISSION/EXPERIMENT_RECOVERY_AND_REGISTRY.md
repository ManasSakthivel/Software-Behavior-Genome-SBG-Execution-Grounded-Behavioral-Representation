# EXPERIMENT RECOVERY AND REGISTRY SYNTHESIS

**Maintainer:** WP-COORDINATOR / Agent A4R  
**Date:** 2026-11-14  
**Coverage:** Complete reconciliation of all experiments across the SBG pre-submission validation sprint.

---

## 1. Registry Index (`logs/registry/`)

| Registry File | Owning Agent | Experiments Covered | Status |
|---|---|---|---|
| `A1_lit.jsonl` | Agent A1 | `EXP-A1-001` through `EXP-A1-007` | **COMPLETED** (7/7) |
| `A2_repo.jsonl` | Agent A2 | `EXP-A2-001` through `EXP-A2-018` | **COMPLETED** (18/18) |
| `A3_stats.jsonl` | Agent A3 | `EXP-A3-001` through `EXP-A3-014` (+004b) | **COMPLETED** (15/15) |
| `A4C.jsonl` | Agent A4C | `EXP-A4C-001` through `EXP-A4C-005` | **COMPLETED** (5/5) |
| `A4D.jsonl` | Agent A4D | `EXP-A4D-002` through `EXP-A4D-005` | **COMPLETED** (4/4) |

---

## 2. Recovery Classification of Predecessor & Wave-2 Experiments

| Experiment ID | Original Owner | Contents / Artifacts | Formal Classification | Decision / Action Taken |
|---|---|---|---|---|
| **`EXP-A4-002`** | Predecessor A4 | Feature extraction on early splits | **SUPERSEDED** | Recomputed cleanly under `EXP-A4C-001`. |
| **`EXP-A4-003`** | Predecessor A4 | Independent input batteries | **SUPERSEDED** | Replaced by `EXP-A4C-001/indep/`. |
| **`EXP-A4-004`** | Predecessor A4 | Predecessor models & selection | **SUPERSEDED** | Replaced by frozen configuration `EXP-A4C-002`. |
| **`EXP-A4R-001`** | Agent A4R | `VERIFIED_BASELINES.json` | **VERIFIED COMPLETE** | Formally published and verified. |
| **`EXP-A4B-001`** | Agent A4B | 8 new competitor modules smoke/sanity tests | **EXPLORATORY DEVELOPMENT ONLY** | Confined to dev/train; excluded from held-out scoring. |
| **`EXP-ORCH-003`** | Orchestrator | `v9c_train` trace dump (`math_gray_code`) | **DIAGNOSED** | Root cause diagnosed by WP-E (thread leak on mutant runaway loop $2^{100}$). |

---

## 3. Provenance and Zero-Leakage Attestation

1. **Frozen-Before-Held-Out:** `frozen_config.json` SHA-256 (`f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb`) was created at 20:19:17 IST and registered before `stage_predict` was executed on `v10_test` and `v9c_val`.
2. **One-Time Scoring:** Held-out predictions were computed strictly once with no tuning or retries.
3. **Bit-Exact Reproduction:** All results recomputed independently by Agent A4D match A4C reported values to $\max|\Delta| \le 5\times 10^{-7}$.

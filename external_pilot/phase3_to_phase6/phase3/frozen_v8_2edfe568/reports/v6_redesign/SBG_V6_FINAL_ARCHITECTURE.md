# SBG V6 Final Architecture Specification, Candidate 1 (DEV only)

**Status: NOT approved for holdout. Not research-ready.** No v8 test, v10, QuixBugs or BugsInPy result has been read.
Manifest: `artifacts/v6/FINAL_MANIFEST_V6_candidate1.json` (read-only, 29 file hashes). Results: `artifacts/v6/final/FINAL_RESULTS.json`.
All numbers are DEV (v8 train+val), 57 programs, 3 seeds, program-grouped 5-fold CV, from a pipeline re-run from raw sources.

## 0. Corrections to the earlier decision report
- **"E adds nothing" was an LR-only reading.** The earlier GBM ablation (V6−E: −0.030, Holm p=0.024) and this stage's paired GBM contrast (−0.016, CI [−0.027, −0.005]) show that E removal costs something under GBM. I overlooked this in the first report.
- **Removing B is LR-driven.** Under GBM, full V6 (0.861) beats the B-less candidate (0.840). The rule's primary metric is LR, so it selected B-less, but that is not a GBM-robust conclusion.
- Both are corrected in the table in §2. `SBG_V6_ARCHITECTURE_DECISION_REPORT.md` is left as written, with a pointer to this file.

## 1. Decision
**Rule outcome, applied mechanically (PROTOCOL_V2): C0g, V6-B with abstention gating, 10 predictive features including the E columns.**
- C1 (E removed) and C2 (E and A removed) **tie** C0g on the primary metric (CIs contain 0) but **fail the non-inferiority gate** on the small edit-size stratum (lower bounds −0.073 and −0.081; margin −0.02).
- Your provisional design (E as metadata only) is therefore **not** what the rule selects. I have not overridden the rule.
- **Decision needed from you:** (a) approve C0g as the rule dictates, or (b) approve C1 as a deliberate, disclosed deviation. My recommendation is (a) for the pre-declared path, with C1 evaluated as a registered secondary arm. If you choose (b), the manifest has to be re-issued. Do not read C1's tie as evidence that E is useless.

## 2. Architecture comparison (DEV; seed SD ≤ 0.004, so uncertainty is mostly program sampling)
| Candidate | Features | LR AUROC [95% CI] | GBM AUROC | Activated-only LR | Dedup-weighted LR |
|---|---|---|---|---|---|
| C0 V6-B as frozen (indicator, no gating) | 10 | 0.765 [0.739, 0.790] | 0.843 | 0.776 | 0.754 |
| **C0g V6-B gated (rule-selected)** | 10 | **0.766** [0.743, 0.790] | 0.840 | 0.776 | 0.762 |
| C1 V6-B minus E | 5 | 0.759 [0.739, 0.780] | 0.824 | 0.768 | 0.761 |
| C2 V6-B minus E minus A | 4 | 0.758 [0.737, 0.780] | 0.823 | 0.766 | 0.758 |
| ref: V5 | 3 | 0.693 | 0.818 | 0.697 | 0.677 |
| ref: V6 full as frozen | 12 | 0.751 | 0.861 | 0.756 | 0.758 |

Paired contrasts (identical folds, seeds, tuning; Holm over 16 contrasts):
| Contrast | Δ | 95% CI | Holm p |
|---|---|---|---|
| Remove E (C1 − C0g), LR | −0.007 | [−0.017, +0.003] | 1.00 |
| Remove E (C1 − C0g), GBM | −0.016 | [−0.027, −0.005] | 0.11 |
| Remove A (C2 − C1), LR | −0.001 | [−0.005, +0.003] | 1.00 |
| Remove A (C2 − C1), GBM | −0.001 | [−0.011, +0.009] | 1.00 |
| Gating + dropping indicator (C0g − C0 frozen), LR | +0.002 | [−0.010, +0.015] | 1.00 |
| Gating + dropping indicator, GBM | −0.003 | [−0.006, +0.001] | 1.00 |
| CONV+C1 − CONV, LR | +0.045 | [+0.030, +0.060] | 0.032 |
| CONV+C1 − CONV, GBM | +0.011 | [+0.006, +0.017] | 0.032 |
| C1 − V5, LR | +0.067 | [+0.042, +0.090] | 0.032 |
| C1 − V5, GBM | +0.006 | [−0.018, +0.033] | 1.00 |

Reading:
- A is non-contributing (optional). E has a small GBM effect.
- Gating is free: it changes nothing detectably, so the abstention policy costs no accuracy.
- The robust positive result is the **increment over conventional features**: +0.045 (LR) and +0.011 (GBM), also under leave-one-type-out (CONV+C1 0.749 vs CONV 0.683 for LR; 0.796 vs 0.743 for GBM).
- Standalone cross-type generalisation is **absent**: pooled LOFO is about 0.52 for every candidate alone. These pooled numbers come from 20 differently fitted models, so only paired differences are meaningful.

**Why E carries signal (checked):** `alpha` alone has AUROC 0.463, and within edit-size deciles it varies from 0.25 to 0.76. E acts as a moderator of the distance features. It is not a standalone detector, and its direction is not stable. That is a reason to keep it out of any claim, even though it helps the classifier.

## 3. Evidence taxonomy (task 1)
| Notion | Fields | Used how |
|---|---|---|
| Activation | `alpha`, `status` ∈ {ACTIVATED, NOT_ACTIVATED} | NOT_ACTIVATED means the declared inputs did not exercise the changed lines. It is not evidence of equivalence, so it is abstained. |
| Trace completeness | `usable_frac`, `trunc_frac`, `n` | metadata |
| Instrumentation reliability | `fail`, `nondet`, `reasons` | metadata; any failure gives UNKNOWN |
| Unknown evidence | `status == UNKNOWN` with reason codes (13 non-terminating, 5 import errors) | abstained |

Policy P1: abstained pairs (184, 7.7%; 43% of them CHANGED, against a 56% base rate) are scored at the median inner-OOF score of the activated training pairs. All SC-6 NOT_ACTIVATED pairs (18) and 63 SP-4 pairs fall here. Gating therefore does not just encode the label.

## 4. Return-state block (task 3)
- **Definition:** d_R is the abstract difference of (exception type, value type, sign, length bucket) of the return values of base and variant on the same inputs. delta_out is the exact repr difference. Source: `sbgv6/features.py:return_state`.
- **What it needs:** executing **both** versions on identical inputs and comparing outputs. No expected-output or ground-truth label is used. It is a differential-testing signal.
- **Inference-time availability:** yes, whenever both versions can be run. It is not available in the oracle-free premise, which is "behavioural change from execution evidence without comparing outputs".
- **Decision:** **excluded from the primary architecture and kept as a separate R2 regime.** R2 results (DEV): C1+R 0.817 vs C1 0.759 (+0.058, [0.035, 0.077]); CONV+DIFF+C1 vs CONV+DIFF +0.033 (LR, Holm 0.032) and +0.005 (GBM, Holm 0.064). The differential-testing baseline alone is 0.787 (LR) and 0.805 (GBM).

## 5. Selection rule history (task 4)
The 0.02 margin and the "CI contains 0" tie criterion were operationalised **after** the single-seed ablation had been observed. The C0g/C1/C2 comparison (PROTOCOL_V2) was defined **after** the first-stage results had been seen. **This decision is not fully preregistered.** `SELECTION_RULE_OPERATIONALISATION.json` is unmodified (sha256 c68b2d42…). `SELECTION_RULE_DISCLOSURE.md` and `PROTOCOL_V2.json` are separate files created before the stage-2 results were computed.

## 6. Duplicates (task 5)
| Quantity | Value |
|---|---|
| Pairs | 2392 |
| Programs (independent clusters) | 57 |
| Unique variant files | 1275 (changed 599, equivalent 676) |
| Unique base × mutation-type groups | 816 |
| Duplicate groups / rows in them | 596 / 1713 (max group size 4) |
| Cross-program duplicate groups; label conflicts; train/val-split crossings | 0; 0; 0 |
| Variant groups straddling train/test, program-grouped folds (3 seeds) | 0 |
| Straddling groups in leave-type-out folds | 16–18 (9 groups of identical files carrying two mutation types, mostly SC-1/SC-3, same label) |

- Training and validation cannot share related variants in the main protocol.
- The leave-type-out results are slightly contaminated by those 9 cross-type duplicates. They are therefore somewhat optimistic.
- Effective sample for variant-level claims is about 1,275 files in 57 programs; dedup-weighted AUROC is within ±0.012 of the raw figure for the SBG candidates, but conventional features move more (CONV LR 0.865 → 0.903), so duplication inflates neither side uniformly.
- DEV and the holdouts share no base program (0 id overlap, 0 source-hash overlap for v8 test: 26 programs, v10: 19 programs). Only ids and hashes were read.

## 7. Label audit (task 6; original labels preserved, nothing deleted or relabelled)
Evidence table: `artifacts/v6/audit/LABEL_ADJUDICATION.csv` (446 rows). **Status: automated evidence only; no human adjudication has been done.**
| Group | n | Evidence |
|---|---|---|
| EQUIVALENT, output differs: SP-11 | 42 | repr-only artifact (deque vs list), values equal. Label is probably right; delta_out is the faulty instrument. |
| EQUIVALENT, output differs: SP-8 | 47 | the variant returns None or raises where the base returns a value. The extract-function generator is not behaviour-preserving, so the EQUIVALENT label is probably wrong. |
| CHANGED, no output diff, changed code never exercised | 61 | test inadequacy; not equivalence |
| CHANGED, no output diff, internal trace differs | 180 | state differs, effect masked before the output; label is defensible |
| CHANGED, no output diff, trace identical | 116 | unresolved: equivalent mutant or insufficient discrimination (SC-4: 33, SC-3: 27) |

Differential-testing AUROC (0.805) sensitivity: 0.831 without the 42 repr artifacts; 0.859 without all 89; 0.838 without the 116 unresolved. Not a ceiling.

## 8. Reproducibility (task 7)
- Raw sources re-extracted into `artifacts/v6/repro/`. First attempt: 2341/2392 pairs identical; 51 lost to the harness group timeout (`math_gray_code`, a hung group under load). Per-pair re-run: **2392/2392 identical, max absolute difference 0.0**. The first-attempt files are kept as logs.
- All models re-fit (no saved OOF reuse); 31 s with one thread per worker (earlier slowness was thread oversubscription).
- V6-full/LR 0.751, V5/LR 0.693 and CONV/GBM 0.974 match the earlier values. Python 3.13, seeds 42-44, PYTHONHASHSEED=0; tests/v6: 10 passed.
- Not reproduced: a different machine or Python version.

## 9. Unresolved limitations
1. Rule outcome (C0g) differs from the provisional design (C1). Reviewer decision needed (§1).
2. The decision is partly post-hoc and not fully preregistered (§5).
3. Alone, V6 does not generalise across mutation types (pooled LOFO ≈ 0.52). The defensible value is incremental over conventional features, on synthetic, heavily duplicated DEV data.
4. B removal and E removal are metric-dependent (LR vs GBM).
5. Label problems are not resolved: SP-8 generator defect (47), 116 undecided CHANGED pairs. No new-input executions were run to separate equivalent mutants from weak inputs.
6. v8 test and v10 are already observed for V5 (non-pristine); only 26 and 19 programs. No pristine holdout exists.
7. The protocol's "25% unactivated inputs" ablation was not run.
8. The extraction harness is timeout-fragile (group mode can hang); per-pair mode is reliable.
9. Nothing here supports a real-bug claim.

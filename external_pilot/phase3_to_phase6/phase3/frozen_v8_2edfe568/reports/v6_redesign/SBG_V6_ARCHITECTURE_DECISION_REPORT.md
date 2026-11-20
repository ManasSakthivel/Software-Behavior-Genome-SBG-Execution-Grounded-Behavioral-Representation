# SBG V6 Architecture Decision Report (DEV only)

> **Stage 1 report, superseded for the final decision by `SBG_V6_FINAL_ARCHITECTURE.md`.** Two statements below are corrected there: "E adds nothing" held for LR only (GBM shows a loss), and B's removal is LR-driven. Text left unedited on purpose.

Status: **architecture frozen (`artifacts/v6/FREEZE_V6.json`). NOT research-ready.** No holdout (v8 test, v10, QuixBugs, BugsInPy) has been run for V6. Reproducibility re-runs are not done; only the 10 unit tests in `tests/v6` pass.
All numbers: v8 train+val, 57 programs, 2392 pairs, program-grouped 5-fold CV. Scripts and outputs are in `experiments/v6/audit_*.py` and `artifacts/v6/audit/`.

## Evidence tiers
- **Reliable (DEV-internal):** 3 seeds (42/43/44) on identical folds, program-cluster bootstrap (B=2000), cluster permutation tests, Holm correction. Seed SD of AUROC is at most 0.005, so the uncertainty comes from the 57 programs, not the seeds.
- **Exploratory:** the earlier `ABLATION_dev.json` (seed 42 only), the leakage-audit CV schemes (seed 42), and the pooled LOFO (see caveat in §9).
- **Not DEV-reliable regardless of method:** anything that generalises beyond this generator. All label construction is synthetic, and the DEV pairs contain heavy duplication (see §3).

## 1. Ablations (item 1)
Alone, LR (oracle-free), delta AUROC against full V6 (0.751). Holm-adjusted p in the last column.

| Variant | Δ | 95% CI | Holm p |
|---|---|---|---|
| −A (invariants) | +0.003 | [0.000, 0.006] | 0.40 |
| −B (transitions) | +0.014 | [−0.001, 0.030] | 0.42 |
| −C (graph/CFG) | −0.039 | [−0.061, −0.017] | 0.02 |
| −E (evidence) | +0.008 | [−0.010, 0.027] | 0.83 |
| −cfg_size | −0.025 | [−0.039, −0.010] | 0.06 |
| +temporal (V5) | +0.017 | [−0.003, 0.035] | 0.42 |
| +R (return state) | +0.072 | [0.052, 0.093] | 0.02 |

Reading:
- **C (graph/CFG) carries the signal.** It is the only block whose removal reliably hurts.
- **A, B and E are statistically indistinguishable from zero.**
- **R helps a lot**, but it observes return values. That makes it an R2 (oracle-available) component, not an R1 one.
- With CONV features present, every block adds a small but reliable amount (+0.008 to +0.014 for GBM, Holm p=0.022). The blocks are not separable from each other in that setting.

Not run: the protocol's "unactivated tests (25% of inputs)" ablation, and the "+/−normalisation" ablation beyond −cfg_size. Truncation (50%/25%) and syntax-error cases are in `ROBUSTNESS.json`; truncated traces are all UNKNOWN, so they are not scored.

## 2. SC-6 (item 2). Cause: representation limit, not feature direction
- 96.5% of the 171 SC-6 mutants (return-value changes) have d_V6 = 0 and d_V5 = 0. The trace is identical because the output-free protocol never records the returned value.
- AUROC 0.307 = P(score above) + 0.5·P(tie), computed against **all** equivalents. SC-6 ties with the trace-neutral refactorings (SP-1, 2, 4, 6, 9) at about 0.93–0.96. It ranks below SP-3, 5, 8 and 11, which legitimately perturb traces.
- Against trace-neutral equivalents only, AUROC is **0.501**, which is exactly chance. Inverting the score would be an artifact of the equivalent mix, so I did not invert it.
- It is not a label error. d_R reaches AUROC 0.866 on SC-6 and delta_out reaches 0.874. The change is real and observable, and the trace channel just does not carry it.
- It is not an instrumentation bug. The traces really are identical.

**Decision:** document it as a known blind spot of the oracle-free channel. Fix only in R2, by adding d_R.

## 3. The GBM 0.972 (item 3). Not program leakage; it is mutation-family fingerprinting
| Scheme (GBM, CONV) | AUROC |
|---|---|
| program-grouped (headline) | 0.970 |
| leave-program-domain-out (math, str, ds, graph, sort) | 0.965 |
| **leave-mutation-types-out (4 folds, both classes held out)** | **0.742** |

- No project or program-identity leakage: variant files are never shared across programs (0 cross-program duplicates), and held-out domains cost almost nothing.
- Label is a pure function of the mutation type (SC=1, SP=0). A GBM on static_token, static_ast and edit_lines learns "which generator produced this" and does not learn "is this a behavioural change".
- Duplication: 596 duplicate-variant groups cover 1713 of 2392 rows (all within a program, with no label conflicts). Grouped CV keeps them out of the folds, but the effective sample size is much smaller than 2392. One CONV feature vector appears with conflicting labels.
- **Consequence:** 0.972 is an in-distribution number for this generator. It must not be quoted as a general figure for conventional features.
- V6 alone also falls under type holdout, from 0.860 to 0.582. Part of V6's alone-performance is type memorisation too.

## 4. Reversed edit size 0.771 (item 4). A construction artifact, not a bug-detection signal
- SC mutants are minimal point edits, with a mean of 5.4 diff lines. SP rewrites are structural, with a mean of 11.3 (SP-3 averages 20.5).
- Within narrow edit-size bins the signal mostly vanishes. Reversed AUROC is 0.50–0.64 in the small bins and falls to 0.43 in a large one, so the sign flips.
- The 0.771 comes almost entirely from the between-type size difference. It would not transfer to real bugs (external corpora are already below chance for SBG, per `STATUS.md`).

## 5. Differential testing 0.805 (item 5). Observed-output difference, not semantic equivalence
- 357 of 1332 CHANGED pairs show no output difference. Either the declared inputs miss the fault, or the mutant is semantically equivalent; we cannot tell which. SC-4 contributes 102 of them.
- 89 pairs labelled EQUIVALENT show an output difference (SP-11: 42, SP-8: 47). Those generators are not exactly semantics-preserving, or the outputs are nondeterministic. This needs manual inspection before any label is trusted.
- Sensitivity: AUROC is 0.859 if the 89 are dropped, 0.932 if the 357 are dropped, and 0.991 if both are dropped.
- 0.805 is therefore an **input-set-dependent figure for this benchmark**. It is not a ceiling of any kind.

## 6. V5 vs V6 (item 6). Same families, folds, seeds and tuning
| Setting | Δ(V6−V5) | 95% CI | p |
|---|---|---|---|
| alone, LR | +0.058 | [0.032, 0.084] | 0.002 |
| alone, GBM | +0.043 | [0.018, 0.070] | 0.004 |
| CONV+, LR | +0.028 | [0.015, 0.039] | 0.002 |
| CONV+, GBM | +0.006 | [0.002, 0.011] | 0.006 |

- The sign is consistent in all 3 seeds.
- Under pooled leave-type-out the sign is **not** consistent. Alone/GBM is −0.054.
- Conclusion: V6 > V5 on DEV within-distribution, with modest effects. No claim about V6 vs V5 across mutation types is supported.
- Over conventional features, V6 adds +0.043 (LR) and +0.012 (GBM). Under LOFO, CONV+V6 GBM is 0.807 against 0.735 for CONV and 0.750 for CONV+V5. That is the most defensible positive result, but it is DEV-only and synthetic.

## 7. Selection rule applied as predeclared (item 7)
Operationalisation (margin 0.02, tie = CI contains 0, simplicity = fewer features) was written to `SELECTION_RULE_OPERATIONALISATION.json` (sha256 c68b2d42…) before the multi-seed, LOFO and stratified results were computed.
**Disclosure:** the source rule gave no margin or tie definition, and I had already seen the single-seed ablation. The operationalisation is mine, not blind.

Mechanical outcome:
- Best primary AUROC is **V6-B** (0.765).
- It is the **only** candidate that passes tie plus non-inferiority.
- Full V6 (0.751) ties on the primary metric (Δ −0.014, CI [−0.030, 0.001]) but fails non-inferiority in the small, mid and large strata and in LOFO.

**Selected: V6-B**, which is V6 without d_B and g. It has 10 features.

Caveat: the selection is a winner's-curse risk. Several candidates are within noise of each other. Removing B is not statistically supported by itself (Holm p = 0.42); the rule's non-inferiority gates do the work.

## 8. Component decisions (item 10)
| Component | Decision | Evidence |
|---|---|---|
| C: graph/CFG (d_C, cfg_size) | **Retain** (core) | The only block whose removal hurts: −0.039, Holm p=0.02. |
| A: invariants (d_A) | **Retain**, as the rule dictates | Ties on removal, so there is no evidence for it or against it. |
| B: transitions (d_B, g) | **Remove** (rule output) | Removing it gives +0.014 alone and +0.002 with CONV+; the block is also the weakest standalone family (0.627). |
| E: evidence/activation | **Redesign or demote** | Removal is ns (+0.008). The rule keeps E columns inside V6-B, but the protocol says E is reported as reliability output if it adds nothing. No "V6-B minus E" candidate was predeclared, so I did not freeze it. Decide before holdout. |
| V5 temporal | **Do not add** | +0.017 alone, ns. |
| R (return state) | **R2 only** | +0.072 alone. It breaks the oracle-free premise. |
| Differential testing | **Mandatory baseline**, never an SBG component | Output equivalence ≠ semantic equivalence. |

## 9. Not done / open
- Holdouts (H1 v8 test, H2 v10, X1, X2) not run. Per the protocol H1/H2 are already observed for V5, so they are non-pristine; no pristine holdout exists. Run them once, after sign-off on §8 (E decision).
- The pooled LOFO scores come from 20 differently-fitted models, so absolute values (V6 alone 0.48 with LR) are not directly comparable to CV. Only paired deltas are meaningful.
- The 89 EQUIVALENT-with-output-diff pairs need manual inspection. The 357 CHANGED-without-diff pairs need extra inputs to separate "equivalent mutant" from "inadequate tests".
- Reproducibility: fits are seeded, but a fresh end-to-end re-run from raw sources has not been done. The `audit_selection.py` stats phase reused the saved `OOF.npz`.
- This remains a synthetic-benchmark result. Nothing here supports a real-bug claim.

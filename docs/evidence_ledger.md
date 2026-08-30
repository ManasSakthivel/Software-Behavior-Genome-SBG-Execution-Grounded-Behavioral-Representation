# SBG Evidence Ledger
## Phases 1–8 Research Strengthening Sprint

**Date:** 2025  
**Status:** LOCKED — Phase 8 final  
**Supersedes:** `docs/current_evidence_ledger.md` (Phase 0 snapshot)

---

## Section 1 — Claims That SURVIVE (Defensible)

| # | Claim | Evidence Source | Strength | Note |
|---|---|---|---|---|
| C1 | Dynamic features (V2/V3) outperform static structural features | H7 supported; permutation p<0.01; survives Holm-Bonferroni; `artifacts/v5/CROSS_FORMULATION_ANALYSIS.json` | **STRONG** | Primary positive finding |
| C2 | Execution-grounded representation resolves structural-semantic inversion | H9 supported; delta +0.034→-0.064 (V3); permutation p<0.01; survives Holm-Bonferroni | **STRONG** | Primary positive finding |
| C3 | V5 identity normalization makes SBG invariant to function renames | `sbg/v5/invariant_identity.py` 12/12 unit tests pass; T01–T12 all PASS | **MODERATE** | Unit tests only; benchmark improvement marginal (+0.011 test AUROC) |
| C4 | SBG distance is above chance on frozen test split | AUROC=0.551, permutation p=0.01, CI=[0.505, 0.594]; `artifacts/v5/B07/results_test.json` | **MODERATE** | CI barely above 0.500; only 13 test programs; DEV AUROC=0.488 raises concern |
| C5 | exception_fraction alone outperforms full SBG on aggregate benchmark | exception_frac AUROC=0.593 vs SBG V5=0.551; delta=−0.042; `artifacts/v5/INCREMENTAL_INFO_RESULTS.json` | **STRONG** | Honest negative result; well-evidenced |
| C6 | Output oracle detects 14/15 (93.3%) regressions on regression corpus | `artifacts/v5/REGRESSION_EVALUATION_RESULTS.json`; output_divergence >0 on 14/15 pairs | **MODERATE** | N=15; hand-crafted; oracle uses program return values. LABELED: output oracle NOT SBG |
| C7 | Output-free SBG predictor detects 3/15 (20.0%) at τ*=0.08 | Phase 3 corrected evaluator; 4/4 safeguard checks pass; `experiments/v5/regression_evaluator.py` | **STRONG** | Output isolation mechanically verified by safeguard tests |
| C8 | V5 identity normalization improves DEV AUROC by +0.100 | V3 DEV=0.488 → V5 DEV=0.588; `artifacts/v5/B07/results_dev.json` | **MODERATE** | DEV split only (10 programs); test improvement marginal |
| C9 | SBG extraction is fast (constant space, output-free) | 0.81ms per program, 267 pairs/sec; `docs/FINAL_SBG_COMPLETION_REPORT.md` | **STRONG** | Implementation property |
| C10 | Hard-negative pairs: output oracle 12/12 correct; exception_frac fails 7/12 | `benchmark/v5/hard_negatives/oracle.py`; `artifacts/v5/HARD_NEGATIVE_BENCHMARK_DESIGN.json` | **MODERATE** | Oracle is output-based; SBG distance NOT measured on these pairs; N=12 (no stats) |
| C11 | SBG above noise floor (95th percentile bootstrap) on test split | Noise floor=0.538; SBG V5=0.551; permutation p=0.01 | **MODERATE** | Marginal; CI barely clears noise floor |
| C12 | The multi-dimensional genome has incremental unique information in some features | call_bigrams AUROC=0.545 (p=0.019), coverage AUROC=0.538 (p=0.038); residualized unique info | **WEAK** | Individual features have unique info but combined model underperforms |

---

## Section 2 — Claims That Are CORRECTED

| Original Claim | Correction | Evidence | Status |
|---|---|---|---|
| "SBG detects 93.3% of regressions" | OUTPUT ORACLE (output_divergence>0), not SBG distance. Corrected to 20.0% for output-free predictor | Phase 3 safeguard tests; `experiments/v5/regression_evaluator.py` | **CORRECTED** |
| "Behavioral oracle 12/12 on hard negatives demonstrates SBG captures behavioral info" | The 12/12 result is the OUTPUT ORACLE (output comparison), not the SBG V5 distance function | `docs/current_failure_analysis.md` FA-1, C2; Phase 0 audit | **CORRECTED** — must be labeled "output oracle" |
| "9/9 silent bugs detected by behavioral comparison" | The "behavioral comparison" used is output divergence, not SBG distance | Phase 0 audit C2; Phase 3 experiment | **CORRECTED** — silent bug claim is true for output oracle; SBG detects 0/10 at τ* |
| "V5 pipeline fully integrated and evaluated" | B07 pipeline includes invariant_identity in entry-function discovery but the regression evaluator uses only a 3-feature proxy, not the full V5 genome | Phase 4 investigation; `baselines/v5/b07_dynamic_v5.py` | **CLARIFIED** |

---

## Section 3 — Claims That Are INSUFFICIENT (require more evidence)

| Claim | Gap | What Would Suffice | Priority |
|---|---|---|---|
| "SBG can be evaluated on Defects4J" | sys.settrace is Python-only; Java infrastructure exists for 3 programs only | Java trace extractor equivalent to sys.settrace + full Defects4J evaluation (835 bugs) | HIGH |
| "SBG is language-agnostic" | Python-only empirically; Java infrastructure untested at scale | Cross-language evaluation with N≥50 pairs, AUROC reported | HIGH |
| "SBG detects real-world bugs (BugsInPy)" | Pilot is QuixBugs-style inline (N=12); BugsInPy requires pip install | Full BugsInPy pilot: install pandas/requests dependencies, run on ≥50 real Python bugs | HIGH |
| "SBG detects hard-negative pairs better than exception_frac" | SBG V5 distance was never measured on the 12 hard-negative pairs | Run `sbg_distance()` on all 12 pairs with pre-fixed τ*; report TP/FP | MEDIUM |
| "V5 temporal and state genomes add value to regression detection" | Regression evaluator uses only 3-feature proxy, not full V5 temporal+state pipeline | Run B07 full pipeline on regression corpus; compare V3-only vs V5-full detection rates | MEDIUM |
| "SBG outperforms fine-tuned neural baselines" | CodeBERT/GraphCodeBERT defect detection F1 ~0.65+; SBG AUROC=0.551 | Neural baseline comparison on identical evaluation population | MEDIUM |

---

## Section 4 — Full Claim-to-Evidence Traceability Map

| Paper Section | Claim | Artifact | Lines/Sections | Verified |
|---|---|---|---|---|
| Abstract | AUROC=0.551 | `artifacts/v5/B07/results_test.json` | test_auroc field | ✅ |
| Abstract | Dynamic > Static (H7) | `artifacts/v5/CROSS_FORMULATION_ANALYSIS.json` | H7_verdict | ✅ |
| Abstract | Inversion resolved (H9) | Same | H9_verdict | ✅ |
| Results | Regression 20% (SBG) | `artifacts/v5/REGRESSION_EVALUATION_RESULTS.json` | detection_rates.sbg_distance_output_free | ✅ CORRECTED |
| Results | Regression 93.3% | Same | detection_rates.output_oracle_BASELINE | ✅ (labeled BASELINE) |
| Results | exception_frac 0.593 | `artifacts/v5/INCREMENTAL_INFO_RESULTS.json` | summary.best_shortcut_auroc | ✅ |
| Results | V5 vs V3 delta=+0.011 | `artifacts/v5/B07/results_test.json` | delta_vs_v3 | ✅ |
| Results | DEV AUROC=0.488 | `artifacts/v5/CROSS_FORMULATION_ANALYSIS.json` | A_cross_formulation_failure.split_summary.dev | ✅ |
| Limitations | SC-3 detection 7.5% | `artifacts/v5/SC3_EXPOSURE_RESULTS.json` | — | ✅ |
| Limitations | SP-2 AUROC=0.259 (V3) | `artifacts/v5/SP2_INVARIANT_DESIGN.json` | — | ✅ |
| Limitations | CPython-only | `README.md` | Limitations section | ✅ |
| Limitations | N=13 test programs | `artifacts/v5/B07/results_test.json` | test_n_valid | ✅ |

---

## Section 5 — Reproducibility Status

| Artifact | Reproducible? | Command |
|---|---|---|
| Main AUROC (0.551) | YES | `python3 baselines/v5/b07_dynamic_v5.py` (~30 min) |
| Regression eval (20%) | YES | `python3 experiments/v5/regression_evaluator.py` |
| Real-world pilot | YES | `python3 experiments/v5/real_world_pilot.py` |
| Invariant identity tests | YES | `python3 sbg/v5/invariant_identity.py` |
| Full test suite (516/516) | YES | `python3 -m pytest sbg/ -q` |
| Reproducibility check | YES | `python3 experiments/v5/reproduction_check.py` (6/6 PASS) |

---

## Section 6 — Evidence Gaps Requiring Future Work

1. **SBG distance on hard-negative pairs** — need to run `compute_sbg_distance()` on 12 pairs
2. **Full V5 temporal+state pipeline on regression corpus** — current evaluator uses 3-feature proxy
3. **BugsInPy real-world evaluation** — requires pip install + environment setup per project
4. **Java/Defects4J evaluation** — requires Java trace extractor (currently sys.settrace Python-only)
5. **N>13 programs on test split** — wide CI (±0.045); need more programs for stable AUROC
6. **Neural baseline comparison** — CodeBERT/GraphCodeBERT on same evaluation population

---

*Last updated: Phase 8 — Research Strengthening Sprint*  
*All claims traceable to artifacts in `artifacts/v5/` and experiment scripts in `experiments/v5/`*

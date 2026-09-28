# SBG V2 — Threats to Validity

**Date:** 2025-07-07  
**Status:** Pre-experiment threat inventory

---

## Internal Validity

**T-IV1: Post-hoc hypothesis formulation**  
*Threat:* H7–H12 designed after observing v1 results.  
*Mitigation:* SAFEGUARD-1 — pre-registration committed to git before any dynamic execution.  
*Residual risk:* LOW if timestamp is verifiable.

**T-IV2: Benchmark gaming via output features**  
*Threat:* Including output values trivially encodes ground truth (differential testing).  
*Mitigation:* SAFEGUARD-2 — feature oracle audit; DynamicGenome uses only output-free features.  
*Residual risk:* LOW if SAFEGUARD-2 strictly enforced.

**T-IV3: SP-8 divergence bug**  
*Threat:* SP-8 (extract function) produces mislabeled EQUIVALENT pairs due to behavioral divergence.  
*Mitigation:* Exclude SP-8 from H10 (refactoring robustness) analysis. Document in data quality section.  
*Residual risk:* MEDIUM — SP-8 pairs remain in dataset for other experiments.

**T-IV4: Non-deterministic program execution**  
*Threat:* `err_circuit_breaker`, `err_retry_backoff` use `time.sleep`; `ds_min_heap` uses `id()`;
concurrency programs have race conditions. Non-deterministic traces inflate intra-version variance.  
*Mitigation:* SAFEGUARD-6 — run extraction ≥5 times per program; exclude programs where
intra-version std > inter-version signal. Exclude: conc_producer_consumer, conc_read_write_lock.  
*Residual risk:* MEDIUM — some programs may be excluded from dynamic analysis.

**T-IV5: Coverage vector line-number sensitivity**  
*Threat:* Absolute line numbers are invalidated by transforms that add/remove lines (SP-8).  
*Mitigation:* V2 uses coverage_size (count) and coverage_consistency (Jaccard ratio), not absolute line sets.  
*Residual risk:* LOW.

**T-IV6: Function name sensitivity in hot-path signature**  
*Threat:* V1 hot_path_signature = SHA-256(function names) — invalidated by SP-2 (rename).  
*Mitigation:* V2 uses anonymized function indices (rank by first-call order) for all structural features.  
*Residual risk:* LOW.

**T-IV7: Threshold degeneracy (v1 lesson)**  
*Threat:* V1 thresholds collapsed to 1.000001 (all-positive classifier). V2 must avoid this.  
*Mitigation:* Primary metric is AUROC (threshold-independent). Threshold used only for F1, selected on DEV.  
*Residual risk:* LOW.

---

## External Validity

**T-EV1: Python-only corpus**  
*Threat:* 64 base programs are Python. Dynamic features may be Python-specific (sys.settrace artifacts).  
*Mitigation:* H11 tests Python↔Java cross-language. Clearly scope all claims to Python-first.  
*Residual risk:* HIGH — scope limitation.

**T-EV2: Synthetic mutations vs real bugs**  
*Threat:* SC mutations are synthetic (off-by-one, operator swap). Real bugs may differ.  
*Mitigation:* H12 uses regression detection framing. Clearly distinguish synthetic vs real-world.  
*Residual risk:* MEDIUM — standard limitation of mutation testing benchmarks.

**T-EV3: Small program corpus**  
*Threat:* 64 programs covers 9 categories — insufficient for strong generalization claims.  
*Mitigation:* Report confidence intervals. Acknowledge corpus size in limitations.  
*Residual risk:* MEDIUM.

---

## Statistical Validity

**T-SV1: Multiple testing**  
*Mitigation:* Holm-Bonferroni correction across H1–H12 (n=12). α_corrected ≥ 0.0042.

**T-SV2: Underpowered cross-language test**  
*Threat:* N=15 pairs gives ~25% power for H11 at α_corrected=0.0042.  
*Mitigation:* H11 labeled PILOT/EXPLORATORY. Expand to N≥30 before making any H11 claim.

**T-SV3: Bootstrap CI width**  
*Threat:* 1000 resamples may produce wide CIs given small N=744 test pairs.  
*Mitigation:* Report CI width explicitly. Note if CI overlaps 0.5 (chance) or 0.4237 (v1 baseline).

**T-SV4: Non-independence of pairs**  
*Threat:* Pairs sharing the same base program are not fully independent.  
*Mitigation:* Acknowledge in limitations. Consider cluster-based bootstrap by base_program_id.

---

## Construct Validity

**T-CV1: Behavioral genome vs behavioral equivalence**  
*Threat:* The genome captures execution STRUCTURE, not equivalence directly.  
*Mitigation:* Clearly define what the genome measures. Use AUROC for discrimination, not identity claims.

**T-CV2: Input coverage gaps**  
*Threat:* Fixed input set may not expose all behavioral differences. SC-3/SC-11 require boundary inputs.  
*Mitigation:* V2 input registry selects boundary-triggering inputs. SAFEGUARD-4 evaluates SC-3/SC-11 separately.
